/**
 * Kürzel mit Sprechblase: Zustandslogik (lib/abbr.ts), Auflösung der Texte und Aufbau der Komponente (components/Abbr.tsx).
 */
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import type { Room, SchoolClass, Site, Subject, Teacher } from '../../api/types';
import { Abbr } from '../../components/Abbr';
import { INITIAL_ABBR, abbrReduce, classText, describeAbbr, isAbbrOpen, roomText, splitIds, subjectText, teacherText, type AbbrEvent, type AbbrState } from '../abbr';

const run = (events: AbbrEvent[], from: AbbrState = INITIAL_ABBR): AbbrState => events.reduce(abbrReduce, from);

describe('Zustand der Sprechblase', () => {
  it('Hover öffnet und schließt wieder', () => {
    expect(isAbbrOpen(run([{ type: 'enter' }]))).toBe(true);
    expect(isAbbrOpen(run([{ type: 'enter' }, { type: 'leave' }]))).toBe(false);
  });

  it('Tastaturfokus öffnet, Verlassen schließt auch Angeheftetes', () => {
    expect(isAbbrOpen(run([{ type: 'focus' }]))).toBe(true);
    expect(isAbbrOpen(run([{ type: 'focus' }, { type: 'pin' }, { type: 'blur' }]))).toBe(false);
  });

  it('Antippen (Touch) öffnet, erneutes Antippen schließt', () => {
    const open = run([{ type: 'toggle' }]);
    expect(open.pinned).toBe(true);
    expect(isAbbrOpen(run([{ type: 'toggle' }, { type: 'toggle' }]))).toBe(false);
  });

  it('eine per Hover offene Blase wird beim Klick geschlossen, danach wieder angeheftet', () => {
    const hovered = run([{ type: 'enter' }]);
    expect(isAbbrOpen(abbrReduce(hovered, { type: 'toggle' }))).toBe(false);
  });

  it('Langdruck heftet an; Mauszeiger wegbewegen schließt dann nicht', () => {
    const s = run([{ type: 'enter' }, { type: 'pin' }, { type: 'leave' }]);
    expect(isAbbrOpen(s)).toBe(true);
  });

  it('Escape und Antippen daneben schließen alles', () => {
    const all = run([{ type: 'enter' }, { type: 'focus' }, { type: 'pin' }]);
    expect(isAbbrOpen(abbrReduce(all, { type: 'escape' }))).toBe(false);
    expect(isAbbrOpen(abbrReduce(all, { type: 'outside' }))).toBe(false);
  });
});

const subjects = new Map<string, Subject>([
  ['D', { id: 'D', name: 'Deutsch' } as Subject],
  ['E', { id: 'E', name: 'Englisch' } as Subject],
  ['M', { id: 'M', name: 'M' } as Subject],
]);
const sites = new Map<string, Site>([['S1', { id: 'S1', name: 'Hauptgebäude' }]]);
const teacher = { id: 'MÜL', name: 'Frau Müller', subjects: ['D', 'E'] } as Teacher;
const teachers = new Map<string, Teacher>([['MÜL', teacher]]);
const rooms = new Map<string, Room>([
  ['R112', { id: 'R112', name: 'R112', site: 'S1' } as Room],
  ['F3', { id: 'F3', name: 'Fachraum 3 (S1)', site: 'S1' } as Room],
  ['K5', { id: 'K5', name: 'Klassenraum 5a', site: 'S1' } as Room],
]);
const classes = new Map<string, SchoolClass>([
  ['5a', { id: '5a', name: '5a', class_teacher: 'MÜL' } as SchoolClass],
  ['9P', { id: '9P', name: '9P (Praxisklasse)', class_teacher: null } as SchoolClass],
]);
const dir = { teachers, subjects, rooms, classes, sites };

describe('Texte zu Kürzeln', () => {
  it('Lehrkraft: Name und Fächer', () => {
    expect(teacherText(teacher, 'MÜL', subjects)).toBe('Frau Müller · Deutsch, Englisch');
    expect(teacherText(undefined, 'XX', subjects)).toBe('');
  });

  it('Fach: Name, aber nur wenn er vom Kürzel abweicht', () => {
    expect(subjectText(subjects.get('D'), 'D')).toBe('Deutsch');
    expect(subjectText(subjects.get('M'), 'M')).toBe('');
  });

  it('Raum: Nummer → „Raum …“ mit Standort; Standort-Kürzel in Klammern wird ersetzt', () => {
    expect(roomText(rooms.get('R112'), 'R112', sites)).toBe('Raum R112 (Hauptgebäude)');
    expect(roomText(rooms.get('F3'), 'F3', sites)).toBe('Fachraum 3 (Hauptgebäude)');
    expect(roomText(rooms.get('K5'), 'K5', sites)).toBe('Klassenraum 5a (Hauptgebäude)');
  });

  it('Klasse: Bezeichnung und Klassenleitung', () => {
    expect(classText(classes.get('5a'), '5a', teachers)).toBe('Klasse 5a · Klassenleitung Frau Müller');
    expect(classText(classes.get('9P'), '9P', teachers)).toBe('9P (Praxisklasse)');
  });

  it('describeAbbr wählt nach Art', () => {
    expect(describeAbbr('subject', 'D', dir)).toBe('Deutsch');
    expect(describeAbbr('site', 'S1', dir)).toBe('Hauptgebäude');
    expect(describeAbbr('teacher', 'NIX', dir)).toBe('');
  });

  it('splitIds zerlegt Listen und lässt Platzhalter weg', () => {
    expect(splitIds('MÜL, SCH')).toEqual(['MÜL', 'SCH']);
    expect(splitIds(['A', '–', ' B '])).toEqual(['A', 'B']);
    expect(splitIds(null)).toEqual([]);
  });
});

describe('Komponente Abbr', () => {
  it('ohne volle Bezeichnung: nur der Text, keine Bedienelemente', () => {
    const html = renderToStaticMarkup(createElement(Abbr, { text: 'MÜL' }));
    expect(html).toBe('MÜL');
  });

  it('mit Bezeichnung: fokussierbar, verknüpfter Beschreibungstext', () => {
    const html = renderToStaticMarkup(createElement(Abbr, { text: 'MÜL', full: 'Frau Müller' }));
    expect(html).toContain('class="abbr"');
    expect(html).toContain('tabindex="0"');
    expect(html).toMatch(/aria-describedby="([^"]+)"/);
    const id = /aria-describedby="([^"]+)"/.exec(html)![1];
    expect(html).toContain(`id="${id}" hidden=""`);
    expect(html).toContain('Frau Müller');
  });

  it('passiv (in Knopf/Rasterfeld): kein eigener Tabstopp', () => {
    const html = renderToStaticMarkup(createElement(Abbr, { text: 'D', full: 'Deutsch', passive: true }));
    expect(html).toContain('abbr-passive');
    expect(html).not.toContain('tabindex');
    expect(html).not.toContain('aria-describedby');
  });
});

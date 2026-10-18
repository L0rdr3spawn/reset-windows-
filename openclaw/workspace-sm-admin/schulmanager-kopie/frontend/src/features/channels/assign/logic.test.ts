import { describe, expect, it } from 'vitest';
import {
  draftToRubric,
  extendedDue,
  fmtPoints,
  gradeFor,
  matchesFilter,
  newRubricDraft,
  parsePoints,
  percentText,
  resultText,
  rowStatus,
  rubricMax,
  rubricToDraft,
  rubricTotal,
  setComment,
  setCriterionPoints,
  setLevel,
  switchKind,
} from './logic';
import type { Rubric } from './types';

const RASTER: Rubric = {
  kind: 'rubric',
  criteria: [
    {
      id: 'c1',
      title: 'Inhalt',
      description: '',
      levels: [
        { id: 'l1', title: 'voll', description: '', points: 4 },
        { id: 'l2', title: 'teils', description: '', points: 2 },
      ],
    },
    {
      id: 'c2',
      title: 'Sprache',
      description: '',
      levels: [
        { id: 'l1', title: 'gut', description: '', points: 3 },
        { id: 'l2', title: 'mäßig', description: '', points: 1 },
      ],
    },
  ],
};
const LEITFADEN: Rubric = {
  kind: 'guide',
  criteria: [
    { id: 'c1', title: 'Argumentation', description: '', max_points: 10 },
    { id: 'c2', title: 'Form', description: '', max_points: 5 },
  ],
};
const NOTEN = [
  { min: 92, label: '1' },
  { min: 81, label: '2' },
  { min: 67, label: '3' },
  { min: 50, label: '4' },
  { min: 30, label: '5' },
  { min: 0, label: '6' },
];

describe('Punkte', () => {
  it('formatiert und liest Punkte mit Komma', () => {
    expect(fmtPoints(4)).toBe('4');
    expect(fmtPoints(3.5)).toBe('3,5');
    expect(fmtPoints(null)).toBe('');
    expect(parsePoints('7,5')).toBe(7.5);
    expect(parsePoints(' 3 ')).toBe(3);
    expect(parsePoints('')).toBeNull();
    expect(parsePoints('abc')).toBeNull();
    expect(parsePoints('-1')).toBeNull();
  });
  it('zeigt Prozent', () => {
    expect(percentText(9, 10)).toBe('90 %');
    expect(percentText(null, 10)).toBe('');
  });
});

describe('Raster auswerten', () => {
  it('summiert angeklickte Stufen und erkennt Unvollständigkeit', () => {
    expect(rubricMax(RASTER)).toBe(7);
    let fill = setLevel({}, 'c1', 'l1');
    expect(rubricTotal(RASTER, fill)).toEqual({ points: 4, complete: false, done: 1 });
    fill = setLevel(fill, 'c2', 'l2');
    expect(rubricTotal(RASTER, fill)).toEqual({ points: 5, complete: true, done: 2 });
    fill = setLevel(fill, 'c1', 'l2');
    expect(rubricTotal(RASTER, fill).points).toBe(3);
  });
  it('rechnet Leitfaden-Punkte und begrenzt auf die Höchstpunkte', () => {
    expect(rubricMax(LEITFADEN)).toBe(15);
    let fill = setCriterionPoints({}, 'c1', '7,5');
    fill = setCriterionPoints(fill, 'c2', '9');
    expect(rubricTotal(LEITFADEN, fill)).toEqual({ points: 12.5, complete: true, done: 2 });
    fill = setCriterionPoints(fill, 'c2', '');
    expect(rubricTotal(LEITFADEN, fill)).toEqual({ points: 7.5, complete: false, done: 1 });
  });
  it('merkt sich Kommentare und räumt leere Einträge weg', () => {
    let fill = setComment({}, 'c1', 'gut begründet');
    expect(fill.c1.comment).toBe('gut begründet');
    fill = setComment(fill, 'c1', '');
    expect(fill).toEqual({});
  });
  it('schlägt die Note nach Notenschlüssel vor', () => {
    expect(gradeFor(95, 100, NOTEN)).toBe('1');
    expect(gradeFor(81, 100, NOTEN)).toBe('2');
    expect(gradeFor(66, 100, NOTEN)).toBe('4');
    expect(gradeFor(0, 100, NOTEN)).toBe('6');
    expect(gradeFor(5, 0, NOTEN)).toBeNull();
    expect(gradeFor(null, 10, NOTEN)).toBeNull();
  });
});

describe('Status der Tabelle', () => {
  it('unterscheidet abgegeben, verspätet, fehlt, bewertet', () => {
    expect(rowStatus({ status: 'abgegeben', late: false }).key).toBe('abgegeben');
    expect(rowStatus({ status: 'abgegeben', late: true }).key).toBe('verspaetet');
    expect(rowStatus({ status: 'verspaetet', late: true }).label).toBe('verspätet');
    expect(rowStatus({ status: 'ueberfaellig', late: false })).toMatchObject({ key: 'fehlt', tone: 'danger' });
    expect(rowStatus({ status: 'offen', late: false }).key).toBe('offen');
    expect(rowStatus({ status: 'bewertet', late: false }).label).toBe('bewertet');
    expect(rowStatus({ status: 'bewertet', late: true }).label).toBe('bewertet · verspätet');
    expect(rowStatus({ status: 'zurueckgegeben', late: false }).key).toBe('ueberarbeitung');
  });
  it('filtert', () => {
    expect(matchesFilter({ status: 'verspaetet' }, 'zu_bewerten')).toBe(true);
    expect(matchesFilter({ status: 'bewertet' }, 'zu_bewerten')).toBe(false);
    expect(matchesFilter({ status: 'ueberfaellig' }, 'fehlt')).toBe(true);
    expect(matchesFilter({ status: 'zurueckgegeben' }, 'fehlt')).toBe(true);
    expect(matchesFilter({ status: 'bewertet' }, 'erledigt')).toBe(true);
    expect(matchesFilter({ status: 'offen' }, 'alle')).toBe(true);
  });
  it('zeigt Punkte und Note', () => {
    const sub = { points: 8, max_points: 10, grade: '3' } as never;
    expect(resultText({ submission: sub })).toBe('8 / 10 · Note 3');
    expect(resultText({ submission: null })).toBe('');
    expect(resultText({ submission: { points: null, max_points: null, grade: '2+' } as never })).toBe('Note 2+');
  });
});

describe('Raster bearbeiten', () => {
  it('wandelt Entwurf und Raster ineinander um', () => {
    const draft = rubricToDraft(RASTER);
    expect(draft.criteria[0].levels[0].points).toBe('4');
    const back = draftToRubric(draft);
    expect('rubric' in back && back.rubric.criteria[1].levels?.[1].points).toBe(1);
  });
  it('prüft Eingaben wie der Server', () => {
    const d = newRubricDraft('rubric');
    expect(draftToRubric(d)).toEqual({ error: 'Kriterium 1: bitte einen Namen angeben.' });
    d.criteria[0].title = 'Inhalt';
    expect('rubric' in draftToRubric(d)).toBe(true);
    d.criteria[0].levels = d.criteria[0].levels.slice(0, 1);
    expect(draftToRubric(d)).toEqual({ error: '„Inhalt“: mindestens zwei Stufen angeben.' });
    const g = switchKind({ ...newRubricDraft('rubric'), criteria: [{ ...newRubricDraft('rubric').criteria[0], title: 'A' }] }, 'guide');
    expect(g.criteria[0].maxPoints).toBe('10');
    g.criteria[0].maxPoints = '0';
    expect(draftToRubric(g)).toEqual({ error: '„A“: Höchstpunkte müssen größer als 0 sein.' });
    g.criteria[0].maxPoints = '12,5';
    const ok = draftToRubric(g);
    expect('rubric' in ok && ok.rubric.criteria[0].max_points).toBe(12.5);
    expect(draftToRubric({ kind: 'guide', criteria: [] })).toEqual({ error: 'Mindestens ein Kriterium angeben.' });
  });
  it('wechselt zwischen Raster und Leitfaden', () => {
    const g = switchKind(rubricToDraft(LEITFADEN), 'rubric');
    expect(g.criteria[0].levels.length).toBe(4);
    expect(switchKind(g, 'rubric')).toBe(g);
  });
});

describe('Fristen', () => {
  it('verlängert um Tage', () => {
    const s = extendedDue('2026-10-15T12:00:00Z', 2);
    expect(s).toMatch(/^2026-10-1[5-7]T\d\d:\d\d$/);
  });
});

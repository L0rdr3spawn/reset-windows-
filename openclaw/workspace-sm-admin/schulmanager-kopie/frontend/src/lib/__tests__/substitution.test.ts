import { describe, expect, it } from 'vitest';
import type { Entry } from '../../api/types';
import { describeEntry, filterEntries, groupByClass, kindInfo, shortNote, sortEntries } from '../substitution';

function entry(id: string, extra: Partial<Entry>): Entry {
  return {
    id,
    date: '2026-10-06',
    period: 0,
    period_label: '1.',
    time: '07:55',
    kind: 'vertretung',
    classes: ['7a'],
    subject: 'M',
    teacher: 'MUE',
    substitute: 'SCH',
    room: 'R1',
    new_room: null,
    moved_from: null,
    lesson_id: 'L1',
    part: 0,
    note: '',
    warning: false,
    manual: false,
    site: 'S1',
    ...extra,
  };
}

const entries = [
  entry('a', { classes: ['10b'], period: 2, kind: 'entfall', substitute: null }),
  entry('b', { classes: ['7a'], period: 4 }),
  entry('c', { classes: ['7a'], period: 1, kind: 'raumaenderung', substitute: null, new_room: 'R9', site: 'S2' }),
  entry('d', { classes: [], kind: 'aufsicht', teacher: 'ABC', substitute: 'XYZ' }),
];

describe('Vertretungsplan-Helfer', () => {
  it('kennt alle Arten mit Kurzzeichen', () => {
    expect(kindInfo('entfall').label).toBe('Entfall');
    expect(kindInfo('raumaenderung').short).toBe('R');
    expect(kindInfo('unbekannt').cls).toBe('k-sonst');
  });

  it('filtert nach Standort, Klasse, Lehrkraft, Art und Text', () => {
    expect(filterEntries(entries, { site: 'S2' }).map((e) => e.id)).toEqual(['c']);
    expect(filterEntries(entries, { classId: '7a' }).map((e) => e.id)).toEqual(['b', 'c']);
    expect(filterEntries(entries, { teacher: 'XYZ' }).map((e) => e.id)).toEqual(['d']);
    expect(filterEntries(entries, { kinds: ['entfall'] }).map((e) => e.id)).toEqual(['a']);
    expect(filterEntries(entries, { text: 'r9' }).map((e) => e.id)).toEqual(['c']);
  });

  it('sortiert natürlich nach Klasse und gruppiert', () => {
    expect(sortEntries(entries, 'class').map((e) => e.id)).toEqual(['d', 'c', 'b', 'a']);
    const groups = groupByClass(entries).map(([k]) => k);
    expect(groups).toEqual(['Pausenaufsichten', '7a', '10b']);
  });

  it('beschreibt Einträge lesbar', () => {
    expect(describeEntry(entries[1] as Entry)).toContain('statt MUE: SCH');
  });
});

describe('shortNote', () => {
  it('kürzt lange Aufsichtshinweise', () => {
    const full = 'Aufsicht für Herr Meyer (Unterricht direkt vor/nach der Pause) – an dem Tag nicht am Standort der Aufsicht';
    expect(shortNote(full)).toBe('für Meyer · Standortwechsel');
    expect(shortNote('Aufsicht für Frau Dr. Kaiser (ohnehin im Haus)')).toBe('für Kaiser');
    expect(shortNote('Keine Lehrkraft für die Aufsicht frei – bitte manuell regeln (unbesetzt)')).toBe('Keine Lehrkraft frei · manuell regeln');
  });
  it('lässt andere Hinweise unverändert', () => {
    expect(shortNote('Vertretung für Herr Meyer')).toBe('Vertretung für Herr Meyer');
    expect(shortNote(null)).toBe('');
  });
});

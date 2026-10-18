import { describe, expect, it } from 'vitest';
import type { AppNotification, NotificationKind } from './api';
import { bellLabel, bellText, changedModes, changedSchoolRules, dayGroup, groupByDay, groupKinds, relativeTime, safeLink, validRetention, validTime } from './logic';

const NOW = new Date('2026-10-14T12:00:00');

function note(id: number, created: string): AppNotification {
  return { id, kind: 'substitution', kind_label: 'Vertretung', title: 't', body: '', link: '/vertretung', read: false, created_at: created, student_id: null };
}

describe('Glocke', () => {
  it('Zähler', () => {
    expect(bellText(0)).toBe('');
    expect(bellText(7)).toBe('7');
    expect(bellText(100)).toBe('99+');
    expect(bellLabel(0)).toContain('keine');
    expect(bellLabel(1)).toBe('Benachrichtigungen, 1 neue');
    expect(bellLabel(3)).toBe('Benachrichtigungen, 3 neue');
  });

  it('relative Zeit', () => {
    expect(relativeTime('2026-10-14T11:59:40', NOW)).toBe('gerade eben');
    expect(relativeTime('2026-10-14T11:30:00', NOW)).toBe('vor 30 Min.');
    expect(relativeTime('2026-10-14T09:00:00', NOW)).toBe('vor 3 Std.');
    expect(relativeTime(null, NOW)).toBe('');
    expect(relativeTime('kaputt', NOW)).toBe('');
  });

  it('Tagesgruppen', () => {
    expect(dayGroup('2026-10-14T01:00:00', NOW)).toBe('Heute');
    expect(dayGroup('2026-10-13T23:00:00', NOW)).toBe('Gestern');
    expect(dayGroup('2026-10-10T10:00:00', NOW)).toBe('Diese Woche');
    expect(dayGroup('2026-09-01T10:00:00', NOW)).toBe('Früher');
    const groups = groupByDay([note(3, '2026-10-14T10:00:00'), note(2, '2026-10-13T10:00:00'), note(1, '2026-08-01T10:00:00')], NOW);
    expect(groups.map((g) => g.label)).toEqual(['Heute', 'Gestern', 'Früher']);
  });

  it('nur relative Ziele', () => {
    expect(safeLink('/kursraeume/5')).toBe('/kursraeume/5');
    expect(safeLink('https://fremd.example')).toBeNull();
    expect(safeLink('//fremd.example')).toBeNull();
    expect(safeLink('')).toBeNull();
  });
});

describe('Einstellungen', () => {
  const kinds: NotificationKind[] = [
    { kind: 'a', label: 'A', group: 'G1', help: '', default: 'app', mode: 'app', school_mode: 'app', locked: false, own: false },
    { kind: 'b', label: 'B', group: 'G2', help: '', default: 'app', mode: 'app', school_mode: 'app', locked: true, own: false },
    { kind: 'c', label: 'C', group: 'G1', help: '', default: 'app', mode: 'mail', school_mode: 'app', locked: false, own: true },
  ];
  it('gruppiert Arten', () => {
    expect(groupKinds(kinds).map((g) => [g.group, g.kinds.length])).toEqual([['G1', 2], ['G2', 1]]);
  });
  it('speichert nur Änderungen und nie gesperrte Arten', () => {
    expect(changedModes(kinds, { a: 'aus', b: 'aus', c: 'mail' })).toEqual({ a: 'aus' });
    expect(changedModes(kinds, {})).toEqual({});
  });
  it('prüft Uhrzeit und Aufbewahrung', () => {
    expect(validTime('21:00')).toBe(true);
    expect(validTime('24:00')).toBe(false);
    expect(validTime('9:00')).toBe(false);
    expect(validRetention('90', 7, 730)).toBe(true);
    expect(validRetention('3', 7, 730)).toBe(false);
    expect(validRetention('abc', 7, 730)).toBe(false);
  });
  it('Schulvorgaben: nur Geändertes', () => {
    const school = [{ kind: 'a', label: 'A', group: 'G', help: '', default: 'app' as const, mode: 'app' as const, locked: false }];
    expect(changedSchoolRules(school, { a: { mode: 'app', locked: false } })).toEqual({});
    expect(changedSchoolRules(school, { a: { mode: 'app', locked: true } })).toEqual({ a: { mode: 'app', locked: true } });
  });
});

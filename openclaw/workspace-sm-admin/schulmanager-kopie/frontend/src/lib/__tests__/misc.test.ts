import { describe, expect, it } from 'vitest';
import { asList, buildQuery, describeDetail, extractConflicts } from '../../api/client';
import { normalizeMonitor } from '../../api/endpoints';
import { contrastRatio, subjectColor, textOn } from '../colors';
import { detectDelimiter, parseCsvLine, previewCsv, suggestMapping } from '../csv';
import { matchesQuery, visibleRange } from '../format';
import { backoffDelay, datesMatch, scopeMatches } from '../live';
import { blockedSlots, describeRule, toggleNum } from '../rules';

describe('API-Client', () => {
  it('extrahiert 409-Konflikte und übersetzt Fehler', () => {
    expect(extractConflicts({ conflicts: ['Lehrkraft MUE belegt'] })).toEqual(['Lehrkraft MUE belegt']);
    expect(describeDetail(401, 'totp_required')).toMatch(/Code/);
    // B-13: Feldcode → Beschriftung, Serverfehler als „Das hat nicht geklappt“ (Details: api/errors.test.ts)
    expect(describeDetail(422, [{ loc: ['body', 'day'], msg: 'zu groß' }])).toBe('Tag: zu groß');
    expect(describeDetail(500, null)).toMatch(/^Das hat nicht geklappt/);
  });
  it('baut Query-Strings ohne leere Werte', () => {
    expect(buildQuery({ a: 1, b: '', c: null, d: 'x y' })).toBe('?a=1&d=x+y');
    expect(buildQuery({})).toBe('');
  });
  it('asList akzeptiert Arrays und {items}', () => {
    expect(asList([1, 2])).toEqual([1, 2]);
    expect(asList({ items: [3] })).toEqual([3]);
    expect(asList(null)).toEqual([]);
  });
  it('normalisiert Monitor-Antworten', () => {
    const day = { date: '2026-10-06', entries: [] };
    expect(normalizeMonitor({ days: [day], announcements: [], site_name: 'Haupthaus' }).site_name).toBe('Haupthaus');
    expect(normalizeMonitor(day).days.length).toBe(1);
    expect(normalizeMonitor({ today: day, tomorrow: day }).days.length).toBe(2);
  });
});

describe('Live-Scopes', () => {
  it('vergleicht Scopes tolerant', () => {
    expect(scopeMatches(['substitutions'], ['substitutions'])).toBe(true);
    expect(scopeMatches(['overrides', 'substitutions'], ['timetable'])).toBe(false);
    expect(scopeMatches(['all'], ['timetable'])).toBe(true);
    expect(scopeMatches([], ['timetable'])).toBe(true);
    expect(scopeMatches(['data.teachers'], ['data'])).toBe(true);
    expect(datesMatch(['2026-10-06'], ['2026-10-07'])).toBe(false);
    expect(datesMatch([], ['2026-10-07'])).toBe(true);
  });
  it('Backoff wächst bis zur Obergrenze', () => {
    expect(backoffDelay(0)).toBe(1000);
    expect(backoffDelay(3)).toBe(8000);
    expect(backoffDelay(20)).toBe(30000);
  });
});

describe('Farben, CSV, Regeln, Listen', () => {
  it('wählt lesbare Textfarbe', () => {
    expect(textOn('#ffffff')).toBe('#111111');
    expect(textOn('#1d4ed8')).toBe('#ffffff');
    expect(contrastRatio('#000000', '#ffffff')).toBeCloseTo(21, 0);
    expect(subjectColor('M', '')).toMatch(/^#/);
    expect(subjectColor('M', '#123456')).toBe('#123456');
  });
  it('liest CSV-Kopfzeilen und schlägt Zuordnung vor', () => {
    expect(detectDelimiter('a;b;c')).toBe(';');
    expect(parseCsvLine('"Müller; Anna";7a;"x""y"', ';')).toEqual(['Müller; Anna', '7a', 'x"y']);
    const p = previewCsv('﻿Nachname;Vorname;Klasse\nMeier;Tom;7a\n');
    expect(p.headers).toEqual(['Nachname', 'Vorname', 'Klasse']);
    expect(p.rows[0]).toEqual(['Meier', 'Tom', '7a']);
    expect(suggestMapping(p.headers, [{ key: 'class_id', aliases: ['klasse'] }, { key: 'last_name', aliases: ['nachname'] }])).toEqual({
      class_id: 'Klasse',
      last_name: 'Nachname',
    });
  });
  it('beschreibt Rhythmus-Regeln', () => {
    expect(describeRule({ weeks: [1], days: [2], periods: [], note: '' })).toBe('Woche 1 · Mi · ganztägig');
    expect(describeRule({ weeks: [], days: [5], periods: [], note: '', rhythm: { every: 2, from_week: 10, to_week: 30 } })).toBe(
      'jede 2. Woche ab Woche 10 bis Woche 30 · Sa · ganztägig',
    );
    expect(describeRule({ weeks: [], days: [1, 3], periods: [0, 1, 2], note: 'Praxis' })).toBe('Di, Do · 1.–3. Stunde (Praxis)');
    expect(blockedSlots([{ weeks: [2], days: [1], periods: [], note: '' }], 2, 5, 2).size).toBe(2);
    expect(toggleNum([1, 3], 2)).toEqual([1, 2, 3]);
    expect(toggleNum([1, 2], 2)).toEqual([1]);
  });
  it('Suche und Virtualisierung', () => {
    expect(matchesQuery('Anna Müller 7a', 'müller 7a')).toBe(true);
    expect(matchesQuery('Anna Müller 7a', 'müller 8a')).toBe(false);
    expect(visibleRange(400, 400, 40, 2600, 2)).toEqual([8, 22]);
    expect(visibleRange(0, 400, 40, 5, 2)).toEqual([0, 5]);
  });
});

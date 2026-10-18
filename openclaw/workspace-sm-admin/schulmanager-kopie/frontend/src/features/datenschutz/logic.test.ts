import { describe, expect, it } from 'vitest';
import { clampDays, confirmMatches, daysText, diffSettings, dueText, groupByCategory, previewSummary, type KindSetting, type PrivacySettings } from './logic';

const kind = (key: string, category: string, over: Partial<KindSetting> = {}): KindSetting => ({
  key, label: key, category, category_label: category.toUpperCase(), legal: '', how: 'gelöscht', description: '', last: false,
  days: 30, default_days: 30, effective_days: 30, age_days: null, age_default: null, has_age: false, ...over,
});
const settings = (kinds: KindSetting[]): PrivacySettings => ({
  grace_days: 30, auto_purge: true, audit_days: 365, log_days: 1095, defaults: { grace_days: 30, audit_days: 365, log_days: 1095 }, kinds,
});

describe('Löschkonzept-Hilfen', () => {
  it('gruppiert Datenarten nach Kategorie in Lieferreihenfolge', () => {
    const g = groupByCategory([kind('a', 'gesundheit'), kind('b', 'leistung'), kind('c', 'gesundheit')]);
    expect(g.map((x) => [x.category, x.kinds.map((k) => k.key)])).toEqual([['gesundheit', ['a', 'c']], ['leistung', ['b']]]);
  });

  it('formuliert Fälligkeit und Fristen', () => {
    expect(dueText(null, 'wartend')).toBe('–');
    expect(dueText(0, 'wartend')).toBe('fällig');
    expect(dueText(1, 'wartend')).toBe('in 1 Tag');
    expect(dueText(12, 'wartend')).toBe('in 12 Tagen');
    expect(dueText(5, 'erledigt')).toBe('erledigt');
    expect(daysText(0)).toBe('aus');
    expect(daysText(365)).toBe('1 Jahr');
    expect(daysText(730)).toBe('2 Jahre');
    expect(daysText(30)).toBe('30 Tage');
  });

  it('verlangt die exakte Bestätigung beim Sofort-Löschen', () => {
    expect(confirmMatches(' S00012 ', 'S00012')).toBe(true);
    expect(confirmMatches('s00012', 'S00012')).toBe(false);
    expect(confirmMatches('', '')).toBe(false);
  });

  it('begrenzt Tage auf 0 bis 3650', () => {
    expect(clampDays('', 7)).toBe(7);
    expect(clampDays('-5', 7)).toBe(0);
    expect(clampDays('99999', 7)).toBe(3650);
    expect(clampDays('45', 7)).toBe(45);
  });

  it('sendet nur geänderte Einstellungen', () => {
    const base = settings([kind('absences', 'gesundheit', { has_age: true, age_days: 365, age_default: 365 }), kind('exam_results', 'leistung')]);
    const draft = structuredClone(base);
    expect(diffSettings(base, draft)).toEqual({});
    draft.grace_days = 60;
    draft.kinds[0].age_days = 400;
    draft.kinds[1].days = 200;
    expect(diffSettings(base, draft)).toEqual({ grace_days: 60, kinds: { absences: { age_days: 400 }, exam_results: { days: 200 } } });
  });

  it('fasst die Vorschau zusammen', () => {
    expect(previewSummary({ people: [], expiry: [] })).toBe('0 Personen, 0 Einträge');
    const item = { kind: 'x', label: 'x', count: 2, due_at: '', due: true, done: false };
    expect(
      previewSummary({
        people: [{ student_id: 'S1', name: 'A', class_id: '5a', left_at: '', items: [item], total: 5, due_total: 2 }],
        expiry: [{ kind: 'absences', label: 'Krankmeldungen', count: 3 }],
      }),
    ).toBe('1 Person, 5 Einträge, davon 2 jetzt fällig, 3 Einträge nach Alter');
  });
});

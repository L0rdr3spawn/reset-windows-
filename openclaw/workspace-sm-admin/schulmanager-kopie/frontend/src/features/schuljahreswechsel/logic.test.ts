import { describe, expect, it } from 'vitest';
import { defaultPlan, runText, setRule, suggestYearStart, toRequest } from './logic';

describe('Schuljahreswechsel', () => {
  it('schlägt den Schuljahresbeginn vor', () => {
    expect(suggestYearStart(new Date(2026, 5, 15))).toBe('2026-08-31'); // 31.8.2026 ist ein Montag
    expect(suggestYearStart(new Date(2026, 8, 10))).toBe('2027-08-30'); // 31.8.2027 ist Dienstag → Montag davor
    expect(new Date(suggestYearStart(new Date(2025, 0, 1)) + 'T00:00:00Z').getUTCDay()).toBe(1);
  });

  it('setzt und entfernt Klassenregeln', () => {
    let p = defaultPlan(new Date(2026, 5, 1));
    p = setRule(p, '5a', 'keep', 'promote');
    expect(p.class_rules).toEqual({ '5a': { action: 'keep' } });
    p = setRule(p, '5a', 'promote', 'promote');
    expect(p.class_rules).toEqual({});
  });

  it('lässt leere neue Klassen weg', () => {
    const p = defaultPlan();
    p.new_classes = [
      { name: ' 5x ', grade: 5, site: '', count: 20 },
      { name: '', grade: 5, site: '', count: 20 },
      { name: 'y', grade: 20, site: '', count: 20 },
    ];
    expect(toRequest(p).new_classes).toEqual([{ name: '5x', grade: 5, site: '', count: 20 }]);
  });

  it('fasst einen Lauf zusammen', () => {
    const t = runText({ id: 'x', at: '', by: '', old_year: '', new_year: '', undone_at: null, notes: [], summary: { promoted: 8, graduated: 2, leavers: 50, accounts: 90 } });
    expect(t).toBe('8 Klassen hochgestuft, 2 Abgangsklassen, 50 Abgänger/innen, 90 Konten gesperrt');
  });
});

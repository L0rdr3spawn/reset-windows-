import { describe, expect, it } from 'vitest';
import { regionOptions, summaryText, visibleChanges, type HolidayChange } from './holidayImport';

const ch = (action: HolidayChange['action'], date_from: string, name = 'x'): HolidayChange => ({ action, name, date_from, date_to: date_from, kind: 'feiertag' });

describe('holidayImport', () => {
  it('blendet Unverändertes aus und sortiert Neues zuerst', () => {
    const rows = visibleChanges([ch('unchanged', '2026-01-01'), ch('exists', '2026-02-01'), ch('add', '2026-05-01'), ch('update', '2026-03-01')]);
    expect(rows.map((r) => r.action)).toEqual(['add', 'update', 'exists']);
  });

  it('fasst Zahlen zusammen', () => {
    const z = { add: 0, update: 0, unchanged: 5, exists: 1, edited: 0, removed: 0 };
    expect(summaryText(z)).toBe('Keine Änderungen');
    expect(summaryText({ ...z, add: 3, update: 1 })).toBe('3 neu, 1 geändert');
  });

  it('ordnet Unterregionen unter die Oberregion', () => {
    const o = regionOptions([
      { code: 'DE-BY-AU', name: 'Augsburg', category: '', parent: 'DE-BY' },
      { code: 'DE-BY', name: 'Bayern', category: '', parent: '' },
      { code: 'DE-BB', name: 'Brandenburg', category: '', parent: '' },
    ]);
    expect(o.map((x) => x.code)).toEqual(['DE-BY', 'DE-BY-AU', 'DE-BB']);
  });
});

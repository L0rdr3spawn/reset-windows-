/**
 * lib/weeks.ts gegen die gemeinsame Tabelle `tests/data/weeks_cases.json` (dieselben Fälle prüft `tests/test_weeks.py`
 * für `schulmanager/weeks.py`) und weitere Fälle der Oberfläche (52-Wochen-System: jede Woche / ausgewählte Wochen /
 * Rhythmus).
 */
import { describe, expect, it } from 'vitest';
import type { WeekRhythm } from '../../api/types';
import {
  classDaysOf,
  classPlanningText,
  daysText,
  describeRhythm,
  describeSelection,
  describeWeeks,
  holidayBadge,
  holidayKindOf,
  normalizeWeeks,
  rhythmActive,
  rhythmErrors,
  schoolDaysOf,
  selectionWeeks,
  specActive,
  specFromWeeks,
  weekOfDate,
  weekOptionLabel,
  weekQueryFromSearch,
  weeksErrors,
  weeksPreview,
  weekText,
} from '../weeks';

interface Cases {
  describe: { weeks: number[]; text: string }[];
  weeks_errors: { weeks: number[]; errors: string[]; normalized: number[] | null }[];
  rhythm_active: { rhythm: WeekRhythm; active: number[]; inactive: number[] }[];
  rhythm_describe: { rhythm: WeekRhythm; text: string }[];
  rhythm_errors: { rhythm: WeekRhythm; errors: string[] }[];
}

const fs = (await import(/* @vite-ignore */ `node:${'fs'}`)) as { readFileSync: (p: URL, enc: 'utf8') => string };
const CASES = JSON.parse(fs.readFileSync(new URL('../../../../tests/data/weeks_cases.json', import.meta.url), 'utf8')) as Cases;

describe('weeks_cases.json (gemeinsam mit weeks.py)', () => {
  it('describe', () => {
    expect(CASES.describe.length).toBeGreaterThan(10);
    for (const c of CASES.describe) expect(describeWeeks(c.weeks), JSON.stringify(c)).toBe(c.text);
  });

  it('weeks_errors + Normalform', () => {
    for (const c of CASES.weeks_errors) {
      expect(weeksErrors(c.weeks), JSON.stringify(c)).toEqual(c.errors);
      if (c.normalized) expect(normalizeWeeks(c.weeks)).toEqual(c.normalized);
    }
  });

  it('Rhythmus: aktiv, Text, Fehler', () => {
    for (const c of CASES.rhythm_active) {
      for (const l of c.active) expect(rhythmActive(c.rhythm, l), `${JSON.stringify(c.rhythm)} L=${l}`).toBe(true);
      for (const l of c.inactive) expect(rhythmActive(c.rhythm, l), `${JSON.stringify(c.rhythm)} L=${l}`).toBe(false);
    }
    for (const c of CASES.rhythm_describe) expect(describeRhythm(c.rhythm)).toBe(c.text);
    for (const c of CASES.rhythm_errors) expect(rhythmErrors(c.rhythm), JSON.stringify(c)).toEqual(c.errors);
  });
});

describe('Wochenangaben in der Oberfläche', () => {
  it('jede Woche, ausgewählte Wochen, Rhythmus (k beliebig)', () => {
    expect(specActive({ weeks: [] }, 7)).toBe(true);
    expect(specActive({ weeks: [2, 9] }, 9)).toBe(true);
    expect(specActive({ weeks: [2, 9] }, 3)).toBe(false);
    expect(specActive({ weeks: [] }, null)).toBe(true);
    const r = { every: 7, from_week: 3 };
    expect(selectionWeeks({ rhythm: r }, 53)).toEqual([3, 10, 17, 24, 31, 38, 45, 52]);
    expect(selectionWeeks({ weeks: [4, 5] }, 52)).toEqual([4, 5]);
    expect(describeSelection({ weeks: [4, 5] })).toBe('Woche 4, 5');
    expect(describeSelection({ rhythm: { every: 4, from_week: 2 } })).toBe('jede 4. Woche ab Woche 2');
    expect(describeSelection({ weeks: [] })).toBe('jede Woche');
  });

  it('specFromWeeks wie weeks.spec_from_weeks', () => {
    expect(specFromWeeks([])).toEqual({ weeks: [], rhythm: null });
    expect(specFromWeeks(Array.from({ length: 53 }, (_, i) => i + 1))).toEqual({ weeks: [], rhythm: null });
    expect(specFromWeeks([2, 4])).toEqual({ weeks: [2, 4], rhythm: null });
    expect(specFromWeeks([1, 3, 5, 7])).toEqual({ weeks: [], rhythm: { every: 2, from_week: 1, to_week: 7 } });
    expect(specFromWeeks(Array.from({ length: 26 }, (_, i) => 2 + 2 * i))).toEqual({ weeks: [], rhythm: { every: 2, from_week: 2, to_week: 0 } });
    expect(specFromWeeks([1, 2, 3, 4])).toEqual({ weeks: [1, 2, 3, 4], rhythm: null });
  });

  it('Vorschau „Woche 2, 5, 8 … (17 von 52)“', () => {
    expect(weeksPreview(selectionWeeks({ rhythm: { every: 3, from_week: 2 } }, 52), 52)).toBe('Woche 2, 5, 8 … (17 von 52)');
    expect(weeksPreview([1, 3], 4)).toBe('Woche 1, 3 (2 von 4)');
    expect(weeksPreview([], 4)).toBe('Keine Woche (0 von 4)');
  });

  it('nie Buchstaben', () => {
    for (let w = 1; w <= 53; w++) expect(describeWeeks([w])).toMatch(/^Woche \d+$/);
  });
});

describe('Unterrichtstage', () => {
  it('Schule: school_days, sonst die ersten days Tage', () => {
    expect(schoolDaysOf({ days: 5 })).toEqual([0, 1, 2, 3, 4]);
    expect(schoolDaysOf({ days: 5, school_days: [] })).toEqual([0, 1, 2, 3, 4]);
    expect(schoolDaysOf({ days: 5, school_days: [5, 0, 0, 2] })).toEqual([0, 2, 5]);
    expect(schoolDaysOf(null)).toEqual([0, 1, 2, 3, 4]);
  });

  it('Klasse: eigene Tage vor Schulvorgabe', () => {
    const st = { days: 5, school_days: [] };
    expect(classDaysOf({ school_days: [5] }, st)).toEqual([5]);
    expect(classDaysOf({}, st)).toEqual([0, 1, 2, 3, 4]);
    expect(classPlanningText({}, st)).toBe('Mo–Fr');
    expect(classPlanningText({ school_days: [0, 1, 5] }, st)).toBe('Eigene Tage · Mo, Di, Sa');
  });

  it('daysText', () => {
    expect(daysText([0, 1, 2, 3, 4])).toBe('Mo–Fr');
    expect(daysText([0, 1, 2, 4])).toBe('Mo–Mi, Fr');
    expect(daysText([1, 3])).toBe('Di, Do');
    expect(daysText([])).toBe('–');
  });
});

describe('Wochen im Schuljahr', () => {
  const year = {
    weeks: [
      { week_no: 6, iso_week: 41, week_start: '2026-10-05', week_end: '2026-10-11', holiday_week: false, holidays: [] },
      { week_no: 8, iso_week: 43, week_start: '2026-10-19', week_end: '2026-10-25', holiday_week: true, holidays: ['Herbstferien (Beispiel)'] },
    ],
  };

  it('Auswahl „Woche 10 · KW 45 · 02.11.–08.11.“ (+ „ · Ferien“), KW-Modus ohne „Woche“', () => {
    expect(weekOptionLabel(year.weeks[0]!)).toBe('Woche 6 · KW 41 · 05.10.–11.10.');
    expect(weekOptionLabel(year.weeks[1]!)).toBe('Woche 8 · KW 43 · 19.10.–25.10. · Ferien');
    expect(weekOptionLabel(year.weeks[1]!, 'iso')).toBe('KW 43 · 19.10.–25.10. · Ferien');
  });

  it('Woche eines Datums, Text mit Rückfall auf die KW', () => {
    expect(weekOfDate(year, '2026-10-08')?.week_no).toBe(6);
    expect(weekOfDate(year, '2026-10-11')?.week_no).toBe(6);
    expect(weekOfDate(year, '2026-10-12')).toBeUndefined();
    expect(weekText({ week_text: 'Woche 6 · KW 41' }, '2026-10-07')).toBe('Woche 6 · KW 41');
    expect(weekText(undefined, '2026-10-07')).toBe('KW 41 · 05.10.–11.10.');
  });

  it('Adresse: ?datum= kanonisch (Montag), ?woche=L laufende Woche, alte ?woche=0 = heute', () => {
    expect(weekQueryFromSearch(new URLSearchParams('datum=2026-10-08'))).toEqual({ date: '2026-10-05' });
    expect(weekQueryFromSearch(new URLSearchParams('woche=12'))).toEqual({ week_no: 12 });
    expect(weekQueryFromSearch(new URLSearchParams('woche=0'))).toEqual({});
    expect(weekQueryFromSearch(new URLSearchParams('woche=x'))).toEqual({});
    expect(weekQueryFromSearch(new URLSearchParams('datum=2026-13-40&woche=3'))).toEqual({ week_no: 3 });
  });

  it('Ferienbadge', () => {
    expect(holidayBadge({ holiday_week: true, holiday_name: 'Herbstferien (Beispiel)' })).toBe('Herbstferien (Beispiel)');
    expect(holidayBadge({ holiday_week: true, holiday_name: null })).toBe('Ferien');
    expect(holidayBadge({ holiday_week: false, holiday_name: null })).toBe('');
  });

  it('Ferienart beim Lesen alter Daten (V15)', () => {
    expect(holidayKindOf({ name: 'Herbstferien (Beispiel)' })).toBe('ferien');
    expect(holidayKindOf({ name: 'Tag der Deutschen Einheit' })).toBe('feiertag');
    expect(holidayKindOf({ name: 'Brückentag', kind: 'beweglich' })).toBe('beweglich');
  });
});

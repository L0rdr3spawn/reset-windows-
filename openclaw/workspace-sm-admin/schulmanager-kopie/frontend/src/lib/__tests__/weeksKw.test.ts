import { afterEach, describe, expect, it } from 'vitest';
import { patternRhythm, selectionForPattern } from '../../components/WeekPatternInput';
import { describeRhythm, describeSelection, describeWeeks, rhythmActive, setWeekCalendar, weekFromNumber, weekNumberOf, weeksPreview } from '../weeks';

// Schuljahr 2027/28: Woche 1 = Mo 30.08.2027 (KW 35), 52 Wochen, KW 52 → KW 1 bei Woche 19
const Y2027 = { iso: true, firstMonday: '2027-08-30', weeks: 52 };
// Schuljahr 2026/27: Woche 1 = Mo 31.08.2026 (KW 36), 53 ISO-Wochen im Jahr 2026
const Y2026 = { iso: true, firstMonday: '2026-08-31', weeks: 52 };

afterEach(() => setWeekCalendar(null));

describe('Kalenderwochen-Anzeige', () => {
  it('ohne Kalender bleibt es bei „Woche 5“', () => {
    expect(describeWeeks([1, 2, 3, 9])).toBe('Woche 1–3, 9');
    expect(describeRhythm({ every: 2, from_week: 3, to_week: 0 })).toBe('jede 2. Woche ab Woche 3');
  });

  it('rechnet laufende Wochen über den Jahreswechsel in KW um', () => {
    setWeekCalendar(Y2027);
    expect([1, 18, 19, 20].map(weekNumberOf)).toEqual([35, 52, 1, 2]);
    expect(describeWeeks([17, 18, 19, 20, 21])).toBe('KW 51, 52, 1–3');
    expect(describeSelection({ weeks: [], rhythm: { every: 2, from_week: 4, to_week: 0 } })).toBe('jede 2. Woche ab KW 38');
  });

  it('KW 53 gibt es nur im langen Jahr', () => {
    setWeekCalendar(Y2026);
    expect(weekNumberOf(18)).toBe(53);
    expect(weekFromNumber(53)).toBe(18);
    expect(describeWeeks([17, 18, 19])).toBe('KW 52, 53, 1');
    setWeekCalendar(Y2027);
    expect(weekFromNumber(53)).toBeNull();
  });

  it('Eingabe „ab KW 38, alle 2 Wochen“ läuft über Neujahr ohne Sprung', () => {
    setWeekCalendar(Y2027);
    const sel = selectionForPattern({ every: 2, from: 38, to: 0 });
    const r = sel?.rhythm;
    expect(r).toEqual({ every: 2, from_week: 4 });
    if (!r) throw new Error('kein Rhythmus');
    const kws = Array.from({ length: 52 }, (_, i) => i + 1).filter((w) => rhythmActive({ ...r, to_week: 0 }, w)).map(weekNumberOf);
    expect(kws.slice(0, 4)).toEqual([38, 40, 42, 44]);
    expect(kws.filter((k) => k < 10)).toEqual([2, 4, 6, 8]);
    expect(weeksPreview([4, 6, 8, 10], 52)).toBe('KW 38, 40, 42 … (4 von 52)');
  });

  it('meldet KW, die es im Schuljahr nicht gibt', () => {
    setWeekCalendar(Y2027);
    expect(patternRhythm({ every: 2, from: 53, to: 0 }).errors).toEqual(['KW 53 gibt es in diesem Schuljahr nicht.']);
    expect(selectionForPattern({ every: 2, from: 53, to: 0 })).toBeNull();
    expect(patternRhythm({ every: 1, from: 40, to: 45 }).rhythm).toEqual({ every: 1, from_week: 6, to_week: 11 });
  });

  it('Kalender im Schuljahr-Modus zählt unverändert', () => {
    setWeekCalendar({ ...Y2027, iso: false });
    expect(describeWeeks([1, 2, 3])).toBe('Woche 1–3');
    expect(weekFromNumber(5)).toBe(5);
  });
});

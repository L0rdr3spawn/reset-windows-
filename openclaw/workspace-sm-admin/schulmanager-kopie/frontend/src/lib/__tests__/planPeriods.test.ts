/** Planzeiträume (lib/planPeriods.ts): Zustand, Texte, Raster, Wochenauswahl, Eingabeprüfung. */
import { describe, expect, it } from 'vitest';
import type { PlanPeriod, PlanState, SchoolYear } from '../../api/types';
import {
  groupLabel,
  groupWeeks,
  noPlanBlocked,
  noPlanDetail,
  noPlanTitle,
  periodEdge,
  periodErrors,
  periodSpan,
  planMissing,
  planOfWeek,
  removedWithPlan,
  rowsBody,
  sameRows,
  toRows,
} from '../planPeriods';

const h1: PlanPeriod = { id: 'hj1', name: '1. Halbjahr', date_from: '2026-08-31', date_to: '2027-01-31', from_week: 1, to_week: 22, lessons: 40, has_plan: true };
const h2: PlanPeriod = { id: 'hj2', name: '2. Halbjahr', date_from: '2027-02-01', date_to: '2027-08-29', from_week: 23, to_week: 52, lessons: 0, has_plan: false };
const missing: PlanState = { active: true, state: 'missing', period: h2 };

describe('Zustand und Texte', () => {
  it('ohne Zeiträume nie „kein Plan“', () => {
    expect(planMissing(undefined)).toBe(false);
    expect(planMissing({ active: false, state: 'ok', period: null })).toBe(false);
    expect(planMissing({ active: true, state: 'ok', period: h1 })).toBe(false);
    expect(planMissing(missing)).toBe(true);
    expect(planMissing({ active: true, state: 'none', period: null })).toBe(true);
  });
  it('Texte nennen Zeitraum und Grenzen', () => {
    expect(noPlanTitle(missing)).toBe('Für diesen Zeitraum ist noch kein Stundenplan festgelegt');
    expect(noPlanTitle({ active: true, state: 'none', period: null })).toBe('Für diese Woche ist kein Planzeitraum festgelegt');
    expect(noPlanDetail(missing)).toBe('2. Halbjahr, 01.02.–29.08.2027');
    expect(noPlanDetail({ active: true, state: 'none', period: null })).toBe('');
    expect(periodSpan(h1)).toBe('31.08.2026–31.01.2027');
    expect(periodSpan({ date_from: '2027-02-01', date_to: '2027-06-30' })).toBe('01.02.–30.06.2027');
  });
  it('Felder: alle Unterrichtstage × Stunden schraffiert', () => {
    const b = noPlanBlocked([0, 1, 4], 3);
    expect(b).toHaveLength(9);
    expect(b[0]).toEqual({ day: 0, period: 0, note: 'Stundenplan noch nicht festgelegt' });
    expect(noPlanBlocked([], 5)).toEqual([]);
  });
});

describe('Beginn und Ende in der Wochennavigation', () => {
  it('erkennt die Woche, in der der Zeitraum beginnt bzw. endet', () => {
    const p1: PlanState = { active: true, state: 'ok', period: h1 };
    expect(periodEdge(p1, '2026-08-31')).toBe('start');
    expect(periodEdge(p1, '2027-01-25')).toBe('end');
    expect(periodEdge(p1, '2026-10-05')).toBeNull();
    expect(periodEdge(missing, '2027-02-01')).toBe('start');
    expect(periodEdge(null, '2027-02-01')).toBeNull();
  });
});

const year = {
  plan_periods: [h1, h2],
  weeks: [
    { week_no: 21, iso_week: 3, week_start: '2027-01-18', week_end: '2027-01-24', holiday_week: false, holidays: [], plan_state: 'ok', plan_period: 'hj1' },
    { week_no: 22, iso_week: 4, week_start: '2027-01-25', week_end: '2027-01-31', holiday_week: false, holidays: [], plan_state: 'ok', plan_period: 'hj1' },
    { week_no: 23, iso_week: 5, week_start: '2027-02-01', week_end: '2027-02-07', holiday_week: false, holidays: [], plan_state: 'missing', plan_period: 'hj2' },
  ],
} as unknown as SchoolYear;

describe('Wochenauswahl', () => {
  it('gruppiert nach Zeitraum', () => {
    const g = groupWeeks(year);
    expect(g.map((x) => [x.period?.id, x.weeks.length])).toEqual([
      ['hj1', 2],
      ['hj2', 1],
    ]);
    expect(groupLabel(g[0]!)).toBe('1. Halbjahr');
    expect(groupLabel(g[1]!)).toBe('2. Halbjahr · noch kein Stundenplan');
    expect(groupLabel({ period: null, weeks: [] })).toBe('Außerhalb der Zeiträume');
  });
  it('ohne Zeiträume eine Gruppe ohne Zeitraum', () => {
    const g = groupWeeks({ weeks: year.weeks.map((w) => ({ ...w, plan_period: undefined })), plan_periods: undefined });
    expect(g).toHaveLength(1);
    expect(g[0]?.period).toBeNull();
  });
  it('Plan-Zustand einer Woche aus der Jahresübersicht', () => {
    expect(planOfWeek(year, year.weeks[2])).toEqual({ active: true, state: 'missing', period: h2 });
    expect(planOfWeek({ plan_periods: [] }, year.weeks[2])).toBeNull();
    expect(planOfWeek(year, undefined)).toBeNull();
  });
});

describe('Zeiträume bearbeiten', () => {
  const ok = toRows([h1, h2]);
  it('gültige Eingabe', () => {
    expect(periodErrors(ok)).toEqual([]);
    expect(sameRows(ok, toRows([h1, h2]))).toBe(true);
    expect(sameRows(ok, [ok[0]!])).toBe(false);
  });
  it('Name, Daten, Reihenfolge, Überschneidung', () => {
    expect(periodErrors([])).toEqual(['Bitte mindestens einen Zeitraum anlegen.']);
    expect(periodErrors([{ name: ' ', date_from: '2026-09-01', date_to: '2026-10-01' }])).toEqual(['Zeitraum 1: Bitte einen Namen angeben.']);
    expect(periodErrors([{ name: 'A', date_from: '', date_to: '2026-10-01' }])[0]).toContain('Beginn und Ende');
    expect(periodErrors([{ name: 'A', date_from: '2026-10-02', date_to: '2026-10-01' }])[0]).toContain('vor dem Beginn');
    // gleiche Kalenderwoche (Mittwoch/Donnerstag) = Überschneidung, da Zeiträume ganze Wochen umfassen
    const e = periodErrors([
      { name: 'A', date_from: '2026-09-01', date_to: '2026-10-07' },
      { name: 'B', date_from: '2026-10-08', date_to: '2026-12-01' },
    ]);
    expect(e).toHaveLength(1);
    expect(e[0]).toContain('überschneiden');
    expect(
      periodErrors([
        { name: 'A', date_from: '2026-09-01', date_to: '2026-10-04' },
        { name: 'B', date_from: '2026-10-05', date_to: '2026-12-01' },
      ]),
    ).toEqual([]);
  });
  it('Körper ohne leere Kennung, Löschen mit Plan erkennen', () => {
    expect(rowsBody([{ name: ' Neu ', date_from: '2027-09-01', date_to: '2027-10-01' }])).toEqual([{ name: 'Neu', date_from: '2027-09-01', date_to: '2027-10-01' }]);
    expect(rowsBody(ok)[0]).toMatchObject({ id: 'hj1' });
    expect(removedWithPlan([h1, h2], [ok[1]!])).toEqual([h1]);        // 1. Halbjahr entfällt und hat 40 Blöcke
    expect(removedWithPlan([h1, h2], [ok[0]!])).toEqual([]);          // 2. Halbjahr ohne Plan: keine Bestätigung nötig
  });
});

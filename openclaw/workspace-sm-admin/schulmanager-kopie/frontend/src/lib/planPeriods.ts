/**
 * Planzeiträume (z. B. 1./2. Halbjahr): je Zeitraum ein eigener Stundenplan (`schulmanager/plan_periods.py`).
 * Reine Hilfsfunktionen (testbar ohne Browser): Zustand einer Woche, Texte, gesperrte Felder für das Raster,
 * Gruppierung der Wochenauswahl, Prüfung der Eingaben.
 */
import type { BlockedSlot, PlanPeriod, PlanPeriodInput, PlanPeriodRef, PlanState, SchoolYear, SchoolYearWeek } from '../api/types';
import { addDays, formatDate, formatDayMonth, isValidISO } from './dates';

export const NO_PLAN_TITLE = 'Für diesen Zeitraum ist noch kein Stundenplan festgelegt';
export const NO_PERIOD_TITLE = 'Für diese Woche ist kein Planzeitraum festgelegt';
/** Kurztext für Felder und Monitor */
export const NO_PLAN_SHORT = 'Stundenplan noch nicht festgelegt';

/** Hat die Woche keinen gültigen Plan? (Ohne Zeiträume nie.) */
export function planMissing(plan: PlanState | null | undefined): boolean {
  return !!plan?.active && plan.state !== 'ok';
}

/** „01.02.–29.08.2027“ (Jahr nur hinten, wenn beide im selben Jahr liegen) */
export function periodSpan(p: Pick<PlanPeriodRef, 'date_from' | 'date_to'>): string {
  const a = p.date_from.slice(0, 4);
  const b = p.date_to.slice(0, 4);
  return a === b ? `${formatDayMonth(p.date_from)}–${formatDate(p.date_to)}` : `${formatDate(p.date_from)}–${formatDate(p.date_to)}`;
}

/** Überschrift des Hinweises „kein Plan“ */
export function noPlanTitle(plan: PlanState | null | undefined): string {
  return plan?.state === 'none' ? NO_PERIOD_TITLE : NO_PLAN_TITLE;
}

/** „2. Halbjahr, 01.02.–29.08.2027“ (leer, wenn die Woche in keinem Zeitraum liegt) */
export function noPlanDetail(plan: PlanState | null | undefined): string {
  return plan?.period ? `${plan.period.name}, ${periodSpan(plan.period)}` : '';
}

/** Alle Felder der Unterrichtstage als gesperrt (schraffiert), mit Hinweis im Tooltip */
export function noPlanBlocked(days: Iterable<number>, periods: number, note = NO_PLAN_SHORT): BlockedSlot[] {
  const out: BlockedSlot[] = [];
  for (const day of days) for (let period = 0; period < periods; period++) out.push({ day, period, note });
  return out;
}

/** Beginnt oder endet der Zeitraum in der Woche `weekStart` … +6? (für die Wochennavigation) */
export function periodEdge(plan: PlanState | null | undefined, weekStart: string): 'start' | 'end' | null {
  const p = plan?.period;
  if (!p) return null;
  const end = addDays(weekStart, 6);
  if (p.date_from >= weekStart && p.date_from <= end) return 'start';
  if (p.date_to >= weekStart && p.date_to <= end) return 'end';
  return null;
}

export interface WeekGroup {
  /** `null` = Wochen außerhalb aller Zeiträume */
  period: PlanPeriod | null;
  weeks: SchoolYearWeek[];
}

/** Wochen des Schuljahres nach Zeiträumen gruppiert (in Reihenfolge); ohne Zeiträume eine Gruppe ohne Zeitraum. */
export function groupWeeks(year: Pick<SchoolYear, 'weeks' | 'plan_periods'>): WeekGroup[] {
  const periods = year.plan_periods ?? [];
  const byId = new Map(periods.map((p) => [p.id, p]));
  const out: WeekGroup[] = [];
  for (const w of year.weeks) {
    const p = (w.plan_period && byId.get(w.plan_period)) || null;
    const last = out[out.length - 1];
    if (last && (last.period?.id ?? null) === (p?.id ?? null)) last.weeks.push(w);
    else out.push({ period: p, weeks: [w] });
  }
  return out;
}

/** Beschriftung einer Gruppe in der Wochenauswahl: „2. Halbjahr · noch kein Stundenplan“ */
export function groupLabel(g: WeekGroup): string {
  if (!g.period) return 'Außerhalb der Zeiträume';
  return g.period.has_plan ? g.period.name : `${g.period.name} · noch kein Stundenplan`;
}

// ------------------------------------------------------------------ Zeiträume bearbeiten
export interface PeriodRow {
  id?: string;
  name: string;
  date_from: string;
  date_to: string;
}

export function toRows(periods: readonly PlanPeriodRef[]): PeriodRow[] {
  return periods.map((p) => ({ id: p.id, name: p.name, date_from: p.date_from, date_to: p.date_to }));
}

export function sameRows(a: readonly PeriodRow[], b: readonly PeriodRow[]): boolean {
  return a.length === b.length && a.every((r, i) => r.id === b[i]?.id && r.name === b[i]?.name && r.date_from === b[i]?.date_from && r.date_to === b[i]?.date_to);
}

/**
 * Prüfung vor dem Speichern (der Server prüft zusätzlich Schuljahr und Wochen): Name, Daten, Reihenfolge.
 * Zeiträume umfassen ganze Wochen; sie dürfen sich nicht überschneiden.
 */
export function periodErrors(rows: readonly PeriodRow[]): string[] {
  const errs: string[] = [];
  if (!rows.length) errs.push('Bitte mindestens einen Zeitraum anlegen.');
  rows.forEach((r, i) => {
    const label = r.name.trim() || `Zeitraum ${i + 1}`;
    if (!r.name.trim()) errs.push(`${label}: Bitte einen Namen angeben.`);
    if (!isValidISO(r.date_from) || !isValidISO(r.date_to)) errs.push(`${label}: Bitte Beginn und Ende angeben.`);
    else if (r.date_to < r.date_from) errs.push(`${label}: Das Ende liegt vor dem Beginn.`);
  });
  const ok = rows.filter((r) => isValidISO(r.date_from) && isValidISO(r.date_to)).sort((a, b) => a.date_from.localeCompare(b.date_from));
  for (let i = 1; i < ok.length; i++) {
    const a = ok[i - 1] as PeriodRow;
    const b = ok[i] as PeriodRow;
    if (mondayKey(b.date_from) <= mondayKey(a.date_to)) errs.push(`${a.name.trim() || 'Zeitraum'} und ${b.name.trim() || 'Zeitraum'} überschneiden sich (Zeiträume umfassen ganze Wochen).`);
  }
  return errs;
}

function mondayKey(iso: string): string {
  const d = new Date(`${iso}T12:00:00`);
  const back = (d.getDay() + 6) % 7;
  return addDays(iso, -back);
}

/** Körper für `PUT /calendar/plan-periods` */
export function rowsBody(rows: readonly PeriodRow[]): PlanPeriodInput[] {
  return rows.map((r) => ({ ...(r.id ? { id: r.id } : {}), name: r.name.trim(), date_from: r.date_from, date_to: r.date_to }));
}

/** Zeiträume, die beim Speichern entfallen und einen Plan haben (Bestätigung nötig) */
export function removedWithPlan(saved: readonly PlanPeriod[], rows: readonly PeriodRow[]): PlanPeriod[] {
  const keep = new Set(rows.map((r) => r.id).filter(Boolean));
  return saved.filter((p) => !keep.has(p.id) && p.lessons > 0);
}

/** Plan-Zustand einer Woche aus der Schuljahresübersicht (wenn die Antwort der Ansicht ihn noch nicht trägt) */
export function planOfWeek(year: Pick<SchoolYear, 'plan_periods'> | null | undefined, w: Pick<SchoolYearWeek, 'plan_state' | 'plan_period'> | null | undefined): PlanState | null {
  if (!year?.plan_periods?.length || !w?.plan_state) return null;
  const p = year.plan_periods.find((x) => x.id === w.plan_period) ?? null;
  return { active: true, state: w.plan_state, period: p };
}

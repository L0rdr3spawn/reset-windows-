/**
 * Reine Hilfsfunktionen für Arbeitszeitfenster (testbar, ohne React).
 *
 * Regel wie im Backend (schulmanager/teacher_profile.py): Eine Stunde zählt als verfügbar, wenn sie
 * KOMPLETT in einem Fenster liegt (Beginn laut Zeitraster, Dauer = period_minutes). Leere Fensterliste =
 * ganztägig verfügbar; sonst gelten Tage ohne Fenster als nicht verfügbar.
 */
import type { TimeRule, User } from '../../api/types';
import { describeSelection, rhythmErrors, specActive, weeksErrors } from '../../lib/weeks';
import { rulesEqual } from './availability';
import type { TeacherProfile, TimeWindow, WorkGrid } from './types';

export const WINDOW_NOTE = 'Zeitfenster';
const DAY_SHORT = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

/** „HH:MM“ → Minuten (null bei ungültiger Eingabe); „24:00“ nur mit allow24. */
export function toMinutes(value: string | null | undefined, allow24 = false): number | null {
  const m = /^(\d{1,2}):(\d{2})$/.exec((value ?? '').trim());
  if (!m) return null;
  const h = Number(m[1]);
  const mi = Number(m[2]);
  if (mi > 59 || h > 24 || (h === 24 && (mi > 0 || !allow24))) return null;
  return h * 60 + mi;
}

export function fmtMinutes(min: number): string {
  const h = Math.floor(min / 60);
  const m = min % 60;
  return `${h < 10 ? '0' : ''}${h}:${m < 10 ? '0' : ''}${m}`;
}

/** Tage der Zeitfenster-Editoren ab Montag: bis zum letzten Unterrichtstag der Schule (R3: auch Sa/So). */
export function profileDays(o: { days: number; school_days?: readonly number[] | null }): number {
  return Math.min(7, Math.max(1, o.days || 5, ...(o.school_days ?? []).map((d) => d + 1)));
}

export function allDays(days: number): number[] {
  return Array.from({ length: Math.max(0, days) }, (_, i) => i);
}

export function emptyWindow(days: number): TimeWindow {
  return { days: allDays(days), start: '08:00', end: '16:00', weeks: [] };
}

export interface WindowTemplate {
  key: string;
  label: string;
  hint: string;
  windows: (days: number) => TimeWindow[];
}

/** Schnellvorlagen für typische Arbeitszeiten. */
export const WINDOW_TEMPLATES: WindowTemplate[] = [
  { key: 'ganztags', label: 'ganztägig', hint: 'keine Einschränkung', windows: () => [] },
  { key: 'ab10', label: 'ab 10:00', hint: 'Unterricht erst ab 10:00 Uhr', windows: (d) => [{ days: allDays(d), start: '10:00', end: '18:30', weeks: [] }] },
  { key: 'abends', label: 'nur abends ab 16:00', hint: 'nur Abendunterricht', windows: (d) => [{ days: allDays(d), start: '16:00', end: '21:00', weeks: [] }] },
  { key: 'vormittags', label: 'nur vormittags', hint: 'bis 13:00 Uhr', windows: (d) => [{ days: allDays(d), start: '07:00', end: '13:00', weeks: [] }] },
];

/** Prüft ein Fenster; liefert eine deutsche Fehlermeldung oder null. */
export function windowError(w: TimeWindow, days: number): string | null {
  if (!w.days.length) return 'Bitte mindestens einen Wochentag wählen.';
  if (w.days.some((d) => d < 0 || d >= days)) return 'Wochentag außerhalb der Schulwoche.';
  if (w.weeks.length && w.rhythm) return 'Bitte entweder Wochen oder einen Rhythmus angeben.';
  const weekErr = w.rhythm ? rhythmErrors(w.rhythm)[0] : weeksErrors(w.weeks)[0];
  if (weekErr) return weekErr;
  const s = toMinutes(w.start);
  const e = toMinutes(w.end, true);
  if (s === null) return `Ungültiger Beginn „${w.start}“.`;
  if (e === null) return `Ungültiges Ende „${w.end}“.`;
  if (e <= s) return 'Das Ende muss nach dem Beginn liegen.';
  return null;
}

/** Gilt das Fenster in der laufenden Woche `weekNo` am Tag? (jede Woche, ausgewählte Wochen oder Rhythmus) */
export function windowApplies(w: TimeWindow, day: number, weekNo?: number | null): boolean {
  return w.days.includes(day) && specActive(w, weekNo);
}

/** Verfügbare Stunden (0-basiert) am Tag der laufenden Woche `weekNo`. */
export function availablePeriods(
  windows: readonly TimeWindow[],
  periodTimes: readonly string[],
  periodMinutes: number,
  day: number,
  weekNo?: number | null,
): Set<number> {
  const all = new Set(periodTimes.map((_, i) => i));
  if (!windows.length) return all;
  const len = Math.max(1, periodMinutes || 45);
  const out = new Set<number>();
  for (const w of windows) {
    if (!windowApplies(w, day, weekNo)) continue;
    const s = toMinutes(w.start);
    const e = toMinutes(w.end, true);
    if (s === null || e === null) continue;
    periodTimes.forEach((t, p) => {
      const ps = toMinutes(t);
      if (ps !== null && ps >= s && ps + len <= e) out.add(p);
    });
  }
  return out;
}

/** Wochen eines Fensters („Woche 2“, „jede 2. Woche ab Woche 10“) oder leer bei jeder Woche. */
export function windowWeeksText(w: Pick<TimeWindow, 'weeks' | 'rhythm'>): string {
  if (!w.rhythm && !w.weeks.length) return '';
  const t = describeSelection(w);
  return t === 'jede Woche' ? '' : t;
}

/** Kurzbeschreibung wie im Backend, z. B. „Mo–Fr 10:00–18:30; Woche 2: Mo–Do 10:00–17:00“. */
export function describeWindows(windows: readonly TimeWindow[]): string {
  if (!windows.length) return 'ganztägig verfügbar';
  return windows
    .map((w) => {
      const d = [...w.days].sort((a, b) => a - b);
      const contiguous = d.length > 2 && d.every((x, i) => i === 0 || x === (d[i - 1] ?? -2) + 1);
      const dtext = contiguous ? `${DAY_SHORT[d[0] ?? 0]}–${DAY_SHORT[d[d.length - 1] ?? 0]}` : d.map((x) => DAY_SHORT[x] ?? String(x + 1)).join(', ');
      const wt = windowWeeksText(w);
      return `${wt ? `${wt}: ` : ''}${dtext} ${w.start}–${w.end}`;
    })
    .join('; ');
}

// ------------------------------------------------------------------ Arbeitszeiten-Raster
export const MAX_GRID_WEEKS = 52;

/** Beliebigen Wert als Raster lesen (leer/ungültig → 1 Woche ohne Sperren). */
export function asGrid(v: unknown): WorkGrid {
  const g = (v && typeof v === 'object' ? v : {}) as Partial<WorkGrid>;
  const weeks = Math.min(MAX_GRID_WEEKS, Math.max(1, Math.floor(Number(g.weeks) || 1)));
  const blocked = (Array.isArray(g.blocked) ? g.blocked : [])
    .filter((b) => b && Number.isInteger(b.week) && Number.isInteger(b.day) && b.week < weeks && Array.isArray(b.periods))
    .map((b) => ({ week: b.week, day: b.day, periods: [...new Set(b.periods)].sort((a, c) => a - c) }))
    .filter((b) => b.periods.length);
  return { weeks, blocked };
}

export const gridKey = (week: number, day: number, period: number) => `${week}:${day}:${period}`;

export function gridBlocked(g: WorkGrid): Set<string> {
  const out = new Set<string>();
  for (const b of g.blocked) for (const p of b.periods) out.add(gridKey(b.week, b.day, p));
  return out;
}

function gridFrom(set: Set<string>, weeks: number): WorkGrid {
  const cells = new Map<string, { week: number; day: number; periods: number[] }>();
  for (const key of set) {
    const [w, d, p] = key.split(':').map(Number) as [number, number, number];
    if (w >= weeks) continue;
    const k = `${w}:${d}`;
    const c = cells.get(k) ?? { week: w, day: d, periods: [] };
    c.periods.push(p);
    cells.set(k, c);
  }
  const blocked = [...cells.values()].map((c) => ({ ...c, periods: c.periods.sort((a, b) => a - b) })).sort((a, b) => a.week - b.week || a.day - b.day);
  return { weeks, blocked };
}

/** Eine Stunde sperren bzw. wieder freigeben. */
export function toggleGridCell(g: WorkGrid, week: number, day: number, period: number): WorkGrid {
  const set = gridBlocked(g);
  const key = gridKey(week, day, period);
  if (set.has(key)) set.delete(key);
  else set.add(key);
  return gridFrom(set, g.weeks);
}

/** Ganzen Tag (alle `periods` Stunden) sperren oder freigeben. */
export function setGridDay(g: WorkGrid, week: number, day: number, periods: number, block: boolean): WorkGrid {
  const set = gridBlocked(g);
  for (let p = 0; p < periods; p++) {
    if (block) set.add(gridKey(week, day, p));
    else set.delete(gridKey(week, day, p));
  }
  return gridFrom(set, g.weeks);
}

/** Wechsel auf `weeks` Wochen ändern. Neue Wochen übernehmen das bisherige Muster (Woche k = Woche k mod alt) – die
 * Arbeitszeiten bleiben damit gleich, bis man eine Woche ändert. */
export function setGridWeeks(g: WorkGrid, weeks: number): WorkGrid {
  const n = Math.min(MAX_GRID_WEEKS, Math.max(1, Math.floor(weeks)));
  const old = Math.max(1, g.weeks);
  const set = new Set<string>();
  for (const b of g.blocked) {
    for (let w = b.week; w < n; w += old) for (const p of b.periods) set.add(gridKey(w, b.day, p));
  }
  return gridFrom(set, n);
}

export function gridEqual(a: unknown, b: unknown): boolean {
  const x = asGrid(a);
  const y = asGrid(b);
  if (!x.blocked.length && !y.blocked.length) return true;
  return x.weeks === y.weeks && JSON.stringify(x.blocked) === JSON.stringify(y.blocked);
}

/** Leeres Raster → `{}` (keine Einschränkung) für den Server. */
export function gridOut(g: WorkGrid): WorkGrid | Record<string, never> {
  return g.blocked.length || g.weeks > 1 ? g : {};
}

export function describeGrid(v: unknown): string {
  const g = asGrid(v);
  if (!g.blocked.length) return 'keine Einschränkung';
  const count = g.blocked.reduce((n, b) => n + b.periods.length, 0);
  return `${g.weeks === 1 ? 'jede Woche' : `Wechsel über ${g.weeks} Wochen`}, ${count} Stunde${count === 1 ? '' : 'n'} gesperrt`;
}

/** Alte Arbeitszeitfenster in das Raster umrechnen (gesperrt = Stunde liegt nicht komplett in einem Fenster). */
export function gridFromWindows(windows: readonly TimeWindow[], periodTimes: readonly string[], periodMinutes: number, days: number): WorkGrid {
  if (!windows.length) return { weeks: 1, blocked: [] };
  // Verfügbarkeit je laufende Woche 1 … 52; das Raster wiederholt sich nach der kleinsten passenden Zahl von Wochen
  const key = (L: number) =>
    Array.from({ length: days }, (_, d) => [...availablePeriods(windows, periodTimes, periodMinutes, d, L)].sort((a, b) => a - b).join(',')).join('|');
  const keys = Array.from({ length: MAX_GRID_WEEKS }, (_, i) => key(i + 1));
  let n = MAX_GRID_WEEKS;
  for (let c = 1; c <= MAX_GRID_WEEKS; c++) {
    if (keys.every((k, i) => k === keys[i % c])) {
      n = c;
      break;
    }
  }
  const set = new Set<string>();
  for (let k = 0; k < n; k++) {
    for (let d = 0; d < days; d++) {
      const free = availablePeriods(windows, periodTimes, periodMinutes, d, k + 1);
      periodTimes.forEach((_, p) => {
        if (!free.has(p)) set.add(gridKey(k, d, p));
      });
    }
  }
  return gridFrom(set, n);
}

export function isWindowRule(r: Pick<TimeRule, 'note'>): boolean {
  return (r.note ?? '').startsWith(WINDOW_NOTE);
}

/** Trennt manuell gepflegte Sperrzeiten von den aus Zeitfenstern erzeugten. */
export function splitRules(rules: readonly TimeRule[]): { manual: TimeRule[]; generated: TimeRule[] } {
  return { manual: rules.filter((r) => !isWindowRule(r)), generated: rules.filter(isWindowRule) };
}

function sameNums(a: readonly number[], b: readonly number[]): boolean {
  return a.length === b.length && a.every((x, i) => x === b[i]);
}

function normWindows(ws: readonly TimeWindow[]): string {
  return JSON.stringify(
    ws.map((w) => ({ days: [...w.days].sort((a, b) => a - b), start: w.start, end: w.end, weeks: [...w.weeks].sort((a, b) => a - b), rhythm: w.rhythm ?? null })),
  );
}

/** Ist das Profil (inhaltlich) unverändert? */
/** Fächer inkl. vorgeschlagener neuer Fächer (der Server ergänzt diese in `subjects`). */
function allSubjects(p: TeacherProfile): string {
  return JSON.stringify([...new Set([...p.subjects, ...(p.new_subjects ?? []).map((n) => n.id)])].sort());
}

function newSubjectsKey(p: TeacherProfile): string {
  return JSON.stringify([...(p.new_subjects ?? [])].map((n) => [n.id, n.name, n.room_type ?? null]).sort());
}

export function profileEqual(a: TeacherProfile, b: TeacherProfile): boolean {
  return (
    sameNums([a.max_hours], [b.max_hours]) &&
    allSubjects(a) === allSubjects(b) &&
    newSubjectsKey(a) === newSubjectsKey(b) &&
    JSON.stringify([...a.preferred_classes].sort()) === JSON.stringify([...b.preferred_classes].sort()) &&
    normWindows(a.time_windows ?? []) === normWindows(b.time_windows ?? []) &&
    gridEqual(a.work_grid, b.work_grid) &&
    rulesEqual(a.unavailable, b.unavailable) &&
    rulesEqual(a.wishes, b.wishes)
  );
}

/**
 * Lehrkraft mit eingeschränktem Planzugriff (Scope own_classes, §9.3)?
 * Die Rechte-Scopes liefert /auth/me nicht – sie gelten laut Rechtematrix für die Rolle „lehrer“.
 */
export function isScopedTeacher(user: Pick<User, 'role' | 'permissions'> | null | undefined): boolean {
  if (!user) return false;
  const perms = new Set(user.permissions ?? []);
  return user.role === 'lehrer' && perms.has('plans.read_all') && !perms.has('timetable.edit');
}

export const STATUS_TONE: Record<string, 'info' | 'success' | 'danger' | 'warning' | ''> = {
  offen: 'warning',
  genehmigt: 'success',
  abgelehnt: 'danger',
  zurueckgezogen: '',
};

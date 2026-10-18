/**
 * Datumshilfen (lokale Zeit, ISO-Format YYYY-MM-DD).
 */

export const WEEKDAYS = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'];
export const WEEKDAYS_SHORT = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];
const MONTHS = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];

function pad(n: number): string {
  return n < 10 ? `0${n}` : String(n);
}

export function toISO(d: Date): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function parseISO(s: string): Date {
  const [y, m, d] = s.slice(0, 10).split('-').map((x) => parseInt(x, 10));
  return new Date(y ?? 1970, (m ?? 1) - 1, d ?? 1, 12, 0, 0);
}

export function isValidISO(s: string | null | undefined): s is string {
  return !!s && /^\d{4}-\d{2}-\d{2}$/.test(s) && !Number.isNaN(parseISO(s).getTime());
}

export function todayISO(now: Date = new Date()): string {
  return toISO(now);
}

export function addDays(iso: string, n: number): string {
  const d = parseISO(iso);
  d.setDate(d.getDate() + n);
  return toISO(d);
}

/** 0 = Montag … 6 = Sonntag */
export function weekdayIndex(iso: string): number {
  return (parseISO(iso).getDay() + 6) % 7;
}

/**
 * Unterrichtstage: eine Zahl n heißt wie bisher „die ersten n Tage ab Montag“, eine Liste nennt die Wochentage
 * (0 = Mo … 6 = So, R3). Eine leere Liste gilt als Mo–Fr.
 */
export type SchoolDays = number | readonly number[];

export function isWeekend(iso: string, schoolDays: SchoolDays = 5): boolean {
  const wd = weekdayIndex(iso);
  if (typeof schoolDays === 'number') return wd >= schoolDays;
  return schoolDays.length ? !schoolDays.includes(wd) : wd >= 5;
}

/** Nächster/vorheriger Schultag (überspringt Tage ohne Unterricht). */
export function shiftSchoolDay(iso: string, dir: 1 | -1, schoolDays: SchoolDays = 5): string {
  let d = addDays(iso, dir);
  for (let i = 0; i < 7 && isWeekend(d, schoolDays); i++) d = addDays(d, dir);
  return d;
}

/** Heute, oder – an einem Tag ohne Unterricht – der nächste Schultag. */
export function currentSchoolDay(now: Date = new Date(), schoolDays: SchoolDays = 5): string {
  const t = toISO(now);
  return isWeekend(t, schoolDays) ? shiftSchoolDay(t, 1, schoolDays) : t;
}

export function mondayOf(iso: string): string {
  return addDays(iso, -weekdayIndex(iso));
}

/** ISO-Kalenderwoche (Woche mit dem ersten Donnerstag des Jahres = KW 1). */
export function isoWeekNumber(iso: string): number {
  const d = parseISO(iso);
  const thursday = new Date(d.getFullYear(), d.getMonth(), d.getDate() + 3 - weekdayIndex(iso), 12);
  const jan4 = new Date(thursday.getFullYear(), 0, 4, 12);
  const firstMonday = new Date(jan4.getFullYear(), 0, 4 - ((jan4.getDay() + 6) % 7), 12);
  const days = Math.round((thursday.getTime() - firstMonday.getTime()) / 86_400_000);
  return 1 + Math.floor(days / 7);
}

/** „05.10.“ */
export function formatDayMonth(iso: string): string {
  const d = parseISO(iso);
  return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.`;
}

/** „Dienstag, 6. Oktober 2026“ */
export function formatLong(iso: string): string {
  const d = parseISO(iso);
  return `${WEEKDAYS[weekdayIndex(iso)]}, ${d.getDate()}. ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

/** „Di, 06.10.“ */
export function formatShort(iso: string): string {
  const d = parseISO(iso);
  return `${WEEKDAYS_SHORT[weekdayIndex(iso)]}, ${pad(d.getDate())}.${pad(d.getMonth() + 1)}.`;
}

/** „06.10.2026“ */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '–';
  const d = parseISO(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()}`;
}

/** Zeitstempel (ISO mit Uhrzeit) → „06.10.2026, 08:15“ */
export function formatDateTime(ts: string | null | undefined): string {
  if (!ts) return '–';
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()}, ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Relativer Tagesname: Heute/Morgen/Gestern oder kurzes Datum. */
export function relativeDayLabel(iso: string, today: string = todayISO()): string {
  if (iso === today) return 'Heute';
  if (iso === addDays(today, 1)) return 'Morgen';
  if (iso === addDays(today, -1)) return 'Gestern';
  return formatShort(iso);
}

export function dateRangeLabel(from: string, to: string): string {
  return from === to ? formatDate(from) : `${formatDate(from)} – ${formatDate(to)}`;
}

export function formatClock(d: Date): string {
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/**
 * Wochen und Unterrichtstage im 52-Wochen-System – rein, testbar.
 *
 * Alles, was nicht jede Woche gilt, hat eine Wochenangabe: **jede Woche** (leer), **ausgewählte Wochen**
 * (`weeks`, laufende Wochen 1 … 53) oder einen **Rhythmus** (`rhythm`: alle k Wochen ab Woche s, optional bis Woche e).
 * Es gibt keine Wochenbuchstaben. `describeWeeks`/`describeRhythm` liefern dieselben
 * Ergebnisse wie `schulmanager/weeks.py` (gemeinsame Tabelle `tests/data/weeks_cases.json`). Texte zum Datum
 * (`week_text`) baut nur das Backend; hier wird nur noch formatiert.
 *
 * **Kalenderwochen (Standard):** Gespeichert wird immer die laufende Woche (Position im Schuljahr, fortlaufend über
 * Neujahr). Nur Anzeige und Eingabe rechnen in ISO-Kalenderwochen um – über den Schuljahreskalender, den `setWeekCalendar`
 * (aus `GET /calendar/school-year`) bereitstellt. Ohne Kalender (Tests, Altserver) bleibt es bei „Woche 5“.
 */
import type {
  DayInfo,
  DayKind,
  Holiday,
  HolidayKind,
  SchoolYear,
  SchoolYearWeek,
  Settings,
  WeekInfo,
  WeekNumbering,
  WeekRhythm,
} from '../api/types';
import { addDays, formatDayMonth, isValidISO, isoWeekNumber, mondayOf, parseISO, toISO, WEEKDAYS, WEEKDAYS_SHORT } from './dates';

/** Höchste laufende Woche (das Schuljahr hat 52 oder 53 Wochen). */
export const MAX_WEEKS = 53;

// ============================================================================================== Kalenderwochen-Anzeige

/** Schuljahreskalender für die Umrechnung laufende Woche ↔ KW (`iso` aus `week_numbering`). */
export interface WeekCalendar {
  iso: boolean;
  /** Montag der laufenden Woche 1 */
  firstMonday: string;
  /** Wochen des Schuljahres (52 oder 53) */
  weeks: number;
}

let calendarState: WeekCalendar | null = null;
let calendarVersion = 0;
const calendarListeners = new Set<() => void>();

/** Setzt den Kalender (`null` = „Woche 5“ wie ohne Kalender). Liefert true, wenn sich etwas geändert hat. */
export function setWeekCalendar(cal: WeekCalendar | null): boolean {
  const same = (!cal && !calendarState) || (!!cal && !!calendarState && cal.iso === calendarState.iso && cal.firstMonday === calendarState.firstMonday && cal.weeks === calendarState.weeks);
  if (same) return false;
  calendarState = cal;
  calendarVersion++;
  calendarListeners.forEach((fn) => fn());
  return true;
}

export function getWeekCalendar(): WeekCalendar | null {
  return calendarState;
}

/** Zähler, der sich mit jedem neuen Kalender erhöht (für `useSyncExternalStore`). */
export function weekCalendarVersion(): number {
  return calendarVersion;
}

export function subscribeWeekCalendar(fn: () => void): () => void {
  calendarListeners.add(fn);
  return () => calendarListeners.delete(fn);
}

function kwMode(): WeekCalendar | null {
  return calendarState?.iso && isValidISO(calendarState.firstMonday) ? calendarState : null;
}

/** „KW“ im KW-Modus, sonst „Woche“. */
export function weekWord(): string {
  return kwMode() ? 'KW' : 'Woche';
}

/** Anzeigenummer der laufenden Woche `w`: ISO-KW im KW-Modus, sonst `w`. */
export function weekNumberOf(w: number): number {
  const cal = kwMode();
  return cal ? isoWeekNumber(addDays(cal.firstMonday, 7 * (w - 1))) : w;
}

/** Folgt die Anzeige von `b` unmittelbar auf `a` (an der Jahresgrenze 52/53 → 1 nicht)? */
function weekFollows(a: number, b: number): boolean {
  return b === a + 1 && weekNumberOf(b) === weekNumberOf(a) + 1;
}

/**
 * Laufende Woche zur eingegebenen Nummer (KW im KW-Modus): `null`, wenn es sie im Schuljahr nicht gibt (z. B. KW 53 in
 * einem 52-Wochen-Jahr). Bei doppelt vorkommender KW (53-Wochen-Schuljahr) gilt für „ab“ die erste, für „bis“ (`last`) die letzte.
 */
export function weekFromNumber(n: number, last = false): number | null {
  const cal = kwMode();
  if (!cal) return Number.isInteger(n) && n >= 1 && n <= MAX_WEEKS ? n : null;
  let hit: number | null = null;
  for (let w = 1; w <= cal.weeks; w++) {
    if (weekNumberOf(w) === n) {
      if (!last) return w;
      hit = w;
    }
  }
  return hit;
}

function clampInt(n: unknown, lo: number, hi: number, fallback: number): number {
  const v = typeof n === 'number' ? n : Number(n);
  if (!Number.isFinite(v)) return fallback;
  return Math.min(hi, Math.max(lo, Math.trunc(v)));
}

/** Wochenangabe eines Eigentümers: ausgewählte Wochen oder Rhythmus (beides leer = jede Woche). */
export interface WeekSpec {
  weeks?: readonly number[] | null;
  rhythm?: WeekRhythm | null;
}

// ============================================================================================== Wochenlisten

/** Sortiert, eindeutig, nur ganze Zahlen 1 … 53; „alle Wochen“ wird zur leeren Liste. */
export function normalizeWeeks(weeks: readonly number[] | null | undefined): number[] {
  const out = [...new Set((weeks ?? []).filter((w) => Number.isInteger(w) && w >= 1 && w <= MAX_WEEKS))].sort((a, b) => a - b);
  return out.length >= MAX_WEEKS ? [] : out;
}

/** „1–4, 9“ (laufende Wochen; Bereiche ab drei aufeinanderfolgenden Wochen). */
export function weekListText(weeks: readonly number[]): string {
  const s = [...new Set(weeks)].filter((w) => Number.isInteger(w) && w >= 1).sort((a, b) => a - b);
  const out: string[] = [];
  let i = 0;
  while (i < s.length) {
    let j = i;
    while (j + 1 < s.length && weekFollows(s[j] as number, s[j + 1] as number)) j++;
    const a = weekNumberOf(s[i] as number);
    const b = weekNumberOf(s[j] as number);
    if (j - i >= 2) out.push(`${a}–${b}`);
    else for (let k = i; k <= j; k++) out.push(String(weekNumberOf(s[k] as number)));
    i = j + 1;
  }
  return out.join(', ');
}

/**
 * Kürzester Text einer Wochenliste (wie `weeks.describe`): leer → „jede Woche“, sonst „Woche 1–4, 9“ bzw.
 * „jede 3. Woche ab Woche 2“ (arithmetische Folge ab vier Wochen mit Abstand ≥ 2).
 */
export function describeWeeks(weeks: readonly number[] | null | undefined): string {
  const w = normalizeWeeks(weeks);
  if (!w.length) return 'jede Woche';
  const word = weekWord();
  let text = `${word} ${weekListText(w)}`;
  if (w.length >= 4) {
    const step = (w[1] as number) - (w[0] as number);
    if (step >= 2 && w.every((x, i) => i === 0 || x - (w[i - 1] as number) === step)) {
      const last = w[w.length - 1] as number;
      const head = `jede ${step}. Woche ab ${word} ${weekNumberOf(w[0] as number)}`;
      const rhythm = last + step > MAX_WEEKS ? head : `${head} bis ${word} ${weekNumberOf(last)}`;
      if (rhythm.length < text.length) text = rhythm;
    }
  }
  return text;
}

/** Vorschau „Woche 2, 5, 8 … (18 von 52)“ für eine konkrete (nicht leere) Liste laufender Wochen. */
export function weeksPreview(weeks: readonly number[], total: number): string {
  const s = [...new Set(weeks)].sort((a, b) => a - b);
  if (!s.length) return `Keine Woche (0 von ${total})`;
  const head = s.slice(0, 3);
  return `${weekWord()} ${head.map(weekNumberOf).join(', ')}${s.length > 3 ? ' …' : ''} (${s.length} von ${total})`;
}

/** Fehler einer Wochenliste (wie `weeks.errors`). */
export function weeksErrors(weeks: readonly number[]): string[] {
  return weeks.some((w) => !Number.isInteger(w) || w < 1 || w > MAX_WEEKS) || weeks.length > MAX_WEEKS
    ? [`Wochen: nur 1 bis ${MAX_WEEKS} möglich.`]
    : [];
}

/**
 * Laufende Wochen → Wochenangabe (wie `weeks.spec_from_weeks`): alle Wochen → leer; mindestens drei Wochen mit gleichem
 * Abstand ab 2 → Rhythmus (`to_week` 0, wenn er bis zur letzten Woche `last` reicht); sonst die Wochenliste.
 */
export function specFromWeeks(weeks: readonly number[], total = MAX_WEEKS, last = MAX_WEEKS): { weeks: number[]; rhythm: WeekRhythm | null } {
  const ls = [...new Set(weeks)].filter((w) => Number.isInteger(w) && w >= 1 && w <= MAX_WEEKS).sort((a, b) => a - b);
  if (ls.length >= total) return { weeks: [], rhythm: null };
  if (ls.length >= 3) {
    const step = (ls[1] as number) - (ls[0] as number);
    if (step >= 2 && ls.every((x, i) => i === 0 || x - (ls[i - 1] as number) === step)) {
      const end = ls[ls.length - 1] as number;
      return { weeks: [], rhythm: { every: step, from_week: ls[0] as number, to_week: end + step > last ? 0 : end } };
    }
  }
  return { weeks: ls, rhythm: null };
}

// ============================================================================================== Rhythmus

/** „jede 2. Woche ab Woche 10 bis Woche 30“ (laufende Wochen). */
export function describeRhythm(r: WeekRhythm): string {
  const word = weekWord();
  const head = r.every > 1 ? `jede ${r.every}. Woche` : 'jede Woche';
  const from = r.from_week > 1 || r.every > 1 ? ` ab ${word} ${weekNumberOf(r.from_week)}` : '';
  const to = r.to_week ? ` bis ${word} ${weekNumberOf(r.to_week)}` : '';
  return `${head}${from}${to}`;
}

/** Ist der Rhythmus in der laufenden Woche `weekNo` aktiv? */
export function rhythmActive(r: WeekRhythm, weekNo: number): boolean {
  if (weekNo < r.from_week) return false;
  if (r.to_week && weekNo > r.to_week) return false;
  return (weekNo - r.from_week) % Math.max(1, r.every) === 0;
}

/** Gilt die Wochenangabe in der laufenden Woche `weekNo`? Ohne `weekNo` (unbekannt) gilt sie. */
export function specActive(sel: WeekSpec, weekNo?: number | null): boolean {
  if (weekNo === undefined || weekNo === null) return true;
  if (sel.rhythm) return rhythmActive(sel.rhythm, weekNo);
  return !sel.weeks?.length || sel.weeks.includes(weekNo);
}

/** Aktive laufende Wochen 1 … total (1-basiert). */
export function selectionWeeks(sel: WeekSpec, total: number): number[] {
  const out: number[] = [];
  for (let l = 1; l <= total; l++) if (specActive(sel, l)) out.push(l);
  return out;
}

export function rhythmErrors(r: Partial<WeekRhythm>, maxWeek = MAX_WEEKS): string[] {
  const errs: string[] = [];
  const every = Number(r.every);
  const from = Number(r.from_week);
  const to = r.to_week === undefined ? 0 : Number(r.to_week);
  if (!Number.isInteger(every) || every < 1 || every > maxWeek) errs.push(`Rhythmus: Abstand 1 bis ${maxWeek}.`);
  if (!Number.isInteger(from) || from < 1 || from > maxWeek || !Number.isInteger(to) || to < 0 || to > maxWeek)
    errs.push(`Wochen: nur 1 bis ${maxWeek} möglich.`);
  else if (to && to < from) errs.push('„Bis Woche“ liegt vor „Ab Woche“.');
  return errs;
}

/** Text einer Wochenangabe (Regel, Kurs, Stunde, Zeitfenster, Aufsicht): Rhythmus vor Wochenliste. */
export function describeSelection(sel: WeekSpec): string {
  if (sel.rhythm) return describeRhythm(sel.rhythm);
  return describeWeeks(sel.weeks ?? []);
}

// ============================================================================================== Unterrichtstage

/** Unterrichtstage der Schule (0 = Mo … 6 = So): `school_days`, sonst die ersten `days` Tage. */
export function schoolDaysOf(st: Pick<Settings, 'days' | 'school_days'> | null | undefined): number[] {
  const list = (st?.school_days ?? []).filter((d) => Number.isInteger(d) && d >= 0 && d <= 6);
  if (list.length) return [...new Set(list)].sort((a, b) => a - b);
  return Array.from({ length: clampInt(st?.days ?? 5, 1, 7, 5) }, (_, i) => i);
}

/** Unterrichtstage einer Klasse (leer = Schulvorgabe). */
export function classDaysOf(
  cls: { school_days?: readonly number[] | null } | null | undefined,
  st: Pick<Settings, 'days' | 'school_days'> | null | undefined,
): number[] {
  const own = (cls?.school_days ?? []).filter((d) => Number.isInteger(d) && d >= 0 && d <= 6);
  return own.length ? [...new Set(own)].sort((a, b) => a - b) : schoolDaysOf(st);
}

/** „Mo–Fr“, „Mo, Di, Sa“, „Mo–Mi, Fr“ (Bereiche ab drei Tagen). */
export function daysText(days: readonly number[]): string {
  const s = [...new Set(days)].filter((d) => d >= 0 && d <= 6).sort((a, b) => a - b);
  if (!s.length) return '–';
  const out: string[] = [];
  let i = 0;
  while (i < s.length) {
    let j = i;
    while (j + 1 < s.length && (s[j + 1] as number) === (s[j] as number) + 1) j++;
    if (j - i >= 2) out.push(`${WEEKDAYS_SHORT[s[i] as number]}–${WEEKDAYS_SHORT[s[j] as number]}`);
    else for (let k = i; k <= j; k++) out.push(WEEKDAYS_SHORT[s[k] as number] as string);
    i = j + 1;
  }
  return out.join(', ');
}

/** Chips „Mo … So“ mit vollem Namen für Bildschirmleser. */
export const DAY_CHIPS: readonly { day: number; short: string; name: string }[] = WEEKDAYS_SHORT.map((short, day) => ({
  day,
  short,
  name: WEEKDAYS[day] as string,
}));

/** Sortierwert einer Wochenangabe (numerisch, U-84): jede Woche zuerst, dann nach erster Woche und Anzahl. */
export function weeksSortValue(sel: WeekSpec): number {
  if (sel.rhythm) return sel.rhythm.from_week * 100 + Math.max(0, 99 - sel.rhythm.every);
  const w = sel.weeks ?? [];
  return w.length ? Math.min(...w) * 100 + w.length : -1;
}

/** Kopfzeile der Klasse: „Mo–Fr“ bzw. „Eigene Tage · Mo, Di, Sa“. */
export function classPlanningText(
  cls: { school_days?: readonly number[] | null } | null | undefined,
  st: Pick<Settings, 'days' | 'school_days'> | null | undefined,
): string {
  const own = (cls?.school_days ?? []).length > 0;
  return `${own ? 'Eigene Tage · ' : ''}${daysText(classDaysOf(cls, st))}`;
}

// ============================================================================================== Wochen im Schuljahr

/** Woche des Schuljahres, in der `iso` liegt (oder `undefined` außerhalb). */
export function weekOfDate(year: Pick<SchoolYear, 'weeks'> | null | undefined, iso: string): SchoolYearWeek | undefined {
  if (!year || !isValidISO(iso)) return undefined;
  const monday = mondayOf(iso);
  return year.weeks.find((w) => w.week_start === monday);
}

/** „02.11.–08.11.“ */
export function weekRangeText(weekStart: string, weekEnd?: string): string {
  const end = weekEnd && isValidISO(weekEnd) ? weekEnd : addDays(weekStart, 6);
  return `${formatDayMonth(weekStart)}–${formatDayMonth(end)}`;
}

/** Eintrag der Wochenauswahl: „Woche 10 · KW 45 · 02.11.–08.11. · Ferien“ (KW-Modus ohne „Woche“). */
export function weekOptionLabel(w: SchoolYearWeek, numbering: WeekNumbering = 'school_year'): string {
  const head = numbering === 'iso' ? `KW ${w.iso_week}` : `Woche ${w.week_no} · KW ${w.iso_week}`;
  return `${head} · ${weekRangeText(w.week_start, w.week_end)}${w.holiday_week ? ' · Ferien' : ''}`;
}

/** Anzeige einer Woche ohne Schuljahresdaten (Altserver, außerhalb des Schuljahres): „KW 41 · 05.10.–11.10.“ */
export function plainWeekText(iso: string): string {
  const monday = mondayOf(iso);
  return `KW ${isoWeekNumber(monday)} · ${weekRangeText(monday)}`;
}

/** Text der Woche: `week_text` vom Server, sonst KW und Zeitraum. */
export function weekText(info: Pick<WeekInfo, 'week_text'> | null | undefined, iso: string): string {
  return info?.week_text || plainWeekText(iso);
}

/** Ferienbadge der Woche: Name der Ferien bzw. „Ferien“; leer, wenn keine Ferienwoche. */
export function holidayBadge(info: Pick<WeekInfo, 'holiday_week' | 'holiday_name'> | null | undefined): string {
  if (!info?.holiday_week) return '';
  return info.holiday_name || 'Ferien';
}

/**
 * Woche aus der Adresse (§14.1 W6, §15.2 V11): `?datum=JJJJ-MM-TT` ist kanonisch, `?woche=L` heißt laufende Woche
 * des aktuellen Schuljahres. Alte Links mit `woche=0` zeigen die aktuelle Woche.
 */
export function weekQueryFromSearch(search: URLSearchParams): { date?: string; week_no?: number } {
  const datum = search.get('datum');
  // streng: 2026-13-40 wäre für `Date` ein gültiger Tag im Folgejahr
  if (isValidISO(datum) && toISO(parseISO(datum)) === datum) return { date: mondayOf(datum) };
  const woche = Number(search.get('woche'));
  if (Number.isInteger(woche) && woche >= 1 && woche <= MAX_WEEKS) return { week_no: woche };
  return {};
}

/** Liegt der Montag `monday` in der Woche von heute? */
export function isCurrentWeek(monday: string, today: string): boolean {
  return mondayOf(monday) === mondayOf(today);
}

// ============================================================================================== Tage und Ferien

/** Tag ohne Unterricht der Klasse (Sa/So schmal und abgeblendet, §16 E2). */
export function isOffDay(d: Pick<DayInfo, 'day_kind'> | { day_kind?: DayKind } | null | undefined): boolean {
  return d?.day_kind === 'kein_unterrichtstag';
}

export const HOLIDAY_KIND_LABELS: Record<HolidayKind, string> = {
  ferien: 'Ferien',
  feiertag: 'Feiertag',
  beweglich: 'Beweglicher Ferientag',
  schulfrei: 'Unterrichtsfrei',
};

/** Ferienart (Lesepfad V15: fehlt `kind`, gilt „ferien“, wenn der Name „ferien“ enthält, sonst „feiertag“). */
export function holidayKindOf(h: Pick<Holiday, 'name' | 'kind'>): HolidayKind {
  if (h.kind && h.kind in HOLIDAY_KIND_LABELS) return h.kind;
  return /ferien/i.test(h.name ?? '') ? 'ferien' : 'feiertag';
}

/** Datum vor/nach dem Schuljahr? (für Warnungen in der Oberfläche) */
export function dateInYear(year: Pick<SchoolYear, 'start' | 'end'> | null | undefined, iso: string): boolean {
  if (!year || !isValidISO(iso) || !isValidISO(year.start) || !isValidISO(year.end)) return false;
  const t = parseISO(iso).getTime();
  return t >= parseISO(year.start).getTime() && t <= parseISO(year.end).getTime();
}

/**
 * Ende und Wochenzahl eines Schuljahres für die Anzeige eines noch nicht gespeicherten Beginns (W3): Sonntag vor der
 * Woche von „Beginn + 1 Jahr“. Maßgeblich bleibt die Antwort des Servers (`GET /calendar/school-year`).
 */
export function schoolYearSpan(start: string): { end: string; weeks: number } | null {
  if (!isValidISO(start)) return null;
  const d = parseISO(start);
  const next = toISO(new Date(d.getFullYear() + 1, d.getMonth(), d.getDate(), 12));
  const first = mondayOf(start);
  const nextMonday = mondayOf(next);
  const weeks = Math.round((parseISO(nextMonday).getTime() - parseISO(first).getTime()) / (7 * 86_400_000));
  return { end: addDays(nextMonday, -1), weeks };
}

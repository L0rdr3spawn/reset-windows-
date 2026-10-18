/**
 * Reine Hilfsfunktionen der Klassen-Seite (ohne React, getestet in classes.test.ts):
 * Kalenderwoche, Klassenliste, Zellen des Wochenplans zusammenführen und einordnen, verständliche Texte für die
 * Vorschau der automatischen Umstellung, Prüfungen und Anfragekörper der Dialoge.
 */
import { addDays, isoWeekNumber, isValidISO, mondayOf, parseISO } from '../../lib/dates';
import { collator, matchesQuery } from '../../lib/format';
import { kindInfo } from '../../lib/substitution';
import type {
  ClassListItem,
  ClassStudent,
  ClassSubject,
  ClassTeacher,
  NotTakingPlaceBody,
  PreviewChange,
  PreviewDay,
  RoomChoice,
  WeekAbsence,
  WeekCell,
} from './types';

const DAY_MS = 86_400_000;

function pad(n: number): string {
  return n < 10 ? `0${n}` : String(n);
}

/** „05.10.“ */
function dayMonth(iso: string): string {
  const d = parseISO(iso);
  return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.`;
}

/** „3. Std.“ */
/** Akkusativ nach „durch“: „Herr Sommer“ → „Herrn Sommer“ (Frau/Kürzel unverändert). */
export function accusative(name: string): string {
  return name.replace(/^Herr /, 'Herrn ');
}

export function periodText(p: number): string {
  return `${p + 1}. Std.`;
}

// ============================================================================================== Kalenderwoche

/** ISO-Kalenderwoche – seit R3 in `lib/dates.ts` (hier für bestehende Aufrufer weitergereicht). */
export { isoWeekNumber };

/** Montag der Woche, `n` Wochen vor (negativ) bzw. nach dem Datum. */
export function shiftWeek(iso: string, n: number): string {
  return addDays(mondayOf(iso), 7 * n);
}

/** Schultage der Woche ab Montag. */
export function weekDates(monday: string, days = 5): string[] {
  return Array.from({ length: Math.max(1, days) }, (_, i) => addDays(monday, i));
}

/** Liegt `iso` in der Woche ab `monday` (Mo–So)? */
export function inWeek(monday: string, iso: string): boolean {
  return mondayOf(iso) === mondayOf(monday);
}

export interface WeekTitle {
  kw: number;
  /** „05.10.–11.10.2026“ */
  range: string;
  /** „Woche 6 · KW 41 · 05.10.–11.10.2026“ (ohne Text vom Server: „KW 41 · 05.10.–11.10.2026“) */
  label: string;
}

/**
 * Titel der Woche. Mit `weekText` (`week_info.week_text` vom Server) wird der Zeitraum hinter die KW gesetzt; ohne
 * ihn stehen nur KW und Zeitraum.
 */
export function weekTitle(weekStart: string, days = 7, weekText?: string | null): WeekTitle {
  const monday = mondayOf(weekStart);
  const last = addDays(monday, Math.max(1, days) - 1);
  const kw = isoWeekNumber(monday);
  const range = `${dayMonth(monday)}–${dayMonth(last)}${parseISO(last).getFullYear()}`;
  if (weekText) {
    const parts = weekText.split(' · ');
    const at = parts.findIndex((p) => p.startsWith('KW '));
    parts.splice(at >= 0 ? at + 1 : parts.length, 0, range);
    return { kw, range, label: parts.join(' · ') };
  }
  return { kw, range, label: `KW ${kw} · ${range}` };
}

// ============================================================================================== Klassenliste

export function gradeLabel(grade: number | null | undefined): string {
  return grade ? `Klassenstufe ${grade}` : 'Ohne Klassenstufe';
}

/** Suche über Klasse, Klassenleitung und Klassenraum (zusätzlich zur Suche im Backend, damit die Liste sofort reagiert). */
export function filterClasses(list: readonly ClassListItem[], q: string, site = ''): ClassListItem[] {
  return list.filter(
    (c) =>
      (!site || c.site === site) &&
      matchesQuery(`${c.name} ${c.id} ${c.class_teacher?.name ?? ''} ${c.home_room?.name ?? ''} ${c.site_name ?? ''}`, q),
  );
}

export interface GradeGroup {
  grade: number;
  label: string;
  classes: ClassListItem[];
}

/** Nach Jahrgang gruppiert (aufsteigend, „Ohne Jahrgang“ zuletzt), innerhalb natürlich sortiert (5a < 5b < 10a). */
export function groupByGrade(list: readonly ClassListItem[]): GradeGroup[] {
  const map = new Map<number, ClassListItem[]>();
  for (const c of list) {
    const g = c.grade || 0;
    const arr = map.get(g) ?? [];
    arr.push(c);
    map.set(g, arr);
  }
  return [...map.entries()]
    .sort(([a], [b]) => (a || 99) - (b || 99))
    .map(([grade, classes]) => ({ grade, label: gradeLabel(grade), classes: classes.slice().sort((x, y) => collator.compare(x.name, y.name)) }));
}

/** „28 Schüler/innen · 12 Kurse · 9 Lehrkräfte“ */
export function countsText(c: Pick<ClassListItem, 'student_count' | 'course_count' | 'teacher_count'>): string {
  const n = (v: number, one: string, many: string) => `${v} ${v === 1 ? one : many}`;
  return [n(c.student_count, 'Schüler/in', 'Schüler/innen'), n(c.course_count, 'Kurs', 'Kurse'), n(c.teacher_count, 'Lehrkraft', 'Lehrkräfte')].join(' · ');
}

// ============================================================================================== Status einer Zelle

export type StatusKey = 'vertretung' | 'betreuung' | 'mitbetreuung' | 'entfall' | 'verlegt' | 'raum' | 'klasse_abwesend' | 'klausur' | 'geaendert';

export interface StatusInfo {
  label: string;
  /** Kurzzeichen, damit der Status nicht nur über Farbe erkennbar ist */
  short: string;
  /** CSS-Klasse der Vertretungsarten (`k-*` aus styles/app.css) */
  cls: string;
  description: string;
}

export const STATUS_INFO: Record<StatusKey, StatusInfo> = {
  vertretung: { label: 'Vertretung', short: 'V', cls: 'k-vertretung', description: 'Eine andere Lehrkraft übernimmt den Unterricht.' },
  betreuung: { label: 'Betreuung', short: 'B', cls: 'k-betreuung', description: 'Fachfremde Betreuung der Klasse.' },
  mitbetreuung: { label: 'Mitbetreuung', short: 'MB', cls: 'k-mitbetreuung', description: 'Die Klasse wird von einer benachbarten Lerngruppe mitbetreut.' },
  entfall: { label: 'Entfall', short: 'E', cls: 'k-entfall', description: 'Die Stunde fällt aus.' },
  verlegt: { label: 'Verlegt', short: 'VL', cls: 'k-verlegung', description: 'Die Stunde findet zu einer anderen Zeit statt.' },
  raum: { label: 'Raum', short: 'R', cls: 'k-raum', description: 'Der Unterricht findet in einem anderen Raum statt.' },
  klasse_abwesend: { label: 'Klasse abwesend', short: 'KA', cls: 'k-abwesend', description: 'Die Klasse ist nicht im Haus (z. B. Exkursion).' },
  klausur: { label: 'Klausur', short: 'K', cls: 'k-klausur', description: 'Klassenarbeit/Klausur in dieser Stunde.' },
  geaendert: { label: 'Geändert', short: '!', cls: 'k-sonst', description: 'Gegenüber dem regulären Plan geändert.' },
};

/** Reihenfolge = Wichtigkeit (für Rahmenfarbe eines zusammengefassten Blocks). */
const STATUS_RANK: StatusKey[] = ['entfall', 'klasse_abwesend', 'verlegt', 'vertretung', 'betreuung', 'mitbetreuung', 'raum', 'klausur', 'geaendert'];

function status(c: Pick<WeekCell, 'status'>): string {
  return (c.status || 'normal').toLowerCase();
}

/** Fällt die Stunde für die Klasse aus (Entfall, alte Position einer Verlegung, Klasse abwesend)? */
export function isCancelled(c: Pick<WeekCell, 'status'>): boolean {
  return status(c) === 'entfall';
}

/** Ausfall durch „Unterricht findet nicht statt“ (§10.1)? */
export function isDropped(c: Pick<WeekCell, 'dropped' | 'note'>): boolean {
  return !!c.dropped || /unterricht entf(ä|ae)llt/i.test(c.note || '');
}

/** Alle Änderungen einer Zelle als Text-Badges (leer = regulär). */
export function cellBadges(c: WeekCell): StatusKey[] {
  const out: StatusKey[] = [];
  const add = (k: StatusKey) => {
    if (!out.includes(k)) out.push(k);
  };
  const k = c.kind ?? '';
  const st = status(c);
  if (k === 'verlegung') add('verlegt');
  else if (k === 'klasse_abwesend') add('klasse_abwesend');
  else if (k === 'entfall') add('entfall');
  else if (k === 'vertretung' || k === 'betreuung' || k === 'mitbetreuung') add(k);
  else if (k === 'raumaenderung') add('raum');
  if (st === 'entfall' && !out.length) add('entfall');
  if (!isCancelled(c)) {
    if (c.original_teacher && c.original_teacher !== c.teacher && !out.some((x) => x === 'vertretung' || x === 'betreuung' || x === 'mitbetreuung'))
      add('vertretung');
    if (c.original_room && c.original_room !== c.room) add('raum');
  }
  if (c.exam) add('klausur');
  if (!out.length && st !== 'normal') add('geaendert');
  return out;
}

/** Kann für diese Zelle „findet nicht statt“ eingetragen werden? (regulärer oder vertretener Unterricht eines Kurses) */
export function canMarkCell(c: WeekCell): boolean {
  const st = status(c);
  return !!c.course_id && st !== 'entfall' && st !== 'neu' && c.kind !== 'aufsicht' && c.kind !== 'klasse_abwesend';
}

// ============================================================================================== Zellen zusammenführen

/** Ein Block im Raster: eine Stunde eines Kurses; gekoppelte Kursteile (gleiche Stunde, gleiche `lesson_id`) zusammengefasst. */
export interface SlotItem {
  key: string;
  period: number;
  lessonId: string | null;
  courseId: string | null;
  /** Kursteile (≥ 1), nach Teil sortiert */
  cells: WeekCell[];
  coupled: boolean;
  /** alle Änderungen (eindeutig) */
  badges: StatusKey[];
  /** wichtigste Änderung (Farbe/Rahmen) */
  main: StatusKey | null;
  /** alle Teile fallen aus */
  cancelled: boolean;
  dropped: boolean;
  /** „findet nicht statt“ möglich */
  markable: boolean;
}

export function mainStatus(badges: readonly StatusKey[]): StatusKey | null {
  for (const k of STATUS_RANK) if (badges.includes(k)) return k;
  return null;
}

/** Zellen eines Tages → Blöcke (sortiert nach Stunde; stattfindender Unterricht vor ausfallendem). */
export function mergeCells(cells: readonly WeekCell[]): SlotItem[] {
  const groups = new Map<string, WeekCell[]>();
  cells.forEach((c, i) => {
    if (c.kind === 'aufsicht') return;
    const key = c.lesson_id ? `${c.period}|${c.lesson_id}|${status(c) === 'neu' ? 'neu' : ''}` : `${c.period}|#${i}`;
    const arr = groups.get(key) ?? [];
    arr.push(c);
    groups.set(key, arr);
  });
  const items: SlotItem[] = [];
  for (const [key, list] of groups) {
    const parts = list.slice().sort((a, b) => (a.part ?? 0) - (b.part ?? 0));
    const badges: StatusKey[] = [];
    for (const c of parts) for (const b of cellBadges(c)) if (!badges.includes(b)) badges.push(b);
    const first = parts[0] as WeekCell;
    items.push({
      key,
      period: first.period,
      lessonId: first.lesson_id ?? null,
      courseId: first.course_id ?? null,
      cells: parts,
      coupled: parts.length > 1,
      badges,
      main: mainStatus(badges),
      cancelled: parts.every(isCancelled),
      dropped: parts.some(isDropped),
      markable: parts.some(canMarkCell),
    });
  }
  return items.sort((a, b) => a.period - b.period || Number(a.cancelled) - Number(b.cancelled) || a.key.localeCompare(b.key));
}

/** Blöcke je Stunde (Index = Stunde) für das Raster. */
export function slotsByPeriod(items: readonly SlotItem[], rows: number): SlotItem[][] {
  const out: SlotItem[][] = Array.from({ length: Math.max(0, rows) }, () => []);
  for (const it of items) out[it.period]?.push(it);
  return out;
}

/** Zeilen des Rasters: bis zur letzten belegten Stunde der Woche (ohne Unterricht: alle Stunden). */
export function rowCount(days: readonly { cells: readonly Pick<WeekCell, 'period'>[] }[], periods: number): number {
  let last = -1;
  for (const d of days) for (const c of d.cells) last = Math.max(last, c.period);
  return last >= 0 ? last + 1 : Math.max(1, periods);
}

/** Stunden, in denen der Kurs an diesem Tag Unterricht hat, der ausfallen kann. */
export function coursePeriods(cells: readonly WeekCell[], courseId: string): number[] {
  return [...new Set(cells.filter((c) => c.course_id === courseId && canMarkCell(c)).map((c) => c.period))].sort((a, b) => a - b);
}

/** Stunden desselben Blocks (Doppelstunde) – Vorauswahl im Dialog. */
export function blockPeriods(cells: readonly WeekCell[], lessonId: string | null, period: number): number[] {
  if (!lessonId) return [period];
  const ps = [...new Set(cells.filter((c) => c.lesson_id === lessonId && canMarkCell(c)).map((c) => c.period))].sort((a, b) => a - b);
  return ps.length ? ps : [period];
}

// ============================================================================================== Namen

/** Auflösung von IDs (Fach/Lehrkraft/Raum) in Anzeigenamen – unbekannte IDs bleiben stehen. */
export interface NameLookup {
  subject: (id: string | null | undefined) => string;
  teacher: (id: string | null | undefined) => string;
  room: (id: string | null | undefined) => string;
}

export const RAW_NAMES: NameLookup = {
  subject: (id) => id ?? '',
  teacher: (id) => id ?? '',
  room: (id) => id ?? '',
};

export function makeNames(maps: { subjects?: Map<string, string>; teachers?: Map<string, string>; rooms?: Map<string, string> }): NameLookup {
  const get = (m: Map<string, string> | undefined) => (id: string | null | undefined) => (id ? m?.get(id) || id : '');
  return { subject: get(maps.subjects), teacher: get(maps.teachers), room: get(maps.rooms) };
}

/** Text für Bildschirmleser/Tooltip eines Blocks. */
export function slotText(it: SlotItem, names: NameLookup, time?: string): string {
  const head = `${periodText(it.period)}${time ? ` (${time})` : ''}`;
  const parts = it.cells.map((c) => {
    const bits = [names.subject(c.subject) || 'Unterricht'];
    if (c.teacher) bits.push(`Lehrkraft ${names.teacher(c.teacher)}${c.original_teacher && c.original_teacher !== c.teacher ? ` statt ${names.teacher(c.original_teacher)}` : ''}`);
    if (c.room) bits.push(`Raum ${names.room(c.room)}${c.original_room && c.original_room !== c.room ? ` statt ${names.room(c.original_room)}` : ''}`);
    const badges = cellBadges(c).map((b) => STATUS_INFO[b].label);
    if (badges.length) bits.push(badges.join(', '));
    if (c.exam) bits.push(c.exam);
    if (c.note) bits.push(c.note);
    return bits.join(', ');
  });
  return `${head}: ${it.coupled ? `${it.cells.length} Kursteile – ` : ''}${parts.join('; ')}`;
}

// ============================================================================================== Vorschau-Texte

export interface ChangeLine {
  key: string;
  /** Entry-Art (für das Badge) */
  kind: string;
  text: string;
  classes: string[];
  /** Eintrag mit Warnung (z. B. keine Vertretung gefunden) */
  warning: boolean;
}

/** Herkunftsstunde einer Verlegung (Feld oder „… aus der 6. Stunde …“ in der Notiz), 0-basiert. */
export function movedFrom(c: Pick<PreviewChange, 'moved_from' | 'note'>): number | null {
  if (typeof c.moved_from === 'number') return c.moved_from;
  const m = /aus der (\d+)\.\s*(Stunde|Std)/i.exec(c.note || '');
  return m ? parseInt(m[1] as string, 10) - 1 : null;
}

function overlaps(a: readonly string[], b: readonly string[]): boolean {
  return a.length === 0 || b.length === 0 || a.some((x) => b.includes(x));
}

/**
 * Notiz eines Eintrags zerlegen: führendes „Entfall“ / „Unterricht entfällt (Grund)“ entfernen (sagt der Satz
 * schon), Grund und Rest getrennt zurückgeben.
 */
export function parseNote(note: string): { dropped: boolean; reason: string; rest: string } {
  const lead = /^\s*(entfall|unterricht entf(?:ä|ae)llt)(?:\s*\(([^)]*)\))?\s*(?:[–:-]\s*)?/i;
  let s = note || '';
  let dropped = false;
  let reason = '';
  for (let i = 0; i < 3; i++) {
    const m = lead.exec(s);
    if (!m) break;
    if (/^unterricht/i.test(m[1] ?? '')) dropped = true;
    if (m[2]?.trim()) reason = m[2].trim();
    s = s.slice(m[0].length);
  }
  return { dropped, reason, rest: s.trim() };
}

function whenWord(from: number, to: number): string {
  return from > to ? 'vorgezogen' : 'nach hinten verlegt';
}

/**
 * Verständliche Sätze für die Änderungen eines Tages, z. B.
 * „Mathe 3. Std. entfällt – dafür wird Deutsch aus der 6. Std. vorgezogen“.
 * Entfall und Verlegung in dieselbe Stunde (gleiche Klasse) werden zu einem Satz zusammengefasst.
 * Entfallender Unterricht (§10.1, `dropped` bzw. Notiz „Unterricht entfällt …“), der betreut/vertreten wird,
 * heißt „Mathe 3. Std. entfällt – Betreuung durch …“.
 * Betrifft eine Änderung andere Klassen als `ownClass`, steht die Klasse vorn („7b: …“).
 */
export function describeChanges(changes: readonly PreviewChange[], names: NameLookup = RAW_NAMES, ownClass?: string): ChangeLine[] {
  const list = changes.map((c, i) => ({ c, i })).sort((a, b) => a.c.period - b.c.period || a.i - b.i);
  // erst Paare bilden: Entfall ↔ Verlegung in dieselbe Stunde derselben Klasse(n)
  const partnerOf = new Map<number, PreviewChange>();
  const paired = new Set<number>();
  for (const { c, i } of list) {
    if (c.kind !== 'entfall' || c.op === 'removed') continue;
    const v = list.find((x) => !paired.has(x.i) && x.c.kind === 'verlegung' && x.c.op !== 'removed' && x.c.period === c.period && overlaps(x.c.classes, c.classes));
    if (v) {
      paired.add(v.i);
      partnerOf.set(i, v.c);
    }
  }
  const out: ChangeLine[] = [];
  const subj = (c: PreviewChange) => names.subject(c.subject) || 'Unterricht';
  const prefix = (c: PreviewChange) =>
    c.classes.length && !(ownClass && c.classes.length === 1 && c.classes[0] === ownClass) ? `${c.classes.join(', ')}: ` : '';

  for (const { c, i } of list) {
    if (paired.has(i)) continue;
    const p = periodText(c.period);
    const note = parseNote(c.note);
    const dropped = !!c.dropped || note.dropped;
    const why = note.reason ? ` (${note.reason})` : '';
    // „Mathe 3. Std.:“ bzw. bei entfallendem Unterricht „Mathe 3. Std. entfällt –“
    const head = dropped ? `${subj(c)} ${p} entfällt${why} –` : `${subj(c)} ${p}:`;
    let text: string;
    switch (c.kind) {
      case 'entfall': {
        const partner = partnerOf.get(i);
        if (partner) {
          const from = movedFrom(partner);
          text =
            from === null
              ? `${subj(c)} ${p} entfällt${why} – dafür wird ${subj(partner)} in diese Stunde verlegt`
              : `${subj(c)} ${p} entfällt${why} – dafür wird ${subj(partner)} aus der ${periodText(from)} ${whenWord(from, c.period)}`;
        } else if (/^dafür\b/i.test(note.rest)) {
          text = `${subj(c)} ${p} entfällt${why} – ${note.rest}`;
        } else {
          const extra = [note.reason, note.rest].filter(Boolean).join(' – ');
          text = `${subj(c)} ${p} entfällt${extra ? ` (${extra})` : ''}`;
        }
        break;
      }
      case 'verlegung': {
        const from = movedFrom(c);
        text = from === null ? `${subj(c)} wird in die ${p} verlegt` : `${subj(c)} wird aus der ${periodText(from)} in die ${p} ${whenWord(from, c.period)}`;
        break;
      }
      case 'vertretung':
        text = c.substitute
          ? `${head} Vertretung durch ${accusative(names.teacher(c.substitute))}${c.teacher && !dropped ? ` (statt ${names.teacher(c.teacher)})` : ''}`
          : `${head} Vertretung noch offen`;
        break;
      case 'betreuung':
        text = c.substitute ? `${head} Betreuung durch ${accusative(names.teacher(c.substitute))}` : `${head} Betreuung noch offen`;
        break;
      case 'mitbetreuung':
        text = dropped
          ? `${head} Mitbetreuung${c.substitute ? ` durch ${accusative(names.teacher(c.substitute))}` : ''}`
          : `${head} wird${c.substitute ? ` von ${names.teacher(c.substitute)}` : ''} mitbetreut`;
        break;
      case 'raumaenderung':
        text = `${subj(c)} ${p}: anderer Raum${c.room ? ` – ${names.room(c.room)}` : ''}`;
        break;
      case 'klasse_abwesend':
        text = `${subj(c)} ${p}: Klasse nicht da`;
        break;
      case 'klausur':
        text = `${p}: Klausur${c.note ? ` – ${c.note}` : ''}`;
        break;
      default:
        text = `${subj(c)} ${p}: ${kindInfo(c.kind).label}${c.note ? ` – ${c.note}` : ''}`;
    }
    if (c.op === 'removed') text = `wieder wie geplant: ${text}`;
    out.push({ key: `${c.period}-${i}`, kind: c.kind, text: prefix(c) + text, classes: c.classes, warning: !!c.warning && c.op !== 'removed' });
  }
  return out;
}

export interface PreviewStats {
  changes: number;
  days: number;
  /** weitere betroffene Klassen (ohne die eigene), natürlich sortiert */
  otherClasses: string[];
}

export function previewStats(preview: readonly PreviewDay[], ownClass?: string): PreviewStats {
  const other = new Set<string>();
  let changes = 0;
  let days = 0;
  for (const d of preview) {
    if (d.changes.length) days++;
    changes += d.changes.length;
    for (const c of d.changes) for (const k of c.classes) if (k !== ownClass) other.add(k);
  }
  return { changes, days, otherClasses: [...other].sort((a, b) => collator.compare(a, b)) };
}

/** „4 Änderungen an 2 Tagen · auch betroffen: 7b, 8a“ */
export function previewStatsText(s: PreviewStats): string {
  if (!s.changes) return 'Keine Änderungen am Vertretungsplan.';
  const head = `${s.changes} ${s.changes === 1 ? 'Änderung' : 'Änderungen'} an ${s.days} ${s.days === 1 ? 'Tag' : 'Tagen'}`;
  return s.otherClasses.length ? `${head} · auch betroffen: ${s.otherClasses.join(', ')}` : head;
}

// ============================================================================================== Dialoge

/** „Höchstens 14 Tage“ (§10.2) */
export const MAX_RANGE_DAYS = 14;

/** Fehlertext für einen Zeitraum oder `null`. */
export function rangeError(from: string, to: string, max = MAX_RANGE_DAYS): string | null {
  if (!isValidISO(from)) return 'Bitte ein gültiges Startdatum wählen.';
  if (!isValidISO(to)) return 'Bitte ein gültiges Enddatum wählen.';
  const days = Math.round((parseISO(to).getTime() - parseISO(from).getTime()) / DAY_MS) + 1;
  if (days < 1) return 'Das Enddatum liegt vor dem Startdatum.';
  if (days > max) return `Höchstens ${max} Tage auf einmal – bitte den Zeitraum teilen.`;
  return null;
}

/** „Findet nicht statt“: eine Stunde (bzw. Block) eines Kurses an einem Tag. */
export function lessonBody(
  input: { date: string; periods: readonly number[]; courseId: string; part: number | null; reason: string },
  dryRun: boolean,
): NotTakingPlaceBody {
  return {
    mode: 'lesson',
    date_from: input.date,
    date_to: input.date,
    periods: [...new Set(input.periods)].sort((a, b) => a - b),
    course_id: input.courseId,
    part: input.part,
    reason: input.reason.trim(),
    dry_run: dryRun,
  };
}

/** „Klasse ist nicht da“: Zeitraum, Stunden (leer = ganztägig), Begleitlehrkräfte. */
export function classBody(
  input: { from: string; to: string; periods: readonly number[]; reason: string; escorts: readonly string[] },
  dryRun: boolean,
): NotTakingPlaceBody {
  return {
    mode: 'class',
    date_from: input.from,
    date_to: input.to < input.from ? input.from : input.to,
    periods: [...new Set(input.periods)].sort((a, b) => a - b),
    reason: input.reason.trim(),
    escort_teachers: [...new Set(input.escorts)],
    dry_run: dryRun,
  };
}

/** „3., 4. Std.“ bzw. Text für „keine Auswahl“ */
export function periodsText(periods: readonly number[] | null | undefined, none = 'ganztägig'): string {
  if (!periods?.length) return none;
  return `${[...periods].sort((a, b) => a - b).map((p) => `${p + 1}.`).join(', ')} Std.`;
}

/** Überschrift eines Ausfalls in der Wochenliste. */
export function absenceTitle(a: Pick<WeekAbsence, 'kind' | 'ref' | 'ref_name' | 'reason'>, className?: string): string {
  const name = a.ref_name || a.ref;
  switch (a.kind) {
    case 'lesson':
      return `Unterricht entfällt: ${name}`;
    case 'class':
      return `Klasse ${className || name} ist nicht da`;
    case 'teacher':
      return /^Begleitung\b/.test(a.reason ?? '') ? `Begleitung: ${name}` : `Lehrkraft abwesend: ${name}`;
    case 'room':
      return `Raum gesperrt: ${name}`;
    default:
      return name;
  }
}

/** Stunden-Text eines Ausfalls: bei `lesson` heißt „keine Auswahl“ alle Stunden des Kurses. */
export function absencePeriodsText(a: Pick<WeekAbsence, 'kind' | 'periods'>): string {
  return periodsText(a.periods, a.kind === 'lesson' ? 'alle Stunden des Kurses' : 'ganztägig');
}

/**
 * Begleitungen zu einer Klassen-Abwesenheit (Lehrkraft-Abwesenheiten „Begleitung <Klasse>“ im selben Zeitraum),
 * damit „Zurücknehmen“ sie mit entfernt – falls das Backend sie in der Wochenliste mitliefert.
 */
export function escortsOf(classAbsence: WeekAbsence, all: readonly WeekAbsence[], className: string): WeekAbsence[] {
  if (classAbsence.kind !== 'class') return [];
  // wie im Backend: „Begleitung 5a“, aber nicht „Begleitung 5a-Fahrt“/„Begleitung 5ab“
  const re = new RegExp(`^Begleitung\\s+(${escapeRe(className)}|${escapeRe(classAbsence.ref)})(?![\\w-])`);
  return all.filter(
    (a) => a.kind === 'teacher' && a.date_from === classAbsence.date_from && a.date_to === classAbsence.date_to && re.test(a.reason ?? ''),
  );
}

function escapeRe(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/** Ausfälle sortiert: nach Beginn, Klassen-Abwesenheit vor Stunden. */
export function sortAbsences<T extends Pick<WeekAbsence, 'date_from' | 'kind' | 'periods' | 'id'>>(list: readonly T[]): T[] {
  const rank: Record<string, number> = { class: 0, lesson: 1, teacher: 2, room: 3 };
  return list
    .slice()
    .sort(
      (a, b) =>
        a.date_from.localeCompare(b.date_from) ||
        (rank[a.kind] ?? 9) - (rank[b.kind] ?? 9) ||
        (a.periods[0] ?? -1) - (b.periods[0] ?? -1) ||
        String(a.id).localeCompare(String(b.id)),
    );
}

// ============================================================================================== Kopf, Lehrkräfte, Schüler/innen

/** Hinweise zur Raumwahl vor dem Speichern (die verbindlichen Warnungen kommen aus der Antwort). */
export function roomHints(room: RoomChoice | undefined, cls: { id: string; site: string }, studentCount: number): string[] {
  if (!room) return [];
  const out: string[] = [];
  const others = room.home_of.filter((c) => c !== cls.id);
  if (others.length) out.push(`ist schon Klassenraum von ${others.join(', ')}`);
  if (room.site && cls.site && room.site !== cls.site) out.push('liegt an einem anderen Standort');
  if (room.capacity && studentCount && room.capacity < studentCount) out.push(`nur ${room.capacity} Plätze für ${studentCount} Schüler/innen`);
  if (room.type && room.type !== 'Klassenraum') out.push(`Raumtyp „${room.type}“ – kein Klassenraum`);
  return out;
}

/** Hinweis zur Klassenleitung: unterrichtet die Lehrkraft die Klasse? */
export function teacherHint(teacherId: string | null | undefined, teachers: readonly Pick<ClassTeacher, 'id'>[]): string | null {
  if (!teacherId) return null;
  return teachers.some((t) => t.id === teacherId) ? null : 'unterrichtet die Klasse bisher nicht';
}

/** Klassenleitung zuerst, dann nach Name. */
export function sortTeachers<T extends Pick<ClassTeacher, 'name' | 'is_class_teacher'>>(list: readonly T[]): T[] {
  return list.slice().sort((a, b) => Number(b.is_class_teacher) - Number(a.is_class_teacher) || collator.compare(a.name, b.name));
}

export interface SubjectGroup {
  subject: string;
  name: string;
  rows: ClassSubject[];
}

/** Fach → Kurse/Kursteile (nach Fachname, dann Kursbezeichnung). */
export function groupSubjects(subjects: readonly ClassSubject[]): SubjectGroup[] {
  const map = new Map<string, SubjectGroup>();
  for (const s of subjects) {
    const g = map.get(s.subject) ?? { subject: s.subject, name: s.subject_name || s.subject, rows: [] };
    g.rows.push(s);
    map.set(s.subject, g);
  }
  const groups = [...map.values()].sort((a, b) => collator.compare(a.name, b.name));
  for (const g of groups) g.rows.sort((a, b) => collator.compare(a.label, b.label) || (a.part ?? 0) - (b.part ?? 0));
  return groups;
}

/** Partnerklassen eines gekoppelten Kurses (ohne die eigene). */
export function partnerClasses(row: Pick<ClassSubject, 'classes'>, ownClass: string): string[] {
  return row.classes.filter((c) => c !== ownClass);
}

export function filterStudents(students: readonly ClassStudent[], q: string): ClassStudent[] {
  return students.filter((s) => matchesQuery(`${s.name} ${s.courses.map((c) => c.label).join(' ')}`, q)).sort((a, b) => collator.compare(a.name, b.name));
}

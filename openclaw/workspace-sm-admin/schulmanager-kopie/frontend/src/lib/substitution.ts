/**
 * Darstellung & Filter für Vertretungsplan-Einträge (rein, testbar).
 */
import type { AbsenceKind, AbsentClassDetail, Entry, EntryKind, TeacherStat } from '../api/types';
import { addDays, mondayOf } from './dates';

export interface KindInfo {
  label: string;
  /** Kurzzeichen, damit die Art nicht nur über Farbe erkennbar ist */
  short: string;
  /** CSS-Klasse (Farben über Design-Tokens) */
  cls: string;
  description: string;
}

export const KIND_INFO: Record<EntryKind, KindInfo> = {
  vertretung: { label: 'Vertretung', short: 'V', cls: 'k-vertretung', description: 'Eine andere Lehrkraft übernimmt den Unterricht.' },
  betreuung: { label: 'Betreuung', short: 'B', cls: 'k-betreuung', description: 'Fachfremde Aufsicht/Betreuung der Klasse.' },
  entfall: { label: 'Entfall', short: 'E', cls: 'k-entfall', description: 'Die Stunde fällt aus.' },
  verlegung: { label: 'Verlegung', short: 'VL', cls: 'k-verlegung', description: 'Die Stunde findet zu einer anderen Zeit statt.' },
  raumaenderung: { label: 'Raumänderung', short: 'R', cls: 'k-raum', description: 'Der Unterricht findet in einem anderen Raum statt.' },
  mitbetreuung: { label: 'Mitbetreuung', short: 'MB', cls: 'k-mitbetreuung', description: 'Die Klasse wird von einer benachbarten Lerngruppe mitbetreut.' },
  klasse_abwesend: { label: 'Klasse abwesend', short: 'KA', cls: 'k-abwesend', description: 'Die Klasse ist nicht im Haus (z. B. Wandertag, Exkursion).' },
  aufsicht: { label: 'Aufsicht', short: 'A', cls: 'k-aufsicht', description: 'Vertretung einer Pausenaufsicht.' },
  klausur: { label: 'Klausur', short: 'K', cls: 'k-klausur', description: 'Klassenarbeit/Klausur in dieser Stunde.' },
};

export const KIND_ORDER: EntryKind[] = [
  'vertretung',
  'betreuung',
  'mitbetreuung',
  'entfall',
  'verlegung',
  'raumaenderung',
  'klasse_abwesend',
  'aufsicht',
  'klausur',
];

export function kindInfo(kind: string | null | undefined): KindInfo {
  if (kind && kind in KIND_INFO) return KIND_INFO[kind as EntryKind];
  return { label: kind || 'Änderung', short: '•', cls: 'k-sonst', description: '' };
}

export interface EntryFilter {
  site?: string;
  classId?: string;
  teacher?: string;
  kinds?: string[];
  text?: string;
}

export function filterEntries(entries: readonly Entry[], f: EntryFilter): Entry[] {
  const text = f.text?.trim().toLowerCase();
  return entries.filter((e) => {
    if (f.site && e.site && e.site !== f.site) return false;
    if (f.classId && !e.classes.includes(f.classId)) return false;
    if (f.teacher && e.teacher !== f.teacher && e.substitute !== f.teacher) return false;
    if (f.kinds && f.kinds.length && !f.kinds.includes(e.kind)) return false;
    if (text) {
      const hay = [e.classes.join(' '), e.subject, e.teacher, e.substitute, e.room, e.new_room, e.note, kindInfo(e.kind).label]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      if (!hay.includes(text)) return false;
    }
    return true;
  });
}

/** Sortierung: Klasse, dann Stunde. */
export function sortEntries(entries: readonly Entry[], by: 'class' | 'period' | 'teacher' = 'class'): Entry[] {
  const first = (e: Entry) => e.classes[0] ?? '';
  return entries.slice().sort((a, b) => {
    if (by === 'period') return a.period - b.period || first(a).localeCompare(first(b), 'de', { numeric: true });
    if (by === 'teacher') return (a.teacher ?? '').localeCompare(b.teacher ?? '') || a.period - b.period;
    return first(a).localeCompare(first(b), 'de', { numeric: true }) || a.period - b.period;
  });
}

/** Gruppiert Einträge nach erster Klasse (Aufsicht ohne Klasse → „Aufsichten“). */
export function groupByClass(entries: readonly Entry[]): [string, Entry[]][] {
  const map = new Map<string, Entry[]>();
  for (const e of sortEntries(entries, 'class')) {
    const key = e.classes.length ? e.classes.join(', ') : e.kind === 'aufsicht' ? 'Pausenaufsichten' : 'Sonstiges';
    const list = map.get(key) ?? [];
    list.push(e);
    map.set(key, list);
  }
  return [...map.entries()];
}

/** Lesbare Beschreibung der Änderung (für Screenreader und Monitor). */
export function describeEntry(e: Entry): string {
  const k = kindInfo(e.kind).label;
  const parts = [`${e.period_label || `${e.period + 1}.`} Stunde`, e.classes.join(', '), e.subject, k];
  if (e.substitute) parts.push(`statt ${e.teacher ?? '—'}: ${e.substitute}`);
  if (e.new_room) parts.push(`Raum ${e.new_room}`);
  if (e.note) parts.push(e.note);
  return parts.filter(Boolean).join(' – ');
}

/** Übersetzt Statistik-Schlüssel des Tagesplans. */
export function statLabel(key: string): string {
  return kindInfo(key).label;
}

/** Eindeutiger Schlüssel einer Unterrichtsstunde im Tagesplan (für Overrides). */
export function entrySlotKey(x: { date: string; lesson_id: string | null; period: number; part?: number | null }): string {
  return `${x.date}|${x.lesson_id ?? ''}|${x.period}|${x.part ?? 0}`;
}

/**
 * Kurzfassung langer Hinweise der Pausenaufsicht für die Tabelle („Aufsicht für Herr Meyer (Unterricht direkt
 * vor/nach der Pause) – an dem Tag nicht am Standort der Aufsicht“ → „für Meyer · Standortwechsel“). Andere
 * Hinweise bleiben unverändert; der volle Text gehört in `title` bzw. ins Detail.
 */
export function shortNote(note: string | null | undefined): string {
  const text = (note ?? '').trim();
  const m = /^Aufsicht für (.+?)(?: \((.+?)\))?(?: – (.+))?$/.exec(text);
  if (m) {
    const who = m[1].replace(/^((Herr|Frau|Dr\.|Prof\.)\s+)+/, '');
    const why = m[3] && /Standort/i.test(m[3]) ? 'Standortwechsel' : m[3] && m[3] !== 'abwesend' ? m[3] : '';
    return ['für ' + who, why].filter(Boolean).join(' · ');
  }
  const open = /^Keine Lehrkraft für die Aufsicht frei – bitte manuell regeln/.exec(text);
  if (open) return 'Keine Lehrkraft frei · manuell regeln';
  return text;
}

// ---------------------------------------------------------------- B-04: abwesende Lehrkräfte und Klassen

/** „ganztägig“ bzw. „1., 3.–5. Std.“ (0-basierte Stunden, zusammenhängende Bereiche). */
export function periodsLabel(periods: readonly number[] | undefined, fullDay?: boolean): string {
  const list = [...new Set(periods ?? [])].sort((a, b) => a - b);
  if (fullDay || list.length === 0) return 'ganztägig';
  const parts: string[] = [];
  let start = list[0];
  let prev = list[0];
  for (const p of [...list.slice(1), Number.NaN]) {
    if (p === prev + 1) {
      prev = p;
      continue;
    }
    parts.push(start === prev ? `${start + 1}.` : `${start + 1}.–${prev + 1}.`);
    start = p;
    prev = p;
  }
  return `${parts.join(', ')} Std.`;
}

/** „1 Fall“ / „3 Fälle“ (Vertretungsfälle einer abwesenden Lehrkraft). */
export function casesLabel(n: number | undefined): string {
  const v = n ?? 0;
  return v === 1 ? '1 Fall' : `${v} Fälle`;
}

/** Eine Zeile je Klasse mit gemeldeter Abwesenheit (Wandertag …) – statt einer Zeile je Stunde. */
export interface ClassAbsenceRow {
  class: string;
  name: string;
  /** „ganztägig“ bzw. „4. Std.“ */
  when: string;
  reason: string;
}

/**
 * Klassen-Zeilen für Vertretungsplan und Druck: nur gemeldete Abwesenheiten (`source = absence`); Klassen mit
 * regulärem Rhythmus (Praxis-/Berufsschultag) erscheinen nicht als abwesend (A-56).
 */
export function classAbsenceRows(details: readonly AbsentClassDetail[] | undefined): ClassAbsenceRow[] {
  const out = new Map<string, ClassAbsenceRow>();
  for (const d of details ?? []) {
    if (d.source !== 'absence' || out.has(d.class)) continue;
    out.set(d.class, { class: d.class, name: d.name || d.class, when: periodsLabel(d.periods, d.full_day), reason: d.reason ?? '' });
  }
  return [...out.values()].sort((a, b) => a.class.localeCompare(b.class, 'de', { numeric: true }));
}

/** Plan-Einträge ohne „Klasse abwesend“: gemeldete stehen als eine Zeile je Klasse, Rhythmus gar nicht. */
export function withoutClassAbsences(entries: readonly Entry[]): Entry[] {
  return entries.filter((e) => e.kind !== 'klasse_abwesend');
}

/**
 * Klassen-Zeilen nach Suchtext und Arten-Filter (Art „klasse_abwesend“). Beim Filter auf eine Lehrkraft nur Klassen,
 * in denen ihr Unterricht wegen der gemeldeten Abwesenheit entfällt (`entries`: „Klasse abwesend“-Einträge vom Server).
 */
export function filterClassRows(
  rows: readonly ClassAbsenceRow[],
  f: Pick<EntryFilter, 'text' | 'kinds' | 'classId' | 'teacher'> & { entries?: readonly Entry[] },
): ClassAbsenceRow[] {
  const text = f.text?.trim().toLowerCase();
  const teacher = f.teacher;
  const affected = teacher
    ? new Set((f.entries ?? []).filter((e) => e.kind === 'klasse_abwesend' && e.source !== 'rhythm' && e.teacher === teacher).flatMap((e) => e.classes))
    : null;
  return rows.filter((r) => {
    if (affected && !affected.has(r.class)) return false;
    if (f.classId && r.class !== f.classId) return false;
    if (f.kinds && f.kinds.length && !f.kinds.includes('klasse_abwesend')) return false;
    if (text && ![r.class, r.name, r.reason, r.when, 'nicht im Haus', kindInfo('klasse_abwesend').label].join(' ').toLowerCase().includes(text)) return false;
    return true;
  });
}

/** Hinweistext einer Klassen-Zeile: „ganztägig nicht im Haus · Wandertag“. */
export function classAbsenceText(r: ClassAbsenceRow): string {
  return [`${r.when} nicht im Haus`, r.reason].filter(Boolean).join(' · ');
}

/** Gruppen für die Tabelle „nach Klasse“: Einträge je Klasse, Klassen-Zeile (falls vorhanden) zuerst. */
export function groupWithClassRows(entries: readonly Entry[], rows: readonly ClassAbsenceRow[]): [string, ClassAbsenceRow | null, Entry[]][] {
  const groups = groupByClass(entries);
  const byKey = new Map<string, [ClassAbsenceRow | null, Entry[], string]>();
  for (const [key, list] of groups) byKey.set(key, [null, list, list[0]?.classes[0] ?? '']);
  for (const r of rows) {
    const g = byKey.get(r.class);
    if (g) g[0] = r;
    else byKey.set(r.class, [r, [], r.class]);
  }
  return [...byKey.entries()]
    .sort((a, b) => a[1][2].localeCompare(b[1][2], 'de', { numeric: true }))
    .map(([key, [row, list]]) => [key, row, list]);
}

/** Zeitraum der Wochenstatistik: Montag bis letzter Schultag laut `settings.days` (1–7) bzw. Unterrichtstagen (R3). */
export function statsWeek(date: string, days: number | readonly number[] | undefined): { from: string; to: string } {
  const from = mondayOf(date);
  const last = Array.isArray(days) ? (days.length ? Math.max(...days) + 1 : 5) : (days as number | undefined);
  const n = Math.min(7, Math.max(1, Math.round(last ?? 5)));
  return { from, to: addDays(from, n - 1) };
}

/** Zeilen der Wochenstatistik: alle mit Vertretungen, eigenem Entfall, Aufsichten oder Aufsichtsvertretungen. */
export function statRows(rows: readonly TeacherStat[]): TeacherStat[] {
  return rows
    .filter((r) => r.substitutions || r.cancelled_own || r.duties || r.supervisions)
    .sort((a, b) => b.substitutions - a.substitutions || b.supervisions - a.supervisions || a.name.localeCompare(b.name, 'de'));
}

/**
 * Feld „Grund“ im Abwesenheits-Dialog je Art (U-60): Gründe von Lehrkraft-Abwesenheiten sehen nur Konten mit
 * `substitution.edit` (Sekretariat, Planung, Schulleitung, Administration) und die Lehrkraft selbst – Server
 * `absence_reasons`/`_absence_out`; Gründe von Klasse, Raum und Unterricht erscheinen als Hinweis im Plan.
 */
export const ABSENCE_REASON_FIELD: Record<AbsenceKind, { label: string; help: string; placeholder: string }> = {
  teacher: {
    label: 'Grund (vertraulich)',
    help: 'Sichtbar nur für Sekretariat, Planung, Schulleitung und Administration sowie für die Lehrkraft selbst – nie im Aushang, auf dem Monitor oder für Schüler und Eltern.',
    placeholder: 'z. B. krank, Fortbildung',
  },
  class: {
    label: 'Grund',
    help: 'Erscheint im Vertretungsplan, im Aushang und auf dem Monitor als Hinweis, z. B. „Wandertag“.',
    placeholder: 'z. B. Wandertag, Exkursion',
  },
  room: {
    label: 'Grund',
    help: 'Sichtbar nur für Sekretariat, Planung, Schulleitung und Administration. Im Vertretungsplan steht nur „Raum … gesperrt“ mit dem Ersatzraum.',
    placeholder: 'z. B. Wasserschaden',
  },
  lesson: { label: 'Grund', help: 'Erscheint im Vertretungsplan als Hinweis zum entfallenden Unterricht.', placeholder: 'z. B. Sporthalle gesperrt' },
};

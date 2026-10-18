/**
 * Kennzahlen des Qualitätsberichts: deutsche Titel, Einheiten, Erklärungen und die Darstellung der Werte.
 *
 * Hohl-/Springstunden und Standortwechsel werden über alle Schulwochen gemittelt. Gelten Kurse oder Sperrzeiten nur in
 * bestimmten Wochen (z. B. jede 2. Woche), gibt es mehrere „Wochenmuster“ – der Durchschnitt ist dann ein halber Wert.
 * Statt „5,5“ zeigen wir die Spanne „5–6“ je Woche und den Durchschnitt als Nebenzeile.
 */

export type ReportDetailKind =
  | 'class_gaps'
  | 'teacher_gaps'
  | 'site_changes'
  | 'conflicts'
  | 'core_late'
  | 'unplaced'
  | 'overplaced'
  | 'teachers'
  | 'weeks';

export interface RangeInfo {
  min: number;
  max: number;
  avg: number;
}

export type TileTone = 'good' | 'warn' | 'bad' | undefined;

export interface TileDef {
  key: string;
  title: string;
  /** Einheit unter dem Wert, z. B. „Stunden“ */
  unit: string;
  /** Was ist das? Warum wichtig? Was tun? (1–2 Sätze) */
  help: string;
  /** Klick: Seite öffnen … */
  nav?: string;
  /** … oder Liste im Dialog */
  detail?: ReportDetailKind;
  /** Färbung bei Wert > 0 (bei 0: grün) */
  tone?: 'bad' | 'warn';
  /** Wert gilt je Schulwoche (Durchschnitt über Wochenmuster) */
  weekly?: boolean;
}

export const TILES: TileDef[] = [
  {
    key: 'courses',
    title: 'Kurse',
    unit: 'geplante Gruppen',
    help: 'Unterrichtsgruppen, die geplant werden (z. B. „Mathe 5a“, auch gekoppelte Kurse). Klick: Kursliste. Fehlt ein Kurs, gibt es keinen Unterricht dafür.',
    nav: '/planung/kurse',
  },
  {
    key: 'lessons',
    title: 'Unterrichtsblöcke',
    unit: 'Blöcke im Plan',
    help: 'Einzel- und Doppelstunden, die im Stundenplan stehen. Ein Kurs mit 4 Stunden als 2 Doppelstunden sind 2 Blöcke. Klick: Stundenpläne ansehen.',
    nav: '/stundenplan/class',
  },
  {
    key: 'classes',
    title: 'Klassen',
    unit: 'in der Schule',
    help: 'Anzahl der Klassen und Jahrgangsgruppen in der Schule. Klick: Klassenliste in den Stammdaten.',
    nav: '/stammdaten/classes',
  },
  {
    key: 'teachers',
    title: 'Lehrkräfte',
    unit: 'im Kollegium',
    help: 'Lehrkräfte mit Deputat (Soll-Stunden) und Ist (Stunden ihrer Kurse). Klick: Liste mit Deputat und Ist, Überschreitungen zuerst.',
    detail: 'teachers',
  },
  {
    key: 'students',
    title: 'Schüler/innen',
    unit: 'erfasst',
    help: 'Anzahl der erfassten Schülerinnen und Schüler. Klick: Schülerliste in den Stammdaten.',
    nav: '/stammdaten/students',
  },
  {
    key: 'unplaced_hours',
    title: 'Unverplante Stunden',
    unit: 'Stunden fehlen',
    help: 'Wochenstunden von Kursen, die noch keinen Platz im Stundenplan haben. Dort fällt Unterricht aus. Klick: Liste mit Grund; dann Lehrkraft zuweisen oder im Generator neu planen.',
    detail: 'unplaced',
    tone: 'bad',
  },
  {
    key: 'overplaced_hours',
    title: 'Zu viel verplante Stunden',
    unit: 'Stunden zu viel',
    help: 'Kurse stehen häufiger im Plan, als ihre Wochenstunden vorsehen (z. B. nach Kürzung der Stundentafel). Klick: betroffene Kurse; überzählige Blöcke im Stundenplan entfernen.',
    detail: 'overplaced',
    tone: 'bad',
  },
  {
    key: 'conflicts',
    title: 'Konflikte',
    unit: 'Doppelbelegungen',
    help: 'Klasse, Lehrkraft oder Raum sind zur selben Zeit doppelt belegt. Das darf nicht sein. Klick: Liste mit Tag, Stunde und Link zum Stundenplan zum Verschieben.',
    detail: 'conflicts',
    tone: 'bad',
  },
  {
    key: 'overloaded_teachers',
    title: 'Lehrkräfte über Deputat',
    unit: 'überlastet',
    help: 'Lehrkräfte, deren Kurse zusammen mehr Wochenstunden haben als ihr Deputat. Klick: Liste mit Soll und Ist; Kurse umverteilen.',
    detail: 'teachers',
    tone: 'bad',
  },
  {
    key: 'class_gaps',
    title: 'Hohlstunden Klassen',
    unit: 'Freistunden je Woche',
    help: 'Freistunden mitten im Schultag einer Klasse (Unterricht davor und danach). Schüler sollten keine haben. Klick: Liste je Klasse mit Tag und Stunde; Stunden im Stundenplan verschieben.',
    detail: 'class_gaps',
    tone: 'warn',
    weekly: true,
  },
  {
    key: 'teacher_gaps',
    title: 'Springstunden Lehrkräfte',
    unit: 'Freistunden je Woche',
    help: 'Freistunden zwischen zwei Unterrichtsstunden einer Lehrkraft. Etwas Spielraum ist ok und hilft bei Vertretungen; sehr viele belasten. Klick: Liste je Lehrkraft mit Tag und Stunde.',
    detail: 'teacher_gaps',
    weekly: true,
  },
  {
    key: 'site_changes',
    title: 'Standortwechsel',
    unit: 'Wechsel je Woche',
    help: 'Lehrkräfte wechseln am selben Tag den Standort (Wegezeit ist eingeplant, kostet aber Zeit). Klick: betroffene Lehrkräfte und Tage.',
    detail: 'site_changes',
    weekly: true,
  },
  {
    key: 'core_late',
    title: 'Hauptfächer spät',
    unit: 'Blöcke',
    help: 'Hauptfächer, die nach der eingestellten Stunde enden (siehe „Prioritäten & Regeln“). Spät ist Konzentration geringer. Klick: betroffene Stunden.',
    detail: 'core_late',
    tone: 'warn',
  },
  {
    key: 'week_variants',
    title: 'Wochenmuster',
    unit: 'verschiedene Wochenarten',
    help: 'So viele unterschiedliche Wochenarten hat das Schuljahr, weil manche Kurse oder Sperrzeiten nur in bestimmten Wochen gelten (z. B. jede 2. Woche). Hohl- und Springstunden werden je Wochenart gezählt. Klick: Aufstellung je Wochenart.',
    detail: 'weeks',
  },
];

export const TILE_BY_KEY: Record<string, TileDef> = Object.fromEntries(TILES.map((t) => [t.key, t]));

/** Kennzahlen, die in der Übersicht zum Bestand gehören (neutral), und die zur Qualität. */
export const STOCK_KEYS = ['courses', 'lessons', 'classes', 'teachers', 'students'];
export const QUALITY_KEYS = ['unplaced_hours', 'overplaced_hours', 'conflicts', 'overloaded_teachers', 'class_gaps', 'teacher_gaps', 'site_changes', 'core_late', 'week_variants'];

/** Zahl deutsch: 5,5 statt 5.5 (höchstens eine Nachkommastelle). */
export function formatNumber(n: number): string {
  if (!Number.isFinite(n)) return '–';
  const r = Math.round(n * 10) / 10;
  return String(r).replace('.', ',');
}

export interface TileValue {
  value: string;
  /** Nebenzeile, z. B. „Ø 5,5 je Woche“ */
  note?: string;
}

/**
 * Anzeigewert einer Kennzahl. Wochenbezogene Werte (Hohl-/Springstunden, Standortwechsel) als ganze Zahl bzw. Spanne
 * („5–6“) der typischen Woche statt „5,5“; der Durchschnitt steht in der Nebenzeile.
 */
export function tileValue(def: TileDef, stats: Record<string, number | string> | undefined, ranges?: Record<string, RangeInfo>): TileValue {
  const raw = Number(stats?.[def.key]);
  if (stats?.[def.key] === undefined || !Number.isFinite(raw)) return { value: '–' };
  if (!def.weekly) return { value: formatNumber(raw) };
  const r = ranges?.[def.key];
  if (r && r.min !== r.max) {
    return { value: `${formatNumber(r.min)}–${formatNumber(r.max)}`, note: `je nach Woche, Ø ${formatNumber(r.avg)}` };
  }
  if (Number.isInteger(raw)) return { value: String(raw) };
  // Ältere Server liefern keine Spanne: Durchschnitt gerundet anzeigen
  return { value: `≈ ${Math.round(raw)}`, note: `Ø ${formatNumber(raw)} je Woche` };
}

export function tileTone(def: TileDef, stats: Record<string, number | string> | undefined): TileTone {
  if (!def.tone) return undefined;
  const n = Number(stats?.[def.key]);
  if (!Number.isFinite(n)) return undefined;
  return n > 0 ? def.tone : 'good';
}

/** Soll die Kachel gezeigt werden? „Wochenmuster“ nur, wenn es mehr als eines gibt; unbekannte Kennzahlen nie. */
export function tileVisible(def: TileDef, stats: Record<string, number | string> | undefined): boolean {
  if (!stats || stats[def.key] === undefined) return false;
  if (def.key === 'week_variants') return Number(stats[def.key]) > 1;
  return true;
}

/** Link in den Stundenplan (Klasse/Lehrkraft/Raum). */
export function timetableLink(kind: string, id: string): string {
  return `/stundenplan/${kind}/${encodeURIComponent(id)}`;
}

/** Link zum Kurs in „Kurse & Kopplungen“ (öffnet den Editor). */
export function courseLink(id: string): string {
  return `/planung/kurse?kurs=${encodeURIComponent(id)}`;
}

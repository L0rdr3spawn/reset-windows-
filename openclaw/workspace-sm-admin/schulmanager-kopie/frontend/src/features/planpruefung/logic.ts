/**
 * Reine Hilfsfunktionen der Plan-Prüfung (testbar ohne Browser): Kennzahlen vorher/nachher, Beschriftungen.
 */
import type { PackageStatus, ProposalMetrics, ProposalVariant } from './api';

export interface MetricRow {
  key: keyof ProposalMetrics;
  label: string;
  /** immer anzeigen (auch bei 0 → 0) */
  always?: boolean;
}

export const METRIC_ROWS: MetricRow[] = [
  { key: 'problems', label: 'Probleme im Plan', always: true },
  { key: 'conflicts', label: 'Konflikte', always: true },
  { key: 'unplaced_hours', label: 'Unverplante Stunden', always: true },
  { key: 'class_gaps', label: 'Hohlstunden Klassen (Ø je Woche)', always: true },
  { key: 'teacher_gaps', label: 'Springstunden Lehrkräfte (Ø je Woche)', always: true },
  { key: 'site_changes', label: 'Standortwechsel (Ø je Woche)' },
  { key: 'core_late', label: 'Hauptfächer spät' },
  { key: 'late_start', label: 'Später Unterrichtsbeginn' },
  { key: 'spread', label: 'Fach an Folgetagen' },
  { key: 'doubles', label: 'Doppelstunden getrennt' },
  { key: 'teacher_wish', label: 'Lehrerwünsche verletzt' },
];

export type Tone = 'good' | 'bad' | 'same';

export interface MetricDelta {
  key: keyof ProposalMetrics;
  label: string;
  before: number;
  after: number;
  tone: Tone;
  text: string;
}

function num(v: number | null | undefined): number | null {
  return typeof v === 'number' && Number.isFinite(v) ? v : null;
}

function fmt(v: number): string {
  return v.toLocaleString('de-DE', { maximumFractionDigits: 1 });
}

/** Kennzahlen eines Plans vorher/nachher; nur Zeilen, die für die Entscheidung etwas sagen. Weniger ist besser. */
export function metricDeltas(before: ProposalMetrics, after: ProposalMetrics): MetricDelta[] {
  const out: MetricDelta[] = [];
  for (const row of METRIC_ROWS) {
    const b = num(before[row.key]);
    const a = num(after[row.key]);
    if (b === null || a === null) continue;
    if (!row.always && b === 0 && a === 0) continue;
    const tone: Tone = a < b ? 'good' : a > b ? 'bad' : 'same';
    out.push({ key: row.key, label: row.label, before: b, after: a, tone, text: b === a ? fmt(a) : `${fmt(b)} → ${fmt(a)}` });
  }
  return out;
}

/** Kurzfazit einer Variante: wie viele Kennzahlen besser/schlechter werden. */
export function verdict(deltas: MetricDelta[]): { better: number; worse: number } {
  return { better: deltas.filter((d) => d.tone === 'good').length, worse: deltas.filter((d) => d.tone === 'bad').length };
}

export const STATUS_LABELS: Record<PackageStatus, string> = {
  berechnung: 'wird berechnet',
  offen: 'offen',
  angenommen: 'angenommen',
  verworfen: 'verworfen',
  ersetzt: 'durch neueren Vorschlag ersetzt',
  erledigt: 'erledigt (Problem besteht nicht mehr)',
  veraltet: 'veraltet',
  fehlgeschlagen: 'keine Lösung gefunden',
};

/** Kurzbeschreibung der Auswirkung für die Variantenkarte. */
export function impactText(v: Pick<ProposalVariant, 'key' | 'moved_lessons' | 'changes' | 'affected_classes' | 'affected_teachers'>): string {
  if (v.key === 'vertretung') return 'Keine Änderung am Stundenplan';
  const parts: string[] = [];
  if (v.moved_lessons > 0) parts.push(`${v.moved_lessons} Stunde${v.moved_lessons === 1 ? '' : 'n'} verschoben`);
  const rooms = v.changes.reduce((n, c) => n + c.rooms.length, 0);
  if (rooms > 0) parts.push(`${rooms} Raumwechsel`);
  if (v.affected_classes.length > 0) parts.push(`${v.affected_classes.length} Klasse${v.affected_classes.length === 1 ? '' : 'n'}`);
  if (v.affected_teachers.length > 0) parts.push(`${v.affected_teachers.length} ${v.affected_teachers.length === 1 ? 'Lehrkraft' : 'Lehrkräfte'}`);
  return parts.join(' · ') || 'Keine Änderung';
}

/** Rechtfertigt das Paket eine Anzeige in Badge/Kachel? (offen, nicht zurückgestellt) */
export function isActionable(p: { status: string; postponed_until: string | null }, now = Date.now()): boolean {
  if (p.status !== 'offen') return false;
  if (!p.postponed_until) return true;
  const t = Date.parse(p.postponed_until.endsWith('Z') ? p.postponed_until : `${p.postponed_until}Z`);
  return !(t > now);
}

/** Sachliche Hinweise an Varianten (keine Empfehlung): wenigste Änderungen, beste Qualität. */
export function highlights(variants: Pick<ProposalVariant, 'id' | 'key' | 'moved_lessons' | 'diff_size' | 'metrics_after' | 'status'>[]): Map<number, string[]> {
  const out = new Map<number, string[]>();
  const add = (id: number, text: string) => out.set(id, [...(out.get(id) ?? []), text]);
  const real = variants.filter((v) => v.status === 'bereit');
  const changing = real.filter((v) => v.key !== 'vertretung');
  if (changing.length > 1) {
    const min = Math.min(...changing.map((v) => v.diff_size));
    if (changing.some((v) => v.diff_size > min)) changing.filter((v) => v.diff_size === min).forEach((v) => add(v.id, 'wenigste Änderungen'));
    const q = (v: (typeof real)[number]) => (v.metrics_after.class_gaps ?? 0) + (v.metrics_after.teacher_gaps ?? 0) + (v.metrics_after.problems ?? 0) * 100;
    const best = Math.min(...changing.map(q));
    if (changing.some((v) => q(v) > best)) changing.filter((v) => q(v) === best).forEach((v) => add(v.id, 'beste Qualität'));
  }
  return out;
}

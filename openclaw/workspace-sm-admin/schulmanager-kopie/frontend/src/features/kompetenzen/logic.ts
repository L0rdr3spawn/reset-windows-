/** Reine Logik für Kompetenzraster und Lernstand (ohne React, testbar). */
import { addDays, mondayOf } from '../../lib/dates';
import type { BadgeCriteria, EvidenceType, Framework, FrameworkInput, OverviewStudent, Plan, PlanStatus } from './api';

export const MIN_LEVELS = 2;
export const MAX_LEVELS = 6;

/** Farbstufe 1…4 einer Niveaustufe (unabhängig von der Zahl der Stufen); 0 = nicht eingeschätzt. */
export function levelBucket(level: number | null | undefined, levels: number): 0 | 1 | 2 | 3 | 4 {
  if (!level || levels < 1) return 0;
  const v = Math.ceil((Math.min(level, levels) / levels) * 4);
  return Math.max(1, Math.min(4, v)) as 1 | 2 | 3 | 4;
}

export function levelLabel(labels: readonly string[], level: number | null | undefined): string {
  if (!level) return 'Noch nicht eingeschätzt';
  return labels[level - 1] ?? `Stufe ${level}`;
}

/** „Stufe 3 von 4: Ich kann es allein“ – für Bildschirmleser und Hinweise. */
export function levelSummary(labels: readonly string[], level: number | null | undefined): string {
  if (!level) return 'Noch nicht eingeschätzt';
  return `Stufe ${level} von ${labels.length}: ${levelLabel(labels, level)}`;
}

export function percent(p: number): string {
  return `${Math.round(Math.max(0, Math.min(1, p)) * 100)} %`;
}

export type StudentFilter = 'alle' | 'unterstuetzung' | 'offen';

/** Schüler/innen der Klassenübersicht filtern: „braucht Unterstützung“ bzw. „Selbsteinschätzung offen“. */
export function filterStudents(students: readonly OverviewStudent[], filter: StudentFilter, query = ''): OverviewStudent[] {
  const q = query.trim().toLowerCase();
  return students.filter((s) => {
    if (q && !s.name.toLowerCase().includes(q)) return false;
    if (filter === 'unterstuetzung') return s.support > 0;
    if (filter === 'offen') return s.pending > 0;
    return true;
  });
}

/** Nachweis-Link für die Oberfläche: nur http(s) und App-Pfade; Verweise `channel:12` führen in den Kursraum. */
export function evidenceHref(type: EvidenceType, ref: string, text: string): string | null {
  if (type === 'link') {
    if (/^https?:\/\//i.test(text) || (text.startsWith('/') && !text.startsWith('//'))) return text;
    return null;
  }
  if (type === 'assignment' || type === 'material') {
    const m = /^channel(?:_item)?:(\d+)$/.exec(ref);
    return m ? `/kursraeume/${m[1]}` : null;
  }
  return null;
}

export const EVIDENCE_LABEL: Record<EvidenceType, string> = {
  '': 'Kein Nachweis',
  note: 'Beobachtung',
  link: 'Link',
  assignment: 'Abgabe',
  material: 'Material',
};

export const STATUS_LABEL: Record<PlanStatus, string> = { offen: 'Offen', in_arbeit: 'In Arbeit', erledigt: 'Erledigt' };

export function nextStatus(s: PlanStatus): PlanStatus {
  return s === 'offen' ? 'in_arbeit' : s === 'in_arbeit' ? 'erledigt' : 'offen';
}

export interface PlanGroup {
  key: string;
  title: string;
  plans: Plan[];
}

/** Lernplan gliedern: diese Woche, nächste Wochen, ohne Woche, frühere Wochen (nur offene) und Erledigtes. */
export function groupPlans(plans: readonly Plan[], currentWeek: string): PlanGroup[] {
  const week = mondayOf(currentWeek);
  const open = plans.filter((p) => p.status !== 'erledigt');
  const done = plans.filter((p) => p.status === 'erledigt');
  const byDue = (a: Plan, b: Plan) => (a.due_date ?? '9999').localeCompare(b.due_date ?? '9999') || a.id - b.id;
  const groups: PlanGroup[] = [
    { key: 'diese', title: 'Diese Woche', plans: open.filter((p) => p.week_start === week).sort(byDue) },
    { key: 'frueher', title: 'Noch offen aus früheren Wochen', plans: open.filter((p) => !!p.week_start && p.week_start < week).sort(byDue) },
    { key: 'spaeter', title: 'Kommende Wochen', plans: open.filter((p) => !!p.week_start && p.week_start > week).sort(byDue) },
    { key: 'ohne', title: 'Ohne feste Woche', plans: open.filter((p) => !p.week_start).sort(byDue) },
    { key: 'erledigt', title: 'Erledigt', plans: done.sort((a, b) => (b.done_at ?? '').localeCompare(a.done_at ?? '')) },
  ];
  return groups.filter((g) => g.plans.length);
}

export function weekRangeText(weekStart: string): string {
  const end = addDays(weekStart, 4);
  const f = (s: string) => `${s.slice(8, 10)}.${s.slice(5, 7)}.`;
  return `${f(weekStart)} – ${f(end)}`;
}

/** Zusammenfassung des Lernplans: erledigte und alle Ziele. */
export function planProgress(plans: readonly Plan[]): { done: number; total: number } {
  return { done: plans.filter((p) => p.status === 'erledigt').length, total: plans.length };
}

// ------------------------------------------------------------------------------------------- Rahmen-Editor
export interface DraftCompetency {
  id?: number;
  code: string;
  title: string;
  descriptors: string[];
}
export interface DraftArea {
  id?: number;
  name: string;
  competencies: DraftCompetency[];
}
export interface Draft {
  name: string;
  subject: string;
  description: string;
  levels: string[];
  support_level: number;
  areas: DraftArea[];
}

export const DEFAULT_LEVELS = ['Ich fange an', 'Ich kann es mit Hilfe', 'Ich kann es allein', 'Ich kann es erklären'];

export function emptyDraft(): Draft {
  return { name: '', subject: '', description: '', levels: [...DEFAULT_LEVELS], support_level: 1, areas: [{ name: '', competencies: [{ code: '', title: '', descriptors: [] }] }] };
}

export function draftOf(fw: Framework): Draft {
  return {
    name: fw.name,
    subject: fw.subject,
    description: fw.description,
    levels: [...fw.levels],
    support_level: fw.support_level,
    areas: fw.areas.map((a) => ({ id: a.id, name: a.name, competencies: a.competencies.map((c) => ({ id: c.id, code: c.code, title: c.title, descriptors: [...c.descriptors] })) })),
  };
}

/** Fehlertext des Entwurfs oder `null`. Leere Zeilen werden beim Speichern ignoriert (`toInput`). */
export function draftError(d: Draft): string | null {
  if (!d.name.trim()) return 'Bitte einen Namen eingeben.';
  if (d.levels.length < MIN_LEVELS || d.levels.length > MAX_LEVELS) return `Es braucht ${MIN_LEVELS} bis ${MAX_LEVELS} Niveaustufen.`;
  if (d.levels.some((l) => !l.trim())) return 'Jede Niveaustufe braucht eine Beschriftung.';
  if (d.support_level >= d.levels.length) return 'Die Stufe für „braucht Unterstützung“ muss unter der höchsten Stufe liegen.';
  const areas = d.areas.filter((a) => a.name.trim() || a.competencies.some((c) => c.title.trim()));
  if (!areas.length) return 'Mindestens ein Bereich mit einer Kompetenz fehlt.';
  for (const a of areas) {
    if (!a.name.trim()) return 'Jeder Bereich braucht einen Namen.';
    if (!a.competencies.some((c) => c.title.trim())) return `Der Bereich „${a.name}“ hat keine Kompetenz.`;
  }
  return null;
}

/** Leere Beschreibungen am Ende weglassen. */
export function trimTail(items: string[]): string[] {
  const out = [...items];
  while (out.length && !out[out.length - 1]) out.pop();
  return out;
}

export function toInput(d: Draft): FrameworkInput {
  return {
    name: d.name.trim(),
    subject: d.subject.trim(),
    description: d.description.trim(),
    levels: d.levels.map((l) => l.trim()),
    support_level: d.support_level,
    areas: d.areas
      .filter((a) => a.name.trim() || a.competencies.some((c) => c.title.trim()))
      .map((a) => ({
        ...(a.id !== undefined ? { id: a.id } : {}),
        name: a.name.trim(),
        competencies: a.competencies
          .filter((c) => c.title.trim())
          .map((c) => ({
            ...(c.id !== undefined ? { id: c.id } : {}),
            code: c.code.trim(),
            title: c.title.trim(),
            descriptors: trimTail(c.descriptors.slice(0, d.levels.length).map((x) => x.trim())),
          })),
      })),
  };
}

/** Nach dem Verkürzen der Stufen die Beschreibungen der entfernten Stufen verwerfen. */
export function setLevelCount(d: Draft, count: number): Draft {
  const n = Math.max(MIN_LEVELS, Math.min(MAX_LEVELS, count));
  const levels = d.levels.slice(0, n);
  while (levels.length < n) levels.push(`Stufe ${levels.length + 1}`);
  return {
    ...d,
    levels,
    support_level: Math.min(d.support_level, n - 1),
    areas: d.areas.map((a) => ({ ...a, competencies: a.competencies.map((c) => ({ ...c, descriptors: c.descriptors.slice(0, n) })) })),
  };
}

// ------------------------------------------------------------------------------------------------ Abzeichen
export const BADGE_ICONS = ['star', 'medal', 'trophy', 'flag', 'book', 'calculator', 'pencil', 'puzzle', 'bulb', 'heart', 'leaf', 'rocket'] as const;
export const BADGE_COLORS = ['gold', 'silver', 'bronze', 'blue', 'green', 'red', 'purple'] as const;
export const ICON_LABEL: Record<(typeof BADGE_ICONS)[number], string> = {
  star: 'Stern',
  medal: 'Medaille',
  trophy: 'Pokal',
  flag: 'Fahne',
  book: 'Buch',
  calculator: 'Rechnen',
  pencil: 'Stift',
  puzzle: 'Puzzle',
  bulb: 'Idee',
  heart: 'Herz',
  leaf: 'Blatt',
  rocket: 'Rakete',
};
export const COLOR_LABEL: Record<(typeof BADGE_COLORS)[number], string> = {
  gold: 'Gold',
  silver: 'Silber',
  bronze: 'Bronze',
  blue: 'Blau',
  green: 'Grün',
  red: 'Rot',
  purple: 'Lila',
};

export type CriteriaKind = 'manual' | 'competencies' | 'area' | 'framework';

export interface CriteriaDraft {
  kind: CriteriaKind;
  competency_ids: number[];
  area_id: number | null;
  framework_id: number | null;
  min_level: number;
  share: number;
}

export function criteriaDraft(c: BadgeCriteria): CriteriaDraft {
  const base: CriteriaDraft = { kind: 'manual', competency_ids: [], area_id: null, framework_id: null, min_level: 3, share: 1 };
  if (!c) return base;
  if (c.type === 'competencies') return { ...base, kind: 'competencies', competency_ids: [...c.competency_ids], min_level: c.min_level };
  if (c.type === 'area') return { ...base, kind: 'area', area_id: c.area_id, min_level: c.min_level, share: c.share };
  return { ...base, kind: 'framework', framework_id: c.framework_id, min_level: c.min_level, share: c.share };
}

export function criteriaOf(d: CriteriaDraft): BadgeCriteria {
  if (d.kind === 'competencies') return { type: 'competencies', competency_ids: d.competency_ids, min_level: d.min_level };
  if (d.kind === 'area' && d.area_id !== null) return { type: 'area', area_id: d.area_id, min_level: d.min_level, share: d.share };
  if (d.kind === 'framework' && d.framework_id !== null) return { type: 'framework', framework_id: d.framework_id, min_level: d.min_level, share: d.share };
  return null;
}

export function criteriaError(d: CriteriaDraft): string | null {
  if (d.kind === 'competencies' && !d.competency_ids.length) return 'Bitte mindestens eine Kompetenz wählen.';
  if (d.kind === 'area' && d.area_id === null) return 'Bitte einen Bereich wählen.';
  if (d.kind === 'framework' && d.framework_id === null) return 'Bitte einen Rahmen wählen.';
  return null;
}

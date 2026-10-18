/**
 * Regeln und Prioritäten als Bausteine – Typen und reine Hilfsfunktionen (Spiegel von `schulmanager/rules.py`,
 * Konzept in `docs/REGELN-UND-PRIORITAETEN.md`). Keine React-Abhängigkeit, damit testbar.
 */
import type { WeekRhythm } from '../../../api/types';
import { APP_NAME } from '../../../brand';

export type Level = 'aus' | 'nett' | 'wichtig' | 'sehr_wichtig' | 'muss';
export type SwitchLevel = 'aus' | 'an';
export type ScopeDim = 'grades' | 'classes' | 'subjects' | 'teachers';

export const LEVELS: Level[] = ['aus', 'nett', 'wichtig', 'sehr_wichtig', 'muss'];
export const SCOPE_DIMS: ScopeDim[] = ['grades', 'classes', 'subjects', 'teachers'];
export const SCOPE_LABELS: Record<ScopeDim, string> = { grades: 'Jahrgänge', classes: 'Klassen', subjects: 'Fächer', teachers: 'Lehrkräfte' };

export interface RuleParamDef {
  key: string;
  label: string;
  kind: 'int' | 'bool' | 'choice';
  min: number | null;
  max: number | null;
  choices: [string, string][];
  help: string;
  one_based: boolean;
  overridable: boolean;
}

export interface RuleDef {
  id: string;
  group: string;
  title: string;
  text: string;
  control: 'level' | 'switch';
  weight_key: string;
  base: number;
  scope: ScopeDim[];
  report: string;
  hard: boolean;
  hard_text: string;
  advanced: boolean;
  entity: 'class' | 'teacher' | 'course' | 'school';
  params: RuleParamDef[];
  /** Datenbezug vorhanden (z. B. mehr als ein Standort) */
  relevant: boolean;
  requires_text: string;
  /** ohne „Erweitert“ sichtbar (Vorlage zeigt den Baustein oder die Schule hat ihn verändert) */
  visible: boolean;
  /** wirksames Gewicht (Server) */
  weight: number | null;
  affects: number;
  affects_text: string;
  violations: number | null;
}

export interface RuleOverride {
  level: Level;
  weight?: number | null;
  params: Record<string, unknown>;
  grades: number[];
  classes: string[];
  subjects: string[];
  teachers: string[];
  weeks: number[];
  rhythm: WeekRhythm | null;
  note: string;
}

export interface RuleItem {
  level: Level | SwitchLevel;
  weight: number | null;
  params: Record<string, unknown>;
  overrides: RuleOverride[];
}

export type RuleItems = Record<string, RuleItem>;

export interface RuleTemplate {
  id: string;
  name: string;
  description: string;
  builtin: boolean;
  show: string[];
  items: Record<string, Partial<RuleItem>>;
}

export interface RulesState {
  profile: string;
  advanced: boolean;
  items: RuleItems;
  templates: RuleTemplate[];
  catalog: RuleDef[];
  groups: { id: string; title: string; text: string }[];
  levels: { id: Level; label: string; factor: number; text: string }[];
  hard_rules: { id: string; title: string; text: string; link: string; count: number | null }[];
  context: Record<string, number | number[]>;
  options: {
    grades: number[];
    classes: { id: string; name: string; grade: number }[];
    subjects: { id: string; name: string; core: boolean }[];
    teachers: { id: string; name: string }[];
    periods: number;
    year_weeks: number;
  };
  numbers: Record<string, unknown>;
}

/** Entwurf, der gespeichert wird (`PUT /settings/rules`). */
export interface RulesDraft {
  profile: string;
  advanced: boolean;
  items: RuleItems;
}

export const LEVEL_FACTOR: Record<Level, number> = { aus: 0, nett: 0.25, wichtig: 1, sehr_wichtig: 4, muss: 20 };
export const LEVEL_LABEL: Record<Level, string> = { aus: 'Aus', nett: 'Nett', wichtig: 'Wichtig', sehr_wichtig: 'Sehr wichtig', muss: 'Muss' };

/** Wirksames Gewicht eines Bausteins oder einer Ausnahme (wie `rules.weight_for`). */
export function weightFor(base: number, level: Level, weight?: number | null): number {
  if (weight !== null && weight !== undefined) return Math.max(0, weight);
  return Math.round(base * LEVEL_FACTOR[level] * 1e6) / 1e6;
}

/** Stufe zu einem Gewicht und ob sie exakt passt (eigener Wert sonst). */
export function levelForWeight(base: number, weight: number): { level: Level; exact: boolean } {
  const w = Math.max(0, weight);
  if (w === 0) return { level: 'aus', exact: true };
  if (base <= 0) return { level: 'wichtig', exact: false };
  const ratio = w / base;
  let best: Level = 'wichtig';
  let dist = Infinity;
  for (const lvl of ['nett', 'wichtig', 'sehr_wichtig', 'muss'] as Level[]) {
    const d = Math.abs(Math.log(ratio) - Math.log(LEVEL_FACTOR[lvl]));
    if (d < dist) {
      best = lvl;
      dist = d;
    }
  }
  return { level: best, exact: Math.abs(ratio - LEVEL_FACTOR[best]) < 1e-6 };
}

export function emptyOverride(level: Level = 'nett'): RuleOverride {
  return { level, weight: null, params: {}, grades: [], classes: [], subjects: [], teachers: [], weeks: [], rhythm: null, note: '' };
}

/** Vollständiger Baustein aus einer (ggf. unvollständigen) Vorlage. */
export function completeItem(partial: Partial<RuleItem> | undefined, fallback: RuleItem): RuleItem {
  return {
    level: partial?.level ?? fallback.level,
    weight: partial?.weight ?? null,
    params: { ...fallback.params, ...(partial?.params ?? {}) },
    overrides: (partial?.overrides ?? []).map((o) => ({ ...emptyOverride(), ...o, params: { ...(o.params ?? {}) } })),
  };
}

/** Bausteine einer Vorlage auf den aktuellen Entwurf anwenden (fehlende behalten ihren Wert, Ausnahmen der Vorlage gelten). */
export function applyTemplate(items: RuleItems, template: Pick<RuleTemplate, 'items'>): RuleItems {
  const out: RuleItems = {};
  for (const [id, cur] of Object.entries(items)) out[id] = completeItem(template.items[id], cur);
  return out;
}

/** Zusammenfassung der Gültigkeit einer Ausnahme: „Jahrgang 11–13 · Fach M“. */
export function scopeText(
  ov: Pick<RuleOverride, 'grades' | 'classes' | 'subjects' | 'teachers'>,
  names: { classes?: Map<string, string>; subjects?: Map<string, string>; teachers?: Map<string, string> } = {},
): string {
  const parts: string[] = [];
  if (ov.grades.length) parts.push(`Jahrgang ${rangesText(ov.grades)}`);
  if (ov.classes.length) parts.push(`Klasse ${ov.classes.map((c) => names.classes?.get(c) ?? c).join(', ')}`);
  if (ov.subjects.length) parts.push(`Fach ${ov.subjects.map((c) => names.subjects?.get(c) ?? c).join(', ')}`);
  if (ov.teachers.length) parts.push(`Lehrkraft ${ov.teachers.map((c) => names.teachers?.get(c) ?? c).join(', ')}`);
  return parts.join(' · ') || 'alle';
}

/** „5–7, 10“ aus einer Zahlenliste. */
export function rangesText(nums: readonly number[]): string {
  const s = [...new Set(nums)].sort((a, b) => a - b);
  const out: string[] = [];
  let i = 0;
  while (i < s.length) {
    let j = i;
    while (j + 1 < s.length && (s[j + 1] as number) === (s[j] as number) + 1) j++;
    out.push(j > i ? `${s[i]}–${s[j]}` : String(s[i]));
    i = j + 1;
  }
  return out.join(', ');
}

/** Hat die Schule den Baustein gegenüber der Vorlage verändert? */
export function differsFromTemplate(item: RuleItem, tmpl: Partial<RuleItem> | undefined, fallback: RuleItem): boolean {
  const t = completeItem(tmpl, fallback);
  if (item.level !== t.level || (item.weight ?? null) !== (t.weight ?? null)) return true;
  if (item.overrides.length !== t.overrides.length) return true;
  for (const [k, v] of Object.entries(t.params)) if (item.params[k] !== v) return true;
  return false;
}

/** Bausteine, die ohne „Erweitert“ gezeigt werden: relevante aus der Vorlage plus alles, was die Schule verändert hat. */
export function visibleRuleIds(state: Pick<RulesState, 'catalog' | 'items' | 'templates' | 'profile'>, advanced: boolean): Set<string> {
  const tmpl = state.templates.find((t) => t.id === state.profile);
  const out = new Set<string>();
  for (const def of state.catalog) {
    if (advanced) {
      out.add(def.id);
      continue;
    }
    if (!def.relevant) continue;
    const item = state.items[def.id];
    const inTemplate = tmpl ? tmpl.show.includes(def.id) : !def.advanced;
    const changed = item ? differsFromTemplate(item, tmpl?.items[def.id], { ...item, overrides: [], weight: null, level: 'wichtig' }) : false;
    if (inTemplate || (changed && item && (item.level !== 'wichtig' || item.overrides.length > 0 || item.weight !== null))) out.add(def.id);
  }
  return out;
}

/** Tiefer Vergleich zweier Entwürfe (JSON-stabil). */
export function sameDraft(a: RulesDraft, b: RulesDraft): boolean {
  return JSON.stringify(normalizeDraft(a)) === JSON.stringify(normalizeDraft(b));
}

function normalizeDraft(d: RulesDraft): RulesDraft {
  const items: RuleItems = {};
  for (const k of Object.keys(d.items).sort()) {
    const it = d.items[k] as RuleItem;
    items[k] = {
      level: it.level,
      weight: it.weight ?? null,
      params: Object.fromEntries(Object.entries(it.params ?? {}).sort()),
      overrides: (it.overrides ?? []).map((o) => ({
        level: o.level,
        weight: o.weight ?? null,
        params: Object.fromEntries(Object.entries(o.params ?? {}).sort()),
        grades: [...o.grades].sort((x, y) => x - y),
        classes: [...o.classes].sort(),
        subjects: [...o.subjects].sort(),
        teachers: [...o.teachers].sort(),
        weeks: [...o.weeks].sort((x, y) => x - y),
        rhythm: o.rhythm ?? null,
        note: o.note ?? '',
      })),
    };
  }
  return { profile: d.profile, advanced: d.advanced, items };
}

/** Kennzahlen des Generator-Entwurfs mit denen des aktuellen Plans vergleichen. */
export interface CompareRow {
  key: string;
  title: string;
  before: number | null;
  after: number | null;
  /** negativ = besser */
  delta: number | null;
}

export const COMPARE_KEYS: { key: string; title: string }[] = [
  { key: 'unplaced_hours', title: 'Unverplante Stunden' },
  { key: 'class_gaps', title: 'Hohlstunden Klassen (je Woche)' },
  { key: 'teacher_gaps', title: 'Springstunden Lehrkräfte (je Woche)' },
  { key: 'core_late', title: 'Hauptfächer spät' },
  { key: 'site_changes', title: 'Standortwechsel (je Woche)' },
];

export function compareStats(before: Record<string, unknown> | undefined, after: Record<string, unknown> | undefined): CompareRow[] {
  const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null);
  return COMPARE_KEYS.map(({ key, title }) => {
    const b = num(before?.[key]) ?? (key === 'unplaced_hours' ? num(before?.unplaced) : null);
    const a = num(after?.[key]) ?? (key === 'unplaced_hours' ? num(after?.unplaced) : null);
    return { key, title, before: b, after: a, delta: a !== null && b !== null ? Math.round((a - b) * 10) / 10 : null };
  });
}

/** Export-Datei der Regeln (JSON) als Blob-URL-Inhalt. */
export function exportPayload(state: Pick<RulesState, 'profile' | 'items' | 'templates'>, schoolName: string): string {
  return JSON.stringify(
    {
      format: 'schulmanager-regeln',
      version: 1,
      school: schoolName,
      profile: state.profile,
      items: state.items,
      templates: state.templates.filter((t) => !t.builtin),
    },
    null,
    2,
  );
}

/** Import prüfen: Form, Bausteine und Stufen (Details prüft der Server). */
export function parseImport(text: string): { profile: string; items: RuleItems; templates: RuleTemplate[] } {
  let raw: unknown;
  try {
    raw = JSON.parse(text);
  } catch {
    throw new Error('Die Datei ist kein gültiges JSON.');
  }
  if (!raw || typeof raw !== 'object' || (raw as { format?: string }).format !== 'schulmanager-regeln') {
    throw new Error(`Das ist keine Regel-Datei von ${APP_NAME} (format „schulmanager-regeln“ fehlt).`);
  }
  const r = raw as { profile?: unknown; items?: unknown; templates?: unknown };
  if (!r.items || typeof r.items !== 'object') throw new Error('Die Datei enthält keine Bausteine („items“).');
  return {
    profile: typeof r.profile === 'string' ? r.profile : '',
    items: r.items as RuleItems,
    templates: Array.isArray(r.templates) ? (r.templates as RuleTemplate[]) : [],
  };
}

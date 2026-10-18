/** Reine Hilfsfunktionen der Generator-Auswertung (testbar ohne Browser). */
import type { CostPart, EntityRow, Kpi, MoveItem, MoveKind, RuleRow, VariantSummary } from './types';

export function fmt(n: number | null | undefined): string {
  if (n === null || n === undefined || !Number.isFinite(n)) return '–';
  const r = Math.round(n * 10) / 10;
  return r.toLocaleString('de-DE', { maximumFractionDigits: 1 });
}

/** „1 Hinweis“, „2 Hinweise“ */
export function plural(n: number, one: string, many: string): string {
  return `${n} ${n === 1 ? one : many}`;
}

export type Verdict = 'besser' | 'schlechter' | 'gleich';

export function verdict(delta: number | null | undefined): Verdict {
  if (!delta) return 'gleich';
  return delta < 0 ? 'besser' : 'schlechter';
}

/** „11 → 5,5“ */
export function beforeAfter(k: Pick<Kpi, 'before' | 'after'>): string {
  return `${fmt(k.before)} → ${fmt(k.after)}`;
}

export function deltaText(delta: number | null | undefined): string {
  if (delta === null || delta === undefined) return '–';
  if (!delta) return 'unverändert';
  return `${delta > 0 ? '+' : '−'}${fmt(Math.abs(delta))} (${verdict(delta)})`;
}

/** Obergrenze einer Achse auf eine „runde“ Zahl (1, 2, 2.5, 5 × 10^n). */
export function niceMax(v: number): number {
  if (!(v > 0)) return 1;
  const exp = Math.floor(Math.log10(v));
  const f = v / 10 ** exp;
  const step = f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10;
  return step * 10 ** exp;
}

/** Achsenwerte von 0 bis zur runden Obergrenze (`n` Abschnitte). */
export function ticks(max: number, n = 4): number[] {
  const top = niceMax(max);
  if (n === 4 && Math.abs(top / 10 ** Math.floor(Math.log10(top)) - 2.5) < 1e-9) n = 5;   // 2,5 teilt sich nicht in 4 runde Schritte
  const out: number[] = [];
  for (let i = 0; i <= n; i++) out.push(Math.round(((top * i) / n) * 100) / 100);
  return out;
}

/** Achse von `min` bis `max` mit runden Schritten: `{lo, hi, ticks}` (für Linien, die nicht bei 0 beginnen müssen). */
export function niceRange(min: number, max: number, n = 4): { lo: number; hi: number; ticks: number[] } {
  if (!(max > min)) {
    const hi = niceMax(max);
    return { lo: 0, hi, ticks: ticks(hi, n) };
  }
  const step = niceMax((max - min) / n);
  const lo = Math.floor(min / step) * step;
  const hi = Math.ceil(max / step) * step;
  const out: number[] = [];
  for (let v = lo; v <= hi + step / 1000; v += step) out.push(Math.round(v * 100) / 100);
  return { lo, hi, ticks: out };
}

/** Kompakte Zahl für Achsen: 1.500 wird zu „1,5 Tsd.“. */
export function compact(n: number): string {
  const a = Math.abs(n);
  if (a >= 1_000_000) return `${fmt(n / 1_000_000)} Mio.`;
  if (a >= 1000) return `${fmt(n / 1000)} Tsd.`;
  return fmt(n);
}

/** Beschriftung kürzen. */
export function clip(text: string, max: number): string {
  if (max < 4 || text.length <= max) return text;
  return `${text.slice(0, max - 1).trimEnd()}…`;
}

export const MOVE_LABELS: Record<MoveKind | 'all', string> = {
  all: 'Alle',
  moved: 'Verschoben',
  room: 'Nur Raum',
  added: 'Neu',
  removed: 'Entfallen',
};

export interface MoveFilter {
  kind: MoveKind | 'all';
  /** nur Verschiebungen mit dieser Änderung */
  change: '' | 'Tag' | 'Stunde' | 'Raum';
  classId: string;
}

export function filterMoves(items: MoveItem[], f: MoveFilter): MoveItem[] {
  return items.filter(
    (m) => (f.kind === 'all' || m.kind === f.kind) && (!f.change || m.changes.includes(f.change)) && (!f.classId || m.classes.includes(f.classId)),
  );
}

/** Klassen, die in den Verschiebungen vorkommen (für den Filter). */
export function moveClasses(items: MoveItem[]): string[] {
  return [...new Set(items.flatMap((m) => m.classes))].sort((a, b) => a.localeCompare(b, 'de', { numeric: true }));
}

function afterOf(v: Pick<VariantSummary, 'kpis'>, key: string): number {
  return v.kpis.find((k) => k.key === key)?.after ?? 0;
}

/** Beste Variante: erst Konflikte, dann unverplante Stunden, dann Kosten (kleiner ist besser). */
export function bestVariant(variants: Pick<VariantSummary, 'index' | 'kpis'>[]): number {
  let best = variants[0]?.index ?? 0;
  let bestKey: number[] | null = null;
  for (const v of variants) {
    const key = [afterOf(v, 'conflicts'), afterOf(v, 'unplaced_hours'), afterOf(v, 'cost')];
    let smaller = bestKey === null;
    if (bestKey) {
      for (let i = 0; i < key.length; i++) {
        if (key[i] !== bestKey[i]) {
          smaller = (key[i] as number) < (bestKey[i] as number);
          break;
        }
      }
    }
    if (smaller) {
      best = v.index;
      bestKey = key;
    }
  }
  return best;
}

/** Je Kennzahl: Indizes der Varianten mit dem kleinsten Wert (nur wenn sich die Werte unterscheiden). */
export function bestPerKpi(variants: Pick<VariantSummary, 'index' | 'kpis'>[]): Record<string, Set<number>> {
  const out: Record<string, Set<number>> = {};
  const keys = variants[0]?.kpis.map((k) => k.key) ?? [];
  for (const key of keys) {
    const nums: { i: number; x: number }[] = [];
    for (const v of variants) {
      const x = v.kpis.find((k) => k.key === key)?.after;
      if (typeof x === 'number') nums.push({ i: v.index, x });
    }
    if (nums.length < 2) continue;
    const min = Math.min(...nums.map((v) => v.x));
    if (nums.every((v) => v.x === min)) continue;
    out[key] = new Set(nums.filter((v) => v.x === min).map((v) => v.i));
  }
  return out;
}

export function entityLabel(r: EntityRow): string {
  return r.name || r.id;
}

/** Zahl der Blöcke, die sich gegenüber dem Ausgangsplan unterscheiden. */
export function movedTotal(c: { moved: number; added: number; removed: number }): number {
  return c.moved + c.added + c.removed;
}

export interface Recommendation {
  tone: 'good' | 'bad' | 'neutral';
  title: string;
  /** Kennzahlen, die schlechter geworden sind („Hohlstunden Klassen: 19 → 22,5“) */
  worse: string[];
  /** Kennzahlen, die besser geworden sind */
  better: string[];
  advice: string;
}

/**
 * Empfehlung zum Übernehmen: Konflikte oder mehr unverplante Stunden bzw. mehr Strafpunkte sprechen dagegen.
 * `worse` nennt die schlechter gewordenen Kennzahlen (ohne die Strafpunkte selbst, sie sind deren Summe).
 */
export function recommendation(kpis: Kpi[]): Recommendation {
  const by = (key: string) => kpis.find((k) => k.key === key);
  const line = (k: Kpi) => `${k.label}: ${beforeAfter(k)}`;
  const detail = kpis.filter((k) => k.key !== 'cost');
  const worse = detail.filter((k) => k.better === false).map(line);
  const better = detail.filter((k) => k.better === true).map(line);
  const cost = by('cost');
  const hard = (by('conflicts')?.delta ?? 0) > 0 || (by('unplaced_hours')?.delta ?? 0) > 0;
  const costDelta = cost?.delta ?? 0;
  if (hard || costDelta > 0) {
    return {
      tone: 'bad',
      title: 'Nicht übernehmen – der aktuelle Plan ist besser',
      worse,
      better,
      advice: 'Mehr Rechenzeit wählen oder mehrere Varianten erzeugen.',
    };
  }
  if (costDelta < 0) {
    return { tone: 'good', title: 'Übernehmen empfohlen – der Entwurf ist besser', worse, better, advice: worse.length ? 'Einzelne Kennzahlen sind schlechter, in der Summe überwiegt die Verbesserung.' : '' };
  }
  return { tone: 'neutral', title: 'Kein Unterschied zum aktuellen Plan', worse, better, advice: 'Übernehmen lohnt sich nicht; mehr Rechenzeit kann bessere Pläne finden.' };
}

export interface PenaltyPart {
  id: string;
  title: string;
  /** Verstöße (Ø je Woche bzw. Stück) */
  before: number;
  after: number;
  weight: number;
  /** Strafpunkte = Verstöße × Gewicht */
  beforePoints: number;
  afterPoints: number;
}

/** Strafpunkte je Baustein aus der Auswertung des Generators (`cost_parts`, Summe = Strafpunkte insgesamt). */
export function costPartRows(ev: { cost_parts?: CostPart[] }): (PenaltyPart & { top: CostPart['top'] })[] {
  return (ev.cost_parts ?? []).map((p) => ({
    id: p.id,
    title: p.title,
    before: p.count_before,
    after: p.count_after,
    weight: p.weight_after || p.weight_before,
    beforePoints: p.points_before,
    afterPoints: p.points_after,
    top: p.top,
  }));
}

/** Strafpunkte je Ziel: Verstöße × Gewicht; unverplante Stunden zählen je 1000. Größte Anteile zuerst. */
export function penaltyParts(rules: RuleRow[], unplacedBefore: number, unplacedAfter: number): PenaltyPart[] {
  const parts: PenaltyPart[] = [];
  for (const r of rules) {
    if (r.weight === null || r.before === null || r.after === null || !r.weight) continue;
    if (!r.before && !r.after) continue;
    parts.push({ id: r.id, title: r.title, before: r.before, after: r.after, weight: r.weight, beforePoints: r.before * r.weight, afterPoints: r.after * r.weight });
  }
  if (unplacedBefore || unplacedAfter) {
    parts.push({ id: 'unplaced', title: 'Unverplante Stunden', before: unplacedBefore, after: unplacedAfter, weight: 1000, beforePoints: unplacedBefore * 1000, afterPoints: unplacedAfter * 1000 });
  }
  return parts.sort((a, b) => Math.max(b.afterPoints, b.beforePoints) - Math.max(a.afterPoints, a.beforePoints));
}

/** Typen der Generator-Auswertung (Spiegel von `schulmanager/generator_report.py`). */

export interface Kpi {
  key: string;
  label: string;
  unit: string;
  before: number | null;
  after: number | null;
  delta: number | null;
  better: boolean | null;
}

export interface EntityRow {
  id: string;
  name: string;
  before: number;
  after: number;
  delta: number;
}

export interface EntityGroup {
  better: EntityRow[];
  worse: EntityRow[];
  highest: EntityRow[];
  changed: number;
  better_count: number;
  worse_count: number;
  total: number;
}

export interface MoveSpot {
  day: number;
  start: number;
  length: number;
  rooms: string[];
}

export type MoveKind = 'moved' | 'room' | 'added' | 'removed';

export interface MoveItem {
  course: string;
  label: string;
  classes: string[];
  teachers: string[];
  kind: MoveKind;
  changes: string[];
  from: MoveSpot | null;
  to: MoveSpot | null;
}

export interface MoveCounts {
  unchanged: number;
  moved: number;
  room: number;
  added: number;
  removed: number;
  day: number;
  period: number;
  total_before: number;
  total_after: number;
}

export interface DistDay {
  day: number;
  label: string;
  before: number;
  after: number;
}

export interface DistPeriod {
  period: number;
  before: number;
  after: number;
}

export interface RuleRow {
  id: string;
  title: string;
  group: string;
  level: string;
  level_label: string;
  weight: number | null;
  before: number | null;
  after: number | null;
  delta: number | null;
  hard: boolean;
}

export interface Hint {
  kind: string;
  text: string;
  course: string | null;
}

export interface Evaluation {
  kpis: Kpi[];
  stats_before: Record<string, number>;
  stats_after: Record<string, number>;
  week_variants: number;
  entities: { classes: EntityGroup; teachers: EntityGroup; teachers_sites: EntityGroup };
  moves: { counts: MoveCounts; items: MoveItem[]; truncated: boolean };
  distribution: { days: DistDay[]; periods: DistPeriod[]; core_periods: DistPeriod[] };
  rules: RuleRow[];
  hints: Hint[];
  cost_before: number | null;
  /** Strafpunkte je Baustein (Anzahl × Gewicht = Punkte), Summe = Strafpunkte insgesamt; fehlt bei älteren Läufen */
  cost_parts?: CostPart[];
}

/** Ein Baustein der Strafpunkte (`Scheduler.cost_parts`); `rest` fasst Kleinstbeträge unter 2 % zusammen */
export interface CostPart {
  id: string;
  title: string;
  count_before: number;
  count_after: number;
  weight_before: number;
  weight_after: number;
  points_before: number;
  points_after: number;
  /** größte Verursacher (Klasse, Lehrkraft, Kurs) mit Strafpunkten im Entwurf */
  top: { name: string; points: number }[];
}

/** Ein Punkt des Verlaufs: [Sekunden, Schritte, Kosten] */
export type TracePoint = [number, number, number];

export interface RunInfo {
  index: number;
  seed: number;
  cost: number | null;
  unplaced: number;
  iterations: number;
  best: boolean;
  trace: TracePoint[];
}

export interface VariantSummary {
  index: number;
  seed: number;
  stats: Record<string, number | string>;
  unplaced_count: number;
  lessons_count: number;
  kpis: Kpi[];
  moved: number;
}

export interface UnplacedRow {
  course: string;
  label: string;
  weeks_text: string;
  missing: number;
  reason: string;
}

export interface VariantDetail {
  index: number;
  seed: number;
  stats: Record<string, number | string>;
  evaluation: Evaluation;
  trace: TracePoint[];
  runs: RunInfo[];
  unplaced: Record<string, unknown>[];
}

export interface SnapshotMeta {
  id: number;
  name: string;
  note: string;
  created_at: string | null;
  user: string;
  source: 'aktuell' | 'entwurf';
  /** Planzeitraum (Kennung); leer = ganzer Plan */
  period: string;
  period_name: string;
  scope: 'period' | 'whole';
  source_version: number | null;
  lessons_count: number;
  metrics: Record<string, number | null>;
}

export interface SnapshotDetail extends SnapshotMeta {
  evaluation: Evaluation;
}

export interface ApplyResult {
  lessons: number;
  warnings: string[];
  duties: number | null;
  duties_open: number | null;
}

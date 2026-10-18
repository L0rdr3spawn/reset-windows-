/**
 * Typen der Aufgaben-Erweiterungen im Kursraum (`schulmanager/server/routes/features_assignments.py`):
 * Bewertungsraster/Leitfaden, Notenschlüssel, Fristverlängerung, Versionen der Abgabe, Gruppen.
 */
import type { StoredFileInfo } from '../../../api/files';

export type RubricKind = 'rubric' | 'guide';

export interface RubricLevel {
  id: string;
  title: string;
  description: string;
  points: number;
}

export interface RubricCriterion {
  id: string;
  title: string;
  description: string;
  /** Raster: Stufen mit Punkten */
  levels?: RubricLevel[];
  /** Leitfaden: Höchstpunkte */
  max_points?: number;
}

export interface Rubric {
  kind: RubricKind;
  criteria: RubricCriterion[];
}

/** Ausfüllung je Kriterium: Raster → `level`, Leitfaden → `points`; `comment` optional */
export type RubricFill = Record<string, { level?: string; points?: number; comment?: string }>;

export interface ScaleStep {
  min: number;
  label: string;
}

export type GradeScale = { preset: 'noten' | 'punkte' } | { steps: ScaleStep[] };

export interface AssignSettings {
  group_mode: boolean;
  group_set_id: number | null;
  /** Höchstpunktzahl: aus dem Raster, sonst frei eingetragen */
  max_points: number | null;
  free_max_points: number | null;
  rubric: Rubric | null;
  rubric_title: string;
  template_id: number | null;
  grade_scale: GradeScale;
  scale_steps: ScaleStep[];
  show_parents: boolean;
  /** nur Lehrende */
  submission_count?: number;
  has_rubric_grades?: boolean;
  presets?: { id: string; label: string }[];
}

export interface SubmissionVersion {
  attempt: number;
  status: string;
  submitted_at: string | null;
  text: string;
  files: StoredFileInfo[];
  feedback: string;
  grade: string;
  points: number | null;
  max_points: number | null;
  rubric: RubricFill | null;
  feedback_files: StoredFileInfo[];
  feedback_at: string | null;
  feedback_by_name: string;
  closed_at: string | null;
}

export interface GroupRef {
  id: number;
  name: string;
}

export interface GroupWithMembers extends GroupRef {
  set_id: number;
  members: { user_id: number; name: string }[];
}

export interface ExtensionInfo {
  id?: number;
  due_at: string | null;
  reason: string;
  kind?: 'user' | 'group';
}

export interface Extension {
  id: number;
  user_id: number | null;
  group_id: number | null;
  name: string;
  due_at: string;
  reason: string;
  created_by_name: string;
  created_at: string;
}

export interface Template {
  id: number;
  title: string;
  kind: RubricKind;
  kind_label: string;
  rubric: Rubric | null;
  max_points: number | null;
  criteria_count: number;
  grade_scale: GradeScale | null;
  updated_at: string | null;
}

export interface AssignmentResult {
  channel_id: number;
  item_id: number;
  title: string;
  student_user_id: number;
  student_id: string | null;
  submission_id: number;
  points: number | null;
  max_points: number | null;
  percent: number | null;
  grade: string;
  grade_number: number | null;
  graded_at: string | null;
  attempt: number;
  late: boolean;
  group_id: number | null;
}

// ------------------------------------------------------------------ Gruppen im Kursraum
export interface GroupMember {
  user_id: number;
  name: string;
  class_id?: string | null;
}

export interface GroupEntry {
  id: number;
  name: string;
  position: number;
  members: GroupMember[];
}

export interface GroupSet {
  id: number;
  name: string;
  groups: GroupEntry[];
  /** nur Lehrende: noch keiner Gruppe zugeordnet */
  unassigned?: GroupMember[];
}

export interface GroupsResponse {
  sets: GroupSet[];
  can_manage: boolean;
  limits: { groups: number; sets: number };
  /** nur Lehrende: Material/Ordner, die auf Gruppen beschränkt sind (ID → Gruppen-IDs) */
  gates?: { items: Record<string, number[]>; folders: Record<string, number[]> };
  without_account?: number;
}

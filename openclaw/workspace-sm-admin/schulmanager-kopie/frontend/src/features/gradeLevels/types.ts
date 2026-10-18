/** Jahrgänge (Backend `/grade-profiles`, Logik `schulmanager/grade_profiles.py`) und Klassenstufen (`/grade-levels`). */
import type { GradeProfile } from '../../api/types';

export interface GradeClassRow {
  id: string;
  name: string;
  grade: number;
  profile?: string | null;
  site: string;
  site_name: string;
  /** erfasste Schüler/innen, sonst die Zahl an der Klasse */
  students: number;
  students_listed: number;
  class_teacher: { id: string; name: string } | null;
  curriculum_id: string | null;
  curriculum_name: string | null;
  curriculum_source: 'class' | 'profile' | 'grade' | null;
  curriculum_conflict: boolean;
  courses: number;
  open_courses: number;
}

/** Ein Jahrgang mit seinen Klassen und Zahlen (`GET /grade-profiles`). */
export interface ProfileRow extends GradeProfile {
  classes: GradeClassRow[];
  students: number;
  courses: number;
  open_courses: number;
  curriculum_info: { id: string; name: string; hours: number; base: string | null; subjects: number } | null;
  curriculum_missing: boolean;
}

export interface CurriculumOption {
  id: string;
  name: string;
  hours: number;
  for_classes: boolean;
  base: string | null;
  grades: number[];
}

export interface ProfilesResponse {
  grade_min: number;
  grade_max: number;
  profiles: ProfileRow[];
  /** Klassen ohne Jahrgang, je Klassenstufen-Nummer */
  unassigned: { grade: number; classes: GradeClassRow[] }[];
  curricula: CurriculumOption[];
  migration: { pending: boolean; profiles: number; classes: number };
  can_edit: boolean;
  can_plan: boolean;
  can_write: boolean;
}

export interface MigrationRow {
  id: string;
  name: string;
  grade: number;
  curriculum: string | null;
  curriculum_name: string | null;
  classes: string[];
  conflict: boolean;
  exists: boolean;
  candidates?: string[];
}

export interface MigrationPreview {
  pending: boolean;
  profiles: MigrationRow[];
  classes: number;
  applied?: boolean;
}

/** Stundentafel eines Jahrgangs beim Anlegen/Ändern: vorhandene, neue leere oder von `base` abgeleitet. */
export interface CurriculumChoice {
  id?: string | null;
  new?: boolean;
  base?: string | null;
  name?: string | null;
}

export interface ProfileInput {
  name: string;
  short: string;
  grade: number | null;
  color: string;
  description: string;
  department: string;
  curriculum?: CurriculumChoice | null;
  class_ids?: string[];
}

export interface ProfileImpact {
  id: string;
  name: string;
  classes: { id: string; name: string }[];
  courses: number;
  lessons: number;
  curriculum: { id: string; name: string; shared: boolean; derived: string[] } | null;
  alternatives: { id: string; name: string; grade: number | null; color: string }[];
}

export interface CurriculumImpact {
  id: string;
  name: string;
  profiles: { id: string; name: string }[];
  classes: { id: string; name: string }[];
  courses: number;
  lessons: number;
  derived: { id: string; name: string }[];
  alternatives: { id: string; name: string }[];
}

export interface SubjectImpact {
  id: string;
  curricula: { id: string; name: string }[];
  courses: number;
  lessons: number;
  teachers: number;
  exams: number;
}

/** `GET /grade-profiles/matrix`: je Stundentafel die wirksamen Zeilen und das Ist aus den Kursen. */
export interface MatrixCurriculum {
  id: string;
  name: string;
  base: string | null;
  classes_only: string[];
  grades: number[];
  profiles: string[];
  derived: string[];
  applies: string[];
  conflicts: string[];
  effective: { subject: string; hours: number; double: boolean }[];
  hours: number;
  /** Ist je Fach: Kursstunden im Mittel über die Klassen der Tafel */
  actual: Record<string, number>;
  actual_hours: number;
}

export interface MatrixResponse {
  curricula: MatrixCurriculum[];
  profiles: GradeProfile[];
  class_names: Record<string, string>;
  subjects: { id: string; name: string; color?: string }[];
}

// ---------------------------------------------------------------- Klassenstufen (Klassen anlegen/löschen)

export interface ClassImpact {
  id: string;
  name: string;
  grade: number;
  students: number;
  courses_deleted: number;
  courses_shared: number;
  lessons: number;
  curricula: string[];
  absences: number;
}

export interface ImpactTotals {
  students: number;
  courses_deleted: number;
  courses_shared: number;
  lessons: number;
  absences: number;
}

export interface ImpactResponse {
  classes: ClassImpact[];
  totals: ImpactTotals;
}

export interface CreateClassesResult {
  created: string[];
  warnings: string[];
  open_parts: string[];
}

export interface DeleteClassesResult {
  deleted: string[];
  moved_students: number;
  impact: ImpactTotals;
}

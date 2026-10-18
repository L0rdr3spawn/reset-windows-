/**
 * Typen der Klassen-Seite (ARCHITECTURE.md §10.2) – Spiegel von `schulmanager/server/routes/features_classes.py`.
 * Alle Stunden 0-basiert (0 = 1. Stunde), Wochentag 0 = Montag.
 */
import type { AbsenceKind, DayKind, EffectiveCell, TimeRule, WeekInfo } from '../../api/types';

/** Verweis mit Anzeigenamen (Lehrkraft, Raum …) */
export interface NamedRef {
  id: string;
  name: string;
}

// ---------------------------------------------------------------------------------------------- GET /classes

export interface ClassListItem {
  id: string;
  name: string;
  grade: number;
  site: string;
  site_name: string;
  home_room: NamedRef | null;
  class_teacher: NamedRef | null;
  student_count: number;
  course_count: number;
  teacher_count: number;
}

export interface ClassListResponse {
  classes: ClassListItem[];
  can_edit: boolean;
  can_plan: boolean;
}

// ---------------------------------------------------------------------------------------------- GET /classes/{id}

export interface HomeRoom {
  id: string;
  name: string;
  type: string;
  capacity: number;
  site: string;
}

export interface ClassInfo {
  id: string;
  name: string;
  grade: number;
  site: string;
  site_name: string;
  max_periods_per_day: number;
  unavailable: TimeRule[];
  home_room: HomeRoom | null;
  class_teacher: NamedRef | null;
  /** Jahrgang der Klasse (`GradeProfile`) */
  profile?: NamedRef | null;
  /** R3 (V12): Planungsfeld; [] = Schulvorgabe */
  school_days?: number[];
  /** R3: wirksame Werte und fertiger Text vom Server („Standard · Mo–Fr“) */
  plan?: { school_days: number[]; text: string };
  /** Klassenarbeiten je Woche/Tag: eigene Werte (null = Vorgabe) und die wirksamen Werte samt Quelle */
  max_exams_per_week?: number | null;
  max_exams_per_day?: number | null;
  exam_limits?: ExamLimits;
}

/** Wirksame Höchstzahlen für Klassenarbeiten (Schule → Jahrgang → Klasse) */
export interface ExamLimits {
  per_week: number;
  per_day: number;
  source_week: 'school' | 'grade' | 'class';
  source_day: 'school' | 'grade' | 'class';
  text: string;
}

/** Fach → Kurs/Kursteil → Lehrkraft */
export interface ClassSubject {
  course_id: string;
  /** Kursteil (Index in `course.parts`); `null` = Kurs ohne Teilung */
  part: number | null;
  label: string;
  subject: string;
  subject_name: string;
  teacher: NamedRef | null;
  hours: number;
  /** alle Klassen des Kurses (bei Kopplung mehrere) */
  classes: string[];
  coupled: boolean;
}

export interface ClassTeacher {
  id: string;
  name: string;
  is_class_teacher: boolean;
  subjects: string[];
  hours: number;
}

export interface StudentCourse {
  course_id: string;
  part: number | null;
  label: string;
}

export interface ClassStudent {
  id: string;
  name: string;
  courses: StudentCourse[];
  /** nur mit Recht „Geburtsdatum pflegen“ (Klassenleitung der Klasse, Sekretariat, Schulleitung, Administration) */
  birth_date?: string | null;
  can_set_birth_date?: boolean;
}

export interface RoomChoice {
  id: string;
  name: string;
  type: string;
  site: string;
  capacity: number;
  /** Klassen, deren Klassenraum dieser Raum schon ist */
  home_of: string[];
}

export interface ClassDetail {
  class: ClassInfo;
  subjects: ClassSubject[];
  teachers: ClassTeacher[];
  /** nur mit `students.read` im Scope, sonst `null` */
  students: ClassStudent[] | null;
  student_count: number;
  /** nur mit `can_edit` */
  room_choices?: RoomChoice[];
  /** nur mit `can_edit` */
  teacher_choices?: NamedRef[];
  /** `masterdata.edit` */
  can_edit: boolean;
  /** `substitution.edit` */
  can_plan: boolean;
  /** R3 (V12): `timetable.edit` – Unterrichtstage der Klasse ändern */
  can_edit_plan?: boolean;
}

// ---------------------------------------------------------------------------------------------- Stundentafel

export interface CurriculumRow {
  subject: string;
  hours: number;
  double: boolean;
  teachers?: string[];
}

export interface CurriculumSubject {
  id: string;
  name: string;
  room_type: string | null;
}

/** GET /classes/{id}/curriculum */
export interface ClassCurriculum {
  class_id: string;
  class_name: string;
  grade: number;
  source: 'class' | 'profile' | 'grade' | null;
  /** Jahrgang der Klasse */
  profile?: { id: string; name: string; color: string } | null;
  curriculum_id: string | null;
  curriculum_name: string | null;
  entries: (CurriculumRow & { subject_name: string; teachers: string[] })[];
  total_hours: number;
  subjects: CurriculumSubject[];
  can_edit: boolean;
}

export interface ClassCurriculumResult {
  added: string[];
  removed: string[];
  changed: string[];
  unchanged: string[];
  warnings: string[];
  open_parts: string[];
  curriculum: ClassCurriculum;
}

// ---------------------------------------------------------------------------------------------- PATCH /classes/{id}

export interface ClassPatch {
  home_room?: string | null;
  class_teacher?: string | null;
  apply_to_timetable?: boolean;
  /** R3 (V12, Recht `timetable.edit`); 409 `plan_change` ohne `?force=1` */
  school_days?: number[];
  /** Klassenarbeiten je Woche/Tag (`masterdata.edit`); `exam_limits_inherit` löscht eigene Werte → Vorgabe gilt */
  max_exams_per_week?: number | null;
  max_exams_per_day?: number | null;
  exam_limits_inherit?: boolean;
  /** Jahrgang (`masterdata.edit` oder `timetable.edit`); leer = keine Zuordnung */
  profile?: string | null;
}

export interface ClassPatchResult {
  class: ClassInfo;
  warnings: string[];
  moved_lessons: number;
  skipped: string[];
}

// ---------------------------------------------------------------------------------------------- GET /classes/{id}/week

/** Zelle wie `/me/today` (`effective_cells(day, "class", id)`); `dropped` = „Unterricht entfällt“ (§10.1), falls geliefert. */
export interface WeekCell extends EffectiveCell {
  dropped?: boolean;
}

export interface ClassWeekDay {
  date: string;
  weekday: number;
  holiday: string | null;
  cells: WeekCell[];
  /** R3: `kein_unterrichtstag` an Tagen ohne Unterricht der Klasse */
  day_kind?: DayKind;
  has_items?: boolean;
}

export interface WeekAbsence {
  id: string;
  kind: AbsenceKind;
  ref: string;
  ref_name: string;
  date_from: string;
  date_to: string;
  periods: number[];
  /** nur mit `substitution.edit` */
  reason?: string;
  can_delete: boolean;
}

export interface ClassWeek {
  class_id: string;
  week_start: string;
  /** R3: laufende Woche und KW */
  week_info?: WeekInfo;
  /** Anzahl Stunden pro Tag */
  periods: number;
  period_times: string[];
  days: ClassWeekDay[];
  absences: WeekAbsence[];
  can_plan: boolean;
}

// ---------------------------------------------------------------------------------------------- POST /classes/{id}/not-taking-place

export type NotTakingPlaceMode = 'lesson' | 'class';

export interface NotTakingPlaceBody {
  mode: NotTakingPlaceMode;
  date_from: string;
  date_to?: string;
  periods?: number[];
  course_id?: string;
  part?: number | null;
  reason: string;
  escort_teachers?: string[];
  dry_run: boolean;
}

/** Eine Änderung im Vertretungsplan (Unterschied vorher/nachher, auch andere Klassen). */
export interface PreviewChange {
  kind: string;
  classes: string[];
  period: number;
  subject: string | null;
  teacher: string | null;
  substitute: string | null;
  room: string | null;
  note: string;
  /** optional (nicht im Vertrag): Herkunftsstunde einer Verlegung – sonst aus `note` gelesen */
  moved_from?: number | null;
  /** optional (Eintrag der Engine, §10.1): Unterricht findet laut `lesson`-Abwesenheit nicht statt */
  dropped?: boolean;
  /** optional: Eintrag mit Warnung (z. B. keine Vertretung gefunden) */
  warning?: boolean;
  /** optional (nicht im Vertrag): Art des Unterschieds; `removed` = Eintrag entfällt durch die Umstellung */
  op?: 'added' | 'changed' | 'removed';
}

export interface PreviewDay {
  date: string;
  changes: PreviewChange[];
  /** optional: neue Warnungen des Tagesplans durch die Umstellung */
  warnings?: string[];
}

export interface NotTakingPlaceResult {
  preview: PreviewDay[];
  summary: string;
  absences?: WeekAbsence[];
}

// ---------------------------------------------------------------------------------------------- POST /classes, /classes/{id}/students (§11.3)

export interface NewStudentBody {
  first_name: string;
  last_name: string;
  email: string | null;
  /** ISO-Datum – daraus wird die Volljährigkeit abgeleitet */
  birth_date: string | null;
  /** nur maßgeblich ohne Geburtsdatum */
  adult: boolean;
  parents: { name: string; email: string | null }[];
}

export type SendTo = 'student' | 'parents' | 'both';

export interface AccountOptionsBody {
  create_student_accounts: boolean;
  create_parent_accounts: boolean;
  /** Zugangsbriefe nach dem Anlegen sofort per E-Mail */
  send_email: boolean;
  /** Ziel bei Minderjährigen (Volljährige bekommen ihren Brief selbst) */
  send_to: SendTo;
  dry_run: boolean;
}

export interface ClassCreateBody extends AccountOptionsBody {
  id: string;
  name?: string;
  grade: number;
  site?: string | null;
  home_room?: string | null;
  class_teacher?: string | null;
  students: NewStudentBody[];
}

export interface PlannedParentAccount {
  username: string;
  display_name: string;
  email: string | null;
  /** vorhandenes Elternkonto (gleiche E-Mail) – Kind wird ergänzt */
  existing: boolean;
}

export interface CreatedStudent {
  index: number;
  /** Schüler-ID (bei der Vorschau voraussichtlich) */
  id: string;
  name: string;
  first_name: string;
  last_name: string;
  email: string | null;
  birth_date: string | null;
  adult: boolean;
  /** Benutzername des Schülerkontos (geplant bzw. angelegt) */
  username: string | null;
  parent_accounts: PlannedParentAccount[];
  user_id?: number | null;
}

export interface CreatedAccount {
  user_id: number;
  username: string;
  display_name: string;
  role: string;
  student_id: string | null;
  children: string[];
}

export interface CreateStudentsResult {
  dry_run: boolean;
  class: ClassInfo;
  students: CreatedStudent[];
  warnings: string[];
  accounts: CreatedAccount[];
  linked_parents: { user_id: number; username: string; display_name: string; student_ids: string[] }[];
  letter_batch: { id: string; expires_at: string; count?: number } | null;
  email: {
    sent: { user_id: number; display_name: string; role: string; recipients?: string[] }[];
    no_address: { user_id: number; display_name: string; role: string }[];
    unavailable: { user_id: number; display_name: string; role: string }[];
  } | null;
}

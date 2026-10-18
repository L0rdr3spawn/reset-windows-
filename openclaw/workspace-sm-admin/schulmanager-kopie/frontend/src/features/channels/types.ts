/**
 * Antworttypen der Kursraum-Endpunkte (`schulmanager/server/routes/features_channels.py`, ARCHITECTURE.md §9.4).
 * Zeitpunkte sind ISO-8601 in UTC mit `Z`, Datumsangaben `YYYY-MM-DD`.
 */
import type { StoredFileInfo } from '../../api/files';
import type { AbsenceLogEvent, ReportInfo } from '../../api/types';
import type { AssignSettings, ExtensionInfo, GroupRef, GroupWithMembers, RubricFill, SubmissionVersion, Extension } from './assign/types';
import type { Availability, CompletionMode, CompletionRule } from './progress';

export type ChannelKind = 'course' | 'class' | 'custom';
export type ChannelRole = 'teacher' | 'student' | 'supervisor' | 'parent';
export type ItemType = 'file' | 'link' | 'text' | 'assignment';
export type Visibility = 'visible' | 'hidden' | 'scheduled' | 'lesson';
/** Eingabe: zusätzlich „zur nächsten stattfindenden Stunde“ (der Server bindet an diese Stunde) */
export type VisibilityChoice = Visibility | 'next_lesson';
/** Sichtbarkeit für Teilnehmende zum aktuellen Zeitpunkt (nur Lehrende/Aufsicht) */
export type ItemState = 'visible' | 'hidden' | 'scheduled' | 'lesson' | 'folder_hidden';
export type SubmissionStatus = 'offen' | 'ueberfaellig' | 'abgegeben' | 'verspaetet' | 'bewertet' | 'zurueckgegeben';

export interface ChannelStats {
  new_items: number;
  new_posts: number;
  open_assignments: number;
  to_grade: number;
  last_activity: string | null;
}

export interface Channel extends Partial<ChannelStats> {
  id: number;
  kind: ChannelKind;
  kind_label: string;
  ref: string | null;
  title: string;
  subtitle: string;
  description: string;
  role: ChannelRole | null;
  role_label: string;
  classes: string[];
  subject: string | null;
  subject_name: string | null;
  course_id: string | null;
  part: number | null;
  grade: number | null;
  teachers: string[];
  teacher_count: number;
  class_teacher: string | null;
  archived: boolean;
  /** Kurs/Klasse gibt es im Planungsdokument nicht mehr */
  orphaned: boolean;
  settings: { students_can_post: boolean; students_can_reply: boolean; progress_parents?: boolean };
}

export interface ChildRef {
  id: string;
  name: string;
  class_id?: string | null;
  /** Eltern dürfen die Kursräume sehen (minderjährig oder vom volljährigen Kind erlaubt) */
  allowed?: boolean;
}

export interface ChannelListResponse {
  channels: Channel[];
  supervisor: boolean;
  can_create: boolean;
  all: boolean;
  count: number;
  now: string;
  /** `no_teacher_link`: Lehrkraft-Konto ohne Zuordnung */
  notice?: 'no_teacher_link' | null;
  notice_text?: string | null;
  // Elternansicht
  parent?: boolean;
  children?: ChildRef[];
  student_id?: string | null;
  restricted?: boolean;
}

export interface ChannelPermissions {
  manage: boolean;
  post: boolean;
  reply: boolean;
  moderate: boolean;
  submit: boolean;
  view_submissions: boolean;
  supervise: boolean;
  add_members: boolean;
  add_teachers?: boolean;
  archive: boolean;
  parent?: boolean;
  lessons: boolean;
  /** alles ändern (Kursräume: alle Lehrenden; Klassenräume: Klassenleitung/Kursraum-Verwaltung) */
  manage_all?: boolean;
  members?: boolean;
  /** Fortschrittsübersicht, Abschluss- und Freigaberegeln (Lehrende) */
  progress?: boolean;
  /** Eltern: Lehrkraft hat den Lernfortschritt freigegeben */
  progress_parents?: boolean;
  /** Papierkorb ansehen (Lehrende) und – mit dem Recht `channels.trash` – wiederherstellen/endgültig löschen */
  trash?: boolean;
  trash_restore?: boolean;
}

export interface Folder {
  id: number;
  parent_id: number | null;
  name: string;
  position: number;
  /** nur Lehrende/Aufsicht */
  hidden?: boolean;
  /** selbst oder über einen übergeordneten Ordner nicht freigegeben (nur Lehrende/Aufsicht) */
  hidden_effective?: boolean;
  visibility?: Visibility;
  state?: ItemState;
  state_label?: string;
  visible_from?: string | null;
  release_at?: string | null;
  lesson?: LessonBinding | null;
  own?: boolean;
  can_edit?: boolean;
}

export interface LessonShift {
  /** `verschoben` (Entfall/schulfrei → nächste stattfindende Stunde) oder `verlegt` (am selben Tag) */
  status: 'verschoben' | 'verlegt';
  reason: string;
  release_at: string | null;
  to_label: string | null;
  to_date: string | null;
}

export interface LessonBinding {
  date: string;
  lesson_id: string;
  period: number;
  label: string;
  key: string;
  /** nur Lehrende/Aufsicht */
  shift?: LessonShift | null;
}

export interface OwnSubmissionState {
  status: SubmissionStatus;
  status_label: string;
  submitted_at: string | null;
  has_feedback: boolean;
  /** Frist, die für diese Person gilt (mit Verlängerung) */
  due_at?: string | null;
}

export interface SubmissionCounts {
  expected: number;
  submitted: number;
  to_grade: number;
  graded: number;
  returned: number;
  late: number;
}

export interface Item {
  id: number;
  channel_id: number;
  folder_id: number | null;
  type: ItemType;
  type_label: string;
  title: string;
  url: string | null;
  file: StoredFileInfo | null;
  attachments: StoredFileInfo[];
  has_body: boolean;
  position: number;
  due_at: string | null;
  allow_late: boolean;
  created_at: string | null;
  updated_at: string | null;
  available_at: string | null;
  /** für Teilnehmende sichtbar */
  visible: boolean;
  is_new: boolean;
  lesson: LessonBinding | null;
  /** Unterrichtsmaterial: erscheint im Bereich „Unterricht“ beim Datum `material_date` */
  lesson_material?: boolean;
  material_date?: string | null;
  /** Abgabe möglich (Aufgaben immer) */
  submittable?: boolean;
  /** Klassenraum: angeheftete Infokarte (Bereich „Klasse“), nicht Teil des Materials */
  info_card?: boolean;
  // nur Lehrende/Aufsicht
  visibility?: Visibility;
  state?: ItemState;
  state_label?: string;
  visible_from?: string | null;
  release_at?: string | null;
  created_by_name?: string;
  own?: boolean;
  /** ändern/verbergen/löschen erlaubt (Klassenräume: nur eigenes, außer Klassenleitung/Verwaltung) */
  can_edit?: boolean;
  /** Abgaben sehen/bewerten erlaubt */
  can_grade?: boolean;
  // Lernfortschritt
  /** Teilnehmende/Eltern: gesperrt – nur Titel, „Verfügbar, sobald …“ steht in `locked_text` */
  locked?: boolean;
  locked_text?: string;
  /** „Erledigt“-Häkchen (nur wenn die Lehrkraft eine Abschlussbedingung festgelegt hat) */
  completion?: { mode: CompletionMode; mode_label: string; done: boolean; can_toggle: boolean };
  /** Lehrende: Abschlussbedingung und bedingte Freigabe */
  completion_rule?: CompletionRule | null;
  availability?: Availability | null;
  // Aufgaben
  submission?: OwnSubmissionState;
  submissions?: SubmissionCounts;
  // nur Einzelabruf
  body?: string;
  my_submission?: Submission | null;
}

export interface ChannelDetail {
  channel: Channel;
  permissions: ChannelPermissions;
  /** Elternansicht: gewähltes Kind und alle Kinder im Kursraum */
  child?: ChildRef | null;
  children?: ChildRef[];
  folders: Folder[];
  items: Item[];
  last_seen_at: string | null;
  next_release_at: string | null;
  now: string;
  limits: {
    max_body: number;
    max_attachments: number;
    max_upload_items: number;
    max_post: number;
    max_submission_text: number;
    max_grade: number;
  };
}

export type LessonStatus = 'normal' | 'geaendert' | 'entfall' | 'verlegt';

export interface UpcomingLesson {
  key: string;
  date: string;
  weekday: number;
  /** laufende Woche des Schuljahres */
  week_no: number;
  lesson_id: string;
  course_id: string;
  parts: number[];
  period: number;
  length: number;
  period_label: string;
  effective_period: number;
  time: string;
  end_time: string;
  label: string;
  subject: string;
  subject_name: string;
  teachers: string[];
  rooms: string[];
  classes: string[];
  status: LessonStatus;
  changes: string[];
  moved_to: number | null;
  substitutes: string[];
  new_rooms: string[];
  exam: string | null;
  release_at: string | null;
  started: boolean;
  items: { id: number; title: string; type: ItemType }[];
}

export interface LessonsResponse {
  from: string;
  to: string;
  lessons: UpcomingLesson[];
  skipped: { date: string; reason: string; count: number }[];
  custom: boolean;
  all: boolean;
  now?: string;
}

export interface Submission {
  id: number;
  item_id: number;
  status: SubmissionStatus;
  status_label: string;
  submitted_at: string | null;
  late: boolean;
  text: string;
  files: StoredFileInfo[];
  feedback: string;
  grade: string;
  feedback_files: StoredFileInfo[];
  feedback_at: string | null;
  feedback_by_name: string;
  updated_at: string | null;
  can_edit: boolean;
  /** Version der Abgabe (1 = erste; „Überarbeitung anfordern“ öffnet die nächste) */
  attempt: number;
  revision_due_at: string | null;
  /** Punkte/Raster: für Eltern nur bei Freigabe (sonst `null`) */
  points: number | null;
  max_points: number | null;
  percent: number | null;
  rubric: RubricFill | null;
  /** Gruppenabgabe: Bewertung weicht von der Gruppe ab (Einzelanpassung) */
  individual: boolean;
  group_id: number | null;
  /** frühere Versionen mit Rückmeldung (älteste zuerst) */
  versions: SubmissionVersion[];
}

export interface MySubmissionResponse {
  item_id: number;
  status: SubmissionStatus;
  status_label: string;
  due_at: string | null;
  /** Frist, die für diese Person gilt (mit Verlängerung bzw. Frist der Überarbeitung) */
  effective_due_at: string | null;
  extension: { due_at: string | null; reason: string } | null;
  allow_late: boolean;
  can_submit: boolean;
  /** Gruppenabgabe, aber noch keiner Gruppe zugeordnet */
  needs_group: boolean;
  group: GroupWithMembers | null;
  settings: AssignSettings;
  submission: Submission | null;
}

export interface SubmissionRow {
  student_id: string | null;
  name: string;
  class_id: string | null;
  user_id: number | null;
  has_account: boolean;
  member: boolean;
  status: SubmissionStatus;
  status_label: string;
  /** abgegeben nach der für diese Person geltenden Frist */
  late: boolean;
  /** geltende Frist (mit Verlängerung) */
  due_at: string | null;
  extension: ExtensionInfo | null;
  group: GroupRef | null;
  /** Nachteilsausgleich-Hinweise (nur Berechtigte) */
  support: string[];
  submission: Submission | null;
}

export interface SubmissionsResponse {
  item: Item;
  rows: SubmissionRow[];
  counts: Partial<Record<SubmissionStatus | 'late', number>>;
  total: number;
  settings: AssignSettings;
  /** Gruppen der Einteilung (nur bei Gruppenabgabe) */
  groups: GroupRef[];
  without_group: number;
  extensions: Extension[];
}

export interface Post {
  id: number;
  parent_id: number | null;
  author_name: string;
  author_is_teacher: boolean;
  own: boolean;
  body: string;
  deleted: boolean;
  pinned: boolean;
  created_at: string | null;
  edited_at: string | null;
  attachments: StoredFileInfo[];
  can_edit: boolean;
  can_delete: boolean;
  can_pin: boolean;
  replies?: Post[];
}

export interface PostsResponse {
  posts: Post[];
  has_more: boolean;
  next_before: number | null;
  permissions: ChannelPermissions;
}

export interface MembersResponse {
  teachers: { id: string; name: string; class_teacher: boolean; has_account?: boolean }[];
  students: { id: string | null; name: string; class_id: string | null; has_account?: boolean; user_id?: number | null }[];
  extra: MemberExtra[];
  /** aus dem Stundenplan ausgetragene Schüler/innen (nur Lehrende/Aufsicht) */
  excluded: MemberExtra[];
  /** Eltern mit Lesezugriff über ihre Kinder (nur Lehrende/Aufsicht) */
  parents: { user_id: number; name: string; children: string[] }[];
  counts: { teachers: number; students: number; parents?: number };
  can_manage_members: boolean;
  can_add_teachers?: boolean;
  creator_id?: number | null;
}

export interface MemberExtra {
  user_id: number | null;
  name: string;
  role: 'teacher' | 'student' | 'excluded';
  role_label: string;
  account_role: string | null;
  added_at: string | null;
  self: boolean;
  creator?: boolean;
  class_id?: string | null;
}

export interface MemberCandidate {
  user_id: number;
  name: string;
  username: string;
  account_role: string;
  class_id: string | null;
  member: boolean;
}

export interface OverviewEntry {
  channel_id: number;
  channel_title: string;
  item_id: number;
  title: string;
  type: ItemType;
  type_label: string;
  due_at: string | null;
  available_at?: string;
  status?: SubmissionStatus;
  status_label?: string;
  overdue?: boolean;
}

export interface TeacherLesson extends UpcomingLesson {
  channel_id: number;
  channel_title: string;
  ended: boolean;
}

export interface OverviewResponse {
  role: 'teacher' | 'student' | 'supervisor' | 'none' | 'parent';
  now: string;
  no_teacher_link?: boolean;
  teacher?: {
    day: string | null;
    is_today: boolean;
    lessons: TeacherLesson[];
    to_grade: { channel_id: number; channel_title: string; item_id: number; title: string; due_at: string | null; count: number }[];
    to_grade_total: number;
  };
  student?: { new_items: OverviewEntry[]; due: OverviewEntry[]; open_assignments: number };
}

/** Sichtbarkeit beim Anlegen/Freigeben (Eingabe) */
export interface VisibilityInput {
  visibility: VisibilityChoice;
  /** ISO mit Zeitzone (`Z`) */
  visible_from?: string | null;
  lesson?: { date: string; lesson_id: string; period: number } | null;
}

/** Bereich „Klasse“ im Klassenraum (`GET /channels/{id}/klasse`) */
export interface ClassContact {
  teacher_id: string;
  name: string;
  class_teacher: boolean;
  subjects: { id: string; name: string }[];
}

export interface ClassEvent {
  id: string;
  title: string;
  kind: string;
  date_from: string;
  date_to: string;
  time_from: string;
  time_to: string;
  location: string;
  note: string;
  parents_evening: boolean;
  /** betrifft nur diese Klasse */
  own: boolean;
  can_delete: boolean;
}

export interface ClassOverview {
  class_id: string;
  class_name: string;
  contacts: ClassContact[];
  events: ClassEvent[];
  plan_links: { label: string; to: string }[];
  can_add_event: boolean;
  default_event_title: string;
}

/** GET /channels/{id}/klasse/absences – „Fehlzeiten & Meldungen“ (nur Lehrkräfte des Klassenraums) */
export interface ClassAbsenceReport extends ReportInfo {
  absence_id: number;
  date_from: string;
  date_to: string;
  periods: number[];
  kind: string;
  kind_label: string;
  /** nur volle Sicht */
  status?: string;
  status_label?: string;
  history?: AbsenceLogEvent[];
  last_change?: AbsenceLogEvent | null;
}

export interface ClassAbsences {
  class_id: string;
  from: string;
  to: string;
  pupils: number;
  full: boolean;
  students: { id: string; name: string; level: 'full' | 'presence'; reports: ClassAbsenceReport[] }[];
}

export interface ClassEventInput {
  title: string;
  date_from: string;
  date_to?: string | null;
  time_from?: string;
  time_to?: string;
  location?: string;
  note?: string;
}

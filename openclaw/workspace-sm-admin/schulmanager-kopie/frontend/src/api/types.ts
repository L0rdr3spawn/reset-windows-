/**
 * Typen gemäß Schnittstellenvertrag (docs/ARCHITECTURE.md §3, §4, §6).
 * Alle Zeitangaben 0-basiert: Tag 0 = Montag, Stunde 0 = 1. Stunde, Woche 0 = A.
 */

export type Role =
  | 'admin'
  | 'schulleitung'
  | 'abteilungsleitung'
  | 'planer'
  | 'sekretariat'
  | 'lehrer'
  | 'hausmeister'
  | 'schulbegleitung'
  | 'schueler'
  | 'eltern'
  | 'monitor'
  | 'zuschauer';

export type Permission =
  | 'users.manage'
  | 'settings.edit'
  | 'masterdata.edit'
  | 'timetable.generate'
  | 'timetable.edit'
  | 'substitution.edit'
  | 'absence.report_self'
  | 'exam.edit'
  | 'announcement.post'
  | 'plans.read_all'
  | 'students.read'
  | 'student_absence.report'
  | 'student_absence.read'
  | 'students.birth_date'
  | 'forms.submit'
  | 'forms.inbox'
  | 'forms.manage'
  | 'audit.read'
  /** Datenschutz (docs/DATENSCHUTZ-LOESCHKONZEPT.md): Löschkonzept verwalten / Auskunft und Sofort-Löschen */
  | 'privacy.manage'
  | 'privacy.subject'
  | 'history.restore'
  | 'system.admin'
  | 'monitor.read'
  | 'substitution.read'
  | 'monitor.manage'
  | 'profile.teacher_self'
  | 'teacher_requests.review'
  | 'channels.use'
  | 'channels.manage'
  | 'channels.trash'
  | 'channels.view_children'
  | 'messages.use'
  | 'messages.broadcast'
  | 'messages.moderate'
  | 'student_documents.read'
  | 'login_policy.manage'
  | 'rights.manage'
  | 'rooms.read'
  | 'masterdata.read'
  | 'register.read_all'
  | 'duties.manage'
  | 'substitution.self_study'
  | 'exam.types.manage'
  | 'support.read'
  | 'support.manage'
  | 'support.catalog'
  | 'support.hints'
  | 'chats.review'
  | 'license.manage'
  /** API-Zugänge für Apps/KIs (docs/API-ZUGAENGE.md): eigene ausgeben / alle verwalten */
  | 'api.own'
  | 'api.manage'
  /** Kompetenzraster und Lernstand (docs/KOMPETENZEN.md): lesen / eintragen / Rahmen und Abzeichen verwalten */
  | 'competency.read'
  | 'competency.assess'
  | 'competency.manage'
  | 'gradebook.use'
  | 'gradebook.read_class'
  | 'gradebook.manage'
  | 'gradebook.export'
  /** §11.3: auf Startpasswort zurücksetzen / selbst setzen (Lehrkräfte nur Schüler/innen ihrer Klassenleitung) */
  | 'passwords.reset';

export interface StudentRef {
  id: string;
  name: string;
  class_id?: string;
}

export interface User {
  id: number | string;
  username: string;
  display_name: string;
  role: Role;
  permissions: string[];
  teacher_id?: string | null;
  student_id?: string | null;
  student_ids?: string[];
  /** optional: Namen der verknüpften Schüler (falls Backend sie mitliefert) */
  students?: StudentRef[];
  /** Anmelde-Richtlinie (§11.5): fehlende Pflicht-Verknüpfungen → Seite /konten-verbinden */
  login_setup?: { missing_links: string[]; setup_only?: boolean } | null;
  site?: string | null;
  must_change_password?: boolean;
  totp_enabled?: boolean;
  /** 2FA ist für die Rolle Pflicht, aber noch nicht eingerichtet (SM_REQUIRE_2FA_ROLES). */
  totp_setup_required?: boolean;
  /** Die Schule empfiehlt Zwei-Faktor für diese Rolle, das Konto hat sie noch nicht */
  totp_recommended?: boolean;
  /** öffentliche Vorführ-Instanz (SM_DEMO_PUBLIC) */
  demo?: boolean;
  /** Lizenz-Kurzstand (Hinweis-Balken) */
  license?: LicenseBrief | null;
}

/** Lizenz-Kurzstand in `GET /auth/me` (Hinweis-Balken, Sperrseite) */
export interface LicenseBrief {
  state: 'valid' | 'grace' | 'locked' | 'missing' | 'invalid' | string;
  stage?: 'ok' | 'warning' | 'grace' | 'locked' | 'trial' | string;
  read_only: boolean;
  locked?: boolean;
  reason?: string;
  message: string;
  warning: string;
  enforced: boolean;
  days_left?: number | null;
  grace_until?: string | null;
}

export interface MeResponse {
  user: User;
  csrf_token: string;
}

/** Antwort der Anmeldung: Sitzung, oder (Konto mit Zwei-Faktor, Passwort stimmt) Schritt 2 „Code eingeben“ */
export type LoginResponse = MeResponse | { totp_required: true };

/** Benutzer in der Verwaltung (GET /users) */
export interface ManagedUser extends User {
  active?: boolean;
  adult?: boolean;
  sso?: boolean;
  /** Klasse des verknüpften Schülers */
  class?: string | null;
  email?: string | null;
  last_login?: string | null;
  created_at?: string | null;
}

export interface SessionInfo {
  id: string | number;
  created_at?: string;
  last_seen?: string;
  expires_at?: string;
  ip?: string | null;
  user_agent?: string | null;
  current?: boolean;
}

export interface ApiTokenInfo {
  id: number | string;
  name: string;
  prefix?: string;
  created_at?: string | null;
  last_used?: string | null;
  expires_at?: string | null;
}

export interface RolesInfo {
  roles: { id: Role; label: string }[];
  permissions: { id: string; label: string }[];
  matrix: Record<string, string[]>;
  scopes?: Record<string, Record<string, string>>;
  manageable?: Record<string, string[]>;
}

export interface BulkCreated {
  username: string;
  display_name: string;
  temp_password: string;
  class?: string | null;
  role?: Role;
  id?: number | string;
  student_id?: string | null;
  teacher_id?: string | null;
}

// ---------------------------------------------------------------- Stammdaten

export interface TimeRule {
  /** ausgewählte laufende Wochen (1-basiert, 1 … 53); leer = jede Woche */
  weeks: number[];
  days: number[];
  periods: number[];
  note: string;
  /** R3 (E6): Rhythmus in laufenden Wochen; gesetzt → `weeks` gilt nicht */
  rhythm?: WeekRhythm | null;
  /** gilt ab diesem Datum (ISO); leer/fehlt = von Anfang des Schuljahres an */
  valid_from?: string;
}

export interface Site {
  id: string;
  name: string;
}

export interface Subject {
  id: string;
  name: string;
  room_type: string | null;
  core: boolean;
  max_per_day: number;
  color: string;
}

export interface Teacher {
  id: string;
  name: string;
  subjects: string[];
  /** Altfeld: pendelt am selben Tag zwischen Standorten (ersetzt durch `commute_mode`) */
  commutes?: boolean;
  /** Pendeln: nie / höchstens 1× am Tag / beliebig (leer = nach `commutes`) */
  commute_mode?: '' | 'never' | 'once' | 'free';
  /** Mindestpause in Minuten zwischen Ende und Beginn der Stunden beim Standortwechsel (0 = nur Wegezeit) */
  commute_gap?: number;
  max_hours: number;
  max_per_day: number;
  unavailable: TimeRule[];
  /** weiche Wünsche (möglichst kein Unterricht) */
  wishes?: TimeRule[];
  email?: string;
  max_subs_per_week: number;
  sites: string[];
  /** Klassen, die die Lehrkraft hauptsächlich unterrichtet (Selbstauskunft, §9.3) */
  preferred_classes?: string[];
  /** Arbeitszeitfenster (z. B. nur ab 10:00 oder Abendunterricht ab 16:00) */
  time_windows?: { days: number[]; start: string; end: string; weeks?: number[]; rhythm?: WeekRhythm | null }[];
}

export interface Room {
  id: string;
  name: string;
  type: string;
  site: string;
  capacity: number;
}

export interface SchoolClass {
  id: string;
  name: string;
  grade: number;
  students: number;
  home_room: string | null;
  site: string;
  max_periods_per_day: number;
  /** Klassenarbeiten je Woche/Tag; null/fehlend = Vorgabe von Jahrgang bzw. Schule */
  max_exams_per_week?: number | null;
  max_exams_per_day?: number | null;
  unavailable: TimeRule[];
  class_teacher: string | null;
  /** Unterrichtstage 0 = Mo … 6 = So (leer = Schule) */
  school_days?: number[];
  /** Jahrgang/Profil (`GradeProfile.id`); bestimmt die Stundentafel, sofern die Klasse keine eigene hat */
  profile?: string | null;
}

export interface Student {
  id: string;
  name: string;
  class_id: string;
  courses: string[];
  /** ISO-Datum (YYYY-MM-DD), optional – daraus wird die Volljährigkeit abgeleitet (§11.3) */
  birth_date?: string | null;
}

export interface CurriculumEntry {
  subject: string;
  hours: number;
  double: boolean;
}

export interface Curriculum {
  id: string;
  name: string;
  /** Altbestand: Klassenstufen-Nummern (Fallback); neue Zuordnung läuft über Jahrgänge (`GradeProfile.curriculum`) */
  grades: number[];
  classes: string[];
  entries: CurriculumEntry[];
  /** abgeleitet von dieser Stundentafel: wirksam = Basis + `deltas` (Stunden-Differenz je Fach, `double` = Zielwert) */
  base?: string | null;
  deltas?: CurriculumEntry[];
}

/** Jahrgang/Profil – frei definierbar („5“, „5 Informatik“, „Montessori“, „GIF 26“) */
export interface GradeProfile {
  id: string;
  name: string;
  short: string;
  /** Klassenstufe (Zahl), optional */
  grade: number | null;
  /** #rrggbb, leer = automatisch */
  color: string;
  description: string;
  department: string;
  /** Stundentafel (`Curriculum.id`) */
  curriculum: string | null;
}

export interface CoursePart {
  subject: string;
  teacher: string | null;
  room: string | null;
  room_type: string | null;
  label: string;
  students: string[] | null;
}

export interface Course {
  id: string;
  classes: string[];
  parts: CoursePart[];
  hours: number;
  double: boolean;
  label: string;
  /** ausgewählte laufende Wochen (1-basiert); leer = jede Woche, außer `rhythm` ist gesetzt */
  weeks: number[];
  rhythm?: WeekRhythm | null;
  origin: string;
  /** Stundentafel-Kurs: im Editor geänderte Felder (bleiben beim erneuten Erzeugen erhalten) */
  pinned?: string[];
}

export interface Lesson {
  id: string;
  course_id: string;
  day: number;
  start: number;
  length: number;
  weeks: number[];
  rhythm?: WeekRhythm | null;
  rooms: (string | null)[];
  locked: boolean;
}

/** `lesson` = „Unterricht findet nicht statt“ (§10.1): `ref` = Kurs-ID bzw. `<kurs>#<teil>` */
export type AbsenceKind = 'teacher' | 'class' | 'room' | 'lesson';

export interface Absence {
  id: string;
  kind: AbsenceKind;
  ref: string;
  date_from: string;
  date_to: string;
  periods: number[];
  reason: string;
  /** von der Lehrkraft selbst gemeldet (nur solche darf sie löschen) */
  self_reported?: boolean;
}

/** POST /absences/preview: Wirkung einer Abwesenheit vor dem Speichern */
export interface AbsencePreview {
  days: number;
  school_days: number;
  /** Ferien-/Feiertage im Zeitraum (ohne Wochenenden) */
  free_days: number;
  free_names: string[];
  /** geänderte Plan-Einträge; `null` bei sehr langem Zeitraum */
  affected: number | null;
}

export type OverrideAction = 'substitute' | 'cancel' | 'keep' | 'room';

export interface Override {
  id: string;
  date: string;
  lesson_id: string;
  period: number;
  part: number;
  action: OverrideAction;
  teacher: string | null;
  room: string | null;
  note: string;
}

export interface Holiday {
  id: string;
  name: string;
  date_from: string;
  date_to: string;
  /** R3; fehlt = aus dem Namen („…ferien…“ → ferien, sonst feiertag) */
  kind?: HolidayKind;
}

/** Termin im Schulkalender (`pflicht` = Anwesenheit Pflicht, z. B. Samstag) */
export interface SchoolEvent {
  id: string;
  title: string;
  date_from: string;
  date_to: string;
  time_from: string;
  time_to: string;
  kind: 'termin' | 'pflicht';
  classes: string[];
  grades: number[];
  location: string;
  note: string;
  /** teilnehmende Lehrkräfte – fehlen im Unterricht, die Vertretung wird automatisch geplant */
  teachers?: string[];
}

export interface SupervisionArea {
  id: string;
  name: string;
  site: string;
  needed: number;
}

export interface Duty {
  id: string;
  area: string;
  day: number;
  break_index: number;
  teacher: string | null;
  weeks: number[];
  rhythm?: WeekRhythm | null;
}

export interface Exam {
  id: string;
  course_id: string;
  date: string;
  start: number;
  length: number;
  title: string;
  part: number | null;
  room: string | null;
  /** klausur = Klassenarbeit/Klausur (zählt zu den Höchstzahlen), test = angekündigter Test */
  kind?: 'klausur' | 'test';
  /** optionale Zusatzinfos vom Server (exam_info) */
  subject?: string;
  subjects?: string[];
  classes?: string[];
  teacher?: string | null;
  teachers?: string[];
  label?: string;
  time?: string;
  /** Lehrkräfte: nur Klausuren eigener Kurse bearbeitbar */
  can_edit?: boolean;
  /** Raum der Unterrichtsstunde zur Klausurzeit (Ersatz, solange `room` leer ist) */
  room_lesson?: string | null;
  /** Kursraum des Fachs, falls das Konto ihn öffnen darf */
  channel_id?: number | null;
  /** volle Namen zu Kürzeln (für Sprechblasen, auch ohne Stammdaten-Zugriff) */
  names?: { teachers: Record<string, string>; subjects: Record<string, string>; rooms: Record<string, string>; classes: Record<string, string> };
}

export interface Weights {
  class_gap: number;
  teacher_gap: number;
  late_start: number;
  position: number;
  core_late: number;
  day_balance: number;
  spread: number;
  site_change: number;
  double_split: number;
  teacher_wish?: number;
}

export interface SubstitutionPolicy {
  cancel_min_grade: number;
  edge_strategy: 'cancel' | 'substitute_if_qualified' | 'substitute';
  middle_strategy: 'shift_first' | 'substitute_first';
  allow_unqualified: boolean;
  max_subs_per_day: number;
}

export interface BreakDef {
  after: number;
  name: string;
  minutes: number;
}

export interface Settings {
  school_name: string;
  days: number;
  periods: number;
  period_times: string[];
  /** Altfeld: Schuljahresbeginn älterer Dokumente (leerer `school_year_start` = `cycle_start`) */
  cycle_start: string;
  /** R3 (§15.3) */
  week_numbering?: WeekNumbering;
  school_year_start?: string;
  /** Schuljahresbeginn: `auto` = Ende der Sommerferien (aus den Ferien), `own` = eigener Schulstart */
  year_start_mode?: YearStartMode;
  school_year_history?: string[];
  /** Unterrichtstage 0 = Mo … 6 = So; leer = die ersten `days` Tage */
  school_days?: number[];
  site_travel_periods: number;
  /** Wegezeit je Standortpaar in Minuten (beide Richtungen) */
  site_travel?: { a: string; b: string; minutes: number }[];
  core_latest_period: number;
  weights: Weights;
  policy: SubstitutionPolicy;
  /** Abwesende Lehrkräfte auf Monitor/Aushang: off = keine, short = nur Kürzel, name = Kürzel + Name (B-04) */
  public_absent_teachers?: 'off' | 'short' | 'name';
  webhooks: string[];
  breaks: BreakDef[];
  /** Klassenarbeiten je Klasse und Woche/Tag – Vorgabe der Schule; je Jahrgang und je Klasse überschreibbar */
  max_exams_per_week: number;
  max_exams_per_day: number;
  exam_limits_by_grade?: Record<string, { per_week?: number | null; per_day?: number | null }>;
  /** Regeln und Prioritäten als Bausteine (`pages/planning/rules`); die Zahlen (`weights` …) folgen daraus */
  rules?: Record<string, unknown>;
  /** Planzeiträume (nur lesen; ändern über `/calendar/plan-periods`) */
  plan_periods?: PlanPeriodRef[];
  /** Erweiterung 2 (§9.1) */
  period_minutes?: number;
  teacher_self_service?: 'approval' | 'direct';
  /** Attestpflicht ab N Schultagen (0 = keine) */
  sick_note_after_days?: number;
  /** Telefonische Krankmeldung: Nummer und Zeiten */
  sick_phone?: string;
  sick_phone_hours?: string;
  messaging_students_to_students?: boolean;
  messaging_retention_days?: number;
  /** Kursraum-Papierkorb: Tage bis zum endgültigen Löschen (1–365, Standard 30) */
  trash_retention_days?: number;
  /** Krankmeldungen für Fachlehrkräfte: none = keine, presence = „fehlt heute in meiner Stunde“ (B-06) */
  subject_teacher_absence_view?: 'none' | 'presence';
  /** Zulässige Fehlzeit je Fach in % der stattgefundenen Stunden (0/leer = keine Grenze): insgesamt bzw. unentschuldigt */
  absence_limit_percent?: number;
  absence_limit_unexcused_percent?: number;
  /** Auto-Planer: Stundenplan nach Änderungen automatisch reparieren */
  auto_replan?: boolean;
  /** Plan prüfen: aus = nichts ohne Zustimmung; raeume = reine Raumänderungen sofort übernehmen */
  plan_auto_apply?: 'aus' | 'raeume';
  /** Vertretung: Vorschläge erst nach Freigabe aktiv */
  substitution_confirm?: boolean;
  /** Generator: Fächer ab 2 Wochenstunden als Doppelstunden planen */
  prefer_doubles?: boolean;
  double_alignment?: 'bloecke' | 'pausen' | 'frei';
}

// ---------------------------------------------------------------- Kalender (R3, Entwurf §15.3)

export type WeekNumbering = 'school_year' | 'iso';
export type YearStartMode = 'auto' | 'own';
export type DayKind = 'unterricht' | 'kein_unterrichtstag' | 'ferien' | 'feiertag';
export type HolidayKind = 'ferien' | 'feiertag' | 'beweglich' | 'schulfrei';

export interface WeekInfo {
  /** laufende Woche 1 … Y im Schuljahr (auch im KW-Modus), null außerhalb */
  week_no: number | null;
  iso_week: number;
  iso_year: number;
  /** Montag bzw. Sonntag der Woche */
  week_start: string;
  week_end: string;
  /** fertiger Text vom Server, z. B. „Woche 6 · KW 41“ */
  week_text: string;
  holiday_week: boolean;
  holiday_name: string | null;
  in_school_year: boolean;
  /** nur mit Planzeiträumen: Zustand des Stundenplans dieser Woche */
  plan?: PlanState;
}

/** Planzeiträume (z. B. Halbjahre): je Zeitraum ein eigener Stundenplan (`schulmanager/plan_periods.py`) */
export interface PlanPeriodRef {
  id: string;
  name: string;
  date_from: string;
  date_to: string;
  from_week: number;
  to_week: number;
}

/** `ok` = Plan vorhanden, `missing` = Zeitraum ohne Plan, `none` = Woche liegt in keinem Zeitraum */
export interface PlanState {
  active: boolean;
  state: 'ok' | 'missing' | 'none';
  period: PlanPeriodRef | null;
}

/** Antwort von `/calendar/plan-periods` */
export interface PlanPeriodsResponse {
  active: boolean;
  periods: PlanPeriod[];
  suggested: PlanPeriodRef[];
  /** Voreinstellung im Generator: laufender bzw. nächster Zeitraum ohne Plan */
  target: string | null;
}

/** Eingabe: ohne `id` legt der Server eine an */
export interface PlanPeriodInput {
  id?: string;
  name: string;
  date_from: string;
  date_to: string;
}

export interface PlanPeriod extends PlanPeriodRef {
  /** Zahl der Stunden des Zeitraums */
  lessons: number;
  has_plan: boolean;
}

export interface DayInfo {
  index: number;
  name: string;
  date: string;
  teaching: boolean;
  day_kind: DayKind;
  holiday: string | null;
}

/** Rhythmus „alle k Wochen ab Woche s (bis Woche e)“ in laufenden Wochen (1-basiert, `to_week` 0/fehlt = offen) */
export interface WeekRhythm {
  every: number;
  from_week: number;
  to_week?: number;
}

export interface SchoolYearWeek {
  week_no: number;
  iso_week: number;
  week_start: string;
  week_end: string;
  holiday_week: boolean;
  holidays: string[];
  /** nur mit Planzeiträumen */
  plan_state?: PlanState['state'];
  plan_period?: string | null;
}

export interface SchoolYear {
  start: string;
  /** Montag der Woche 1 (R3-A1) */
  first_monday?: string;
  end: string;
  numbering: WeekNumbering;
  /** Woher der Beginn kommt, und der aus den Sommerferien erkannte Beginn (ISO-Datum, sonst `null`) */
  year_start_mode?: YearStartMode;
  detected_start?: string | null;
  weeks_in_year: number;
  open_days: number[];
  warnings: string[];
  weeks: SchoolYearWeek[];
  plan_periods?: PlanPeriod[];
}

export interface ChangeItem {
  kind: string;
  id: string;
  label: string;
  before: string;
  after: string;
}

/** `detail` einer 409-Bestätigung; übernommen wird mit `?force=1` */
export interface ConfirmDetail {
  message: string;
  code: 'plan_change' | 'grid_change' | 'time_grid_change';
  changes: ChangeItem[];
}

export interface CalendarPreview {
  today_before: WeekInfo;
  today_after: WeekInfo;
  warnings: string[];
}


/** GET /planning/autoplan */
export interface AutoPlanStatus {
  status: 'idle' | 'ok' | 'running' | 'waiting' | 'applied' | 'partial' | 'unsolved' | 'proposal' | 'covered' | 'off' | 'error' | string;
  message: string;
  checked_at: string | null;
  applied_at: string | null;
  enabled: boolean;
  checking: boolean;
  setting: boolean;
  version: number;
  open_count: number;
  open_problems: string[];
  problems: string[];
  job_id?: string | null;
  /** Plan prüfen: Einstellung „Raumänderungen ohne Rückfrage“ */
  auto_apply?: 'aus' | 'raeume';
  last: {
    kind: 'rooms' | 'generator';
    at: string;
    fixed?: number;
    reasons: string[];
    remaining?: string[];
    changes: { course_id: string; label: string; classes: string[]; from: string[]; to: string[] }[];
    room_changes: { lesson: string; course: string; old: string | null; new: string }[];
  } | null;
}

export interface CollectionTypes {
  sites: Site;
  subjects: Subject;
  teachers: Teacher;
  rooms: Room;
  classes: SchoolClass;
  students: Student;
  curricula: Curriculum;
  grade_profiles: GradeProfile;
  courses: Course;
  holidays: Holiday;
  events: SchoolEvent;
  areas: SupervisionArea;
  duties: Duty;
  exams: Exam;
}

export type CollectionName = keyof CollectionTypes;

// ---------------------------------------------------------------- Stundenplan

export type TimetableKind = 'class' | 'teacher' | 'room' | 'student';

export interface CellPart {
  index?: number;
  subject: string;
  teacher: string | null;
  room: string | null;
  label: string;
}

export interface Cell {
  lesson_id: string;
  course_id: string;
  day: number;
  start: number;
  length: number;
  weeks: number[];
  subject: string;
  subject_name: string;
  color: string;
  teachers: string[];
  rooms: string[];
  classes: string[];
  label: string;
  locked: boolean;
  parts: CellPart[];
  /** „Woche 1, 3“, „jede 2. Woche ab Woche 2“ bzw. „jede Woche“ */
  weeks_text?: string;
  rhythm?: WeekRhythm | null;
  /** nur Kalenderwoche: Änderung gegenüber dem Regelplan (Vertretung, Entfall, Raum …) */
  status?: { label: string; cancelled: boolean; note?: string };
  /** nur Kalenderwoche: kleine Links im Block (z. B. „HA“ → Hausaufgabe im Kursraum) */
  links?: { label: string; to: string; title?: string; kind?: 'ha' | 'exam' | 'makeup' | 'support' | 'missing' | 'event' | 'duty' | 'absent'; done?: boolean; onClick?: () => void }[];
  /** nur Kalenderwoche: Block einer Klausur/eines Tests/Nachschreibtermins in seinen Stunden (statt des Regelplans) */
  exam?: { id: string; kind: 'klausur' | 'test' | 'nachschreiben'; /** Ziel beim Klick: Kursraum, sonst Klausur-Detail */ to?: string };
  /** nur Kalenderwoche (Schüleransicht): gefehlt – „krank“, „beurlaubt“ oder „gefehlt“ (rot gestrichelt) */
  absent?: string;
}

export interface PeriodInfo {
  index: number;
  label: string;
  time: string;
}

export interface BlockedSlot {
  day: number;
  period: number;
  note: string;
}

export interface TimetableView {
  kind: TimetableKind;
  ref: string;
  title: string;
  /** laufende Woche des Schuljahres */
  week_no?: number | null;
  days: string[];
  /** Vertrag: Zeiten als Strings; Implementierung: {index,label,time} */
  periods: (string | PeriodInfo)[];
  breaks?: BreakDef[];
  /** Sperrzeiten (Rhythmus/Praxistag) der Klasse/Lehrkraft */
  blocked?: BlockedSlot[];
  cells: Cell[];
  /** R3: Woche der Ansicht; Spalten ab Montag (`days` = Spaltennamen, V10) */
  week_info?: WeekInfo;
  day_info?: DayInfo[];
}

export interface MoveOption {
  day: number;
  start: number;
  ok: boolean;
  conflicts: string[];
}

// ---------------------------------------------------------------- Vertretung

export type EntryKind =
  | 'vertretung'
  | 'betreuung'
  | 'entfall'
  | 'verlegung'
  | 'raumaenderung'
  | 'mitbetreuung'
  | 'klasse_abwesend'
  | 'aufsicht'
  | 'klausur';

export interface Entry {
  id: string;
  date: string;
  period: number;
  period_label: string;
  time: string;
  kind: EntryKind | string;
  classes: string[];
  subject: string;
  teacher: string | null;
  substitute: string | null;
  room: string | null;
  new_room: string | null;
  moved_from: number | string | null;
  lesson_id: string | null;
  part: number;
  note: string;
  warning: boolean;
  manual: boolean;
  /** Bestätigungsmodus: automatischer Vorschlag, noch nicht freigegeben (nur für die Vertretungsplanung sichtbar) */
  proposed?: boolean;
  site: string | null;
  /** nur `klasse_abwesend`: gemeldete Abwesenheit oder regulärer Rhythmus (B-04) */
  source?: 'absence' | 'rhythm';
}

export interface DayPlan {
  date: string;
  weekday: number;
  week_no?: number;
  holiday: string | null;
  week_info?: WeekInfo;
  day_kind?: DayKind;
  entries: Entry[];
  warnings: string[];
  stats: Record<string, number>;
  absent_teachers: string[];
  absent_classes: string[];
  /** je abwesender Lehrkraft (B-04); öffentliche Sicht nur `teacher` bzw. `teacher` + `name` */
  absent_teacher_details?: AbsentTeacherDetail[];
  /** je Klasse in `absent_classes`; `rhythm` = regulärer Praxis-/Berufsschultag (nicht anzeigen) */
  absent_class_details?: AbsentClassDetail[];
  /** Bestätigungsmodus der Schule aktiv (Vorschläge erst nach Freigabe) */
  confirm_mode?: boolean;
  /** Zahl der noch nicht freigegebenen Vorschläge (nur Vertretungsplanung) */
  proposals?: number;
}

export interface AbsentTeacherDetail {
  teacher: string;
  name?: string;
  full_day?: boolean;
  /** 0-basiert, leer bei ganztägig */
  periods?: number[];
  /** Vertretungsfälle (vertreten, betreut, entfallen, Aufsicht) */
  cases?: number;
}

export interface AbsentClassDetail {
  class: string;
  name: string;
  source: 'absence' | 'rhythm';
  full_day: boolean;
  periods: number[];
  reason: string;
}

export interface Candidate {
  teacher: string;
  name: string;
  score: number;
  reasons: string[];
  qualified: boolean;
  free: boolean;
}

/**
 * Zelle aus effective_day (Mein Tag).
 * status ∈ normal | geaendert | entfall | neu; kind = Entry-Art bzw. unterricht/aufsicht.
 * `teacher`/`room` sind bereits die tatsächlichen Werte; `original_*` = ursprünglich geplant.
 */
export interface EffectiveCell {
  period: number;
  period_label?: string;
  time?: string;
  subject: string;
  teacher: string | null;
  room: string | null;
  classes: string[];
  status: string;
  note: string;
  lesson_id: string | null;
  part: number | null;
  kind: string | null;
  course_id?: string | null;
  original_teacher?: string | null;
  original_room?: string | null;
  entry_id?: string | null;
  /** Titel der Klausur in dieser Stunde */
  exam?: string | null;
  /** ältere Varianten */
  substitute?: string | null;
  new_room?: string | null;
}

export type AnnouncementAudience = 'all' | 'staff' | 'classes';

export interface Announcement {
  id: string | number;
  title: string;
  body: string;
  created_at?: string;
  author_id?: number | string | null;
  author?: string | null;
  author_name?: string | null;
  audience?: AnnouncementAudience | string | null;
  class_ids?: string[];
  audience_roles?: Role[];
  pinned?: boolean;
  site?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
  priority?: 'normal' | 'wichtig' | string;
  monitor?: boolean;
  /** darf der aktuelle Benutzer löschen (optional vom Server) */
  can_delete?: boolean;
}

export interface MyDay {
  date: string;
  student_id?: string | null;
  title?: string;
  week_no?: number;
  holiday?: string | null;
  day_kind?: DayKind;
  week_info?: WeekInfo;
  has_items?: boolean;
  plan_entries: Entry[];
  cells: EffectiveCell[];
  announcements: Announcement[];
  exams: Exam[];
}

export interface MyWeek {
  /** R3: immer 7 Tage (Mo–So) */
  days: MyDay[];
  week_info?: WeekInfo;
}

export type StudentAbsenceStatus = 'gemeldet' | 'teilweise' | 'entschuldigt' | 'unentschuldigt';
/** krank (auch ganze Tage), zu spät, früher gegangen, ohne Meldung gefehlt */
export type StudentAbsenceKind = 'krank' | 'verspaetung' | 'frueh' | 'fehlt' | 'beurlaubung';
export type StudentAbsenceSource = 'online' | 'telefon' | 'schriftlich' | 'lehrkraft';

export interface StudentAbsence {
  id: string | number;
  student_id: string;
  student_name?: string | null;
  class_id?: string | null;
  date_from: string;
  date_to: string;
  periods?: number[];
  reason: string;
  /** null = für dieses Konto verborgen (Fachlehrkraft, B-06) */
  status: StudentAbsenceStatus | null;
  note?: string | null;
  reported_by?: string | number | null;
  reported_by_name?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  can_manage?: boolean;
  can_delete?: boolean;
  /** Sicht: full (Klassenleitung, Sekretariat, Schulleitung), family, own (eigene Meldung), presence („fehlt heute in meiner Stunde“) */
  view?: 'full' | 'family' | 'own' | 'presence' | 'leave' | 'hidden';
  /** Grund für diese Rolle ausgeblendet (z. B. Fachlehrkräfte, §9.6) */
  reason_hidden?: boolean;
  /** Attestpflicht/-zustand (§9.6); null = verborgen */
  attest?: AttestInfo | null;
  /** Schülerkonto als volljährig markiert (nur für Schulpersonal geliefert) */
  student_adult?: boolean;
  /** Antwort auf POST: mit eigener Meldung zusammengeführt */
  merged?: boolean;
  status_label?: string;
  kind?: StudentAbsenceKind;
  kind_label?: string;
  /** Minuten (zu spät) */
  minutes?: number | null;
  source?: StudentAbsenceSource;
  source_label?: string;
  excused_by_name?: string | null;
  /** Meldungsprotokoll (nur volle Sicht: Klassenleitung, Sekretariat, Schulleitung) */
  history?: AbsenceLogEvent[];
  channel_label?: string;
  reported_at?: string | null;
  reported_by_role?: string;
  excused_at?: string | null;
  /** Schultage im Zeitraum (nur in der Fehlzeiten-Übersicht) */
  school_days?: number;
  /** Was die Familie an dieser Meldung gerade tun darf (siehe Backend `_row_actions`) */
  actions?: AbsenceAction[];
  /** Die Familie hat die Rücknahme einer schon bearbeiteten Meldung angefragt */
  withdrawal_requested?: boolean;
}

/** `withdraw` zurücknehmen/zurückziehen, `request_withdrawal` Rücknahme anfragen, `shorten` früher zurück, `extend` verlängern, `return_leave` Beurlaubung zurückgeben */
export type AbsenceAction = 'withdraw' | 'request_withdrawal' | 'shorten' | 'extend' | 'return_leave';

/** GET /student-absences/preview: Schultage und Attestpflicht eines Meldezeitraums */
export interface ReportPreview {
  school_days: number;
  /** Schul-Einstellung „Attest ab … Schultagen“ (0 = aus) */
  attest_after_days: number;
  attest_by_days: boolean;
  attest_due: string | null;
  exams: { date: string; title: string; kind?: string | null }[];
  attest_needed: boolean;
}

/** GET /student-absences/access (B-06) */
export interface StudentAbsenceAccess {
  all: boolean;
  family: boolean;
  can_report: boolean;
  /** Klassen, deren Klassenleitung das Konto ist */
  class_ids: string[];
  /** Schulschalter für Fachlehrkräfte (für alle Konten geliefert) */
  subject_view: 'none' | 'presence';
  /** Familie: Personen, deren Krankmeldungen das Konto sieht und meldet (Volljährige nur mit Freigabe) */
  student_ids?: string[];
  max_days: number;
  max_backdate_days: number;
}

/** Eintrag im Meldungsprotokoll (nur anhängend); Fachlehrkräfte sehen nur `event: 'abwesend'` mit Zeitpunkt und Kanal */
export interface AbsenceLogEvent {
  id: number;
  absence_id: number;
  at: string;
  event: string;
  text: string;
  channel: string;
  channel_label: string;
  actor_name?: string;
  actor_role?: string;
}

/** Wann/von wem/wie eine Meldung einging (Name und Rolle nur in der vollen Sicht) */
export interface ReportInfo {
  reported_at: string | null;
  channel: string;
  channel_label: string;
  reported_by_name?: string;
  reported_by_role?: string;
}

/** GET /student-absences/record – Fehlzeiten eines Kindes */
export interface AttendanceRecord {
  student: { id: string; name: string; class_id: string };
  /** Konto darf für die Person melden (Eltern, volljährige Schüler/innen, Personal); Minderjährige sehen keine Melde-Elemente */
  can_report?: boolean;
  from: string;
  to: string;
  entries: StudentAbsence[];
  /** zurückgenommene/gelöschte Meldungen (nur volle Sicht) – bleiben im Protokoll */
  withdrawn?: { absence_id: number; history: AbsenceLogEvent[] }[];
  documents: {
    id: number;
    category: string;
    category_label: string;
    title: string;
    status: string;
    status_label?: string;
    absence_id: number | null;
    created_at: string;
    file?: { id: string; filename: string; inline?: boolean } | null;
    can_handle?: boolean;
  }[];
  summary: {
    days: number;
    days_excused: number;
    days_unexcused: number;
    days_open: number;
    lessons: number;
    lessons_excused: number;
    lessons_unexcused: number;
    late_count: number;
    late_minutes: number;
    early_count: number;
    open_count: number;
  };
  can_manage: boolean;
  phone: { number: string; hours: string };
}

export type AttestState = 'nicht_noetig' | 'erforderlich' | 'fehlt' | 'eingereicht' | 'geprueft' | 'abgelehnt';

export interface AttestInfo {
  required: boolean;
  school_days: number;
  due: string | null;
  state: AttestState;
  label: string;
  missing: boolean;
}

export interface TeacherStat {
  teacher: string;
  name: string;
  substitutions: number;
  cancelled_own: number;
  duties: number;
  supervisions: number;
}

// ---------------------------------------------------------------- Planung

export interface UnplacedHours {
  course: string;
  label: string;
  /** Wochen, für die die Stunden fehlen: „jede Woche“, „Woche 1“ … */
  weeks_text: string;
  missing: number;
  /** Wochenstunden des Kurses / bisher gelegt / Grund (nur im Bericht mit Einzelheiten) */
  hours?: number;
  placed?: number;
  reason?: string;
}

export interface OverplacedHours {
  course: string;
  label: string;
  weeks_text: string;
  extra: number;
  hours: number;
  placed: number;
}

export interface OpenPart {
  course: string;
  label: string;
  part: number;
  subject: string;
}

/** Spanne einer wochenbezogenen Kennzahl: kleinster/größter Wert je Wochenmuster und Durchschnitt je Schulwoche. */
export interface ReportRange {
  min: number;
  max: number;
  avg: number;
}

export interface ReportGapRow {
  kind: 'class' | 'teacher';
  id: string;
  day: number;
  /** 1-basiert */
  period: number;
  weeks_text: string;
}

export interface ReportSiteChangeRow extends ReportGapRow {
  from_site: string;
  to_site: string;
}

export interface ReportConflictRow {
  text: string;
  kind: 'class' | 'teacher' | 'room';
  id: string;
  day: number;
  period: number;
  weeks_text: string;
  lessons: string[];
}

export interface ReportCoreLateRow {
  lesson: string;
  course: string;
  label: string;
  classes: string[];
  teachers: string[];
  day: number;
  /** letzte belegte Stunde, 1-basiert */
  period: number;
}

export interface ReportTeacherRow {
  id: string;
  name: string;
  max_hours: number;
  load: number;
  over: number;
}

export interface ReportWeekRow {
  weeks_text: string;
  week_count: number;
  class_gaps: number;
  teacher_gaps: number;
  site_changes: number;
}

export interface ReportDetails {
  class_gaps: ReportGapRow[];
  teacher_gaps: ReportGapRow[];
  site_changes: ReportSiteChangeRow[];
  conflicts: ReportConflictRow[];
  core_late: ReportCoreLateRow[];
  unplaced: UnplacedHours[];
  overplaced: OverplacedHours[];
  teachers: ReportTeacherRow[];
  weeks: ReportWeekRow[];
}

export interface ReportDetailsResponse {
  details: ReportDetails;
  ranges: Record<string, ReportRange>;
  stats: Record<string, number | string>;
  version?: number;
}

export interface PlanningReport {
  stats: Record<string, number | string>;
  ranges?: Record<string, ReportRange>;
  warnings: string[];
  conflicts?: string[];
  unplaced_hours?: UnplacedHours[] | number;
  overplaced_hours?: OverplacedHours[];
  class_gaps?: Record<string, number>;
  capacity_warnings?: string[];
  open_parts?: OpenPart[];
  version?: number;
}

export interface UnplacedItem {
  course_id?: string;
  classes?: string[];
  subject?: string;
  hours?: number;
  reason?: string;
  [key: string]: unknown;
}

export type JobStatus = 'queued' | 'pending' | 'running' | 'done' | 'finished' | 'failed' | 'error' | 'applied' | 'cancelled';

export interface GenerateResultSummary {
  stats?: Record<string, number | string>;
  unplaced?: UnplacedItem[];
  warnings?: string[];
  lessons?: number;
}

export interface Job {
  id: string;
  kind?: string;
  status: JobStatus | string;
  progress: number;
  message: string;
  /** Ergebnis (Implementierung liefert stats/unplaced/warnings direkt am Job) */
  stats?: Record<string, number | string>;
  unplaced?: UnplacedItem[];
  warnings?: string[];
  lessons_count?: number;
  outdated?: boolean;
  result?: GenerateResultSummary | null;
  error?: string | null;
  created_at?: string;
  started_at?: string;
  finished_at?: string;
}

/** Eine Aufsicht in der Wochenübersicht (`GET /duties/overview`) */
export interface DutyOverviewRow {
  duty_id: string;
  teacher: string | null;
  teacher_name: string;
  /** ok | hinweis (kein Unterricht an dem Tag) | vertreten (Ersatz gefunden) | konflikt (kein Ersatz) | offen (niemand eingeteilt) */
  status: 'ok' | 'hinweis' | 'vertreten' | 'konflikt' | 'offen';
  /** Standorte, an denen die Lehrkraft an dem Tag laut Stundenplan unterrichtet */
  sites_today: string[];
  first_site: string;
  note: string;
  substitute: string | null;
  substitute_name: string;
  substitute_reason: string;
}
export interface DutyOverviewCell {
  area: string;
  area_name: string;
  site: string;
  needed: number;
  duties: DutyOverviewRow[];
  missing: number;
}
export interface DutyOverviewBreak {
  index: number;
  name: string;
  after: number;
  time: string;
  cells: DutyOverviewCell[];
}
export interface DutyOverviewDay {
  date: string;
  weekday: number;
  open: boolean;
  reason: string | null;
  breaks: DutyOverviewBreak[];
}
export interface DutyOverview {
  week_start: string;
  sites: { id: string; name: string }[];
  days: DutyOverviewDay[];
}

export interface WarningsResponse {
  warnings?: string[];
  [key: string]: unknown;
}

/** Überschneidung von Stundentafeln (gleichrangig: beide nennen die Klasse bzw. beide über den Jahrgang) */
export interface CurriculumConflict {
  curricula: string[];
  classes: string[];
  source: 'class' | 'grade';
}

/** `POST /planning/courses-from-curricula` (auch als Vorschau mit `dry_run`) */
export interface RebuildResult {
  warnings: string[];
  conflicts: CurriculumConflict[];
  created: string[];
  removed: string[];
  changed: { id: string; label: string; fields: string[] }[];
  /** Kurse mit eigenen Anpassungen, die erhalten bleiben */
  kept: { id: string; label: string; fields: string[]; labels: string[]; curriculum_hours: number }[];
  replan_needed: boolean;
  courses: number;
  before: number;
  removed_lessons: number;
  dry_run: boolean;
}

/** `GET /planning/curricula/overview`: welche Stundentafel gilt für welche Klasse */
export interface CurriculaOverview {
  curricula: Record<string, { classes: string[]; conflicts: string[]; via_grade: string[]; via_profile: string[]; shadowed: string[]; profiles: string[] }>;
  classes: Record<string, { curriculum: string | null; source: 'class' | 'profile' | 'grade' | null; candidates: string[]; conflict: boolean }>;
  class_names: Record<string, string>;
  without: string[];
  conflicts: CurriculumConflict[];
}

// ---------------------------------------------------------------- Verlauf/Audit/System

export interface HistoryEntry {
  version: number;
  created_at: string;
  user: string | null;
  user_display_name?: string | null;
  restored_from?: number | null;
  current?: boolean;
  message: string;
  scope: string[] | string | null;
}

export interface AuditEntry {
  id: number | string;
  created_at: string;
  user: string | null;
  action: string;
  target: string | null;
  details: Record<string, unknown> | string | null;
  ip?: string | null;
}

export interface BackupInfo {
  name: string;
  size?: number;
  created_at?: string;
}

export interface LiveChangeEvent {
  version?: number;
  scope?: string[];
  dates?: string[];
}

export interface LiveJobEvent {
  id: string;
  status: string;
  progress: number;
  message: string;
}

export interface MonitorNotice {
  text: string;
  until?: string | null;
  important?: boolean;
}

/** Einstellungen eines Vertretungsmonitors (je Standort, `""` = alle Standorte) */
export interface MonitorConfig {
  days: number;
  title: string;
  ticker: string;
  notices: MonitorNotice[];
  scroll: 'langsam' | 'normal' | 'schnell';
  font_scale: number;
  show_absent_classes: boolean;
}

export interface MonitorData {
  site?: string | null;
  site_name?: string | null;
  school_name?: string | null;
  days: DayPlan[];
  announcements: Announcement[];
  config?: MonitorConfig | null;
}

export interface ImportReport {
  created?: number;
  updated?: number;
  skipped?: number;
  errors?: string[];
  warnings?: string[];
  [key: string]: unknown;
}

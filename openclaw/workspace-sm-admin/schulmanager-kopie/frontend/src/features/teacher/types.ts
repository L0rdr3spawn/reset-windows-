/**
 * Typen der Lehrer-Selbstverwaltung (ARCHITECTURE.md §9.3) – lokal im Modul, damit geteilte
 * Dateien (api/types.ts) unverändert bleiben.
 */
import type { Job, Teacher, TimeRule, WeekRhythm } from '../../api/types';

/** Arbeitszeitfenster: an diesen Tagen (und Wochen) von `start` bis `end` verfügbar. */
export interface TimeWindow {
  days: number[];
  start: string;
  end: string;
  /** ausgewählte laufende Wochen (1-basiert; leer = jede Woche) */
  weeks: number[];
  /** Rhythmus in laufenden Wochen; gesetzt → `weeks` gilt nicht */
  rhythm?: WeekRhythm | null;
}

/** Arbeitszeiten als Raster: gesperrte Stunden je Woche des Wechsels (1–52 Wochen; Woche k gilt in den Schulwochen
 * k+1, k+1+N, …). Leer = keine Einschränkung. */
export interface WorkGrid {
  weeks: number;
  blocked: { week: number; day: number; periods: number[] }[];
}

/** Lehrkraft inkl. Selbstauskunft (Felder aus models.Teacher, die types.ts noch nicht kennt). */
export type TeacherEx = Teacher & { preferred_classes?: string[]; time_windows?: TimeWindow[]; work_grid?: WorkGrid | Record<string, never> };

/** Von der Lehrkraft vorgeschlagenes, noch nicht vorhandenes Fach (wird nach Genehmigung angelegt). */
export interface NewSubject {
  id: string;
  name: string;
  room_type?: string | null;
}

export interface TeacherProfile {
  subjects: string[];
  /** Vorschläge für neue Fächer (gehen immer als Antrag an die Planung) */
  new_subjects?: NewSubject[];
  preferred_classes: string[];
  max_hours: number;
  /** harte Sperrzeiten als Regeln (Tage × Stunden, Rhythmus, „gilt ab“) – ersetzt Zeitfenster und Raster */
  unavailable?: TimeRule[];
  /** Altformate: vom Server nur noch leer geliefert, werden beim Speichern in `unavailable` umgerechnet */
  time_windows: TimeWindow[];
  work_grid?: WorkGrid | Record<string, never>;
  wishes: TimeRule[];
}

export type ProfileField = keyof TeacherProfile;

/** Verfügbarkeit je Wochengruppe und Tag (`weeks`/`rhythm` = laufende Wochen der Gruppe, `weeks_text` der fertige Text). */
export interface Availability {
  weeks?: number[];
  rhythm?: WeekRhythm | null;
  weeks_text?: string;
  day: number;
  day_name: string;
  /** komplett im Zeitfenster liegende Stunden (0-basiert) */
  periods: number[];
}

export interface OutsideConflict {
  lesson_id: string;
  course_id: string;
  label: string;
  classes: string[];
  day: number;
  start: number;
  length: number;
  weeks: number[];
  periods: number[];
  reason: string;
  text: string;
}

/** Lösungsvorschlag der Konfliktprüfung (nichts davon geschieht automatisch) */
export interface Suggestion {
  kind: 'replan' | 'move' | 'later' | 'teacher';
  text: string;
  link?: string;
  lesson_id?: string;
  teachers?: string[];
}

export interface Conflicts {
  outside_windows: OutsideConflict[];
  suggestions?: Suggestion[];
  dropped_subjects: { subject: string; hours: number; courses: { id: string; label: string; hours: number }[] }[];
  hours: { current: number; max_hours: number; previous_max: number; diff: number; status: 'ok' | 'ueber' | 'unter' };
  preferred_new: string[];
  messages: string[];
  count: number;
}

export interface DiffRow {
  field: ProfileField;
  label: string;
  old: unknown;
  new: unknown;
  old_text: string;
  new_text: string;
}

/** Einmalige Ausnahme: Datum (Bereich) und Stunden (leer = ganztägig) */
export interface ExceptionData {
  date: string;
  date_to: string;
  periods: number[];
  reason: string;
}

export interface ExceptionImpact {
  lessons: { date: string; day: number; period: number; label: string; classes: string[] }[];
  count: number;
  text: string;
}

export type RequestStatus = 'offen' | 'genehmigt' | 'abgelehnt' | 'zurueckgezogen';

export interface ChangeRequest {
  id: number;
  teacher_id: string;
  teacher_name: string;
  /** `profil` = Profiländerung, `ausnahme` = einmalige Ausnahme (Genehmigung legt eine Abwesenheit an) */
  kind?: 'profil' | 'ausnahme';
  exception?: ExceptionData | null;
  exception_text?: string;
  impact?: ExceptionImpact;
  user_id: number | null;
  user_name: string;
  status: RequestStatus;
  status_label: string;
  auto: boolean;
  payload: TeacherProfile;
  previous: TeacherProfile | null;
  current: TeacherProfile | null;
  diff: DiffRow[];
  note: string;
  review_comment: string;
  reviewer_id: number | null;
  reviewer_name: string;
  created_at: string | null;
  updated_at: string | null;
  decided_at: string | null;
  applied_version: number | null;
  /** nur bei offenen Anträgen bzw. Einzelabruf */
  conflicts?: Conflicts;
  availability?: Availability[];
  load?: Load;
}

export interface Load {
  hours: number;
  courses: { id: string; label: string; classes: string[]; subjects: string[]; hours: number; weeks: number[] }[];
}

export interface ProfileOptions {
  subjects: { id: string; name: string }[];
  classes: { id: string; name: string; grade: number; site: string }[];
  days: number;
  periods: number;
  period_times: string[];
  period_minutes: number;
  /** R3: Unterrichtstage der Schule (0 = Mo … 6 = So) */
  school_days?: number[];
}

export interface MyProfileResponse {
  /** darf die eigenen Arbeitszeiten festlegen (Freigabe der Schule) */
  can_edit_times?: boolean;
  teacher_id: string;
  name: string;
  mode: 'approval' | 'direct';
  profile: TeacherProfile;
  description: string;
  load: Load;
  availability: Availability[];
  conflicts: Conflicts;
  pending: ChangeRequest | null;
  requests: ChangeRequest[];
  /** eigene Ausnahme-Anträge */
  exceptions?: ChangeRequest[];
  options: ProfileOptions;
}

export interface PreviewResponse {
  teacher_id: string;
  profile: TeacherProfile;
  diff: DiffRow[];
  conflicts: Conflicts;
  availability: Availability[];
  rules: TimeRule[];
  description: string;
}

export interface SaveResponse {
  status: 'pending' | 'applied';
  mode: 'approval' | 'direct';
  request: ChangeRequest;
  conflicts: Conflicts;
  version?: number;
}

export interface RequestsSummary {
  open: number;
  latest: { id: number; teacher_id: string; teacher_name: string; created_at: string | null }[];
}

/** Antwort von GET /timetable/allowed (null = alle der Sammlung). */
export interface AllowedRefs {
  all: boolean;
  kinds: ('class' | 'teacher' | 'room' | 'student')[];
  classes: string[] | null;
  teachers: string[] | null;
  rooms: string[] | null;
  students: string[] | null;
}

export interface ReplanChange {
  course_id: string;
  label: string;
  classes: string[];
  from: string[];
  to: string[];
}

export type ReplanJob = Job & {
  params?: Record<string, unknown>;
  replan?: { teacher_id: string; scope: string; free_courses: number; changed_courses: string[]; moved: number };
  changes?: ReplanChange[];
  applied_version?: number | null;
};

/**
 * Typen der Schüler-Selbstbedienung (§9.6) – Spiegel von `schulmanager/server/routes/features_student_self.py`.
 */
import type { AttestInfo, Exam, StudentAbsence } from '../../api/types';

export type DocCategory = 'attest' | 'entschuldigung' | 'beurlaubung' | 'einverstaendnis' | 'sonstiges';
export type DocStatus = 'eingegangen' | 'geprueft' | 'abgelehnt';

export interface StudentDocument {
  id: number;
  student_id: string;
  student_name: string;
  class_id: string | null;
  absence_id: number | null;
  category: DocCategory;
  category_label: string;
  title: string;
  file: { id: string; filename: string; size: number; content_type: string; inline: boolean } | null;
  /** nur Papiervorlage im Sekretariat vermerkt (ohne Datei) */
  paper: boolean;
  status: DocStatus;
  status_label: string;
  note: string;
  uploaded_by_name: string;
  own: boolean;
  handled_by_name: string;
  handled_at: string | null;
  created_at: string | null;
  can_handle: boolean;
  can_delete: boolean;
}

export interface DocSummary {
  open: number;
  attest_missing: number;
  /** nur Lehrkräfte: Klassen, deren Klassenleitung sie sind */
  class_teacher_of?: string[];
}

export interface ChildRef {
  id: string;
  name: string;
  class_id: string;
  adult: boolean;
}

export interface StudentOverview {
  student: { id: string; name: string; class_id: string; class_name: string; adult: boolean };
  children: ChildRef[];
  role: 'schueler' | 'eltern';
  today: string;
  today_is_school_day: boolean;
  today_note: string | null;
  next_school_day: string | null;
  can_report: boolean;
  report_hint: string | null;
  can_submit_documents: boolean;
  documents_hidden: boolean;
  /** Eltern eines volljährigen Kindes ohne Freigabe „Krankmeldungen“ (B-06/U-103) */
  absences_hidden?: boolean;
  sick_note_after_days: number;
  absences: (StudentAbsence & { attest: AttestInfo })[];
  attest_missing: number;
  documents: StudentDocument[];
  exams: Exam[];
  class_teacher: { id: string; name: string } | null;
  periods: number;
}

export interface DocumentInput {
  student_id?: string;
  absence_id?: number | null;
  category: DocCategory;
  title?: string;
  file_id?: string | null;
  note?: string;
}

/** Aufgaben aus den Kursräumen (nur die hier gebrauchten Felder von `/channels/overview`). */
export interface TaskEntry {
  channel_id: number;
  channel_title: string;
  item_id: number;
  title: string;
  due_at: string | null;
  status_label?: string;
  overdue?: boolean;
}

export interface TasksOverview {
  role: string;
  due?: TaskEntry[];
  restricted?: boolean;
  student?: { due: TaskEntry[]; open_assignments: number };
}

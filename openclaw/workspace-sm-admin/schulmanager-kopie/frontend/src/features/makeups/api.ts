/**
 * Nachschreibtermine (`/exam-makeups`, siehe schulmanager/server/routes/features_makeups.py).
 */
import { asList, http } from '../../api/client';
import type { AbbrNames } from '../../components/Abbr';

export type MakeupStatus = 'offen' | 'angesetzt' | 'erledigt' | 'entfallen';
export type MakeupAttestState = 'fehlt' | 'eingereicht' | 'genehmigt' | 'abgelehnt' | 'nicht_noetig';
/** Stufe der Sicht: full = Klassenleitung/Sekretariat/Leitung, family = Betroffene, teacher = Lehrkraft der Klausur */
export type MakeupLevel = 'full' | 'family' | 'teacher';

export interface MakeupAppointment {
  id: number;
  date: string;
  start: number;
  length: number;
  room: string | null;
  note: string;
  time: string;
  students: number;
}

export interface MakeupRow {
  id: number;
  exam_id: string;
  /** Kursraum der Klausur, nur wenn das Konto ihn öffnen darf */
  channel_id?: number | null;
  can_open?: boolean;
  course_id: string;
  student_id: string;
  student_name: string;
  class_id: string | null;
  exam_title: string;
  exam_kind: 'klausur' | 'test';
  label: string;
  subject: string;
  classes: string[];
  teachers: string[];
  exam_date: string;
  exam_start: number;
  exam_length: number;
  exam_time: string;
  exam_room: string | null;
  status: MakeupStatus;
  status_label: string;
  /** Fachlehrkräfte sehen nur „abwesend“ (nie Krankmeldung/Grund) */
  source: string;
  source_label: string;
  attest: { state: MakeupAttestState; label: string; missing: boolean; absence_ids?: number[] };
  attest_waived: boolean;
  level: MakeupLevel;
  appointment: MakeupAppointment | null;
  can_schedule: boolean;
  can_waive: boolean;
  names: { teachers: Record<string, string>; subjects: Record<string, string>; rooms: Record<string, string>; classes: Record<string, string> };
}

export interface MakeupSummary {
  open: number;
  attest_missing: number;
  total: number;
}

export interface AppointmentInput {
  date: string;
  start: number;
  length: number;
  room?: string | null;
  note?: string;
  force?: boolean;
}

/** Terminvorschlag: eigene Stunde der Lehrkraft (`unterricht`) oder freie Zeit (`frei`: Freistunde `luecke` bzw. Randstunde `rand`) */
export interface MakeupSuggestion {
  kind: 'unterricht' | 'frei';
  slot?: 'luecke' | 'rand';
  date: string;
  start: number;
  length: number;
  room: string | null;
  time: string;
  /** Kinder, für die der Vorschlag gilt (bei `unterricht` nur die, die in der Stunde sitzen) */
  student_ids: string[];
  covers_all: boolean;
  reason: string;
}

export const makeupsApi = {
  suggestions: (ids: number[], signal?: AbortSignal) =>
    http.get<{ suggestions: MakeupSuggestion[]; students: Record<string, string> }>('/exam-makeups/suggestions', { makeup_ids: ids.join(',') }, { signal }),
  list: async (q: { from?: string; to?: string; status?: MakeupStatus; exam_id?: string; student_id?: string } = {}, signal?: AbortSignal) =>
    asList<MakeupRow>(await http.get<unknown>('/exam-makeups', { ...q }, { signal })),
  summary: (signal?: AbortSignal) => http.get<MakeupSummary>('/exam-makeups/summary', undefined, { signal }),
  schedule: (makeup_ids: number[], a: AppointmentInput) => http.post<MakeupAppointment>('/exam-makeups/dates', { makeup_ids, ...a }),
  reschedule: (id: number, a: AppointmentInput) => http.put<MakeupAppointment>(`/exam-makeups/dates/${id}`, a),
  unschedule: (id: number) => http.del<{ deleted: number }>(`/exam-makeups/dates/${id}`),
  patch: (id: number, p: { status?: 'offen' | 'erledigt' | 'entfallen'; attest_waived?: boolean }) => http.patch<MakeupRow>(`/exam-makeups/${id}`, p),
};

/** Namen der Zeile im Format des Kürzel-Bausteins (`AbbrNamesProvider`). */
export function abbrNamesOf(rows: readonly MakeupRow[]): AbbrNames | null {
  const first = rows[0];
  if (!first) return null;
  const n = first.names;
  return { teacher: n.teachers, subject: n.subjects, room: n.rooms, class: n.classes };
}

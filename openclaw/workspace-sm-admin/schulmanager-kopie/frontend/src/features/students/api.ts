/**
 * Endpunkte der Schüler-Selbstbedienung (§9.6).
 */
import { asList, http } from '../../api/client';
import type { StudentAbsence } from '../../api/types';
import type { DocCategory, DocStatus, DocSummary, DocumentInput, StudentDocument, StudentOverview, TasksOverview } from './types';

export const studentSelfApi = {
  overview: (studentId?: string | null, signal?: AbortSignal) =>
    http.get<StudentOverview>('/me/student-overview', { student_id: studentId || undefined }, { signal }),
  /** „Heute krank melden“ bzw. mehrere Tage/einzelne Stunden */
  report: (a: { student_id?: string; date_from: string; date_to: string; periods?: number[]; reason?: string; kind?: 'krank' | 'beurlaubung' }) =>
    http.post<StudentAbsence>('/student-absences', { reason: '', ...a }),
  withdrawAbsence: (id: number | string) => http.del<unknown>(`/student-absences/${encodeURIComponent(String(id))}`),
  /** „Ich komme früher zurück“: ab `back_date` (bzw. ab `back_lesson`. Stunde dieses Tages) wieder da */
  shorten: (id: number | string, body: { back_date: string; back_lesson?: number }) =>
    http.post<StudentAbsence & { new_absence_id: number | null }>(`/student-absences/${encodeURIComponent(String(id))}/shorten`, body),
  /** Verlängern bis `date_to` (bei genehmigter Beurlaubung: neuer Antrag; `reason` = Anlass) */
  extend: (id: number | string, body: { date_to: string; reason?: string }) =>
    http.post<StudentAbsence & { extended_from: number | null }>(`/student-absences/${encodeURIComponent(String(id))}/extend`, body),
  /** schon bearbeitete Meldung: Klassenleitung um Rücknahme bitten */
  requestWithdrawal: (id: number | string) =>
    http.post<{ requested: boolean; already: boolean }>(`/student-absences/${encodeURIComponent(String(id))}/request-withdrawal`, {}),
  /** genehmigte Beurlaubung zurückgeben */
  returnLeave: (id: number | string) => http.post<{ returned: number }>(`/student-absences/${encodeURIComponent(String(id))}/return-leave`, {}),
  /** offene Aufgaben (Kursräume) – Eltern je Kind */
  tasks: (studentId?: string | null, signal?: AbortSignal) =>
    http.get<TasksOverview>('/channels/overview', { student_id: studentId || undefined }, { signal }),
  unread: (signal?: AbortSignal) => http.get<{ unread: number }>('/messages/unread', undefined, { signal }),
};

export const documentsApi = {
  list: async (q: { student_id?: string; status?: DocStatus | ''; category?: DocCategory | ''; absence_id?: number } = {}, signal?: AbortSignal) =>
    asList<StudentDocument>(
      await http.get<unknown>('/student-documents', { student_id: q.student_id, status: q.status || undefined, category: q.category || undefined, absence_id: q.absence_id }, { signal }),
    ),
  submit: (d: DocumentInput) => http.post<StudentDocument>('/student-documents', d),
  handle: (id: number, patch: { status?: DocStatus; note?: string }) => http.patch<StudentDocument>(`/student-documents/${id}`, patch),
  remove: (id: number) => http.del<{ deleted: number }>(`/student-documents/${id}`),
  summary: (signal?: AbortSignal) => http.get<DocSummary>('/student-documents/summary', undefined, { signal }),
  missingAttests: async (from: string, signal?: AbortSignal) =>
    asList<StudentAbsence>(await http.get<unknown>('/student-absences', { from, attest_missing: 1 }, { signal })),
};

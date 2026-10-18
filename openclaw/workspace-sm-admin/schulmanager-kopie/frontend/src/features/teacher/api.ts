/**
 * Endpunkte der Lehrer-Selbstverwaltung (§9.3) und der Planauswahl (Lehrer-Scope).
 */
import { asList, http } from '../../api/client';
import type {
  AllowedRefs,
  ChangeRequest,
  ExceptionImpact,
  MyProfileResponse,
  PreviewResponse,
  ReplanJob,
  RequestStatus,
  RequestsSummary,
  SaveResponse,
  TeacherProfile,
} from './types';

const enc = encodeURIComponent;

export type ProfileInput = Partial<TeacherProfile>;

export const teacherProfileApi = {
  mine: () => http.get<MyProfileResponse>('/me/teacher-profile'),
  previewMine: (p: ProfileInput) => http.post<PreviewResponse>('/me/teacher-profile/preview', p),
  saveMine: (p: ProfileInput & { note?: string }) => http.put<SaveResponse>('/me/teacher-profile', p),
  withdraw: () => http.del<ChangeRequest>('/me/teacher-profile/request'),
  /** Einmalige Ausnahme beantragen (Datum, Stunden; leer = ganztägig) */
  requestException: (b: { date_from: string; date_to?: string; periods: number[]; reason: string; note?: string }) =>
    http.post<{ status: string; request: ChangeRequest; impact: ExceptionImpact }>('/me/teacher-requests/exception', b),
  withdrawException: (id: number) => http.del<ChangeRequest>(`/me/teacher-requests/${id}`),
  /** Vorschau für den Stammdaten-Editor (Planung) */
  preview: (teacherId: string, p: ProfileInput) => http.post<PreviewResponse>(`/teacher-profiles/${enc(teacherId)}/preview`, p),
};

export const teacherRequestsApi = {
  list: async (status: RequestStatus | 'alle' = 'offen', teacherId?: string) =>
    asList<ChangeRequest>(await http.get<unknown>('/teacher-requests', { status, teacher_id: teacherId })),
  get: (id: number) => http.get<ChangeRequest>(`/teacher-requests/${id}`),
  summary: () => http.get<RequestsSummary>('/teacher-requests/summary'),
  approve: (id: number, comment = '') =>
    http.post<{ request: ChangeRequest; conflicts: ChangeRequest['conflicts']; version: number }>(`/teacher-requests/${id}/approve`, { comment }),
  reject: (id: number, comment = '') => http.post<{ request: ChangeRequest }>(`/teacher-requests/${id}/reject`, { comment }),
};

export const replanApi = {
  start: (teacherId: string, opts: { time_limit?: number; scope?: 'teacher' | 'classes'; seed?: number } = {}) =>
    http.post<{ job_id: string; job: ReplanJob }>(`/planning/replan-teacher/${enc(teacherId)}`, opts),
  job: (id: string) => http.get<ReplanJob>(`/planning/jobs/${enc(id)}`),
  jobs: async () => asList<ReplanJob>(await http.get<unknown>('/planning/jobs')),
  cancel: (id: string) => http.post<ReplanJob>(`/planning/jobs/${enc(id)}/cancel`, {}),
  apply: (id: string) => http.post<{ job: ReplanJob; lessons: number; version: number }>(`/planning/jobs/${enc(id)}/apply`, {}),
};

export const timetableScopeApi = {
  allowed: () => http.get<AllowedRefs>('/timetable/allowed'),
};

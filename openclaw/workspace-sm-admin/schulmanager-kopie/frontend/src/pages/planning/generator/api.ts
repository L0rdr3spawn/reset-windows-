import { http } from '../../../api/client';
import type { Job, TimetableView } from '../../../api/types';
import type { ApplyResult, SnapshotDetail, SnapshotMeta, VariantDetail } from './types';

const enc = encodeURIComponent;
export type ViewKind = 'class' | 'teacher';

/** Endpunkte der Generator-Auswertung, Varianten und Plan-Stände. */
export const genApi = {
  generate: (opts: { time_limit?: number; keep_locked?: boolean; seed?: number; workers?: number; variants?: number; period?: string; copy_from?: string }) =>
    http.post<{ job_id: string; job?: Job }>('/planning/generate', opts),
  variant: (jobId: string, index: number, signal?: AbortSignal) =>
    http.get<VariantDetail>(`/planning/jobs/${enc(jobId)}/variants/${index}`, undefined, { signal }),
  variantView: (jobId: string, index: number, kind: ViewKind, ref: string, date?: string) =>
    http.get<TimetableView>(`/planning/jobs/${enc(jobId)}/variants/${index}/timetable/${kind}/${enc(ref)}`, { date }),
  apply: (jobId: string, body: { variant?: number; regenerate_duties: boolean }) =>
    http.post<ApplyResult>(`/planning/jobs/${enc(jobId)}/apply`, body),
  clear: (body: { period?: string; all?: boolean } = {}) => http.post<{ lessons: number; period?: string }>('/planning/clear', body),
  snapshots: (signal?: AbortSignal) => http.get<SnapshotMeta[]>('/planning/snapshots', undefined, { signal }),
  snapshot: (id: number, signal?: AbortSignal) => http.get<SnapshotDetail>(`/planning/snapshots/${id}`, undefined, { signal }),
  snapshotView: (id: number, kind: ViewKind, ref: string, date?: string) =>
    http.get<TimetableView>(`/planning/snapshots/${id}/timetable/${kind}/${enc(ref)}`, { date }),
  saveSnapshot: (body: { name: string; note?: string; job_id?: string; variant?: number; period?: string; whole?: boolean }) =>
    http.post<SnapshotMeta>('/planning/snapshots', body),
  restoreSnapshot: (id: number, regenerate_duties: boolean) =>
    http.post<ApplyResult>(`/planning/snapshots/${id}/restore`, { regenerate_duties }),
  deleteSnapshot: (id: number) => http.del<{ ok: boolean }>(`/planning/snapshots/${id}`),
};

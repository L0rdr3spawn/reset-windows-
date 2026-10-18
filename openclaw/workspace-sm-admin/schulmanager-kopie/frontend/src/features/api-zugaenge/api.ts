/** Endpunkte der API-Zugänge (docs/API-ZUGAENGE.md). */
import { http, request } from '../../api/client';
import type { AccessDetail, AccessDraft, AccessItem, AccessMeta, CreatedAccess, Preview } from './types';

export const accessApi = {
  meta: (signal?: AbortSignal) => http.get<AccessMeta>('/api-access/meta', undefined, { signal }),
  list: (all: boolean, signal?: AbortSignal) => http.get<AccessItem[]>('/api-access', all ? { all: 1 } : undefined, { signal }),
  detail: (id: number, signal?: AbortSignal) => http.get<AccessDetail>(`/api-access/${id}`, undefined, { signal }),
  preview: (body: AccessDraft) => http.post<Preview>('/api-access/preview', body),
  create: (body: AccessDraft) => http.post<CreatedAccess>('/api-access', body),
  revoke: (id: number) => request<{ ok: boolean }>('DELETE', `/api-access/${id}`),
};

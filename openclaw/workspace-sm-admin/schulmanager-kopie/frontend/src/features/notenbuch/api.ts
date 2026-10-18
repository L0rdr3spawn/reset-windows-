/** Endpunkte des Notenbuchs (`docs/NOTENBUCH.md`). */
import { API_BASE, http } from '../../api/client';
import type {
  BookListItem,
  ClassOverview,
  CourseOption,
  EntryPatch,
  GradebookSettings,
  LogRow,
  Meta,
  MyGradebook,
  SourceCandidate,
  Table,
} from './types';

const enc = encodeURIComponent;
const q = (params: Record<string, string | undefined>): string => {
  const parts = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== '')
    .map(([k, v]) => `${k}=${enc(String(v))}`);
  return parts.length ? `?${parts.join('&')}` : '';
};

export const gbApi = {
  meta: (signal?: AbortSignal) => http.get<Meta>('/gradebook/meta', undefined, { signal }),
  saveSettings: (body: Partial<GradebookSettings>) => http.put<Meta>('/gradebook/settings', body),
  books: (term?: string, signal?: AbortSignal) => http.get<{ term: string; term_label: string; books: BookListItem[] }>('/gradebook/books', { term }, { signal }),
  courses: (term: string, classId?: string, signal?: AbortSignal) =>
    http.get<{ term: string; term_label: string; courses: CourseOption[] }>('/gradebook/courses', { term, class_id: classId }, { signal }),
  create: (body: { course_id: string; part: number; term: string; scale_id?: string; copy_from?: number }) => http.post<Table>('/gradebook/books', body),
  book: (id: number, signal?: AbortSignal) => http.get<Table>(`/gradebook/books/${id}`, undefined, { signal }),
  patchBook: (id: number, body: { scale_id?: string; key_id?: string; rounding?: string; decimals?: number }) => http.patch<Table>(`/gradebook/books/${id}`, body),
  deleteBook: (id: number) => http.del<{ ok: boolean }>(`/gradebook/books/${id}`),
  addCategory: (id: number, body: { name: string; weight: number; parent_id?: number | null }) => http.post<Table>(`/gradebook/books/${id}/categories`, body),
  patchCategory: (cid: number, body: { name?: string; weight?: number; parent_id?: number | null; move_to_root?: boolean }) => http.patch<Table>(`/gradebook/categories/${cid}`, body),
  deleteCategory: (cid: number) => http.del<Table>(`/gradebook/categories/${cid}`),
  addItem: (id: number, body: Record<string, unknown>) => http.post<Table>(`/gradebook/books/${id}/items`, body),
  patchItem: (iid: number, body: Record<string, unknown>) => http.patch<Table>(`/gradebook/items/${iid}`, body),
  deleteItem: (iid: number) => http.del<Table>(`/gradebook/items/${iid}`),
  entries: (iid: number, entries: EntryPatch[]) => http.put<Table & { changed: number }>(`/gradebook/items/${iid}/entries`, { entries }),
  finals: (id: number, finals: { student_id: string; value?: string; note?: string }[]) => http.put<Table & { changed: number }>(`/gradebook/books/${id}/finals`, { finals }),
  applyProposals: (id: number, overwrite = false) => http.post<Table & { changed: number }>(`/gradebook/books/${id}/finals/apply-proposals`, { overwrite }),
  lock: (id: number) => http.post<Table & { missing_finals: number }>(`/gradebook/books/${id}/lock`),
  unlock: (id: number) => http.post<Table>(`/gradebook/books/${id}/unlock`),
  log: (id: number, signal?: AbortSignal) => http.get<{ log: LogRow[] }>(`/gradebook/books/${id}/log`, undefined, { signal }),
  sources: (id: number, signal?: AbortSignal) => http.get<{ sources: SourceCandidate[] }>(`/gradebook/books/${id}/sources`, undefined, { signal }),
  adopt: (id: number, body: { source_type: string; source_id: string; category_id?: number | null; weight?: number }) => http.post<Table>(`/gradebook/books/${id}/sources/adopt`, body),
  dismiss: (id: number, body: { source_type: string; source_id: string }) => http.post<Table>(`/gradebook/books/${id}/sources/dismiss`, body),
  restore: (id: number, body: { source_type: string; source_id: string }) => http.post<{ sources: SourceCandidate[] }>(`/gradebook/books/${id}/sources/restore`, body),
  sync: (id: number) => http.post<Table & { changed: number }>(`/gradebook/books/${id}/sources/sync`),
  my: (studentId?: string, term?: string, signal?: AbortSignal) => http.get<MyGradebook>('/gradebook/my', { student_id: studentId, term }, { signal }),
  classOverview: (classId: string, term?: string, signal?: AbortSignal) => http.get<ClassOverview>(`/gradebook/class/${enc(classId)}`, { term }, { signal }),
  conferenceUrl: (classId: string, term: string) => `${API_BASE}/gradebook/class/${enc(classId)}/conference.pdf${q({ term })}`,
  exportUrl: (term: string, format: string, classId?: string, includeOpen?: boolean) =>
    `${API_BASE}/gradebook/export${q({ term, format, class_id: classId, include_open: includeOpen ? 'true' : undefined })}`,
};

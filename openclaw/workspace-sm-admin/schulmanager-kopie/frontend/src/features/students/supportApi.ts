/** Nachteilsausgleich & Förderung: API-Aufrufe und Typen (Katalog, Einträge, Hinweise bei Klausuren, Personen). */
import { http } from '../../api/client';

export type SupportKind = 'nachteilsausgleich' | 'schulbegleitung' | 'foerderplan' | 'sonstiges';

export interface CatalogItem {
  id: number;
  label: string;
  kind: SupportKind;
  kind_label: string;
  uses_minutes: boolean;
  default_minutes: number | null;
  teacher_visible: boolean;
  active: boolean;
  sort: number;
}
export interface CatalogResponse {
  can_manage: boolean;
  kinds: Record<SupportKind, string>;
  items: CatalogItem[];
}
export interface CatalogBody {
  label: string;
  kind: SupportKind;
  uses_minutes: boolean;
  default_minutes: number | null;
  teacher_visible: boolean;
  active: boolean;
  sort?: number;
}

export interface SupportEntry {
  id: number;
  kind: SupportKind;
  kind_label: string;
  label: string;
  title?: string;
  details?: string;
  catalog_id?: number | null;
  minutes: number | null;
  subjects: string[];
  aids: string;
  valid_from: string | null;
  valid_to: string | null;
  files: { id: string; filename: string; inline?: boolean }[];
  created_by_name?: string;
  can_edit: boolean;
  /** full = Vollsicht mit Details und Nachweisen; hints = Kurzsicht für Lehrkräfte */
  level: 'full' | 'hints';
}
export interface SupportResponse {
  can_edit: boolean;
  level: 'full' | 'hints';
  kinds: Record<SupportKind, string>;
  catalog: CatalogItem[];
  entries: SupportEntry[];
}
export interface SupportBody {
  catalog_id: number | null;
  kind: SupportKind;
  title: string;
  details: string;
  minutes: number | null;
  subjects: string[];
  aids: string;
  valid_from: string | null;
  valid_to: string | null;
  file_ids: string[];
}

export interface ExamHintStudent {
  student_id: string;
  name: string;
  minutes: number;
  summary: string;
  items: { label: string; minutes: number | null; subjects: string[]; aids: string }[];
}

export interface StudentPeople {
  student: { id: string; name: string; class_id: string };
  class_teacher: { id: string; name: string } | null;
  parents: { id: number; name: string; email: string }[];
  subject_teachers: { subject: string; subject_name: string; teachers: { id: string; name: string; course: string }[] }[];
  can_see_support: boolean;
}

const sid = (id: string) => encodeURIComponent(id);

export const supportApi = {
  catalog: (signal?: AbortSignal) => http.get<CatalogResponse>('/support/catalog', undefined, { signal }),
  createCatalog: (b: CatalogBody) => http.post<CatalogItem>('/support/catalog', b),
  updateCatalog: (id: number, b: CatalogBody) => http.put<CatalogItem>(`/support/catalog/${id}`, b),
  removeCatalog: (id: number) => http.del<unknown>(`/support/catalog/${id}`),
  list: (id: string, signal?: AbortSignal) => http.get<SupportResponse>(`/students/${sid(id)}/support`, undefined, { signal }),
  create: (id: string, b: SupportBody) => http.post<SupportEntry>(`/students/${sid(id)}/support`, b),
  remove: (id: string, entry: number) => http.del<unknown>(`/students/${sid(id)}/support/${entry}`),
  flags: (signal?: AbortSignal) => http.get<{ flags: Record<string, string[]> }>('/students/support-flags', undefined, { signal }),
  examHints: (from: string, to: string, signal?: AbortSignal) =>
    http.get<{ hints: Record<string, ExamHintStudent[]> }>('/exams/support-hints', { from, to }, { signal }),
  people: (id: string, signal?: AbortSignal) => http.get<StudentPeople>(`/students/${sid(id)}/people`, undefined, { signal }),
};

/** Kurztext eines Eintrags für Listen: „Zeitzuschlag +15 Min. (Deutsch)“ */
export function entryText(e: Pick<SupportEntry, 'label' | 'minutes' | 'aids'>, subjectNames: string[] = []): string {
  let t = e.label;
  if (e.minutes) t += ` +${e.minutes} Min.`;
  if (e.aids) t += `: ${e.aids}`;
  if (subjectNames.length) t += ` (${subjectNames.join(', ')})`;
  return t;
}

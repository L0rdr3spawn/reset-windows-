/** Endpunkte der Aufgaben-Erweiterungen (Raster, Vorlagen, Fristverlängerung, Gruppen, Ergebnisse). */
import { buildQuery, http } from '../../../api/client';
import type { AssignSettings, AssignmentResult, Extension, GradeScale, GroupsResponse, Rubric, Template } from './types';

const base = (id: number) => `/channels/${id}`;

export interface SettingsInput {
  group_mode?: boolean;
  group_set_id?: number | null;
  max_points?: number | null;
  grade_scale?: GradeScale | null;
  rubric?: Rubric;
  rubric_title?: string;
  template_id?: number;
  clear_rubric?: boolean;
  show_parents?: boolean;
}

export interface AutoGroupsInput {
  count?: number;
  size?: number;
  shuffle?: boolean;
  mode?: 'new' | 'fill';
  name_prefix?: string;
}

export const assignApi = {
  settings: (id: number, itemId: number, signal?: AbortSignal) => http.get<AssignSettings>(`${base(id)}/items/${itemId}/assignment`, undefined, { signal }),
  saveSettings: (id: number, itemId: number, body: SettingsInput) => http.put<AssignSettings>(`${base(id)}/items/${itemId}/assignment`, body),

  templates: (signal?: AbortSignal) => http.get<{ templates: Template[]; presets: { id: string; label: string }[] }>('/grading/templates', undefined, { signal }),
  saveTemplate: (body: { title: string; rubric: Rubric; grade_scale?: GradeScale | null }, id?: number) =>
    id ? http.put<Template>(`/grading/templates/${id}`, body) : http.post<Template>('/grading/templates', body),
  deleteTemplate: (id: number) => http.del<{ deleted: number }>(`/grading/templates/${id}`),

  extensions: (id: number, itemId: number, signal?: AbortSignal) =>
    http.get<{ extensions: Extension[]; due_at: string | null }>(`${base(id)}/items/${itemId}/extensions`, undefined, { signal }),
  putExtension: (id: number, itemId: number, body: { user_id?: number; group_id?: number; due_at: string; reason: string }) =>
    http.put<Extension>(`${base(id)}/items/${itemId}/extensions`, body),
  deleteExtension: (id: number, itemId: number, extensionId: number) => http.del<{ deleted: number }>(`${base(id)}/items/${itemId}/extensions/${extensionId}`),

  results: (id: number, itemId?: number, signal?: AbortSignal) =>
    http.get<{ results: AssignmentResult[] }>(`${base(id)}/assignment-results`, { item_id: itemId }, { signal }),

  groups: (id: number, signal?: AbortSignal, studentId?: string | null) => http.get<GroupsResponse>(`${base(id)}/groups${buildQuery({ student_id: studentId || undefined })}`, undefined, { signal }),
  createSet: (id: number, name: string) => http.post<GroupsResponse>(`${base(id)}/group-sets`, { name }),
  renameSet: (id: number, setId: number, name: string) => http.patch<GroupsResponse>(`${base(id)}/group-sets/${setId}`, { name }),
  deleteSet: (id: number, setId: number) => http.del<GroupsResponse>(`${base(id)}/group-sets/${setId}`),
  createGroup: (id: number, setId: number, name: string) => http.post<GroupsResponse>(`${base(id)}/group-sets/${setId}/groups`, { name }),
  renameGroup: (id: number, groupId: number, name: string) => http.patch<GroupsResponse>(`${base(id)}/groups/${groupId}`, { name }),
  deleteGroup: (id: number, groupId: number) => http.del<GroupsResponse>(`${base(id)}/groups/${groupId}`),
  setMembers: (id: number, groupId: number, userIds: number[]) => http.put<GroupsResponse>(`${base(id)}/groups/${groupId}/members`, { user_ids: userIds }),
  autoGroups: (id: number, setId: number, body: AutoGroupsInput) => http.post<GroupsResponse>(`${base(id)}/group-sets/${setId}/auto`, body),
  itemGate: (id: number, itemId: number, groupIds: number[]) => http.put<{ group_ids: number[] }>(`${base(id)}/items/${itemId}/groups`, { group_ids: groupIds }),
  folderGate: (id: number, folderId: number, groupIds: number[]) => http.put<{ group_ids: number[] }>(`${base(id)}/folders/${folderId}/groups`, { group_ids: groupIds }),
};

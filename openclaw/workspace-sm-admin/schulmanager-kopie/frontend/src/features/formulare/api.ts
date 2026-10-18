/**
 * Formular-Baukasten (`/forms`, siehe schulmanager/server/routes/features_forms.py und docs/FORMULARE.md).
 */
import { API_BASE, asList, http } from '../../api/client';
import type { StoredFileInfo } from '../../api/files';

export type FieldType =
  | 'text'
  | 'textarea'
  | 'number'
  | 'date'
  | 'daterange'
  | 'select'
  | 'multiselect'
  | 'yesno'
  | 'confirm'
  | 'signature'
  | 'file'
  | 'student'
  | 'periods'
  | 'scale';

export interface FormField {
  id: string;
  type: FieldType;
  label: string;
  help?: string;
  required?: boolean;
  options?: string[];
  min?: number;
  max?: number;
  text?: string;
  /** Skala 1–5: Beschriftung der Enden */
  low?: string;
  high?: string;
}

export type AudienceRole = 'eltern' | 'schueler_adult' | 'schueler' | 'lehrer' | 'sekretariat' | 'schulleitung';
export type Approver = 'class_teacher' | 'sekretariat' | 'schulleitung' | 'user';
export type ActionType = 'create_absence' | 'inform_teachers' | 'calendar_entry';
export type AbsenceKind = 'beurlaubung' | 'krank' | 'fehlt';
export type FormStatus = 'eingereicht' | 'in_pruefung' | 'genehmigt' | 'abgelehnt' | 'erledigt' | 'zurueckgezogen';
export type TemplateStatus = 'entwurf' | 'aktiv' | 'archiviert';

export interface FormStep {
  approver: Approver;
  label?: string;
  user_id?: number | null;
}

export interface FormAction {
  type: ActionType;
  kind?: AbsenceKind;
  status?: 'gemeldet' | 'entschuldigt';
  student?: string | null;
  range?: string | null;
  periods?: string | null;
  reason?: string | null;
  title?: string;
  date?: string | null;
}

export interface FormDefinition {
  fields: FormField[];
  intro?: string;
  once?: boolean;
  legacy_pdf?: 'leave-form' | 'excuse-form' | null;
  audience: { roles: AudienceRole[]; scope: 'all' | 'classes' | 'grades'; classes: string[]; grades: number[] };
  workflow: { steps: FormStep[]; auto_complete: boolean };
  deadline: { open_from: string | null; open_until: string | null; decide_days: number | null; remind_days: number | null };
  actions: FormAction[];
  notify?: { submitter: boolean };
}

export interface FormTemplate {
  id: number;
  title: string;
  description: string;
  category: string;
  category_label: string;
  status: TemplateStatus;
  version: number;
  library_key: string | null;
  sensitive: boolean;
  created_by_name: string;
  created_at: string | null;
  updated_at: string | null;
  definition: FormDefinition;
  counts: { total: number; open: number } | null;
  versions?: { version: number; created_at: string | null; created_by_name: string; submissions: number }[];
}

export interface TemplateInput {
  title: string;
  description: string;
  category: string;
  sensitive: boolean;
  status?: TemplateStatus;
  definition: FormDefinition;
}

export interface LibraryEntry {
  key: string;
  title: string;
  description: string;
  category: string;
  category_label: string;
  sensitive: boolean;
  definition: FormDefinition;
  legacy_pdf: 'leave-form' | 'excuse-form' | null;
}

export interface FormsMeta {
  field_types: Record<FieldType, string>;
  categories: Record<string, string>;
  audience_roles: Record<AudienceRole, string>;
  approvers: Record<Approver, string>;
  action_types: Record<ActionType, string>;
  statuses: Record<FormStatus, string>;
  absence_kinds: Record<AbsenceKind, string>;
  manage: boolean;
  inbox: boolean;
  submit: boolean;
  periods: number;
  classes: { id: string; name: string; grade: number }[];
}

export interface Approvable {
  id: number;
  name: string;
  role: string;
  role_label: string;
}

export interface AvailableStudent {
  id: string;
  name: string;
  class_id: string | null;
  submission_id: number | null;
}

export interface AvailableForm {
  id: number;
  title: string;
  description: string;
  category: string;
  category_label: string;
  sensitive: boolean;
  version: number;
  open_until: string | null;
  needs_student: boolean;
  once: boolean;
  students: AvailableStudent[];
  submission_id: number | null;
  legacy_pdf: 'leave-form' | 'excuse-form' | null;
  fields: number;
}

export interface FillInfo extends AvailableForm {
  definition: FormDefinition;
  periods: number;
  signer: string;
}

export type Answers = Record<string, unknown>;

export interface SubmissionStep {
  approver: Approver;
  label: string;
}

export interface SubmissionEvent {
  id: number;
  action: string;
  step: number;
  actor_name: string;
  note: string;
  at: string | null;
}

export interface ActionResult {
  type: ActionType;
  ok: boolean;
  message: string;
  absence_id?: number;
}

export interface Submission {
  id: number;
  template_id: number;
  template_title: string;
  category: string;
  sensitive: boolean;
  version: number;
  student_id: string | null;
  student_name: string | null;
  class_id: string | null;
  submitted_by_name: string;
  submitted_role: string;
  status: FormStatus;
  status_label: string;
  step: number;
  steps: SubmissionStep[];
  current_step: string | null;
  created_at: string | null;
  updated_at: string | null;
  decided_at: string | null;
  decided_by_name: string | null;
  due_on: string | null;
  overdue: boolean;
  can_decide: boolean;
  can_complete: boolean;
  can_withdraw: boolean;
  can_scan: boolean;
  scan_count: number;
  staff: boolean;
  // nur im Detail
  answers?: { id: string; label: string; type: FieldType; value: unknown; display: string }[];
  definition?: FormDefinition;
  events?: SubmissionEvent[];
  decision_note?: string;
  scans?: StoredFileInfo[];
  attachments?: StoredFileInfo[];
  result?: { actions: ActionResult[]; at: string } | null;
  legacy_pdf?: string | null;
}

export interface FormsSummary {
  to_decide: number;
  overdue: number;
  to_fill: number;
  mine_open: number;
}

export interface SubmissionFilter {
  template_id?: number;
  status?: string;
  class_id?: string;
  student_id?: string;
  scope?: 'inbox' | 'mine' | 'all';
  open_only?: boolean;
  q?: string;
}

export type DecideAction = 'approve' | 'reject' | 'complete' | 'comment';

const url = (path: string, query: Record<string, string | number | undefined> = {}) => {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(query)) if (v !== undefined && v !== '') sp.set(k, String(v));
  const q = sp.toString();
  return `${API_BASE}${path}${q ? `?${q}` : ''}`;
};

export const formsApi = {
  meta: (signal?: AbortSignal) => http.get<FormsMeta>('/forms/meta', undefined, { signal }),
  summary: (signal?: AbortSignal) => http.get<FormsSummary>('/forms/summary', undefined, { signal }),
  approvers: (signal?: AbortSignal) => http.get<Approvable[]>('/forms/approvers', undefined, { signal }),
  // Vorlagen (Verwaltung)
  templates: async (signal?: AbortSignal) => asList<FormTemplate>(await http.get<unknown>('/forms/templates', undefined, { signal })),
  template: (id: number, signal?: AbortSignal) => http.get<FormTemplate>(`/forms/templates/${id}`, undefined, { signal }),
  create: (body: TemplateInput) => http.post<FormTemplate>('/forms/templates', body),
  update: (id: number, body: TemplateInput) => http.put<FormTemplate>(`/forms/templates/${id}`, body),
  setStatus: (id: number, status: TemplateStatus) => http.post<FormTemplate>(`/forms/templates/${id}/status`, { status }),
  duplicate: (id: number) => http.post<FormTemplate>(`/forms/templates/${id}/duplicate`),
  remove: (id: number) => http.del<{ deleted: number }>(`/forms/templates/${id}`),
  library: async (signal?: AbortSignal) => asList<LibraryEntry>(await http.get<unknown>('/forms/library', undefined, { signal })),
  adopt: (key: string) => http.post<FormTemplate>(`/forms/library/${encodeURIComponent(key)}/adopt`),
  // Ausfüllen
  available: async (signal?: AbortSignal) => asList<AvailableForm>(await http.get<unknown>('/forms/available', undefined, { signal })),
  fillInfo: (id: number, signal?: AbortSignal) => http.get<FillInfo>(`/forms/templates/${id}/fill`, undefined, { signal }),
  submit: (id: number, body: { student_id?: string | null; answers: Answers }) => http.post<Submission>(`/forms/templates/${id}/submit`, body),
  // Einreichungen
  submissions: async (f: SubmissionFilter = {}, signal?: AbortSignal) =>
    asList<Submission>(await http.get<unknown>('/forms/submissions', { ...f }, { signal })),
  submission: (id: number, signal?: AbortSignal) => http.get<Submission>(`/forms/submissions/${id}`, undefined, { signal }),
  decide: (id: number, action: DecideAction, note = '') => http.post<Submission>(`/forms/submissions/${id}/decide`, { action, note }),
  retry: (id: number) => http.post<Submission>(`/forms/submissions/${id}/retry-actions`),
  withdraw: (id: number) => http.post<Submission>(`/forms/submissions/${id}/withdraw`),
  addScan: (id: number, file_id: string) => http.post<Submission>(`/forms/submissions/${id}/scan`, { file_id }),
  removeScan: (id: number, file_id: string) => http.del<Submission>(`/forms/submissions/${id}/scan/${encodeURIComponent(file_id)}`),
  // Adressen für Downloads (PDF/CSV)
  blankPdfUrl: (id: number) => url(`/forms/templates/${id}/blank.pdf`),
  submissionPdfUrl: (id: number) => url(`/forms/submissions/${id}/pdf`),
  exportCsvUrl: (template_id: number, status?: string) => url('/forms/export.csv', { template_id, status }),
  exportPdfUrl: (template_id: number, status?: string) => url('/forms/export.pdf', { template_id, status }),
  legacyPdfUrl: (kind: 'leave-form' | 'excuse-form', student_id?: string) =>
    url(kind === 'leave-form' ? '/student-absences/leave-form.pdf' : '/student-absences/form.pdf', { student_id }),
  /** Vorschau eines noch ungespeicherten Formulars als PDF (Blob) */
  previewPdf: async (title: string, description: string, definition: FormDefinition): Promise<Blob> => {
    const { getCsrfToken } = await import('../../api/client');
    const res = await fetch(`${API_BASE}/forms/preview.pdf`, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrfToken() ?? '' },
      body: JSON.stringify({ title, description, definition }),
    });
    if (!res.ok) throw new Error('Die Vorschau konnte nicht erstellt werden. Bitte die Felder prüfen.');
    return res.blob();
  },
};

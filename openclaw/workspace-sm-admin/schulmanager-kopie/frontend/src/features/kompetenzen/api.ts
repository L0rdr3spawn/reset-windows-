/**
 * Kompetenzraster und Lernstand (`/competency/*`, schulmanager/server/routes/features_competency*.py, docs/KOMPETENZEN.md).
 */
import { API_BASE, asList, buildQuery, http } from '../../api/client';

export type ViewKind = 'staff' | 'self' | 'family';
export type EvidenceType = '' | 'note' | 'link' | 'assignment' | 'material';
export type PlanStatus = 'offen' | 'in_arbeit' | 'erledigt';

export interface Competency {
  id: number;
  code: string;
  title: string;
  descriptors: string[];
}
export interface Area {
  id: number;
  name: string;
  competencies: Competency[];
}
export interface Framework {
  id: number;
  name: string;
  subject: string;
  description: string;
  levels: string[];
  support_level: number;
  archived: boolean;
  areas: Area[];
}
export interface FrameworkSummary {
  id: number;
  name: string;
  subject: string;
  description: string;
  levels: string[];
  support_level: number;
  archived: boolean;
  areas: number;
  competencies: number;
}
export interface TemplateInfo {
  key: string;
  name: string;
  description: string;
  levels: string[];
  areas: number;
  competencies: number;
}

export interface AssessmentEntry {
  id: number;
  kind: 'teacher' | 'self';
  level: number;
  date: string;
  by: string;
  evidence_type: EvidenceType;
  evidence_ref: string;
  evidence: string;
  comment: string;
  confirmed: boolean;
  confirmed_by: string;
}
export interface CompetencyState extends Competency {
  teacher: AssessmentEntry | null;
  self: AssessmentEntry | null;
  pending: boolean;
  history: AssessmentEntry[];
  links: { item_type: string; item_id: string; title: string }[];
  /** nur Lehrkräfte */
  support?: boolean;
}
export interface AreaState {
  id: number;
  name: string;
  competencies: CompetencyState[];
  progress: number;
  assessed: number;
}
export interface FrameworkState {
  id: number;
  name: string;
  subject: string;
  description: string;
  levels: string[];
  support_level: number;
  areas: AreaState[];
  progress: number;
  assessed: number;
  total: number;
}
export interface AwardedBadge {
  award_id: number;
  badge_id: number;
  name: string;
  description: string;
  icon: string;
  color: string;
  date: string;
  auto: boolean;
  by: string;
  note: string;
}
export interface StudentView {
  student: { id: string; name: string; class_id: string };
  kind: ViewKind;
  can_assess: boolean;
  frameworks: FrameworkState[];
  badges: AwardedBadge[];
}

export interface OverviewCell {
  t: number | null;
  s: number | null;
  p: boolean;
}
export interface OverviewStudent {
  id: string;
  name: string;
  cells: Record<string, OverviewCell>;
  support: number;
  pending: number;
  progress: number;
}
export interface Overview {
  classes: { id: string; name: string }[];
  frameworks: FrameworkSummary[];
  framework: (Pick<Framework, 'id' | 'name' | 'subject' | 'levels' | 'support_level' | 'areas'> & { all_areas: { id: number; name: string }[] }) | null;
  class: { id: string; name: string } | null;
  students: OverviewStudent[];
  summary: { students?: number; support_students?: number; pending?: number };
}

export interface Plan {
  id: number;
  student_id: string;
  competency_id: number | null;
  competency_title: string;
  framework_name: string;
  area_name: string;
  title: string;
  note: string;
  week_start: string | null;
  due_date: string | null;
  status: PlanStatus;
  source: 'lehrkraft' | 'schueler';
  item_type: string;
  item_id: string;
  overdue: boolean;
  done_at: string | null;
  can_edit: boolean;
  can_status: boolean;
}
export interface PlanList {
  student: { id: string; name: string; class_id: string };
  kind: ViewKind;
  can_assess: boolean;
  current_week: string;
  plans: Plan[];
}

export type BadgeCriteria =
  | null
  | { type: 'competencies'; competency_ids: number[]; min_level: number }
  | { type: 'area'; area_id: number; min_level: number; share: number }
  | { type: 'framework'; framework_id: number; min_level: number; share: number };
export interface Badge {
  id: number;
  name: string;
  description: string;
  icon: string;
  color: string;
  criteria: BadgeCriteria;
  criteria_text: string;
  auto: boolean;
  active: boolean;
  awarded: number;
}
export interface BadgeInput {
  name: string;
  description: string;
  icon: string;
  color: string;
  criteria: BadgeCriteria;
  active: boolean;
}

export interface AssessInput {
  student_id: string;
  competency_id: number;
  level: number;
  date?: string;
  evidence_type?: EvidenceType;
  evidence_ref?: string;
  evidence_text?: string;
  comment?: string;
}

export interface FrameworkInput {
  name: string;
  subject: string;
  description: string;
  levels: string[];
  support_level: number;
  areas: { id?: number; name: string; competencies: { id?: number; code: string; title: string; descriptors: string[] }[] }[];
}

export interface LinkedCompetency {
  competency_id: number;
  title: string;
  code: string;
  framework_id: number;
  framework_name: string;
  area_name: string;
}

const enc = encodeURIComponent;

export const compApi = {
  frameworks: async (archived = false, signal?: AbortSignal) =>
    asList<FrameworkSummary>(await http.get<unknown>('/competency/frameworks', { archived: archived ? 1 : undefined }, { signal })),
  framework: (id: number, signal?: AbortSignal) => http.get<Framework>(`/competency/frameworks/${id}`, undefined, { signal }),
  createFramework: (b: FrameworkInput) => http.post<Framework>('/competency/frameworks', b),
  saveFramework: (id: number, b: FrameworkInput, force = false) => http.put<Framework>(`/competency/frameworks/${id}${buildQuery({ force: force ? 1 : undefined })}`, b),
  archiveFramework: (id: number, archived: boolean) => http.post<{ id: number }>(`/competency/frameworks/${id}/archive${buildQuery({ archived })}`),
  deleteFramework: (id: number) => http.del<{ deleted: number }>(`/competency/frameworks/${id}`),
  importFramework: (b: { format: 'json' | 'csv'; content: string; name?: string; subject?: string; levels?: string[] }) => http.post<Framework>('/competency/frameworks/import', b),
  exportUrl: (id: number, format: 'json' | 'csv') => `${API_BASE}/competency/frameworks/${id}/export${buildQuery({ format })}`,
  templates: async (signal?: AbortSignal) => asList<TemplateInfo>(await http.get<unknown>('/competency/templates', undefined, { signal })),
  useTemplate: (key: string) => http.post<Framework>(`/competency/templates/${enc(key)}/use`),

  student: (sid: string, frameworkId?: number, signal?: AbortSignal) => http.get<StudentView>(`/competency/students/${enc(sid)}`, { framework_id: frameworkId }, { signal }),
  reportUrl: (sid: string, frameworkId?: number) => `${API_BASE}/competency/students/${enc(sid)}/report.pdf${buildQuery({ framework_id: frameworkId })}`,
  assess: (entries: AssessInput[]) => http.post<{ created: number; skipped: number; badges: { student_id: string; name: string }[] }>('/competency/assessments', { entries }),
  selfAssess: (competency_id: number, level: number, comment = '') => http.post<AssessmentEntry>('/competency/self', { competency_id, level, comment }),
  confirm: (id: number, level?: number, comment = '') => http.post<{ teacher: AssessmentEntry }>(`/competency/self/${id}/confirm`, { level, comment }),
  overview: (q: { framework_id?: number; class_id?: string; area_id?: number }, signal?: AbortSignal) => http.get<Overview>('/competency/overview', q, { signal }),

  plans: (sid: string, signal?: AbortSignal) => http.get<PlanList>('/competency/plans', { student_id: sid }, { signal }),
  createPlans: (b: { student_ids?: string[]; student_id?: string; competency_id?: number | null; title?: string; note?: string; week_start?: string | null; due_date?: string | null }) =>
    http.post<{ created: Plan[] }>('/competency/plans', b),
  patchPlan: (id: number, b: Partial<{ title: string; note: string; week_start: string | null; due_date: string | null; status: PlanStatus }>) => http.patch<Plan>(`/competency/plans/${id}`, b),
  deletePlan: (id: number) => http.del<{ deleted: number }>(`/competency/plans/${id}`),

  badges: async (signal?: AbortSignal) => asList<Badge>(await http.get<unknown>('/competency/badges', undefined, { signal })),
  createBadge: (b: BadgeInput) => http.post<Badge>('/competency/badges', b),
  saveBadge: (id: number, b: BadgeInput) => http.put<Badge>(`/competency/badges/${id}`, b),
  deleteBadge: (id: number) => http.del<{ deleted: number }>(`/competency/badges/${id}`),
  award: (id: number, student_ids: string[], note = '') => http.post<{ awarded: number; already: number }>(`/competency/badges/${id}/award`, { student_ids, note }),
  revoke: (id: number, sid: string) => http.del<{ revoked: string }>(`/competency/badges/${id}/award/${enc(sid)}`),
  evaluateBadges: () => http.post<{ awarded: number }>('/competency/badges/evaluate'),

  links: async (itemType: string, itemId: string, signal?: AbortSignal) =>
    asList<LinkedCompetency>(await http.get<unknown>('/competency/links', { item_type: itemType, item_id: itemId }, { signal })),
  setLinks: (itemType: string, itemId: string, competencyIds: number[]) =>
    http.put<{ competency_ids: number[] }>('/competency/links', { item_type: itemType, item_id: itemId, competency_ids: competencyIds }),
};

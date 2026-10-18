/**
 * Plan prüfen: Vorschlagspakete der Dauerprüfung (`/planning/proposals`, siehe schulmanager/server/routes/features_proposals.py
 * und docs/PLAN-PRUEFUNG.md).
 */
import { http } from '../../api/client';
import type { AutoPlanStatus, TimetableView } from '../../api/types';

export type PackageStatus = 'berechnung' | 'offen' | 'angenommen' | 'verworfen' | 'ersetzt' | 'erledigt' | 'veraltet' | 'fehlgeschlagen';
export type VariantKey = 'minimal' | 'lokal' | 'gruendlich' | 'vertretung' | 'raeume';

export interface ProposalMetrics {
  problems?: number;
  conflicts?: number;
  unplaced_hours?: number;
  class_gaps?: number | null;
  teacher_gaps?: number | null;
  site_changes?: number | null;
  core_late?: number | null;
  late_start?: number | null;
  spread?: number | null;
  doubles?: number | null;
  teacher_wish?: number | null;
}

export interface ProposalChange {
  course_id: string;
  label: string;
  classes: string[];
  teachers: string[];
  from: string[];
  to: string[];
  rooms: { where: string; old: string[]; new: string[] }[];
  cover?: string;
}

export interface ProposalVariant {
  id: number;
  package_id: number;
  key: VariantKey | string;
  position: number;
  title: string;
  description: string;
  status: string;
  metrics_before: ProposalMetrics;
  metrics_after: ProposalMetrics;
  changes: ProposalChange[];
  affected_classes: string[];
  affected_teachers: string[];
  moved_lessons: number;
  remaining: string[];
  valid_from: string | null;
  compute_seconds: number;
  diff_size: number;
}

export interface ProposalLogRow {
  at: string;
  action: string;
  actor: string;
  variant_id: number | null;
  note: string | null;
  detail: Record<string, unknown>;
}

export interface ProposalPackage {
  id: number;
  status: PackageStatus;
  title: string;
  created_at: string;
  updated_at: string;
  base_version: number | null;
  reasons: string[];
  trigger_scope: string[];
  trigger_labels: string[];
  problem_count: number;
  valid_from: string | null;
  postponed_until: string | null;
  postponed_by: string | null;
  decided_at: string | null;
  decided_by: string | null;
  decision_note: string | null;
  chosen_variant_id: number | null;
  applied_version: number | null;
  informed: string[];
  variants?: ProposalVariant[];
  log?: ProposalLogRow[];
  outdated?: boolean;
}

export interface ProposalSummary {
  open: number;
  postponed: number;
  computing: number;
  newest: { id: number; title: string; created_at: string; problem_count: number } | null;
  builder: { package_id: number; done: number; total: number; job_id: string | null } | null;
}

export interface ProposalsResponse {
  summary: ProposalSummary;
  open: ProposalPackage[];
  recent: ProposalPackage[];
  check: AutoPlanStatus & { auto_apply?: 'aus' | 'raeume' };
}

export const proposalsApi = {
  list: (signal?: AbortSignal) => http.get<ProposalsResponse>('/planning/proposals', undefined, { signal }),
  summary: (signal?: AbortSignal) => http.get<ProposalSummary>('/planning/proposals/summary', undefined, { signal }),
  get: (id: number, signal?: AbortSignal) => http.get<ProposalPackage>(`/planning/proposals/${id}`, undefined, { signal }),
  accept: (id: number, variantId: number, note: string) =>
    http.post<ProposalPackage>(`/planning/proposals/${id}/variants/${variantId}/accept`, { note }),
  discard: (id: number, reason: string) => http.post<ProposalPackage>(`/planning/proposals/${id}/discard`, { reason }),
  postpone: (id: number, hours = 24) => http.post<ProposalPackage>(`/planning/proposals/${id}/postpone`, { hours }),
  wake: (id: number) => http.post<ProposalPackage>(`/planning/proposals/${id}/wake`, {}),
  draftView: (id: number, variantId: number, kind: 'class' | 'teacher' | 'room', ref: string, date?: string) =>
    http.get<TimetableView>(`/planning/proposals/${id}/variants/${variantId}/timetable/${kind}/${encodeURIComponent(ref)}`, { date }),
};

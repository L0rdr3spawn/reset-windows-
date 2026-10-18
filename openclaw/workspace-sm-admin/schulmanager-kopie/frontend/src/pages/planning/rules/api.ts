/** Endpunkte der Regel-Bausteine (`routes/features_rules.py`). */
import { http } from '../../../api/client';
import type { Job } from '../../../api/types';
import type { RuleItems, RulesDraft, RulesState, RuleTemplate } from './model';

export const rulesApi = {
  get: (signal?: AbortSignal) => http.get<RulesState>('/settings/rules', undefined, { signal }),
  /** Teil-Update; `items` ersetzt alle Bausteine */
  put: (body: Partial<RulesDraft> & { templates?: Omit<RuleTemplate, 'builtin'>[] }) => http.put<RulesState>('/settings/rules', body),
  /** Vorlage anwenden – liefert nur den Entwurf, speichert nichts */
  applyTemplate: (template: string) => http.post<{ profile: string; items: RuleItems; show: string[] }>('/settings/rules/template', { template }),
  saveTemplate: (body: { name: string; description: string; items: RuleItems; show?: string[] }) =>
    http.post<{ id: string; templates: RuleTemplate[] }>('/settings/rules/templates', body),
  deleteTemplate: (id: string) => http.del<{ templates: RuleTemplate[] }>(`/settings/rules/templates/${encodeURIComponent(id)}`),
  /** Probelauf des Generators mit ungespeicherten Regeln (Entwurf wird nicht übernommen) */
  simulate: (rules: RulesDraft, time_limit: number) => http.post<{ job_id: string; job?: Job }>('/planning/generate', { rules, time_limit, workers: 1 }),
};

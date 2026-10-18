/** Endpunkte der Anmelde-Richtlinien (§11.5) und der Verknüpfung (Agent Anbieter, §11.4). */
import { asList, http, request } from '../../api/client';
import type { Audience, EffectiveResponse, PoliciesResponse, PolicyRule, ReportResponse, RuleBody, Scope, SsoProvider } from './types';

const enc = encodeURIComponent;

/** `ref` in der Adresse: Standard-Regel ohne Bezug → „-“. */
function rulePath(scope: Scope, ref: string): string {
  return `/login-policies/${enc(scope)}/${enc(scope === 'default' ? '-' : ref)}`;
}

function audienceQuery(scope: Scope, audience: Audience): { audience?: string } {
  return scope === 'grade' || scope === 'class' ? { audience } : {};
}

export const policyApi = {
  list: (signal?: AbortSignal) => http.get<PoliciesResponse>('/login-policies', undefined, { signal }),
  save: (scope: Scope, ref: string, audience: Audience, body: RuleBody) =>
    request<{ rule: PolicyRule | null }>('PUT', rulePath(scope, ref), { body, query: audienceQuery(scope, audience) }),
  remove: (scope: Scope, ref: string, audience: Audience) =>
    request<{ ok: boolean }>('DELETE', rulePath(scope, ref), { query: audienceQuery(scope, audience) }),
  effectiveUser: (userId: number, signal?: AbortSignal) =>
    http.get<EffectiveResponse>('/login-policies/effective', { user_id: userId }, { signal }),
  effectiveGroup: (q: { class_id?: string; grade?: string; role?: string; audience?: Audience }, signal?: AbortSignal) =>
    http.get<EffectiveResponse>('/login-policies/effective', { ...q, audience: q.audience === 'alle' ? undefined : q.audience }, { signal }),
  report: (classId: string, audience: Audience, signal?: AbortSignal) =>
    http.get<ReportResponse>('/login-policies/report', { class_id: classId, audience }, { signal }),
};

export const linkApi = {
  /** Anbieter, die gerade nutzbar sind (öffentlich, auch für die Login-Seite). */
  providers: async (signal?: AbortSignal) => asList<SsoProvider>(await http.get<unknown>('/auth/sso/providers', undefined, { signal, skipAuthRedirect: true })),
  /** Verknüpfung starten → Adresse des Anbieters (Status an die Sitzung gebunden). */
  start: (provider: string) => http.post<{ url: string }>(`/me/identities/${enc(provider)}/link`, { next: '/konten-verbinden' }),
};

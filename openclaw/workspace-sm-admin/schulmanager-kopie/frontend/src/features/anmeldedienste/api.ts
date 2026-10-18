/** Endpunkte der Anmeldedienste (§11.4). */
import { asList, http } from '../../api/client';
import type { MyIdentities, ProviderSetup, ProviderUpdate, SetupOverview, SsoProvider, TestResult, UserIdentities } from './types';

export const ssoApi = {
  /** öffentlich (Login-Seite) */
  providers: async (signal?: AbortSignal) =>
    asList<SsoProvider>(await http.get<unknown>('/auth/sso/providers', undefined, { signal, skipAuthRedirect: true })),
  /** Nonce für ein ID-Token, das der Browser direkt bekommt (Google One Tap, Apple-Popup) */
  nonce: (provider: string) => http.post<{ nonce: string }>(`/auth/sso/${encodeURIComponent(provider)}/nonce`, {}, { skipAuthRedirect: true }),
  /** Anmelden mit diesem ID-Token (der Server prüft Signatur, Aussteller, Zielgruppe, Ablauf und Nonce) */
  token: (provider: string, idToken: string, next: string | null, add: boolean) =>
    http.post<{ next: string }>(`/auth/sso/${encodeURIComponent(provider)}/token`, { id_token: idToken, next, add }, { skipAuthRedirect: true }),
  mine: (signal?: AbortSignal) => http.get<MyIdentities>('/me/identities', undefined, { signal }),
  /** Verbinden starten → Adresse beim Anbieter (bzw. Test-Anbieter) */
  link: (provider: string, next?: string) => http.post<{ url: string }>(`/me/identities/${encodeURIComponent(provider)}/link`, { next }),
  unlink: (provider: string) => http.del<MyIdentities>(`/me/identities/${encodeURIComponent(provider)}`),
  // Verwaltung
  ofUser: (userId: number, signal?: AbortSignal) => http.get<UserIdentities>(`/users/${userId}/identities`, undefined, { signal }),
  reserve: (userId: number, provider: string, email: string) => http.post<UserIdentities>(`/users/${userId}/identities`, { provider, email }),
  remove: (userId: number, provider: string) => http.del<UserIdentities>(`/users/${userId}/identities/${encodeURIComponent(provider)}`),
  // Einrichtung (nur Administration)
  setup: (signal?: AbortSignal) => http.get<SetupOverview>('/sso/providers/config', undefined, { signal }),
  update: (provider: string, body: ProviderUpdate) => http.put<ProviderSetup>(`/sso/providers/${encodeURIComponent(provider)}`, body),
  test: (provider: string) => http.post<TestResult>(`/sso/providers/${encodeURIComponent(provider)}/test`),
};

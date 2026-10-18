/**
 * Endpunkte der Zugangsbriefe (§11.3). Downloads laufen über normale Links (Cookie-Anmeldung, GET ohne CSRF).
 */
import { API_BASE, http } from '../../api/client';
import type { BatchCreateBody, BatchCreateResult, BatchInfo, ClassAccounts, PasswordInfo, PasswordResult, SendResult, SendTarget } from './types';

const enc = encodeURIComponent;
const BASE = '/letters/batches';

export const lettersApi = {
  /** neue Startpasswörter für vorhandene Konten (bzw. Schüler/innen) + Brief-Stapel */
  create: (body: BatchCreateBody) => http.post<BatchCreateResult>(BASE, body),
  get: async (id: string, signal?: AbortSignal): Promise<BatchInfo> => {
    const b = await http.get<BatchInfo>(`${BASE}/${enc(id)}`, undefined, { signal });
    return {
      ...b,
      entries: (b.entries ?? []).map((e) => ({
        ...e,
        children: e.children ?? [],
        login_methods: e.login_methods ?? [],
        required_links: e.required_links ?? [],
      })),
    };
  },
  pdfUrl: (id: string) => `${API_BASE}${BASE}/${enc(id)}/pdf`,
  zipUrl: (id: string) => `${API_BASE}${BASE}/${enc(id)}/zip`,
  entryUrl: (id: string, userId: number | string) => `${API_BASE}${BASE}/${enc(id)}/entries/${enc(String(userId))}.pdf`,
  send: async (id: string, body: { to: SendTarget; user_ids?: number[] }): Promise<SendResult> => {
    const r = await http.post<SendResult>(`${BASE}/${enc(id)}/send`, body);
    return { ...r, sent: r?.sent ?? [], no_address: r?.no_address ?? [], unavailable: r?.unavailable ?? [] };
  },
};

export const passwordsApi = {
  info: (userId: number | string, signal?: AbortSignal) => http.get<PasswordInfo>(`/users/${enc(String(userId))}/password`, undefined, { signal }),
  /** neues Einmal-/Startpasswort (einmalig in der Antwort) + Brief als PDF; Passwortwechsel-Zwang */
  resetToNew: (userId: number | string) => http.post<PasswordResult>(`/users/${enc(String(userId))}/password`, { mode: 'new' }),
  /** Passwort wieder auf das gespeicherte Startpasswort (Passwortwechsel-Zwang, Brief erneut als PDF) */
  /** selbst gewähltes Passwort; `mustChange` = beim nächsten Anmelden ändern */
  set: (userId: number | string, password: string, mustChange: boolean) =>
    http.post<PasswordResult>(`/users/${enc(String(userId))}/password`, { mode: 'set', password, must_change: mustChange }),
  /** Konten der Schüler/innen einer Klasse (Verwaltung bzw. Klassenleitung) */
  classAccounts: async (classId: string, signal?: AbortSignal): Promise<ClassAccounts> => {
    const r = await http.get<ClassAccounts>(`/classes/${enc(classId)}/accounts`, undefined, { signal });
    return { ...r, students: (r.students ?? []).map((s) => ({ ...s, parents: s.parents ?? [] })) };
  },
};

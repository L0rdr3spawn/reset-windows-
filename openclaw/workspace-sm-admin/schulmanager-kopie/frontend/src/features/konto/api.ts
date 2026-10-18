/**
 * Endpunkte des Features „konto“ (§11.2). Die öffentlichen Aufrufe („Passwort vergessen“, Test-Postausgang) lösen
 * bei Fehlern keine globale Abmeldung aus (`skipAuthRedirect`).
 */
import { API_BASE, http } from '../../api/client';
import type {
  AdminContact,
  AdminContactInput,
  ContactKind,
  ContactStartResult,
  DevOutboxList,
  MyContact,
  ResetChannel,
  ResetOptions,
  ResetRequestResult,
  ResetVerifyResult,
  SendResetResult,
} from './types';

const PUBLIC = { skipAuthRedirect: true } as const;

export const contactApi = {
  mine: (signal?: AbortSignal) => http.get<MyContact>('/me/contact', undefined, { signal }),
  startEmail: (email: string, password: string) => http.post<ContactStartResult>('/me/contact/email', { email, password }),
  startPhone: (phone: string, password: string) => http.post<ContactStartResult>('/me/contact/phone', { phone, password }),
  verify: (kind: ContactKind, code: string) => http.post<MyContact>('/me/contact/verify', { kind, code }),
  confirmLink: (token: string) => http.post<MyContact>('/me/contact/confirm-link', { token }),
  remove: (kind: ContactKind, password: string) => http.post<MyContact>(`/me/contact/${kind}/remove`, { password }),
};

export const adminContactApi = {
  get: (userId: number, signal?: AbortSignal) => http.get<AdminContact>(`/users/${userId}/contact`, undefined, { signal }),
  put: (userId: number, body: AdminContactInput) => http.put<AdminContact>(`/users/${userId}/contact`, body),
  sendReset: (userId: number, channel: ResetChannel) => http.post<SendResetResult>(`/users/${userId}/send-reset`, { channel }),
};

export const resetApi = {
  options: (signal?: AbortSignal) => http.get<ResetOptions>('/auth/password-reset/options', undefined, { signal, ...PUBLIC }),
  request: (identifier: string, channel: ResetChannel | 'auto') =>
    http.post<ResetRequestResult>('/auth/password-reset/request', { identifier, channel }, PUBLIC),
  verifyCode: (identifier: string, code: string) =>
    http.post<ResetVerifyResult>('/auth/password-reset/verify', { identifier, code }, PUBLIC),
  verifyLink: (token: string) => http.post<ResetVerifyResult>('/auth/password-reset/verify', { token }, PUBLIC),
  confirm: (resetToken: string, newPassword: string) =>
    http.post<{ ok: boolean; username: string }>('/auth/password-reset/confirm', { reset_token: resetToken, new_password: newPassword }, PUBLIC),
};

export const devOutboxApi = {
  list: (signal?: AbortSignal) => http.get<DevOutboxList>('/dev-outbox', undefined, { signal, ...PUBLIC }),
  attachmentUrl: (id: number, index: number) => `${API_BASE}/dev-outbox/${id}/attachments/${index}`,
};

import { http, request } from '../../api/client';
import type { Person } from '../messages/types';
import type { ChatPollMeta, PollState } from '../lernen/api';
import type { MemberDevice, Sealed } from './crypto';

export type PostMode = 'all' | 'admins' | 'selected';

export interface ChatListItem {
  id: number;
  kind: 'direct' | 'group';
  title: string;
  members: number;
  last_activity_at: string;
  last: { id: number; sender_name: string; mine: boolean; system_text: string; deleted: boolean; created_at: string } | null;
  unread: number;
  muted: boolean;
  archived: boolean;
  can_post: boolean;
}

export interface ChatMemberInfo extends Person {
  admin: boolean;
  /** darf schreiben (false = nur lesen) */
  can_post: boolean;
}

export interface ChatDetail {
  id: number;
  kind: 'direct' | 'group';
  title: string;
  only_admins_post: boolean;
  post_mode: PostMode;
  admin: boolean;
  muted: boolean;
  archived: boolean;
  can_post: boolean;
  /** enthält aus dem Postfach übernommene (serverseitig verschlüsselte) Nachrichten */
  has_imported: boolean;
  members: ChatMemberInfo[];
  created_at: string;
}

export interface ChatMessage {
  id: number;
  sender_id: number | null;
  sender_name: string;
  mine: boolean;
  system_text: string;
  created_at: string;
  reply_to: number | null;
  deleted: boolean;
  nonce: string;
  ciphertext: string;
  /** aus dem Postfach übernommen: Text steht im Klartext in `legacy_text` (nicht Ende-zu-Ende) */
  imported?: boolean;
  legacy_text?: string;
  sender_key: string;
  key: { nonce: string; wrapped: string; wrapper_key?: string } | null;
  /** hat die angemeldete Person diese Nachricht gemeldet? */
  reported?: boolean;
  /** Umfrage: Einstellungen und Stimmen (Frage und Antworten stehen im verschluesselten Inhalt) */
  poll?: PollState;
}

export interface ClassOption {
  class_id: string;
  name: string;
  students: boolean;
  teachers: boolean;
  parents: boolean;
}

export interface ClassPick {
  class_id: string;
  students: boolean;
  teachers: boolean;
  parents: boolean;
}

export interface ChatReport {
  id: number;
  chat_id: number;
  message_id: number;
  status: string;
  reporter_name: string;
  sender_name: string;
  reason: string;
  content: string;
  images: { id: number; mime: string }[];
  sent_at: string | null;
  created_at: string;
  message_deleted: boolean;
}

export interface DeviceInfo {
  id: number;
  label: string;
  public_key: string;
  created_at: string;
  last_seen_at: string | null;
  kind: 'device' | 'archive';
  /** von einem anderen eigenen Gerät als bekannt bestätigt */
  acked: boolean;
}

export interface LinkInfo {
  id: number;
  device_id: number;
  status: 'pending' | 'approved' | 'cancelled' | 'expired';
  created_at: string;
  expires_at: string;
  label: string;
  public_key: string;
  /** nur bei der Anfrage selbst */
  code?: string;
  done?: number;
  total?: number;
}

export interface PendingKeys {
  items: { message_id: number; wrapper_key: string; nonce: string; wrapped: string }[];
  more: boolean;
  last_id: number;
}

export interface BackupInfo {
  enabled: boolean;
  archive_device_id?: number;
  public_key?: string;
  blob?: string;
  created_at?: string;
  updated_at?: string;
}

export interface WrappedKey {
  message_id: number;
  nonce: string;
  wrapped: string;
}

const c = (id: number) => `/chats/${id}`;

export const chatsApi = {
  list: (signal?: AbortSignal) => http.get<{ chats: ChatListItem[] }>('/chats', undefined, { signal }),
  unread: (signal?: AbortSignal) => http.get<{ unread: number }>('/chats/unread', undefined, { signal }),
  classOptions: (signal?: AbortSignal) => http.get<{ classes: ClassOption[] }>('/chats/class-options', undefined, { signal }),
  create: (body: { kind: 'direct' | 'group'; title?: string; user_ids: number[]; classes?: ClassPick[]; post_mode?: PostMode }) => http.post<ChatDetail>('/chats', body),
  detail: (id: number, signal?: AbortSignal) => http.get<ChatDetail>(c(id), undefined, { signal }),
  patch: (id: number, body: { title?: string; post_mode?: PostMode; muted?: boolean; archived?: boolean }) => http.patch<ChatDetail>(c(id), body),
  devices: (id: number) => http.get<{ devices: MemberDevice[] }>(`${c(id)}/devices`),
  messages: (id: number, deviceId: number, before?: number, signal?: AbortSignal) =>
    http.get<{ messages: ChatMessage[]; more: boolean; last_read_id: number }>(`${c(id)}/messages`, { device_id: deviceId, before }, { signal }),
  send: (id: number, body: Sealed & { device_id: number; reply_to?: number | null; attachment_ids?: string[]; poll?: ChatPollMeta }) => http.post<ChatMessage>(`${c(id)}/messages`, body),
  remove: (id: number, mid: number) => http.del<unknown>(`${c(id)}/messages/${mid}`),
  read: (id: number, upTo?: number) => http.post<unknown>(`${c(id)}/read`, { up_to: upTo }),
  report: (id: number, mid: number, body: { reason: string; content: string; images?: { data: string }[] }) => http.post<unknown>(`${c(id)}/messages/${mid}/report`, body),
  uploadImage: (id: number, blob: Uint8Array) => request<{ id: string; size: number }>('POST', `${c(id)}/attachments`, { raw: blob }),
  image: async (id: number, aid: string): Promise<Uint8Array> =>
    new Uint8Array(await (await request<Blob>('GET', `${c(id)}/attachments/${aid}`, { blob: true })).arrayBuffer()),
  addMembers: (id: number, body: { user_ids: number[]; classes?: ClassPick[] }) => http.post<ChatDetail>(`${c(id)}/members`, body),
  removeMember: (id: number, uid: number) => http.del<{ removed: number; chat_deleted: boolean }>(`${c(id)}/members/${uid}`),
  setAdmin: (id: number, uid: number, admin: boolean) => http.patch<ChatDetail>(`${c(id)}/members/${uid}`, { admin }),
  setCanPost: (id: number, uid: number, can_post: boolean) => http.patch<ChatDetail>(`${c(id)}/members/${uid}`, { can_post }),
  myDevices: (signal?: AbortSignal) => http.get<{ devices: DeviceInfo[] }>('/chats/devices', undefined, { signal }),
  revokeDevice: (id: number) => http.del<unknown>(`/chats/devices/${id}`),
  ackDevice: (id: number, byDeviceId: number) => http.post<DeviceInfo>(`/chats/devices/${id}/ack`, { by_device_id: byDeviceId }),
  resetDevices: (body: { public_key: string; label: string; keep_backup: boolean }) => http.post<DeviceInfo>('/chats/devices/reset', body),
  createLink: (deviceId: number, approveBy?: number) => http.post<LinkInfo>('/chat-links', { device_id: deviceId, approve_by_device_id: approveBy ?? null }),
  lookupLink: (code: string) => http.post<LinkInfo>('/chat-links/lookup', { code }),
  getLink: (id: number, signal?: AbortSignal) => http.get<LinkInfo>(`/chat-links/${id}`, undefined, { signal }),
  approveLink: (id: number, byDeviceId: number) => http.post<LinkInfo>(`/chat-links/${id}/approve`, { by_device_id: byDeviceId }),
  cancelLink: (id: number) => http.del<unknown>(`/chat-links/${id}`),
  pendingKeys: (source: number, target: number, after: number, signal?: AbortSignal) =>
    http.get<PendingKeys>('/chat-keys/pending', { source_device_id: source, target_device_id: target, after }, { signal }),
  addKeys: (target: number, wrapper: number, keys: WrappedKey[]) => http.post<{ added: number; skipped: number }>('/chat-keys', { target_device_id: target, wrapper_device_id: wrapper, keys }),
  backup: (signal?: AbortSignal) => http.get<BackupInfo>('/chat-keys/backup', undefined, { signal }),
  putBackup: (body: { public_key: string; blob: string }) => http.put<BackupInfo>('/chat-keys/backup', body),
  deleteBackup: () => http.del<BackupInfo>('/chat-keys/backup'),
  reports: (signal?: AbortSignal) => http.get<{ reports: ChatReport[] }>('/chat-reports', undefined, { signal }),
  resolve: (id: number, action: 'dismiss' | 'remove') => http.post<unknown>(`/chat-reports/${id}`, { action }),
};

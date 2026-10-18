/**
 * Endpunkte des Postfachs (§9.5). Anhänge werden vorher über `uploadFile` (`src/api/files.ts`) mit dem Zweck
 * `message` hochgeladen und beim Senden per `attachment_ids` angehängt.
 */
import { http } from '../../api/client';
import type {
  BlockEntry,
  ConversationDetail,
  ConversationList,
  Draft,
  DraftInput,
  DraftSummary,
  Folder,
  MailAccount,
  MailProvider,
  MessageSettings,
  Person,
  RecipientInput,
  RecipientsResponse,
  ClassRoster,
  ReplyMode,
  ReplyResponse,
  ReportDetail,
  ReportList,
  ReportStatus,
  ResolveInput,
  RetentionResult,
  Suspension,
  UnreadCounts,
} from './types';

/** Zweck der Dateiablage für Nachrichtenanhänge (Backend `PURPOSE`). */
export const ATTACHMENT_PURPOSE = 'message';

export interface ListQuery {
  folder?: Folder;
  q?: string;
  unread?: boolean;
  offset?: number;
  limit?: number;
}

export interface SendInput {
  recipients: RecipientInput[];
  subject: string;
  body: string;
  attachment_ids: string[];
  allow_replies: ReplyMode;
  draft_id?: number | null;
  mail_account_id?: number | null;
}

export const mailApi = {
  providers: (signal?: AbortSignal) => http.get<{ providers: MailProvider[]; redirect_uri: string; custom_allowed?: boolean }>('/mail/providers', undefined, { signal }),
  accounts: (signal?: AbortSignal) => http.get<{ accounts: MailAccount[]; max: number }>('/mail/accounts', undefined, { signal }),
  add: (body: {
    provider: string;
    email: string;
    password: string;
    display_name?: string;
    username?: string;
    imap_host?: string;
    imap_port?: number;
    smtp_host?: string;
    smtp_port?: number;
    smtp_security?: 'ssl' | 'starttls';
  }) => http.post<MailAccount>('/mail/accounts', body),
  patch: (id: number, body: Partial<{ display_name: string; sync_enabled: boolean; is_default: boolean; password: string }>) =>
    http.patch<MailAccount>(`/mail/accounts/${id}`, body),
  remove: (id: number) => http.del<{ deleted: number }>(`/mail/accounts/${id}`),
  sync: (id: number) => http.post<{ imported: number; account: MailAccount }>(`/mail/accounts/${id}/sync`, {}),
  oauthStart: (provider: 'google' | 'microsoft', loginHint = '') => http.get<{ url: string }>(`/mail/oauth/${provider}/start`, { login_hint: loginHint || undefined }),
};

const conv = (id: number) => `/messages/conversations/${id}`;

export const messagesApi = {
  unread: (signal?: AbortSignal) => http.get<UnreadCounts>('/messages/unread', undefined, { signal }),
  readAll: () => http.post<{ updated: number; counts: UnreadCounts }>('/messages/read-all', {}),
  list: (q: ListQuery = {}, signal?: AbortSignal) =>
    http.get<ConversationList>(
      '/messages/conversations',
      { folder: q.folder ?? 'inbox', q: q.q?.trim() || undefined, unread: q.unread ? 1 : undefined, offset: q.offset || undefined, limit: q.limit },
      { signal },
    ),
  get: (id: number, before?: number | null, signal?: AbortSignal) =>
    http.get<ConversationDetail>(conv(id), { before: before ?? undefined }, { signal }),
  create: (body: SendInput) => http.post<ConversationDetail>('/messages/conversations', body),
  reply: (id: number, body: { body: string; attachment_ids: string[]; draft_id?: number | null }) =>
    http.post<ReplyResponse>(`${conv(id)}/messages`, body),
  patch: (id: number, body: { archived?: boolean; muted?: boolean }) =>
    http.patch<{ id: number; archived: boolean; muted: boolean; counts: UnreadCounts }>(conv(id), body),
  read: (id: number, upTo?: number | null) =>
    http.post<{ id: number; last_read_id: number; counts: UnreadCounts }>(`${conv(id)}/read`, upTo ? { up_to: upTo } : {}),
  markUnread: (id: number) => http.post<{ id: number; last_read_id: number; counts: UnreadCounts }>(`${conv(id)}/unread`, {}),
  remove: (id: number) => http.del<{ deleted: number; purged: boolean; counts: UnreadCounts }>(conv(id)),
  report: (id: number, messageId: number, body: { category: string; reason: string }) =>
    http.post<{ id: number; status: ReportStatus; duplicate: boolean }>(`${conv(id)}/messages/${messageId}/report`, body),

  recipients: (q: string, signal?: AbortSignal) =>
    http.get<RecipientsResponse>('/messages/recipients', { q: q.trim() || undefined }, { signal }),
  classRoster: (classId: string, signal?: AbortSignal) =>
    http.get<ClassRoster>(`/messages/recipients/class/${encodeURIComponent(classId)}`, undefined, { signal }),
  lookup: (q: { user_id?: number; teacher_id?: string; student_id?: string; parents_of?: string }, signal?: AbortSignal) =>
    http.get<{ people: Person[] }>('/messages/recipients/lookup', q, { signal }),

  blocks: (signal?: AbortSignal) => http.get<BlockEntry[]>('/messages/blocks', undefined, { signal }),
  block: (userId: number) => http.post<{ blocked: number }>('/messages/blocks', { user_id: userId }),
  unblock: (userId: number) => http.del<{ unblocked: number }>(`/messages/blocks/${userId}`),

  settings: (signal?: AbortSignal) => http.get<MessageSettings>('/messages/settings', undefined, { signal }),
  saveSettings: (body: { email_notify?: boolean }) => http.put<MessageSettings>('/messages/settings', body),

  drafts: (signal?: AbortSignal) => http.get<DraftSummary[]>('/messages/drafts', undefined, { signal }),
  draft: (id: number, signal?: AbortSignal) => http.get<Draft>(`/messages/drafts/${id}`, undefined, { signal }),
  createDraft: (body: DraftInput) => http.post<Draft>('/messages/drafts', body),
  updateDraft: (id: number, body: DraftInput) => http.put<Draft>(`/messages/drafts/${id}`, body),
  deleteDraft: (id: number) => http.del<{ deleted: number }>(`/messages/drafts/${id}`),

  reports: (status: ReportStatus | 'alle' = 'offen', signal?: AbortSignal, limit?: number) =>
    http.get<ReportList>('/messages/moderation/reports', { status, limit }, { signal }),
  /** Entschlüsselte Ansicht – jeder Aufruf wird im Audit-Protokoll vermerkt. */
  reportDetail: (id: number, context = 0, signal?: AbortSignal) =>
    http.get<ReportDetail>(`/messages/moderation/reports/${id}`, { context: context || undefined }, { signal }),
  resolve: (id: number, body: ResolveInput) =>
    http.post<{ id: number; status: ReportStatus; actions: string[]; resolved: number[]; suspended_until: string | null }>(
      `/messages/moderation/reports/${id}/resolve`,
      body,
    ),
  suspensions: (signal?: AbortSignal) => http.get<Suspension[]>('/messages/moderation/suspensions', undefined, { signal }),
  suspend: (userId: number, body: { days: number; reason: string }) =>
    http.post<{ user_id: number; suspended_until: string }>(`/messages/moderation/users/${userId}/suspend`, body),
  unsuspend: (userId: number) => http.del<{ user_id: number; suspended_until: null }>(`/messages/moderation/users/${userId}/suspend`),
  retention: () => http.post<RetentionResult>('/messages/moderation/retention', {}),
};

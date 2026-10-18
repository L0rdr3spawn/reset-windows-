/**
 * Typen des Postfachs (Backend `schulmanager/server/routes/features_messages.py`, ARCHITECTURE.md §9.5).
 * Zeitstempel sind ISO-8601 in UTC mit „Z“.
 */
import type { Role } from '../../api/types';
import type { StoredFileInfo } from '../../api/files';

export type ConversationKind = 'direct' | 'group' | 'broadcast' | 'email';
export type RecipientRole = 'to' | 'cc' | 'bcc';
export type ReplyMode = 'all' | 'sender' | 'none';
export type Folder = 'inbox' | 'sent' | 'archive' | 'all';
export type ReportStatus = 'offen' | 'erledigt' | 'abgelehnt';

/** Person aus Sicht des Betrachters (datensparsam: Name, Rolle, Klasse bzw. Kürzel). */
export interface Person {
  type: 'user';
  /** `null` = gelöschtes Konto */
  id: number | null;
  name: string;
  role: Role | null;
  role_label: string;
  info: string;
  /** erreichbar (aktiv, mit Postfach) – nur in Unterhaltungen */
  active?: boolean;
  /** das eigene Konto */
  me?: boolean;
  /** externe E-Mail-Adresse (kein Konto der Schule) */
  external?: boolean;
  email?: string;
  /** An/CC/BCC in dieser Unterhaltung */
  recipient_role?: RecipientRole | 'from';
}

/** Freie E-Mail-Adresse als Empfänger (Schulkonto mit dieser Adresse oder extern). */
export interface EmailRecipient {
  type: 'email';
  email: string;
  name?: string;
}

/** Gruppe fürs Adressbuch (nur mit `messages.broadcast`). */
export interface GroupOption {
  type: 'group';
  kind: string;
  ref: string;
  /** `kind:ref` */
  key: string;
  label: string;
  category: string;
  category_label: string;
  /** erreichbare Personen der Gruppe (ohne mich) */
  count?: number;
}

export type Recipient = Person | GroupOption | EmailRecipient;

/** Empfänger wie vom Backend erwartet. */
export type RecipientInput = (
  | { type: 'user'; id: number }
  | { type: 'group'; kind: string; ref: string }
  | { type: 'email'; email: string; name?: string }
) & { role?: RecipientRole };

export interface AudienceEntry {
  kind: string;
  ref: string;
  label: string;
}

export interface UnreadCounts {
  /** Unterhaltungen mit Ungelesenem (ohne stumme/archivierte) */
  unread: number;
  /** deren ungelesene Nachrichten */
  messages: number;
  muted: number;
  archived: number;
}

export interface MessagePreview {
  id: number;
  sender_id: number | null;
  own: boolean;
  preview: string;
  integrity_ok: boolean;
  created_at: string;
  attachments: number;
  removed: boolean;
  sender_name?: string;
}

export interface SearchMatch {
  in: 'subject' | 'people' | 'message';
  snippet: string;
  message_id?: number;
}

export interface ConversationSummary {
  id: number;
  /** Verlauf wurde nach „Chats & Gruppen“ übernommen (Chat-ID) – hier nicht mehr bearbeitbar */
  chat_id?: number | null;
  kind: ConversationKind;
  kind_label: string;
  subject: string;
  integrity_ok: boolean;
  title: string;
  allow_replies: ReplyMode;
  created_at: string;
  last_message_at: string;
  last_message: MessagePreview | null;
  unread: number;
  archived: boolean;
  muted: boolean;
  is_creator: boolean;
  creator: Person;
  /** andere Teilnehmende (nicht bei Rundschreiben) */
  participants: Person[];
  participant_count: number | null;
  audience: AudienceEntry[];
  recipient_count: number;
  parent_id: number | null;
  match?: SearchMatch;
  /** externe E-Mail-Beteiligte (BCC nur für die absendende Person) */
  external?: Person[];
  my_role?: RecipientRole | 'from' | null;
}

export interface ReplyState {
  /** `all` = in der Unterhaltung, `private` = eigene Unterhaltung mit der absendenden Person, `null` = keine */
  mode: 'all' | 'private' | null;
  can_reply: boolean;
  code: string | null;
  reason: string | null;
  hint: string | null;
  private_conversation_id: number | null;
}

export interface ConversationDetailInfo extends ConversationSummary {
  reply: ReplyState;
  can_block: boolean;
  blocked: boolean;
  other_user_id: number | null;
  /** nur für die absendende Person eines Rundschreibens */
  read_count?: number;
  recipients?: Person[];
  recipients_more?: number;
}

export interface Message {
  id: number;
  conversation_id: number;
  sender: Person;
  own: boolean;
  body: string;
  integrity_ok: boolean;
  created_at: string;
  attachments: StoredFileInfo[];
  removed: boolean;
  blocked_sender: boolean;
  unread: boolean;
  can_report: boolean;
  reported: boolean;
  /** eigene Nachricht: Versand an externe E-Mail-Adressen */
  delivery?: { status: 'sent' | 'failed' | 'no_account' | 'none'; error?: string; to?: string[]; account?: string; at?: string } | null;
  /** per E-Mail empfangen bzw. verschickt */
  email?: boolean;
}

export interface MailAccount {
  id: number;
  provider: string;
  provider_label: string;
  email: string;
  display_name: string;
  auth: 'password' | 'oauth2';
  imap_host: string;
  imap_port: number;
  smtp_host: string;
  smtp_port: number;
  smtp_security: 'ssl' | 'starttls';
  sync_enabled: boolean;
  is_default: boolean;
  last_sync_at: string | null;
  last_error: string | null;
}

export interface MailProvider {
  id: string;
  label: string;
  imap_host: string;
  imap_port: number;
  smtp_host: string;
  smtp_port: number;
  smtp_security: 'ssl' | 'starttls';
  password_ok: boolean;
  oauth: boolean;
  hint: string;
  domains: string[];
}

export interface ConversationDetail {
  conversation: ConversationDetailInfo;
  messages: Message[];
  has_more: boolean;
  last_read_id: number;
}

export interface ConversationList {
  items: ConversationSummary[];
  total: number;
  offset: number;
  limit: number;
  folder: Folder;
  query: string;
  search: { scanned_messages: number; truncated: boolean } | null;
  counts: UnreadCounts;
}

export interface ReplyResponse {
  conversation_id: number;
  private: boolean;
  message: Message;
}

export interface RecipientsResponse {
  people: Person[];
  groups: GroupOption[];
  suggestions: boolean;
  query: string;
  /** Klassen, die zum Suchtext passen (→ Klassenansicht) */
  classes?: { id: string; name: string }[];
  can_broadcast: boolean;
}

/** Elternteil in der Klassenansicht: alle Kinder (auch in anderen Klassen) */
export type RosterParent = Person & { children?: { id: string; name: string; class: string; same_class: boolean }[] };

export interface ClassRoster {
  class: { id: string; name: string };
  /** Kinder und Eltern sichtbar (Personal mit Sicht auf die Klasse) */
  full: boolean;
  leads: Person[];
  teachers: Person[];
  students: { student_id: string; name: string; account: Person | null; parents: RosterParent[] }[];
  /** erlaubte Rundschreiben an diese Klasse */
  groups: GroupOption[];
}

export interface BlockEntry {
  user: Person;
  user_id: number;
  created_at: string;
}

export interface MessageSettings {
  email_notify: boolean;
  email_available: boolean;
  has_email: boolean;
  suspended_until: string | null;
  suspension_reason: string;
  students_to_students: boolean;
  retention_days: number;
  can_broadcast: boolean;
  broadcast_scope: string | null;
  can_moderate: boolean;
  limits: { subject: number; body: number; attachments: number; individuals: number; groups: number };
  report_categories: { key: string; label: string }[];
  reply_modes: { key: ReplyMode; label: string }[];
  purpose: string;
}

export interface DraftSummary {
  id: number;
  conversation_id: number | null;
  subject: string;
  preview: string;
  recipient_labels: string[];
  updated_at: string;
  created_at: string;
  integrity_ok: boolean;
}

export interface Draft extends DraftSummary {
  recipients: RecipientInput[];
  body: string;
  allow_replies: ReplyMode;
  attachments: StoredFileInfo[];
}

export interface DraftInput {
  conversation_id?: number | null;
  recipients?: RecipientInput[];
  subject?: string;
  body?: string;
  allow_replies?: ReplyMode;
  attachment_ids?: string[];
}

export interface Report {
  id: number;
  status: ReportStatus;
  status_label: string;
  category: string;
  category_label: string;
  reason: string;
  resolution: string;
  integrity_ok: boolean;
  created_at: string;
  handled_at: string | null;
  actions: string[];
  reporter: Person;
  sender: Person;
  sender_id: number | null;
  handled_by: Person | null;
  message_id: number;
  conversation_id: number | null;
  conversation_kind: ConversationKind | null;
  conversation_kind_label: string;
  message_created_at: string | null;
  message_removed: boolean;
  reports_on_message: number;
  /** Meldung über eine eigene Nachricht der/des Moderierenden */
  own: boolean;
}

export interface ReportMessage {
  id: number;
  body: string;
  integrity_ok: boolean;
  created_at: string;
  sender: Person;
  reported: boolean;
  removed: boolean;
  attachments: StoredFileInfo[];
}

export interface ReportDetail extends Report {
  messages: ReportMessage[];
  subject: string;
  conversation: { id: number | null; kind: ConversationKind | null; kind_label: string; recipient_count: number; audience: AudienceEntry[] };
  other_reports: Report[];
  sender_reports: number;
  sender_suspended_until: string | null;
  can_resolve: boolean;
}

export interface ReportList {
  items: Report[];
  counts: Record<ReportStatus, number>;
}

export interface ResolveInput {
  status: 'erledigt' | 'abgelehnt';
  resolution: string;
  remove_message: boolean;
  suspend_days?: number | null;
}

export interface Suspension {
  user_id: number;
  user: Person;
  suspended_until: string;
  suspended_at: string | null;
  suspended_by: Person | null;
  reason: string;
  integrity_ok: boolean;
}

export interface RetentionResult {
  messages_expired: number;
  conversations_removed: number;
  attachments_removed: number;
  drafts_expired: number;
  reports_removed: number;
  suspensions_ended: number;
}

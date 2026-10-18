/** Typen des Features „konto“ (§11.2): Kontakt & Wiederherstellung, „Passwort vergessen“, Test-Postausgang. */

export type ResetChannel = 'email' | 'sms';
export type ContactKind = 'email' | 'phone';

export interface ChannelAvailability {
  email: boolean;
  sms: boolean;
}

export interface PendingContact {
  /** neue Adresse (voll) bzw. Nummer (maskiert) */
  target: string;
  expires_at: string;
}

/** GET /me/contact */
export interface MyContact {
  email: string | null;
  email_verified: boolean;
  email_verified_at: string | null;
  /** maskiert, z. B. „+49 171 •••••67“ */
  phone: string | null;
  phone_verified: boolean;
  phone_verified_at: string | null;
  has_password: boolean;
  password_login: boolean;
  reset_channels: ResetChannel[];
  channels: ChannelAvailability;
  pending: { email: PendingContact | null; phone: PendingContact | null };
  code_minutes: number;
  dev_outbox: boolean;
}

export interface ContactStartResult extends MyContact {
  ok: boolean;
  sent_to: string;
  expires_at: string;
}

/** GET/PUT /users/{id}/contact */
export interface AdminContact {
  user_id: number;
  username: string;
  display_name: string;
  active: boolean;
  email: string | null;
  email_verified: boolean;
  email_verified_at: string | null;
  /** E.164, z. B. „+491711234567“ */
  phone: string | null;
  phone_display: string | null;
  phone_masked: string | null;
  phone_verified: boolean;
  phone_verified_at: string | null;
  has_password: boolean;
  password_login: boolean;
  reset_channels: ResetChannel[];
  channels: ChannelAvailability;
  can_send_reset: ChannelAvailability;
  code_minutes: number;
  dev_outbox: boolean;
}

export interface AdminContactInput {
  email?: string | null;
  email_verified?: boolean;
  phone?: string | null;
  phone_verified?: boolean;
}

export interface SendResetResult {
  ok: boolean;
  channel: ResetChannel;
  sent_to: string;
  expires_at: string;
  dev_outbox: boolean;
}

/** GET /auth/capabilities (öffentlich): was der Server kann + wer „Passwort vergessen“ selbst nutzen darf */
export interface ResetOptions {
  email: boolean;
  sms: boolean;
  channels: ChannelAvailability;
  /** je Rolle: laut Anmelde-Richtlinie darf „Passwort vergessen“ selbst genutzt werden */
  self_reset: Record<string, boolean>;
  code_minutes: number;
  dev_outbox: boolean;
}

export interface ResetRequestResult {
  ok: boolean;
  message: string;
  code_minutes: number;
  dev_outbox: boolean;
}

export interface ResetVerifyResult {
  reset_token: string;
  username: string;
  display_name: string;
  min_length: number;
  expires_at: string;
}

export interface DevOutboxAttachment {
  index: number;
  filename: string;
  content_type: string;
  size: number;
}

export interface DevOutboxItem {
  id: number;
  channel: 'email' | 'sms';
  to: string;
  subject: string;
  text: string;
  purpose: string;
  created_at: string | null;
  attachments: DevOutboxAttachment[];
}

export interface DevOutboxList {
  enabled: boolean;
  hours: number;
  items: DevOutboxItem[];
}

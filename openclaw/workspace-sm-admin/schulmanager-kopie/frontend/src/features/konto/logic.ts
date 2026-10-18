/**
 * Reine Logik des Features „konto“ (§11.2) – ohne React, mit vitest getestet (logic.test.ts).
 * Die verbindliche Prüfung macht immer das Backend; hier nur Vorschau, Formatprüfung und Anzeige.
 */
import type { ResetChannel, ResetOptions } from './types';

export const CODE_LENGTH = 6;

/** Einfache Formatprüfung einer E-Mail-Adresse (wie im Backend: eine Adresse, keine Sonderzeichen für Kopfzeilen). */
export function isValidEmail(value: string): boolean {
  const v = value.trim();
  return v.length <= 254 && /^[^@\s<>"',;]+@[^@\s<>"',;]+\.[^@\s<>"',;.]{2,}$/.test(v);
}

/**
 * Telefonnummer → E.164 (`0171 1234567` → `+491711234567`) oder `null` – Vorschau für die Eingabe, gleiche Regeln
 * wie `server/sms.py::normalize_phone`.
 */
export function normalizePhone(raw: string, defaultCountry = '49'): string | null {
  let text = raw.trim();
  if (!text || text.length > 40) return null;
  text = text.replace(/\(\s*0\s*\)/g, '').replace(/[\s\-/.()   ]/g, '');
  let digits: string;
  if (text.startsWith('+')) digits = text.slice(1);
  else if (text.startsWith('00')) digits = text.slice(2);
  else if (text.startsWith('0')) digits = defaultCountry + text.slice(1);
  else return null;
  if (!/^\d+$/.test(digits) || digits.startsWith('0')) return null;
  if (digits.startsWith('49') && digits[2] === '0') digits = '49' + digits.slice(3);
  if (digits.length < 8 || digits.length > 15) return null;
  if (digits.startsWith('49') && digits.length < 9) return null;
  return `+${digits}`;
}

/** Lesbare Form einer E.164-Nummer: `+49 171 1234567`. */
export function formatPhone(e164: string | null | undefined): string {
  if (!e164 || !e164.startsWith('+')) return e164 ?? '';
  const d = e164.slice(1);
  if (d.startsWith('49')) return `+49 ${d.slice(2, 5)} ${d.slice(5)}`.trim();
  return `+${d.slice(0, 2)} ${d.slice(2)}`;
}

/** Maskierte Anzeige wie im Backend: `+49 171 •••••67`. */
export function maskPhone(e164: string | null | undefined): string {
  if (!e164 || !e164.startsWith('+') || e164.length < 6) return '•••';
  const d = e164.slice(1);
  const rest = d.slice(2);
  const head = rest.slice(0, 3);
  const tail = rest.slice(-2);
  return `+${d.slice(0, 2)} ${head} ${'•'.repeat(Math.max(1, rest.length - head.length - tail.length))}${tail}`;
}

/** `maria@schule.de` → `m•••@schule.de` */
export function maskEmail(address: string | null | undefined): string {
  const [local = '', domain] = (address ?? '').split('@');
  if (!domain) return '•••';
  return `${local.slice(0, 1)}•••@${domain}`;
}

/** Nur Ziffern, höchstens 6 (Eingabe mit Leerzeichen/Bindestrich, eingefügt aus E-Mail/SMS). */
export function cleanCode(value: string): string {
  return value.replace(/\D/g, '').slice(0, CODE_LENGTH);
}

export function isCompleteCode(value: string): boolean {
  return cleanCode(value).length === CODE_LENGTH;
}

export type IdentifierKind = 'email' | 'phone' | 'username' | 'empty';

/** Was hat jemand bei „Passwort vergessen“ eingegeben? (nur für Hinweise) */
export function identifierKind(value: string): IdentifierKind {
  const v = value.trim();
  if (!v) return 'empty';
  if (v.includes('@')) return 'email';
  if (/^\+?[\d\s\-/.()]{6,}$/.test(v) && /\d{3}/.test(v.replace(/\D/g, ''))) return 'phone';
  return 'username';
}

export const CHANNEL_LABELS: Record<ResetChannel, string> = { email: 'E-Mail', sms: 'SMS' };

/** „E-Mail und SMS“ / „E-Mail“ / „—“ */
export function channelList(channels: readonly ResetChannel[]): string {
  const labels = channels.map((c) => CHANNEL_LABELS[c] ?? c);
  if (labels.length === 0) return '';
  if (labels.length === 1) return labels[0] ?? '';
  return `${labels.slice(0, -1).join(', ')} und ${labels[labels.length - 1]}`;
}

/** Hinweise zum neuen Passwort (Server prüft verbindlich: Mindestlänge je Rolle, leicht zu erraten, Benutzername). */
export function passwordIssues(password: string, minLength: number, username = ''): string[] {
  const out: string[] = [];
  if (password.length < minLength) out.push(`mindestens ${minLength} Zeichen`);
  if (password && new Set(password).size < 4) out.push('nicht so gleichförmig');
  if (username.length >= 3 && password.toLowerCase().includes(username.toLowerCase())) out.push('ohne den Benutzernamen');
  return out;
}

/** Sechsstellige Codes in einem Nachrichtentext (Test-Postausgang: Kopierknopf). */
export function extractCodes(text: string): string[] {
  const found = text.match(/(?<!\d)\d{6}(?!\d)/g) ?? [];
  return Array.from(new Set(found));
}

/** Adressen in einem Nachrichtentext. */
export function extractLinks(text: string): string[] {
  const found = text.match(/https?:\/\/[^\s<>"']+/g) ?? [];
  return Array.from(new Set(found.map((u) => u.replace(/[.,;:)]+$/, ''))));
}

const APP_LINK_PATHS = ['/passwort-zuruecksetzen', '/passwort-vergessen', '/profil', '/login'];

/**
 * Link aus einer Test-Nachricht als App-interner Pfad (die Basisadresse `SM_BASE_URL` passt in der Vorschau oft nicht
 * zur tatsächlichen Adresse). Nur bekannte App-Seiten, sonst `null` (kein Open Redirect).
 */
export function internalAppPath(url: string): string | null {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return null;
  }
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return null;
  if (!APP_LINK_PATHS.includes(parsed.pathname)) return null;
  return parsed.pathname + parsed.search;
}

/** Restzeit bis `expiresAt` in ganzen Minuten (mindestens 0). */
export function minutesLeft(expiresAt: string | null | undefined, now: Date = new Date()): number {
  if (!expiresAt) return 0;
  const t = Date.parse(expiresAt);
  if (Number.isNaN(t)) return 0;
  return Math.max(0, Math.ceil((t - now.getTime()) / 60000));
}

/** Größe einer Datei für die Anzeige. */
export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1).replace('.', ',')} KB`;
  return `${(n / 1024 / 1024).toFixed(1).replace('.', ',')} MB`;
}

/** Kann der Server überhaupt E-Mail oder SMS zustellen? */
export function anyChannel(caps: Pick<ResetOptions, 'channels'> | null | undefined): boolean {
  return !!caps && (caps.channels.email || caps.channels.sms);
}

/** „Passwort vergessen“ ist nutzbar: Versand möglich und mindestens eine Rolle darf es selbst anstoßen. */
export function resetUsable(caps: ResetOptions | null | undefined): boolean {
  return anyChannel(caps) && Object.values(caps?.self_reset ?? {}).some(Boolean);
}

/** Satz zu den verfügbaren Wegen, z. B. „E-Mail-Adresse“ / „E-Mail-Adresse oder Handynummer“. */
export function contactWays(caps: Pick<ResetOptions, 'channels'> | null | undefined): string {
  const ways = [caps?.channels.email ? 'E-Mail-Adresse' : '', caps?.channels.sms ? 'Handynummer' : ''].filter(Boolean);
  return ways.join(' oder ');
}

/** Hinweis für Gruppen, die „Passwort vergessen“ nicht selbst nutzen dürfen (Standard: Schüler/innen). */
export function managedByStaffNote(caps: Pick<ResetOptions, 'self_reset'> | null | undefined): string | null {
  const sr = caps?.self_reset;
  if (!sr) return null;
  const off = [sr.schueler === false ? 'Schüler/innen' : '', sr.eltern === false ? 'Eltern' : ''].filter(Boolean);
  if (!off.length) return null;
  return `${off.join(' und ')}: Bitte wenden Sie sich an ${sr.schueler === false && off.length === 1 ? 'Ihre Klassenleitung' : 'die Klassenleitung bzw. das Sekretariat'}.`;
}

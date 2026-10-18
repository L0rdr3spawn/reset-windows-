/**
 * Schlüsselverwaltung der Chats: Verlauf auf ein neues Gerät übertragen, Wiederherstellung mit Passwort,
 * neue Schlüssel erzeugen und Schlüsselwechsel bei Gesprächspartnern bemerken.
 *
 * Grundprinzip: Jede Nachricht hat einen Inhaltsschlüssel K, den der Absender je Empfängergerät mit `nacl.box`
 * verpackt. Ein *eingerichtetes* Gerät kann K öffnen und für ein weiteres eigenes Gerät neu verpacken – der Server
 * sieht nur verpackte Schlüssel, nie K und nie Inhalte.
 *
 * Wiederherstellung (optional): Das Konto bekommt ein Archiv-Schlüsselpaar. Der öffentliche Teil ist ein „Gerät“
 * (`kind: archive`), für das alle Teilnehmer künftig mitverpacken; der private Teil liegt nur als Blob auf dem
 * Server, verschlüsselt mit einem aus Code/Passwort abgeleiteten Schlüssel (PBKDF2-SHA-256, viele Runden).
 * Ohne Code/Passwort gibt es keine Wiederherstellung – auch nicht durch die Schule.
 */
import nacl from 'tweetnacl';
import { http } from '../../api/client';
import { chatsApi, type WrappedKey } from './api';
import { createDevice, deviceLabel, fingerprint, fromB64, rewrapKey, saveDevice, toB64, type LocalDevice, type MemberDevice } from './crypto';

const enc = new TextEncoder();

// ------------------------------------------------------------------------------------------------ Übertragen
export interface TransferOptions {
  sourceId: number;
  targetId: number;
  targetPublicKey: string;
  /** Schlüssel, mit dem die vorhandenen verpackten Schlüssel geöffnet werden (Quellgerät bzw. Archiv) */
  openSecret: Uint8Array;
  /** Gerät, das neu verpackt (Quellgerät bzw. das neue Gerät selbst bei der Wiederherstellung) */
  wrapper: { id: number; secret: Uint8Array };
  signal?: AbortSignal;
  onProgress?: (processed: number) => void;
}

export interface TransferResult {
  added: number;
  /** Schlüssel, die sich nicht öffnen ließen (z. B. Gerät ohne passenden Schlüssel) */
  unreadable: number;
}

/**
 * Verpackt in Paketen alle Nachrichtenschlüssel neu, die das Quellgerät hat, das Ziel aber nicht. Fortsetzbar: der
 * Server liefert immer nur, was dem Ziel noch fehlt. Abbrechen über `signal`.
 */
export async function transferKeys(o: TransferOptions): Promise<TransferResult> {
  let after = 0;
  let added = 0;
  let unreadable = 0;
  let processed = 0;
  for (;;) {
    if (o.signal?.aborted) throw new DOMException('Abgebrochen', 'AbortError');
    const page = await chatsApi.pendingKeys(o.sourceId, o.targetId, after, o.signal);
    const keys: WrappedKey[] = [];
    for (const item of page.items) {
      const w = rewrapKey(item, o.openSecret, o.targetPublicKey, o.wrapper.secret);
      if (w) keys.push({ message_id: item.message_id, ...w });
      else unreadable += 1;
    }
    if (keys.length) added += (await chatsApi.addKeys(o.targetId, o.wrapper.id, keys)).added;
    processed += page.items.length;
    o.onProgress?.(processed);
    after = page.last_id;
    if (!page.more) return { added, unreadable };
  }
}

/** Altes Gerät → neues Gerät (nach Freigabe). */
export function sendHistory(source: LocalDevice, targetId: number, targetPublicKey: string, signal?: AbortSignal, onProgress?: (n: number) => void): Promise<TransferResult> {
  const secret = fromB64(source.secretKey);
  return transferKeys({ sourceId: source.deviceId, targetId, targetPublicKey, openSecret: secret, wrapper: { id: source.deviceId, secret }, signal, onProgress });
}

/** Kurzer Code, den das neue Gerät anzeigt (8 Zeichen, ohne verwechselbare Buchstaben). */
export function formatLinkCode(code: string): string {
  const c = code.replace(/[^A-Za-z0-9]/g, '').toUpperCase();
  return c.length > 4 ? `${c.slice(0, 4)}-${c.slice(4)}` : c;
}

/** Inhalt des QR-Codes: Link, der auf dem eingerichteten Gerät das Freigabe-Fenster mit dem Code öffnet. */
export function linkUrl(code: string, origin = typeof window !== 'undefined' ? window.location.origin : ''): string {
  return `${origin}/nachrichten?link=${encodeURIComponent(code.replace(/[^A-Za-z0-9]/g, '').toUpperCase())}`;
}

/** Aus einem eingegebenen/gescannten Wert (Code oder Link) den Code ziehen. */
export function parseLinkCode(input: string): string {
  const m = /[?&]link=([A-Za-z0-9]+)/.exec(input);
  return (m ? m[1] : input).replace(/[^A-Za-z0-9]/g, '').toUpperCase();
}

// ------------------------------------------------------------------------------------------------ Neue Schlüssel
/**
 * „Dieses Gerät neu einrichten“: neues Schlüsselpaar; auf Wunsch wandert der bisherige Verlauf auf den neuen
 * Schlüssel, danach wird der alte widerrufen. Bei einem Fehler bleibt alles beim Alten.
 */
export async function rekeyThisDevice(old: LocalDevice, keepHistory: boolean, onProgress?: (n: number) => void): Promise<LocalDevice> {
  const fresh = await createDeviceUnsaved(old.userId);
  try {
    if (keepHistory) {
      await chatsApi.createLink(fresh.deviceId, old.deviceId);
      await sendHistory(old, fresh.deviceId, fresh.publicKey, undefined, onProgress);
    }
  } catch (e) {
    await chatsApi.revokeDevice(fresh.deviceId).catch(() => undefined);
    throw e;
  }
  if (!saveDevice(fresh)) {
    await chatsApi.revokeDevice(fresh.deviceId).catch(() => undefined);
    throw new Error('Der Browser erlaubt keine lokale Speicherung.');
  }
  await chatsApi.revokeDevice(old.deviceId);
  return fresh;
}

async function createDeviceUnsaved(userId: number | string): Promise<LocalDevice> {
  const kp = nacl.box.keyPair();
  const publicKey = toB64(kp.publicKey);
  const created = await http.post<{ id: number }>('/chats/devices', { public_key: publicKey, label: deviceLabel() });
  return { userId, deviceId: created.id, publicKey, secretKey: toB64(kp.secretKey) };
}

/** „Alle Geräte zurücksetzen“: alle Geräteschlüssel des Kontos widerrufen, dieses Gerät bekommt einen neuen. */
export async function resetAllDevices(userId: number | string, keepBackup: boolean): Promise<LocalDevice> {
  return createDevice(userId, (publicKey, label) => chatsApi.resetDevices({ public_key: publicKey, label, keep_backup: keepBackup }));
}

// ------------------------------------------------------------------------------------------------ Backup
/** Runden der Schlüsselableitung (PBKDF2-SHA-256; OWASP empfiehlt ≥ 600 000, hier bewusst mehr). */
export const BACKUP_ITERATIONS = 1_000_000;
const CODE_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
export const MIN_PASSWORD = 12;

/** Zufälliger Wiederherstellungscode: 25 Zeichen aus 32 (125 Bit), in Fünfergruppen. */
export function generateRecoveryCode(): string {
  const bytes = nacl.randomBytes(25);
  let out = '';
  for (let i = 0; i < 25; i++) out += CODE_CHARS[bytes[i] & 31] + (i % 5 === 4 && i < 24 ? '-' : '');
  return out;
}

/** Eingaben vereinheitlichen: ein Wiederherstellungscode darf klein, mit Leerzeichen oder ohne Striche getippt werden. */
export function canonicalSecret(input: string): string {
  const compact = input.replace(/[\s-]/g, '').toUpperCase();
  if (compact.length === 25 && [...compact].every((ch) => CODE_CHARS.includes(ch))) return compact.replace(/(.{5})(?=.)/g, '$1-');
  return input.normalize('NFKC');
}

async function deriveKey(secret: string, salt: Uint8Array, iterations: number): Promise<Uint8Array> {
  const base = await crypto.subtle.importKey('raw', enc.encode(secret), 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits({ name: 'PBKDF2', hash: 'SHA-256', salt: salt as BufferSource, iterations }, base, 256);
  return new Uint8Array(bits);
}

interface BlobV1 {
  v: 1;
  kdf: 'pbkdf2-sha256';
  iter: number;
  salt: string;
  nonce: string;
  box: string;
}

/** Verschlüsselt den privaten Archivschlüssel mit einem aus Code/Passwort abgeleiteten Schlüssel (für den Server undurchsichtig). */
export async function sealBackup(archiveSecret: Uint8Array, secret: string, iterations = BACKUP_ITERATIONS): Promise<string> {
  const salt = nacl.randomBytes(16);
  const nonce = nacl.randomBytes(nacl.secretbox.nonceLength);
  const key = await deriveKey(canonicalSecret(secret), salt, iterations);
  const blob: BlobV1 = { v: 1, kdf: 'pbkdf2-sha256', iter: iterations, salt: toB64(salt), nonce: toB64(nonce), box: toB64(nacl.secretbox(archiveSecret, nonce, key)) };
  return JSON.stringify(blob);
}

/** Öffnet das Backup-Blob; `null` bei falschem Code/Passwort oder beschädigtem Blob. */
export async function openBackup(blob: string, secret: string): Promise<Uint8Array | null> {
  try {
    const b = JSON.parse(blob) as BlobV1;
    if (b.v !== 1 || b.kdf !== 'pbkdf2-sha256' || !Number.isInteger(b.iter) || b.iter < 100_000 || b.iter > 5_000_000) return null;
    const key = await deriveKey(canonicalSecret(secret), fromB64(b.salt), b.iter);
    return nacl.secretbox.open(fromB64(b.box), fromB64(b.nonce), key);
  } catch {
    return null;
  }
}

/** Passwortregel für selbst gewählte Passwörter (der generierte Code ist immer stark genug). */
export function passwordProblem(secret: string): string | null {
  const s = canonicalSecret(secret);
  if (/^[A-Z2-9]{5}(-[A-Z2-9]{5}){4}$/.test(s)) return null;
  if (s.length < MIN_PASSWORD) return `Mindestens ${MIN_PASSWORD} Zeichen – besser ein ganzer Satz oder der erzeugte Code.`;
  if (new Set(s).size < 5) return 'Zu einfach – bitte mehr verschiedene Zeichen.';
  return null;
}

/** Backup einrichten: Archivschlüssel erzeugen, verschlüsselt ablegen und den bisherigen Verlauf dieses Geräts hineinpacken. */
export async function enableBackup(device: LocalDevice, secret: string, onProgress?: (n: number) => void): Promise<TransferResult> {
  const archive = nacl.box.keyPair();
  const blob = await sealBackup(archive.secretKey, secret);
  const info = await chatsApi.putBackup({ public_key: toB64(archive.publicKey), blob });
  const own = fromB64(device.secretKey);
  return transferKeys({ sourceId: device.deviceId, targetId: info.archive_device_id as number, targetPublicKey: toB64(archive.publicKey), openSecret: own, wrapper: { id: device.deviceId, secret: own }, onProgress });
}

/** Passwort/Code ändern: altes Passwort öffnet den Archivschlüssel, neues verschlüsselt ihn neu. */
export async function changeBackupSecret(oldSecret: string, newSecret: string): Promise<boolean> {
  const info = await chatsApi.backup();
  if (!info.enabled || !info.blob || !info.public_key) return false;
  const archive = await openBackup(info.blob, oldSecret);
  if (!archive || toB64(nacl.box.keyPair.fromSecretKey(archive).publicKey) !== info.public_key) return false;
  await chatsApi.putBackup({ public_key: info.public_key, blob: await sealBackup(archive, newSecret) });
  return true;
}

/** Verlauf auf diesem Gerät aus dem Backup holen. `null` = falsches Passwort/falscher Code. */
export async function restoreFromBackup(device: LocalDevice, secret: string, signal?: AbortSignal, onProgress?: (n: number) => void): Promise<TransferResult | null> {
  const info = await chatsApi.backup(signal);
  if (!info.enabled || !info.blob || !info.public_key || !info.archive_device_id) throw new Error('Für dieses Konto gibt es kein Wiederherstellungs-Backup.');
  const archive = await openBackup(info.blob, secret);
  if (!archive || toB64(nacl.box.keyPair.fromSecretKey(archive).publicKey) !== info.public_key) return null;
  const own = fromB64(device.secretKey);
  return transferKeys({ sourceId: info.archive_device_id, targetId: device.deviceId, targetPublicKey: device.publicKey, openSecret: archive, wrapper: { id: device.deviceId, secret: own }, signal, onProgress });
}

// ------------------------------------------------------------------------------------------------ Schlüsselwechsel
export type SeenKeys = Record<string, string[]>;

export interface KeyChange {
  userId: number;
  /** changed = Schlüssel ersetzt (Gerät neu eingerichtet/zurückgesetzt); added = zusätzliches Gerät */
  kind: 'changed' | 'added';
  fingerprints: string[];
}

/**
 * Vergleicht die aktuellen Gerätschlüssel der anderen Mitglieder mit den bisher gesehenen (wie die Sicherheitsnummer
 * bei Signal). `next` enthält den neuen Stand; erst nach dem Bestätigen speichern, damit die Warnung stehen bleibt.
 * Beim ersten Kontakt gibt es keine Warnung.
 */
export function detectKeyChanges(seen: SeenKeys, devices: MemberDevice[], myUserId: number | string): { changes: KeyChange[]; next: SeenKeys } {
  const current = new Map<number, string[]>();
  for (const d of devices) {
    if (d.kind === 'archive' || String(d.user_id) === String(myUserId)) continue;
    current.set(d.user_id, [...(current.get(d.user_id) ?? []), fingerprint(d.public_key)]);
  }
  const next: SeenKeys = { ...seen };
  const changes: KeyChange[] = [];
  for (const [uid, now] of current) {
    const before = seen[String(uid)];
    if (!before) {
      next[String(uid)] = now;
      continue;
    }
    const added = now.filter((f) => !before.includes(f));
    const removed = before.filter((f) => !now.includes(f));
    if (added.length && removed.length) changes.push({ userId: uid, kind: 'changed', fingerprints: added });
    else if (added.length) changes.push({ userId: uid, kind: 'added', fingerprints: added });
    next[String(uid)] = now;
  }
  return { changes, next };
}

const seenKey = (userId: number | string) => `sm-chat-seen-${userId}`;

export function loadSeen(userId: number | string): SeenKeys {
  try {
    const raw = localStorage.getItem(seenKey(userId));
    const v = raw ? (JSON.parse(raw) as SeenKeys) : {};
    return v && typeof v === 'object' ? v : {};
  } catch {
    return {};
  }
}

export function saveSeen(userId: number | string, seen: SeenKeys): void {
  try {
    localStorage.setItem(seenKey(userId), JSON.stringify(seen));
  } catch {
    /* egal */
  }
}

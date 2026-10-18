/**
 * Ende-zu-Ende-Verschlüsselung der Chats (tweetnacl, dieselben Verfahren wie libsodium):
 *
 * * Jedes Gerät (Browser) hat ein eigenes Schlüsselpaar (X25519). Der private Schlüssel bleibt im Browser
 *   (localStorage dieses Kontos); der Server kennt nur den öffentlichen.
 * * Je Nachricht ein zufälliger Schlüssel K: Inhalt mit `secretbox` (XSalsa20-Poly1305) verschlüsselt, K für jedes
 *   Mitgliedsgerät mit `box` (X25519 + XSalsa20-Poly1305) verpackt – das authentisiert zugleich das Absendergerät.
 * * Neue Mitglieder können ältere Nachrichten nicht lesen (wie bei Signal). Ein neues eigenes Gerät bekommt den
 *   Verlauf nur, wenn ein eingerichtetes Gerät die Nachrichtenschlüssel neu für es verpackt (`rewrapKey`, siehe
 *   `keys.ts`: Verknüpfen und Passwort-Backup). Beim Entpacken zählt dann der Schlüssel des Verpackers.
 */
import nacl from 'tweetnacl';
import { http } from '../../api/client';

const enc = new TextEncoder();
const dec = new TextDecoder();

export function toB64(bytes: Uint8Array): string {
  let s = '';
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(s);
}

export function fromB64(text: string): Uint8Array {
  const bin = atob(text);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

export interface LocalDevice {
  userId: number | string;
  deviceId: number;
  publicKey: string;
  secretKey: string;
}

export interface MemberDevice {
  device_id: number;
  user_id: number;
  public_key: string;
  /** `archive` = Wiederherstellungsschlüssel des Kontos (kein Gerät) */
  kind?: 'device' | 'archive';
}

/** Bild/GIF in einer Nachricht: das Blob liegt verschlüsselt auf dem Server, Schlüssel und Typ nur hier (im Chiffrat). */
export interface ImageRef {
  /** ID des hochgeladenen Blobs (`/chats/{id}/attachments/{id}`) */
  id: string;
  /** Base64-Schlüssel des Blobs (secretbox) */
  key: string;
  nonce: string;
  mime: string;
  name: string;
  size: number;
}

/** Umfrage in einer Nachricht: die Frage steht in `text`, die Antworten hier - beides Ende-zu-Ende-verschluesselt. */
export interface PollPayload {
  options: string[];
}

export interface Payload {
  v: 1;
  text: string;
  images?: ImageRef[];
  poll?: PollPayload;
}

export const IMAGE_MIMES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp'] as const;
/** Größte erlaubte Bilddatei (Klartext) – das Backend lehnt Größeres ab. */
export const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
export const MAX_IMAGES = 4;

/** Bildtyp aus den ersten Bytes (nicht dem Dateinamen/Browser-Typ vertrauen); `null` = kein erlaubtes Rasterbild. */
export function sniffImageType(b: Uint8Array): (typeof IMAGE_MIMES)[number] | null {
  const at = (i: number, ...v: number[]) => v.every((x, k) => b[i + k] === x);
  if (at(0, 0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a)) return 'image/png';
  if (at(0, 0xff, 0xd8, 0xff)) return 'image/jpeg';
  if (at(0, 0x47, 0x49, 0x46, 0x38) && (b[4] === 0x37 || b[4] === 0x39) && b[5] === 0x61) return 'image/gif';
  if (at(0, 0x52, 0x49, 0x46, 0x46) && at(8, 0x57, 0x45, 0x42, 0x50)) return 'image/webp';
  return null;
}

/** Verschlüsselt ein Bild mit eigenem Zufallsschlüssel (der Server bekommt nur das Chiffrat). */
export function encryptImage(bytes: Uint8Array): { blob: Uint8Array; key: string; nonce: string } {
  const key = nacl.randomBytes(nacl.secretbox.keyLength);
  const nonce = nacl.randomBytes(nacl.secretbox.nonceLength);
  return { blob: nacl.secretbox(bytes, nonce, key), key: toB64(key), nonce: toB64(nonce) };
}

export function decryptImage(blob: Uint8Array, ref: Pick<ImageRef, 'key' | 'nonce'>): Uint8Array | null {
  try {
    return nacl.secretbox.open(blob, fromB64(ref.nonce), fromB64(ref.key));
  } catch {
    return null;
  }
}

function cleanPoll(raw: unknown): PollPayload | undefined {
  const opts = (raw as Partial<PollPayload> | null)?.options;
  if (!Array.isArray(opts) || opts.length < 2 || opts.length > 20 || !opts.every((o) => typeof o === 'string')) return undefined;
  return { options: opts.map((o: string) => o.slice(0, 200)) };
}

function cleanImages(raw: unknown): ImageRef[] {
  if (!Array.isArray(raw)) return [];
  const out: ImageRef[] = [];
  for (const r of raw.slice(0, MAX_IMAGES)) {
    const x = r as Partial<ImageRef> | null;
    if (x && typeof x.id === 'string' && typeof x.key === 'string' && typeof x.nonce === 'string' && typeof x.mime === 'string' && (IMAGE_MIMES as readonly string[]).includes(x.mime)) {
      out.push({ id: x.id, key: x.key, nonce: x.nonce, mime: x.mime, name: typeof x.name === 'string' ? x.name.slice(0, 120) : '', size: typeof x.size === 'number' ? x.size : 0 });
    }
  }
  return out;
}

const storeKey = (userId: number | string) => `sm-chat-device-${userId}`;

export function loadDevice(userId: number | string): LocalDevice | null {
  try {
    const raw = localStorage.getItem(storeKey(userId));
    const d = raw ? (JSON.parse(raw) as LocalDevice) : null;
    return d && d.deviceId && d.secretKey && String(d.userId) === String(userId) ? d : null;
  } catch {
    return null;
  }
}

export function saveDevice(d: LocalDevice): boolean {
  try {
    localStorage.setItem(storeKey(d.userId), JSON.stringify(d));
    return true;
  } catch {
    return false;
  }
}

export function forgetDevice(userId: number | string): void {
  try {
    localStorage.removeItem(storeKey(userId));
  } catch {
    /* egal */
  }
}

export function deviceLabel(ua = typeof navigator !== 'undefined' ? navigator.userAgent : ''): string {
  const browser = /Edg\//.test(ua) ? 'Edge' : /Firefox\//.test(ua) ? 'Firefox' : /Chrome\//.test(ua) ? 'Chrome' : /Safari\//.test(ua) ? 'Safari' : 'Browser';
  const os = /iPhone|iPad/.test(ua) ? 'iOS' : /Android/.test(ua) ? 'Android' : /Windows/.test(ua) ? 'Windows' : /Mac OS/.test(ua) ? 'macOS' : /Linux/.test(ua) ? 'Linux' : '';
  return os ? `${browser} · ${os}` : browser;
}

/** Gerät dieses Browsers für das Konto: vorhandenes prüfen, sonst neues Schlüsselpaar anlegen und anmelden. */
const inflight = new Map<string, Promise<LocalDevice>>();

export function ensureDevice(userId: number | string): Promise<LocalDevice> {
  // gleichzeitige Aufrufe (z. B. React StrictMode) teilen sich eine Anmeldung – sonst entstünden verwaiste Geräte
  const key = String(userId);
  let p = inflight.get(key);
  if (!p) {
    p = ensureDeviceNow(userId).finally(() => inflight.delete(key));
    inflight.set(key, p);
  }
  return p;
}

async function ensureDeviceNow(userId: number | string): Promise<LocalDevice> {
  const known = loadDevice(userId);
  if (known) {
    const { devices } = await http.get<{ devices: { id: number; public_key: string }[] }>('/chats/devices');
    if (devices.some((d) => d.id === known.deviceId && d.public_key === known.publicKey)) return known;
  }
  return createDevice(userId);
}

/** Neues Schlüsselpaar erzeugen, beim Server anmelden und lokal speichern (ersetzt ein vorhandenes lokales Gerät). */
export async function createDevice(userId: number | string, register?: (publicKey: string, label: string) => Promise<{ id: number }>): Promise<LocalDevice> {
  const kp = nacl.box.keyPair();
  const publicKey = toB64(kp.publicKey);
  const label = deviceLabel();
  const created = await (register ? register(publicKey, label) : http.post<{ id: number }>('/chats/devices', { public_key: publicKey, label }));
  const device: LocalDevice = { userId, deviceId: created.id, publicKey, secretKey: toB64(kp.secretKey) };
  if (!saveDevice(device)) throw new Error('Der Browser erlaubt keine lokale Speicherung – Chats sind hier nicht möglich.');
  return device;
}

export interface Sealed {
  nonce: string;
  ciphertext: string;
  keys: { device_id: number; nonce: string; wrapped: string }[];
}

export function seal(payload: Payload, devices: MemberDevice[], me: LocalDevice): Sealed {
  const key = nacl.randomBytes(nacl.secretbox.keyLength);
  const nonce = nacl.randomBytes(nacl.secretbox.nonceLength);
  const ciphertext = nacl.secretbox(enc.encode(JSON.stringify(payload)), nonce, key);
  const secret = fromB64(me.secretKey);
  const keys = devices.map((d) => {
    const n = nacl.randomBytes(nacl.box.nonceLength);
    return { device_id: d.device_id, nonce: toB64(n), wrapped: toB64(nacl.box(key, n, fromB64(d.public_key), secret)) };
  });
  return { nonce: toB64(nonce), ciphertext: toB64(ciphertext), keys };
}

/** Entschlüsselt eine Nachricht; `null`, wenn sie nicht für dieses Gerät bestimmt oder manipuliert ist. */
export function open(
  msg: { nonce: string; ciphertext: string; sender_key: string; key: { nonce: string; wrapped: string; wrapper_key?: string } | null },
  me: LocalDevice,
): Payload | null {
  if (!msg.key || !msg.ciphertext || !msg.sender_key) return null;
  try {
    const key = nacl.box.open(fromB64(msg.key.wrapped), fromB64(msg.key.nonce), fromB64(msg.key.wrapper_key || msg.sender_key), fromB64(me.secretKey));
    if (!key) return null;
    const plain = nacl.secretbox.open(fromB64(msg.ciphertext), fromB64(msg.nonce), key);
    if (!plain) return null;
    const data = JSON.parse(dec.decode(plain)) as Payload;
    if (!data || typeof data.text !== 'string') return null;
    const images = cleanImages(data.images);
    const poll = cleanPoll(data.poll);
    const out: Payload = { v: 1, text: data.text };
    if (images.length) out.images = images;
    if (poll) out.poll = poll;
    return out;
  } catch {
    return null;
  }
}

/** Packt einen vorhandenen Nachrichtenschlüssel für ein anderes eigenes Gerät (oder das Archiv) neu ein; `null`, wenn
 *  er sich mit `secretKey` nicht öffnen lässt. Inhalt der Nachricht wird dabei nie entschlüsselt. */
export function rewrapKey(
  item: { wrapper_key: string; nonce: string; wrapped: string },
  openSecret: Uint8Array,
  targetPublicKey: string,
  wrapSecret: Uint8Array = openSecret,
): { nonce: string; wrapped: string } | null {
  try {
    if (!item.wrapper_key) return null;
    const key = nacl.box.open(fromB64(item.wrapped), fromB64(item.nonce), fromB64(item.wrapper_key), openSecret);
    if (!key) return null;
    const n = nacl.randomBytes(nacl.box.nonceLength);
    return { nonce: toB64(n), wrapped: toB64(nacl.box(key, n, fromB64(targetPublicKey), wrapSecret)) };
  } catch {
    return null;
  }
}

/** Kurzer Fingerabdruck eines öffentlichen Schlüssels (zum Vergleichen, z. B. „4F2A 91C0 …“). */
export function fingerprint(publicKey: string): string {
  const h = nacl.hash(fromB64(publicKey)).subarray(0, 10);
  return Array.from(h, (b) => b.toString(16).padStart(2, '0'))
    .join('')
    .toUpperCase()
    .replace(/(.{4})/g, '$1 ')
    .trim();
}

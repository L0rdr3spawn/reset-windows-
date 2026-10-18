/**
 * Schlanker, typisierter HTTP-Client für die REST-API (/api/v1).
 *
 * - Cookie-Authentifizierung (credentials: same-origin)
 * - CSRF-Schutz: Header `X-CSRF-Token` bei zustandsändernden Requests
 * - Einheitliche Fehler: ApiError mit status, verständlicher deutscher Meldung, Konflikten (409), Fehlern je Feld
 *   (422, `api/errors.ts`) und Fehlernummer bei Unerwartetem (Request-ID des Servers)
 * - 401 (außer Login) → globales Ereignis, die App zeigt die Anmeldung
 */
import {
  isValidationList,
  looksTechnical,
  shortErrorId,
  translateValidation,
  unexpectedText,
  type FieldIssue,
  type FieldLabels,
} from './errors';
import { resetSession } from '../lib/session';

export const API_BASE = '/api/v1';

let csrfToken: string | null = null;

export function setCsrfToken(token: string | null | undefined): void {
  csrfToken = token ?? null;
}

export function getCsrfToken(): string | null {
  return csrfToken;
}

type UnauthorizedListener = () => void;
const unauthorizedListeners = new Set<UnauthorizedListener>();

const passwordListeners = new Set<UnauthorizedListener>();

/** Server verlangt Passwortwechsel (403 password_change_required). */
export function onPasswordChangeRequired(fn: UnauthorizedListener): () => void {
  passwordListeners.add(fn);
  return () => passwordListeners.delete(fn);
}

const linkListeners = new Set<UnauthorizedListener>();

/** Anmelde-Richtlinie verlangt verbundene Konten (403 link_required, §11.5). */
export function onLinkRequired(fn: UnauthorizedListener): () => void {
  linkListeners.add(fn);
  return () => linkListeners.delete(fn);
}

const licenseListeners = new Set<UnauthorizedListener>();

/** Lizenz der Schule ist gesperrt (403 license_locked): Konto neu laden, der Rahmen zeigt die Sperrseite. */
export function onLicenseLocked(fn: UnauthorizedListener): () => void {
  licenseListeners.add(fn);
  return () => licenseListeners.delete(fn);
}

const totpSetupListeners = new Set<UnauthorizedListener>();

/** Server verlangt Einrichtung der Zwei-Faktor-Anmeldung (403 totp_setup_required). */
export function onTotpSetupRequired(fn: UnauthorizedListener): () => void {
  totpSetupListeners.add(fn);
  return () => totpSetupListeners.delete(fn);
}

/** Wird aufgerufen, wenn die Sitzung abgelaufen ist (401). */
export function onUnauthorized(fn: UnauthorizedListener): () => void {
  unauthorizedListeners.add(fn);
  return () => unauthorizedListeners.delete(fn);
}

export interface ApiErrorExtra {
  /** Request-ID des Servers (Kopfzeile `X-Request-ID` bzw. `request_id` im Fehlertext) */
  requestId?: string | null;
  /** Unerwarteter Fehler (Serverfehler, unbekannter Code, englischer Text) – Meldung enthält die Fehlernummer */
  unexpected?: boolean;
  errorId?: string | null;
}

export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;
  readonly conflicts: string[];
  readonly requestId: string | null;
  /** Unerwarteter Fehler: „Das hat nicht geklappt …“ mit Fehlernummer (nie Servertexte auf Englisch) */
  readonly unexpected: boolean;
  /** Kurze Fehlernummer für den Support (erste 8 Zeichen der Request-ID) */
  readonly errorId: string | null;
  /** Validierungsfehler je Feldcode (z. B. `date_from` → „Bitte ein Startdatum angeben.“) */
  readonly fields: Record<string, string>;
  /** Übersetzte Validierungsfehler (für Listen im Toast) */
  readonly issues: FieldIssue[];

  constructor(status: number, message: string, detail: unknown, conflicts: string[] = [], extra: ApiErrorExtra = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
    this.conflicts = conflicts;
    this.requestId = extra.requestId ?? null;
    this.unexpected = extra.unexpected ?? false;
    this.errorId = extra.errorId ?? null;
    const v = isValidationList(detail) ? translateValidation(detail) : null;
    this.fields = v?.fields ?? {};
    this.issues = v?.issues ?? [];
  }

  get isTotpRequired(): boolean {
    return this.status === 401 && detailCode(this.detail) === 'totp_required';
  }

  get isForbidden(): boolean {
    return this.status === 403;
  }

  get isConflict(): boolean {
    return this.status === 409;
  }
}

function detailCode(detail: unknown): string | null {
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object' && 'code' in detail) {
    const c = (detail as { code: unknown }).code;
    return typeof c === 'string' ? c : null;
  }
  return null;
}

export const KNOWN_DETAILS: Readonly<Record<string, string>> = {
  not_authenticated: 'Bitte erneut anmelden.',
  invalid_token: 'Die Anmeldung ist nicht mehr gültig. Bitte erneut anmelden.',
  totp_required: 'Bitte den 6-stelligen Code aus der Authenticator-App eingeben.',
  invalid_totp: 'Der Bestätigungscode ist ungültig.',
  invalid_credentials: 'Benutzername oder Passwort ist falsch.',
  initial_password_expired: 'Das Startpasswort ist abgelaufen. Bitte bei der Schule ein neues Startpasswort anfordern.',
  password_change_required: 'Bitte zuerst das Passwort ändern.',
  totp_setup_required: 'Für Ihre Rolle ist die Zwei-Faktor-Anmeldung Pflicht – bitte zuerst einrichten.',
  csrf_failed: 'Sicherheitsprüfung fehlgeschlagen – bitte Seite neu laden.',
  locked: 'Das Konto ist vorübergehend gesperrt. Bitte später erneut versuchen.',
  too_many_attempts: 'Zu viele Versuche. Bitte kurz warten.',
  not_found: 'Nicht gefunden.',
  forbidden: 'Dafür fehlt die Berechtigung.',
  account_disabled: 'Dieses Konto ist deaktiviert. Bitte wenden Sie sich an die Schulverwaltung.',
  method_not_allowed: 'Für dieses Konto ist die Anmeldung mit Passwort nicht vorgesehen. Bitte melden Sie sich über einen der Anmeldedienste unten an.',
  link_required: 'Bitte verbinden Sie zuerst die vorgeschriebenen Konten.',
  license_locked: 'Die Lizenz dieser Schule ist nicht mehr gültig. Bitte wenden Sie sich an die Schulleitung bzw. Administration.',
};

/** Extrahiert Konfliktliste aus `{"detail":{"conflicts":[...]}}` */
export function extractConflicts(detail: unknown): string[] {
  if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
    for (const key of ['conflicts', 'references', 'errors']) {
      const c = (detail as Record<string, unknown>)[key];
      if (Array.isArray(c)) return c.map((x) => (typeof x === 'string' ? x : JSON.stringify(x)));
    }
  }
  return [];
}

const STATUS_TEXT: Readonly<Record<number, string>> = {
  400: 'Die Anfrage war ungültig.',
  401: 'Bitte erneut anmelden.',
  403: 'Dafür fehlt die Berechtigung.',
  404: 'Nicht gefunden.',
  409: 'Konflikt – die Änderung ist so nicht möglich.',
  413: 'Die Datei ist zu groß.',
  422: 'Bitte die Eingabe prüfen.',
  429: 'Zu viele Anfragen – bitte kurz warten.',
};

/** Status, deren allgemeiner Text auch einen unbekannten Servertext ersetzen darf („Not Found“ → „Nicht gefunden.“) */
const GENERIC_OK: ReadonlySet<number> = new Set([401, 403, 404, 413, 429]);

/** Ein Servertext, der angezeigt werden darf (bekannter Code → deutscher Text; Codes/Englisch → `null`). */
function knownText(text: string): string | null {
  const known = KNOWN_DETAILS[text];
  if (known) return known;
  return looksTechnical(text) ? null : text;
}

interface DetailText {
  text: string | null;
  issues: FieldIssue[];
  fields: Record<string, string>;
}

function detailText(detail: unknown, labels?: FieldLabels): DetailText {
  const none = { issues: [], fields: {} };
  if (typeof detail === 'string') return { text: knownText(detail), ...none };
  if (isValidationList(detail)) {
    // Pydantic-Validierungsfehler: [{type, loc, msg, ctx}] → deutsch, Beschriftung statt Feldcode
    const v = translateValidation(detail, labels);
    return { text: v.message, issues: v.issues, fields: v.fields };
  }
  if (Array.isArray(detail)) {
    const parts = detail.map((d) => (typeof d === 'string' ? knownText(d) : null)).filter((x): x is string => !!x);
    return { text: parts.length ? parts.join(' ') : null, ...none };
  }
  if (detail && typeof detail === 'object') {
    const msg = (detail as { message?: unknown; msg?: unknown }).message ?? (detail as { msg?: unknown }).msg;
    const conflicts = extractConflicts(detail);
    if (conflicts.length && typeof msg !== 'string') return { text: `Konflikt: ${conflicts.join('; ')}`, ...none };
    if (typeof msg === 'string') return { text: knownText(msg), ...none };
    const code = detailCode(detail);
    if (code) return { text: KNOWN_DETAILS[code] ?? null, ...none };
  }
  return { text: null, ...none };
}

interface ErrorInfo {
  message: string;
  unexpected: boolean;
  requestId: string | null;
  errorId: string | null;
  fields: Record<string, string>;
  issues: FieldIssue[];
}

/** Meldung, Feldfehler und Einordnung „unerwartet“ für eine Fehlerantwort. */
export function errorInfo(status: number, detail: unknown, requestId: string | null = null, labels?: FieldLabels): ErrorInfo {
  const d = detailText(detail, labels);
  const rid = requestId || null;
  const base = { requestId: rid, fields: d.fields, issues: d.issues };
  if (status === 0) return { ...base, message: 'Server nicht erreichbar. Bitte Verbindung prüfen.', unexpected: false, errorId: null };
  // Serverfehler zeigen nur einen ausdrücklich deutschen Text (z. B. „… ist gerade nicht erreichbar“), sonst Fehlernummer
  const serverError = status >= 500 && (!d.text || d.text === 'Interner Serverfehler');
  // Code oder englischer Text vom Server, den die Oberfläche nicht kennt → unerwartet (außer bei klaren Status)
  const technical = detail != null && detail !== '' && !d.text && !GENERIC_OK.has(status);
  const fallback = STATUS_TEXT[status];
  if (!serverError && !technical && (d.text || fallback)) {
    return { ...base, message: d.text ?? (fallback as string), unexpected: false, errorId: null };
  }
  const errorId = rid ? shortErrorId(rid) : null;
  return { ...base, message: unexpectedText(errorId), unexpected: true, errorId };
}

/**
 * Wandelt das FastAPI-`detail` in einen lesbaren deutschen Text um (nie Codes, Pfade oder englische Servertexte).
 * `labels` ergänzt die allgemeine Zuordnung Feldcode → Beschriftung (`api/errors.ts`).
 */
export function describeDetail(status: number, detail: unknown, labels?: FieldLabels): string {
  return errorInfo(status, detail, null, labels).message;
}

/**
 * Fehler eines Formulars: Meldung und Texte je Feld, mit formulareigenen Beschriftungen neu übersetzt.
 * Für `FormErrors`/`Field name=…` (components/ui.tsx) und Toasts.
 */
export function formErrors(e: unknown, labels?: FieldLabels): { message: string; fields: Record<string, string>; issues: FieldIssue[] } {
  if (e instanceof ApiError) {
    if (e.unexpected || !labels) return { message: e.message, fields: e.fields, issues: e.issues };
    const info = errorInfo(e.status, e.detail, e.requestId, labels);
    return { message: info.message, fields: info.fields, issues: info.issues };
  }
  return { message: errorMessage(e), fields: {}, issues: [] };
}

export type QueryValue = string | number | boolean | null | undefined;

export function buildQuery(params?: Record<string, QueryValue>): string {
  if (!params) return '';
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue;
    sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : '';
}

export interface RequestOptions {
  query?: Record<string, QueryValue>;
  body?: unknown;
  /** FormData für Datei-Uploads (multipart) */
  form?: FormData;
  /** roher Binärkörper (`application/octet-stream`), z. B. im Browser verschlüsselte Blobs */
  raw?: Uint8Array;
  signal?: AbortSignal;
  /** 401 nicht global als „abgemeldet“ behandeln (Login, /auth/me) */
  skipAuthRedirect?: boolean;
  /** Antwort als Blob statt JSON */
  blob?: boolean;
}

const UNSAFE = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

/**
 * Request-ID je Anfrage (32 Hex-Zeichen). Wird als `X-Request-ID` mitgeschickt; der Server übernimmt sie (Log,
 * Antwort-Kopfzeile). Nennt eine Fehlerantwort keine eigene ID (z. B. 500 aus der äußersten Fehlerbehandlung,
 * `request_id: null`), ist sie trotzdem die Fehlernummer (B-13 Kriterium 4). `getRandomValues` gibt es auch ohne HTTPS.
 */
export function newRequestId(): string {
  const c = typeof globalThis !== 'undefined' ? globalThis.crypto : undefined;
  const bytes = new Uint8Array(16);
  if (c && typeof c.getRandomValues === 'function') c.getRandomValues(bytes);
  else for (let i = 0; i < bytes.length; i++) bytes[i] = Math.floor(Math.random() * 256);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

export async function request<T>(method: string, path: string, opts: RequestOptions = {}): Promise<T> {
  const sentRid = newRequestId();
  // feste Kopfzeile: Kontoliste/-wechsel ohne Sitzung (Seite „Abgemeldet“) ersetzt damit das Sitzungs-CSRF-Token
  const headers: Record<string, string> = { Accept: 'application/json', 'X-Request-ID': sentRid, 'X-Requested-With': 'schulmanager' };
  let body: BodyInit | undefined;
  if (opts.form) {
    body = opts.form;
  } else if (opts.raw) {
    headers['Content-Type'] = 'application/octet-stream';
    body = opts.raw as BodyInit;
  } else if (opts.body !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(opts.body);
  }
  if (UNSAFE.has(method) && csrfToken) headers['X-CSRF-Token'] = csrfToken;

  const url = `${API_BASE}${path}${buildQuery(opts.query)}`;
  let res: Response;
  try {
    res = await fetch(url, {
      method,
      headers,
      body,
      credentials: 'same-origin',
      signal: opts.signal,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') throw e;
    throw new ApiError(0, 'Server nicht erreichbar. Bitte Verbindung prüfen.', null);
  }

  if (!res.ok) {
    let detail: unknown = null;
    let bodyRid: unknown = null;
    try {
      const data: unknown = await res.json();
      detail = data && typeof data === 'object' && 'detail' in data ? (data as { detail: unknown }).detail : data;
      bodyRid = data && typeof data === 'object' ? (data as { request_id?: unknown }).request_id : null;
    } catch {
      detail = null;
    }
    const rid = res.headers.get('X-Request-ID') || (typeof bodyRid === 'string' && bodyRid ? bodyRid : null) || sentRid;
    const info = errorInfo(res.status, detail, rid);
    const err = new ApiError(res.status, info.message, detail, extractConflicts(detail), info);
    if (info.unexpected && typeof console !== 'undefined') {
      console.warn(`[api] ${method} ${path}: ${res.status} (Fehlernummer ${info.errorId ?? '–'}, Request-ID ${rid ?? '–'})`);
    }
    if (res.status === 401 && !opts.skipAuthRedirect && !err.isTotpRequired) {
      // Sitzung abgelaufen: kontobezogene Zwischenspeicher sofort leeren (U-01), dann die App benachrichtigen
      resetSession();
      unauthorizedListeners.forEach((fn) => fn());
    }
    if (res.status === 403 && detailCode(detail) === 'password_change_required') {
      passwordListeners.forEach((fn) => fn());
    }
    if (res.status === 403 && detailCode(detail) === 'link_required') {
      linkListeners.forEach((fn) => fn());
    }
    if (res.status === 403 && detailCode(detail) === 'license_locked') {
      licenseListeners.forEach((fn) => fn());
    }
    if (res.status === 403 && detailCode(detail) === 'totp_setup_required') {
      totpSetupListeners.forEach((fn) => fn());
    }
    throw err;
  }

  // neues CSRF-Token (falls Server rotiert)
  const rotated = res.headers.get('X-CSRF-Token');
  if (rotated) csrfToken = rotated;

  if (opts.blob) return (await res.blob()) as T;
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  if (!text) return undefined as T;
  try {
    return JSON.parse(text) as T;
  } catch {
    return text as T;
  }
}

export const http = {
  get: <T>(path: string, query?: Record<string, QueryValue>, opts: Omit<RequestOptions, 'query'> = {}) =>
    request<T>('GET', path, { ...opts, query }),
  post: <T>(path: string, body?: unknown, opts: RequestOptions = {}) => request<T>('POST', path, { ...opts, body }),
  put: <T>(path: string, body?: unknown, opts: RequestOptions = {}) => request<T>('PUT', path, { ...opts, body }),
  patch: <T>(path: string, body?: unknown, opts: RequestOptions = {}) => request<T>('PATCH', path, { ...opts, body }),
  del: <T>(path: string, opts: RequestOptions = {}) => request<T>('DELETE', path, opts),
  upload: <T>(path: string, form: FormData, query?: Record<string, QueryValue>) =>
    request<T>('POST', path, { form, query }),
};

/** Akzeptiert sowohl Arrays als auch `{items:[...]}` / `{data:[...]}` (robust gegenüber Backend-Varianten). */
export function asList<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === 'object') {
    for (const key of ['items', 'data', 'results', 'entries', 'rows']) {
      const v = (data as Record<string, unknown>)[key];
      if (Array.isArray(v)) return v as T[];
    }
  }
  return [];
}

/** Lesbare Fehlermeldung für beliebige Fehler. */
export function errorMessage(e: unknown): string {
  if (e instanceof ApiError) return e.message;
  if (e instanceof Error) return e.message;
  return String(e);
}

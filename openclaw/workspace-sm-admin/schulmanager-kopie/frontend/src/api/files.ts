/**
 * Dateiablage (Basisdienst, docs/ARCHITECTURE.md §9.2) – Backend: `schulmanager/server/routes/files.py`.
 *
 * - {@link uploadFile}: Upload per `XMLHttpRequest` (Fortschritt!) mit CSRF-Header, `purpose` als Query-Parameter,
 *   Abbruch über `AbortSignal`, Fehler als {@link ApiError} mit verständlicher Meldung (413/415/Kontingent/Virus …).
 * - {@link fileUrl}: Download-Adresse (Cookie-Anmeldung reicht, `?inline=1` zeigt PDF/Bilder im Browser).
 * - {@link filesApi}: Limits/Kontingent, eigene Dateien, Metadaten, Löschen (nur eigene, nicht angehängte).
 *
 * Hochgeladene Dateien sind zunächst „lose“ und verfallen nach 24 h, wenn kein Feature sie anhängt
 * (`files.attach(...)` im Backend, z. B. beim Speichern einer Nachricht oder eines Materials).
 */
import { API_BASE, ApiError, buildQuery, describeDetail, extractConflicts, getCsrfToken, http, request, setCsrfToken } from './client';

/** Dateigruppen der Allowlist (Backend `files.KINDS[...].group`). */
export type FileGroup = 'document' | 'image' | 'office' | 'text' | 'audio' | 'video' | 'archive';

/** Metadaten einer gespeicherten Datei (Backend `files.file_info`). */
export interface StoredFileInfo {
  id: string;
  filename: string;
  /** Klartext-Größe in Byte */
  size: number;
  /** aus dem Inhalt erkannt (nicht vom Browser übernommen) */
  content_type: string;
  /** z. B. `pdf`, `png`, `docx` */
  kind: string;
  /** z. B. „PDF-Dokument“ */
  kind_label: string;
  group: FileGroup | string;
  /** darf im Browser angezeigt werden (PDF, Bilder – nie SVG) */
  inline: boolean;
  purpose: string;
  attached: boolean;
  ref_type: string | null;
  ref_id: string | null;
  created_at: string | null;
  /** `clean` (Virenscan ok), `unscanned` (kein Scanner), `error` (Scanner nicht erreichbar → ungeprüft) */
  scan_status: string;
  /** eigene Datei */
  owner: boolean;
  /** eigene, noch nicht angehängte Datei → löschbar */
  can_delete: boolean;
  /** `/api/v1/files/{id}` */
  url: string;
}

export interface FileKindInfo {
  key: string;
  label: string;
  mime: string;
  extensions: string[];
  group: FileGroup | string;
  inline: boolean;
}

/** `GET /files/limits?purpose=` */
export interface FileLimits {
  max_upload_bytes: number;
  /** `null` = unbegrenzt */
  quota_bytes: number | null;
  used_bytes: number;
  /** für `<input accept>`: `.pdf,.png,…` */
  accept: string;
  kinds: FileKindInfo[];
  virus_scan: boolean;
  can_upload: boolean;
}

/** Fehlercodes des Backends (`detail.code`). */
export type FileErrorCode =
  | 'file_too_large'
  | 'quota_exceeded'
  | 'unsupported_type'
  | 'blocked_type'
  | 'virus_found'
  | 'empty_file'
  | 'no_file'
  | 'scan_failed'
  | 'invalid_purpose'
  | 'bad_request'
  | 'attached'
  | 'already_attached'
  | 'not_found';

const enc = encodeURIComponent;

export const filesApi = {
  /** Größenlimit, Kontingent und erlaubte Dateiarten (optional je Zweck). */
  limits: (purpose?: string, signal?: AbortSignal) => http.get<FileLimits>('/files/limits', { purpose }, { signal }),
  /** Eigene Dateien, neueste zuerst. */
  mine: (opts: { purpose?: string; unattached?: boolean; limit?: number } = {}, signal?: AbortSignal) =>
    http.get<StoredFileInfo[]>('/files', { purpose: opts.purpose, unattached: opts.unattached ? 1 : undefined, limit: opts.limit }, { signal }),
  /** Metadaten (Eigentümer oder Zugriff über das Feature, sonst 404). */
  meta: (id: string, signal?: AbortSignal) => http.get<StoredFileInfo>(`/files/${enc(id)}/meta`, undefined, { signal }),
  /** Eigene, nicht angehängte Datei löschen (409 `attached`, wenn angehängt). */
  remove: (id: string) => http.del<{ deleted: string }>(`/files/${enc(id)}`),
};

/** Download-Adresse; `inline` zeigt PDF/Bilder im Browser an (SVG und alles andere immer als Download). */
export function fileUrl(id: string, opts: { inline?: boolean } = {}): string {
  return `${API_BASE}/files/${enc(id)}${opts.inline ? '?inline=1' : ''}`;
}

// ------------------------------------------------------------------ Formatierung & Vorabprüfung

const NUM_DE = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 1 });

/** „830 Byte“, „12,4 KB“, „3,2 MB“, „1,1 GB“ */
export function formatFileSize(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined || !Number.isFinite(bytes)) return '–';
  if (bytes < 1024) return `${bytes} Byte`;
  if (bytes < 1024 * 1024) return `${NUM_DE.format(bytes / 1024)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${NUM_DE.format(bytes / 1024 / 1024)} MB`;
  return `${NUM_DE.format(bytes / 1024 / 1024 / 1024)} GB`;
}

/** Kleingeschriebene Endung inkl. Punkt (`Foto.JPG` → `.jpg`), sonst `''`. */
export function extensionOf(name: string): string {
  const m = /\.([A-Za-z0-9]{1,10})$/.exec(name.trim());
  return m ? `.${m[1].toLowerCase()}` : '';
}

/** `accept`-Liste (`.pdf,.png` bzw. MIME-Typen) → Endungen in Kleinbuchstaben. */
export function acceptedExtensions(accept: string | null | undefined): Set<string> {
  return new Set(
    (accept ?? '')
      .split(',')
      .map((x) => x.trim().toLowerCase())
      .filter((x) => x.startsWith('.')),
  );
}

/**
 * Prüfung VOR dem Hochladen (spart Datenvolumen; das Backend prüft ohnehin alles noch einmal am Inhalt).
 * `pendingBytes` = bereits angenommene, aber noch nicht vom Server gezählte Uploads. Liefert eine Meldung oder `null`.
 */
export function precheckFile(
  file: { name: string; size: number },
  limits: Pick<FileLimits, 'max_upload_bytes' | 'quota_bytes' | 'used_bytes' | 'accept'> | null | undefined,
  opts: { accept?: string; pendingBytes?: number } = {},
): string | null {
  if (file.size === 0) return 'Die Datei ist leer.';
  if (!limits) return null;
  if (file.size > limits.max_upload_bytes) {
    return `Die Datei ist zu groß (${formatFileSize(file.size)}, erlaubt sind höchstens ${formatFileSize(limits.max_upload_bytes)}).`;
  }
  const ext = extensionOf(file.name);
  const allowed = acceptedExtensions(opts.accept ?? limits.accept);
  // ohne Endung entscheidet der Server am Inhalt (z. B. Fotos aus der Zwischenablage)
  if (ext && allowed.size && !allowed.has(ext)) {
    return `Dateien vom Typ „${ext}“ sind hier nicht erlaubt.`;
  }
  if (limits.quota_bytes !== null && limits.quota_bytes !== undefined) {
    const used = limits.used_bytes + (opts.pendingBytes ?? 0);
    if (used + file.size > limits.quota_bytes) {
      return `Ihr Speicherplatz reicht nicht: ${formatFileSize(used)} von ${formatFileSize(limits.quota_bytes)} belegt. Bitte nicht mehr benötigte Dateien löschen.`;
    }
  }
  return null;
}

function detailObject(detail: unknown): { code?: string; message?: string } {
  return detail && typeof detail === 'object' && !Array.isArray(detail) ? (detail as { code?: string; message?: string }) : {};
}

/** Code aus `detail` (`{"code","message"}`) – auch für Aufrufer, die z. B. `quota_exceeded` gesondert behandeln. */
export function fileErrorCode(error: unknown): FileErrorCode | string | null {
  if (!(error instanceof ApiError)) return null;
  const code = detailObject(error.detail).code;
  if (typeof code === 'string') return code;
  if (error.status === 413) return 'file_too_large';
  if (error.status === 415) return 'unsupported_type';
  return null;
}

/** Verständliche deutsche Meldung für einen fehlgeschlagenen Upload/Download. */
export function uploadErrorMessage(status: number, detail: unknown): string {
  const d = detailObject(detail);
  if (typeof d.message === 'string' && d.message) return d.message;
  switch (status) {
    case 0:
      return 'Keine Verbindung zum Server – bitte Verbindung prüfen und erneut versuchen.';
    case 401:
      return 'Ihre Anmeldung ist abgelaufen. Bitte erneut anmelden.';
    case 403:
      if (detail === 'csrf_failed') return 'Sicherheitsprüfung fehlgeschlagen – bitte die Seite neu laden.';
      if (typeof detail === 'string' && detail && detail !== 'forbidden') return describeDetail(status, detail);
      return 'Ihr Konto darf hier keine Dateien hochladen.';
    case 413:
      return 'Die Datei ist zu groß.';
    case 415:
      return 'Dieser Dateityp ist nicht erlaubt.';
    case 429:
      return 'Zu viele Uploads in kurzer Zeit – bitte kurz warten.';
    case 503:
      return 'Der Upload ist gerade nicht möglich (z. B. Virenscanner nicht erreichbar). Bitte später erneut versuchen.';
    case 507:
      return 'Auf dem Server ist kein Speicherplatz mehr frei. Bitte die Schulverwaltung informieren.';
    default:
      return describeDetail(status, detail);
  }
}

// ------------------------------------------------------------------ Upload mit Fortschritt

export interface UploadProgress {
  loaded: number;
  total: number;
  /** 0 … 1 */
  fraction: number;
}

export interface UploadOptions {
  /** Zweck, z. B. `channel_material`, `message`, `student_document` (Backend-Regeln je Zweck) */
  purpose?: string;
  /** Dateiname (Standard: `file.name`) */
  filename?: string;
  onProgress?: (p: UploadProgress) => void;
  signal?: AbortSignal;
}

function parseJson(text: string): unknown {
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

/** Fehler eines Uploads (`DOMException('AbortError')` bei Abbruch, sonst {@link ApiError}). */
export function isAbortError(e: unknown): boolean {
  return e instanceof DOMException ? e.name === 'AbortError' : !!e && typeof e === 'object' && (e as { name?: string }).name === 'AbortError';
}

/**
 * Lädt eine Datei hoch (multipart, Feld `file`) und liefert die Metadaten. Der Fortschritt kommt über `onProgress`.
 * Fehler: {@link ApiError} (Status + `detail = {code, message}`), Abbruch: `DOMException` „AbortError“.
 */
export function uploadFile(file: Blob, opts: UploadOptions = {}): Promise<StoredFileInfo> {
  return new Promise<StoredFileInfo>((resolve, reject) => {
    if (opts.signal?.aborted) {
      reject(new DOMException('Upload abgebrochen', 'AbortError'));
      return;
    }
    const purpose = opts.purpose || 'general';
    const name = opts.filename ?? (typeof File !== 'undefined' && file instanceof File ? file.name : 'datei');
    const form = new FormData();
    form.append('purpose', purpose); // vor der Datei: das Backend kennt den Zweck dann schon beim Streamen
    form.append('file', file, name);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE}/files${buildQuery({ purpose })}`);
    xhr.setRequestHeader('Accept', 'application/json');
    const csrf = getCsrfToken();
    if (csrf) xhr.setRequestHeader('X-CSRF-Token', csrf);

    const onAbort = () => xhr.abort();
    const cleanup = () => opts.signal?.removeEventListener('abort', onAbort);
    opts.signal?.addEventListener('abort', onAbort, { once: true });

    if (opts.onProgress && xhr.upload) {
      const report = opts.onProgress;
      xhr.upload.onprogress = (e: ProgressEvent) => {
        const total = e.lengthComputable && e.total ? e.total : file.size;
        report({ loaded: e.loaded, total, fraction: total ? Math.min(1, e.loaded / total) : 0 });
      };
    }
    xhr.onload = () => {
      cleanup();
      const rotated = xhr.getResponseHeader('X-CSRF-Token');
      if (rotated) setCsrfToken(rotated);
      const data = parseJson(xhr.responseText);
      if (xhr.status >= 200 && xhr.status < 300 && data && typeof data === 'object') {
        resolve(data as StoredFileInfo);
        return;
      }
      const detail = data && typeof data === 'object' && 'detail' in data ? (data as { detail: unknown }).detail : data;
      if (xhr.status === 401) {
        // globale Behandlung („abgemeldet“ → Anmeldeseite) wie bei allen anderen API-Aufrufen auslösen
        void request('GET', '/auth/me').catch(() => undefined);
      }
      reject(new ApiError(xhr.status, uploadErrorMessage(xhr.status, detail), detail, extractConflicts(detail)));
    };
    xhr.onerror = () => {
      cleanup();
      reject(new ApiError(0, uploadErrorMessage(0, null), null));
    };
    xhr.onabort = () => {
      cleanup();
      reject(new DOMException('Upload abgebrochen', 'AbortError'));
    };
    xhr.send(form);
  });
}

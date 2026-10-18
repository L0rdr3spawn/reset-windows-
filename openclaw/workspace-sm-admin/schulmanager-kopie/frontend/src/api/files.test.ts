/**
 * Tests der Dateiablage im Frontend: Upload per XMLHttpRequest (CSRF, Fortschritt, Fehler, Abbruch, 401),
 * Vorabprüfung, Fehlermeldungen und Darstellung von FileList/FileUpload (statisch gerendert).
 */
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { FileList, canView, fileMetaText } from '../components/FileList';
import { FileUpload, allowedKindsText } from '../components/FileUpload';
import { ApiError, getCsrfToken, onUnauthorized, setCsrfToken } from './client';
import {
  acceptedExtensions,
  extensionOf,
  fileErrorCode,
  fileUrl,
  formatFileSize,
  isAbortError,
  precheckFile,
  uploadErrorMessage,
  uploadFile,
  type FileLimits,
  type StoredFileInfo,
} from './files';

// ------------------------------------------------------------------ Hilfen

type Progress = { loaded: number; total: number; lengthComputable: boolean };

class FakeXHR {
  static instances: FakeXHR[] = [];
  method = '';
  url = '';
  headers: Record<string, string> = {};
  body: unknown = null;
  status = 0;
  responseText = '';
  responseHeaders: Record<string, string> = {};
  aborted = false;
  upload: { onprogress: ((e: Progress) => void) | null } = { onprogress: null };
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onabort: (() => void) | null = null;

  constructor() {
    FakeXHR.instances.push(this);
  }

  open(method: string, url: string): void {
    this.method = method;
    this.url = url;
  }

  setRequestHeader(name: string, value: string): void {
    this.headers[name] = value;
  }

  getResponseHeader(name: string): string | null {
    return this.responseHeaders[name] ?? null;
  }

  send(body: unknown): void {
    this.body = body;
  }

  abort(): void {
    this.aborted = true;
    this.onabort?.();
  }

  respond(status: number, body?: unknown, headers: Record<string, string> = {}): void {
    this.status = status;
    this.responseText = body === undefined ? '' : typeof body === 'string' ? body : JSON.stringify(body);
    this.responseHeaders = headers;
    this.onload?.();
  }
}

const last = () => FakeXHR.instances[FakeXHR.instances.length - 1];

const ID = '0f8fad5b-d9cb-469f-a165-70867728950e';

function info(over: Partial<StoredFileInfo> = {}): StoredFileInfo {
  return {
    id: ID,
    filename: 'Arbeitsblatt Übung 1.pdf',
    size: 1536,
    content_type: 'application/pdf',
    kind: 'pdf',
    kind_label: 'PDF-Dokument',
    group: 'document',
    inline: true,
    purpose: 'test',
    attached: false,
    ref_type: null,
    ref_id: null,
    created_at: '2026-10-06T08:15:00Z',
    scan_status: 'unscanned',
    owner: true,
    can_delete: true,
    url: `/api/v1/files/${ID}`,
    ...over,
  };
}

const LIMITS: FileLimits = {
  max_upload_bytes: 25 * 1024 * 1024,
  quota_bytes: 200 * 1024 * 1024,
  used_bytes: 199 * 1024 * 1024,
  accept: '.pdf,.png,.jpg,.jpeg,.txt,.svg',
  kinds: [
    { key: 'pdf', label: 'PDF-Dokument', mime: 'application/pdf', extensions: ['.pdf'], group: 'document', inline: true },
    { key: 'png', label: 'PNG-Bild', mime: 'image/png', extensions: ['.png'], group: 'image', inline: true },
    { key: 'jpeg', label: 'JPEG-Bild', mime: 'image/jpeg', extensions: ['.jpg', '.jpeg'], group: 'image', inline: true },
    { key: 'txt', label: 'Textdatei', mime: 'text/plain', extensions: ['.txt'], group: 'text', inline: false },
  ],
  virus_scan: false,
  can_upload: true,
};

beforeEach(() => {
  FakeXHR.instances = [];
  vi.stubGlobal('XMLHttpRequest', FakeXHR);
  setCsrfToken('csrf-1');
});

afterEach(() => {
  vi.unstubAllGlobals();
  setCsrfToken(null);
});

// ------------------------------------------------------------------ Upload

describe('uploadFile', () => {
  it('sendet multipart mit purpose, CSRF-Header und meldet Fortschritt', async () => {
    const progress: number[] = [];
    const blob = new File(['%PDF-1.4 Inhalt'], 'Arbeitsblatt.pdf', { type: 'application/pdf' });
    const promise = uploadFile(blob, { purpose: 'channel_material', onProgress: (p) => progress.push(p.fraction) });
    const xhr = last();
    expect(xhr.method).toBe('POST');
    expect(xhr.url).toBe('/api/v1/files?purpose=channel_material');
    expect(xhr.headers['X-CSRF-Token']).toBe('csrf-1');
    expect(xhr.headers.Accept).toBe('application/json');
    const form = xhr.body as FormData;
    expect(form.get('purpose')).toBe('channel_material');
    expect((form.get('file') as File).name).toBe('Arbeitsblatt.pdf');
    expect([...form.keys()]).toEqual(['purpose', 'file']); // Zweck vor der Datei (Backend streamt)
    xhr.upload.onprogress?.({ loaded: 5, total: 10, lengthComputable: true });
    xhr.upload.onprogress?.({ loaded: 10, total: 10, lengthComputable: true });
    xhr.respond(201, info(), { 'X-CSRF-Token': 'csrf-2' });
    await expect(promise).resolves.toMatchObject({ id: ID, kind: 'pdf' });
    expect(progress).toEqual([0.5, 1]);
    expect(getCsrfToken()).toBe('csrf-2'); // rotiertes Token übernommen
  });

  it('übernimmt Fehlermeldungen des Servers (415/413/Kontingent) als ApiError', async () => {
    const p1 = uploadFile(new Blob(['MZ']), { purpose: 'test', filename: 'setup.exe' });
    last().respond(415, { detail: { code: 'blocked_type', message: 'Windows-Programme sind aus Sicherheitsgründen nicht erlaubt.' } });
    const e1 = await p1.catch((e: unknown) => e);
    expect(e1).toBeInstanceOf(ApiError);
    expect((e1 as ApiError).status).toBe(415);
    expect((e1 as ApiError).message).toContain('Windows-Programme');
    expect(fileErrorCode(e1)).toBe('blocked_type');

    const p2 = uploadFile(new Blob(['x']), { filename: 'gross.mp4' });
    last().respond(413, '<html>Request Entity Too Large</html>'); // z. B. vom Reverse Proxy
    const e2 = await p2.catch((e: unknown) => e);
    expect((e2 as ApiError).message).toBe('Die Datei ist zu groß.');
    expect(fileErrorCode(e2)).toBe('file_too_large');

    const p3 = uploadFile(new Blob(['x']), { filename: 'a.pdf' });
    last().respond(413, { detail: { code: 'quota_exceeded', message: 'Ihr Speicherplatz reicht nicht: 200 MB von 200 MB belegt.' } });
    const e3 = await p3.catch((e: unknown) => e);
    expect(fileErrorCode(e3)).toBe('quota_exceeded');
    expect((e3 as ApiError).message).toContain('Speicherplatz');
  });

  it('Abbruch per AbortSignal und Netzwerkfehler', async () => {
    const ctrl = new AbortController();
    const p = uploadFile(new Blob(['x']), { filename: 'a.txt', signal: ctrl.signal });
    ctrl.abort();
    const err = await p.catch((e: unknown) => e);
    expect(isAbortError(err)).toBe(true);
    expect(last().aborted).toBe(true);

    const before = FakeXHR.instances.length;
    await expect(uploadFile(new Blob(['x']), { signal: ctrl.signal })).rejects.toMatchObject({ name: 'AbortError' });
    expect(FakeXHR.instances.length).toBe(before); // gar nicht erst gesendet

    const p2 = uploadFile(new Blob(['x']), { filename: 'a.txt' });
    last().onerror?.();
    const e2 = await p2.catch((e: unknown) => e);
    expect((e2 as ApiError).status).toBe(0);
    expect((e2 as ApiError).message).toContain('Keine Verbindung');
  });

  it('401 löst die globale Abmelde-Behandlung aus', async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ detail: 'not_authenticated' }), { status: 401 }));
    vi.stubGlobal('fetch', fetchMock);
    const loggedOut = vi.fn();
    const off = onUnauthorized(loggedOut);
    const p = uploadFile(new Blob(['x']), { filename: 'a.txt' });
    last().respond(401, { detail: 'not_authenticated' });
    const err = await p.catch((e: unknown) => e);
    expect((err as ApiError).message).toContain('erneut anmelden');
    await vi.waitFor(() => expect(loggedOut).toHaveBeenCalled());
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/auth/me', expect.anything());
    off();
  });
});

// ------------------------------------------------------------------ Helfer

describe('Vorabprüfung und Formatierung', () => {
  it('formatiert Größen deutsch und erkennt Endungen', () => {
    expect(formatFileSize(830)).toBe('830 Byte');
    expect(formatFileSize(1536)).toBe('1,5 KB');
    expect(formatFileSize(25 * 1024 * 1024)).toBe('25 MB');
    expect(formatFileSize(null)).toBe('–');
    expect(extensionOf('Foto.JPG')).toBe('.jpg');
    expect(extensionOf('ohne-endung')).toBe('');
    expect([...acceptedExtensions('.PDF, .png,image/*')]).toEqual(['.pdf', '.png']);
  });

  it('precheckFile: leer, zu groß, Typ, Kontingent, ohne Endung', () => {
    expect(precheckFile({ name: 'a.pdf', size: 0 }, LIMITS)).toBe('Die Datei ist leer.');
    expect(precheckFile({ name: 'film.pdf', size: 30 * 1024 * 1024 }, LIMITS)).toContain('zu groß');
    expect(precheckFile({ name: 'setup.exe', size: 10 }, LIMITS)).toContain('„.exe“');
    expect(precheckFile({ name: 'a.pdf', size: 2 * 1024 * 1024 }, LIMITS)).toContain('Speicherplatz');
    expect(precheckFile({ name: 'a.pdf', size: 1024 }, LIMITS)).toBeNull();
    expect(precheckFile({ name: 'a.pdf', size: 1024 }, LIMITS, { pendingBytes: 1024 * 1024 })).toContain('Speicherplatz');
    expect(precheckFile({ name: 'foto', size: 1024 }, LIMITS)).toBeNull(); // Server entscheidet am Inhalt
    expect(precheckFile({ name: 'a.png', size: 1024 }, LIMITS, { accept: '.pdf' })).toContain('„.png“');
    expect(precheckFile({ name: 'a.exe', size: 1024 }, null)).toBeNull();
    expect(precheckFile({ name: 'a.pdf', size: 1024 }, { ...LIMITS, quota_bytes: null })).toBeNull();
  });

  it('uploadErrorMessage ohne Serverdetails', () => {
    expect(uploadErrorMessage(415, null)).toBe('Dieser Dateityp ist nicht erlaubt.');
    expect(uploadErrorMessage(403, 'csrf_failed')).toContain('Seite neu laden');
    expect(uploadErrorMessage(403, null)).toContain('keine Dateien hochladen');
    expect(uploadErrorMessage(403, 'Keine Berechtigung zum Hochladen von Dateien')).toBe('Keine Berechtigung zum Hochladen von Dateien');
    expect(uploadErrorMessage(503, null)).toContain('später erneut');
    expect(uploadErrorMessage(422, { code: 'virus_found', message: 'Virus erkannt.' })).toBe('Virus erkannt.');
  });

  it('fileUrl mit und ohne Anzeige im Browser', () => {
    expect(fileUrl(ID)).toBe(`/api/v1/files/${ID}`);
    expect(fileUrl(ID, { inline: true })).toBe(`/api/v1/files/${ID}?inline=1`);
    expect(fileUrl('a/b')).toBe('/api/v1/files/a%2Fb');
  });
});

// ------------------------------------------------------------------ Komponenten (statisch gerendert)

describe('FileList', () => {
  it('zeigt Name, Download-Link, Größe; „Ansehen“ nur für PDF/Bilder, nie für SVG', () => {
    const svg = info({ id: 'svg-1', filename: 'grafik.svg', kind: 'svg', kind_label: 'SVG-Grafik', group: 'image', inline: false });
    const scanned = info({ id: 'txt-1', filename: 'notiz.txt', kind: 'txt', group: 'text', inline: false, scan_status: 'error', can_delete: false });
    const html = renderToStaticMarkup(createElement(FileList, { files: [info(), svg, scanned], onDelete: () => undefined }));
    expect(html).toContain('Arbeitsblatt Übung 1.pdf');
    expect(html).toContain(`href="/api/v1/files/${ID}"`);
    expect(html).toContain(`href="/api/v1/files/${ID}?inline=1"`);
    expect(html).not.toContain('href="/api/v1/files/svg-1?inline=1"');
    expect(html).toContain('rel="noopener noreferrer"');
    expect(html).toContain('1,5 KB');
    expect(html).toContain('06.10.2026');
    expect(html).toContain('nicht virengeprüft');
    expect((html.match(/title="Löschen"/g) ?? []).length).toBe(2); // PDF + SVG (can_delete), nicht notiz.txt
    expect(html).toContain('aria-label="grafik.svg löschen"');
    expect(canView(svg)).toBe(false);
    expect(fileMetaText(info(), { date: false })).toBe('PDF-Dokument · 1,5 KB');
  });

  it('leere Liste: Hinweistext oder nichts', () => {
    expect(renderToStaticMarkup(createElement(FileList, { files: [] }))).toContain('Keine Dateien');
    expect(renderToStaticMarkup(createElement(FileList, { files: [], emptyText: null }))).toBe('');
    const html = renderToStaticMarkup(createElement(FileList, { files: [info()] }));
    expect(html).not.toContain('Löschen'); // ohne onDelete kein Knopf
  });
});

describe('FileUpload', () => {
  it('Ablagefläche mit Auswahlknopf, kompakte Variante, Einzeldatei', () => {
    const full = renderToStaticMarkup(createElement(FileUpload, { purpose: 'test', label: 'Material' }));
    // Test-Umgebung ohne Maus (wie Touch): kein „hierher ziehen“, nur der Auswahlknopf
    expect(full).not.toContain('hierher ziehen');
    expect(full).toContain('Dateien auswählen');
    expect(full).toContain('type="file"');
    expect(full).toContain('multiple');
    expect(full).toContain('aria-live="polite"');
    const compact = renderToStaticMarkup(createElement(FileUpload, { purpose: 'message_attachment', compact: true }));
    expect(compact).toContain('Dateien anhängen');
    const single = renderToStaticMarkup(createElement(FileUpload, { purpose: 'student_document', multiple: false }));
    expect(single).toContain('Datei auswählen');
    expect(single).not.toContain('multiple=""');
  });

  it('beschreibt erlaubte Dateiarten', () => {
    expect(allowedKindsText(LIMITS)).toBe('PDF, Bilder, Text/CSV');
    expect(allowedKindsText(null)).toBe('');
  });
});

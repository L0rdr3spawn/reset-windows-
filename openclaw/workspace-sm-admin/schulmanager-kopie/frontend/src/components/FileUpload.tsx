/**
 * Datei-Upload (Basisdienst §9.2): Ablagefläche für Drag & Drop + Auswahlknopf, mehrere Dateien nacheinander mit
 * Fortschritt, Abbrechen/Erneut versuchen/Entfernen, verständliche Fehler (zu groß 413, Typ nicht erlaubt 415,
 * Speicherplatz voll, Virenfund, Netzwerk). Vorabprüfung von Größe/Typ/Kontingent spart Datenvolumen; das Backend
 * prüft trotzdem alles am Inhalt.
 *
 *   <FileUpload purpose="channel_material" onChange={(files) => setFileIds(files.map((f) => f.id))} />
 *
 * Hochgeladene Dateien sind „lose“, bis das Feature sie im Backend anhängt (sonst nach 24 h gelöscht).
 * Nach dem Speichern die Komponente per `key` neu aufbauen, um die Liste zu leeren.
 */
import { useInputMode } from '../hooks/useInputMode';
import { useCallback, useEffect, useId, useMemo, useRef, useState, type DragEvent, type MutableRefObject, type ReactNode } from 'react';
import { ApiError, errorMessage } from '../api/client';
import {
  filesApi,
  formatFileSize,
  isAbortError,
  precheckFile,
  uploadFile,
  type FileLimits,
  type StoredFileInfo,
} from '../api/files';
import { onSessionReset } from '../lib/session';
import { FileList } from './FileList';
import { Icon } from './Icon';

// ------------------------------------------------------------------ Limits (kurz zwischengespeichert)

const LIMITS_TTL_MS = 60_000;
const limitsCache = new Map<string, { at: number; promise: Promise<FileLimits> }>();

/** Limits/Kontingent eines Zwecks (60 s zwischengespeichert, gemeinsam für alle Upload-Felder). */
export function loadFileLimits(purpose = ''): Promise<FileLimits> {
  const hit = limitsCache.get(purpose);
  if (hit && Date.now() - hit.at < LIMITS_TTL_MS) return hit.promise;
  const promise = filesApi.limits(purpose || undefined);
  limitsCache.set(purpose, { at: Date.now(), promise });
  promise.catch(() => limitsCache.delete(purpose));
  return promise;
}

/** Nach Upload/Löschen: belegten Speicher neu laden. */
export function invalidateFileLimits(): void {
  limitsCache.clear();
}
onSessionReset(invalidateFileLimits); // Kontingent gehört zum Konto (U-01)

export function useFileLimits(purpose?: string): { limits: FileLimits | null; error: unknown; reload: () => void } {
  const [state, setState] = useState<{ limits: FileLimits | null; error: unknown }>({ limits: null, error: null });
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let alive = true;
    loadFileLimits(purpose ?? '').then(
      (limits) => alive && setState({ limits, error: null }),
      (error: unknown) => alive && setState((s) => ({ limits: s.limits, error })),
    );
    return () => {
      alive = false;
    };
  }, [purpose, tick]);
  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { ...state, reload };
}

const GROUP_LABELS: Record<string, string> = {
  document: 'PDF',
  image: 'Bilder',
  office: 'Office-Dokumente',
  text: 'Text/CSV',
  audio: 'Audio',
  video: 'Video',
  archive: 'ZIP',
  app: 'GeoGebra/SMART/Scratch/H5P',
  code: 'Quelltext',
};

/** „PDF, Bilder, Office-Dokumente, …“ aus den erlaubten Dateiarten. */
export function allowedKindsText(limits: Pick<FileLimits, 'kinds'> | null | undefined): string {
  if (!limits?.kinds?.length) return '';
  const groups = [...new Set(limits.kinds.map((k) => k.group))];
  return groups.map((g) => GROUP_LABELS[g] ?? g).join(', ');
}

// ------------------------------------------------------------------ Komponente

type ItemStatus = 'waiting' | 'uploading' | 'done' | 'error';

interface UploadItem {
  key: string;
  name: string;
  size: number;
  status: ItemStatus;
  progress: number;
  error: string | null;
  /** nur solange ein (erneuter) Upload möglich ist */
  file: File | null;
  result: StoredFileInfo | null;
}

/** Vorübergehende Fehler (Netz, Server, Scanner) → „Erneut versuchen“ anbieten. */
function retryable(e: unknown): boolean {
  return e instanceof ApiError && (e.status === 0 || e.status === 429 || e.status >= 500);
}

export interface FileUploadProps {
  /** Zweck, z. B. `channel_material`, `message`, `student_document` (Backend-Regeln je Zweck) */
  purpose: string;
  /** mehrere Dateien (Standard: ja) */
  multiple?: boolean;
  /** höchstens so viele Dateien in diesem Feld (Standard 20) */
  maxFiles?: number;
  /** eigene, strengere Auswahl (z. B. `.pdf,.jpg,.jpeg,.png`); Standard: Allowlist des Servers für den Zweck */
  accept?: string;
  disabled?: boolean;
  /** Überschrift bzw. Knopftext (kompakt) */
  label?: ReactNode;
  /** zusätzlicher Hinweis unter der Ablagefläche */
  hint?: ReactNode;
  /** schmale Variante (Knopf „Datei anhängen“, Drag & Drop auf den Knopf) – z. B. für Nachrichten */
  compact?: boolean;
  /** je erfolgreich hochgeladener Datei */
  onUploaded?: (file: StoredFileInfo) => void;
  /** alle erfolgreich hochgeladenen (und nicht wieder entfernten) Dateien dieses Felds */
  onChange?: (files: StoredFileInfo[]) => void;
  /** „Entfernen“ löscht den noch nicht angehängten Upload auch auf dem Server (Standard: ja) */
  deleteOnRemove?: boolean;
  /** hochgeladene Dateien im Feld anzeigen (Standard: ja) */
  showList?: boolean;
  /** kompakt ohne eigenen Knopf: ausgelöst wird die Auswahl von außen über `pickRef.current()` (z. B. „+“ im Eingabefeld) */
  hidePicker?: boolean;
  pickRef?: MutableRefObject<(() => void) | null>;
}

let keySeq = 0;

/** Icon mit fester Größe (`.icon` ist nur in Knöpfen/Menü/Hinweisen bemaßt – sonst füllt das SVG die Breite). */
function SizedIcon({ name, size }: { name: string; size: number }) {
  return (
    <span aria-hidden="true" style={{ display: 'inline-block', width: size, height: size, flex: 'none', lineHeight: 0, verticalAlign: 'middle' }}>
      <Icon name={name} />
    </span>
  );
}

export function FileUpload({
  purpose,
  multiple = true,
  maxFiles = 20,
  accept,
  disabled = false,
  label,
  hint,
  compact = false,
  onUploaded,
  onChange,
  deleteOnRemove = true,
  showList = true,
  hidePicker = false,
  pickRef,
}: FileUploadProps) {
  const ids = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const controllers = useRef(new Map<string, AbortController>());
  const dragDepth = useRef(0);
  const [items, setItems] = useState<UploadItem[]>([]);
  const [over, setOver] = useState(false);
  const { fine } = useInputMode();
  const [notice, setNotice] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState('');
  const { limits, error: limitsError, reload: reloadLimits } = useFileLimits(purpose);

  const onUploadedRef = useRef(onUploaded);
  onUploadedRef.current = onUploaded;
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const update = useCallback((key: string, patch: Partial<UploadItem>) => {
    setItems((list) => list.map((i) => (i.key === key ? { ...i, ...patch } : i)));
  }, []);
  const drop = useCallback((key: string) => setItems((list) => list.filter((i) => i.key !== key)), []);

  // Warteschlange: immer nur ein Upload gleichzeitig (schont Server und Mobilfunk)
  useEffect(() => {
    if (items.some((i) => i.status === 'uploading')) return;
    const next = items.find((i) => i.status === 'waiting');
    if (!next?.file) return;
    const file = next.file;
    const controller = new AbortController();
    controllers.current.set(next.key, controller);
    update(next.key, { status: 'uploading', progress: 0, error: null });
    uploadFile(file, {
      purpose,
      signal: controller.signal,
      onProgress: (p) => update(next.key, { progress: p.fraction }),
    })
      .then((info) => {
        update(next.key, { status: 'done', progress: 1, result: info, file: null });
        setAnnouncement(`${info.filename} wurde hochgeladen.`);
        invalidateFileLimits();
        reloadLimits();
        onUploadedRef.current?.(info);
      })
      .catch((e: unknown) => {
        if (isAbortError(e)) {
          drop(next.key);
          setAnnouncement(`Hochladen von ${next.name} abgebrochen.`);
          return;
        }
        const message = errorMessage(e);
        update(next.key, { status: 'error', error: message, file: retryable(e) ? file : null });
        setAnnouncement(`${next.name}: ${message}`);
        if (e instanceof ApiError && e.status === 413) reloadLimits();
      })
      .finally(() => controllers.current.delete(next.key));
  }, [items, purpose, update, drop, reloadLimits]);

  // laufende Uploads beim Verlassen abbrechen
  useEffect(() => {
    const map = controllers.current;
    return () => map.forEach((c) => c.abort());
  }, []);

  const done = useMemo(() => items.filter((i) => i.status === 'done' && i.result).map((i) => i.result as StoredFileInfo), [items]);
  const doneKey = done.map((f) => f.id).join(',');
  const lastDoneKey = useRef('');
  useEffect(() => {
    if (doneKey === lastDoneKey.current) return;
    lastDoneKey.current = doneKey;
    onChangeRef.current?.(done);
  }, [doneKey, done]);

  const active = items.filter((i) => i.status !== 'error').length;
  const canUpload = !disabled && limits?.can_upload !== false;
  const room = multiple ? Math.max(0, maxFiles - active) : active ? 0 : 1;

  const addFiles = (list: ArrayLike<File> | null | undefined) => {
    const all = Array.from(list ?? []);
    if (!all.length || !canUpload) return;
    const taken = all.slice(0, room);
    let pending = items.filter((i) => i.status === 'waiting' || i.status === 'uploading').reduce((s, i) => s + i.size, 0);
    const added: UploadItem[] = taken.map((file) => {
      const problem = precheckFile({ name: file.name, size: file.size }, limits, { accept, pendingBytes: pending });
      if (!problem) pending += file.size;
      keySeq += 1;
      return {
        key: `u${keySeq}`,
        name: file.name || 'Datei',
        size: file.size,
        status: problem ? 'error' : 'waiting',
        progress: 0,
        error: problem,
        file: problem ? null : file,
        result: null,
      };
    });
    setItems((prev) => [...prev, ...added]);
    const rejected = added.filter((i) => i.status === 'error');
    if (rejected.length) setAnnouncement(rejected.map((i) => `${i.name}: ${i.error}`).join(' '));
    const skipped = all.length - taken.length;
    setNotice(
      skipped
        ? multiple
          ? `Höchstens ${maxFiles} Dateien – ${skipped === 1 ? 'eine Datei wurde' : `${skipped} Dateien wurden`} nicht übernommen.`
          : 'Bitte nur eine Datei auswählen.'
        : null,
    );
  };

  const removeDone = async (file: StoredFileInfo) => {
    const item = items.find((i) => i.result?.id === file.id);
    if (deleteOnRemove && file.can_delete) {
      try {
        await filesApi.remove(file.id);
        invalidateFileLimits();
        reloadLimits();
      } catch (e) {
        // schon gelöscht (404) oder inzwischen angehängt (409): nur aus dem Feld nehmen
        if (!(e instanceof ApiError && (e.status === 404 || e.status === 409))) throw e;
      }
    }
    if (item) drop(item.key);
    setAnnouncement(`${file.filename} entfernt.`);
  };

  const onDragEnter = (e: DragEvent) => {
    if (!canUpload || !Array.from(e.dataTransfer.types).includes('Files')) return;
    e.preventDefault();
    dragDepth.current += 1;
    setOver(true);
  };
  const onDragOver = (e: DragEvent) => {
    if (!canUpload || !Array.from(e.dataTransfer.types).includes('Files')) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = room ? 'copy' : 'none';
  };
  const onDragLeave = () => {
    dragDepth.current = Math.max(0, dragDepth.current - 1);
    if (!dragDepth.current) setOver(false);
  };
  const onDrop = (e: DragEvent) => {
    if (!canUpload) return;
    e.preventDefault();
    dragDepth.current = 0;
    setOver(false);
    addFiles(e.dataTransfer.files);
  };

  const openPicker = () => inputRef.current?.click();
  if (pickRef) pickRef.current = canUpload && room ? openPicker : null;
  const hintId = `${ids}-hint`;
  const limitText = [
    limits ? `höchstens ${formatFileSize(limits.max_upload_bytes)} je Datei` : '',
    allowedKindsText(limits),
    limits && limits.quota_bytes !== null ? `belegt: ${formatFileSize(limits.used_bytes)} von ${formatFileSize(limits.quota_bytes)}` : '',
    limits?.virus_scan ? 'mit Virenprüfung' : '',
  ]
    .filter(Boolean)
    .join(' · ');
  const queue = items.filter((i) => i.status !== 'done');
  const pickLabel = multiple ? 'Dateien auswählen' : 'Datei auswählen';

  const input = (
    <input
      ref={inputRef}
      type="file"
      hidden
      multiple={multiple}
      accept={accept ?? limits?.accept ?? undefined}
      onChange={(e) => {
        addFiles(e.target.files);
        e.target.value = ''; // dieselbe Datei erneut wählbar
      }}
    />
  );

  return (
    <div className="file-upload" style={{ minWidth: 0 }}>
      {input}
      {compact ? (
        <div className="row" onDragEnter={onDragEnter} onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}>
          {!hidePicker && (
            <button
              type="button"
              className={`btn btn-sm${over ? ' btn-primary' : ''}`}
              onClick={openPicker}
              disabled={!canUpload || !room}
              aria-describedby={hintId}
            >
              <Icon name="upload" /> {label ?? (multiple ? 'Dateien anhängen' : 'Datei anhängen')}
            </button>
          )}
          {!hidePicker && (
            <span id={hintId} className="xsmall muted">
              {limits ? `max. ${formatFileSize(limits.max_upload_bytes)}` : ''}
              {hint ? <> · {hint}</> : null}
            </span>
          )}
        </div>
      ) : (
        <div
          className={`dropzone${over ? ' over' : ''}`}
          onDragEnter={onDragEnter}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          style={{ padding: 'var(--space-4)', opacity: canUpload ? 1 : 0.7 }}
        >
          <div style={{ color: 'var(--primary)' }}>
            <SizedIcon name="upload" size={36} />
          </div>
          <div style={{ margin: 'var(--space-2) 0' }}>
            {label && <div style={{ fontWeight: 600, color: 'var(--text)' }}>{label}</div>}
            {fine && <span>{multiple ? 'Dateien hierher ziehen oder' : 'Datei hierher ziehen oder'}</span>}{' '}
            <button type="button" className="btn btn-sm btn-primary" onClick={openPicker} disabled={!canUpload || !room} aria-describedby={hintId}>
              {pickLabel}
            </button>
          </div>
          <div id={hintId} className="small">
            {limitText}
            {hint ? <div>{hint}</div> : null}
          </div>
        </div>
      )}

      {!canUpload && !disabled && limits && (
        <p className="small muted" style={{ margin: 'var(--space-2) 0 0' }}>
          Ihr Konto darf keine Dateien hochladen.
        </p>
      )}
      {limitsError && !limits ? (
        <p className="xsmall muted" style={{ margin: 'var(--space-1) 0 0' }}>
          Grenzen konnten nicht geladen werden – der Server prüft die Dateien beim Hochladen.
        </p>
      ) : null}
      {notice && (
        <p className="small" role="status" style={{ color: 'var(--warning)', margin: 'var(--space-2) 0 0' }}>
          {notice}
        </p>
      )}

      {queue.length > 0 && (
        <ul aria-label="Uploads" style={{ listStyle: 'none', margin: 'var(--space-2) 0 0', padding: 0, display: 'grid', gap: 'var(--space-2)' }}>
          {queue.map((i) => {
            const pct = Math.round(i.progress * 100);
            return (
              <li
                key={i.key}
                style={{
                  border: '1px solid var(--border)',
                  borderLeft: `4px solid ${i.status === 'error' ? 'var(--danger)' : 'var(--primary)'}`,
                  borderRadius: 'var(--radius-sm)',
                  padding: 'var(--space-2) var(--space-3)',
                  background: 'var(--surface)',
                  minWidth: 0,
                }}
              >
                <div className="row-between" style={{ alignItems: 'flex-start' }}>
                  <div style={{ minWidth: 0, flex: '1 1 10rem' }}>
                    <div style={{ fontWeight: 600, overflowWrap: 'anywhere' }}>{i.name}</div>
                    <div className="xsmall muted">
                      {formatFileSize(i.size)}
                      {i.status === 'waiting' && ' · wartet …'}
                      {i.status === 'uploading' && ` · wird hochgeladen (${pct} %)`}
                    </div>
                  </div>
                  <div className="row" style={{ gap: 4 }}>
                    {i.status === 'uploading' && (
                      <button type="button" className="btn btn-sm btn-ghost" onClick={() => controllers.current.get(i.key)?.abort()}>
                        <Icon name="x" /> Abbrechen<span className="sr-only">: {i.name}</span>
                      </button>
                    )}
                    {i.status === 'error' && i.file && (
                      <button type="button" className="btn btn-sm" onClick={() => update(i.key, { status: 'waiting', error: null, progress: 0 })}>
                        <Icon name="refresh" /> Erneut versuchen<span className="sr-only">: {i.name}</span>
                      </button>
                    )}
                    {(i.status === 'error' || i.status === 'waiting') && (
                      <button type="button" className="btn btn-sm btn-ghost" onClick={() => drop(i.key)} aria-label={`${i.name} aus der Liste entfernen`}>
                        <Icon name="close" />
                      </button>
                    )}
                  </div>
                </div>
                {i.status === 'uploading' && (
                  <div
                    className="progress"
                    role="progressbar"
                    aria-label={`Fortschritt ${i.name}`}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={pct}
                    style={{ marginTop: 'var(--space-2)', height: 8 }}
                  >
                    <div className="progress-bar" style={{ width: `${pct}%`, transition: 'width 0.15s linear' }} />
                  </div>
                )}
                {i.status === 'error' && i.error && (
                  <p className="small" style={{ color: 'var(--danger)', margin: 'var(--space-1) 0 0' }}>
                    <SizedIcon name="alert" size={16} /> {i.error}
                  </p>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {showList && done.length > 0 && (
        <div style={{ marginTop: 'var(--space-2)' }}>
          <FileList files={done} onDelete={removeDone} confirmDelete={false} deleteLabel="Entfernen" compact={compact} label="Hochgeladene Dateien" />
        </div>
      )}

      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {announcement}
      </div>
    </div>
  );
}

export default FileUpload;

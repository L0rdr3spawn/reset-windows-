/**
 * Hochladen ins Material in **einem** Schritt (A-45): einzelne Dateien und ganze Ordner (Auswahl mit Unterordnern
 * oder Drag & Drop) – jede fertig hochgeladene Datei wird sofort als Material gespeichert (verborgen/sichtbar/zur
 * Stunde je nach Wahl). Ordner: erst `POST …/folders/tree` (Struktur, oberste Ordner mit der Sichtbarkeit), dann
 * die Dateien sichtbar in ihre Ordner. Schließen verliert nichts: Gespeichertes bleibt, Laufendes wird abgebrochen.
 */
import { useCallback, useEffect, useId, useRef, useState, type DragEvent } from 'react';
import { useInputMode } from '../../hooks/useInputMode';
import { ApiError, errorMessage } from '../../api/client';
import { formatFileSize, isAbortError, precheckFile, uploadFile } from '../../api/files';
import { allowedKindsText, invalidateFileLimits, useFileLimits } from '../../components/FileUpload';
import { Icon } from '../../components/Icon';
import { channelsApi } from './api';
import { DEFAULT_DRAFT, dirOf, draftToInput, folderPaths, type PathFile, type VisibilityDraft } from './logic';
import type { ChannelDetail, VisibilityInput } from './types';
import { VisibilityPicker } from './VisibilityPicker';
import { confirmAsk } from '../../lib/confirm';

const PURPOSE = 'channel_material';
const MAX_PER_DROP = 500;
const SKIP_NAMES = new Set(['thumbs.db', 'desktop.ini']);

type Status = 'waiting' | 'uploading' | 'saving' | 'done' | 'error';

interface Entry {
  key: string;
  name: string;
  dir: string;
  size: number;
  status: Status;
  progress: number;
  error: string | null;
  file: File | null;
  /** schon hochgeladen (nur Speichern als Material fehlt noch) */
  fileId: string | null;
  folderId: number | null;
  vis: VisibilityInput;
}

let seq = 0;

/** Systemdateien (`.DS_Store`, `Thumbs.db`, versteckte Dateien) überspringen. */
function skipped(name: string): boolean {
  return name.startsWith('.') || SKIP_NAMES.has(name.toLowerCase());
}

/** Wie beim Ablegen auch bei der Ordner-Auswahl: Systemdateien und alles in versteckten Ordnern (`.git`, `.idea` …). */
export function usableFiles(files: readonly PathFile[]): PathFile[] {
  return files.filter((f) => !skipped(f.file.name) && !f.dir.split('/').some((part) => part.startsWith('.')));
}

function readAll(reader: FileSystemDirectoryReader): Promise<FileSystemEntry[]> {
  return new Promise((resolve, reject) => {
    const out: FileSystemEntry[] = [];
    const next = () =>
      reader.readEntries((batch) => {
        if (!batch.length) resolve(out);
        else {
          out.push(...batch);
          next();
        }
      }, reject);
    next();
  });
}

async function walk(entry: FileSystemEntry, dir: string, out: PathFile[], depth = 0): Promise<void> {
  if (depth > 16 || out.length > MAX_PER_DROP || skipped(entry.name)) return;
  if (entry.isFile) {
    const file = await new Promise<File>((resolve, reject) => (entry as FileSystemFileEntry).file(resolve, reject));
    out.push({ file, dir });
  } else if (entry.isDirectory) {
    const children = await readAll((entry as FileSystemDirectoryEntry).createReader());
    const path = dir ? `${dir}/${entry.name}` : entry.name;
    for (const child of children) await walk(child, path, out, depth + 1);
  }
}

/** Abgelegte Dateien und Ordner (rekursiv, mit relativem Pfad). Muss synchron im `drop`-Ereignis starten. */
export function collectDropped(dt: DataTransfer): Promise<PathFile[]> {
  const entries = Array.from(dt.items ?? [])
    .filter((i) => i.kind === 'file')
    .map((i) => (typeof i.webkitGetAsEntry === 'function' ? i.webkitGetAsEntry() : null));
  if (!entries.length || entries.some((e) => !e)) {
    return Promise.resolve(Array.from(dt.files ?? []).filter((f) => !skipped(f.name)).map((file) => ({ file, dir: '' })));
  }
  return (async () => {
    const out: PathFile[] = [];
    for (const e of entries) if (e) await walk(e, '', out);
    return out;
  })();
}

/** Rückfrage vor dem Schließen, solange noch Dateien warten oder hochgeladen werden (Gespeichertes bleibt). */
export async function confirmAbortUploads(pending: number): Promise<boolean> {
  if (!pending) return true;
  return confirmAsk({
    title: 'Hochladen abbrechen',
    message: `${pending} ${pending === 1 ? 'Datei wird' : 'Dateien werden'} noch hochgeladen. Abbrechen? Bereits gespeicherte Dateien bleiben erhalten.`,
    confirmLabel: 'Abbrechen',
    danger: true,
  });
}

export function hasFiles(e: DragEvent): boolean {
  return Array.from(e.dataTransfer?.types ?? []).includes('Files');
}

export default function MaterialUpload({
  detail,
  folderId,
  incoming,
  onSaved,
  onClose,
  onPendingChange,
}: {
  detail: ChannelDetail;
  folderId: number | null;
  /** von außen abgelegte Dateien (Ablagefläche über der ganzen Materialliste) */
  incoming?: { seq: number; files: PathFile[] } | null;
  onSaved: () => void;
  onClose: () => void;
  /** Anzahl wartender/laufender Dateien (für die Rückfrage beim Schließen über die Werkzeugleiste) */
  onPendingChange?: (pending: number) => void;
}) {
  const ch = detail.channel;
  const ids = useId();
  const [vis, setVis] = useState<VisibilityDraft>(DEFAULT_DRAFT);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const [over, setOver] = useState(false);
  const { fine } = useInputMode();
  const [busy, setBusy] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const dirInput = useRef<HTMLInputElement>(null);
  const controller = useRef<AbortController | null>(null);
  const { limits, reload: reloadLimits } = useFileLimits(PURPOSE);
  const folderName = folderId === null ? 'Oberste Ebene' : detail.folders.find((f) => f.id === folderId)?.name ?? 'Ordner';
  const onSavedRef = useRef(onSaved);
  onSavedRef.current = onSaved;

  useEffect(() => {
    dirInput.current?.setAttribute('webkitdirectory', '');
    dirInput.current?.setAttribute('directory', '');
  }, []);

  const patch = useCallback((key: string, p: Partial<Entry>) => setEntries((list) => list.map((e) => (e.key === key ? { ...e, ...p } : e))), []);

  // Warteschlange: eine Datei nach der anderen hochladen und sofort als Material speichern
  useEffect(() => {
    if (entries.some((e) => e.status === 'uploading' || e.status === 'saving')) return;
    const next = entries.find((e) => e.status === 'waiting');
    if (!next) return;
    const ctl = new AbortController();
    controller.current = ctl;
    const run = async () => {
      let fileId = next.fileId;
      if (!fileId) {
        if (!next.file) throw new Error('Datei fehlt');
        patch(next.key, { status: 'uploading', progress: 0, error: null });
        const info = await uploadFile(next.file, { purpose: PURPOSE, signal: ctl.signal, onProgress: (p) => patch(next.key, { progress: p.fraction }) });
        fileId = info.id;
      }
      patch(next.key, { status: 'saving', fileId, progress: 1 });
      await channelsApi.createFileItems(ch.id, { folder_id: next.folderId, file_ids: [fileId], ...next.vis });
      patch(next.key, { status: 'done', file: null });
    };
    run().catch((e: unknown) => {
      if (isAbortError(e)) {
        setEntries((list) => list.filter((x) => x.key !== next.key));
        return;
      }
      const retry = !(e instanceof ApiError) || e.status === 0 || e.status === 429 || e.status >= 500 || e.status === 409;
      patch(next.key, { status: 'error', error: errorMessage(e), file: retry ? next.file : null });
      if (e instanceof ApiError && e.status === 413) reloadLimits();
    });
  }, [entries, ch.id, patch, reloadLimits]);

  // Material neu laden, sobald die Warteschlange leer ist
  const pending = entries.filter((e) => e.status === 'waiting' || e.status === 'uploading' || e.status === 'saving').length;
  const doneCount = entries.filter((e) => e.status === 'done').length;
  const lastDone = useRef(0);
  useEffect(() => {
    if (!pending && doneCount !== lastDone.current) {
      lastDone.current = doneCount;
      invalidateFileLimits();
      reloadLimits();
      onSavedRef.current();
    }
  }, [pending, doneCount, reloadLimits]);

  useEffect(() => () => controller.current?.abort(), []);

  const onPendingRef = useRef(onPendingChange);
  onPendingRef.current = onPendingChange;
  useEffect(() => {
    onPendingRef.current?.(pending);
    if (!pending) return undefined;
    // Neu laden oder Tab schließen bricht laufende Uploads ab – der Browser fragt nach
    const warn = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [pending]);
  useEffect(() => () => onPendingRef.current?.(0), []);

  const add = useCallback(
    async (files: PathFile[]) => {
      const choice = draftToInput(vis);
      if (typeof choice === 'string') {
        setNotice(choice);
        return;
      }
      const usable = usableFiles(files);
      const skippedCount = files.length - usable.length;
      const taken = usable.slice(0, MAX_PER_DROP);
      const messages: string[] = [];
      if (skippedCount) messages.push(`${skippedCount} Systemdatei${skippedCount === 1 ? '' : 'en'} übersprungen.`);
      if (usable.length > taken.length) messages.push(`Höchstens ${MAX_PER_DROP} Dateien auf einmal – der Rest wurde nicht übernommen.`);
      if (!taken.length) {
        setNotice(messages.join(' ') || null);
        return;
      }
      let map: Record<string, number> = {};
      const dirs = folderPaths(taken);
      if (dirs.length) {
        setBusy(true);
        try {
          map = (await channelsApi.createFolderTree(ch.id, { parent_id: folderId, paths: dirs, ...choice })).folders;
          onSavedRef.current();
        } catch (e) {
          setBusy(false);
          setNotice(errorMessage(e));
          return;
        }
        setBusy(false);
      }
      let pendingBytes = 0;
      const added: Entry[] = taken.map(({ file, dir }) => {
        const problem = precheckFile({ name: file.name, size: file.size }, limits, { pendingBytes });
        if (!problem) pendingBytes += file.size;
        seq += 1;
        return {
          key: `m${seq}`,
          name: file.name || 'Datei',
          dir,
          size: file.size,
          status: problem ? 'error' : 'waiting',
          progress: 0,
          error: problem,
          file: problem ? null : file,
          fileId: null,
          folderId: dir ? (map[dir] ?? folderId) : folderId,
          vis: dir ? { visibility: 'visible' } : choice,
        };
      });
      setEntries((list) => [...list, ...added]);
      setNotice(messages.join(' ') || null);
    },
    [vis, ch.id, folderId, limits],
  );

  const lastIncoming = useRef(0);
  useEffect(() => {
    if (incoming && incoming.seq !== lastIncoming.current) {
      lastIncoming.current = incoming.seq;
      void add(incoming.files);
    }
  }, [incoming, add]);

  const fromInput = (list: FileList | null) => {
    const files = Array.from(list ?? []).map((file) => ({ file, dir: dirOf(file.webkitRelativePath || file.name) }));
    void add(files);
  };

  const close = async () => {
    if (!(await confirmAbortUploads(pending))) return;
    controller.current?.abort();
    onClose();
  };

  const limitText = [limits ? `höchstens ${formatFileSize(limits.max_upload_bytes)} je Datei` : '', allowedKindsText(limits)].filter(Boolean).join(' · ');
  const errors = entries.filter((e) => e.status === 'error').length;

  return (
    <section className="card kr-upload" aria-labelledby={`${ids}-h`}>
      <div className="card-head">
        <h3 id={`${ids}-h`} style={{ margin: 0 }}>
          Hochladen <span className="muted small">→ {folderName}</span>
        </h3>
        <button type="button" className="btn btn-sm btn-ghost" onClick={close}>
          <Icon name="close" /> Schließen
        </button>
      </div>
      <div className="stack-sm">
        <VisibilityPicker channelId={ch.id} kind={ch.kind} value={vis} onChange={setVis} allowLesson={detail.permissions.lessons} />
        <div
          className={`dropzone kr-dropzone${over ? ' over' : ''}`}
          onDragEnter={(e) => {
            if (!hasFiles(e)) return;
            e.preventDefault();
            setOver(true);
          }}
          onDragOver={(e) => {
            if (!hasFiles(e)) return;
            e.preventDefault();
            e.stopPropagation();
            e.dataTransfer.dropEffect = 'copy';
          }}
          onDragLeave={() => setOver(false)}
          onDrop={(e) => {
            if (!hasFiles(e)) return;
            e.preventDefault();
            e.stopPropagation();
            setOver(false);
            void collectDropped(e.dataTransfer)
              .then(add)
              .catch((err: unknown) => setNotice(errorMessage(err)));
          }}
        >
          {fine && <span>Dateien oder Ordner hierher ziehen</span>}
          <div className="row kr-upload-buttons">
            <button type="button" className="btn btn-sm btn-primary" onClick={() => fileInput.current?.click()} disabled={busy}>
              <Icon name="upload" /> Dateien auswählen
            </button>
            <button type="button" className="btn btn-sm" onClick={() => dirInput.current?.click()} disabled={busy}>
              <Icon name="folder" /> Ordner auswählen
            </button>
          </div>
          {limitText && <div className="xsmall">{limitText}</div>}
          <input
            ref={fileInput}
            type="file"
            hidden
            multiple
            accept={limits?.accept}
            onChange={(e) => {
              fromInput(e.target.files);
              e.target.value = '';
            }}
          />
          <input
            ref={dirInput}
            type="file"
            hidden
            multiple
            onChange={(e) => {
              fromInput(e.target.files);
              e.target.value = '';
            }}
          />
        </div>
        {notice && (
          <p className="small" role="status" style={{ color: 'var(--warning)', margin: 0 }}>
            {notice}
          </p>
        )}
        {entries.length > 0 && (
          <>
            <p className="small" aria-live="polite" style={{ margin: 0 }}>
              {doneCount} von {entries.length} gespeichert
              {errors ? ` · ${errors} mit Fehler` : ''}
            </p>
            <ul className="kr-upq" aria-label="Hochgeladene Dateien">
              {entries.map((e) => {
                const pct = Math.round(e.progress * 100);
                return (
                  <li key={e.key} className={`kr-upq-item kr-upq-${e.status}`}>
                    <div className="kr-upq-main">
                      <span className="kr-upq-name">
                        {e.dir ? <span className="muted">{e.dir}/</span> : null}
                        {e.name}
                      </span>
                      <span className="xsmall muted">
                        {formatFileSize(e.size)}
                        {e.status === 'waiting' && ' · wartet'}
                        {e.status === 'uploading' && ` · ${pct} %`}
                        {e.status === 'saving' && ' · wird gespeichert'}
                        {e.status === 'done' && ' · gespeichert'}
                      </span>
                      {e.status === 'error' && e.error && <span className="small kr-error">{e.error}</span>}
                    </div>
                    {e.status === 'uploading' && (
                      <div className="progress" role="progressbar" aria-label={`Fortschritt ${e.name}`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct}>
                        <div className="progress-bar" style={{ width: `${pct}%` }} />
                      </div>
                    )}
                    {e.status === 'done' && <Icon name="check" />}
                    {e.status === 'error' && (e.file || e.fileId) && (
                      <button type="button" className="btn btn-sm" onClick={() => patch(e.key, { status: 'waiting', error: null })}>
                        <Icon name="refresh" /> Erneut<span className="sr-only">: {e.name}</span>
                      </button>
                    )}
                  </li>
                );
              })}
            </ul>
          </>
        )}
      </div>
    </section>
  );
}

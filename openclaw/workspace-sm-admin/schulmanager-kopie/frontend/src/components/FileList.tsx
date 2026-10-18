/**
 * Liste gespeicherter Dateien (Basisdienst §9.2): Name als Download-Link, „Ansehen“ für PDF/Bilder, Größe, Art,
 * Datum, optional Löschen und eigene Aktionen. Rein darstellend – die Dateien (`StoredFileInfo[]`) liefert das
 * Feature (z. B. Anhänge einer Nachricht, Material eines Kursraums, `filesApi.mine()`).
 *
 *   <FileList files={anhaenge} onDelete={(f) => entfernen(f.id)} />
 */
import { useState, type ReactNode } from 'react';
import { fileUrl, formatFileSize, type StoredFileInfo } from '../api/files';
import { errorMessage } from '../api/client';
import { formatDateTime } from '../lib/dates';
import { Icon } from './Icon';
import { confirmAsk } from '../lib/confirm';

/** Strichzeichnungen je Dateigruppe (24×24, wie components/Icon). */
const GLYPHS: Record<string, string> = {
  file: 'M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8zM14 3v5h5',
  document: 'M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8zM14 3v5h5M8 13h8M8 17h5',
  office: 'M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8zM14 3v5h5M8 12h8M8 15h8M8 18h8',
  text: 'M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8zM14 3v5h5M8 13h8M8 17h8',
  image: 'M3 5h18v14H3zM3 16l5-5 4 4 3-3 6 6M15.5 9h.01',
  audio: 'M9 18V5l12-2v13M9 18a3 3 0 1 1-6 0 3 3 0 0 1 6 0zM21 16a3 3 0 1 1-6 0 3 3 0 0 1 6 0z',
  video: 'M3 6h13v12H3zM16 10l5-3v10l-5-3z',
  archive: 'M3 4h18v4H3zM5 8v12h14V8M10 12h4',
};

/** Pfad der Strichzeichnung für eine Datei (Gruppe aus dem Backend, unbekannt → allgemeines Dokument). */
export function fileGlyph(file: Pick<StoredFileInfo, 'group'>): string {
  return GLYPHS[file.group] ?? GLYPHS.file;
}

/** Darf die Datei im Browser angezeigt werden? (PDF/Bilder laut Backend; SVG nie.) */
export function canView(file: Pick<StoredFileInfo, 'inline' | 'kind'>): boolean {
  return file.inline && file.kind !== 'svg';
}

/** Bildvorschau nur für Formate, die alle Browser darstellen (kein HEIC/SVG). */
function canPreview(file: StoredFileInfo): boolean {
  return file.group === 'image' && canView(file) && file.kind !== 'heic';
}

/** „PDF-Dokument · 1,2 MB · 06.10.2026, 08:15“ */
export function fileMetaText(file: StoredFileInfo, opts: { date?: boolean; kind?: boolean } = {}): string {
  const parts: string[] = [];
  if (opts.kind !== false && file.kind_label) parts.push(file.kind_label);
  parts.push(formatFileSize(file.size));
  if (opts.date !== false && file.created_at) parts.push(formatDateTime(file.created_at));
  return parts.join(' · ');
}

export function FileGlyph({ file, size = 28 }: { file: Pick<StoredFileInfo, 'group'>; size?: number }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      style={{ flex: 'none', color: 'var(--primary)' }}
    >
      <path d={fileGlyph(file)} />
    </svg>
  );
}

export interface FileListProps {
  files: readonly StoredFileInfo[];
  /** Löschen-Knopf; erscheint für Dateien mit `can_delete` bzw. wenn `canDelete(file)` true liefert */
  onDelete?: (file: StoredFileInfo) => void | Promise<unknown>;
  canDelete?: (file: StoredFileInfo) => boolean;
  /** Rückfrage vor dem Löschen (Standard: ja) */
  confirmDelete?: boolean;
  /** Beschriftung des Löschen-Knopfs (Standard „Löschen“, z. B. „Entfernen“ für Anhänge) */
  deleteLabel?: string;
  /** zusätzliche Aktionen je Datei (rechts neben „Ansehen“) */
  actions?: (file: StoredFileInfo) => ReactNode;
  /** Text bei leerer Liste; `null` = nichts anzeigen */
  emptyText?: ReactNode;
  /** kompakt: ohne Dateiart/Datum, kleinere Symbole (z. B. Nachrichtenanhänge) */
  compact?: boolean;
  /** kleine Vorschaubilder für Bilder (lädt die Bilder – nur für kurze Listen) */
  previews?: boolean;
  /** Name der Liste für Bildschirmleser */
  label?: string;
}

export function FileList({
  files,
  onDelete,
  canDelete,
  confirmDelete = true,
  deleteLabel = 'Löschen',
  actions,
  emptyText = 'Keine Dateien vorhanden.',
  compact = false,
  previews = false,
  label = 'Dateien',
}: FileListProps) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!files.length) {
    return emptyText === null ? null : <p className="muted small" style={{ margin: 0 }}>{emptyText}</p>;
  }

  const remove = async (file: StoredFileInfo) => {
    if (!onDelete) return;
    if (confirmDelete && !(await confirmAsk({ title: `Datei ${deleteLabel.toLowerCase()}`, message: `„${file.filename}“ wirklich ${deleteLabel.toLowerCase()}?`, confirmLabel: deleteLabel, danger: true }))) return;
    setBusy(file.id);
    setError(null);
    try {
      await onDelete(file);
    } catch (e) {
      setError(`„${file.filename}“: ${errorMessage(e)}`);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div>
      {error && (
        <p role="alert" className="small" style={{ color: 'var(--danger)', margin: '0 0 var(--space-2)' }}>
          {error}
        </p>
      )}
      <ul aria-label={label} style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gap: compact ? 4 : 'var(--space-2)' }}>
        {files.map((f) => {
          const deletable = !!onDelete && (canDelete ? canDelete(f) : f.can_delete);
          return (
            <li
              key={f.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 'var(--space-2) var(--space-3)',
                padding: compact ? '4px 0' : 'var(--space-2) var(--space-3)',
                border: compact ? 0 : '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)',
                background: compact ? 'transparent' : 'var(--surface)',
                minWidth: 0,
              }}
            >
              {previews && canPreview(f) ? (
                <img
                  src={fileUrl(f.id, { inline: true })}
                  alt=""
                  loading="lazy"
                  width={48}
                  height={48}
                  style={{ objectFit: 'cover', borderRadius: 4, flex: 'none', background: 'var(--surface-3)' }}
                />
              ) : (
                <FileGlyph file={f} size={compact ? 20 : 28} />
              )}
              <div style={{ flex: '1 1 12rem', minWidth: 0 }}>
                <a href={fileUrl(f.id)} download={f.filename} style={{ fontWeight: 600, overflowWrap: 'anywhere' }}>
                  {f.filename}
                  <span className="sr-only"> herunterladen ({formatFileSize(f.size)})</span>
                </a>
                <div className="small muted" style={{ overflowWrap: 'anywhere' }}>
                  {fileMetaText(f, { date: !compact, kind: !compact })}
                  {f.scan_status === 'error' && (
                    <span className="badge badge-warning" style={{ marginLeft: 6 }} title="Der Virenscanner war beim Hochladen nicht erreichbar">
                      nicht virengeprüft
                    </span>
                  )}
                </div>
              </div>
              <div className="row" style={{ gap: 4, flex: 'none' }}>
                {canView(f) && (
                  <a className="btn btn-sm btn-ghost" href={fileUrl(f.id, { inline: true })} target="_blank" rel="noopener noreferrer">
                    <Icon name="eye" /> Ansehen<span className="sr-only">: {f.filename} (neues Fenster)</span>
                  </a>
                )}
                {actions?.(f)}
                {deletable && (
                  <button
                    type="button"
                    className="btn btn-sm btn-ghost"
                    onClick={() => void remove(f)}
                    disabled={busy === f.id}
                    aria-label={`${f.filename} ${deleteLabel.toLowerCase()}`}
                    title={deleteLabel}
                  >
                    <Icon name="trash" />
                    {!compact && <span>{deleteLabel}</span>}
                  </button>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default FileList;

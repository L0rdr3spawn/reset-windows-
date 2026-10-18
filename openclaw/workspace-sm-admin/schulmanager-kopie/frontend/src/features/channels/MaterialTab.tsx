/**
 * Bereich „Material“: Ordnerbaum + Liste, Hochladen von Dateien und ganzen Ordnern (Auswahl oder Drag & Drop auf
 * die ganze Liste, sofort als Material gespeichert), Links/Textseiten, Freigaben für Material und Ordner (sofort,
 * verborgen, ab Zeitpunkt, zur nächsten Stunde, zur Unterrichtsstunde), Kopieren in eigene Parallelkurse,
 * Unterrichtsmaterial und „Abgabe möglich“. Teilnehmende/Eltern sehen nur Freigegebenes (filtert der Server); in Klassenräumen ändern Lehrkräfte
 * nur eigenes Material (`can_edit`, außer Klassenleitung/Kursraum-Verwaltung).
 */
import { useMemo, useRef, useState, type DragEvent } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useInputMode } from '../../hooks/useInputMode';
import { ApiError } from '../../api/client';
import { fileUrl, formatFileSize } from '../../api/files';
import { canView, FileList } from '../../components/FileList';
import { Icon } from '../../components/Icon';
import { AsyncButton, Empty } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { formatDate } from '../../lib/dates';
import { channelsApi } from './api';
import { Glyph, NewBadge, StateBadge } from './components';
import { CopyDialog, EditItemDialog, FolderDialog, NewItemDialog, TextViewer, VisibilityDialog } from './dialogs';
import {
  buildFolderTree,
  canEdit,
  childFolders,
  countInFolder,
  dueText,
  folderPath,
  folderVisibilityText,
  formatWhen,
  itemKindLabel,
  itemsIn,
  safeHref,
  visibilityText,
  type FolderNode,
  type PathFile,
} from './logic';
import { progressApi } from './progress';
import MaterialUpload, { collectDropped, confirmAbortUploads, hasFiles } from './MaterialUpload';
import RulesDialog from './RulesDialog';
import type { ChannelDetail, Folder, Item } from './types';
import type { VisibilityDraft } from './VisibilityPicker';
import { confirmAsk } from '../../lib/confirm';

type DialogState =
  | { kind: 'folder'; folder?: Folder }
  | { kind: 'link' | 'text' }
  | { kind: 'edit'; item: Item }
  | { kind: 'visibility'; items: Item[]; folders?: Folder[]; mode?: VisibilityDraft['mode'] }
  | { kind: 'copy'; itemIds: number[]; folderIds: number[] }
  | { kind: 'view'; item: Item }
  | { kind: 'rules'; item: Item }
  | null;

function conflictMessage(e: unknown): string | null {
  if (e instanceof ApiError && e.status === 409 && e.detail && typeof e.detail === 'object' && 'message' in e.detail) {
    return String((e.detail as { message: unknown }).message);
  }
  return null;
}

function FolderTree({
  nodes,
  current,
  onOpen,
  staff,
}: {
  nodes: FolderNode[];
  current: number | null;
  onOpen: (id: number | null) => void;
  staff: boolean;
}) {
  const render = (list: FolderNode[]) => (
    <ul className="kr-tree-list">
      {list.map((n) => (
        <li key={n.id}>
          <button type="button" className={`kr-tree-btn${current === n.id ? ' active' : ''}`} aria-current={current === n.id ? 'true' : undefined} onClick={() => onOpen(n.id)}>
            <Glyph name={current === n.id ? 'folderOpen' : 'folder'} size={18} />
            <span className="kr-tree-name">{n.name}</span>
            {staff && n.hidden_effective && <span className="sr-only"> (nicht freigegeben)</span>}
            {staff && n.state && n.state !== 'visible' && n.state !== 'folder_hidden' && (
              <span className="kr-tree-hidden" title="verborgen" aria-hidden="true">
                <Icon name="lock" />
              </span>
            )}
          </button>
          {n.children.length > 0 && render(n.children)}
        </li>
      ))}
    </ul>
  );
  return (
    <nav aria-label="Ordner" className="kr-tree">
      <button type="button" className={`kr-tree-btn${current === null ? ' active' : ''}`} aria-current={current === null ? 'true' : undefined} onClick={() => onOpen(null)}>
        <Glyph name="room" size={18} />
        <span className="kr-tree-name">Alle Inhalte</span>
      </button>
      {render(nodes)}
    </nav>
  );
}

function ItemRow({
  item,
  detail,
  selected,
  onSelect,
  onAction,
  onOpened,
  onToggle,
}: {
  item: Item;
  detail: ChannelDetail;
  selected: boolean;
  onSelect: (on: boolean) => void;
  onAction: (a: 'view' | 'edit' | 'visibility' | 'lesson' | 'delete' | 'copy' | 'rules') => void;
  onOpened: () => void;
  onToggle: (done: boolean) => void;
}) {
  const perms = detail.permissions;
  const staff = perms.manage || perms.supervise;
  const editable = canEdit(item, perms.manage);
  const meta: string[] = [itemKindLabel(item)];
  if (item.file) meta.push(formatFileSize(item.file.size));
  if (item.type === 'assignment') meta.push(dueText(item.due_at));
  if (item.available_at) meta.push(formatWhen(item.available_at));
  const glyph = item.type === 'file' ? 'file' : item.type;
  const href = item.type === 'link' ? safeHref(item.url) : null;
  const locked = !!item.locked;
  return (
    <li className={`kr-item${(item.state && item.state !== 'visible') || locked ? ' kr-item-muted' : ''}`}>
      {item.completion &&
        (item.completion.can_toggle ? (
          <input type="checkbox" className="kr-item-check" checked={item.completion.done} onChange={(e) => onToggle(e.target.checked)} aria-label={`${item.title} erledigt`} />
        ) : (
          <span className={`kr-done-mark${item.completion.done ? ' is-done' : ''}`} role="img" aria-label={item.completion.done ? 'erledigt' : 'offen'} title={item.completion.mode_label}>
            <Icon name={item.completion.done ? 'checkCircle' : 'clock'} />
          </span>
        ))}
      {perms.manage && (
        <input
          type="checkbox"
          className="kr-item-check"
          checked={selected}
          disabled={!editable}
          onChange={(e) => onSelect(e.target.checked)}
          aria-label={`${item.title} auswählen`}
        />
      )}
      <span className="kr-item-icon">
        <Glyph name={glyph} />
      </span>
      <div className="kr-item-main">
        <div className="kr-item-title">
          {locked ? (
            <span>
              <Icon name="lock" /> {item.title}
            </span>
          ) : item.type === 'file' && item.file ? (
            <a href={fileUrl(item.file.id)} download={item.file.filename} onClick={onOpened}>
              {item.title}
              <span className="sr-only"> herunterladen</span>
            </a>
          ) : item.type === 'link' && href ? (
            <a href={href} target="_blank" rel="noopener noreferrer nofollow" onClick={onOpened}>
              {item.title}
              <span className="sr-only"> (öffnet neues Fenster)</span>
            </a>
          ) : item.type === 'assignment' ? (
            <Link to={`?tab=aufgaben&aufgabe=${item.id}`}>{item.title}</Link>
          ) : (
            <button
              type="button"
              className="kr-linkbtn"
              onClick={() => {
                onOpened();
                onAction('view');
              }}
            >
              {item.title}
            </button>
          )}
          {item.is_new && <NewBadge />}
          {item.lesson_material && (
            <span className="badge badge-info" title="Erscheint unter „Unterricht“">
              Unterricht {item.material_date ? formatDate(item.material_date) : ''}
            </span>
          )}
          {item.type !== 'assignment' && item.submittable && (
            <Link className="badge badge-primary" to={`?tab=aufgaben&aufgabe=${item.id}`}>
              {item.submission ? `Abgabe: ${item.submission.status_label}` : 'Abgabe möglich'}
            </Link>
          )}
          {item.type === 'assignment' && item.submission && <span className="badge">{item.submission.status_label}</span>}
        </div>
        <div className="kr-item-meta">
          {meta.join(' · ')}
          {staff && item.created_by_name && !item.own ? ` · ${item.created_by_name}` : ''}
        </div>
        {locked && <div className="kr-locked-text">Verfügbar, sobald {item.locked_text}</div>}
        {staff && (item.completion_rule || item.availability) && (
          <div className="kr-item-state">
            {item.completion_rule && <span className="badge badge-info">Abschluss: {item.completion_rule.mode_label}</span>}
            {item.availability && (
              <span className="badge badge-warning" title={item.availability.text}>
                Bedingte Freigabe
              </span>
            )}
          </div>
        )}
        {item.type === 'link' && item.url && <div className="kr-item-url">{item.url}</div>}
        {staff && item.state && (
          <div className="kr-item-state">
            <StateBadge state={item.state} label={item.state_label} />
            {visibilityText(item) !== item.state_label && <span className="xsmall muted">{visibilityText(item)}</span>}
          </div>
        )}
        {staff && item.submissions && item.can_grade !== false && (
          <div className="xsmall muted">
            {item.submissions.submitted} von {item.submissions.expected} abgegeben
            {item.submissions.to_grade ? ` · ${item.submissions.to_grade} zu bewerten` : ''}
          </div>
        )}
        {item.type !== 'assignment' && item.attachments.length > 0 && <FileList files={item.attachments} compact label={`Anhänge zu ${item.title}`} />}
      </div>
      <div className="kr-item-actions">
        {!locked && item.type === 'file' && item.file && canView(item.file) && (
          <a className="btn btn-sm btn-ghost" href={fileUrl(item.file.id, { inline: true })} target="_blank" rel="noopener noreferrer" onClick={onOpened}>
            <Icon name="eye" /> <span className="kr-hide-sm">Ansehen</span>
            <span className="sr-only">: {item.title}</span>
          </a>
        )}
        {editable && (
          <>
            <button type="button" className="btn btn-sm" onClick={() => onAction('lesson')} title="Zur Unterrichtsstunde freigeben" hidden={!perms.lessons}>
              <Icon name="calendar" /> <span className="kr-hide-sm">Zur Stunde</span>
              <span className="sr-only">: {item.title} zur Stunde freigeben</span>
            </button>
            <button type="button" className="btn btn-sm btn-ghost" onClick={() => onAction('visibility')} title="Freigabe ändern">
              <Icon name="eye" />
              <span className="sr-only">Freigabe von {item.title} ändern</span>
            </button>
            <button type="button" className="btn btn-sm btn-ghost" onClick={() => onAction('rules')} title="Abschluss &amp; Bedingungen">
              <Icon name="checkCircle" />
              <span className="sr-only">Abschluss und Bedingungen von {item.title}</span>
            </button>
            <button type="button" className="btn btn-sm btn-ghost" onClick={() => onAction('edit')} title="Bearbeiten">
              <Icon name="edit" />
              <span className="sr-only">{item.title} bearbeiten</span>
            </button>
            <button type="button" className="btn btn-sm btn-ghost" onClick={() => onAction('delete')} title="Löschen">
              <Icon name="trash" />
              <span className="sr-only">{item.title} löschen</span>
            </button>
          </>
        )}
      </div>
    </li>
  );
}

export default function MaterialTab({ detail, reload }: { detail: ChannelDetail; reload: () => void }) {
  const ch = detail.channel;
  const perms = detail.permissions;
  const staff = perms.manage || perms.supervise;
  const { fine } = useInputMode();
  const childId = detail.child?.id ?? null;
  const [params, setParams] = useSearchParams();
  const raw = params.get('ordner');
  const folderIds = useMemo(() => new Set(detail.folders.map((f) => f.id)), [detail.folders]);
  const current = raw && folderIds.has(Number(raw)) ? Number(raw) : null;
  const [dialog, setDialog] = useState<DialogState>(null);
  const [upload, setUpload] = useState(false);
  const [incoming, setIncoming] = useState<{ seq: number; files: PathFile[] } | null>(null);
  const uploadPending = useRef(0);
  const [dropOver, setDropOver] = useState(false);
  const dropDepth = useRef(0);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [selectedFolders, setSelectedFolders] = useState<Set<number>>(new Set());
  const toast = useToast();

  const tree = useMemo(() => buildFolderTree(detail.folders), [detail.folders]);
  const path = folderPath(detail.folders, current);
  const subfolders = childFolders(detail.folders, current);
  const items = itemsIn(detail.items, current);
  const currentFolder = path[path.length - 1] ?? null;
  const selectedItems = detail.items.filter((i) => selected.has(i.id));
  const chosenFolders = detail.folders.filter((f) => selectedFolders.has(f.id));
  const selectionCount = selected.size + selectedFolders.size;

  const clearSelection = () => {
    setSelected(new Set());
    setSelectedFolders(new Set());
  };

  const open = (id: number | null) => {
    const next = new URLSearchParams(params);
    if (id === null) next.delete('ordner');
    else next.set('ordner', String(id));
    setParams(next, { replace: true });
    clearSelection();
  };

  const deleteItem = async (item: Item) => {
    if (!(await confirmAsk({ title: 'In den Papierkorb legen', message: `„${item.title}“ in den Papierkorb legen? Es bleibt dort wiederherstellbar.`, confirmLabel: 'In den Papierkorb' }))) return;
    try {
      await channelsApi.deleteItem(ch.id, item.id);
    } catch (e) {
      const msg = conflictMessage(e);
      if (!msg) {
        toast.error(e);
        return;
      }
      if (!(await confirmAsk({ title: 'Verwendet', message: msg, confirmLabel: 'Trotzdem entfernen', danger: true }))) return;
      await channelsApi.deleteItem(ch.id, item.id, true);
    }
    toast.success('In den Papierkorb gelegt');
    reload();
  };

  const deleteFolder = async (f: Folder) => {
    if (!(await confirmAsk({ title: 'In den Papierkorb legen', message: `Ordner „${f.name}“ in den Papierkorb legen? Er bleibt dort wiederherstellbar.`, confirmLabel: 'In den Papierkorb' }))) return;
    try {
      await channelsApi.deleteFolder(ch.id, f.id);
    } catch (e) {
      const msg = conflictMessage(e);
      if (!msg) {
        toast.error(e);
        return;
      }
      if (!(await confirmAsk({ title: 'Verwendet', message: msg, confirmLabel: 'Trotzdem entfernen', danger: true }))) return;
      await channelsApi.deleteFolder(ch.id, f.id, true);
    }
    toast.success('Ordner in den Papierkorb gelegt');
    if (current === f.id) open(f.parent_id);
    reload();
  };

  /** Material geöffnet (Abschlussbedingung „Angesehen“) – nur Teilnehmende zählen. */
  const opened = (item: Item) => () => {
    if (item.completion?.mode !== 'viewed' || item.completion.done || perms.manage || perms.parent || perms.supervise) return;
    channelsApi
      .markViewed(ch.id, item.id)
      .then(reload)
      .catch(() => undefined);
  };
  const toggle = (item: Item) => (done: boolean) => {
    progressApi
      .markDone(ch.id, 'item', item.id, done)
      .then(reload)
      .catch((e: unknown) => toast.error(e));
  };

  const onAction = (item: Item) => (a: 'view' | 'edit' | 'visibility' | 'lesson' | 'delete' | 'copy' | 'rules') => {
    if (a === 'view') setDialog({ kind: 'view', item });
    else if (a === 'rules') setDialog({ kind: 'rules', item });
    else if (a === 'edit') setDialog({ kind: 'edit', item });
    else if (a === 'visibility') setDialog({ kind: 'visibility', items: [item] });
    else if (a === 'lesson') setDialog({ kind: 'visibility', items: [item], mode: 'lesson' });
    else if (a === 'copy') setDialog({ kind: 'copy', itemIds: [item.id], folderIds: [] });
    else void deleteItem(item);
  };

  // Dateien/Ordner auf die ganze Materialliste ziehen → Hochladen in den geöffneten Ordner
  const dropProps = perms.manage
    ? {
        onDragEnter: (e: DragEvent) => {
          if (!hasFiles(e)) return;
          e.preventDefault();
          dropDepth.current += 1;
          setDropOver(true);
        },
        onDragOver: (e: DragEvent) => {
          if (!hasFiles(e)) return;
          e.preventDefault();
          e.dataTransfer.dropEffect = 'copy';
        },
        onDragLeave: () => {
          dropDepth.current = Math.max(0, dropDepth.current - 1);
          if (!dropDepth.current) setDropOver(false);
        },
        onDrop: (e: DragEvent) => {
          if (!hasFiles(e)) return;
          e.preventDefault();
          dropDepth.current = 0;
          setDropOver(false);
          setUpload(true);
          collectDropped(e.dataTransfer)
            .then((files) => setIncoming((prev) => ({ seq: (prev?.seq ?? 0) + 1, files })))
            .catch((err: unknown) => toast.error(err));
        },
      }
    : {};

  const empty = !subfolders.length && !items.length;
  const folderEditable = currentFolder ? canEdit(currentFolder, perms.manage) : false;

  return (
    <div className="kr-material">
      <aside className="kr-side">
        <FolderTree nodes={tree} current={current} onOpen={open} staff={staff} />
      </aside>
      <div className={`kr-main stack-sm${dropOver ? ' kr-drop-over' : ''}`} {...dropProps}>
        <div className="row-between kr-crumbs-row">
          <nav aria-label="Ordnerpfad" className="kr-crumbs">
            <button type="button" className="kr-linkbtn" onClick={() => open(null)} aria-current={current === null ? 'page' : undefined}>
              Alle Inhalte
            </button>
            {path.map((f) => (
              <span key={f.id}>
                <span aria-hidden="true"> › </span>
                <button type="button" className="kr-linkbtn" onClick={() => open(f.id)} aria-current={current === f.id ? 'page' : undefined}>
                  {f.name}
                </button>
              </span>
            ))}
          </nav>
        </div>

        {perms.manage && (
          <div className="kr-toolbar" role="toolbar" aria-label="Material hinzufügen">
            <button
              type="button"
              className="btn btn-sm btn-primary"
              onClick={async () => {
                if (upload && !(await confirmAbortUploads(uploadPending.current))) return;
                if (upload) setIncoming(null);
                setUpload(!upload);
              }}
              aria-expanded={upload}
            >
              <Icon name="upload" /> Hochladen
            </button>
            <button type="button" className="btn btn-sm" onClick={() => setDialog({ kind: 'folder' })}>
              <Icon name="plus" /> Ordner
            </button>
            <button type="button" className="btn btn-sm" onClick={() => setDialog({ kind: 'link' })}>
              <Icon name="link" /> Link
            </button>
            <button type="button" className="btn btn-sm" onClick={() => setDialog({ kind: 'text' })}>
              <Icon name="edit" /> Textseite
            </button>
            {currentFolder && folderEditable && (
              <>
                <button type="button" className="btn btn-sm btn-ghost" onClick={() => setDialog({ kind: 'folder', folder: currentFolder })}>
                  Ordner umbenennen
                </button>
                <button type="button" className="btn btn-sm btn-ghost" onClick={() => setDialog({ kind: 'visibility', items: [], folders: [currentFolder] })}>
                  <Icon name="eye" /> Ordner freigeben …
                </button>
              </>
            )}
          </div>
        )}
        {perms.manage && upload && (
          <MaterialUpload
            detail={detail}
            folderId={current}
            incoming={incoming}
            onSaved={reload}
            onPendingChange={(n) => {
              uploadPending.current = n;
            }}
            onClose={() => {
              // abgelegte Dateien gehören zu diesem Panel – beim nächsten Öffnen nicht noch einmal hochladen
              setIncoming(null);
              setUpload(false);
            }}
          />
        )}
        {staff && currentFolder?.state && currentFolder.state !== 'visible' && (
          <p className="small kr-note">
            <StateBadge state={currentFolder.state} label={currentFolder.state_label} />{' '}
            {folderVisibilityText(currentFolder) !== currentFolder.state_label && folderVisibilityText(currentFolder)}
          </p>
        )}

        {perms.manage && selectionCount > 0 && (
          <div className="kr-bulk" role="region" aria-label="Auswahl">
            <span className="small">
              <strong>{selectionCount}</strong> ausgewählt
            </span>
            <button
              type="button"
              className="btn btn-sm btn-primary"
              onClick={() => setDialog({ kind: 'visibility', items: selectedItems, folders: chosenFolders, mode: 'lesson' })}
              hidden={!perms.lessons}
            >
              <Icon name="calendar" /> Zur Stunde freigeben
            </button>
            <button type="button" className="btn btn-sm" onClick={() => setDialog({ kind: 'visibility', items: selectedItems, folders: chosenFolders })}>
              <Icon name="eye" /> Freigabe …
            </button>
            <button type="button" className="btn btn-sm" onClick={() => setDialog({ kind: 'copy', itemIds: [...selected], folderIds: [...selectedFolders] })}>
              <Icon name="copy" /> Kopieren …
            </button>
            <button type="button" className="btn btn-sm btn-ghost" onClick={clearSelection}>
              Auswahl aufheben
            </button>
          </div>
        )}

        {empty ? (
          <Empty icon="info">
            {current === null
              ? perms.manage
                ? fine
                  ? 'Noch kein Material. Dateien oder Ordner hierher ziehen.'
                  : 'Noch kein Material. Mit „Hochladen“ hinzufügen.'
                : 'Hier ist noch kein Material freigegeben.'
              : 'Dieser Ordner ist leer.'}
          </Empty>
        ) : (
          <ul className="kr-list" aria-label={currentFolder ? `Inhalt von ${currentFolder.name}` : 'Material'}>
            {subfolders.map((f) => {
              const editable = canEdit(f, perms.manage);
              return (
                <li key={`f${f.id}`} className={`kr-item kr-folder${f.hidden_effective ? ' kr-item-muted' : ''}`}>
                  {perms.manage && (
                    <input
                      type="checkbox"
                      className="kr-item-check"
                      checked={selectedFolders.has(f.id)}
                      disabled={!editable}
                      onChange={(e) =>
                        setSelectedFolders((cur) => {
                          const next = new Set(cur);
                          if (e.target.checked) next.add(f.id);
                          else next.delete(f.id);
                          return next;
                        })
                      }
                      aria-label={`Ordner ${f.name} auswählen`}
                    />
                  )}
                  <span className="kr-item-icon">
                    <Glyph name="folder" />
                  </span>
                  <div className="kr-item-main">
                    <div className="kr-item-title">
                      <button type="button" className="kr-linkbtn" onClick={() => open(f.id)}>
                        {f.name}
                      </button>
                    </div>
                    <div className="kr-item-meta">Ordner · {((n) => (n === 1 ? '1 Eintrag' : `${n} Einträge`))(countInFolder(detail.folders, detail.items, f.id))}</div>
                    {staff && f.state && f.state !== 'visible' && (
                      <div className="kr-item-state">
                        <StateBadge state={f.state} label={f.state_label} />
                        {folderVisibilityText(f) !== f.state_label && <span className="xsmall muted">{folderVisibilityText(f)}</span>}
                      </div>
                    )}
                  </div>
                  <div className="kr-item-actions">
                    {editable && (
                      <>
                        <button type="button" className="btn btn-sm btn-ghost" onClick={() => setDialog({ kind: 'visibility', items: [], folders: [f] })} title="Freigabe des Ordners">
                          <Icon name="eye" />
                          <span className="sr-only">Freigabe von {f.name} ändern</span>
                        </button>
                        <button type="button" className="btn btn-sm btn-ghost" onClick={() => setDialog({ kind: 'copy', itemIds: [], folderIds: [f.id] })} title="In anderen Kursraum kopieren">
                          <Icon name="copy" />
                          <span className="sr-only">{f.name} kopieren</span>
                        </button>
                        <button type="button" className="btn btn-sm btn-ghost" onClick={() => setDialog({ kind: 'folder', folder: f })} title="Umbenennen">
                          <Icon name="edit" />
                          <span className="sr-only">{f.name} umbenennen</span>
                        </button>
                        <AsyncButton className="btn btn-sm btn-ghost" onClick={() => deleteFolder(f)} title="Löschen">
                          <Icon name="trash" />
                          <span className="sr-only">{f.name} löschen</span>
                        </AsyncButton>
                      </>
                    )}
                  </div>
                </li>
              );
            })}
            {items.map((item) => (
              <ItemRow
                key={item.id}
                item={item}
                detail={detail}
                selected={selected.has(item.id)}
                onSelect={(on) =>
                  setSelected((cur) => {
                    const next = new Set(cur);
                    if (on) next.add(item.id);
                    else next.delete(item.id);
                    return next;
                  })
                }
                onAction={onAction(item)}
                onOpened={opened(item)}
                onToggle={toggle(item)}
              />
            ))}
          </ul>
        )}
      </div>

      {dialog?.kind === 'folder' && <FolderDialog channelId={ch.id} parentId={current} folder={dialog.folder} onClose={() => setDialog(null)} onDone={reload} />}
      {(dialog?.kind === 'link' || dialog?.kind === 'text') && (
        <NewItemDialog detail={detail} type={dialog.kind} folderId={current} onClose={() => setDialog(null)} onDone={reload} />
      )}
      {dialog?.kind === 'edit' && <EditItemDialog detail={detail} item={dialog.item} onClose={() => setDialog(null)} onDone={reload} />}
      {dialog?.kind === 'visibility' && (
        <VisibilityDialog
          detail={detail}
          items={dialog.items}
          folders={dialog.folders}
          initialMode={dialog.mode}
          onClose={() => setDialog(null)}
          onDone={() => {
            clearSelection();
            reload();
          }}
        />
      )}
      {dialog?.kind === 'copy' && <CopyDialog detail={detail} itemIds={dialog.itemIds} folderIds={dialog.folderIds} onClose={() => setDialog(null)} />}
      {dialog?.kind === 'rules' && <RulesDialog item={dialog.item} onClose={() => setDialog(null)} onDone={reload} />}
      {dialog?.kind === 'view' && <TextViewer channelId={ch.id} item={dialog.item} studentId={childId} onClose={() => setDialog(null)} />}
    </div>
  );
}

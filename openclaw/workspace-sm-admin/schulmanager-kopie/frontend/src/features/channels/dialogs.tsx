/**
 * Dialoge der Kursräume: Ordner anlegen/umbenennen, Link/Textseite anlegen, Material bearbeiten,
 * Sichtbarkeit/„Zur Stunde freigeben“, in anderen eigenen Kursraum kopieren, Textseite ansehen.
 */
import { useState } from 'react';
import { errorMessage } from '../../api/client';
import { FileList } from '../../components/FileList';
import { FileUpload } from '../../components/FileUpload';
import { Modal } from '../../components/Modal';
import { HelpTip } from '../../components/HelpTip';
import { AsyncButton, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { todayISO } from '../../lib/dates';
import { channelsApi } from './api';
import { flattenTree, buildFolderTree, folderVisibilityText, toLocalInput, visibilityText } from './logic';
import { Markdown } from './MarkdownView';
import type { ChannelDetail, Folder, Item, ItemType } from './types';
import { DEFAULT_DRAFT, draftToInput, VisibilityPicker, type VisibilityDraft } from './VisibilityPicker';

function Cancel({ onClose }: { onClose: () => void }) {
  return (
    <button type="button" className="btn" onClick={onClose}>
      Abbrechen
    </button>
  );
}

/** Ordner-Auswahl mit Einrückung (oberste Ebene = leer). */
export function FolderSelect({
  id,
  folders,
  value,
  onChange,
  exclude,
}: {
  id: string;
  folders: readonly Folder[];
  value: number | null;
  onChange: (v: number | null) => void;
  exclude?: Set<number>;
}) {
  const flat = flattenTree(buildFolderTree(folders)).filter((f) => !exclude?.has(f.id));
  return (
    <select id={id} value={value ?? ''} onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}>
      <option value="">Oberste Ebene</option>
      {flat.map((f) => (
        <option key={f.id} value={f.id}>
          {`${'  '.repeat(f.depth)}${f.depth ? '└ ' : ''}${f.name}${f.hidden ? ' (verborgen)' : ''}`}
        </option>
      ))}
    </select>
  );
}

export function FolderDialog({
  channelId,
  parentId,
  folder,
  onClose,
  onDone,
}: {
  channelId: number;
  parentId: number | null;
  folder?: Folder;
  onClose: () => void;
  onDone: () => void;
}) {
  const [name, setName] = useState(folder?.name ?? '');
  const [hidden, setHidden] = useState(folder?.hidden ?? false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const save = async () => {
    if (!name.trim()) {
      setError('Bitte einen Namen angeben.');
      return;
    }
    try {
      if (folder) await channelsApi.patchFolder(channelId, folder.id, { name: name.trim() });
      else await channelsApi.createFolder(channelId, { name: name.trim(), parent_id: parentId, hidden });
      toast.success(folder ? 'Ordner gespeichert' : `Ordner „${name.trim()}“ angelegt`);
      onDone();
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <Modal
      title={folder ? 'Ordner bearbeiten' : 'Neuer Ordner'}
      onClose={onClose}
      footer={
        <>
          <Cancel onClose={onClose} />
          <AsyncButton className="btn btn-primary" onClick={save}>
            {folder ? 'Speichern' : 'Anlegen'}
          </AsyncButton>
        </>
      }
    >
      <form
        className="stack-sm"
        onSubmit={(e) => {
          e.preventDefault();
          void save();
        }}
      >
        <Field label="Name des Ordners" htmlFor="kr-folder-name" error={error}>
          <input id="kr-folder-name" value={name} maxLength={120} onChange={(e) => setName(e.target.value)} autoFocus />
        </Field>
        {!folder && (
          <label className="check">
            <input type="checkbox" checked={hidden} onChange={(e) => setHidden(e.target.checked)} /> Ordner verbergen (samt Inhalt)
          </label>
        )}
      </form>
    </Modal>
  );
}

/** Link oder Textseite anlegen. */
/** Haken „Unterrichtsmaterial“ (mit Datum der Stunde) und „Abgabe möglich“. */
export interface MaterialFlagsValue {
  lessonMaterial: boolean;
  date: string;
  submittable: boolean;
}

export function materialFlagsInput(v: MaterialFlagsValue, withSubmit = true) {
  return {
    lesson_material: v.lessonMaterial,
    material_date: v.lessonMaterial && v.date ? v.date : null,
    ...(withSubmit ? { submittable: v.submittable } : {}),
  };
}

export function materialFlagsOf(item?: Item): MaterialFlagsValue {
  return { lessonMaterial: !!item?.lesson_material, date: item?.material_date ?? todayISO(), submittable: !!(item && item.type !== 'assignment' && item.submittable) };
}

export function MaterialFlags({ value, onChange, withSubmit = true }: { value: MaterialFlagsValue; onChange: (v: MaterialFlagsValue) => void; withSubmit?: boolean }) {
  return (
    <fieldset className="kr-flags">
      <legend className="sr-only">Verwendung</legend>
      <label className="check">
        <input type="checkbox" checked={value.lessonMaterial} onChange={(e) => onChange({ ...value, lessonMaterial: e.target.checked })} /> Unterrichtsmaterial – unter „Unterricht“ bei der
        Stunde zeigen (z. B. für alle, die gefehlt haben)
      </label>
      {value.lessonMaterial && (
        <Field label="Datum der Stunde" htmlFor="kr-flag-date">
          <input id="kr-flag-date" type="date" value={value.date} onChange={(e) => onChange({ ...value, date: e.target.value })} />
        </Field>
      )}
      {withSubmit && (
        <label className="check">
          <input type="checkbox" checked={value.submittable} onChange={(e) => onChange({ ...value, submittable: e.target.checked })} /> Abgabe möglich – Schüler/innen können dazu etwas
          abgeben (erscheint unter „Hausaufgaben“)
        </label>
      )}
    </fieldset>
  );
}

export function NewItemDialog({
  detail,
  type,
  folderId,
  onClose,
  onDone,
}: {
  detail: ChannelDetail;
  type: Extract<ItemType, 'link' | 'text'>;
  folderId: number | null;
  onClose: () => void;
  onDone: () => void;
}) {
  const ch = detail.channel;
  const [title, setTitle] = useState('');
  const [url, setUrl] = useState('https://');
  const [body, setBody] = useState('');
  const [folder, setFolder] = useState<number | null>(folderId);
  const [attachments, setAttachments] = useState<string[]>([]);
  const [vis, setVis] = useState<VisibilityDraft>(DEFAULT_DRAFT);
  const [flags, setFlags] = useState<MaterialFlagsValue>(materialFlagsOf());
  const [preview, setPreview] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const save = async () => {
    const v = draftToInput(vis);
    if (typeof v === 'string') {
      setError(v);
      return;
    }
    try {
      await channelsApi.createItem(ch.id, {
        type,
        title,
        folder_id: folder,
        ...(type === 'link' ? { url } : { body, attachment_ids: attachments }),
        ...materialFlagsInput(flags),
        ...v,
      });
      toast.success(type === 'link' ? 'Link angelegt' : 'Textseite angelegt');
      onDone();
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <Modal
      title={type === 'link' ? 'Link hinzufügen' : 'Textseite anlegen'}
      size="lg"
      onClose={onClose}
      footer={
        <>
          <Cancel onClose={onClose} />
          <AsyncButton className="btn btn-primary" onClick={save}>
            Speichern
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        {error && (
          <p role="alert" className="kr-error">
            {error}
          </p>
        )}
        <div className="form-grid">
          <Field label={type === 'link' ? 'Titel (optional – sonst die Adresse)' : 'Titel'} htmlFor="kr-item-title">
            <input id="kr-item-title" value={title} maxLength={200} onChange={(e) => setTitle(e.target.value)} />
          </Field>
          <Field label="Ordner" htmlFor="kr-item-folder">
            <FolderSelect id="kr-item-folder" folders={detail.folders} value={folder} onChange={setFolder} />
          </Field>
        </div>
        {type === 'link' ? (
          <Field label="Adresse" htmlFor="kr-item-url" hint="Nur http:// oder https://">
            <input id="kr-item-url" type="url" inputMode="url" value={url} maxLength={2000} onChange={(e) => setUrl(e.target.value)} />
          </Field>
        ) : (
          <>
            <div className="field">
              <div className="row-between">
                <label htmlFor="kr-item-body">Text</label>
                <button type="button" className="btn btn-sm btn-ghost" aria-pressed={preview} onClick={() => setPreview((p) => !p)}>
                  {preview ? 'Bearbeiten' : 'Vorschau'}
                </button>
              </div>
              {preview ? (
                <div className="kr-preview">{body.trim() ? <Markdown text={body} /> : <span className="muted small">Noch kein Text.</span>}</div>
              ) : (
                <textarea id="kr-item-body" rows={10} value={body} maxLength={detail.limits.max_body} onChange={(e) => setBody(e.target.value)} />
              )}
              <span className="hint">Formatierung: # Überschrift, **fett**, *kursiv*, - Liste, [Linktext](https://…)</span>
            </div>
            <FileUpload purpose="channel_material" compact label="Anhänge hinzufügen" maxFiles={detail.limits.max_attachments} onChange={(f) => setAttachments(f.map((x) => x.id))} />
          </>
        )}
        <MaterialFlags value={flags} onChange={setFlags} />
        <VisibilityPicker channelId={ch.id} kind={ch.kind} value={vis} onChange={setVis} allowLesson={detail.permissions.lessons} />
      </div>
    </Modal>
  );
}

/** Titel, Ordner, Text/Adresse eines Materials ändern (Sichtbarkeit separat). */
export function EditItemDialog({ detail, item, onClose, onDone }: { detail: ChannelDetail; item: Item; onClose: () => void; onDone: () => void }) {
  const ch = detail.channel;
  const full = useApi<Item>((signal) => channelsApi.item(ch.id, item.id, signal), [ch.id, item.id], { enabled: item.type === 'text' || item.type === 'assignment' });
  const [title, setTitle] = useState(item.title);
  const [folder, setFolder] = useState<number | null>(item.folder_id);
  const [url, setUrl] = useState(item.url ?? '');
  const [body, setBody] = useState<string | null>(null);
  const [flags, setFlags] = useState<MaterialFlagsValue>(materialFlagsOf(item));
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const text = body ?? full.data?.body ?? '';
  const save = async () => {
    try {
      await channelsApi.patchItem(ch.id, item.id, {
        title,
        folder_id: folder,
        ...materialFlagsInput(flags, item.type !== 'assignment'),
        ...(item.type === 'link' ? { url } : {}),
        ...((item.type === 'text' || item.type === 'assignment') && body !== null ? { body } : {}),
      });
      toast.success('Gespeichert');
      onDone();
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <Modal
      title={`${item.type_label} bearbeiten`}
      size="lg"
      onClose={onClose}
      footer={
        <>
          <Cancel onClose={onClose} />
          <AsyncButton className="btn btn-primary" onClick={save} disabled={full.loading && body === null && item.type === 'text'}>
            Speichern
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        {error && (
          <p role="alert" className="kr-error">
            {error}
          </p>
        )}
        <div className="form-grid">
          <Field label="Titel" htmlFor="kr-edit-title">
            <input id="kr-edit-title" value={title} maxLength={200} onChange={(e) => setTitle(e.target.value)} />
          </Field>
          <Field label="Ordner" htmlFor="kr-edit-folder">
            <FolderSelect id="kr-edit-folder" folders={detail.folders} value={folder} onChange={setFolder} />
          </Field>
        </div>
        {item.type === 'link' && (
          <Field label="Adresse" htmlFor="kr-edit-url">
            <input id="kr-edit-url" type="url" value={url} maxLength={2000} onChange={(e) => setUrl(e.target.value)} />
          </Field>
        )}
        {item.type === 'text' && (
          <Field label="Text" htmlFor="kr-edit-body" hint="Formatierung: # Überschrift, **fett**, *kursiv*, - Liste, [Linktext](https://…)">
            {full.initialLoading ? <Loading /> : <textarea id="kr-edit-body" rows={12} value={text} maxLength={detail.limits.max_body} onChange={(e) => setBody(e.target.value)} />}
          </Field>
        )}
        <MaterialFlags value={flags} onChange={setFlags} withSubmit={item.type !== 'assignment'} />
        <p className="small muted" style={{ margin: 0 }}>
          Sichtbarkeit: {visibilityText(item)} – ändern über „Freigabe“.
        </p>
      </div>
    </Modal>
  );
}

/** Sichtbarkeit für ein oder mehrere Materialien setzen – inkl. „Zur Stunde freigeben“. */
export function VisibilityDialog({
  detail,
  items,
  folders = [],
  initialMode,
  onClose,
  onDone,
}: {
  detail: ChannelDetail;
  items: Item[];
  /** ganze Ordner freigeben (Inhalt folgt dem Ordner) */
  folders?: Folder[];
  initialMode?: VisibilityDraft['mode'];
  onClose: () => void;
  onDone: () => void;
}) {
  const ch = detail.channel;
  const first: (Item | Folder) | undefined = items[0] ?? folders[0];
  const [vis, setVis] = useState<VisibilityDraft>(() => ({
    mode: initialMode ?? first?.visibility ?? 'visible',
    from: first?.visibility === 'scheduled' ? toLocalInput(first.visible_from) : '',
    lesson: null,
  }));
  const count = items.length + folders.length;
  const firstName = items[0]?.title ?? folders[0]?.name ?? '';
  const currentText = items[0] ? visibilityText(items[0]) : folders[0]?.state ? folderVisibilityText(folders[0]) : '';
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const apply = async () => {
    const v = draftToInput(vis);
    if (typeof v === 'string') {
      setError(v);
      return;
    }
    try {
      const res = await channelsApi.setVisibility(
        ch.id,
        items.map((i) => i.id),
        v,
        folders.map((f) => f.id),
      );
      const visibleNow = res.items.filter((i) => i.visible).length;
      toast.success(
        vis.mode === 'lesson' && vis.lesson
          ? `${count === 1 ? 'Freigegeben' : `${count} Einträge freigegeben`} zur Stunde ${vis.lesson.label}${visibleNow ? ' – bereits sichtbar' : ''}`
          : 'Sichtbarkeit gespeichert',
      );
      onDone();
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <Modal
      title={vis.mode === 'lesson' ? 'Zur Stunde freigeben' : 'Freigabe festlegen'}
      size="lg"
      onClose={onClose}
      footer={
        <>
          <Cancel onClose={onClose} />
          <AsyncButton className="btn btn-primary" onClick={apply}>
            Übernehmen
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        <p className="small" style={{ margin: 0 }}>
          {count === 1 && first ? (
            <>
              <strong>{firstName}</strong>
              {currentText ? <span className="muted"> – derzeit {currentText}</span> : null}
            </>
          ) : (
            <>
              <strong>{count} Einträge</strong> ausgewählt
            </>
          )}
        </p>
        {error && (
          <p role="alert" className="kr-error">
            {error}
          </p>
        )}
        <VisibilityPicker channelId={ch.id} kind={ch.kind} value={vis} onChange={setVis} allowLesson={detail.permissions.lessons} />
      </div>
    </Modal>
  );
}

/** Material/Ordner in einen anderen eigenen Kursraum kopieren (z. B. Parallelkurs). */
export function CopyDialog({
  detail,
  itemIds,
  folderIds,
  onClose,
}: {
  detail: ChannelDetail;
  itemIds: number[];
  folderIds: number[];
  onClose: () => void;
}) {
  const ch = detail.channel;
  const targets = useApi((signal) => channelsApi.list({}, signal), []);
  const own = (targets.data?.channels ?? []).filter((c) => c.role === 'teacher' && !c.archived && c.id !== ch.id);
  const [target, setTarget] = useState<number | null>(null);
  const [keep, setKeep] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const chosen = target ?? own[0]?.id ?? null;
  const copy = async () => {
    if (!chosen) return;
    try {
      const res = await channelsApi.copy(ch.id, { target_channel_id: chosen, item_ids: itemIds, folder_ids: folderIds, keep_visibility: keep });
      const name = own.find((c) => c.id === chosen)?.title ?? 'Ziel';
      toast.success(`${res.items} Materialien${res.folders ? ` und ${res.folders} Ordner` : ''} nach „${name}“ kopiert`);
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  const n = itemIds.length + folderIds.length;
  return (
    <Modal
      title="In anderen Kursraum kopieren"
      onClose={onClose}
      footer={
        <>
          <Cancel onClose={onClose} />
          <AsyncButton className="btn btn-primary" onClick={copy} disabled={!chosen}>
            Kopieren
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        <p className="small" style={{ margin: 0 }}>
          {n === 1 ? 'Ein Eintrag' : `${n} Einträge`}
          <HelpTip>Ordner werden samt Inhalt kopiert. Dateien werden kopiert, Abgaben nicht.</HelpTip>
        </p>
        {targets.error ? <ErrorBox error={targets.error} onRetry={targets.reload} /> : null}
        {targets.initialLoading && <Loading />}
        {targets.data && !own.length && <p className="small muted">Sie haben keinen weiteren eigenen Kursraum.</p>}
        {own.length > 0 && (
          <Field label="Ziel-Kursraum" htmlFor="kr-copy-target">
            <select id="kr-copy-target" value={chosen ?? ''} onChange={(e) => setTarget(Number(e.target.value))}>
              {own.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                  {c.subtitle ? ` – ${c.subtitle}` : ''}
                </option>
              ))}
            </select>
          </Field>
        )}
        <label className="check">
          <input type="checkbox" checked={keep} onChange={(e) => setKeep(e.target.checked)} /> Sichtbarkeit übernehmen (sonst im Ziel zunächst verborgen; an
          Stunden gebundenes Material immer verborgen)
        </label>
        {error && (
          <p role="alert" className="kr-error">
            {error}
          </p>
        )}
      </div>
    </Modal>
  );
}

/** Textseite lesen (Markdown + Anhänge). */
export function TextViewer({ channelId, item, studentId, onClose }: { channelId: number; item: Item; studentId?: string | null; onClose: () => void }) {
  const q = useApi<Item>((signal) => channelsApi.item(channelId, item.id, signal, studentId), [channelId, item.id, studentId]);
  return (
    <Modal title={item.title} size="lg" onClose={onClose}>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {q.data && (
        <div className="stack-sm">
          {q.data.body ? <Markdown text={q.data.body} /> : <p className="muted">Kein Text.</p>}
          {q.data.attachments.length > 0 && <FileList files={q.data.attachments} label="Anhänge" />}
        </div>
      )}
    </Modal>
  );
}

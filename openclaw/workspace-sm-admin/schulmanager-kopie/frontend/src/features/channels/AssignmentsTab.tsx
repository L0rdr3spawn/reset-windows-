/**
 * Bereich „Aufgaben“: Lehrende legen Aufgaben an (Beschreibung, Frist, Anhänge, Freigabe), sehen alle Abgaben
 * und geben Rückmeldung/Bewertung oder zur Überarbeitung zurück. Schüler/innen geben mit Text + Dateien ab
 * (nur die eigene Abgabe ist sichtbar). Die Aufsicht sieht nur Aufgaben und Zahlen – keine Abgabe-Inhalte.
 */
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import type { StoredFileInfo } from '../../api/files';
import { FileList } from '../../components/FileList';
import { FileUpload } from '../../components/FileUpload';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { AsyncButton, Empty, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { channelsApi } from './api';
import { StateBadge, SubmissionBadge } from './components';
import { FolderSelect, MaterialFlags, materialFlagsInput, materialFlagsOf, VisibilityDialog, type MaterialFlagsValue } from './dialogs';
import { defaultDue, dueText, formatWhen, fromLocalInput, isOpenForStudent, remainingText, toLocalInput, visibilityText } from './logic';
import { Markdown } from './MarkdownView';
import type { ChannelDetail, Item, MySubmissionResponse, SubmissionsResponse } from './types';
import { DEFAULT_DRAFT, draftToInput, VisibilityPicker, type VisibilityDraft } from './VisibilityPicker';
import { GateDialog } from './assign/GateDialog';
import { GradingTable } from './assign/GradingTable';
import { fmtPoints } from './assign/logic';
import { SettingsDialog } from './assign/SettingsDialog';
import { FilledResult, StudentInfo, StudentVersions } from './assign/StudentExtras';
import './assign/aufgaben.css';

function AssignmentDialog({ detail, item, onClose, onDone }: { detail: ChannelDetail; item?: Item; onClose: () => void; onDone: (id: number) => void }) {
  const ch = detail.channel;
  const full = useApi<Item>((signal) => channelsApi.item(ch.id, item!.id, signal), [ch.id, item?.id], { enabled: !!item });
  const [title, setTitle] = useState(item?.title ?? '');
  const [body, setBody] = useState<string | null>(item ? null : '');
  const [due, setDue] = useState(item ? toLocalInput(item.due_at) : defaultDue());
  const [allowLate, setAllowLate] = useState(item?.allow_late ?? true);
  const [folder, setFolder] = useState<number | null>(item?.folder_id ?? null);
  const [kept, setKept] = useState<StoredFileInfo[] | null>(null);
  const [added, setAdded] = useState<string[]>([]);
  const [vis, setVis] = useState<VisibilityDraft>(DEFAULT_DRAFT);
  const [flags, setFlags] = useState<MaterialFlagsValue>(materialFlagsOf(item));
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const text = body ?? full.data?.body ?? '';
  const attachments = kept ?? item?.attachments ?? [];
  const save = async () => {
    if (!title.trim()) {
      setError('Bitte einen Titel angeben.');
      return;
    }
    const dueIso = due ? fromLocalInput(due) : null;
    if (due && !dueIso) {
      setError('Die Frist ist ungültig.');
      return;
    }
    try {
      if (item) {
        await channelsApi.patchItem(ch.id, item.id, {
          title,
          folder_id: folder,
          due_at: dueIso,
          allow_late: allowLate,
          ...materialFlagsInput(flags, false),
          ...(body !== null ? { body } : {}),
          attachment_ids: [...attachments.map((f) => f.id), ...added],
        });
        toast.success('Aufgabe gespeichert');
        onDone(item.id);
      } else {
        const v = draftToInput(vis);
        if (typeof v === 'string') {
          setError(v);
          return;
        }
        const created = await channelsApi.createItem(ch.id, {
          type: 'assignment',
          title,
          body: text,
          folder_id: folder,
          due_at: dueIso,
          allow_late: allowLate,
          attachment_ids: added,
          ...materialFlagsInput(flags, false),
          ...v,
        });
        toast.success('Aufgabe angelegt');
        onDone(created.id);
      }
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <Modal
      title={item ? 'Aufgabe bearbeiten' : 'Neue Aufgabe'}
      size="lg"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={save} disabled={!!item && full.initialLoading}>
            {item ? 'Speichern' : 'Aufgabe anlegen'}
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
        <Field label="Titel" htmlFor="kr-task-title">
          <input id="kr-task-title" value={title} maxLength={200} onChange={(e) => setTitle(e.target.value)} />
        </Field>
        <Field label="Aufgabenstellung" htmlFor="kr-task-body" hint="Formatierung: # Überschrift, **fett**, *kursiv*, - Liste, [Linktext](https://…)">
          {item && full.initialLoading ? (
            <Loading />
          ) : (
            <textarea id="kr-task-body" rows={8} value={text} maxLength={detail.limits.max_body} onChange={(e) => setBody(e.target.value)} />
          )}
        </Field>
        <div className="form-grid">
          <Field label="Abgabe bis" htmlFor="kr-task-due" hint="leer = ohne Frist">
            <input id="kr-task-due" type="datetime-local" value={due} onChange={(e) => setDue(e.target.value)} />
          </Field>
          <Field label="Ordner" htmlFor="kr-task-folder">
            <FolderSelect id="kr-task-folder" folders={detail.folders} value={folder} onChange={setFolder} />
          </Field>
        </div>
        <label className="check">
          <input type="checkbox" checked={allowLate} onChange={(e) => setAllowLate(e.target.checked)} /> Verspätete Abgabe erlauben (wird markiert)
        </label>
        {attachments.length > 0 && (
          <FileList
            files={attachments}
            label="Anhänge"
            onDelete={(f) => setKept(attachments.filter((x) => x.id !== f.id))}
            canDelete={() => true}
            deleteLabel="Entfernen"
            confirmDelete={false}
          />
        )}
        <FileUpload purpose="channel_material" compact label="Anhänge hinzufügen" maxFiles={detail.limits.max_attachments} onChange={(f) => setAdded(f.map((x) => x.id))} />
        <MaterialFlags value={flags} onChange={setFlags} withSubmit={false} />
        {!item && <VisibilityPicker channelId={ch.id} kind={ch.kind} value={vis} onChange={setVis} allowLesson={detail.permissions.lessons} />}
      </div>
    </Modal>
  );
}

function TeacherAssignment({ detail, item, onBack, onEdit, onRelease }: { detail: ChannelDetail; item: Item; onBack: () => void; onEdit: () => void; onRelease: () => void }) {
  const ch = detail.channel;
  const q = useApi<SubmissionsResponse>((signal) => channelsApi.submissions(ch.id, item.id, signal), [ch.id, item.id], { live: [`channel:${ch.id}:`] });
  const body = useApi<Item>((signal) => channelsApi.item(ch.id, item.id, signal), [ch.id, item.id, item.updated_at]);
  const [dialog, setDialog] = useState<'settings' | 'gate' | null>(null);
  const settings = q.data?.settings;
  return (
    <div className="stack-sm">
      <button type="button" className="btn btn-sm btn-ghost" onClick={onBack}>
        <Icon name="chevronLeft" /> Alle Aufgaben
      </button>
      <section className="card stack-sm" aria-labelledby="kr-task-h">
        <div className="row-between">
          <h2 id="kr-task-h" style={{ margin: 0, overflowWrap: 'anywhere' }}>
            {item.title}
          </h2>
          {detail.permissions.manage && (
            <div className="row">
              <button type="button" className="btn btn-sm" onClick={onRelease}>
                <Icon name="eye" /> Freigabe
              </button>
              <button type="button" className="btn btn-sm" onClick={() => setDialog('gate')}>
                <Icon name="users" /> Gruppen
              </button>
              <button type="button" className="btn btn-sm" onClick={() => setDialog('settings')} disabled={!settings}>
                <Icon name="cog" /> Bewertung
              </button>
              <button type="button" className="btn btn-sm" onClick={onEdit}>
                <Icon name="edit" /> Bearbeiten
              </button>
            </div>
          )}
        </div>
        <div className="row small">
          <span>
            <Icon name="clock" /> {dueText(item.due_at)}
          </span>
          {item.created_at && <span className="muted">gestellt {formatWhen(item.created_at)}</span>}
          {item.due_at && <span className="badge">{item.allow_late ? 'späte Abgabe möglich (wird markiert)' : 'keine verspätete Abgabe'}</span>}
          <StateBadge state={item.state} label={item.state_label} />
          <span className="muted xsmall">{visibilityText(item)}</span>
        </div>
        {settings && (settings.rubric || settings.max_points || settings.group_mode) && (
          <div className="row small">
            {settings.rubric && (
              <span className="badge badge-primary">
                {settings.rubric.kind === 'guide' ? 'Leitfaden' : 'Raster'}
                {settings.rubric_title ? `: ${settings.rubric_title}` : ''} · {fmtPoints(settings.max_points)} P.
              </span>
            )}
            {!settings.rubric && settings.max_points ? <span className="badge badge-primary">{fmtPoints(settings.max_points)} Punkte</span> : null}
            {settings.group_mode && <span className="badge badge-info">Gruppenabgabe</span>}
          </div>
        )}
        {body.data?.body ? <Markdown text={body.data.body} /> : body.initialLoading ? <Loading /> : null}
        {item.attachments.length > 0 && <FileList files={item.attachments} label="Anhänge" />}
      </section>

      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {q.data && <GradingTable channelId={ch.id} item={item} data={q.data} reload={q.reload} />}
      {dialog === 'settings' && settings && <SettingsDialog channelId={ch.id} item={item} settings={settings} onClose={() => setDialog(null)} onDone={q.reload} />}
      {dialog === 'gate' && <GateDialog channelId={ch.id} target={{ kind: 'item', id: item.id, title: item.title }} onClose={() => setDialog(null)} />}
    </div>
  );
}

function StudentAssignment({ detail, item, onBack }: { detail: ChannelDetail; item: Item; onBack: () => void }) {
  const ch = detail.channel;
  const childId = detail.child?.id ?? null;
  const full = useApi<Item>((signal) => channelsApi.item(ch.id, item.id, signal, childId), [ch.id, item.id, item.updated_at, childId]);
  const mine = useApi<MySubmissionResponse>((signal) => channelsApi.mySubmission(ch.id, item.id, signal, childId), [ch.id, item.id, childId], {
    live: [`channel:${ch.id}:`],
  });
  const sub = mine.data?.submission ?? null;
  // Abschlussbedingung „Angesehen“: Aufgabe geöffnet (nur eigene Ansicht, nicht die der Eltern)
  useEffect(() => {
    if (!childId) channelsApi.markViewed(ch.id, item.id).catch(() => undefined);
  }, [ch.id, item.id, childId]);
  const [text, setText] = useState<string | null>(null);
  const [kept, setKept] = useState<StoredFileInfo[] | null>(null);
  const [added, setAdded] = useState<string[]>([]);
  const [round, setRound] = useState(0);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const value = text ?? sub?.text ?? '';
  const files = kept ?? sub?.files ?? [];
  const showForm = !!mine.data?.can_submit && (!sub || editing || sub.status === 'zurueckgegeben');
  const submit = async () => {
    try {
      await channelsApi.submit(ch.id, item.id, { text: value, file_ids: [...files.map((f) => f.id), ...added] });
      toast.success(sub ? 'Abgabe aktualisiert' : 'Abgegeben');
      setText(null);
      setKept(null);
      setAdded([]);
      setRound((r) => r + 1);
      setEditing(false);
      setError(null);
      mine.reload();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  const withdraw = async () => {
    try {
      await channelsApi.withdraw(ch.id, item.id);
      toast.success('Abgabe zurückgezogen');
      setText(null);
      setKept(null);
      mine.reload();
    } catch (e) {
      toast.error(e);
    }
  };
  const dueIso = mine.data?.effective_due_at ?? item.due_at;
  const remaining = remainingText(dueIso);
  return (
    <div className="stack-sm">
      <button type="button" className="btn btn-sm btn-ghost" onClick={onBack}>
        <Icon name="chevronLeft" /> Alle Aufgaben
      </button>
      <section className="card stack-sm" aria-labelledby="kr-task-h">
        <h2 id="kr-task-h" style={{ margin: 0, overflowWrap: 'anywhere' }}>
          {item.title}
        </h2>
        <div className="row small">
          <span>
            <Icon name="clock" /> {dueText(dueIso)}
          </span>
          {item.created_at && <span className="muted">gestellt {formatWhen(item.created_at)}</span>}
          {remaining && <span className="badge badge-info">{remaining}</span>}
          {mine.data && <SubmissionBadge status={mine.data.status} label={mine.data.status_label} />}
        </div>
        {full.error ? <ErrorBox error={full.error} onRetry={full.reload} /> : null}
        {full.data?.body ? <Markdown text={full.data.body} /> : full.initialLoading ? <Loading /> : null}
        {item.attachments.length > 0 && <FileList files={item.attachments} label="Material zur Aufgabe" />}
      </section>

      {mine.error ? <ErrorBox error={mine.error} onRetry={mine.reload} /> : null}
      {mine.data && <StudentInfo data={mine.data} />}
      {sub && (sub.feedback || sub.grade || sub.points !== null || sub.rubric || sub.feedback_files.length > 0) && (
        <section className="card kr-feedback-card stack-sm" aria-labelledby="kr-fb-h">
          <h3 id="kr-fb-h" style={{ margin: 0 }}>
            Rückmeldung{sub.feedback_by_name ? ` von ${sub.feedback_by_name}` : ''}
          </h3>
          <div className="xsmall muted">{formatWhen(sub.feedback_at)}</div>
          {sub.grade && (
            <p style={{ margin: 0 }}>
              Bewertung: <strong>{sub.grade}</strong>
            </p>
          )}
          {mine.data && <FilledResult sub={sub} settings={mine.data.settings} />}
          {sub.feedback && <div className="kr-subtext">{sub.feedback}</div>}
          {sub.feedback_files.length > 0 && <FileList files={sub.feedback_files} label="Dateien zur Rückmeldung" />}
        </section>
      )}
      {sub && !showForm && (
        <section className="card stack-sm" aria-labelledby="kr-mine-h">
          <div className="row-between">
            <h3 id="kr-mine-h" style={{ margin: 0 }}>
              {detail.child ? `Abgabe von ${detail.child.name}` : 'Meine Abgabe'}
            </h3>
            <span className="xsmall muted">{formatWhen(sub.submitted_at)}</span>
          </div>
          {sub.text ? <div className="kr-subtext">{sub.text}</div> : null}
          {sub.files.length > 0 && <FileList files={sub.files} label="Meine Dateien" />}
          {mine.data && <StudentVersions sub={sub} settings={mine.data.settings} />}
          {sub.can_edit && mine.data?.can_submit && (
            <div className="row-end">
              {sub.attempt <= 1 && (
                <AsyncButton className="btn btn-ghost" confirm={mine.data?.group ? 'Abgabe der ganzen Gruppe wirklich zurückziehen? Die Dateien werden gelöscht.' : 'Abgabe wirklich zurückziehen? Die Dateien werden gelöscht.'} onClick={withdraw}>
                  <Icon name="trash" /> Zurückziehen
                </AsyncButton>
              )}
              <button type="button" className="btn" onClick={() => setEditing(true)}>
                <Icon name="edit" /> Abgabe ändern
              </button>
            </div>
          )}
        </section>
      )}
      {mine.data && !mine.data.can_submit && !sub && (
        <p className="small muted">
          {detail.channel.archived ? 'Der Kursraum ist archiviert.' : mine.data.needs_group ? 'Eine Abgabe ist erst möglich, wenn Sie einer Gruppe zugeordnet sind.' : 'Die Abgabefrist ist abgelaufen – eine Abgabe ist nicht mehr möglich.'}
        </p>
      )}
      {showForm && (
        <section className="card stack-sm" aria-labelledby="kr-submit-h">
          <h3 id="kr-submit-h" style={{ margin: 0 }}>
            {sub ? 'Abgabe überarbeiten' : 'Abgeben'}
          </h3>
          <Field label="Text" htmlFor="kr-submit-text">
            <textarea id="kr-submit-text" rows={6} value={value} maxLength={detail.limits.max_submission_text} onChange={(e) => setText(e.target.value)} />
          </Field>
          {files.length > 0 && (
            <FileList files={files} label="Bereits abgegebene Dateien" onDelete={(f) => setKept(files.filter((x) => x.id !== f.id))} canDelete={() => true} deleteLabel="Entfernen" confirmDelete={false} />
          )}
          <FileUpload key={round} purpose="submission" label="Dateien anhängen" maxFiles={detail.limits.max_attachments} onChange={(f) => setAdded(f.map((x) => x.id))} />
          {error && (
            <p role="alert" className="kr-error">
              {error}
            </p>
          )}
          <div className="row-end">
            {editing && (
              <button type="button" className="btn" onClick={() => setEditing(false)}>
                Abbrechen
              </button>
            )}
            <AsyncButton className="btn btn-primary" onClick={submit} disabled={!value.trim() && !files.length && !added.length}>
              <Icon name="upload" /> {sub ? 'Erneut abgeben' : 'Abgeben'}
            </AsyncButton>
          </div>
        </section>
      )}
    </div>
  );
}

export default function AssignmentsTab({ detail, reload }: { detail: ChannelDetail; reload: () => void }) {
  const [params, setParams] = useSearchParams();
  const perms = detail.permissions;
  const ch = detail.channel;
  const [dialog, setDialog] = useState<{ kind: 'create' } | { kind: 'edit'; item: Item } | { kind: 'release'; item: Item } | null>(null);
  const assignments = useMemo(
    () =>
      detail.items
        .filter((i) => i.type === 'assignment' || i.submittable)
        .sort((a, b) => (a.due_at ?? '9999').localeCompare(b.due_at ?? '9999') || a.title.localeCompare(b.title, 'de')),
    [detail.items],
  );
  const selectedId = Number(params.get('aufgabe')) || null;
  const selected = assignments.find((a) => a.id === selectedId) ?? null;
  const select = (id: number | null) => {
    const next = new URLSearchParams(params);
    next.set('tab', 'aufgaben');
    if (id === null) next.delete('aufgabe');
    else next.set('aufgabe', String(id));
    setParams(next);
  };
  const now = new Date().toISOString();
  const dialogs = (
    <>
      {dialog?.kind === 'create' && (
        <AssignmentDialog
          detail={detail}
          onClose={() => setDialog(null)}
          onDone={(id) => {
            reload();
            select(id);
          }}
        />
      )}
      {dialog?.kind === 'edit' && <AssignmentDialog detail={detail} item={dialog.item} onClose={() => setDialog(null)} onDone={() => reload()} />}
      {dialog?.kind === 'release' && <VisibilityDialog detail={detail} items={[dialog.item]} onClose={() => setDialog(null)} onDone={reload} />}
    </>
  );

  if (selectedId && !selected) {
    return (
      <div className="stack-sm">
        <p className="small muted">Diese Aufgabe gibt es nicht (mehr) oder sie ist noch nicht freigegeben.</p>
        <button type="button" className="btn btn-sm" onClick={() => select(null)}>
          Alle Aufgaben
        </button>
      </div>
    );
  }
  if (selected) {
    return (
      <>
        {ch.role === 'student' || ch.role === 'parent' ? (
          <StudentAssignment detail={detail} item={selected} onBack={() => select(null)} />
        ) : perms.view_submissions && selected.can_grade !== false ? (
          <TeacherAssignment
            detail={detail}
            item={selected}
            onBack={() => select(null)}
            onEdit={() => setDialog({ kind: 'edit', item: selected })}
            onRelease={() => setDialog({ kind: 'release', item: selected })}
          />
        ) : (
          <div className="stack-sm">
            <button type="button" className="btn btn-sm btn-ghost" onClick={() => select(null)}>
              <Icon name="chevronLeft" /> Alle Aufgaben
            </button>
            <section className="card stack-sm">
              <h2 style={{ margin: 0 }}>{selected.title}</h2>
              <p className="small" style={{ margin: 0 }}>
                {dueText(selected.due_at)}
                {selected.created_at ? ` · gestellt ${formatWhen(selected.created_at)}` : ''} · {visibilityText(selected)}
              </p>
              {selected.submissions && (
                <p className="small muted" style={{ margin: 0 }}>
                  {selected.submissions.submitted} von {selected.submissions.expected} abgegeben
                </p>
              )}
              {selected.can_grade === false && (
                <p className="small muted" style={{ margin: 0 }}>
                  Abgaben: bei {selected.created_by_name || 'der Lehrkraft, die die Aufgabe gestellt hat'}
                </p>
              )}
            </section>
          </div>
        )}
        {dialogs}
      </>
    );
  }

  return (
    <div className="stack-sm">
      {perms.manage && (
        <div className="kr-toolbar">
          <button type="button" className="btn btn-sm btn-primary" onClick={() => setDialog({ kind: 'create' })}>
            <Icon name="plus" /> Neue Aufgabe
          </button>
        </div>
      )}
      {!assignments.length ? (
        <Empty icon="exam">{perms.manage ? 'Noch keine Aufgaben. Legen Sie eine Aufgabe mit Frist an – Abgaben erscheinen hier.' : 'Zurzeit gibt es keine Aufgaben.'}</Empty>
      ) : (
        <ul className="kr-list" aria-label="Aufgaben">
          {assignments.map((a) => {
            const overdue = !!a.due_at && a.due_at < now;
            return (
              <li key={a.id} className={`kr-item${a.state && a.state !== 'visible' ? ' kr-item-muted' : ''}`}>
                <span className="kr-item-icon" aria-hidden="true">
                  <Icon name="exam" />
                </span>
                <div className="kr-item-main">
                  <div className="kr-item-title">
                    {a.locked ? (
                      <span>
                        <Icon name="lock" /> {a.title}
                      </span>
                    ) : (
                      <button type="button" className="kr-linkbtn" onClick={() => select(a.id)}>
                        {a.title}
                      </button>
                    )}
                    {a.is_new && <span className="badge badge-info">neu</span>}
                    {a.completion?.done && <span className="badge badge-success">erledigt</span>}
                  </div>
                  {a.locked && <div className="kr-locked-text">Verfügbar, sobald {a.locked_text}</div>}
                  <div className={`kr-item-meta${overdue ? ' kr-overdue' : ''}`}>{dueText(a.due_at)}</div>
                  {a.submission && (
                    <div className="row" style={{ gap: 6 }}>
                      <SubmissionBadge status={a.submission.status} label={a.submission.status_label} />
                      {a.submission.has_feedback && <span className="badge badge-primary">Rückmeldung</span>}
                      {isOpenForStudent(a.submission.status) && remainingText(a.due_at) && <span className="xsmall muted">{remainingText(a.due_at)}</span>}
                    </div>
                  )}
                  {a.submissions && (
                    <div className="row" style={{ gap: 6 }}>
                      <span className="xsmall">
                        {a.submissions.submitted}/{a.submissions.expected} abgegeben
                      </span>
                      {a.submissions.to_grade > 0 && <span className="badge badge-warning">{a.submissions.to_grade} zu bewerten</span>}
                      <StateBadge state={a.state} label={a.state_label} />
                    </div>
                  )}
                </div>
                <div className="kr-item-actions">
                  <button type="button" className="btn btn-sm" onClick={() => select(a.id)} hidden={!!a.locked}>
                    {ch.role === 'student'
                      ? a.submission && !isOpenForStudent(a.submission.status)
                        ? 'Ansehen'
                        : 'Bearbeiten'
                      : ch.role === 'parent' || a.can_grade === false || !perms.view_submissions
                        ? 'Ansehen'
                        : 'Abgaben'}
                    <span className="sr-only">: {a.title}</span>
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
      {dialogs}
    </div>
  );
}

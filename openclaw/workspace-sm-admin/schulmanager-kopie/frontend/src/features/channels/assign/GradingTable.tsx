/**
 * Bewertungsübersicht einer Aufgabe: Tabelle Schüler/in × Status (abgegeben, verspätet, fehlt, bewertet) mit Punkten,
 * Note, Gruppe und Frist; je Zeile Bewerten (Raster/Punkte/Note), Überarbeitung anfordern und Frist verlängern.
 */
import { useMemo, useState } from 'react';
import { errorMessage } from '../../../api/client';
import type { StoredFileInfo } from '../../../api/files';
import { Abbr } from '../../../components/Abbr';
import { FileList } from '../../../components/FileList';
import { FileUpload } from '../../../components/FileUpload';
import { Icon } from '../../../components/Icon';
import { Modal } from '../../../components/Modal';
import { AsyncButton, Field, SegmentedControl } from '../../../components/ui';
import { useToast } from '../../../context/ToastContext';
import { channelsApi } from '../api';
import { formatWhen, fromLocalInput, toneClass } from '../logic';
import type { Item, SubmissionRow, SubmissionsResponse } from '../types';
import { ExtensionDialog, type ExtensionTarget } from './ExtensionDialog';
import { extendedDue, fmtPoints, gradeFor, matchesFilter, parsePoints, percentText, resultText, rowStatus, rubricTotal, type TableFilter } from './logic';
import { RubricGrader, RubricView } from './RubricGrader';
import type { AssignSettings, RubricFill, SubmissionVersion } from './types';
import './aufgaben.css';

export function VersionList({ versions, settings }: { versions: SubmissionVersion[]; settings: AssignSettings }) {
  if (!versions.length) return null;
  return (
    <details className="au-versions">
      <summary>Frühere Versionen ({versions.length})</summary>
      <ol className="stack-sm">
        {[...versions].reverse().map((v) => (
          <li key={v.attempt} className="au-version">
            <div className="small">
              <strong>Version {v.attempt}</strong> · abgegeben {formatWhen(v.submitted_at)}
            </div>
            {v.text && <div className="kr-subtext">{v.text}</div>}
            {v.files.length > 0 && <FileList files={v.files} label={`Dateien der Version ${v.attempt}`} compact />}
            {(v.feedback || v.grade || v.points !== null) && (
              <div className="small">
                <strong>Rückmeldung{v.feedback_by_name ? ` von ${v.feedback_by_name}` : ''}</strong>
                {v.grade ? ` · Note ${v.grade}` : ''}
                {v.points !== null ? ` · ${fmtPoints(v.points)} / ${fmtPoints(v.max_points)} P.` : ''}
                {v.feedback && <div className="kr-subtext">{v.feedback}</div>}
                {v.rubric && settings.rubric && <RubricView rubric={settings.rubric} fill={v.rubric} />}
              </div>
            )}
          </li>
        ))}
      </ol>
    </details>
  );
}

function RevisionDialog({ name, dueIso, allowLate, onClose, onConfirm }: { name: string; dueIso: string | null; allowLate: boolean; onClose: () => void; onConfirm: (dueIso: string | null) => Promise<void> }) {
  const [due, setDue] = useState('');
  const [error, setError] = useState<string | null>(null);
  const go = async () => {
    const iso = due ? fromLocalInput(due) : null;
    if (due && !iso) {
      setError('Die Frist ist ungültig.');
      return;
    }
    try {
      await onConfirm(iso);
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <Modal
      title={`Überarbeitung anfordern – ${name}`}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={go}>
            Überarbeitung anfordern
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
        <Field
          label="Neue Frist (optional)"
          htmlFor="au-rev-due"
          help={`Die bisherige Abgabe bleibt mit Ihrer Rückmeldung als Version erhalten, ${name} kann eine neue Version abgeben. ${
            !allowLate && dueIso ? 'Späte Abgaben sind gesperrt: Ohne neue Frist ist nach Fristende keine Abgabe möglich.' : 'Leer = keine Frist für die Überarbeitung.'
          }`}
        >
          <input id="au-rev-due" type="datetime-local" value={due} onChange={(e) => setDue(e.target.value)} />
        </Field>
        <button type="button" className="btn btn-sm" onClick={() => setDue(extendedDue(null, 7))}>
          + 1 Woche
        </button>
      </div>
    </Modal>
  );
}

function FeedbackForm({ channelId, item, row, settings, onSaved }: { channelId: number; item: Item; row: SubmissionRow; settings: AssignSettings; onSaved: () => void }) {
  const sub = row.submission!;
  const rubric = settings.rubric;
  const [feedback, setFeedback] = useState(sub.feedback);
  const [grade, setGrade] = useState(sub.grade);
  const [gradeTouched, setGradeTouched] = useState(!!sub.grade);
  const [fill, setFill] = useState<RubricFill>(sub.rubric ?? {});
  const [points, setPoints] = useState(sub.points !== null && !rubric ? fmtPoints(sub.points) : '');
  const [scope, setScope] = useState<'group' | 'self'>('group');
  const [overwrite, setOverwrite] = useState(false);
  const [kept, setKept] = useState<StoredFileInfo[]>(sub.feedback_files);
  const [added, setAdded] = useState<string[]>([]);
  const [round, setRound] = useState(0);
  const [revision, setRevision] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const isGroup = !!sub.group_id && !!row.group;
  const total = rubric ? rubricTotal(rubric, fill) : null;
  const numPoints = rubric ? (total && total.done ? total.points : null) : parsePoints(points);
  const suggestion = gradeFor(numPoints, settings.max_points, settings.scale_steps);
  const shownGrade = gradeTouched ? grade : (suggestion ?? grade);
  const fid = `kr-fb-${sub.id}`;

  const body = (status: 'bewertet' | 'zurueckgegeben', revisionDue?: string | null) => ({
    feedback,
    grade: shownGrade,
    status,
    file_ids: [...kept.map((f) => f.id), ...added],
    ...(rubric ? { rubric: Object.keys(fill).length ? fill : null } : numPoints !== null ? { points: numPoints } : {}),
    ...(isGroup ? { scope, overwrite_individual: scope === 'group' && overwrite } : {}),
    ...(status === 'zurueckgegeben' ? { revision_due_at: revisionDue ?? null } : {}),
    auto_grade: !gradeTouched,
  });
  const save = async (status: 'bewertet' | 'zurueckgegeben', revisionDue?: string | null) => {
    try {
      await channelsApi.feedback(channelId, sub.id, body(status, revisionDue));
      toast.success(status === 'bewertet' ? `Bewertung für ${row.name} gespeichert` : `${row.name}: Überarbeitung angefordert`);
      setAdded([]);
      setRound((r) => r + 1);
      setError(null);
      onSaved();
    } catch (e) {
      setError(errorMessage(e));
      throw e;
    }
  };
  const submitGrade = async () => {
    try {
      await save('bewertet');
    } catch {
      /* Fehler steht im Formular */
    }
  };
  return (
    <div className="kr-feedback stack-sm">
      <div>
        <div className="small muted">
          Version {sub.attempt} · abgegeben {formatWhen(sub.submitted_at)}
          {row.late ? ' · verspätet' : ''}
          {isGroup ? ` · Gruppe ${row.group!.name}` : ''}
        </div>
        {sub.text ? <div className="kr-subtext">{sub.text}</div> : <p className="small muted">Kein Text.</p>}
        {sub.files.length > 0 && <FileList files={sub.files} label={`Dateien von ${row.name}`} />}
      </div>
      <VersionList versions={sub.versions} settings={settings} />
      {rubric && <RubricGrader rubric={rubric} fill={fill} onChange={setFill} idPrefix={fid} />}
      {!rubric && settings.max_points ? (
        <Field label={`Punkte (von ${fmtPoints(settings.max_points)})`} htmlFor={`${fid}-pts`}>
          <input id={`${fid}-pts`} inputMode="decimal" value={points} onChange={(e) => setPoints(e.target.value)} />
        </Field>
      ) : null}
      <Field label="Rückmeldung" htmlFor={`${fid}-text`}>
        <textarea id={`${fid}-text`} rows={4} value={feedback} onChange={(e) => setFeedback(e.target.value)} />
      </Field>
      <div className="form-grid">
        <Field
          label="Note (optional)"
          htmlFor={`${fid}-grade`}
          hint={suggestion && !gradeTouched ? `Vorschlag aus den Punkten (${percentText(numPoints, settings.max_points)}): ${suggestion}` : 'z. B. „2+“, „12 Punkte“, „erledigt“'}
          hintInline
        >
          <input
            id={`${fid}-grade`}
            value={shownGrade}
            maxLength={30}
            onChange={(e) => {
              setGrade(e.target.value);
              setGradeTouched(true);
            }}
          />
        </Field>
      </div>
      {isGroup && (
        <fieldset className="au-scope">
          <legend className="small">Gilt für</legend>
          <label className="check">
            <input type="radio" name={`${fid}-scope`} checked={scope === 'group'} onChange={() => setScope('group')} /> Die ganze Gruppe „{row.group!.name}“
          </label>
          <label className="check">
            <input type="radio" name={`${fid}-scope`} checked={scope === 'self'} onChange={() => setScope('self')} /> Nur {row.name} (Einzelanpassung)
          </label>
          {scope === 'group' && (
            <label className="check">
              <input type="checkbox" checked={overwrite} onChange={(e) => setOverwrite(e.target.checked)} /> Einzelanpassungen überschreiben
            </label>
          )}
          {sub.individual && <p className="xsmall muted">Für {row.name} gilt zurzeit eine Einzelanpassung.</p>}
        </fieldset>
      )}
      {kept.length > 0 && (
        <FileList files={kept} label="Dateien zur Rückmeldung" compact onDelete={(f) => setKept(kept.filter((x) => x.id !== f.id))} canDelete={() => true} deleteLabel="Entfernen" confirmDelete={false} />
      )}
      <FileUpload key={round} purpose="submission" compact label="Datei zur Rückmeldung anhängen" maxFiles={10} onChange={(f) => setAdded(f.map((x) => x.id))} />
      {error && (
        <p role="alert" className="kr-error">
          {error}
        </p>
      )}
      <div className="row-end">
        <button type="button" className="btn" onClick={() => setRevision(true)}>
          <Icon name="undo" /> Überarbeitung anfordern
        </button>
        <AsyncButton className="btn btn-primary" onClick={submitGrade}>
          <Icon name="check" /> {sub.status === 'bewertet' ? 'Bewertung ändern' : 'Bewertung speichern'}
        </AsyncButton>
      </div>
      {revision && <RevisionDialog name={isGroup && scope === 'group' ? `Gruppe ${row.group!.name}` : row.name} dueIso={row.due_at} allowLate={item.allow_late} onClose={() => setRevision(false)} onConfirm={(d) => save('zurueckgegeben', d)} />}
    </div>
  );
}

export function GradingTable({ channelId, item, data, reload }: { channelId: number; item: Item; data: SubmissionsResponse; reload: () => void }) {
  const [filter, setFilter] = useState<TableFilter>('alle');
  const [openRow, setOpenRow] = useState<string | null>(null);
  const [ext, setExt] = useState<{ target: ExtensionTarget; existing: SubmissionRow['extension']; support: string[] } | null>(null);
  const settings = data.settings;
  const grouped = settings.group_mode;
  const c = data.counts;
  const toGrade = (c.abgegeben ?? 0) + (c.verspaetet ?? 0);
  const missing = (c.offen ?? 0) + (c.ueberfaellig ?? 0);
  const rows = useMemo(() => {
    const list = data.rows.filter((r) => matchesFilter(r, filter));
    if (!grouped) return list;
    return [...list].sort((a, b) => (a.group?.name ?? '￿').localeCompare(b.group?.name ?? '￿', 'de') || a.name.localeCompare(b.name, 'de'));
  }, [data.rows, filter, grouped]);
  const cols = 6 + (grouped ? 1 : 0);
  const hasMax = settings.max_points !== null;
  return (
    <section className="card" aria-labelledby="kr-subs-h">
      <div className="card-head">
        <h3 id="kr-subs-h" style={{ margin: 0 }}>
          Abgaben
        </h3>
        <span className="small muted" aria-live="polite">
          {data.total - missing} von {data.total} abgegeben · {toGrade} zu bewerten · {c.late ?? 0} verspätet
          {grouped && data.without_group > 0 ? ` · ${data.without_group} ohne Gruppe` : ''}
        </span>
      </div>
      <SegmentedControl<TableFilter>
        label="Abgaben filtern"
        value={filter}
        onChange={setFilter}
        options={[
          { value: 'alle', label: 'Alle' },
          { value: 'zu_bewerten', label: `Zu bewerten${toGrade ? ` (${toGrade})` : ''}` },
          { value: 'fehlt', label: 'Fehlt' },
          { value: 'erledigt', label: 'Bewertet' },
        ]}
      />
      {!rows.length && <p className="small muted">Keine Einträge in dieser Auswahl.</p>}
      {rows.length > 0 && (
        <div className="table-wrap">
          <table className="table table-compact au-table">
            <caption className="sr-only">Abgaben der Teilnehmenden mit Status, Ergebnis und Frist</caption>
            <thead>
              <tr>
                <th scope="col">Name</th>
                {grouped && <th scope="col">Gruppe</th>}
                <th scope="col">Status</th>
                <th scope="col">Abgegeben</th>
                <th scope="col">{hasMax ? 'Punkte · Note' : 'Note'}</th>
                <th scope="col">Frist</th>
                <th scope="col">
                  <span className="sr-only">Aktionen</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const key = `${r.user_id ?? r.student_id ?? r.name}`;
                const expanded = openRow === key;
                const st = rowStatus(r);
                return [
                  <tr key={key} className={expanded ? 'selected' : undefined}>
                    <th scope="row" className="au-name">
                      <span className="kr-sub-name">{r.name}</span>
                      <span className="xsmall muted">
                        {r.class_id ? ` · ${r.class_id}` : ''}
                        {!r.has_account ? ' · kein Konto' : ''}
                        {!r.member ? ' · nicht mehr im Kurs' : ''}
                      </span>
                      {r.support.length > 0 && (
                        <>
                          {' '}
                          <Abbr text="NTA" full={`Nachteilsausgleich: ${r.support.join(', ')}`} />
                        </>
                      )}
                    </th>
                    {grouped && <td>{r.group ? r.group.name : <span className="badge badge-warning">ohne Gruppe</span>}</td>}
                    <td>
                      <span className={toneClass(st.tone)}>{st.label}</span>
                      {r.submission && r.submission.attempt > 1 && <span className="xsmall muted"> · Version {r.submission.attempt}</span>}
                    </td>
                    <td className="xsmall">{r.submission?.submitted_at ? formatWhen(r.submission.submitted_at) : '–'}</td>
                    <td>{resultText(r) || '–'}</td>
                    <td className="xsmall">
                      {r.due_at ? formatWhen(r.due_at) : '–'}
                      {r.extension && (
                        <span className="badge badge-info" title={r.extension.reason || undefined}>
                          {r.extension.kind === 'group' ? 'Gruppenfrist' : 'verlängert'}
                        </span>
                      )}
                    </td>
                    <td className="actions">
                      <div className="row" style={{ justifyContent: 'flex-end' }}>
                        {r.submission?.submitted_at && (
                          <button type="button" className="btn btn-sm" aria-expanded={expanded} onClick={() => setOpenRow(expanded ? null : key)}>
                            {expanded ? 'Schließen' : r.status === 'bewertet' ? 'Ansehen' : 'Bewerten'}
                            <span className="sr-only">: Abgabe von {r.name}</span>
                          </button>
                        )}
                        {item.due_at && r.user_id && r.member && (
                          <button
                            type="button"
                            className="btn btn-sm btn-ghost"
                            onClick={() => setExt({ target: { kind: 'user', userId: r.user_id!, name: r.name }, existing: r.extension, support: r.support })}
                            title="Frist verlängern"
                          >
                            <Icon name="clock" />
                            <span className="sr-only">Frist verlängern für {r.name}</span>
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>,
                  expanded && r.submission ? (
                    <tr key={`${key}-fb`}>
                      <td colSpan={cols} className="au-fb-cell">
                        <FeedbackForm
                          channelId={channelId}
                          item={item}
                          row={r}
                          settings={settings}
                          onSaved={() => {
                            setOpenRow(null);
                            reload();
                          }}
                        />
                      </td>
                    </tr>
                  ) : null,
                ];
              })}
            </tbody>
          </table>
        </div>
      )}
      {grouped && data.groups.length > 0 && item.due_at && (
        <div className="au-groupext">
          <span className="small muted">Frist für eine ganze Gruppe verlängern:</span>
          {data.groups.map((g) => (
            <button key={g.id} type="button" className="btn btn-sm" onClick={() => setExt({ target: { kind: 'group', groupId: g.id, name: g.name }, existing: data.extensions.find((e) => e.group_id === g.id) ? { ...data.extensions.find((e) => e.group_id === g.id)!, kind: 'group' } : null, support: [] })}>
              {g.name}
            </button>
          ))}
        </div>
      )}
      {ext && <ExtensionDialog channelId={channelId} item={item} target={ext.target} existing={ext.existing} support={ext.support} onClose={() => setExt(null)} onDone={reload} />}
    </section>
  );
}


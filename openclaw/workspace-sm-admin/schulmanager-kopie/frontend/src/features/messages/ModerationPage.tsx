/**
 * `/nachrichten/moderation` (nur `messages.moderate`): gemeldete Nachrichten prüfen. Die Liste zeigt keine Inhalte;
 * erst „Nachricht anzeigen“ entschlüsselt sie (jede Ansicht steht im Audit-Protokoll). Abschließen mit Vermerk,
 * optional Nachricht ausblenden und Postfach der absendenden Person befristet sperren; Sperren verwalten;
 * Aufbewahrungsfrist sofort anwenden.
 */
import { useEffect, useId, useState } from 'react';
import { Link } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import { FileList } from '../../components/FileList';
import { HelpTip } from '../../components/HelpTip';
import { Alert, AsyncButton, Empty, ErrorBox, Loading, SegmentedControl } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useMediaQuery, useTitle } from '../../hooks/misc';
import { useApi } from '../../hooks/useApi';
import { messagesApi } from './api';
import { Glyph, PersonLine, When } from './components';
import { actionsText, folderPath, fullTime, plural } from './logic';
import type { Report, ReportDetail, ReportList, ReportStatus, Suspension } from './types';
import './messages.css';

type StatusFilter = ReportStatus | 'alle';

function statusClass(s: ReportStatus): string {
  return s === 'offen' ? 'badge badge-warning' : s === 'erledigt' ? 'badge badge-success' : 'badge';
}

function ResolveForm({ report, onDone }: { report: Report; onDone: () => void }) {
  const toast = useToast();
  const ids = { note: useId(), days: useId() };
  const [status, setStatus] = useState<'erledigt' | 'abgelehnt'>('erledigt');
  const [resolution, setResolution] = useState('');
  const [remove, setRemove] = useState(false);
  const [suspend, setSuspend] = useState(false);
  const [days, setDays] = useState(7);
  const submit = async () => {
    try {
      const res = await messagesApi.resolve(report.id, {
        status,
        resolution: resolution.trim(),
        remove_message: status === 'erledigt' && remove,
        suspend_days: status === 'erledigt' && suspend ? days : null,
      });
      toast.success(`Meldung abgeschlossen${res.actions.length ? ` (${actionsText(res.actions)})` : ''}`);
      onDone();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  return (
    <fieldset className="pf-resolve stack-sm">
      <legend>Meldung abschließen</legend>
      <SegmentedControl<'erledigt' | 'abgelehnt'>
        label="Entscheidung"
        value={status}
        onChange={setStatus}
        options={[
          { value: 'erledigt', label: 'Verstoß – erledigt' },
          { value: 'abgelehnt', label: 'Kein Verstoß' },
        ]}
      />
      {status === 'erledigt' && (
        <>
          <label className="check">
            <input type="checkbox" checked={remove} onChange={(e) => setRemove(e.target.checked)} /> Nachricht für alle ausblenden
          </label>
          <div className="pf-suspend-row">
            <label className="check">
              <input type="checkbox" checked={suspend} disabled={!report.sender_id} onChange={(e) => setSuspend(e.target.checked)} /> Postfach von{' '}
              {report.sender.name} für das Senden sperren
            </label>
            {suspend && (
              <span className="pf-days">
                <label htmlFor={ids.days} className="sr-only">
                  Tage
                </label>
                <input id={ids.days} type="number" min={1} max={365} value={days} onChange={(e) => setDays(Math.max(1, Math.min(365, Number(e.target.value) || 1)))} />{' '}
                Tage
              </span>
            )}
          </div>
        </>
      )}
      <div className="field">
        <label htmlFor={ids.note}>Vermerk (nur für die Moderation, verschlüsselt gespeichert)</label>
        <textarea id={ids.note} rows={3} maxLength={2000} value={resolution} onChange={(e) => setResolution(e.target.value)} />
      </div>
      <div>
        <AsyncButton className="btn btn-primary" onClick={submit}>
          Abschließen
        </AsyncButton>
      </div>
    </fieldset>
  );
}

function ReportPanel({ report, onChanged, onBack }: { report: Report; onChanged: () => void; onBack?: () => void }) {
  const toast = useToast();
  const contextId = useId();
  const [context, setContext] = useState(0);
  const [detail, setDetail] = useState<ReportDetail | null>(null);
  useEffect(() => setDetail(null), [report.id]);

  const reveal = async () => {
    try {
      setDetail(await messagesApi.reportDetail(report.id, context));
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  return (
    <article className="card stack-sm pf-report" aria-labelledby={`pf-rep-${report.id}`}>
      {onBack && (
        <button type="button" className="btn btn-ghost btn-sm pf-back" onClick={onBack}>
          <Glyph name="back" size={16} /> Zurück zur Liste
        </button>
      )}
      <h2 id={`pf-rep-${report.id}`}>
        Meldung #{report.id}: {report.category_label}
      </h2>
      <dl className="pf-facts">
        <dt>Status</dt>
        <dd>
          <span className={statusClass(report.status)}>{report.status_label}</span>
          {report.actions.length > 0 && <span className="small"> · {actionsText(report.actions)}</span>}
        </dd>
        <dt>Gemeldet von</dt>
        <dd>
          <PersonLine person={report.reporter} /> <span className="xsmall muted">am {fullTime(report.created_at)}</span>
        </dd>
        <dt>Grund</dt>
        <dd>{report.integrity_ok ? report.reason || <span className="muted">(keine Beschreibung)</span> : <span className="pf-note-warn">beschädigt</span>}</dd>
        <dt>Nachricht von</dt>
        <dd>
          <PersonLine person={report.sender} />
          {report.message_created_at && <span className="xsmall muted"> · gesendet {fullTime(report.message_created_at)}</span>}
        </dd>
        <dt>Unterhaltung</dt>
        <dd>
          {report.conversation_kind_label || '–'}
          {report.reports_on_message > 1 && <span className="small"> · {plural(report.reports_on_message, 'Meldung', 'Meldungen')} zu dieser Nachricht</span>}
          {report.message_removed && <span className="badge"> ausgeblendet</span>}
        </dd>
        {report.status !== 'offen' && (
          <>
            <dt>Bearbeitet</dt>
            <dd>
              {report.handled_by?.name ?? '–'} {report.handled_at && <span className="xsmall muted">am {fullTime(report.handled_at)}</span>}
              {report.resolution && <p className="pf-resolution">{report.resolution}</p>}
            </dd>
          </>
        )}
      </dl>

      {!detail ? (
        <div className="pf-reveal">
          <p className="small" style={{ margin: 0 }}>
            <Glyph name="lock" size={14} /> Der Inhalt ist verschlüsselt. Das Anzeigen wird mit Ihrem Namen protokolliert.
          </p>
          <div className="pf-reveal-row">
            <label htmlFor={contextId} className="small">
              Umfang
            </label>
            <select id={contextId} value={context} onChange={(e) => setContext(Number(e.target.value))}>
              <option value={0}>nur die gemeldete Nachricht</option>
              <option value={2}>mit je 2 Nachrichten davor/danach</option>
              <option value={5}>mit je 5 Nachrichten davor/danach</option>
            </select>
            <AsyncButton className="btn" onClick={reveal}>
              <Glyph name="shield" size={16} /> Nachricht anzeigen
            </AsyncButton>
          </div>
        </div>
      ) : (
        <section className="pf-mod-thread" aria-label="Entschlüsselte Nachrichten">
          {detail.subject && (
            <p className="small">
              <strong>Betreff:</strong> {detail.subject}
            </p>
          )}
          {detail.conversation.kind === 'broadcast' && (
            <p className="xsmall muted">
              Rundschreiben an {detail.conversation.audience.map((a) => a.label).join(', ')} ({plural(detail.conversation.recipient_count, 'Person', 'Personen')})
            </p>
          )}
          <ol className="pf-msgs">
            {detail.messages.map((m) => (
              <li key={m.id} className={`pf-mod-msg${m.reported ? ' pf-mod-msg-reported' : ''}`}>
                <div className="pf-mod-msg-head">
                  <PersonLine person={m.sender} />
                  <When ts={m.created_at} />
                  {m.reported && <span className="badge badge-warning">gemeldet</span>}
                  {m.removed && <span className="badge">ausgeblendet</span>}
                </div>
                {m.integrity_ok ? <div className="pf-text">{m.body}</div> : <p className="pf-note pf-note-warn">beschädigt – nicht lesbar</p>}
                {m.attachments.length > 0 && <FileList files={m.attachments} compact label="Anhänge" emptyText={null} />}
              </li>
            ))}
          </ol>
          <p className="xsmall muted">
            {detail.sender_reports > 1 ? `${plural(detail.sender_reports, 'Meldung', 'Meldungen')} insgesamt zu Nachrichten dieser Person. ` : ''}
            {detail.sender_suspended_until ? `Postfach gesperrt bis ${fullTime(detail.sender_suspended_until)}.` : ''}
          </p>
        </section>
      )}

      {report.status === 'offen' &&
        (report.own ? (
          <Alert kind="info">Die Meldung betrifft Ihre eigene Nachricht, eine andere Person entscheidet.</Alert>
        ) : (
          <ResolveForm report={report} onDone={onChanged} />
        ))}
    </article>
  );
}

function Suspensions() {
  const toast = useToast();
  const q = useApi<Suspension[]>((signal) => messagesApi.suspensions(signal), [], { live: ['message_reports'] });
  const lift = async (s: Suspension) => {
    try {
      await messagesApi.unsuspend(s.user_id);
      toast.success(`Sperre für ${s.user.name} aufgehoben`);
      q.reload();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  const retention = async () => {
    try {
      const r = await messagesApi.retention();
      toast.success(`Aufbewahrungsfrist angewendet: ${plural(r.messages_expired, 'Nachricht', 'Nachrichten')} gelöscht`);
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  return (
    <section className="card stack-sm" aria-labelledby="pf-sus-h">
      <h2 id="pf-sus-h">Gesperrte Postfächer</h2>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.data && !q.data.length && <p className="small muted">Zurzeit ist kein Postfach gesperrt.</p>}
      {q.data && q.data.length > 0 && (
        <ul className="pf-people pf-block-list">
          {q.data.map((s) => (
            <li key={s.user_id}>
              <span>
                <PersonLine person={s.user} />
                <span className="xsmall muted">
                  {' '}
                  bis {fullTime(s.suspended_until)}
                  {s.suspended_by ? ` · von ${s.suspended_by.name}` : ''}
                  {s.reason ? ` · ${s.reason}` : ''}
                </span>
              </span>
              <AsyncButton className="btn btn-sm" onClick={() => lift(s)}>
                Sperre aufheben
              </AsyncButton>
            </li>
          ))}
        </ul>
      )}
      <div className="pf-retention">
        <AsyncButton className="btn btn-sm" onClick={retention} confirm="Abgelaufene Nachrichten jetzt endgültig löschen?">
          Aufbewahrungsfrist jetzt anwenden
        </AsyncButton>
        <span className="xsmall muted">Läuft sonst automatisch in der nächtlichen Wartung.</span>
      </div>
    </section>
  );
}

export default function ModerationPage() {
  useTitle('Nachrichten-Moderation');
  const narrow = useMediaQuery('(max-width: 899px)');
  const [status, setStatus] = useState<StatusFilter>('offen');
  const [selected, setSelected] = useState<number | null>(null);
  const q = useApi<ReportList>((signal) => messagesApi.reports(status, signal), [status], { live: ['message_reports'] });
  const items = q.data?.items ?? [];
  const current = items.find((r) => r.id === selected) ?? null;
  const counts = q.data?.counts;

  return (
    <div className="page stack">
      <div className="page-head">
        <div>
          <h1>
            Nachrichten-Moderation
            <HelpTip>Gemeldete Nachrichten prüfen. Inhalte werden erst auf Anforderung entschlüsselt, jede Ansicht wird protokolliert.</HelpTip>
          </h1>
        </div>
        <Link to={folderPath('alle')} className="btn btn-ghost">
          <Glyph name="back" size={16} /> Zu den Nachrichten
        </Link>
      </div>
      <div className={`pf-mod-layout${current ? ' pf-mod-has-detail' : ''}`}>
        {(!narrow || !current) && (
          <section className="card stack-sm" aria-labelledby="pf-mod-list-h">
            <h2 id="pf-mod-list-h" className="sr-only">
              Meldungen
            </h2>
            <SegmentedControl<StatusFilter>
              label="Status der Meldungen"
              value={status}
              onChange={(s) => {
                setStatus(s);
                setSelected(null);
              }}
              options={[
                { value: 'offen', label: `Offen${counts ? ` (${counts.offen})` : ''}` },
                { value: 'erledigt', label: 'Erledigt' },
                { value: 'abgelehnt', label: 'Abgelehnt' },
                { value: 'alle', label: 'Alle' },
              ]}
            />
            {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
            {q.initialLoading && <Loading />}
            {q.data && !items.length && <Empty icon="check">{status === 'offen' ? 'Keine offenen Meldungen.' : 'Keine Meldungen.'}</Empty>}
            {items.length > 0 && (
              <ul className="pf-list">
                {items.map((r) => (
                  <li key={r.id}>
                    <button
                      type="button"
                      className={`pf-item pf-report-item${r.id === selected ? ' pf-item-selected' : ''}`}
                      aria-pressed={r.id === selected}
                      onClick={() => setSelected(r.id)}
                    >
                      <span className="pf-item-main">
                        <span className="pf-item-top">
                          <span className="pf-item-who">
                            {r.category_label}: Nachricht von {r.sender.name}
                          </span>
                          <When ts={r.created_at} />
                        </span>
                        <span className="pf-item-preview">
                          gemeldet von {r.reporter.name}
                          {r.reason ? ` – „${r.reason.length > 90 ? `${r.reason.slice(0, 89)}…` : r.reason}“` : ''}
                        </span>
                        <span className="pf-item-tags">
                          <span className={statusClass(r.status)}>{r.status_label}</span>
                          {r.reports_on_message > 1 && <span className="badge badge-danger">{r.reports_on_message}× gemeldet</span>}
                          {r.message_removed && <span className="badge">ausgeblendet</span>}
                        </span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}
        {current ? (
          <ReportPanel key={current.id} report={current} onChanged={q.reload} onBack={narrow ? () => setSelected(null) : undefined} />
        ) : (
          !narrow && (
            <div className="card pf-placeholder">
              <Glyph name="shield" size={40} />
              <p>Wählen Sie links eine Meldung aus.</p>
            </div>
          )
        )}
      </div>
      {(!narrow || !current) && <Suspensions />}
    </div>
  );
}

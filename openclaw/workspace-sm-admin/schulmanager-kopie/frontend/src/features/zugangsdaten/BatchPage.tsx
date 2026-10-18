/**
 * Stapel-Seite `/zugangsdaten/:id` (§11.3): Ablauf-Countdown, Einträge, Downloads (Sammel-PDF, ZIP, einzeln) und
 * Versand per E-Mail (Ziel Schüler/in, Eltern oder beide). Passwörter erscheinen nie auf der Seite, nur in den PDFs.
 */
import { useEffect, useId, useMemo, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { ApiError, errorMessage } from '../../api/client';
import { Icon } from '../../components/Icon';
import { HelpTip } from '../../components/HelpTip';
import { Alert, AsyncButton, ErrorBox, Loading } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useApi } from '../../hooks/useApi';
import { useNow, useTitle } from '../../hooks/misc';
import { formatDateTime } from '../../lib/dates';
import { can } from '../../lib/permissions';
import { lettersApi } from './api';
import { LetterBatchActions } from './components';
import { formatClock, loginHint, reachable, remainingLabel, ROLE_TEXT, secondsLeft, sendPreview, sendSummary, TARGET_TEXT } from './logic';
import type { BatchEntry, SendResult, SendTarget } from './types';
import './zugangsdaten.css';

function EmailStatus({ e }: { e: BatchEntry }) {
  const parts: string[] = [];
  if (e.has_email) parts.push('eigene Adresse');
  if (e.role === 'schueler' && e.parents_with_email > 0) parts.push(e.parents_with_email === 1 ? 'Eltern (1)' : `Eltern (${e.parents_with_email})`);
  return parts.length ? (
    <span>
      <Icon name="mail" /> {parts.join(', ')}
    </span>
  ) : (
    <span className="muted">keine</span>
  );
}

function ResultList({ title, rows, kind }: { title: string; rows: SendResult['sent']; kind: 'success' | 'warning' | 'error' }) {
  if (!rows.length) return null;
  return (
    <Alert kind={kind} title={`${title} (${rows.length})`}>
      <ul className="zd-result">
        {rows.map((r) => (
          <li key={r.user_id}>
            {r.display_name}
            {r.recipients?.length ? <span className="muted small"> – {r.recipients.join(', ')}</span> : null}
          </li>
        ))}
      </ul>
    </Alert>
  );
}

export default function BatchPage() {
  const { id = '' } = useParams();
  const location = useLocation();
  const me = useUser();
  const q = useApi((signal) => lettersApi.get(id, signal), [id]);
  const now = useNow(1000);
  const [to, setTo] = useState<SendTarget>('student');
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [result, setResult] = useState<SendResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const toName = useId();
  const sendId = useId();
  const batch = q.data;
  useTitle(batch ? batch.title || 'Zugangsdaten' : 'Zugangsdaten');

  const left = batch ? secondsLeft(batch.expires_at, now) : 0;
  const expired = !!batch && left <= 0;
  useEffect(() => {
    if (expired) q.reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [expired]);
  useEffect(() => {
    if (location.hash === '#senden' && batch) document.getElementById(sendId)?.scrollIntoView({ block: 'start' });
  }, [location.hash, batch, sendId]);

  const entries = useMemo(() => batch?.entries ?? [], [batch]);
  const chosen = useMemo(() => (selected.size ? entries.filter((e) => selected.has(e.user_id)) : entries), [entries, selected]);
  const preview = useMemo(() => sendPreview(chosen, to), [chosen, to]);
  const hasStudents = entries.some((e) => e.role === 'schueler');
  const back = can(me, 'users.manage') ? '/benutzer' : '/klassen';

  if (q.error && !batch) {
    const status = q.error instanceof ApiError ? q.error.status : 0;
    return (
      <div className="page stack zd-page">
        <h1>Zugangsdaten</h1>
        {status === 410 || status === 404 ? (
          <Alert kind="warning" title={status === 410 ? 'Stapel abgelaufen' : 'Stapel nicht gefunden'}>
            {errorMessage(q.error)}
            <HelpTip>Startpasswörter werden aus Sicherheitsgründen nur kurz aufbewahrt. Für neue Briefe erzeugen Sie neue Zugangsdaten bzw. setzen auf das Startpasswort zurück.</HelpTip>{' '}
            <Link to={back}>Zurück</Link>
          </Alert>
        ) : (
          <ErrorBox error={q.error} onRetry={q.reload} />
        )}
      </div>
    );
  }
  if (!batch) return <Loading label="Zugangsdaten werden geladen …" />;

  const toggle = (uid: number) => {
    const next = new Set(selected);
    if (next.has(uid)) next.delete(uid);
    else next.add(uid);
    setSelected(next);
  };

  return (
    <div className="page stack zd-page">
      <div className="page-head">
        <div style={{ minWidth: 0 }}>
          <h1 className="zd-title">{batch.title || 'Zugangsdaten'}</h1>
          <p className="small muted" style={{ margin: 0 }}>
            {batch.count === 1 ? '1 Brief' : `${batch.count} Briefe`} · erstellt {formatDateTime(batch.created_at)}
            {batch.created_by ? ` von ${batch.created_by.name}` : ''}
          </p>
        </div>
        <div className="zd-timer" role="timer" aria-label={`Stapel läuft ab: ${remainingLabel(left)}`}>
          <Icon name="clock" />
          <span>
            <span className="small muted">läuft ab in</span> <strong className="mono">{formatClock(left)}</strong>
          </span>
        </div>
      </div>

      <Alert kind="info" title="Startpasswörter nur kurz verfügbar">
        Die Briefe lassen sich nur bis {formatDateTime(batch.expires_at)} abrufen.
        <HelpTip>Beim ersten Anmelden muss jede Person ein eigenes Passwort festlegen. Ausgedruckte Briefe bitte persönlich und verschlossen übergeben.</HelpTip>
      </Alert>

      <section className="card" aria-labelledby="zd-dl-h">
        <div className="card-head">
          <h2 id="zd-dl-h">
            Herunterladen
            <HelpTip>
              „Alle Briefe“ ist ein PDF mit einer Seite je Person (zum Drucken); das ZIP enthält ein PDF je Person (Dateinamen wie „5a_Mustermann_Max.pdf“) zum einzelnen Verschicken.
            </HelpTip>
          </h2>
        </div>
        <LetterBatchActions batch={{ id: batch.id, expires_at: batch.expires_at, count: batch.count }} page={false} small={false} />
      </section>

      <section className="card" aria-labelledby="zd-list-h">
        <div className="card-head">
          <h2 id="zd-list-h">Briefe</h2>
          <span className="badge">{entries.length}</span>
        </div>
        <div className="table-wrap">
          <table className="table table-compact zd-table">
            <caption className="sr-only">Zugangsbriefe dieses Stapels</caption>
            <thead>
              <tr>
                <th scope="col">
                  <span className="sr-only">Für den Versand auswählen</span>
                </th>
                <th scope="col">Name</th>
                <th scope="col">Klasse</th>
                <th scope="col">Benutzername</th>
                <th scope="col">E-Mail</th>
                <th scope="col">Anmeldung</th>
                <th scope="col">
                  <span className="sr-only">Brief</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => {
                const cls = e.class_id ?? [...new Set(e.children.map((c) => c.class_id).filter(Boolean))].join(', ');
                return (
                  <tr key={e.user_id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selected.has(e.user_id)}
                        onChange={() => toggle(e.user_id)}
                        aria-label={`${e.display_name} für den Versand auswählen`}
                      />
                    </td>
                    <td className="zd-name">
                      <strong>{e.display_name}</strong>
                      <span className="small muted">
                        {ROLE_TEXT[e.role] ?? e.role}
                        {e.role === 'eltern' && e.children.length ? ` von ${e.children.map((c) => c.name).join(', ')}` : ''}
                        {!e.exists ? ' · Konto gelöscht' : ''}
                      </span>
                    </td>
                    <td>{cls || '–'}</td>
                    <td className="mono">{e.username}</td>
                    <td className="small">
                      <EmailStatus e={e} />
                    </td>
                    <td className="small">{loginHint(e)}</td>
                    <td>
                      <a
                        className="btn btn-ghost btn-sm"
                        href={lettersApi.entryUrl(batch.id, e.user_id)}
                        download
                        aria-label={`Brief für ${e.display_name} als PDF`}
                      >
                        <Icon name="download" /> PDF
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card" aria-labelledby={sendId} id={sendId}>
        <div className="card-head">
          <h2 id={`${sendId}-h`}>Per E-Mail senden</h2>
        </div>
        <Alert kind="warning" title="E-Mail ist weniger sicher als Papier">
          Startpasswörter per E-Mail können mitgelesen oder weitergeleitet werden.
          <HelpTip>Das gilt z. B. für gemeinsame Postfächer und Familien-Tablets. Wenn möglich, übergeben Sie den ausgedruckten Brief persönlich.</HelpTip>
        </Alert>
        {!batch.email_available && (
          <Alert kind="info" title="E-Mail-Versand ist nicht eingerichtet">
            Ohne eingerichteten E-Mail-Versand (SMTP) werden die Nachrichten als „nicht zustellbar“ gemeldet.
          </Alert>
        )}
        <fieldset className="zd-fieldset">
          <legend>Empfänger</legend>
          {(['student', 'parents', 'both'] as SendTarget[]).map((t) => (
            <label key={t} className="check">
              <input type="radio" name={toName} checked={to === t} onChange={() => setTo(t)} disabled={!hasStudents && t !== 'student'} /> {TARGET_TEXT[t]}
              {t === 'parents' && <span className="small muted"> (Schülerbriefe an die verknüpften Elternkonten, Volljährige nur selbst)</span>}
            </label>
          ))}
        </fieldset>
        <p className="small" aria-live="polite">
          {selected.size ? `${selected.size} ausgewählt` : 'Alle Briefe'}: {preview.reachable} mit E-Mail-Adresse
          {preview.missing ? `, ${preview.missing} ohne Adresse (bitte ausdrucken)` : ''}.
        </p>
        <div className="row">
          <AsyncButton
            className="btn btn-primary"
            disabled={preview.reachable === 0 || expired}
            confirm={`${preview.reachable} ${preview.reachable === 1 ? 'Brief' : 'Briefe'} ${TARGET_TEXT[to]} per E-Mail senden?`}
            onClick={async () => {
              setError(null);
              try {
                setResult(await lettersApi.send(batch.id, { to, ...(selected.size ? { user_ids: [...selected] } : {}) }));
              } catch (e) {
                setError(errorMessage(e));
              }
            }}
          >
            <Icon name="mail" /> Per E-Mail senden
          </AsyncButton>
          {selected.size > 0 && (
            <button type="button" className="btn btn-ghost" onClick={() => setSelected(new Set())}>
              Auswahl aufheben
            </button>
          )}
        </div>
        <div aria-live="polite" className="stack-sm" style={{ marginTop: 12 }}>
          {error && (
            <Alert kind="error" title="Versand nicht möglich">
              {error}
            </Alert>
          )}
          {result && (
            <>
              <p>
                <strong>{sendSummary(result)}</strong>
              </p>
              <ResultList title="Verschickt" rows={result.sent} kind="success" />
              <ResultList title="Ohne E-Mail-Adresse – bitte ausdrucken" rows={result.no_address} kind="warning" />
              <ResultList title="Nicht zustellbar" rows={result.unavailable} kind="error" />
            </>
          )}
          {entries.some((e) => !reachable(e, to)) && !result && (
            <p className="small muted">Personen ohne E-Mail-Adresse: Briefe bitte ausdrucken.</p>
          )}
        </div>
      </section>
    </div>
  );
}

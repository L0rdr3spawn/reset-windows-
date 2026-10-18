/**
 * Öffentliche Seite `/test-postausgang` (§11.2, nur mit `SM_DEV_OUTBOX`): zeigt die E-Mails und SMS, die das
 * Produkt verschickt hätte – mit Kopierknopf für Codes, internen Links und Anhängen zum Herunterladen.
 */
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ApiError } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Alert, ErrorBox, Loading } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { useTitle } from '../../hooks/misc';
import { formatDateTime } from '../../lib/dates';
import { devOutboxApi } from './api';
import { APP_NAME } from '../../brand';
import { extractCodes, extractLinks, formatBytes, internalAppPath } from './logic';
import type { DevOutboxItem } from './types';
import './konto.css';

const REFRESH_MS = 5000;

function CopyCode({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      className="btn btn-sm"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(code);
          setCopied(true);
          window.setTimeout(() => setCopied(false), 2000);
        } catch {
          /* Zwischenablage nicht verfügbar – Code steht im Text */
        }
      }}
      aria-label={`Code ${code} kopieren`}
    >
      <Icon name={copied ? 'check' : 'copy'} /> <span className="mono">{code}</span> {copied ? 'kopiert' : 'kopieren'}
    </button>
  );
}

function Message({ item }: { item: DevOutboxItem }) {
  const codes = extractCodes(item.text);
  const links = extractLinks(item.text)
    .map((url) => ({ url, path: internalAppPath(url) }))
    .filter((l): l is { url: string; path: string } => l.path !== null);
  return (
    <article className="card ko-msg" aria-labelledby={`ko-msg-${item.id}`}>
      <header className="ko-msg-head">
        <span className={`badge ${item.channel === 'sms' ? 'badge-info' : 'badge-primary'}`}>{item.channel === 'sms' ? 'SMS' : 'E-Mail'}</span>
        <span className="mono ko-break">an {item.to}</span>
        <span className="small muted">{formatDateTime(item.created_at)}</span>
      </header>
      <h2 id={`ko-msg-${item.id}`} className="ko-msg-subject">
        {item.channel === 'sms' ? `SMS (${item.purpose})` : item.subject}
      </h2>
      <pre className="ko-text">{item.text}</pre>
      {(codes.length > 0 || links.length > 0) && (
        <div className="ko-actions">
          {codes.map((c) => (
            <CopyCode key={c} code={c} />
          ))}
          {links.map((l) => (
            <Link key={l.url} className="btn btn-sm" to={l.path}>
              <Icon name="link" /> Link öffnen
            </Link>
          ))}
        </div>
      )}
      {item.attachments.length > 0 && (
        <ul className="list-plain small ko-attachments" aria-label="Anhänge">
          {item.attachments.map((a) => (
            <li key={a.index}>
              <a href={devOutboxApi.attachmentUrl(item.id, a.index)} download={a.filename}>
                <Icon name="download" /> {a.filename}
              </a>{' '}
              <span className="muted">({formatBytes(a.size)})</span>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

export default function DevOutboxPage() {
  useTitle('Test-Postausgang');
  const [auto, setAuto] = useState(true);
  const [filter, setFilter] = useState('');
  const list = useApi((signal) => devOutboxApi.list(signal), []);
  const { reload } = list;
  const disabled = list.error instanceof ApiError && list.error.status === 404;

  useEffect(() => {
    if (!auto || disabled) return undefined;
    const t = window.setInterval(() => {
      if (document.visibilityState === 'visible') reload();
    }, REFRESH_MS);
    return () => window.clearInterval(t);
  }, [auto, disabled, reload]);

  const items = useMemo(() => {
    const q = filter.trim().toLowerCase();
    const all = list.data?.items ?? [];
    return q ? all.filter((m) => `${m.to} ${m.subject} ${m.text}`.toLowerCase().includes(q)) : all;
  }, [list.data, filter]);

  return (
    <main className="ko-page stack">
      <div className="row-between ko-wrap">
        <h1>Test-Postausgang</h1>
        <Link className="btn btn-ghost btn-sm" to="/login">
          Zur Anmeldung
        </Link>
      </div>
      <Alert kind="warning" title="Nur Test-Umgebung">
        Es wird nichts zugestellt.
        <HelpTip>
          Hier erscheinen alle E-Mails und SMS (Codes, Links, Zugangsbriefe), die {APP_NAME} verschicken würde, ohne Anmeldung für jede Person sichtbar. In Produktion ist diese Seite abgeschaltet.
        </HelpTip>
      </Alert>
      {disabled ? (
        <Alert kind="info" title="Test-Postausgang ausgeschaltet">
          Dieser Server stellt Nachrichten echt zu (SM_DEV_OUTBOX ist aus).
        </Alert>
      ) : (
        <>
          <div className="row ko-wrap ko-toolbar">
            <div className="field ko-filter">
              <label htmlFor="ko-filter">Empfänger oder Text filtern</label>
              <input id="ko-filter" type="search" value={filter} onChange={(e) => setFilter(e.target.value)} autoComplete="off" />
            </div>
            <label className="check">
              <input type="checkbox" checked={auto} onChange={(e) => setAuto(e.target.checked)} /> alle 5 Sekunden aktualisieren
            </label>
            <button type="button" className="btn btn-sm" onClick={reload}>
              <Icon name="refresh" /> Aktualisieren
            </button>
          </div>
          {list.error && !disabled ? <ErrorBox error={list.error} onRetry={reload} /> : null}
          {list.initialLoading ? (
            <Loading />
          ) : (
            <>
              <p className="small muted" aria-live="polite">
                {items.length === 1 ? '1 Nachricht' : `${items.length} Nachrichten`} (die letzten 50, Aufbewahrung {list.data?.hours ?? 24} Stunden)
              </p>
              {items.map((m) => (
                <Message key={m.id} item={m} />
              ))}
            </>
          )}
        </>
      )}
    </main>
  );
}

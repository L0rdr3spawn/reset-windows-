/**
 * `/chats/moderation` – gemeldete Chat-Nachrichten. Inhalte sind Ende-zu-Ende-verschlüsselt; zu sehen ist nur der
 * Text, den die meldende Person freiwillig mitgeschickt hat.
 */
import { useState } from 'react';
import { API_BASE } from '../../api/client';
import '../../components/emoji.css';
import { HelpTip } from '../../components/HelpTip';
import { AsyncButton, ErrorBox, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useTitle } from '../../hooks/misc';
import { formatDateTime } from '../../lib/dates';
import { chatsApi } from './api';
import './chats.css';

const STATUS: Record<string, string> = { open: 'offen', dismissed: 'abgelehnt', removed: 'entfernt' };

export default function ModerationPage() {
  useTitle('Chat-Meldungen');
  const toast = useToast();
  const [all, setAll] = useState(false);
  const q = useApi((signal) => chatsApi.reports(signal), [], { live: ['chat_reports', 'chats'] });
  const rows = (q.data?.reports ?? []).filter((r) => all || r.status === 'open');
  const act = async (id: number, action: 'dismiss' | 'remove') => {
    try {
      await chatsApi.resolve(id, action);
      q.reload();
    } catch (e) {
      toast.error(e);
    }
  };
  return (
    <div className="page stack">
      <div className="page-head">
        <h1>
          Gemeldete Chat-Nachrichten
          <HelpTip>
            Chats sind Ende-zu-Ende-verschlüsselt. Sie sehen nur Text und Bilder, die die meldende Person mitgeschickt hat. „Entfernen“ löscht die Nachricht für alle.
          </HelpTip>
        </h1>
        <label className="check">
          <input type="checkbox" checked={all} onChange={(e) => setAll(e.target.checked)} /> auch erledigte
        </label>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!q.data && q.loading && <Loading />}
      {q.data && !rows.length && <p className="muted">Keine offenen Meldungen.</p>}
      {rows.map((r) => (
        <section key={r.id} className="card stack-sm">
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <strong>
              {r.sender_name}{' '}
              <span className="muted small">
                gemeldet von {r.reporter_name} · {formatDateTime(r.created_at)}
              </span>
            </strong>
            <span className="badge">{STATUS[r.status] ?? r.status}</span>
          </div>
          {(r.content || !r.images.length) && <blockquote className="ch-quote">{r.content || '(kein Text mitgeschickt)'}</blockquote>}
          {r.images.length > 0 && (
            <div className="row" style={{ flexWrap: 'wrap' }}>
              {r.images.map((im) => (
                <a key={im.id} href={`${API_BASE}/chat-reports/${r.id}/images/${im.id}`} target="_blank" rel="noopener noreferrer">
                  <img className="msg-img msg-img-small" src={`${API_BASE}/chat-reports/${r.id}/images/${im.id}`} alt="Mitgeschicktes Bild" />
                </a>
              ))}
            </div>
          )}
          {r.reason && <p className="small">Begründung: {r.reason}</p>}
          {r.status === 'open' && (
            <div className="row">
              <AsyncButton className="btn btn-danger btn-sm" confirm="Nachricht für alle entfernen?" onClick={() => act(r.id, 'remove')}>
                Nachricht entfernen
              </AsyncButton>
              <AsyncButton className="btn btn-sm" onClick={() => act(r.id, 'dismiss')}>
                Ablehnen
              </AsyncButton>
            </div>
          )}
        </section>
      ))}
    </div>
  );
}

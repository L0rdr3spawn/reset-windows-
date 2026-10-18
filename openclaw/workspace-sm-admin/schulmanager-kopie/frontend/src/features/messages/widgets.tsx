/**
 * Startseiten-Kachel „Neue Nachrichten“: ungelesene Unterhaltungen (höchstens 5) mit Absender, Betreff und
 * Vorschau; für die Moderation ein Hinweis auf offene Meldungen.
 */
import { Link } from 'react-router-dom';
import { useUser } from '../../context/AuthContext';
import { ErrorBox, Loading } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { can } from '../../lib/permissions';
import { useBadge } from '../registry';
import { messagesApi } from './api';
import { REPORTS_BADGE } from '../nachrichten/badge';
import { Avatar, Glyph, When } from './components';
import { conversationPath, listHeadline, plural, previewLine } from './logic';
import type { ConversationList } from './types';
import './messages.css';

export function InboxWidget() {
  const user = useUser();
  const q = useApi<ConversationList>((signal) => messagesApi.list({ folder: 'inbox', unread: true, limit: 5 }, signal), [user.id], { live: ['messages'] });
  const reports = useBadge(REPORTS_BADGE) ?? 0;
  const moderator = can(user, 'messages.moderate');
  const data = q.data;
  return (
    <section className="card pf-widget" aria-labelledby="pfw-h">
      <div className="card-head">
        <h2 id="pfw-h">Neue Nachrichten</h2>
        <Link to="/nachrichten" className="small">
          Zu den Nachrichten
        </Link>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {data && !data.items.length && (
        <p className="small muted" style={{ margin: 0 }}>
          Keine ungelesenen Nachrichten.
        </p>
      )}
      {data && data.items.length > 0 && (
        <ul className="pf-widget-list">
          {data.items.map((c) => {
            const other = c.kind === 'direct' ? c.participants[0] : undefined;
            return (
              <li key={c.id}>
                <Link to={conversationPath(c.id)} className="pf-widget-item">
                  <Avatar name={other?.name ?? c.title} role={other?.role} glyph={c.kind === 'broadcast' ? 'megaphone' : c.kind === 'group' ? 'people' : undefined} size={32} />
                  <span className="pf-item-main">
                    <span className="pf-item-top">
                      <span className="pf-item-who">{listHeadline(c)}</span>
                      <When ts={c.last_message_at} />
                    </span>
                    {c.subject && <span className="pf-item-subject">{c.subject}</span>}
                    <span className="pf-item-preview">{previewLine(c)}</span>
                  </span>
                  <span className="pf-pill">
                    {c.unread}
                    <span className="sr-only"> ungelesen</span>
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
      {data && data.total > data.items.length && (
        <p className="xsmall muted" style={{ margin: 'var(--space-2) 0 0' }}>
          … und {plural(data.total - data.items.length, 'weitere Unterhaltung', 'weitere Unterhaltungen')}
        </p>
      )}
      {moderator && reports > 0 && (
        <p className="pf-widget-mod small">
          <Glyph name="shield" size={14} /> {plural(reports, 'gemeldete Nachricht wartet', 'gemeldete Nachrichten warten')} auf Prüfung –{' '}
          <Link to="/nachrichten/moderation">zur Moderation</Link>
        </p>
      )}
      <div className="pf-widget-actions">
        <Link to="/nachrichten/neu" className="btn btn-sm">
          <Glyph name="pen" size={14} /> Neue Nachricht
        </Link>
      </div>
    </section>
  );
}

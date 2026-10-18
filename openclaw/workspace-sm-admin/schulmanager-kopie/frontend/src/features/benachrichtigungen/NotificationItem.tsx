import { Icon } from '../../components/Icon';
import type { AppNotification } from './api';
import { relativeTime } from './logic';

/** Eine Zeile der Benachrichtigungsliste (Glocke und Seite): Klick öffnet das Ziel und markiert als gelesen. */
export function NotificationItem({
  n,
  onOpen,
  onToggleRead,
  onRemove,
}: {
  n: AppNotification;
  onOpen: (n: AppNotification) => void;
  onToggleRead?: (n: AppNotification) => void;
  onRemove?: (n: AppNotification) => void;
}) {
  return (
    <li className={`nt-item${n.read ? '' : ' unread'}`}>
      <button type="button" className="nt-main" onClick={() => onOpen(n)}>
        <span className="nt-meta">
          <span className="nt-kind">{n.kind_label}</span>
          {n.child ? <span className="badge nt-child">für {n.child}</span> : null}
          <time dateTime={n.created_at ?? undefined}>{relativeTime(n.created_at)}</time>
        </span>
        <span className="nt-title">
          {!n.read && <span className="sr-only">Ungelesen: </span>}
          {n.title}
        </span>
        {n.body ? <span className="nt-body">{n.body}</span> : null}
      </button>
      {(onToggleRead || onRemove) && (
        <span className="nt-actions">
          {onToggleRead && (
            <button type="button" className="btn btn-ghost btn-icon" onClick={() => onToggleRead(n)} aria-label={n.read ? 'Als ungelesen markieren' : 'Als gelesen markieren'} title={n.read ? 'Als ungelesen markieren' : 'Als gelesen markieren'}>
              <Icon name={n.read ? 'eyeOff' : 'check'} />
            </button>
          )}
          {onRemove && (
            <button type="button" className="btn btn-ghost btn-icon" onClick={() => onRemove(n)} aria-label="Benachrichtigung löschen" title="Löschen">
              <Icon name="trash" />
            </button>
          )}
        </span>
      )}
    </li>
  );
}

/**
 * Glocke in der Kopfleiste: Zähler ungelesener Benachrichtigungen, Ausklapp-Liste der letzten, „Alle als gelesen“.
 * Live über die bestehende SSE-Verbindung (Bereich `notifications`); ist sie nicht offen, fragt die Glocke minütlich nach.
 * Chats und Postfach haben ihren eigenen Zähler („Nachrichten“) und zählen hier nicht mit.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Icon } from '../../components/Icon';
import { Spinner } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useLiveStatus } from '../../hooks/useLive';
import { notificationsApi, type AppNotification } from './api';
import { NotificationItem } from './NotificationItem';
import { bellLabel, bellText, safeLink } from './logic';
import './benachrichtigungen.css';

const POLL_MS = 60_000;
const PREVIEW = 10;

/** Zähler mit Live-Aktualisierung; Rückfall auf Abfragen, solange die Live-Verbindung nicht offen ist. */
export function useUnreadCount(): { unread: number; reload: () => void } {
  const q = useApi((signal) => notificationsApi.count(signal), [], { live: ['notifications'], keepPrevious: true });
  const live = useLiveStatus();
  const { reload } = q;
  useEffect(() => {
    if (live === 'open') return undefined;
    const t = window.setInterval(reload, POLL_MS);
    return () => window.clearInterval(t);
  }, [live, reload]);
  return { unread: q.data?.unread ?? 0, reload };
}

export function NotificationBell() {
  const toast = useToast();
  const navigate = useNavigate();
  const { unread, reload } = useUnreadCount();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const btn = useRef<HTMLButtonElement>(null);
  const list = useApi((signal) => notificationsApi.list({ limit: PREVIEW }, signal), [open], {
    enabled: open,
    live: ['notifications'],
    keepPrevious: true,
  });

  useEffect(() => {
    if (!open) return undefined;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false);
        btn.current?.focus();
      }
    };
    document.addEventListener('mousedown', onDoc);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDoc);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const openItem = useCallback(
    async (n: AppNotification) => {
      setOpen(false);
      if (!n.read) {
        try {
          await notificationsApi.markRead([n.id]);
          reload();
        } catch {
          /* Zähler zieht beim nächsten Ereignis nach */
        }
      }
      const target = safeLink(n.link);
      if (target) navigate(target);
    },
    [navigate, reload],
  );

  const markAll = async () => {
    try {
      await notificationsApi.markRead(null);
      reload();
      list.reload();
    } catch (e) {
      toast.error(e);
    }
  };

  const text = bellText(unread);
  const items = list.data?.items ?? [];
  return (
    <div className="nt-bell" ref={ref}>
      <button ref={btn} type="button" className="btn btn-ghost btn-icon nt-bell-btn" aria-haspopup="dialog" aria-expanded={open} aria-label={bellLabel(unread)} title="Benachrichtigungen" onClick={() => setOpen((o) => !o)}>
        <Icon name="bell" />
        {text ? (
          <span className="nt-count" aria-hidden="true">
            {text}
          </span>
        ) : null}
      </button>
      {open && (
        <div className="nt-pop" role="dialog" aria-label="Benachrichtigungen">
          <div className="nt-pop-head">
            <strong>Benachrichtigungen</strong>
            <button type="button" className="btn btn-ghost btn-sm" disabled={unread === 0} onClick={() => void markAll()}>
              Alle als gelesen
            </button>
          </div>
          {list.data === undefined && !list.error ? (
            <div className="nt-pop-empty">
              <Spinner />
            </div>
          ) : list.error ? (
            <p className="nt-pop-empty muted">Benachrichtigungen konnten nicht geladen werden.</p>
          ) : items.length === 0 ? (
            <p className="nt-pop-empty muted">Keine Benachrichtigungen.</p>
          ) : (
            <ul className="nt-list">
              {items.map((n) => (
                <NotificationItem key={n.id} n={n} onOpen={(x) => void openItem(x)} />
              ))}
            </ul>
          )}
          <div className="nt-pop-foot">
            <Link to="/benachrichtigungen" onClick={() => setOpen(false)}>
              Alle anzeigen und einstellen
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * `/nachrichten` – EINE Liste für alles wie in einem Messenger: Einzelchats, Gruppen, Briefe/Rundschreiben, E-Mails
 * verknüpfter Konten und Mitteilungen der Schule, sortiert nach der letzten Aktivität. Oben Filter-Chips und Suche.
 *
 * * `/nachrichten/c/:id` – Chat bzw. Gruppe (Ende-zu-Ende-verschlüsselt)
 * * `/nachrichten/b/:id` – Brief, Rundschreiben oder E-Mail (Betreff, Anhänge, Antworten)
 * * `/nachrichten/mitteilungen` – Mitteilungen der Schule
 *
 * Am PC steht die Liste links und das Geöffnete rechts; auf dem Handy nacheinander (Liste, dann Vollbild mit „Zurück“).
 */
import { useEffect, useId, useMemo, useState } from 'react';
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import { announcements as announcementsApi } from '../../api/endpoints';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton, Empty, ErrorBox, Loading } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { useDebounced, useMediaQuery, useTitle } from '../../hooks/misc';
import { useApi } from '../../hooks/useApi';
import { AnnouncementsPanel } from '../../pages/AnnouncementsPage';
import { chatsApi } from '../chats/api';
import { ChatView, NewGroupModal, PersonSearch, useDevice } from '../chats/ChatsPage';
import { DevicesModal, NewDeviceBanner } from '../chats/DevicesPanel';
import { mailApi, messagesApi } from '../messages/api';
import { Avatar, Glyph, When } from '../messages/components';
import { ConversationView } from '../messages/ConversationView';
import { chatPath, conversationPath, filterFromParam, filterQuery, folderPath, INBOX_FILTERS, plural, retentionText, suspendedText, type InboxFilter } from '../messages/logic';
import type { ConversationList, DraftSummary, MessageSettings } from '../messages/types';
import '../messages/messages.css';
import { useBadge } from '../registry';
import { UNREAD_BADGE } from './badge';
import { buildList, fromAnnouncement, fromChat, fromConversation, type InboxItem, unreadChats } from './inbox';
import './nachrichten.css';
import { confirmAsk } from '../../lib/confirm';

const PAGE = 30;
const MAX_LIST = 100;

const EMPTY_TEXT: Record<InboxFilter, string> = {
  alle: 'Noch keine Nachrichten. Mit „Neu“ starten Sie einen Chat, eine Gruppe oder schreiben einen Brief.',
  chats: 'Noch keine Chats – mit „Neu“ eine Person anschreiben.',
  gruppen: 'Noch keine Gruppen – mit „Neu“ eine Gruppe erstellen.',
  briefe: 'Keine Briefe.',
  email: 'Keine E-Mails.',
  mitteilungen: 'Keine Mitteilungen.',
  archiv: 'Nichts archiviert. Archivierte Unterhaltungen verschwinden aus der Liste und kommen bei einer neuen Nachricht zurück (stumme bleiben hier).',
  entwuerfe: 'Keine Entwürfe.',
};

// ---------------------------------------------------------------------------------------------- Liste

function ItemRow({ item, filter, selected }: { item: InboxItem; filter: InboxFilter; selected: boolean }) {
  return (
    <li>
      <Link
        to={`${item.path}${filterQuery(filter)}`}
        className={`pf-item${item.unread ? ' pf-item-unread' : ''}${selected ? ' pf-item-selected' : ''}`}
        aria-current={selected ? 'true' : undefined}
      >
        <Avatar name={item.avatar.name} role={item.avatar.role} glyph={item.avatar.glyph} size={40} />
        <span className="pf-item-main">
          <span className="pf-item-top">
            <span className="pf-item-who">{item.title}</span>
            {item.at && <When ts={item.at.endsWith('Z') || /[+-]\d\d:?\d\d$/.test(item.at) ? item.at : `${item.at}Z`} />}
          </span>
          {item.subtitle && <span className="pf-item-subject">{item.subtitle}</span>}
          {item.preview && <span className="pf-item-preview">{item.preview}</span>}
          <span className="pf-item-tags">
            {item.tag && <span className={`badge${item.type === 'mitteilung' || item.tag === 'Rundschreiben' ? ' badge-info' : ''}`}>{item.tag}</span>}
            {item.muted && (
              <span className="pf-tag" title="stummgeschaltet">
                <Glyph name="bellOff" size={13} />
                <span className="sr-only">stummgeschaltet</span>
              </span>
            )}
            {item.attachment && (
              <span className="pf-tag" title="mit Anhang">
                <Glyph name="clip" size={13} />
                <span className="sr-only">mit Anhang</span>
              </span>
            )}
            {item.archived && filter !== 'archiv' && <span className="badge">archiviert</span>}
          </span>
        </span>
        {item.unread > 0 && (
          <span className={`pf-pill${item.muted ? ' pf-pill-muted' : ''}`}>
            {item.unread}
            <span className="sr-only"> ungelesen</span>
          </span>
        )}
      </Link>
    </li>
  );
}

function DraftList({ drafts, onChanged }: { drafts: DraftSummary[]; onChanged: () => void }) {
  const toast = useToast();
  const remove = async (d: DraftSummary) => {
    if (!(await confirmAsk({ title: 'Entwurf löschen', message: 'Entwurf löschen?', confirmLabel: 'Löschen', danger: true }))) return;
    try {
      await messagesApi.deleteDraft(d.id);
      toast.success('Entwurf gelöscht');
      onChanged();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  if (!drafts.length) return <Empty icon="info">{EMPTY_TEXT.entwuerfe}</Empty>;
  return (
    <ul className="pf-list">
      {drafts.map((d) => (
        <li key={d.id} className="pf-draft">
          <Link to={d.conversation_id ? conversationPath(d.conversation_id) : `/nachrichten/neu?entwurf=${d.id}`} className="pf-item">
            <Avatar name="" glyph="pen" size={40} />
            <span className="pf-item-main">
              <span className="pf-item-top">
                <span className="pf-item-who">{d.conversation_id ? 'Antwort-Entwurf' : d.recipient_labels.join(', ') || 'Noch keine Empfänger/innen'}</span>
                <When ts={d.updated_at} />
              </span>
              {d.subject && <span className="pf-item-subject">{d.subject}</span>}
              <span className="pf-item-preview">{d.integrity_ok ? d.preview || '(noch kein Text)' : 'Entwurf beschädigt'}</span>
            </span>
          </Link>
          <AsyncButton className="btn btn-ghost btn-sm pf-draft-del" onClick={() => remove(d)} title="Entwurf löschen">
            <Icon name="trash" />
            <span className="sr-only">Entwurf löschen</span>
          </AsyncButton>
        </li>
      ))}
    </ul>
  );
}

// ---------------------------------------------------------------------------------------------- Neu

function NewMenu({ mailAccounts, onChat, onGroup }: { mailAccounts: boolean; onChat: () => void; onGroup: () => void }) {
  const [open, setOpen] = useState(false);
  const menuId = useId();
  useEffect(() => {
    if (!open) return undefined;
    const away = (e: MouseEvent | TouchEvent) => {
      if (!(e.target as HTMLElement | null)?.closest?.('.nm-new')) setOpen(false);
    };
    const key = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', away);
    document.addEventListener('touchstart', away);
    document.addEventListener('keydown', key);
    return () => {
      document.removeEventListener('mousedown', away);
      document.removeEventListener('touchstart', away);
      document.removeEventListener('keydown', key);
    };
  }, [open]);
  const pick = (fn?: () => void) => () => {
    setOpen(false);
    fn?.();
  };
  return (
    <div className="nm-new">
      <button type="button" className="btn btn-primary" aria-haspopup="menu" aria-expanded={open} aria-controls={menuId} onClick={() => setOpen((o) => !o)}>
        <Glyph name="plus" size={16} /> Neu
      </button>
      {open && (
        <ul id={menuId} className="nm-new-menu card" role="menu" aria-label="Neu">
          <li role="none">
            <button type="button" role="menuitem" onClick={pick(onChat)}>
              <Glyph name="send" size={18} />
              <span>
                <strong>Chat</strong>
                <span className="xsmall muted">Mit einer Person schreiben</span>
              </span>
            </button>
          </li>
          <li role="none">
            <button type="button" role="menuitem" onClick={pick(onGroup)}>
              <Glyph name="people" size={18} />
              <span>
                <strong>Gruppe</strong>
                <span className="xsmall muted">Mehrere Personen oder eine Klasse</span>
              </span>
            </button>
          </li>
          <li role="none">
            <Link to="/nachrichten/neu" role="menuitem" onClick={pick()}>
              <Glyph name="pen" size={18} />
              <span>
                <strong>Brief</strong>
                <span className="xsmall muted">Mit Betreff, an mehrere Personen oder Klassen</span>
              </span>
            </Link>
          </li>
          {mailAccounts && (
            <li role="none">
              <Link to="/nachrichten/neu?art=email" role="menuitem" onClick={pick()}>
                <Glyph name="mail" size={18} />
                <span>
                  <strong>E-Mail</strong>
                  <span className="xsmall muted">Über Ihr verknüpftes Konto</span>
                </span>
              </Link>
            </li>
          )}
        </ul>
      )}
    </div>
  );
}

function NewChatModal({ onClose, onOpen }: { onClose: () => void; onOpen: (chatId: number) => void }) {
  return (
    <Modal title="Neuer Chat" onClose={onClose}>
      <PersonSearch onOpen={onOpen} />
    </Modal>
  );
}

// ---------------------------------------------------------------------------------------------- Seite

export default function NachrichtenPage() {
  useTitle('Nachrichten');
  const user = useUser();
  const navigate = useNavigate();
  const location = useLocation();
  const searchId = useId();
  const { kind, id: idParam } = useParams<{ kind?: string; id?: string }>();
  const [params, setParams] = useSearchParams();
  const filter = filterFromParam(params.get('f'));
  const linkCode = params.get('link') ?? '';
  const narrow = useMediaQuery('(max-width: 899px)');

  const id = idParam && /^\d+$/.test(idParam) ? Number(idParam) : null;
  const openChat = kind === 'c' && id ? id : null;
  const openLetter = kind === 'b' && id ? id : null;
  const openNotices = kind === 'mitteilungen';
  const hasThread = !!(openChat || openLetter || openNotices);
  const badKind = kind !== undefined && !hasThread;

  const [query, setQuery] = useState('');
  const debounced = useDebounced(query.trim(), 300);
  const [onlyUnread, setOnlyUnread] = useState(false);
  const [pages, setPages] = useState(1);
  useEffect(() => setPages(1), [filter, debounced, onlyUnread]);
  const limit = Math.min(MAX_LIST, PAGE * pages);

  const [newChat, setNewChat] = useState(false);
  const [newGroup, setNewGroup] = useState(false);
  const [devicesOpen, setDevicesOpen] = useState(false);
  const { device, error: devError, retry } = useDevice(user.id, !!openChat || devicesOpen || !!linkCode);
  useEffect(() => {
    if (linkCode && device) setDevicesOpen(true);
  }, [linkCode, device]);

  // Daten: Chats immer (klein), Briefe/E-Mails nach Filter, Mitteilungen nur wo sie gebraucht werden
  const chatsQ = useApi((signal) => chatsApi.list(signal), [user.id], { live: ['chats'] });
  const wantMail = filter === 'alle' || filter === 'briefe' || filter === 'email' || filter === 'archiv';
  const mailQ = useApi<ConversationList>(
    (signal) => messagesApi.list({ folder: filter === 'archiv' ? 'archive' : 'all', q: debounced, unread: onlyUnread, limit }, signal),
    [filter === 'archiv', debounced, onlyUnread, limit],
    { live: ['messages'], enabled: wantMail },
  );
  const wantNotices = filter === 'alle' || filter === 'mitteilungen';
  const noticesQ = useApi(() => announcementsApi.list(), [], { live: ['announcements'], enabled: wantNotices });
  const draftsQ = useApi<DraftSummary[]>((signal) => messagesApi.drafts(signal), [user.id], { live: ['messages'] });
  const settingsQ = useApi<MessageSettings>((signal) => messagesApi.settings(signal), [], { live: ['messages'] });
  const accountsQ = useApi((signal) => mailApi.accounts(signal).catch(() => ({ accounts: [], max: 0 })), []);
  const settings = settingsQ.data;
  const drafts = draftsQ.data ?? [];

  const chats = chatsQ.data?.chats ?? [];
  const merged = useMemo(() => {
    const items: InboxItem[] = [];
    if (filter !== 'mitteilungen') items.push(...chats.map(fromChat));
    if (wantMail) items.push(...(mailQ.data?.items ?? []).map(fromConversation));
    if (wantNotices) items.push(...(noticesQ.data ?? []).map(fromAnnouncement));
    const base = buildList(items, filter, debounced);
    return onlyUnread ? base.filter((i) => i.unread > 0) : base;
  }, [chats, mailQ.data, noticesQ.data, filter, wantMail, wantNotices, debounced, onlyUnread]);
  const shown = merged.slice(0, PAGE * pages);
  const mailHasMore = wantMail && (mailQ.data?.total ?? 0) > (mailQ.data?.items.length ?? 0);
  const hasMore = merged.length > shown.length || (mailHasMore && limit < MAX_LIST);
  const capped = merged.length <= shown.length && mailHasMore && limit >= MAX_LIST;

  const totalUnreadBadge = useBadge(UNREAD_BADGE) ?? 0;
  const chipCount = (f: InboxFilter): number => {
    if (f === 'alle') return totalUnreadBadge;
    if (f === 'chats') return unreadChats(chats, 'direct');
    if (f === 'gruppen') return unreadChats(chats, 'group');
    if (f === 'entwuerfe') return drafts.length;
    return 0;
  };
  const chips = INBOX_FILTERS.filter((f) => f.key !== 'entwuerfe' || drafts.length > 0 || filter === 'entwuerfe');

  const selectedKey = openChat ? `c:${openChat}` : openLetter ? `b:${openLetter}` : null;
  const suspended = suspendedText(settings?.suspended_until);
  const listPath = folderPath(filter);
  const loading = (wantMail && mailQ.initialLoading) || chatsQ.initialLoading;
  const error = chatsQ.error ?? (wantMail ? mailQ.error : null);
  const readAll = async () => {
    try {
      await messagesApi.readAll();
      mailQ.reload();
    } catch {
      /* Anzeige aktualisiert sich über Live-Ereignisse */
    }
  };

  const openNewChat = (cid: number) => {
    setNewChat(false);
    setNewGroup(false);
    chatsQ.reload();
    navigate(chatPath(cid));
  };

  let main;
  if (openChat) {
    main = device ? (
      <ChatView key={openChat} chatId={openChat} device={device} backTo={listPath} onGone={() => navigate(listPath, { replace: true })} onDevices={() => setDevicesOpen(true)} />
    ) : devError ? (
      <Alert
        kind="error"
        title="Verschlüsselung auf diesem Gerät nicht verfügbar"
        action={
          <button type="button" className="btn btn-sm" onClick={retry}>
            Erneut versuchen
          </button>
        }
      >
        {errorMessage(devError)}
      </Alert>
    ) : (
      <Loading label="Schlüssel werden vorbereitet …" />
    );
  } else if (openLetter) {
    main = <ConversationView key={openLetter} id={openLetter} filter={filter} settings={settings} showBack={narrow} />;
  } else if (openNotices) {
    main = (
      <section className="nm-notices" aria-label="Mitteilungen">
        <Link to={listPath} className="btn btn-sm btn-ghost nm-back">
          <Icon name="chevronLeft" /> Zurück zur Liste
        </Link>
        <AnnouncementsPanel />
      </section>
    );
  } else if (badKind) {
    main = <Alert kind="error">Diese Unterhaltung gibt es nicht.</Alert>;
  } else {
    main = (
      <div className="card pf-placeholder">
        <Glyph name="mail" size={44} />
        <p>Wählen Sie links eine Unterhaltung oder starten Sie mit „Neu“.</p>
        <p className="small muted">
          <Glyph name="lock" size={14} /> Verschlüsselt
          <HelpTip>
            Chats sind Ende-zu-Ende-verschlüsselt, Briefe und Anhänge werden verschlüsselt gespeichert.
            {settings ? ` ${retentionText(settings.retention_days)}` : ''}
          </HelpTip>
        </p>
      </div>
    );
  }

  return (
    <div className={`page nm-page${hasThread ? ' nm-has-thread' : ''}`}>
      <div className="page-head pf-head nm-head">
        <h1>Nachrichten</h1>
        <div className="pf-head-actions">
          <NewMenu mailAccounts={(accountsQ.data?.accounts.length ?? 0) > 0} onChat={() => setNewChat(true)} onGroup={() => setNewGroup(true)} />
          <Link to="/nachrichten/einstellungen" className="btn btn-ghost btn-icon" aria-label="Einstellungen der Nachrichten" title="Einstellungen">
            <Glyph name="cog" size={20} />
          </Link>
        </div>
      </div>
      {device && <NewDeviceBanner device={device} onOpen={() => setDevicesOpen(true)} />}
      {suspended && (
        <Alert kind="warning" title="Senden gesperrt">
          {suspended}
          {settings?.suspension_reason ? ` Grund: ${settings.suspension_reason}` : ''}
        </Alert>
      )}
      <div className={`pf-layout nm-layout${hasThread ? ' pf-layout-thread' : ''}`}>
        <aside className="card pf-sidebar nm-sidebar" aria-label="Unterhaltungen">
          <nav className="nm-chips" aria-label="Filter">
            {chips.map((f) => {
              const n = chipCount(f.key);
              const active = f.key === filter;
              return (
                <Link
                  key={f.key}
                  to={{ pathname: location.pathname, search: filterQuery(f.key) }}
                  replace
                  className={`nm-chip${active ? ' active' : ''}`}
                  aria-current={active ? 'true' : undefined}
                >
                  {f.label}
                  {n > 0 && f.key !== 'entwuerfe' && (
                    <span className="pf-pill pf-pill-sm">
                      {n}
                      <span className="sr-only"> ungelesen</span>
                    </span>
                  )}
                  {n > 0 && f.key === 'entwuerfe' && <span className="nm-chip-n">{n}</span>}
                </Link>
              );
            })}
          </nav>
          {filter !== 'entwuerfe' && (
            <div className="pf-tools">
              <div className="pf-search">
                <label htmlFor={searchId} className="sr-only">
                  In den Nachrichten suchen
                </label>
                <Icon name="search" />
                <input id={searchId} type="search" value={query} placeholder="Suchen" maxLength={100} autoComplete="off" onChange={(e) => setQuery(e.target.value)} />
              </div>
              {filter !== 'mitteilungen' && filter !== 'archiv' && (
                <div className="pf-tools-row">
                  <label className="check">
                    <input type="checkbox" checked={onlyUnread} onChange={(e) => setOnlyUnread(e.target.checked)} /> Nur ungelesene
                  </label>
                  {(mailQ.data?.counts.unread ?? 0) > 0 && (
                    <AsyncButton className="btn btn-ghost btn-sm" onClick={readAll}>
                      Briefe als gelesen
                    </AsyncButton>
                  )}
                </div>
              )}
            </div>
          )}
          <p className="sr-only" aria-live="polite">
            {filter === 'entwuerfe' ? '' : debounced ? `${plural(merged.length, 'Treffer', 'Treffer')} für „${debounced}“` : plural(merged.length, 'Unterhaltung', 'Unterhaltungen')}
          </p>
          {filter === 'entwuerfe' ? (
            <DraftList drafts={drafts} onChanged={draftsQ.reload} />
          ) : (
            <>
              {error ? <ErrorBox error={error} onRetry={() => (chatsQ.error ? chatsQ.reload() : mailQ.reload())} /> : null}
              {loading && <Loading />}
              {!loading && !error && !shown.length && <Empty icon={debounced ? 'search' : 'info'}>{debounced ? 'Nichts gefunden.' : onlyUnread ? 'Nichts Ungelesenes.' : EMPTY_TEXT[filter]}</Empty>}
              {mailQ.data?.search?.truncated && wantMail && <p className="xsmall muted pf-note-line">Durchsucht wurden die neuesten {mailQ.data.search.scanned_messages} Nachrichten.</p>}
              {shown.length > 0 && (
                <ul className="pf-list">
                  {shown.map((item) => (
                    <ItemRow key={item.key} item={item} filter={filter} selected={item.key === selectedKey || (openNotices && item.type === 'mitteilung')} />
                  ))}
                </ul>
              )}
              {hasMore && (
                <div className="pf-more">
                  <button
                    type="button"
                    className="btn btn-sm"
                    onClick={() => {
                      if (merged.length <= PAGE * pages && limit < MAX_LIST) setPages((p) => p + 1);
                      else setPages((p) => p + 1);
                    }}
                  >
                    Weitere laden
                  </button>
                </div>
              )}
              {capped && <p className="xsmall muted pf-more">Ältere Briefe finden Sie über die Suche.</p>}
            </>
          )}
        </aside>
        <section className="pf-main nm-main" aria-label="Geöffnete Unterhaltung">
          {main}
        </section>
      </div>
      {newChat && <NewChatModal onClose={() => setNewChat(false)} onOpen={openNewChat} />}
      {newGroup && <NewGroupModal onClose={() => setNewGroup(false)} onCreated={openNewChat} />}
      {devicesOpen && device && (
        <DevicesModal
          device={device}
          initialCode={linkCode}
          onClose={() => {
            setDevicesOpen(false);
            if (linkCode) setParams({}, { replace: true });
          }}
        />
      )}
    </div>
  );
}

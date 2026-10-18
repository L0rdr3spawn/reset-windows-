/**
 * Bausteine der Chats (Einzelchats, eigene Gruppen, Klassenchats mit/ohne Lehrkräfte, Elternchats), eingebunden in die
 * Seite „Nachrichten“ (`features/nachrichten`). Ende-zu-Ende-verschlüsselt (siehe `crypto.ts`): der Server sieht keine
 * Inhalte. Der Chat hat oben ein Zahnrad; dahinter liegen Stumm/Archiv, Mitglieder und Rechte, Geräte und Schlüssel.
 */
import { useEffect, useMemo, useRef, useState, type ClipboardEvent, type DragEvent } from 'react';
import { Link } from 'react-router-dom';
import { ApiError } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton, ErrorBox, Loading } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useDebounced } from '../../hooks/misc';
import { can } from '../../lib/permissions';
import { formatDate, todayISO } from '../../lib/dates';
import { isEmojiOnly, truncateText } from '../../lib/emoji';
import { Avatar, Glyph } from '../messages/components';
import { Composer } from '../nachrichten/Composer';
import { messagesApi } from '../messages/api';
import { RecipientPicker } from '../messages/RecipientPicker';
import type { Recipient } from '../messages/types';
import '../messages/messages.css';
import { chatsApi, type ChatDetail, type ChatMessage, type ClassPick, type PostMode } from './api';
import { learnApi, type ChatPollMeta, type PollInput } from '../lernen/api';
import { PollCard } from '../lernen/PollCard';
import { PollDialog } from '../lernen/PollDialog';
import { encryptImage, ensureDevice, MAX_IMAGES, open, seal, type ImageRef, type LocalDevice, type MemberDevice, type Payload } from './crypto';
import { detectKeyChanges, loadSeen, saveSeen } from './keys';
import { ChatImage, fetchImageBase64, imageFiles, ImageError, PendingImages, readImageFile, type PendingImage } from './images';
import './chats.css';
import { confirmAsk } from '../../lib/confirm';

const userIds = (list: Recipient[]) => list.flatMap((r) => (r.type === 'user' && r.id != null ? [r.id] : []));

export function timeOf(iso: string): string {
  const d = iso.slice(0, 10);
  const local = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`);
  const hm = local.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  return d === todayISO() ? hm : `${formatDate(d)} ${hm}`;
}

// ---------------------------------------------------------------------------------------------- Gerät
/** Schlüsselgerät dieses Browsers; wird erst angelegt, wenn `enabled` (ein Chat geöffnet wird), nicht schon beim Lesen von Briefen. */
export function useDevice(userId: number | string, enabled = true) {
  const [device, setDevice] = useState<LocalDevice | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [key, setKey] = useState(0);
  useEffect(() => {
    if (!enabled) return undefined;
    let alive = true;
    setError(null);
    ensureDevice(userId).then(
      (d) => alive && setDevice(d),
      (e) => alive && setError(e),
    );
    return () => {
      alive = false;
    };
  }, [userId, key, enabled]);
  return { device, error, retry: () => setKey((k) => k + 1) };
}

// ---------------------------------------------------------------------------------------------- Neue Gruppe
const POST_MODES: [PostMode, string][] = [
  ['all', 'Alle Mitglieder schreiben'],
  ['admins', 'Nur Admins schreiben, alle anderen lesen'],
  ['selected', 'Ausgewählte Mitglieder schreiben'],
];
const POST_MODE_HINT: Record<PostMode, string> = {
  all: 'Jedes Mitglied darf Nachrichten senden.',
  admins: 'Zum Beispiel Lehrkraft-Chat mit Schüler/innen: Admins schreiben, die anderen können nur lesen.',
  selected: 'Admins und freigegebene Mitglieder schreiben; wen Sie freigeben, legen Sie danach unter „Mitglieder“ fest.',
};

export function NewGroupModal({ onClose, onCreated }: { onClose: () => void; onCreated: (id: number) => void }) {
  const toast = useToast();
  const [people, setPeople] = useState<Recipient[]>([]);
  const [title, setTitle] = useState('');
  const opts = useApi((signal) => chatsApi.classOptions(signal), []);
  const classes = opts.data?.classes ?? [];
  const [classId, setClassId] = useState('');
  const cls = classes.find((c) => c.class_id === classId);
  const [mode, setMode] = useState<'schueler' | 'schueler_lehrer' | 'eltern'>('schueler');
  const [postMode, setPostMode] = useState<PostMode>('all');
  const modes = cls
    ? ([
        cls.students && ['schueler', 'Schüler/innen (ohne Lehrkräfte)'],
        cls.students && cls.teachers && ['schueler_lehrer', 'Schüler/innen mit Lehrkräften'],
        cls.parents && ['eltern', 'Eltern der Klasse'],
      ].filter(Boolean) as [typeof mode, string][])
    : [];
  const effMode = modes.some(([m]) => m === mode) ? mode : modes[0]?.[0];

  const create = async () => {
    try {
      const picks: ClassPick[] =
        cls && effMode ? [{ class_id: cls.class_id, students: effMode !== 'eltern', teachers: effMode === 'schueler_lehrer', parents: effMode === 'eltern' }] : [];
      const ids = userIds(people);
      if (!ids.length && !picks.length) throw new Error('Bitte Personen oder eine Klasse hinzufügen.');
      const chat = await chatsApi.create({ kind: 'group', title, user_ids: ids, classes: picks, post_mode: postMode });
      onCreated(chat.id);
    } catch (e) {
      toast.error(e, 'Gruppe');
    }
  };

  return (
    <Modal
      title="Neue Gruppe"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={create}>
            <Icon name="plus" /> Gruppe erstellen
          </AsyncButton>
        </>
      }
    >
      <div className="stack">
        <div className="field">
          <label htmlFor="ng-title">Name der Gruppe</label>
          <input id="ng-title" value={title} maxLength={80} onChange={(e) => setTitle(e.target.value)} placeholder="z. B. Lerngruppe Mathe" />
        </div>
        <div className="field">
          <label htmlFor="ng-people">Mitglieder</label>
          <RecipientPicker inputId="ng-people" value={people} onChange={(list) => setPeople(list.filter((r) => r.type === 'user'))} placeholder="Namen suchen und hinzufügen …" />
        </div>
        {classes.length > 0 && (
          <div className="field">
            <label htmlFor="ng-class">Ganze Klasse hinzufügen (optional)</label>
            <select id="ng-class" value={classId} onChange={(e) => setClassId(e.target.value)}>
              <option value="">– keine –</option>
              {classes.map((c) => (
                <option key={c.class_id} value={c.class_id}>
                  {c.name}
                </option>
              ))}
            </select>
            {cls && (
              <div className="stack-xs" style={{ marginTop: 6 }}>
                {modes.map(([m, label]) => (
                  <label key={m} className="check">
                    <input type="radio" name="ng-mode" checked={effMode === m} onChange={() => setMode(m)} /> {label}
                  </label>
                ))}
              </div>
            )}
          </div>
        )}
        <div className="field">
          <label htmlFor="ng-post">Wer darf schreiben?</label>
          <select id="ng-post" value={postMode} onChange={(e) => setPostMode(e.target.value as PostMode)}>
            {POST_MODES.map(([m, label]) => (
              <option key={m} value={m}>
                {label}
              </option>
            ))}
          </select>
          <span className="xsmall muted">{POST_MODE_HINT[postMode]}</span>
        </div>
        <p className="xsmall muted">
          <Icon name="lock" /> Ende-zu-Ende-verschlüsselt. Wer später dazukommt, sieht ältere Nachrichten nicht.
        </p>
      </div>
    </Modal>
  );
}

// ---------------------------------------------------------------------------------------------- Personensuche
export function PersonSearch({ onOpen }: { onOpen: (chatId: number) => void }) {
  const toast = useToast();
  const [q, setQ] = useState('');
  const query = useDebounced(q.trim(), 250);
  const res = useApi((signal) => (query.length >= 2 ? messagesApi.recipients(query, signal) : Promise.resolve(null)), [query]);
  const people = (res.data?.people ?? []).filter((p) => p.type === 'user' && p.id != null);
  const start = async (id: number) => {
    try {
      const chat = await chatsApi.create({ kind: 'direct', user_ids: [id] });
      setQ('');
      onOpen(chat.id);
    } catch (e) {
      toast.error(e, 'Chat');
    }
  };
  return (
    <div className="ch-search">
      <label htmlFor="ch-people" className="sr-only">
        Person suchen
      </label>
      <input id="ch-people" type="search" placeholder="Person suchen und anschreiben …" value={q} onChange={(e) => setQ(e.target.value)} autoComplete="off" />
      {query.length >= 2 && (
        <ul className="pf-list ch-search-results" aria-label="Gefundene Personen">
          {res.loading && !res.data && <li className="small muted ch-pad">Suche …</li>}
          {res.data && !people.length && <li className="small muted ch-pad">Niemand gefunden.</li>}
          {people.map((p) => (
            <li key={p.id}>
              <button type="button" className="pf-item" onClick={() => start(p.id as number)}>
                <Avatar name={p.name} role={p.role} size={32} />
                <span className="pf-item-main">
                  <strong>{p.name}</strong>
                  <span className="xsmall muted">{[p.role_label, p.info].filter(Boolean).join(' · ')}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------------------------- Mitglieder
function ChatSettings({ chat, onClose, onLeft, onDevices }: { chat: ChatDetail; onClose: () => void; onLeft: () => void; onDevices: () => void }) {
  const toast = useToast();
  const user = useUser();
  const moderator = can(user, 'messages.moderate');
  const [title, setTitle] = useState(chat.title);
  const [add, setAdd] = useState<Recipient[]>([]);
  const group = chat.kind === 'group';
  const run = async (fn: () => Promise<unknown>) => {
    try {
      await fn();
    } catch (e) {
      toast.error(e, 'Chat');
    }
  };
  return (
    <Modal title={group ? 'Einstellungen der Gruppe' : 'Einstellungen des Chats'} onClose={onClose} variant="drawer">
      <div className="stack">
        <label className="check">
          <input type="checkbox" checked={chat.muted} onChange={(e) => run(() => chatsApi.patch(chat.id, { muted: e.target.checked }))} /> Stumm (nicht im Zähler)
        </label>
        <label className="check">
          <input type="checkbox" checked={chat.archived} onChange={(e) => run(() => chatsApi.patch(chat.id, { archived: e.target.checked }))} /> Archiviert (nur für Sie; neue Nachrichten holen den Chat zurück, außer er ist stumm)
        </label>
        {group && chat.admin && (
          <div className="stack-sm">
            <div className="field">
              <label htmlFor="cm-title">Name</label>
              <div className="row">
                <input id="cm-title" value={title} maxLength={80} onChange={(e) => setTitle(e.target.value)} />
                <AsyncButton className="btn btn-sm" disabled={!title.trim() || title === chat.title} onClick={() => run(() => chatsApi.patch(chat.id, { title }))}>
                  Speichern
                </AsyncButton>
              </div>
            </div>
            <fieldset className="stack-xs" style={{ border: 0, padding: 0, margin: 0 }}>
              <legend className="small">
                <strong>Wer darf schreiben?</strong>
              </legend>
              {POST_MODES.map(([m, label]) => (
                <label key={m} className="check">
                  <input type="radio" name="cm-post" checked={chat.post_mode === m} onChange={() => run(() => chatsApi.patch(chat.id, { post_mode: m }))} /> {label}
                </label>
              ))}
              <span className="xsmall muted">{POST_MODE_HINT[chat.post_mode]}</span>
            </fieldset>
          </div>
        )}
        <h3 style={{ margin: 0 }}>{group ? `${chat.members.length} Mitglieder` : 'Details'}</h3>
        <ul className="pf-list">
          {chat.members.map((m) => (
            <li key={m.id ?? m.name} className="ch-member">
              <Avatar name={m.name} role={m.role} size={32} />
              <span className="ch-member-main">
                <strong>{m.name}</strong>
                {m.me && <span className="muted small"> (Sie)</span>}
                {m.admin && group && <span className="badge badge-info" style={{ marginLeft: 6 }}>Admin</span>}
                {group && !m.admin && !m.can_post && <span className="badge" style={{ marginLeft: 6 }}>nur lesen</span>}
                <span className="xsmall muted">{[m.role_label, m.info].filter(Boolean).join(' · ')}</span>
              </span>
              {group && chat.admin && !m.me && m.id != null && (
                <span className="row">
                  {chat.post_mode === 'selected' && !m.admin && (
                    <AsyncButton className="btn btn-sm btn-ghost" onClick={() => run(() => chatsApi.setCanPost(chat.id, m.id as number, !m.can_post))}>
                      {m.can_post ? 'Nur lesen' : 'Darf schreiben'}
                    </AsyncButton>
                  )}
                  <AsyncButton className="btn btn-sm btn-ghost" onClick={() => run(() => chatsApi.setAdmin(chat.id, m.id as number, !m.admin))}>
                    {m.admin ? 'Admin entziehen' : 'Zum Admin'}
                  </AsyncButton>
                  <AsyncButton className="btn btn-sm btn-ghost" confirm={`${m.name} aus dem Chat entfernen?`} onClick={() => run(() => chatsApi.removeMember(chat.id, m.id as number))}>
                    Entfernen
                  </AsyncButton>
                </span>
              )}
            </li>
          ))}
        </ul>
        {group && chat.admin && (
          <div className="stack-sm">
            <div className="field">
              <label htmlFor="cm-add">Personen hinzufügen</label>
              <RecipientPicker inputId="cm-add" value={add} onChange={(l) => setAdd(l.filter((r) => r.type === 'user'))} placeholder="Name suchen …" />
            </div>
            <AsyncButton
              className="btn btn-sm"
              disabled={!add.length}
              onClick={() =>
                run(async () => {
                  await chatsApi.addMembers(chat.id, { user_ids: userIds(add) });
                  setAdd([]);
                })
              }
            >
              <Icon name="plus" /> Hinzufügen
            </AsyncButton>
          </div>
        )}
        <div className="stack-xs">
          <button
            type="button"
            className="btn"
            onClick={() => {
              onClose();
              onDevices();
            }}
          >
            <Icon name="lock" /> Geräte &amp; Schlüssel
          </button>
          {moderator && (
            <Link to="/nachrichten/chat-meldungen" className="btn">
              <Icon name="shield" /> Gemeldete Chat-Nachrichten
            </Link>
          )}
          <span className="xsmall muted">
            <Icon name="lock" /> Ende-zu-Ende-verschlüsselt
            <HelpTip>Nur die Mitglieder können die Nachrichten lesen, auch die Schule nicht.</HelpTip> <Link to="/datenschutz">Datenschutz</Link>
          </span>
        </div>
        <AsyncButton
          className="btn btn-danger"
          confirm={group ? 'Gruppe verlassen?' : 'Chat verlassen? Er verschwindet aus Ihrer Liste.'}
          onClick={() =>
            run(async () => {
              await chatsApi.removeMember(chat.id, Number(user.id));
              onLeft();
            })
          }
        >
          {group ? 'Gruppe verlassen' : 'Chat verlassen'}
        </AsyncButton>
      </div>
    </Modal>
  );
}

// ---------------------------------------------------------------------------------------------- Unterhaltung
interface Shown extends ChatMessage {
  payload: Payload | null;
}

/** Kurztext für Antwort-Zitate. */
function quoteText(p: Payload): string {
  const t = p.text.trim();
  if (p.poll) return `📊 Umfrage: ${truncateText(t, 140)}`;
  if (t) return truncateText(t, 160);
  return p.images?.length ? '📷 Bild' : '';
}

function Bubble({
  chatId,
  m,
  quoted,
  group,
  onReply,
  onDelete,
  onReport,
  onPollChanged,
}: {
  chatId: number;
  m: Shown;
  quoted: Shown | undefined;
  group: boolean;
  onReply: () => void;
  onDelete: () => void;
  onReport: () => void;
  onPollChanged: () => void;
}) {
  if (m.system_text && !m.sender_id) {
    return (
      <li className="ch-system" id={`m${m.id}`}>
        <span>{m.system_text}</span>
      </li>
    );
  }
  const text = m.deleted ? (m.system_text || 'Nachricht gelöscht') : m.payload ? m.payload.text : null;
  const images = m.deleted ? [] : m.payload?.images ?? [];
  return (
    <li className={`pf-msg ${m.mine ? 'pf-msg-own' : 'pf-msg-other'}`} id={`m${m.id}`}>
      <div className="pf-bubble ch-bubble">
        {group && !m.mine && <div className="pf-sender"><strong>{m.sender_name}</strong></div>}
        {quoted && (
          <a className="ch-quote" href={`#m${quoted.id}`}>
            <strong>{quoted.mine ? 'Sie' : quoted.sender_name}</strong>
            <span>{quoted.deleted ? 'Nachricht gelöscht' : quoted.payload ? quoteText(quoted.payload) : '🔒 nicht lesbar'}</span>
          </a>
        )}
        {text === null ? (
          <div className="pf-text muted">
            <Icon name="lock" /> Auf diesem Gerät nicht lesbar (vor der Einrichtung des Geräts gesendet).
          </div>
        ) : !m.deleted && m.poll && m.payload?.poll && m.payload.poll.options.length === m.poll.option_count ? (
          <div className="ln-chat-poll">
            <PollCard
              compact
              question={<span>{m.payload.text}</span>}
              options={m.payload.poll.options}
              poll={m.poll}
              onVote={async (choices) => {
                await learnApi.chatVote(chatId, m.id, choices);
                onPollChanged();
              }}
              onClose={
                m.mine && !m.poll.closed
                  ? async () => {
                      await learnApi.chatClose(chatId, m.id);
                      onPollChanged();
                    }
                  : undefined
              }
            />
          </div>
        ) : (
          <>
            {images.map((img) => (
              <ChatImage key={img.id} chatId={chatId} image={img} />
            ))}
            {(text || !images.length) && (
              <div className={`pf-text${m.deleted ? ' muted' : ''}${!m.deleted && isEmojiOnly(text) ? ' emoji-only' : ''}`}>{text}</div>
            )}
          </>
        )}
        <div className="ch-meta">
          <span className="xsmall muted">{timeOf(m.created_at)}</span>
          {m.imported && !m.deleted && (
            <span className="xsmall muted" title="Aus dem Postfach übernommen (serverseitig verschlüsselt)">
              aus dem Postfach
            </span>
          )}
          {!m.deleted && (
            <span className="ch-actions">
              <button type="button" className="btn btn-ghost btn-xs" onClick={onReply}>
                Antworten
              </button>
              {m.mine ? (
                <button type="button" className="btn btn-ghost btn-xs" onClick={onDelete}>
                  Löschen
                </button>
              ) : m.reported ? (
                <span className="badge badge-warning" title="Die Schulleitung prüft Ihre Meldung.">
                  gemeldet
                </span>
              ) : (
                <button type="button" className="btn btn-ghost btn-xs" onClick={onReport}>
                  Melden
                </button>
              )}
            </span>
          )}
        </div>
      </div>
    </li>
  );
}

export function ChatView({ chatId, device, backTo, onGone, onDevices }: { chatId: number; device: LocalDevice; backTo?: string; onGone: () => void; onDevices: () => void }) {
  const toast = useToast();
  const detail = useApi((signal) => chatsApi.detail(chatId, signal), [chatId], { live: ['chats'] });
  const latest = useApi((signal) => chatsApi.messages(chatId, device.deviceId, undefined, signal), [chatId, device.deviceId], { live: ['chats'] });
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [older, setOlder] = useState<ChatMessage[]>([]);
  const [more, setMore] = useState<boolean | null>(null);
  const [text, setText] = useState('');
  const [replyTo, setReplyTo] = useState<Shown | null>(null);
  const [settings, setSettings] = useState(false);
  const [reportFor, setReportFor] = useState<Shown | null>(null);
  const [images, setImages] = useState<PendingImage[]>([]);
  const [pollOpen, setPollOpen] = useState(false);
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const cache = useRef(new Map<number, Payload | null>());

  useEffect(() => {
    setOlder([]);
    setMore(null);
    setReplyTo(null);
    setText('');
    setImages((list) => {
      list.forEach((p) => URL.revokeObjectURL(p.previewUrl));
      return [];
    });
    cache.current = new Map();
  }, [chatId]);

  const addImages = async (files: File[]) => {
    let count = images.length;
    for (const f of files) {
      if (count >= MAX_IMAGES) {
        toast.error(new Error(`Höchstens ${MAX_IMAGES} Bilder je Nachricht.`));
        break;
      }
      try {
        const p = await readImageFile(f);
        count += 1;
        setImages((list) => (list.length >= MAX_IMAGES ? list : [...list, p]));
      } catch (e) {
        toast.error(e instanceof ImageError ? e : new Error('Das Bild konnte nicht gelesen werden.'));
      }
    }
  };
  const removeImage = (key: string) =>
    setImages((list) => {
      list.filter((p) => p.key === key).forEach((p) => URL.revokeObjectURL(p.previewUrl));
      return list.filter((p) => p.key !== key);
    });
  const onPaste = (e: ClipboardEvent<HTMLTextAreaElement>) => {
    const files = imageFiles(e.clipboardData?.items);
    if (files.length) {
      e.preventDefault();
      void addImages(files);
    }
  };
  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    void addImages(imageFiles(e.dataTransfer?.files));
  };

  const shown: Shown[] = useMemo(() => {
    const seen = new Set<number>();
    const all = [...older, ...(latest.data?.messages ?? [])].filter((m) => (seen.has(m.id) ? false : (seen.add(m.id), true)));
    return all.map((m) => {
      if (!cache.current.has(m.id) || m.deleted || (cache.current.get(m.id) === null && m.key)) cache.current.set(m.id, m.deleted ? null : m.imported ? { v: 1, text: m.legacy_text ?? '' } : open(m, device));
      return { ...m, payload: cache.current.get(m.id) ?? null };
    });
  }, [older, latest.data, device]);
  const byId = useMemo(() => new Map(shown.map((m) => [m.id, m])), [shown]);
  const lastId = shown.length ? shown[shown.length - 1].id : 0;
  const hasMore = more ?? latest.data?.more ?? false;

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'end' });
    if (lastId && latest.data && lastId > latest.data.last_read_id) chatsApi.read(chatId, lastId).catch(() => undefined);
  }, [lastId, chatId, latest.data]);

  useEffect(() => {
    if (detail.error instanceof ApiError && detail.error.status === 404) onGone();
  }, [detail.error, onGone]);

  const loadOlder = async () => {
    const first = shown[0]?.id;
    if (!first) return;
    try {
      const r = await chatsApi.messages(chatId, device.deviceId, first);
      setOlder((o) => [...r.messages, ...o]);
      setMore(r.more);
    } catch (e) {
      toast.error(e);
    }
  };

  /** Nachricht verschluesseln und senden; bei geaenderten Geraeten einmal mit der neuen Liste wiederholen. */
  const deliver = async (payload: Payload, extra: { attachment_ids?: string[]; poll?: ChatPollMeta } = {}) => {
    const attempt = async (devices: MemberDevice[]) =>
      chatsApi.send(chatId, { ...seal(payload, devices, device), device_id: device.deviceId, reply_to: replyTo?.id ?? null, attachment_ids: extra.attachment_ids ?? [], poll: extra.poll });
    const { devices } = await chatsApi.devices(chatId);
    try {
      await attempt(devices);
    } catch (e) {
      const d = e instanceof ApiError ? (e.detail as { code?: string; devices?: MemberDevice[] } | null) : null;
      if (e instanceof ApiError && e.status === 409 && d?.code === 'devices_changed' && d.devices) await attempt(d.devices);
      else throw e;
    }
    setReplyTo(null);
    latest.reload();
  };

  /** Umfrage: Frage und Antworten nur im verschluesselten Inhalt, der Server bekommt Einstellungen und Zahl der Antworten. */
  const sendPoll = async (input: PollInput) => {
    const payload: Payload = { v: 1, text: input.question, poll: { options: input.options } };
    await deliver(payload, {
      poll: { option_count: input.options.length, multiple: input.multiple, max_choices: input.max_choices, anonymous: input.anonymous, results: input.results, ends_at: input.ends_at },
    });
  };

  const sending = useRef(false);
  const send = async () => {
    const body = text.trim();
    if ((!body && !images.length) || sending.current) return;
    sending.current = true;
    try {
      // Bilder zuerst im Browser verschlüsseln und als Blob hochladen – der Server sieht nur Zufallsbytes
      const refs: ImageRef[] = [];
      for (const img of images) {
        const enc = encryptImage(img.bytes);
        const up = await chatsApi.uploadImage(chatId, enc.blob);
        refs.push({ id: up.id, key: enc.key, nonce: enc.nonce, mime: img.mime, name: img.name, size: img.bytes.length });
      }
      const payload: Payload = refs.length ? { v: 1, text: body, images: refs } : { v: 1, text: body };
      await deliver(payload, { attachment_ids: refs.map((r) => r.id) });
      setText('');
      images.forEach((p) => URL.revokeObjectURL(p.previewUrl));
      setImages([]);
    } catch (e) {
      toast.error(e, 'Senden');
    } finally {
      sending.current = false;
      inputRef.current?.focus();
    }
  };

  // Schlüsselwechsel bei Gesprächspartnern (wie die Sicherheitsnummer bei Signal)
  const memberDevices = useApi(() => chatsApi.devices(chatId).then((r) => r.devices, () => [] as MemberDevice[]), [chatId], { live: ['chats'] });
  const [ackTick, setAckTick] = useState(0);
  const keyCheck = useMemo(() => {
    void ackTick;
    return detectKeyChanges(loadSeen(device.userId), memberDevices.data ?? [], device.userId);
  }, [memberDevices.data, device.userId, ackTick]);
  useEffect(() => {
    // erster Kontakt: still merken (Änderungen bleiben bis zum Bestätigen sichtbar)
    if (memberDevices.data && !keyCheck.changes.length) saveSeen(device.userId, keyCheck.next);
  }, [memberDevices.data, keyCheck, device.userId]);
  const unreadable = shown.some((m) => !m.deleted && !m.imported && !m.system_text && m.ciphertext && !m.payload);

  const chat = detail.data;
  if (detail.error && !(detail.error instanceof ApiError && detail.error.status === 404)) return <ErrorBox error={detail.error} onRetry={detail.reload} />;
  if (!chat) return <Loading />;
  const group = chat.kind === 'group';

  return (
    <section className="card ch-view" aria-label={`Chat ${chat.title}`}>
      <div className="card-head ch-head">
        <span className="row ch-head-who">
          {backTo && (
            <Link to={backTo} className="btn btn-ghost btn-sm ch-back" aria-label="Zurück zur Liste">
              <Icon name="chevronLeft" />
            </Link>
          )}
          <Avatar name={chat.title} group={group} glyph={group ? 'people' : undefined} size={36} />
          <span className="stack-xs ch-head-text">
            <strong className="ch-ellipsis">{chat.title}</strong>
            <span className="xsmall muted ch-ellipsis">
              <Icon name="lock" /> Ende-zu-Ende-verschlüsselt{group ? ` · ${chat.members.length} Mitglieder` : ''}
              {chat.muted ? ' · stumm' : ''}
            </span>
          </span>
        </span>
        <button type="button" className="btn btn-ghost btn-icon" aria-label="Einstellungen" title="Einstellungen" onClick={() => setSettings(true)}>
          <Glyph name="cog" size={20} />
        </button>
      </div>
      {chat.has_imported && (
        <p className="xsmall muted ch-compose" style={{ margin: 0 }}>
          <Icon name="info" /> Älterer Verlauf stammt aus dem Postfach.
          <HelpTip>Diese Nachrichten sind serverseitig verschlüsselt (nicht Ende-zu-Ende); alles Neue ist Ende-zu-Ende-verschlüsselt.</HelpTip>
        </p>
      )}
      {keyCheck.changes.map((c) => {
        const who = chat.members.find((m) => m.id === c.userId)?.name ?? 'Eine Person';
        return (
          <Alert
            key={c.userId}
            kind={c.kind === 'changed' ? 'warning' : 'info'}
            title={c.kind === 'changed' ? `Der Sicherheitsschlüssel von ${who} hat sich geändert` : `${who} verwendet ein weiteres Gerät`}
            action={
              <button
                type="button"
                className="btn btn-sm"
                onClick={() => {
                  saveSeen(device.userId, keyCheck.next);
                  setAckTick((n) => n + 1);
                }}
              >
                Verstanden
              </button>
            }
          >
            {c.kind === 'changed'
              ? 'Das passiert, wenn die Person ein Gerät neu einrichtet oder zurücksetzt. Fragen Sie im Zweifel auf anderem Weg nach. Neuer Schlüssel: '
              : 'Neuer Schlüssel: '}
            <code className="mono">{c.fingerprints.join(' · ')}</code>
          </Alert>
        );
      })}
      {unreadable && (
        <Alert
          kind="info"
          action={
            <button type="button" className="btn btn-sm" onClick={onDevices}>
              Verlauf übertragen
            </button>
          }
        >
          Ältere Nachrichten sind auf diesem Gerät nicht lesbar.
        </Alert>
      )}
      <div className="ch-scroll">
        {hasMore && (
          <div style={{ textAlign: 'center' }}>
            <AsyncButton className="btn btn-sm btn-ghost" onClick={loadOlder}>
              Ältere Nachrichten laden
            </AsyncButton>
          </div>
        )}
        {latest.error ? <ErrorBox error={latest.error} onRetry={latest.reload} /> : null}
        {!latest.data && latest.loading && <Loading />}
        {latest.data && !shown.length && <p className="muted small" style={{ textAlign: 'center' }}>Noch keine Nachrichten.</p>}
        <ul className="pf-msgs">
          {shown.map((m) => (
            <Bubble
              key={m.id}
              chatId={chatId}
              m={m}
              group={group}
              quoted={m.reply_to ? byId.get(m.reply_to) : undefined}
              onReply={() => {
                setReplyTo(m);
                inputRef.current?.focus();
              }}
              onReport={() => setReportFor(m)}
              onPollChanged={latest.reload}
              onDelete={async () => {
                if (!(await confirmAsk({ title: 'Nachricht löschen', message: 'Nachricht für alle löschen?', confirmLabel: 'Löschen', danger: true }))) return;
                try {
                  await chatsApi.remove(chatId, m.id);
                  latest.reload();
                } catch (e) {
                  toast.error(e);
                }
              }}
            />
          ))}
        </ul>
        <div ref={endRef} />
      </div>
      {chat.can_post ? (
        <div
          className={`ch-compose${dragging ? ' ch-drop' : ''}`}
          onDragOver={(e) => {
            if (e.dataTransfer?.types.includes('Files')) {
              e.preventDefault();
              setDragging(true);
            }
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          {replyTo && (
            <div className="ch-replybar">
              <span className="small">
                Antwort an <strong>{replyTo.mine ? 'Sie' : replyTo.sender_name}</strong>: {replyTo.payload ? truncateText(quoteText(replyTo.payload), 120) : '…'}
              </span>
              <button type="button" className="btn btn-icon btn-sm" aria-label="Antwort abbrechen" onClick={() => setReplyTo(null)}>
                <Icon name="x" />
              </button>
            </div>
          )}
          <PendingImages images={images} onRemove={removeImage} />
          <div className="ln-chat-tools">
            <button type="button" className="btn btn-ghost btn-xs" onClick={() => setPollOpen(true)}>
              <Icon name="list" /> Umfrage
            </button>
          </div>
          <Composer
            id="ch-text"
            value={text}
            onChange={setText}
            onSend={send}
            canSend={!!text.trim() || images.length > 0}
            maxLength={20000}
            label="Nachricht"
            placeholder="Nachricht"
            textRef={inputRef}
            attachLabel="Bilder anhängen"
            onAttach={() => fileRef.current?.click()}
            onPaste={onPaste}
          />
          <input
            ref={fileRef}
            type="file"
            accept="image/png,image/jpeg,image/gif,image/webp"
            multiple
            hidden
            onChange={(e) => {
              void addImages(Array.from(e.target.files ?? []));
              e.target.value = '';
            }}
          />
        </div>
      ) : (
        <p className="small muted ch-compose">
          <Icon name="lock" /> {chat.post_mode === 'admins' ? 'In dieser Gruppe schreiben nur die Admins – Sie können mitlesen.' : 'Sie haben in dieser Gruppe nur Leserechte.'}
        </p>
      )}
      {settings && <ChatSettings chat={chat} onClose={() => setSettings(false)} onLeft={onGone} onDevices={onDevices} />}
      {reportFor && <ReportModal chatId={chatId} m={reportFor} onClose={() => setReportFor(null)} />}
      {pollOpen && <PollDialog title="Neue Umfrage" submitLabel="Umfrage senden" onClose={() => setPollOpen(false)} onSubmit={sendPoll} />}
    </section>
  );
}

function ReportModal({ chatId, m, onClose }: { chatId: number; m: Shown; onClose: () => void }) {
  const toast = useToast();
  const [reason, setReason] = useState('');
  const [share, setShare] = useState(true);
  const images = m.payload?.images ?? [];
  const hasContent = !!m.payload?.text || images.length > 0;
  return (
    <Modal
      title="Nachricht melden"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton
            className="btn btn-danger"
            onClick={async () => {
              try {
                const shared: { data: string }[] = [];
                if (share) {
                  for (const img of images) {
                    const data = await fetchImageBase64(chatId, img);
                    if (data) shared.push({ data });
                  }
                }
                await chatsApi.report(chatId, m.id, { reason, content: share ? m.payload?.text ?? '' : '', images: shared });
                toast.success('Gemeldet. Die Schulleitung prüft die Meldung.');
                onClose();
              } catch (e) {
                toast.error(e);
              }
            }}
          >
            Melden
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        <p className="small">
          Die Schule kann verschlüsselte Nachrichten nicht lesen. Zur Prüfung wird der Inhalt dieser einen Nachricht (Text und Bilder) mitgeschickt.
        </p>
        {m.payload?.text && <blockquote className="ch-quote">{m.payload.text}</blockquote>}
        {!m.payload && <blockquote className="ch-quote">🔒 nicht lesbar</blockquote>}
        {images.map((img) => (
          <ChatImage key={img.id} chatId={chatId} image={img} small />
        ))}
        {hasContent && (
          <label className="check">
            <input type="checkbox" checked={share} onChange={(e) => setShare(e.target.checked)} /> Inhalt dieser Nachricht mitschicken
          </label>
        )}
        <div className="field">
          <label htmlFor="ch-rep">Was ist passiert? (optional)</label>
          <textarea id="ch-rep" rows={3} maxLength={1000} value={reason} onChange={(e) => setReason(e.target.value)} />
        </div>
      </div>
    </Modal>
  );
}

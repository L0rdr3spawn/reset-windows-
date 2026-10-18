/**
 * Ein Brief bzw. eine E-Mail im Chat-Stil: Kopf mit Betreff und Zahnrad (dahinter Archiv, stumm, ungelesen, blockieren,
 * für mich löschen, Teilnehmende), Verlauf nach Tagen (eigene Nachrichten rechts), Anhänge, Melden und eine
 * Eingabezeile mit „+“ für Anhänge und Senden-Pfeil (der Entwurf wird automatisch gespeichert).
 * Live-Aktualisierung über `useApi(…, { live: ['messages'] })`.
 */
import { Fragment, useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import { fileUrl, type StoredFileInfo } from '../../api/files';
import { canView, FileList } from '../../components/FileList';
import { FileUpload } from '../../components/FileUpload';
import { Modal } from '../../components/Modal';
import { AsyncButton, ErrorBox, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { isEmojiOnly } from '../../lib/emoji';
import { Composer } from '../nachrichten/Composer';
import { ATTACHMENT_PURPOSE, messagesApi } from './api';
import { Avatar, Glyph, KindTag, PersonLine, type GlyphName } from './components';
import { ReportDialog } from './dialogs';
import {
  audienceText,
  clock,
  chatPath,
  conversationPath,
  DEFAULT_LIMITS,
  folderPath,
  fullTime,
  groupByDay,
  linkify,
  mergeMessages,
  nearBottom,
  participantsText,
  plural,
  threadTitle,
  type InboxFilter,
} from './logic';
import type { ConversationDetail, ConversationDetailInfo, Message, MessageSettings, ReplyResponse } from './types';
import { confirmAsk } from '../../lib/confirm';

function MessageText({ text }: { text: string }) {
  const parts = useMemo(() => linkify(text), [text]);
  return (
    <div className={`pf-text${isEmojiOnly(text) ? ' emoji-only' : ''}`}>
      {parts.map((p, i) =>
        p.type === 'link' ? (
          <a key={i} href={p.href} target="_blank" rel="noopener noreferrer nofollow">
            {p.value}
          </a>
        ) : (
          <Fragment key={i}>{p.value}</Fragment>
        ),
      )}
    </div>
  );
}

/** Bilder/GIFs groß im Verlauf (GIFs bleiben animiert), alle anderen Dateien als Liste. */
function MessageAttachments({ files }: { files: StoredFileInfo[] }) {
  const isImage = (f: StoredFileInfo) => f.group === 'image' && canView(f) && f.kind !== 'heic';
  const images = files.filter(isImage);
  const others = files.filter((f) => !isImage(f));
  return (
    <>
      {images.map((f) => (
        <a key={f.id} className="pf-img-link" href={fileUrl(f.id, { inline: true })} target="_blank" rel="noopener noreferrer" title={`${f.filename} – in neuem Fenster öffnen`}>
          <img className="msg-img" src={fileUrl(f.id, { inline: true })} alt={f.filename} loading="lazy" />
          <span className="sr-only"> (neues Fenster)</span>
        </a>
      ))}
      {others.length > 0 && <FileList files={others} compact previews label="Anhänge" emptyText={null} />}
    </>
  );
}

function MessageItem({ m, showSender, onReport }: { m: Message; showSender: boolean; onReport: (m: Message) => void }) {
  return (
    <li className={`pf-msg ${m.own ? 'pf-msg-own' : 'pf-msg-other'}${m.unread ? ' pf-msg-unread' : ''}`} id={`pf-m-${m.id}`}>
      {!m.own && showSender && <Avatar name={m.sender.name} role={m.sender.role} size={32} />}
      <div className="pf-bubble">
        <span className="sr-only">
          {m.unread ? 'Neu. ' : ''}
          {m.own ? 'Sie' : m.sender.name}, {fullTime(m.created_at)}:
        </span>
        {!m.own && showSender && (
          <div className="pf-sender" aria-hidden="true">
            <PersonLine person={m.sender} />
          </div>
        )}
        {m.removed ? (
          <p className="pf-note">
            <Glyph name="shield" size={14} /> Diese Nachricht wurde von der Moderation entfernt.
          </p>
        ) : m.blocked_sender ? (
          <p className="pf-note">
            <Glyph name="ban" size={14} /> Nachricht einer von Ihnen blockierten Person – ausgeblendet.
          </p>
        ) : !m.integrity_ok ? (
          <p className="pf-note pf-note-warn">Diese Nachricht ist beschädigt oder wurde verändert und kann nicht angezeigt werden.</p>
        ) : m.body ? (
          <MessageText text={m.body} />
        ) : null}
        {m.attachments.length > 0 && <MessageAttachments files={m.attachments} />}
        <div className="pf-meta">
          <time dateTime={m.created_at} title={fullTime(m.created_at)} aria-hidden="true">
            {clock(m.created_at)}
          </time>
          {m.email && !m.own && <span className="badge">E-Mail</span>}
          {m.delivery?.status === 'sent' && (
            <span className="xsmall muted" title={(m.delivery.to ?? []).join(', ')}>
              per E-Mail{m.delivery.account ? ` über ${m.delivery.account}` : ''} gesendet
            </span>
          )}
          {m.delivery?.status === 'failed' && <span className="badge badge-danger" title={m.delivery.error}>E-Mail nicht gesendet: {m.delivery.error}</span>}
          {m.delivery?.status === 'no_account' && <span className="badge badge-warning">nur im Postfach – Externe haben die Nachricht nicht erhalten</span>}
          {m.reported && <span className="badge badge-warning">gemeldet</span>}
          {m.can_report && !m.reported && (
            <button type="button" className="pf-link-btn" onClick={() => onReport(m)} aria-label={`Nachricht von ${m.sender.name} melden`}>
              <Glyph name="flag" size={13} /> Melden
            </button>
          )}
        </div>
      </div>
    </li>
  );
}

function ActionButton({ icon, label, onClick, danger }: { icon: GlyphName; label: string; onClick: () => Promise<unknown> | void; danger?: boolean }) {
  return (
    <AsyncButton className={`btn pf-act pf-sheet-act${danger ? ' pf-act-danger' : ''}`} onClick={onClick} title={label}>
      <Glyph name={icon} size={16} />
      <span>{label}</span>
    </AsyncButton>
  );
}

// ------------------------------------------------------------------ Antwortfeld

function ReplyBox({ conv, settings, onSent }: { conv: ConversationDetailInfo; settings?: MessageSettings; onSent: (res: ReplyResponse) => void }) {
  const limits = settings?.limits ?? DEFAULT_LIMITS;
  const [text, setText] = useState('');
  const [uploaded, setUploaded] = useState<StoredFileInfo[]>([]);
  const [restored, setRestored] = useState<StoredFileInfo[]>([]);
  const [draftId, setDraftId] = useState<number | null>(null);
  const [draftState, setDraftState] = useState<'' | 'saving' | 'saved' | 'error'>('');
  const [uploadKey, setUploadKey] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const textId = useId();
  const hintId = useId();
  const textRef = useRef<HTMLTextAreaElement>(null);
  const pickRef = useRef<(() => void) | null>(null);
  const lastSaved = useRef('');
  const generation = useRef(0);
  const draftRef = useRef<number | null>(null);
  draftRef.current = draftId;

  const attachments = useMemo(() => [...restored, ...uploaded], [restored, uploaded]);
  const attKey = attachments.map((f) => f.id).join(',');
  const contentKey = `${text}\u0000${attKey}`;

  // vorhandenen Antwort-Entwurf dieser Unterhaltung laden
  useEffect(() => {
    let alive = true;
    messagesApi
      .drafts()
      .then(async (list) => {
        const found = list.find((d) => d.conversation_id === conv.id);
        if (!found || !alive) return;
        const d = await messagesApi.draft(found.id);
        if (!alive) return;
        lastSaved.current = `${d.body}\u0000${d.attachments.map((f) => f.id).join(',')}`;
        setDraftId(d.id);
        setText(d.body);
        setRestored(d.attachments);
        setDraftState('saved');
      })
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, [conv.id]);

  // Entwurf automatisch speichern (verschlüsselt auf dem Server), leer → Entwurf löschen
  useEffect(() => {
    if (contentKey === lastSaved.current) return undefined;
    const gen = generation.current;
    const timer = window.setTimeout(async () => {
      const id = draftRef.current;
      const empty = !text.trim() && !attachments.length;
      try {
        if (empty) {
          if (id) await messagesApi.deleteDraft(id);
          if (generation.current !== gen) return;
          lastSaved.current = contentKey;
          setDraftId(null);
          setDraftState('');
          return;
        }
        setDraftState('saving');
        const input = { conversation_id: conv.id, body: text, attachment_ids: attachments.map((f) => f.id) };
        const d = id ? await messagesApi.updateDraft(id, input) : await messagesApi.createDraft(input);
        if (generation.current !== gen) {
          // inzwischen gesendet: verspäteten Entwurf wieder entfernen
          if (!id) messagesApi.deleteDraft(d.id).catch(() => undefined);
          return;
        }
        lastSaved.current = contentKey;
        setDraftId(d.id);
        setDraftState('saved');
      } catch {
        if (generation.current === gen) setDraftState('error');
      }
    }, 1500);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contentKey]);

  const send = async () => {
    if (!text.trim() && !attachments.length) {
      setError('Bitte einen Text eingeben oder eine Datei anhängen.');
      return;
    }
    setError(null);
    generation.current += 1;
    try {
      const res = await messagesApi.reply(conv.id, { body: text, attachment_ids: attachments.map((f) => f.id), draft_id: draftId });
      setText('');
      setUploaded([]);
      setRestored([]);
      setDraftId(null);
      setDraftState('');
      setUploadKey((k) => k + 1);
      lastSaved.current = '\u0000';
      onSent(res);
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  if (!conv.reply.can_reply) {
    return (
      <div className="pf-reply pf-reply-off" role="note">
        <Glyph name="lock" size={16} /> <span>{conv.reply.reason ?? 'Antworten ist hier nicht möglich.'}</span>
      </div>
    );
  }
  const canSend = !!text.trim() || attachments.length > 0;
  const status = draftState === 'saving' ? 'Entwurf wird gespeichert …' : draftState === 'saved' ? 'Entwurf gespeichert' : draftState === 'error' ? 'Entwurf konnte nicht gespeichert werden' : '';
  return (
    <div className="pf-reply">
      {conv.reply.hint && (
        <p className="pf-reply-hint small">
          <Glyph name="lock" size={14} /> {conv.reply.hint}
        </p>
      )}
      {restored.length > 0 && (
        <FileList
          files={restored}
          compact
          label="Anhänge aus dem Entwurf"
          confirmDelete={false}
          deleteLabel="Entfernen"
          canDelete={() => true}
          onDelete={(f) => setRestored((list) => list.filter((x) => x.id !== f.id))}
        />
      )}
      <FileUpload
        key={uploadKey}
        purpose={ATTACHMENT_PURPOSE}
        compact
        hidePicker
        pickRef={pickRef}
        maxFiles={Math.max(1, limits.attachments - restored.length)}
        deleteOnRemove={false}
        onChange={setUploaded}
      />
      <Composer
        id={textId}
        value={text}
        onChange={setText}
        onSend={send}
        canSend={canSend}
        maxLength={limits.body}
        label={conv.reply.mode === 'private' ? 'Private Antwort' : 'Antwort'}
        placeholder={conv.reply.mode === 'private' ? 'Private Antwort schreiben …' : 'Antwort schreiben …'}
        attachLabel="Datei anhängen"
        onAttach={() => pickRef.current?.()}
        describedBy={hintId}
        textRef={textRef}
      />
      <span id={hintId} className="pf-reply-status xsmall muted" aria-live="polite">
        {status}
      </span>
      {error && (
        <p className="pf-error-text" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

// ------------------------------------------------------------------ Unterhaltung

export function ConversationView({ id, filter, settings, showBack }: { id: number; filter: InboxFilter; settings?: MessageSettings; showBack: boolean }) {
  const navigate = useNavigate();
  const toast = useToast();
  const titleId = useId();
  const q = useApi<ConversationDetail>((signal) => messagesApi.get(id, null, signal), [id], { live: ['messages'] });
  const data = q.data && q.data.conversation.id === id ? q.data : undefined;
  const [older, setOlder] = useState<{ id: number; messages: Message[]; hasMore: boolean } | null>(null);
  const [reporting, setReporting] = useState<Message | null>(null);
  const [sheet, setSheet] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const near = useRef(true);
  const seen = useRef<{ id: number; lastId: number } | null>(null);
  const keepFromBottom = useRef<number | null>(null);

  const olderMsgs = older && older.id === id ? older.messages : null;
  const messages = useMemo(() => (data ? mergeMessages(olderMsgs ?? [], data.messages) : []), [data, olderMsgs]);
  const hasMore = older && older.id === id ? older.hasMore : !!data?.has_more;
  const conv = data?.conversation;
  // Verlauf wurde in einen Chat übernommen → dort weiter
  useEffect(() => {
    if (conv?.chat_id) navigate(chatPath(conv.chat_id, filter), { replace: true });
  }, [conv?.chat_id, filter, navigate]);
  const lastId = messages[messages.length - 1]?.id ?? 0;
  const firstUnread = messages.find((m) => m.unread)?.id ?? null;

  // als gelesen markieren, sobald sichtbar
  const unread = conv?.unread ?? 0;
  const newestLoaded = data?.messages[data.messages.length - 1]?.id ?? 0;
  useEffect(() => {
    if (!unread || !newestLoaded) return undefined;
    const markRead = () => {
      if (document.visibilityState === 'visible') messagesApi.read(id, newestLoaded).catch(() => undefined);
    };
    markRead();
    document.addEventListener('visibilitychange', markRead);
    return () => document.removeEventListener('visibilitychange', markRead);
  }, [id, unread, newestLoaded]);

  // Bildlauf: beim Öffnen zur ersten neuen Nachricht bzw. ans Ende, neue Nachrichten nur, wenn man unten ist
  useLayoutEffect(() => {
    const el = scrollRef.current;
    if (!el || !data) return;
    if (keepFromBottom.current !== null) {
      el.scrollTop = el.scrollHeight - keepFromBottom.current;
      keepFromBottom.current = null;
    } else if (!seen.current || seen.current.id !== id) {
      const target = firstUnread ? document.getElementById(`pf-m-${firstUnread}`) : null;
      el.scrollTop = target ? Math.max(0, target.offsetTop - 48) : el.scrollHeight;
    } else if (lastId > seen.current.lastId && near.current) {
      el.scrollTop = el.scrollHeight;
    }
    seen.current = { id, lastId };
  }, [id, data, lastId, firstUnread, messages.length]);

  const loadOlder = async () => {
    const first = messages[0]?.id;
    if (!first) return;
    try {
      const res = await messagesApi.get(id, first);
      const el = scrollRef.current;
      if (el) keepFromBottom.current = el.scrollHeight - el.scrollTop;
      setOlder({ id, messages: mergeMessages(res.messages, olderMsgs ?? []), hasMore: res.has_more });
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  const run = async (fn: () => Promise<unknown>, success?: string, after?: () => void) => {
    try {
      await fn();
      if (success) toast.success(success);
      if (after) after();
      else q.reload();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  if (q.error && !data) return <ErrorBox error={q.error} onRetry={q.reload} title="Unterhaltung konnte nicht geladen werden" />;
  if (!data || !conv) return <Loading />;

  const other = conv.kind === 'direct' ? conv.participants.find((p) => !p.me) : undefined;
  const showSender = conv.kind !== 'direct';
  const subline =
    conv.kind === 'broadcast'
      ? conv.is_creator
        ? `Rundschreiben an ${audienceText(conv)}`
        : `Von ${conv.creator.name} an ${audienceText(conv)}`
      : conv.kind === 'group'
        ? `Mit ${participantsText([...conv.participants, ...(conv.external ?? [])], 4)}`
        : conv.kind === 'email'
          ? `E-Mail mit ${participantsText(conv.external ?? [], 4)}`
          : '';
  const onSent = (res: ReplyResponse) => {
    if (res.private && res.conversation_id !== id) {
      toast.success('Ihre Antwort wurde privat an die absendende Person geschickt.');
      navigate(conversationPath(res.conversation_id, filter));
    } else {
      near.current = true;
      q.reload();
    }
  };

  return (
    <article className="card pf-thread" aria-labelledby={titleId}>
      <header className="pf-thread-head">
        {showBack && (
          <Link to={folderPath(filter)} className="btn btn-ghost btn-sm pf-back" aria-label="Zurück zur Liste">
            <Glyph name="back" size={18} />
          </Link>
        )}
        <div className="pf-thread-title">
          <h2 id={titleId}>{threadTitle(conv)}</h2>
          <p className="pf-thread-sub">
            <KindTag kind={conv.kind} label={conv.kind_label} />
            {other && <PersonLine person={other} />}
            {subline && <span>{subline}</span>}
            {conv.muted && (
              <span className="badge">
                <Glyph name="bellOff" size={12} /> stumm
              </span>
            )}
            {conv.archived && <span className="badge">archiviert</span>}
            {conv.blocked && <span className="badge badge-danger">blockiert</span>}
          </p>
          {!conv.integrity_ok && <p className="pf-note pf-note-warn">Der Betreff ist beschädigt und kann nicht angezeigt werden.</p>}
        </div>
        <button type="button" className="btn btn-ghost btn-icon pf-gear" aria-label="Einstellungen dieser Unterhaltung" title="Einstellungen" onClick={() => setSheet(true)}>
          <Glyph name="cog" size={20} />
        </button>
      </header>

      <div
        className="pf-scroll"
        ref={scrollRef}
        role="log"
        aria-label="Nachrichtenverlauf"
        tabIndex={0}
        onScroll={(e) => {
          const el = e.currentTarget;
          near.current = nearBottom(el.scrollTop, el.clientHeight, el.scrollHeight);
        }}
      >
        {hasMore && (
          <div className="pf-older">
            <AsyncButton className="btn btn-sm" onClick={loadOlder}>
              Ältere Nachrichten laden
            </AsyncButton>
          </div>
        )}
        {groupByDay(messages).map((g) => (
          <section key={g.key} className="pf-day-group" aria-label={g.label}>
            <h3 className="pf-day">
              <span>{g.label}</span>
            </h3>
            <ol className="pf-msgs">
              {g.items.map((m) => (
                <Fragment key={m.id}>
                  {m.id === firstUnread && (
                    <li className="pf-new-divider" aria-hidden="true">
                      <span>Neu</span>
                    </li>
                  )}
                  <MessageItem m={m} showSender={showSender} onReport={setReporting} />
                </Fragment>
              ))}
            </ol>
          </section>
        ))}
        {!messages.length && <p className="muted small pf-empty-thread">Keine Nachrichten (ältere wurden für Sie gelöscht oder sind abgelaufen).</p>}
      </div>

      <ReplyBox key={id} conv={conv} settings={settings} onSent={onSent} />
      {sheet && (
        <Modal title="Einstellungen" onClose={() => setSheet(false)} variant="drawer">
          <div className="stack pf-sheet">
            <ActionButton
              icon={conv.archived ? 'unarchive' : 'archive'}
              label={conv.archived ? 'Zurück aus dem Archiv holen' : 'Archivieren'}
              onClick={() => run(() => messagesApi.patch(id, { archived: !conv.archived }), conv.archived ? 'Zurück aus dem Archiv' : 'Archiviert')}
            />
            <ActionButton
              icon={conv.muted ? 'bell' : 'bellOff'}
              label={conv.muted ? 'Stummschaltung aufheben' : 'Stummschalten'}
              onClick={() => run(() => messagesApi.patch(id, { muted: !conv.muted }), conv.muted ? 'Hinweise wieder an' : 'Stummgeschaltet – keine Hinweise mehr')}
            />
            <ActionButton
              icon="unread"
              label="Als ungelesen markieren"
              onClick={() =>
                run(
                  () => messagesApi.markUnread(id),
                  'Als ungelesen markiert',
                  () => {
                    setSheet(false);
                    navigate(folderPath(filter));
                  },
                )
              }
            />
            {conv.can_block && other && other.id !== null && (
              <ActionButton
                icon="ban"
                label={conv.blocked ? 'Blockierung aufheben' : 'Blockieren'}
                danger={!conv.blocked}
                onClick={async () => {
                  if (conv.blocked) return run(() => messagesApi.unblock(Number(other.id)), `${other.name} ist nicht mehr blockiert`);
                  if (!(await confirmAsk({ title: 'Blockieren', message: `${other.name} blockieren? Die Person kann Ihnen dann keine Nachrichten mehr schicken; ihre Beiträge in Gruppen werden für Sie ausgeblendet.`, confirmLabel: 'Blockieren', danger: true }))) return undefined;
                  return run(() => messagesApi.block(Number(other.id)), `${other.name} ist blockiert`);
                }}
              />
            )}
            <ActionButton
              icon="trash"
              label="Für mich löschen"
              danger
              onClick={async () => {
                if (!(await confirmAsk({ title: 'Unterhaltung löschen', message: 'Unterhaltung für Sie löschen? Die anderen Teilnehmenden behalten sie; eine neue Nachricht holt sie zurück.', confirmLabel: 'Löschen', danger: true }))) return undefined;
                return run(
                  () => messagesApi.remove(id),
                  'Unterhaltung gelöscht',
                  () => {
                    setSheet(false);
                    navigate(folderPath(filter));
                  },
                );
              }}
            />
            {conv.kind === 'broadcast' && conv.is_creator && (
              <section className="stack-sm">
                <h3 className="pf-sheet-h">
                  {plural(conv.recipient_count, 'Empfänger/in', 'Empfänger/innen')}
                  {typeof conv.read_count === 'number' ? ` · ${conv.read_count} gelesen` : ''}
                </h3>
                <ul className="pf-people">
                  {(conv.recipients ?? []).map((p) => (
                    <li key={p.id ?? p.name}>
                      <PersonLine person={p} />
                    </li>
                  ))}
                </ul>
                {(conv.recipients_more ?? 0) > 0 && <p className="xsmall muted">… und {conv.recipients_more} weitere</p>}
              </section>
            )}
            {(conv.kind === 'group' || conv.kind === 'email' || (conv.external?.length ?? 0) > 0) && (
              <section className="stack-sm">
                <h3 className="pf-sheet-h">{plural(conv.participants.length + (conv.external?.length ?? 0), 'Teilnehmende/r', 'Teilnehmende')}</h3>
                <ul className="pf-people">
                  {conv.participants.map((p) => (
                    <li key={p.id ?? p.name}>
                      <PersonLine
                        person={p}
                        extra={
                          <>
                            {p.me && <span className="badge">Sie</span>}
                            {p.recipient_role === 'cc' && <span className="badge">CC</span>}
                            {p.recipient_role === 'bcc' && <span className="badge badge-warning">BCC</span>}
                          </>
                        }
                      />
                    </li>
                  ))}
                  {(conv.external ?? []).map((p) => (
                    <li key={`ext-${p.email}`}>
                      <PersonLine
                        person={p}
                        extra={
                          <>
                            <span className="badge">E-Mail</span>
                            {p.recipient_role === 'cc' && <span className="badge">CC</span>}
                            {p.recipient_role === 'bcc' && <span className="badge badge-warning">BCC</span>}
                          </>
                        }
                      />
                    </li>
                  ))}
                </ul>
                {conv.my_role === 'bcc' && <p className="xsmall muted">Sie haben diese Nachricht als Blindkopie (BCC) erhalten.</p>}
              </section>
            )}
          </div>
        </Modal>
      )}
      {reporting && (
        <ReportDialog
          conversationId={id}
          message={reporting}
          categories={settings?.report_categories}
          onClose={() => setReporting(null)}
          onDone={() => {
            setReporting(null);
            q.reload();
          }}
        />
      )}
    </article>
  );
}

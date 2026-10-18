/**
 * `/nachrichten/neu` – Nachricht verfassen: An / CC / BCC (Personen, E-Mail-Adressen; mit `messages.broadcast` auch
 * Gruppen), bei Adressen außerhalb der Schule das E-Mail-Konto („Von“), Betreff, Text, Anhänge, bei Rundschreiben die
 * Antwortregel; Entwürfe (verschlüsselt auf dem Server).
 *
 * Vorbelegung per Adresse: `?an=<Konto-ID>`, `?lehrkraft=<Kürzel>`, `?eltern=<Schüler-ID>`, `?schueler=<Schüler-ID>`,
 * `?betreff=…`, `?entwurf=<ID>`.
 */
import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import type { StoredFileInfo } from '../../api/files';
import { EmojiButton, useEmojiInsert } from '../../components/EmojiPicker';
import { FileList } from '../../components/FileList';
import { FileUpload } from '../../components/FileUpload';
import { useLeaveGuard } from '../../components/UnsavedChanges';
import { Alert, AsyncButton, ErrorBox, Loading, SegmentedControl } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useTitle } from '../../hooks/misc';
import { useApi } from '../../hooks/useApi';
import { ATTACHMENT_PURPOSE, mailApi, messagesApi } from './api';
import { Glyph } from './components';
import {
  composeProblems,
  conversationPath,
  DEFAULT_LIMITS,
  folderPath,
  kindDescription,
  predictKind,
  REPLY_MODE_OPTIONS,
  suspendedText,
  toInput,
} from './logic';
import { RecipientPicker } from './RecipientPicker';
import type { Draft, MailAccount, MessageSettings, Person, Recipient, RecipientInput, RecipientRole, ReplyMode } from './types';
import './messages.css';
import { confirmAsk } from '../../lib/confirm';

type ByRole = Record<RecipientRole, Recipient[]>;
const NO_RECIPIENTS: ByRole = { to: [], cc: [], bcc: [] };

/** Empfänger eines Entwurfs wieder als Auswahl, getrennt nach An/CC/BCC (Beschriftungen aus dem Entwurf). */
function draftRecipients(d: Draft): ByRole {
  const out: ByRole = { to: [], cc: [], bcc: [] };
  d.recipients.forEach((r: RecipientInput, i) => {
    const label = d.recipient_labels[i] ?? '';
    let item: Recipient;
    if (r.type === 'user') item = { type: 'user', id: r.id, name: label || 'Unbekannt', role: null, role_label: '', info: '' };
    else if (r.type === 'email') item = { type: 'email', email: r.email, name: r.name || undefined };
    else item = { type: 'group', kind: r.kind, ref: r.ref, key: `${r.kind}:${r.ref}`, label: label || r.ref, category: '', category_label: 'Gruppe' };
    out[r.role ?? 'to'].push(item);
  });
  return out;
}

async function prefill(params: URLSearchParams): Promise<Person[]> {
  const an = Number(params.get('an'));
  const teacher = params.get('lehrkraft');
  const parentsOf = params.get('eltern');
  const student = params.get('schueler');
  let q: Parameters<typeof messagesApi.lookup>[0] | null = null;
  if (an > 0) q = { user_id: an };
  else if (teacher) q = { teacher_id: teacher };
  else if (parentsOf) q = { parents_of: parentsOf };
  else if (student) q = { student_id: student };
  if (!q) return [];
  return (await messagesApi.lookup(q)).people;
}

export default function ComposePage() {
  useTitle('Neuer Brief');
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const toast = useToast();
  const ids = { to: useId(), cc: useId(), bcc: useId(), from: useId(), toHint: useId(), subject: useId(), body: useId(), problems: useId() };
  const accountsQ = useApi((signal) => mailApi.accounts(signal), []);
  const accounts: MailAccount[] = accountsQ.data?.accounts ?? [];
  const [fromAccount, setFromAccount] = useState<number | null>(null);
  const settingsQ = useApi<MessageSettings>((signal) => messagesApi.settings(signal), []);
  const settings = settingsQ.data;
  const canBroadcast = !!settings?.can_broadcast;
  const limits = settings?.limits ?? DEFAULT_LIMITS;

  const [byRole, setByRole] = useState<ByRole>(NO_RECIPIENTS);
  const [showCopies, setShowCopies] = useState(false);
  const recipients = useMemo(() => [...byRole.to, ...byRole.cc, ...byRole.bcc], [byRole]);
  const setRole = (role: RecipientRole) => (list: Recipient[]) => setByRole((b) => ({ ...b, [role]: list }));
  const [subject, setSubject] = useState(params.get('betreff') ?? '');
  const [body, setBody] = useState('');
  const bodyRef = useRef<HTMLTextAreaElement>(null);
  const [allowReplies, setAllowReplies] = useState<ReplyMode>('all');
  const [uploaded, setUploaded] = useState<StoredFileInfo[]>([]);
  const [restored, setRestored] = useState<StoredFileInfo[]>([]);
  const [draftId, setDraftId] = useState<number | null>(null);
  const [tried, setTried] = useState(false);
  const [prefillError, setPrefillError] = useState<string | null>(null);
  const [loadingDraft, setLoadingDraft] = useState(false);

  // Vorbelegung (Empfänger aus Verknüpfungen bzw. Entwurf)
  const draftParam = Number(params.get('entwurf'));
  const prefillKey = params.toString();
  useEffect(() => {
    let alive = true;
    if (draftParam > 0) {
      setLoadingDraft(true);
      messagesApi
        .draft(draftParam)
        .then((d) => {
          if (!alive) return;
          if (d.conversation_id) {
            navigate(conversationPath(d.conversation_id), { replace: true });
            return;
          }
          setDraftId(d.id);
          const restoredRecipients = draftRecipients(d);
          setByRole(restoredRecipients);
          if (restoredRecipients.cc.length || restoredRecipients.bcc.length) setShowCopies(true);
          setSubject(d.subject);
          setBody(d.body);
          setAllowReplies(d.allow_replies);
          setRestored(d.attachments);
          if (!d.integrity_ok) setPrefillError('Der Entwurf ist beschädigt und konnte nicht vollständig gelesen werden.');
        })
        .catch((e: unknown) => alive && setPrefillError(errorMessage(e)))
        .finally(() => alive && setLoadingDraft(false));
    } else {
      prefill(params)
        .then((people) => alive && people.length && setByRole((b) => (b.to.length ? b : { ...b, to: people })))
        .catch((e: unknown) => alive && setPrefillError(`Die vorgeschlagene Person kann nicht angeschrieben werden: ${errorMessage(e)}`));
    }
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefillKey]);

  const insertEmoji = useEmojiInsert(bodyRef, body, setBody, limits.body);
  const attachments = useMemo(() => [...restored, ...uploaded], [restored, uploaded]);
  const predicted = predictKind(recipients, canBroadcast, allowReplies);
  const kind = predicted === 'direct' && byRole.bcc.length ? 'group' : predicted;
  const emailRecipients = recipients.filter((r) => r.type === 'email');
  const problems = composeProblems({ recipients, subject, body, attachments: attachments.length, kind, limits });
  const dirty = recipients.length > 0 || !!subject.trim() || !!body.trim() || attachments.length > 0;

  const input = () => ({
    recipients: [...byRole.to.map((r) => toInput(r, 'to')), ...byRole.cc.map((r) => toInput(r, 'cc')), ...byRole.bcc.map((r) => toInput(r, 'bcc'))],
    subject,
    body,
    allow_replies: kind === 'broadcast' ? allowReplies : ('all' as ReplyMode),
    attachment_ids: attachments.map((f) => f.id),
  });

  const send = async () => {
    setTried(true);
    if (problems.length) {
      document.getElementById(ids.problems)?.focus();
      return;
    }
    try {
      const res = await messagesApi.create({ ...input(), draft_id: draftId, mail_account_id: fromAccount ?? undefined });
      const c = res.conversation;
      const delivery = (res as { messages?: { delivery?: { status: string; error?: string } | null }[] }).messages?.[0]?.delivery;
      if (delivery?.status === 'failed') toast.error(`Im Postfach gespeichert, aber der E-Mail-Versand ist fehlgeschlagen: ${delivery.error ?? ''}`);
      else toast.success(c.kind === 'broadcast' ? `Rundschreiben an ${c.recipient_count === 1 ? '1 Person' : `${c.recipient_count} Personen`} gesendet` : 'Nachricht gesendet');
      navigate(conversationPath(c.id));
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  const saveDraft = async () => {
    try {
      const d = draftId ? await messagesApi.updateDraft(draftId, input()) : await messagesApi.createDraft(input());
      setDraftId(d.id);
      toast.success('Entwurf gespeichert');
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  const discard = async () => {
    if (draftId) {
      if (!(await confirmAsk({ title: 'Entwurf löschen', message: 'Entwurf löschen?', confirmLabel: 'Löschen', danger: true }))) return;
      try {
        await messagesApi.deleteDraft(draftId);
      } catch (e) {
        toast.error(errorMessage(e));
        return;
      }
    } else if (dirty && !(await confirmAsk({ title: 'Nachricht verwerfen', message: 'Nachricht verwerfen?', confirmLabel: 'Verwerfen', danger: true }))) {
      return;
    }
    navigate(draftId ? folderPath('entwuerfe') : folderPath('alle'));
  };

  // Beim Wechsel auf eine andere Seite den Entwurf automatisch merken (kein Popup)
  useLeaveGuard(dirty, async () => {
    try {
      const d = draftId ? await messagesApi.updateDraft(draftId, input()) : await messagesApi.createDraft(input());
      setDraftId(d.id);
      toast.success('Entwurf gespeichert');
    } catch (e) {
      toast.error(errorMessage(e));
      return false;
    }
    return true;
  });

  const suspended = suspendedText(settings?.suspended_until);

  return (
    <div className="page page-narrow stack pf-compose-page">
      <div className="page-head">
        <div>
          <h1>{params.get('art') === 'email' ? 'Neue E-Mail' : 'Neuer Brief'}</h1>
          <p className="muted small" style={{ margin: 0 }}>
            <Glyph name="lock" size={14} /> Betreff, Text und Anhänge werden verschlüsselt gespeichert.
          </p>
        </div>
        <Link to={folderPath('alle')} className="btn btn-ghost">
          <Glyph name="back" /> Zu den Nachrichten
        </Link>
      </div>
      {settingsQ.error ? <ErrorBox error={settingsQ.error} onRetry={settingsQ.reload} /> : null}
      {suspended && <Alert kind="warning" title="Senden gesperrt">{suspended}</Alert>}
      {prefillError && <Alert kind="warning">{prefillError}</Alert>}
      {(loadingDraft || (settingsQ.initialLoading && !settings)) && <Loading />}
      <form
        className="card stack pf-compose"
        onSubmit={(e) => e.preventDefault()}
        aria-describedby={tried && problems.length ? ids.problems : undefined}
      >
        <div className="field">
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <label htmlFor={ids.to}>An</label>
            {!showCopies && (
              <button type="button" className="pf-link-btn" onClick={() => setShowCopies(true)}>
                CC / BCC hinzufügen
              </button>
            )}
          </div>
          <RecipientPicker
            value={byRole.to}
            onChange={setRole('to')}
            inputId={ids.to}
            describedBy={ids.toHint}
            invalid={tried && !recipients.length}
            disabled={!!suspended}
          />
          <span id={ids.toHint} className="hint">
            {kind
              ? kindDescription(kind, recipients)
              : canBroadcast
                ? 'Name, Gruppe (Klasse, Eltern einer Klasse, Kurs, Kollegium …) oder E-Mail-Adresse eingeben.'
                : 'Name oder E-Mail-Adresse eingeben – Sie können jeder Person mit Postfach schreiben.'}
          </span>
        </div>
        {showCopies && (
          <>
            <div className="field">
              <label htmlFor={ids.cc}>CC (Kopie – für alle sichtbar)</label>
              <RecipientPicker value={byRole.cc} onChange={setRole('cc')} inputId={ids.cc} disabled={!!suspended} placeholder="Name, Gruppe oder E-Mail-Adresse" />
            </div>
            <div className="field">
              <label htmlFor={ids.bcc}>BCC (Blindkopie – die anderen sehen nicht, dass diese Personen die Nachricht bekommen)</label>
              <RecipientPicker value={byRole.bcc} onChange={setRole('bcc')} inputId={ids.bcc} disabled={!!suspended} placeholder="Name, Gruppe oder E-Mail-Adresse" />
            </div>
          </>
        )}
        {emailRecipients.length > 0 && accounts.length > 0 && (
          <div className="field">
            <label htmlFor={ids.from}>Von (für E-Mail-Adressen außerhalb der Schule)</label>
            <select id={ids.from} value={fromAccount ?? accounts.find((a) => a.is_default)?.id ?? accounts[0].id} onChange={(e) => setFromAccount(Number(e.target.value))}>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.display_name ? `${a.display_name} <${a.email}>` : a.email}
                </option>
              ))}
            </select>
          </div>
        )}
        {emailRecipients.length > 0 && accountsQ.data && accounts.length === 0 && (
          <Alert kind="info" title="E-Mail-Konto verbinden">
            Für Adressen außerhalb der Schule verbinden Sie zuerst Ihr E-Mail-Konto unter <Link to="/nachrichten/einstellungen">Nachrichten → Einstellungen</Link>.
          </Alert>
        )}
        {kind === 'broadcast' && (
          <div className="field">
            <span className="field-label">Antworten</span>
            <SegmentedControl<ReplyMode>
              label="Wer darf antworten?"
              value={allowReplies}
              onChange={setAllowReplies}
              options={REPLY_MODE_OPTIONS.map((o) => ({ value: o.value, label: o.label, title: o.hint }))}
            />
            <span className="hint">{REPLY_MODE_OPTIONS.find((o) => o.value === allowReplies)?.hint}</span>
          </div>
        )}
        <div className="field">
          <label htmlFor={ids.subject}>
            Betreff{kind === 'email' ? ' (optional)' : ''}
          </label>
          <input
            id={ids.subject}
            value={subject}
            maxLength={limits.subject}
            aria-invalid={(tried && !!kind && kind !== 'email' && !subject.trim()) || undefined}
            onChange={(e) => setSubject(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor={ids.body}>Nachricht</label>
          <textarea
            ref={bodyRef}
            id={ids.body}
            rows={9}
            value={body}
            maxLength={limits.body}
            onChange={(e) => setBody(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                void send();
              }
            }}
          />
          <span className="hint" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <EmojiButton onPick={insertEmoji} className="btn btn-sm btn-icon" />
            {body.length > limits.body * 0.9 ? `${body.length} von ${limits.body} Zeichen · ` : ''}Strg + Enter sendet.
          </span>
        </div>
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
          purpose={ATTACHMENT_PURPOSE}
          label="Anhänge"
          maxFiles={Math.max(1, limits.attachments - restored.length)}
          deleteOnRemove={false}
          disabled={!!suspended}
          hint="Dateien werden verschlüsselt abgelegt; nur die Empfangenden können sie öffnen."
          onChange={setUploaded}
        />
        {tried && problems.length > 0 && (
          <div id={ids.problems} tabIndex={-1} role="alert" className="alert alert-error">
            <ul className="pf-problems">
              {problems.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          </div>
        )}
        <div className="pf-compose-actions">
          <button type="button" className="btn btn-ghost" onClick={() => void discard()}>
            {draftId ? 'Entwurf löschen' : 'Verwerfen'}
          </button>
          <AsyncButton className="btn" onClick={saveDraft} disabled={!dirty}>
            Als Entwurf speichern
          </AsyncButton>
          <AsyncButton className="btn btn-primary" onClick={send} disabled={!!suspended}>
            <Glyph name="send" /> Senden
          </AsyncButton>
        </div>
      </form>
    </div>
  );
}

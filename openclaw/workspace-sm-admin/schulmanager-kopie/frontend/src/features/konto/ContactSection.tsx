/**
 * Profil: Abschnitt „Kontakt & Wiederherstellung“ (§11.2). E-Mail/Handy anzeigen, ändern (Code an die neue
 * Adresse/Nummer, aktuelles Passwort nötig), entfernen; Bestätigungslink `/profil?kontakt=<token>` aus der E-Mail.
 */
import { useEffect, useId, useRef, useState, type FormEvent } from 'react';
import { useSearchParams } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Alert, ErrorBox, Loading } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { formatDateTime } from '../../lib/dates';
import { contactApi } from './api';
import { CodeInput, DevOutboxHint } from './components';
import { channelList, cleanCode, formatPhone, isCompleteCode, isValidEmail, normalizePhone } from './logic';
import type { ContactKind, MyContact } from './types';
import './konto.css';
import { PasswordInput } from '../../components/PasswordInput';

const LABELS: Record<ContactKind, string> = { email: 'E-Mail-Adresse', phone: 'Handynummer' };

/** Bestätigungslink nur einmal einlösen (StrictMode ruft Effekte doppelt auf). */
const confirmedLinks = new Set<string>();

function VerifiedBadge({ ok }: { ok: boolean }) {
  return ok ? (
    <span className="badge badge-success">
      <Icon name="check" /> bestätigt
    </span>
  ) : (
    <span className="badge badge-warning">nicht bestätigt</span>
  );
}

/** Hinweis, über welche Wege „Passwort vergessen“ für dieses Konto möglich ist (nur zustellbare Wege). */
function PolicyHint({ c }: { c: MyContact }) {
  if (!c.password_login) {
    return <p className="small muted">Für Ihr Konto ist „Passwort vergessen“ nicht nötig.</p>;
  }
  const ways = c.reset_channels.filter((ch) => c.channels[ch]);
  if (ways.length === 0) return null;
  const usable = ways.filter((ch) => (ch === 'email' ? c.email_verified : c.phone_verified));
  return (
    <p className="small muted">
      „Passwort vergessen“ ist für Ihr Konto per {channelList(ways)} möglich
      {usable.length ? ` – eingerichtet: ${channelList(usable)}.` : ' – bitte bestätigen Sie dazu eine Adresse oder Nummer.'}
    </p>
  );
}

function Editor({ kind, contact, onDone, onCancel }: { kind: ContactKind; contact: MyContact; onDone: (c: MyContact) => void; onCancel: () => void }) {
  const id = useId();
  const user = useUser();
  const toast = useToast();
  const pending = contact.pending[kind];
  const [phase, setPhase] = useState<'enter' | 'code'>(pending ? 'code' : 'enter');
  const [value, setValue] = useState(kind === 'email' && !contact.email_verified ? contact.email ?? '' : '');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [sentTo, setSentTo] = useState<string | null>(pending?.target ?? null);
  const [expires, setExpires] = useState<string | null>(pending?.expires_at ?? null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const normalized = kind === 'phone' ? normalizePhone(value) : null;
  const valid = kind === 'email' ? isValidEmail(value) : normalized !== null;
  const channelOk = kind === 'email' ? contact.channels.email : contact.channels.sms;

  const send = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = kind === 'email' ? await contactApi.startEmail(value.trim(), password) : await contactApi.startPhone(value.trim(), password);
      setSentTo(res.sent_to);
      setExpires(res.expires_at);
      setPassword('');
      setCode('');
      setPhase('code');
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const verify = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await contactApi.verify(kind, cleanCode(code));
      toast.success(kind === 'email' ? 'E-Mail-Adresse bestätigt' : 'Handynummer bestätigt');
      onDone(res);
    } catch (err) {
      setError(errorMessage(err));
      setCode('');
    } finally {
      setBusy(false);
    }
  };

  if (!channelOk) return null; // Versandweg nicht eingerichtet: die Oberfläche bietet ihn gar nicht erst an

  return (
    <div className="ko-editor stack">
      {error && <Alert kind="error">{error}</Alert>}
      {phase === 'enter' ? (
        <form className="stack" onSubmit={send} noValidate>
          {/* für Passwort-Manager: zu welchem Konto gehört das Passwort-Feld */}
          <input type="text" name="username" autoComplete="username" value={user.username} readOnly hidden />
          <div className="field">
            <label htmlFor={`${id}-value`}>{kind === 'email' ? 'Neue E-Mail-Adresse' : 'Neue Handynummer'}</label>
            {kind === 'email' ? (
              <input id={`${id}-value`} name="email" type="email" inputMode="email" autoComplete="email" autoCapitalize="none" spellCheck={false} required value={value} onChange={(e) => setValue(e.target.value)} autoFocus />
            ) : (
              <input id={`${id}-value`} name="tel" type="tel" inputMode="tel" autoComplete="tel" required value={value} onChange={(e) => setValue(e.target.value)} aria-describedby={`${id}-tel-hint`} autoFocus />
            )}
            {kind === 'phone' && (
              <span className="hint" id={`${id}-tel-hint`} aria-live="polite">
                {value.trim() === '' ? 'Mit Vorwahl, z. B. 0171 1234567 oder +49 171 1234567.' : normalized ? `Wird gespeichert als ${formatPhone(normalized)}.` : 'Bitte mit Vorwahl angeben (0… oder +…).'}
              </span>
            )}
          </div>
          {contact.has_password && (
            <div className="field">
              <label htmlFor={`${id}-pw`}>Aktuelles Passwort</label>
              <PasswordInput id={`${id}-pw`} name="current-password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
          )}
          <p className="small muted">
            Wir schicken einen Code {kind === 'email' ? 'an diese Adresse' : 'per SMS an diese Nummer'}. Erst nach der Bestätigung wird sie gespeichert.
          </p>
          <div className="row-end ko-wrap">
            <button type="button" className="btn" onClick={onCancel}>
              Abbrechen
            </button>
            <button type="submit" className="btn btn-primary" disabled={busy || !valid || (contact.has_password && !password)}>
              {busy ? 'Wird gesendet …' : 'Code senden'}
            </button>
          </div>
        </form>
      ) : (
        <form className="stack" onSubmit={verify} noValidate>
          <p className="small" aria-live="polite">
            Code gesendet an <strong className="ko-break">{sentTo}</strong>
            {expires ? ` – gültig bis ${formatDateTime(expires)}` : ''}.
          </p>
          <CodeInput id={`${id}-code`} value={code} onChange={setCode} label={kind === 'email' ? 'Code aus der E-Mail' : 'Code aus der SMS'} />
          <div className="row-end ko-wrap">
            <button type="button" className="btn btn-ghost" onClick={() => setPhase('enter')}>
              Neuen Code anfordern
            </button>
            <button type="button" className="btn" onClick={onCancel}>
              Abbrechen
            </button>
            <button type="submit" className="btn btn-primary" disabled={busy || !isCompleteCode(code)}>
              {busy ? 'Wird geprüft …' : 'Bestätigen'}
            </button>
          </div>
        </form>
      )}
      {contact.dev_outbox && <DevOutboxHint />}
    </div>
  );
}

function RemoveForm({ kind, contact, onDone, onCancel }: { kind: ContactKind; contact: MyContact; onDone: (c: MyContact) => void; onCancel: () => void }) {
  const id = useId();
  const user = useUser();
  const toast = useToast();
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await contactApi.remove(kind, password);
      toast.success(`${LABELS[kind]} entfernt`);
      onDone(res);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };
  return (
    <form className="ko-editor stack" onSubmit={submit} noValidate>
      {error && <Alert kind="error">{error}</Alert>}
      <p className="small">
        {LABELS[kind]} wirklich entfernen?
        <HelpTip>Darüber können Sie Ihr Passwort dann nicht mehr selbst zurücksetzen.</HelpTip>
      </p>
      <input type="text" name="username" autoComplete="username" value={user.username} readOnly hidden />
      {contact.has_password && (
        <div className="field">
          <label htmlFor={`${id}-pw`}>Aktuelles Passwort</label>
          <PasswordInput id={`${id}-pw`} name="current-password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} autoFocus />
        </div>
      )}
      <div className="row-end ko-wrap">
        <button type="button" className="btn" onClick={onCancel}>
          Abbrechen
        </button>
        <button type="submit" className="btn btn-danger" disabled={busy || (contact.has_password && !password)}>
          <Icon name="trash" /> Entfernen
        </button>
      </div>
    </form>
  );
}

function Row({ kind, contact, onChange }: { kind: ContactKind; contact: MyContact; onChange: (c: MyContact) => void }) {
  const hasValue = !!(kind === 'email' ? contact.email : contact.phone);
  const available = kind === 'email' ? contact.channels.email : contact.channels.sms;
  if (!available && !hasValue) return null; // Weg nicht zustellbar und nichts hinterlegt: gar nicht anzeigen
  return <RowInner kind={kind} contact={contact} onChange={onChange} />;
}

function RowInner({ kind, contact, onChange }: { kind: ContactKind; contact: MyContact; onChange: (c: MyContact) => void }) {
  const [mode, setMode] = useState<'view' | 'edit' | 'remove'>(contact.pending[kind] ? 'edit' : 'view');
  const value = kind === 'email' ? contact.email : contact.phone;
  const verified = kind === 'email' ? contact.email_verified : contact.phone_verified;
  const at = kind === 'email' ? contact.email_verified_at : contact.phone_verified_at;
  const usable = kind === 'email' ? contact.channels.email : contact.channels.sms;
  const done = (c: MyContact) => {
    onChange(c);
    setMode('view');
  };
  return (
    <div className="ko-row">
      <div className="ko-row-main">
        <span className="ko-row-label">{LABELS[kind]}</span>
        {value ? (
          <span className="ko-row-value">
            <span className={kind === 'phone' ? 'mono ko-break' : 'ko-break'}>{value}</span> {usable && <VerifiedBadge ok={verified} />}
          </span>
        ) : (
          <span className="muted">nicht hinterlegt</span>
        )}
        {verified && at && <span className="small muted">bestätigt am {formatDateTime(at)}</span>}
        {!verified && contact.pending[kind] && mode === 'view' && <span className="small">Bestätigung offen für {contact.pending[kind]?.target}</span>}
      </div>
      {mode === 'view' && usable && (
        <div className="ko-row-actions">
          {kind === 'email' && value && !verified ? (
            <button type="button" className="btn btn-sm btn-primary" onClick={() => setMode('edit')}>
              Bestätigen
            </button>
          ) : null}
          <button type="button" className="btn btn-sm" onClick={() => setMode('edit')}>
            <Icon name={value ? 'edit' : 'plus'} /> {value ? 'Ändern' : 'Hinzufügen'}
          </button>
          {value && (
            <button type="button" className="btn btn-sm btn-ghost" onClick={() => setMode('remove')} aria-label={`${LABELS[kind]} entfernen`}>
              <Icon name="trash" /> Entfernen
            </button>
          )}
        </div>
      )}
      {mode === 'edit' && <Editor kind={kind} contact={contact} onDone={done} onCancel={() => setMode('view')} />}
      {mode === 'remove' && <RemoveForm kind={kind} contact={contact} onDone={done} onCancel={() => setMode('view')} />}
    </div>
  );
}

export function ContactSection() {
  const toast = useToast();
  const [params, setParams] = useSearchParams();
  const data = useApi((signal) => contactApi.mine(signal), []);
  const { setData } = data;
  const linkToken = params.get('kontakt');
  const [linkError, setLinkError] = useState<string | null>(null);
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!linkToken || confirmedLinks.has(linkToken)) return;
    confirmedLinks.add(linkToken);
    sectionRef.current?.scrollIntoView({ block: 'start' });
    contactApi
      .confirmLink(linkToken)
      .then((c) => {
        setData(c);
        setLinkError(null);
        toast.success('E-Mail-Adresse bestätigt');
      })
      .catch((err: unknown) => setLinkError(errorMessage(err)))
      .finally(() => {
        const next = new URLSearchParams(params);
        next.delete('kontakt');
        setParams(next, { replace: true });
      });
  }, [linkToken, params, setParams, setData, toast]);

  // Konten, die „Passwort vergessen“ nicht selbst nutzen dürfen (Standard: Schüler/innen), oder ohne einen einzigen
  // zustellbaren Weg bekommen keinen Wiederherstellungsabschnitt
  const loaded = data.data;
  if (loaded && (loaded.reset_channels.length === 0 || (!loaded.channels.email && !loaded.channels.sms))) return null;

  return (
    <section className="card ko-contact" ref={sectionRef} aria-labelledby="ko-contact-title">
      <h2 id="ko-contact-title" className="with-help">
        E-Mail & Handynummer
        <HelpTip label="Hilfe zu E-Mail und Handynummer">
          Mit einer bestätigten E-Mail-Adresse oder Handynummer können Sie ein vergessenes Passwort selbst zurücksetzen („Passwort vergessen?“ auf der
          Anmeldeseite). Wir schicken einen Code zur Bestätigung; erst danach gilt die Angabe.
        </HelpTip>
      </h2>
      {linkError && (
        <Alert kind="error" title="Bestätigungslink">
          {linkError}
        </Alert>
      )}
      {data.error ? <ErrorBox error={data.error} onRetry={data.reload} /> : null}
      {data.initialLoading && <Loading />}
      {data.data && (
        <>
          <PolicyHint c={data.data} />
          <div className="ko-rows">
            <Row kind="email" contact={data.data} onChange={setData} />
            <Row kind="phone" contact={data.data} onChange={setData} />
          </div>
        </>
      )}
    </section>
  );
}

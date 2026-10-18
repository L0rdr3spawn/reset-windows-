/**
 * Verbundene E-Mail-Konten (Postfach-Einstellungen): Konto mit App-Passwort verbinden oder – wenn die Schule es
 * eingerichtet hat – mit Google/Microsoft anmelden. Über ein verbundenes Konto gehen Nachrichten an Adressen außerhalb
 * der Schule hinaus, und eingehende E-Mails erscheinen im Postfach.
 */
import { useEffect, useId, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Alert, AsyncButton, ErrorBox, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { mailApi } from './api';
import { Glyph } from './components';
import { fullTime, isEmail } from './logic';
import type { MailAccount, MailProvider } from './types';
import { promptAsk } from '../../lib/confirm';

function guessProvider(address: string, providers: MailProvider[]): string {
  const domain = address.split('@')[1]?.toLowerCase() ?? '';
  return providers.find((p) => p.domains.includes(domain))?.id ?? '';
}

function ConnectForm({ providers: allProviders, customAllowed, onDone }: { providers: MailProvider[]; customAllowed: boolean; onDone: () => void }) {
  const toast = useToast();
  const ids = { email: useId(), provider: useId(), name: useId(), pw: useId(), user: useId(), imap: useId(), imapPort: useId(), smtp: useId(), smtpPort: useId(), sec: useId() };
  const [email, setEmail] = useState('');
  const [provider, setProvider] = useState('');
  const [touchedProvider, setTouchedProvider] = useState(false);
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  // Eigene Mailserver tragen nur Konten mit dem Recht „Eigene Mailserver eintragen“ ein; bekannte Anbieter haben feste Server
  const providers = useMemo(() => allProviders.filter((x) => customAllowed || x.id !== 'custom'), [allProviders, customAllowed]);
  const [server, setServer] = useState({ username: '', imap_host: '', imap_port: 993, smtp_host: '', smtp_port: 587, smtp_security: 'starttls' as 'ssl' | 'starttls' });
  useEffect(() => {
    if (!touchedProvider && isEmail(email)) setProvider(guessProvider(email, providers) || (customAllowed ? 'custom' : ''));
  }, [email, providers, touchedProvider]);
  const p = providers.find((x) => x.id === provider);
  const custom = provider === 'custom';

  const connect = async () => {
    if (!isEmail(email)) {
      toast.warning('Bitte eine gültige E-Mail-Adresse eingeben');
      return;
    }
    try {
      await mailApi.add({
        provider: provider || 'custom',
        email,
        password,
        display_name: name,
        ...(custom ? server : {}),
      });
      toast.success(`${email} verbunden – E-Mails werden ab jetzt abgerufen`);
      setPassword('');
      setEmail('');
      onDone();
    } catch (e) {
      toast.error(errorMessage(e), 'Verbinden');
    }
  };

  const oauth = async (which: 'google' | 'microsoft') => {
    try {
      const r = await mailApi.oauthStart(which, email);
      window.location.assign(r.url);
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  return (
    <div className="stack-sm">
      <div className="form-grid">
        <div className="field">
          <label htmlFor={ids.email}>E-Mail-Adresse</label>
          <input id={ids.email} type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value.trim())} placeholder="name@gmail.com" />
        </div>
        <div className="field">
          <label htmlFor={ids.provider}>Anbieter</label>
          <select
            id={ids.provider}
            value={provider}
            onChange={(e) => {
              setTouchedProvider(true);
              setProvider(e.target.value);
            }}
          >
            <option value="">bitte wählen …</option>
            {providers.map((x) => (
              <option key={x.id} value={x.id}>
                {x.label}
              </option>
            ))}
          </select>
        </div>
      </div>
      {p && <p className="small muted" style={{ margin: 0 }}>{p.hint}</p>}
      {!p && isEmail(email) && !customAllowed && (
        <p className="small muted" style={{ margin: 0 }}>
          Für diese Adresse gibt es keinen vorbereiteten Anbieter.
          <HelpTip>Eigene Mailserver darf nur Personal mit Freigabe eintragen. Bitte fragen Sie die Verwaltung.</HelpTip>
        </p>
      )}
      {p?.oauth && (
        <div className="row">
          <AsyncButton className="btn btn-primary" onClick={() => oauth(p.id as 'google' | 'microsoft')}>
            <Glyph name="lock" size={16} /> Mit {p.id === 'google' ? 'Google' : 'Microsoft'} anmelden
          </AsyncButton>
          {p.password_ok && <span className="small muted">oder unten mit App-Passwort</span>}
        </div>
      )}
      {p && !p.password_ok && !p.oauth && (
        <Alert kind="warning" title="Anmeldung über Microsoft noch nicht eingerichtet">
          Microsoft erlaubt den E-Mail-Zugriff nur über die Microsoft-Anmeldung.
          <HelpTip>Die Administration der Schule muss dafür einmal eine App bei Microsoft registrieren (Anleitung in der Betriebsdokumentation).</HelpTip>
        </Alert>
      )}
      {p && p.password_ok && (
        <>
          <div className="form-grid">
            <div className="field">
              <label htmlFor={ids.pw}>{provider === 'apple' || provider === 'google' || provider === 'yahoo' ? 'App-Passwort' : 'Passwort bzw. App-Passwort'}</label>
              <input id={ids.pw} type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor={ids.name}>Absendername (optional)</label>
              <input id={ids.name} value={name} onChange={(e) => setName(e.target.value)} placeholder="z. B. Frau Ludwig" />
            </div>
          </div>
          {custom && (
            <div className="form-grid">
              <div className="field">
                <label htmlFor={ids.imap}>IMAP-Server (Empfang)</label>
                <input id={ids.imap} value={server.imap_host} placeholder={p.imap_host || 'imap.beispiel.de'} onChange={(e) => setServer({ ...server, imap_host: e.target.value.trim() })} />
              </div>
              <div className="field">
                <label htmlFor={ids.imapPort}>IMAP-Port</label>
                <input id={ids.imapPort} type="number" value={server.imap_port} onChange={(e) => setServer({ ...server, imap_port: Number(e.target.value) || 993 })} />
              </div>
              <div className="field">
                <label htmlFor={ids.smtp}>SMTP-Server (Versand)</label>
                <input id={ids.smtp} value={server.smtp_host} placeholder={p.smtp_host || 'smtp.beispiel.de'} onChange={(e) => setServer({ ...server, smtp_host: e.target.value.trim() })} />
              </div>
              <div className="field">
                <label htmlFor={ids.smtpPort}>SMTP-Port</label>
                <input id={ids.smtpPort} type="number" value={server.smtp_port} onChange={(e) => setServer({ ...server, smtp_port: Number(e.target.value) || 587 })} />
              </div>
              <div className="field">
                <label htmlFor={ids.sec}>Verschlüsselung (Versand)</label>
                <select id={ids.sec} value={server.smtp_security} onChange={(e) => setServer({ ...server, smtp_security: e.target.value as 'ssl' | 'starttls' })}>
                  <option value="starttls">STARTTLS (meist Port 587)</option>
                  <option value="ssl">SSL/TLS (meist Port 465)</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor={ids.user}>Benutzername (falls nicht die Adresse)</label>
                <input id={ids.user} value={server.username} onChange={(e) => setServer({ ...server, username: e.target.value.trim() })} />
              </div>
            </div>
          )}
          <div className="row">
            <AsyncButton className="btn btn-primary" disabled={!email || !password} onClick={connect}>
              <Glyph name="mail" size={16} /> Verbinden und testen
            </AsyncButton>
          </div>
        </>
      )}
    </div>
  );
}

function AccountRow({ a, onChanged }: { a: MailAccount; onChanged: () => void }) {
  const toast = useToast();
  const run = async (fn: () => Promise<unknown>, ok: string) => {
    try {
      await fn();
      toast.success(ok);
      onChanged();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  return (
    <li className="pf-mail-account">
      <div>
        <strong>{a.display_name ? `${a.display_name} <${a.email}>` : a.email}</strong> <span className="badge">{a.provider_label}</span>{' '}
        {a.is_default && <span className="badge badge-primary">Standard</span>}{' '}
        {a.auth === 'oauth2' && <span className="badge">angemeldet über den Anbieter</span>}
        <div className="xsmall muted">
          {a.sync_enabled ? (a.last_sync_at ? `zuletzt abgerufen ${fullTime(a.last_sync_at)}` : 'wird gleich abgerufen') : 'Abruf ausgeschaltet'}
        </div>
        {a.last_error && <div className="small" style={{ color: 'var(--danger, #b42318)' }}>{a.last_error}</div>}
      </div>
      <div className="row">
        <AsyncButton
          className="btn btn-sm"
          onClick={async () => {
            try {
              const r = await mailApi.sync(a.id);
              toast.success(r.imported ? `${r.imported} neue E-Mail(s) übernommen` : 'Keine neuen E-Mails');
              onChanged();
            } catch (e) {
              toast.error(errorMessage(e));
            }
          }}
        >
          <Glyph name="unread" size={14} /> Jetzt abrufen
        </AsyncButton>
        <label className="check small">
          <input type="checkbox" checked={a.sync_enabled} onChange={(e) => void run(() => mailApi.patch(a.id, { sync_enabled: e.target.checked }), e.target.checked ? 'Abruf eingeschaltet' : 'Abruf ausgeschaltet')} />{' '}
          E-Mails abrufen
        </label>
        {!a.is_default && (
          <AsyncButton className="btn btn-sm btn-ghost" onClick={() => run(() => mailApi.patch(a.id, { is_default: true }), 'Als Standard gesetzt')}>
            Als Standard
          </AsyncButton>
        )}
        {a.auth === 'password' && (
          <AsyncButton
            className="btn btn-sm btn-ghost"
            onClick={async () => {
              const pw = await promptAsk({ title: 'Passwort ändern', message: `Neues (App-)Passwort für ${a.email}`, confirmLabel: 'Speichern', secret: true });
              if (pw) await run(() => mailApi.patch(a.id, { password: pw }), 'Passwort aktualisiert');
            }}
          >
            Passwort ändern
          </AsyncButton>
        )}
        <AsyncButton
          className="btn btn-sm btn-ghost"
          confirm={`${a.email} trennen? Bereits abgerufene E-Mails bleiben im Postfach.`}
          onClick={() => run(() => mailApi.remove(a.id), 'Konto getrennt')}
        >
          <Glyph name="trash" size={14} /> Trennen
        </AsyncButton>
      </div>
    </li>
  );
}

export function MailAccounts() {
  const toast = useToast();
  const [params, setParams] = useSearchParams();
  const acc = useApi((signal) => mailApi.accounts(signal), []);
  const prov = useApi((signal) => mailApi.providers(signal), []);
  const [adding, setAdding] = useState(false);
  const providers = useMemo(() => prov.data?.providers ?? [], [prov.data]);

  // Rückkehr von der Google-/Microsoft-Anmeldung
  useEffect(() => {
    const state = params.get('mail');
    if (!state) return;
    if (state === 'verbunden') toast.success('E-Mail-Konto verbunden');
    else if (state === 'abgebrochen') toast.info('Anmeldung abgebrochen');
    else toast.error('Das E-Mail-Konto konnte nicht verbunden werden');
    const next = new URLSearchParams(params);
    next.delete('mail');
    setParams(next, { replace: true });
    acc.reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const list = acc.data?.accounts ?? [];
  return (
    <section className="card stack-sm" aria-labelledby="pf-set-accounts">
      <h2 id="pf-set-accounts">
        E-Mail-Konten
        <HelpTip>
          Verbinden Sie Ihr E-Mail-Konto (Google, Apple/iCloud, Microsoft/Outlook, GMX, WEB.DE, T-Online, Yahoo oder ein anderes). Dann können Sie im Postfach auch an E-Mail-Adressen außerhalb der Schule schreiben, und Ihre E-Mails erscheinen hier
          im Postfach. Ihr Postfach beim Anbieter bleibt unverändert; Zugangsdaten werden verschlüsselt gespeichert.
        </HelpTip>
      </h2>
      {acc.error ? <ErrorBox error={acc.error} onRetry={acc.reload} /> : null}
      {(acc.initialLoading || prov.initialLoading) && <Loading />}
      {list.length > 0 && (
        <ul className="pf-people pf-mail-accounts">
          {list.map((a) => (
            <AccountRow key={a.id} a={a} onChanged={acc.reload} />
          ))}
        </ul>
      )}
      {acc.data && !list.length && !adding && <p className="small">Noch kein E-Mail-Konto verbunden.</p>}
      {adding ? (
        <div className="card stack-sm">
          <ConnectForm
            providers={providers}
            customAllowed={prov.data?.custom_allowed ?? false}
            onDone={() => {
              setAdding(false);
              acc.reload();
            }}
          />
          <div>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setAdding(false)}>
              Abbrechen
            </button>
          </div>
        </div>
      ) : (
        acc.data &&
        list.length < (acc.data.max ?? 5) && (
          <div>
            <button type="button" className="btn" onClick={() => setAdding(true)}>
              <Glyph name="mail" size={16} /> E-Mail-Konto verbinden
            </button>
          </div>
        )
      )}
    </section>
  );
}

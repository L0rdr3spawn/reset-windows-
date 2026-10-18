/**
 * Benutzerverwaltung, Reiter „Kontakt“ im Konto-Dialog (§11.2, Admin/Sekretariat): E-Mail/Handynummer setzen, als
 * bestätigt markieren, Nummer entfernen, „Link zum Zurücksetzen senden“. Das Backend prüft Recht und Rolle
 * (Sekretariat nur Schüler/innen und Eltern).
 */
import { useEffect, useId, useState, type FormEvent } from 'react';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Alert, AsyncButton, ErrorBox, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { formatDateTime } from '../../lib/dates';
import { adminContactApi } from './api';
import { DevOutboxHint } from './components';
import { channelList, formatPhone, isValidEmail, normalizePhone } from './logic';
import type { AdminContact, AdminContactInput, ResetChannel } from './types';
import './konto.css';

function resetReason(c: AdminContact, channel: ResetChannel): string | null {
  if (!c.active) return 'Konto ist deaktiviert.';
  if (!c.password_login) return 'Anmeldung mit Passwort ist laut Richtlinie nicht erlaubt.';
  if (channel === 'email' && !c.email_verified) return 'Keine bestätigte E-Mail-Adresse.';
  if (channel === 'sms' && !c.phone_verified) return 'Keine bestätigte Handynummer.';
  return null;
}

export function UserContactPanel({ userId, onEmailChange }: { userId: number; onEmailChange?: (email: string | null) => void }) {
  const id = useId();
  const toast = useToast();
  const data = useApi((signal) => adminContactApi.get(userId, signal), [userId]);
  const { setData } = data;
  const c = data.data;
  const [email, setEmail] = useState('');
  const [emailVerified, setEmailVerified] = useState(false);
  const [phone, setPhone] = useState('');
  const [phoneVerified, setPhoneVerified] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!c) return;
    setEmail(c.email ?? '');
    setEmailVerified(c.email_verified);
    setPhone(c.phone ? formatPhone(c.phone) : '');
    setPhoneVerified(c.phone_verified);
  }, [c]);

  if (data.error) return <ErrorBox error={data.error} onRetry={data.reload} />;
  if (!c) return <Loading />;

  // nur Wege anbieten, die der Server zustellen kann (sonst gar nicht anzeigen)
  const sendWays = (['email', 'sms'] as const).filter((ch) => c.channels[ch]);
  const showPhone = c.channels.sms || !!c.phone;
  const normalized = phone.trim() ? normalizePhone(phone) : null;
  const emailOk = !email.trim() || isValidEmail(email);
  const phoneOk = !phone.trim() || normalized !== null;

  const body = (): AdminContactInput => {
    const out: AdminContactInput = {};
    const nextEmail = email.trim() || null;
    if ((nextEmail ?? '') !== (c.email ?? '')) out.email = nextEmail;
    const emailChanged = (nextEmail ?? '').toLowerCase() !== (c.email ?? '').toLowerCase();
    if (nextEmail && (emailVerified !== c.email_verified || (emailChanged && emailVerified))) out.email_verified = emailVerified;
    if (!nextEmail && c.email_verified) out.email_verified = false;
    if ((normalized ?? null) !== (c.phone ?? null)) out.phone = normalized;
    const phoneChanged = (normalized ?? null) !== (c.phone ?? null);
    if (normalized && (phoneVerified !== c.phone_verified || (phoneChanged && phoneVerified))) out.phone_verified = phoneVerified;
    return out;
  };

  const save = async (e: FormEvent) => {
    e.preventDefault();
    const payload = body();
    if (Object.keys(payload).length === 0) {
      toast.info('Keine Änderungen');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await adminContactApi.put(userId, payload);
      setData(res);
      if ('email' in payload) onEmailChange?.(res.email);
      toast.success('Kontakt gespeichert');
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const send = async (channel: ResetChannel) => {
    try {
      const res = await adminContactApi.sendReset(userId, channel);
      toast.success(channel === 'email' ? `Link zum Zurücksetzen an ${res.sent_to} gesendet` : `Code zum Zurücksetzen per SMS an ${res.sent_to} gesendet`);
    } catch (err) {
      toast.error(err);
    }
  };

  return (
    <div className="stack ko-admin">
      {error && <Alert kind="error">{error}</Alert>}
      <form className="stack" onSubmit={save} autoComplete="off" noValidate>
        <div className="form-grid">
          <div className="field">
            <label htmlFor={`${id}-mail`}>E-Mail-Adresse</label>
            <input id={`${id}-mail`} name="contact-email" type="email" autoComplete="off" value={email} onChange={(e) => setEmail(e.target.value)} aria-invalid={!emailOk} />
            {!emailOk && <span className="error-text">Bitte eine gültige Adresse angeben.</span>}
            <label className="check small">
              <input type="checkbox" checked={emailVerified && !!email.trim()} disabled={!email.trim()} onChange={(e) => setEmailVerified(e.target.checked)} /> bestätigt
              {c.email_verified && c.email_verified_at ? <span className="muted"> (seit {formatDateTime(c.email_verified_at)})</span> : null}
            </label>
          </div>
          {showPhone && (
          <div className="field">
            <label htmlFor={`${id}-tel`}>Handynummer</label>
            <input id={`${id}-tel`} name="contact-tel" type="tel" inputMode="tel" autoComplete="off" value={phone} onChange={(e) => setPhone(e.target.value)} aria-invalid={!phoneOk} aria-describedby={`${id}-tel-hint`} />
            <span className={phoneOk ? 'hint' : 'error-text'} id={`${id}-tel-hint`}>
              {!phone.trim() ? 'Mit Vorwahl, z. B. 0171 1234567.' : normalized ? `wird gespeichert als ${formatPhone(normalized)}` : 'Bitte mit Vorwahl angeben (0… oder +…).'}
            </span>
            <label className="check small">
              <input type="checkbox" checked={phoneVerified && !!normalized} disabled={!normalized} onChange={(e) => setPhoneVerified(e.target.checked)} /> bestätigt
              {c.phone_verified && c.phone_verified_at ? <span className="muted"> (seit {formatDateTime(c.phone_verified_at)})</span> : null}
            </label>
          </div>
          )}
        </div>
        <p className="small muted">
          Nur bestätigte Kontakte werden verwendet.
          <HelpTip>Nur als bestätigt markieren, wenn Adresse bzw. Nummer sicher dieser Person gehört (z. B. persönlich geprüft). Dorthin kann ein Link zum Zurücksetzen des Passworts gehen.</HelpTip>
        </p>
        <div className="row-end ko-wrap">
          {c.phone && (
            <button type="button" className="btn btn-ghost" onClick={() => setPhone('')}>
              <Icon name="trash" /> Nummer entfernen
            </button>
          )}
          <button type="submit" className="btn btn-primary" disabled={busy || !emailOk || !phoneOk}>
            {busy ? 'Speichern …' : 'Kontakt speichern'}
          </button>
        </div>
      </form>

      {sendWays.length > 0 && (
      <section className="stack" aria-labelledby={`${id}-reset`}>
        <h3 id={`${id}-reset`}>
          Passwort zurücksetzen lassen
          <HelpTip>
            Schickt einen Link (E-Mail) bzw. Code (SMS), mit dem die Person selbst ein neues Passwort festlegt, gültig {c.code_minutes} Minuten. Alternative für Personen ohne bestätigten Kontakt: neues Einmalpasswort im Reiter „Sicherheit“.
          </HelpTip>
        </h3>
        <p className="small muted">
          {c.reset_channels.length
            ? `Selbst zurücksetzen („Passwort vergessen“) ist laut Richtlinie per ${channelList(c.reset_channels)} erlaubt.`
            : 'Selbst zurücksetzen („Passwort vergessen“) ist laut Richtlinie für dieses Konto nicht freigeschaltet.'}
        </p>
        <div className="ko-actions">
          {sendWays.map((ch) => {
            const reason = resetReason(c, ch);
            return (
              <AsyncButton key={ch} className="btn" disabled={!!reason} title={reason ?? undefined} onClick={() => send(ch)} confirm={`${ch === 'email' ? 'Link per E-Mail' : 'Code per SMS'} an ${c.display_name || c.username} senden?`}>
                <Icon name={ch === 'email' ? 'mail' : 'megaphone'} /> {ch === 'email' ? 'Link per E-Mail senden' : 'Code per SMS senden'}
              </AsyncButton>
            );
          })}
        </div>
        {sendWays.some((ch) => resetReason(c, ch)) && (
          <ul className="list-plain small muted">
            {sendWays.map((ch) => {
              const reason = resetReason(c, ch);
              return reason ? <li key={ch}>{ch === 'email' ? 'E-Mail' : 'SMS'}: {reason}</li> : null;
            })}
          </ul>
        )}
        {c.dev_outbox && <DevOutboxHint />}
      </section>
      )}
    </div>
  );
}

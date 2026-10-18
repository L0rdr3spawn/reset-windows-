/**
 * Öffentliche Seite „Passwort vergessen“ (§11.2): Kennung + Kanal → neutrale Bestätigung → Code → neues Passwort.
 * Die Antwort des Servers ist für bekannte und unbekannte Kennungen gleich – die Seite verrät nie, ob es ein Konto gibt.
 */
import { useId, useState, type FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Alert } from '../../components/ui';
import { useAuth } from '../../context/AuthContext';
import { useApi } from '../../hooks/useApi';
import { useTitle } from '../../hooks/misc';
import { resetApi } from './api';
import { CodeInput, DevOutboxHint, NewPasswordForm } from './components';
import { anyChannel, cleanCode, contactWays, isCompleteCode, managedByStaffNote } from './logic';
import type { ResetRequestResult, ResetVerifyResult } from './types';
import './konto.css';

type Step = 'request' | 'code' | 'password';

export default function ForgotPasswordPage() {
  useTitle('Passwort vergessen');
  const id = useId();
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const [params] = useSearchParams();
  const options = useApi((signal) => resetApi.options(signal), []);
  const [step, setStep] = useState<Step>(params.get('code') ? 'code' : 'request');
  const [identifier, setIdentifier] = useState(params.get('kennung') ?? '');
  const [sent, setSent] = useState<ResetRequestResult | null>(null);
  const [code, setCode] = useState('');
  const [reset, setReset] = useState<ResetVerifyResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const devOutbox = options.data?.dev_outbox ?? sent?.dev_outbox ?? false;

  const noChannel = options.data ? !anyChannel(options.data) : false;
  const staffNote = managedByStaffNote(options.data);
  const ways = contactWays(options.data) || 'E-Mail-Adresse oder Handynummer';

  const request = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await resetApi.request(identifier.trim(), 'auto');
      setSent(res);
      setCode('');
      setStep('code');
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
      const res = await resetApi.verifyCode(identifier.trim(), cleanCode(code));
      setReset(res);
      setStep('password');
    } catch (err) {
      setError(errorMessage(err));
      setCode('');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-wrap">
      <main className="card login-card ko-card">
        <h1 className="with-help">
          Passwort vergessen
          <HelpTip label="Hilfe zu Passwort vergessen">
            Wir schicken einen Code an die bestätigte {ways} Ihres Kontos (hinterlegen unter Profil, „E-Mail & Handynummer“). Der Code ist{' '}
            {options.data?.code_minutes ?? 15} Minuten gültig. Nichts angekommen? Prüfen Sie den Spam-Ordner. Ohne bestätigte Angabe hilft das
            Sekretariat.
          </HelpTip>
        </h1>
        {error && (
          <Alert kind="error" title="Das hat nicht geklappt">
            {error}
          </Alert>
        )}

        {step === 'request' && (
          <>
            {staffNote && <p className="small muted">{staffNote}</p>}
            {noChannel ? (
              <p>Bitte wenden Sie sich an das Sekretariat oder Ihre Klassenleitung, wenn Sie Ihr Passwort vergessen haben.</p>
            ) : (
            <form className="stack" onSubmit={request} noValidate>
              <div className="field">
                <label htmlFor={`${id}-ident`}>Benutzername, E-Mail oder Handynummer</label>
                <input
                  id={`${id}-ident`}
                  name="username"
                  type="text"
                  autoComplete="username"
                  autoCapitalize="none"
                  autoCorrect="off"
                  spellCheck={false}
                  required
                  autoFocus
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                />
              </div>
              <button type="submit" className="btn btn-primary w-100" disabled={busy || !identifier.trim()}>
                {busy ? 'Wird gesendet …' : 'Code senden'}
              </button>
            </form>
            )}
            {!noChannel && (
              <button type="button" className="btn btn-ghost w-100" onClick={() => { setError(null); setStep('code'); }}>
                Ich habe schon einen Code
              </button>
            )}
          </>
        )}

        {step === 'code' && (
          <>
            {sent && <p aria-live="polite">{sent.message}</p>}
            {devOutbox && <DevOutboxHint />}
            <form className="stack" onSubmit={verify} noValidate>
              {!sent && (
                <div className="field">
                  <label htmlFor={`${id}-ident2`}>Benutzername, E-Mail oder Handynummer</label>
                  <input
                    id={`${id}-ident2`}
                    name="username"
                    type="text"
                    autoComplete="username"
                    autoCapitalize="none"
                    autoCorrect="off"
                    spellCheck={false}
                    required
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                  />
                </div>
              )}
              <CodeInput id={`${id}-code`} value={code} onChange={setCode} label="Code (6 Ziffern)" />
              <button type="submit" className="btn btn-primary w-100" disabled={busy || !identifier.trim() || !isCompleteCode(code)}>
                {busy ? 'Wird geprüft …' : 'Weiter'}
              </button>
            </form>
            <button type="button" className="btn btn-ghost w-100" onClick={() => { setError(null); setSent(null); setStep('request'); }}>
              Neuen Code anfordern
            </button>
          </>
        )}

        {step === 'password' && reset && (
          <>
            <p>Neues Passwort für {reset.display_name || reset.username}:</p>
            <NewPasswordForm
              username={reset.username}
              minLength={reset.min_length}
              onSubmit={async (pw) => {
                await resetApi.confirm(reset.reset_token, pw);
                await refresh();
                navigate('/login?reset=ok', { replace: true });
              }}
            />
          </>
        )}

        <div className="row-end">
          <Link className="btn btn-ghost btn-sm" to="/login">
            Zurück zur Anmeldung
          </Link>
        </div>
      </main>
    </div>
  );
}

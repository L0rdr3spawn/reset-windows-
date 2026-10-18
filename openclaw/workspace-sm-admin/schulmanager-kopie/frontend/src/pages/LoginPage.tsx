import { useState, type FormEvent } from 'react';
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { ApiError, errorMessage } from '../api/client';
import { Icon } from '../components/Icon';
import { Alert, Field, Loading } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useTitle } from '../hooks/misc';
import { homePath } from '../lib/permissions';
import { SSO_ERROR_MESSAGES, SsoButtons } from '../features/anmeldedienste/slots';
import { ForgotPasswordLink } from '../features/konto/slots';
import { PasswordInput } from '../components/PasswordInput';
import { BrandLogo } from '../components/BrandLogo';
import { APP_NAME } from '../brand';

const SSO_ERRORS: Record<string, string> = {
  not_configured: 'Single Sign-on ist nicht eingerichtet.',
  state: 'Die Anmeldung ist abgelaufen – bitte erneut versuchen.',
  provider: 'Der Anmeldedienst hat einen Fehler gemeldet.',
  unknown_user: `Zu diesem Konto gibt es keinen Zugang im ${APP_NAME}.`,
  account_disabled: 'Dieses Konto ist deaktiviert.',
  ...SSO_ERROR_MESSAGES,
};

/** Nur interne Pfade als Rücksprungziel zulassen (kein Open Redirect). */
function safeNext(next: string | null): string | null {
  if (!next || !next.startsWith('/') || next.startsWith('//') || next.startsWith('/login')) return null;
  return next;
}

export default function LoginPage() {
  useTitle('Anmelden');
  const { user, loading, login, expired } = useAuth();
  const { mode, nextMode } = useTheme();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [totp, setTotp] = useState('');
  /** Schritt 2: Passwort stimmt, das Konto verlangt den Bestätigungscode (Zwei-Faktor) */
  const [needCode, setNeedCode] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const next = safeNext(params.get('next'));
  const ssoError = params.get('sso_error');

  if (loading) return <Loading />;
  if (user) {
    if (user.must_change_password) return <Navigate to="/passwort" replace />;
    return <Navigate to={next ?? homePath(user)} replace />;
  }

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const u = await login(username.trim(), password, needCode ? totp.trim() || undefined : undefined);
      if (u === null) {
        setNeedCode(true);
        setTotp('');
        return;
      }
      if (u.must_change_password) navigate('/passwort', { replace: true });
      else navigate(next ?? homePath(u), { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        setError('Zu viele Fehlversuche von diesem Anschluss. Bitte kurz warten und erneut versuchen.');
      } else {
        setError(needCode && err instanceof ApiError && err.status === 401
          ? 'Der Code ist falsch oder wurde schon verwendet. Bitte warten Sie auf den nächsten Code.'
          : errorMessage(err));
        setTotp('');
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-wrap">
      <main className="card login-card">
        <div className="row-between">
          <div className="login-brand">
            <span className="brand-logo" aria-hidden="true">
              <BrandLogo />
            </span>
            {APP_NAME}
          </div>
          <button type="button" className="btn btn-ghost btn-icon" onClick={nextMode} aria-label="Farbschema umschalten" title={`Farbschema: ${mode}`}>
            <Icon name={mode === 'dark' ? 'moon' : mode === 'light' ? 'sun' : 'contrast'} />
          </button>
        </div>
        <h1>Anmelden</h1>
        {ssoError && (
          <Alert kind="error" title="Anmeldung über Single Sign-on fehlgeschlagen">
            {SSO_ERRORS[ssoError] ?? 'Unbekannter Fehler.'}
          </Alert>
        )}
        {expired && !error && (
          <Alert kind="info" title="Sitzung abgelaufen">
            Bitte erneut anmelden.
          </Alert>
        )}
        {error && (
          <Alert kind="error" title="Anmeldung fehlgeschlagen">
            {error}
          </Alert>
        )}
        {needCode ? (
          <form onSubmit={submit} className="stack" noValidate>
            <p className="small muted">
              Konto {username.trim()}. Geben Sie den 6-stelligen Code aus Ihrer Authenticator-App ein.
            </p>
            <input type="text" name="username" value={username} autoComplete="username" readOnly hidden />
            <Field label="Bestätigungscode" htmlFor="login-totp" help="Der Code wechselt alle 30 Sekunden. Ohne Authenticator-App hilft die Administration.">
              <input
                id="login-totp"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                pattern="[0-9]*"
                maxLength={8}
                required
                autoFocus
                value={totp}
                onChange={(e) => setTotp(e.target.value.replace(/\s/g, ''))}
              />
            </Field>
            <button type="submit" className="btn btn-primary w-100" disabled={busy || !totp}>
              {busy ? 'Prüfen …' : 'Anmelden'}
            </button>
            <button
              type="button"
              className="btn btn-ghost w-100"
              onClick={() => {
                setNeedCode(false);
                setTotp('');
                setPassword('');
                setError(null);
              }}
            >
              Zurück
            </button>
          </form>
        ) : (
          <form onSubmit={submit} className="stack" noValidate>
            <Field label="Benutzername" htmlFor="login-user" help="Wie auf Ihrem Zugangsbrief. Groß- und Kleinschreibung spielt keine Rolle.">
              <input
                id="login-user"
                type="text"
                autoComplete="username"
                autoCapitalize="none"
                autoCorrect="off"
                spellCheck={false}
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoFocus
              />
            </Field>
            <Field label="Passwort" htmlFor="login-pass">
              <PasswordInput
                id="login-pass"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </Field>
            <button type="submit" className="btn btn-primary w-100" disabled={busy || !username || !password}>
              {busy ? 'Anmelden …' : 'Anmelden'}
            </button>
          </form>
        )}
        {!needCode && <ForgotPasswordLink />}
        {!needCode && <SsoButtons next={next} />}
      </main>
    </div>
  );
}

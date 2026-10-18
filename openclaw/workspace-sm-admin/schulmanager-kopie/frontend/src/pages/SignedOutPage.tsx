/**
 * Seite nach dem Abmelden: „Sie sind abgemeldet.“ + die in diesem Browser noch angemeldeten weiteren Konten
 * (Klick = weiter als …, × = dieses Konto auch abmelden) + „Mit anderem Konto anmelden“. Ohne weitere Konten geht es
 * direkt zur Anmeldeseite. Die Seite zeigt nie Daten des gerade abgemeldeten Kontos: die Liste kommt vom Server und
 * enthält nur Konten mit gültiger Sitzung (Name, Rolle).
 */
import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { errorMessage } from '../api/client';
import { auth as authApi } from '../api/endpoints';
import { Icon } from '../components/Icon';
import { Alert, Loading } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { BrandLogo } from '../components/BrandLogo';
import { APP_NAME } from '../brand';
import { useTitle } from '../hooks/misc';
import { useApi } from '../hooks/useApi';
import { homePath, ROLE_LABELS } from '../lib/permissions';

export default function SignedOutPage() {
  useTitle('Abgemeldet');
  const { user, loading, switchAccount } = useAuth();
  const { mode, nextMode } = useTheme();
  const q = useApi((signal) => authApi.accounts(signal), []);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<number | null>(null);

  if (loading || q.loading) return <Loading />;
  if (user) return <Navigate to={homePath(user)} replace />;
  const accounts = (q.data?.accounts ?? []).filter((a) => !a.active);
  if (!q.error && accounts.length === 0) return <Navigate to="/login" replace />;

  const choose = async (id: number) => {
    setBusy(id);
    setError(null);
    try {
      await switchAccount(id);
    } catch (e) {
      setError(errorMessage(e));
      setBusy(null);
      q.reload();
    }
  };
  const signOutOne = async (id: number) => {
    setBusy(id);
    setError(null);
    try {
      await authApi.logoutOther(id);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(null);
      q.reload();
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
        <h1>Sie sind abgemeldet.</h1>
        {error || q.error ? <Alert kind="error">{error ?? errorMessage(q.error)}</Alert> : null}
        <div className="stack">
          <div className="small muted" id="signedout-accounts">
            Noch angemeldet in diesem Browser
          </div>
          <ul className="list-plain signedout-list" aria-labelledby="signedout-accounts">
            {accounts.map((a) => (
              <li key={a.id} className="acc-row">
                <button type="button" className="btn signedout-account" disabled={busy !== null} onClick={() => void choose(a.id)}>
                  <Icon name="user" />
                  <span>
                    Weiter als {a.display_name || a.username}
                    <span className="xsmall muted"> · {ROLE_LABELS[a.role] ?? a.role}</span>
                  </span>
                </button>
                <button
                  type="button"
                  className="btn btn-ghost btn-icon btn-sm"
                  aria-label={`${a.display_name || a.username} abmelden`}
                  title="Dieses Konto abmelden"
                  disabled={busy !== null}
                  onClick={() => void signOutOne(a.id)}
                >
                  <Icon name="x" />
                </button>
              </li>
            ))}
          </ul>
          <Link className="btn btn-primary w-100" to="/login">
            Mit anderem Konto anmelden
          </Link>
        </div>
      </main>
    </div>
  );
}

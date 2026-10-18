/**
 * Öffentliche Seite `/passwort-zuruecksetzen?token=…` (Link aus der E-Mail, §11.2): Link prüfen → neues Passwort →
 * `/login?reset=ok`. Der Link ist nur einmal gültig; das daraus erzeugte kurzlebige Reset-Token bleibt für diesen
 * Tab in `sessionStorage`, damit ein Neuladen der Seite nicht ins Leere läuft.
 */
import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import { Alert, Loading } from '../../components/ui';
import { useAuth } from '../../context/AuthContext';
import { useTitle } from '../../hooks/misc';
import { resetApi } from './api';
import { NewPasswordForm } from './components';
import type { ResetVerifyResult } from './types';
import './konto.css';

const STORAGE_KEY = 'sm-konto-reset';
/** Gleiche Prüfung nur einmal (React StrictMode ruft Effekte doppelt auf, der Link ist aber einmalig). */
const pending = new Map<string, Promise<ResetVerifyResult>>();

function loadStored(token: string): ResetVerifyResult | null {
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as { link?: string; result?: ResetVerifyResult };
    if (data.link !== token || !data.result) return null;
    if (Date.parse(data.result.expires_at) < Date.now()) return null;
    return data.result;
  } catch {
    return null;
  }
}

function store(token: string, result: ResetVerifyResult | null): void {
  try {
    if (result) window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ link: token, result }));
    else window.sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    /* privater Modus: ohne Zwischenspeicher */
  }
}

function verifyOnce(token: string): Promise<ResetVerifyResult> {
  let p = pending.get(token);
  if (!p) {
    p = resetApi.verifyLink(token);
    pending.set(token, p);
  }
  return p;
}

export default function ResetPasswordPage() {
  useTitle('Neues Passwort festlegen');
  const [params] = useSearchParams();
  const token = params.get('token') ?? '';
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const [reset, setReset] = useState<ResetVerifyResult | null>(() => (token ? loadStored(token) : null));
  const [error, setError] = useState<string | null>(token ? null : 'Der Link ist unvollständig.');

  useEffect(() => {
    if (!token || reset) return;
    let active = true;
    verifyOnce(token)
      .then((res) => {
        store(token, res);
        if (active) setReset(res);
      })
      .catch((err: unknown) => {
        if (active) setError(errorMessage(err));
      });
    return () => {
      active = false;
    };
  }, [token, reset]);

  return (
    <div className="login-wrap">
      <main className="card login-card ko-card">
        <h1>Neues Passwort festlegen</h1>
        {error ? (
          <>
            <Alert kind="error" title="Link nicht gültig">
              {error}
            </Alert>
            <p>
              <Link to="/passwort-vergessen">Neuen Code oder Link anfordern</Link>
            </p>
          </>
        ) : !reset ? (
          <Loading label="Link wird geprüft …" />
        ) : (
          <>
            <p>
              Neues Passwort für <strong>{reset.display_name || reset.username}</strong>:
            </p>
            <NewPasswordForm
              username={reset.username}
              minLength={reset.min_length}
              onSubmit={async (pw) => {
                await resetApi.confirm(reset.reset_token, pw);
                store(token, null);
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

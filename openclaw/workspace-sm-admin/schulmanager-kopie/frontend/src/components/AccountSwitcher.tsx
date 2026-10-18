/**
 * Kontowechsel im Benutzermenü: alle in diesem Browser angemeldeten Konten, mit einem Klick wechseln, weiteres Konto
 * anmelden (ohne Abmelden). Abmelden (mit Rückfrage) gibt es hier und unten in der Seitenleiste; die übrigen Konten wählt/meldet die Seite
 * „Abgemeldet“ danach ab. Höchstens 5 Konten je Browser.
 */
import { useState, type FormEvent } from 'react';
import { ApiError, errorMessage } from '../api/client';
import { auth as authApi } from '../api/endpoints';
import { useAuth } from '../context/AuthContext';
import { SsoButtons } from '../features/anmeldedienste/slots';
import { useApi } from '../hooks/useApi';
import { ROLE_LABELS } from '../lib/permissions';
import { Icon } from './Icon';
import { Modal } from './Modal';
import { Alert } from './ui';

export function AddAccountModal({ onClose }: { onClose: () => void }) {
  const { addAccount } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [totp, setTotp] = useState('');
  const [needCode, setNeedCode] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await addAccount(username.trim(), password, needCode ? totp.trim() || undefined : undefined);
      if (res === 'code_needed') {
        setNeedCode(true);
        setTotp('');
      }
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 401
          ? needCode
            ? 'Der Code ist falsch oder wurde schon verwendet.'
            : 'Benutzername oder Passwort ist falsch.'
          : errorMessage(err),
      );
      setTotp('');
    } finally {
      setBusy(false);
    }
  };
  return (
    <Modal title="Weiteres Konto anmelden" onClose={onClose}>
      <form className="stack" onSubmit={submit} noValidate>
        {error && <Alert kind="error">{error}</Alert>}
        {needCode ? (
          <>
            <p className="small muted">Konto {username.trim()}. Geben Sie den 6-stelligen Code aus Ihrer Authenticator-App ein.</p>
            <div className="field">
              <label htmlFor="acc-totp">Bestätigungscode</label>
              <input id="acc-totp" inputMode="numeric" autoComplete="one-time-code" maxLength={8} value={totp} onChange={(e) => setTotp(e.target.value.replace(/\s/g, ''))} autoFocus />
            </div>
          </>
        ) : (
          <>
            <div className="field">
              <label htmlFor="acc-user">Benutzername</label>
              <input id="acc-user" autoComplete="username" autoCapitalize="none" spellCheck={false} value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
            </div>
            <div className="field">
              <label htmlFor="acc-pass">Passwort</label>
              <input id="acc-pass" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
          </>
        )}
        <div className="row" style={{ justifyContent: 'flex-end' }}>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <button type="submit" className="btn btn-primary" disabled={busy || !username || !password || (needCode && !totp)}>
            {busy ? 'Anmelden …' : 'Anmelden'}
          </button>
        </div>
      </form>
      {!needCode && <SsoButtons next={null} add />}
    </Modal>
  );
}

/** Bestätigung vor dem Abmelden (Benutzermenü und Seitenleiste). Meldet nur das aktive Konto ab. */
export function LogoutConfirm({ onClose }: { onClose: () => void }) {
  const { logout } = useAuth();
  const [busy, setBusy] = useState(false);
  return (
    <Modal
      title="Abmelden"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose} disabled={busy}>
            Nein
          </button>
          <button
            type="button"
            className="btn btn-primary"
            disabled={busy}
            onClick={() => {
              setBusy(true);
              void logout();
            }}
          >
            Ja, abmelden
          </button>
        </>
      }
    >
      <p>Möchten Sie sich wirklich abmelden?</p>
    </Modal>
  );
}

/** Abschnitt im Benutzermenü */
export function AccountSwitcher({ onAction, onAdd, onLogout }: { onAction: () => void; onAdd: () => void; onLogout: () => void }) {
  const { switchAccount } = useAuth();
  const q = useApi((signal) => authApi.accounts(signal), []);
  const others = (q.data?.accounts ?? []).filter((a) => !a.active);
  const full = (q.data?.accounts.length ?? 0) >= (q.data?.max ?? 5);
  return (
    <>
      {others.length > 0 && <div className="small muted" style={{ padding: '4px 12px' }}>Konto wechseln</div>}
      {others.map((a) => (
        <div key={a.id} className="acc-row">
          <button
            role="menuitem"
            type="button"
            className="item"
            onClick={() => {
              onAction();
              void switchAccount(a.id);
            }}
          >
            <Icon name="user" /> {a.display_name || a.username}
            <span className="xsmall muted"> · {ROLE_LABELS[a.role] ?? a.role}</span>
          </button>
        </div>
      ))}
      {!full && (
        <button
          role="menuitem"
          type="button"
          className="item"
          onClick={() => {
            onAction();
            onAdd();
          }}
        >
          <Icon name="plus" /> Weiteres Konto anmelden
        </button>
      )}
      <button
        role="menuitem"
        type="button"
        className="item"
        onClick={() => {
          onAction();
          onLogout();
        }}
      >
        <Icon name="logout" /> Abmelden
      </button>
    </>
  );
}

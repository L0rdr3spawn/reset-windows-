import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { errorMessage } from '../api/client';
import { auth } from '../api/endpoints';
import { Alert } from '../components/ui';
import { useAuth, useUser } from '../context/AuthContext';
import { useTitle } from '../hooks/misc';
import { homePath } from '../lib/permissions';
import { PasswordInput } from '../components/PasswordInput';

export function passwordHints(pw: string): string[] {
  const out: string[] = [];
  if (pw.length < 10) out.push('mindestens 10 Zeichen');
  if (!/[a-zäöüß]/.test(pw) || !/[A-ZÄÖÜ]/.test(pw)) out.push('Groß- und Kleinbuchstaben');
  if (!/[0-9]/.test(pw)) out.push('mindestens eine Ziffer');
  return out;
}

/** Formular zum Ändern des Passworts (auch als Pflichtseite nach Erstanmeldung). */
export function PasswordForm({ onDone, forced }: { onDone: () => void; forced?: boolean }) {
  const [oldPw, setOldPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [repeat, setRepeat] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hints = passwordHints(newPw);
  const mismatch = repeat.length > 0 && repeat !== newPw;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (newPw !== repeat) {
      setError('Die Passwörter stimmen nicht überein.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await auth.changePassword(oldPw, newPw);
      setOldPw('');
      setNewPw('');
      setRepeat('');
      onDone();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="stack" noValidate>
      {error && <Alert kind="error">{error}</Alert>}
      <div className="field">
        <label htmlFor="pw-old">{forced ? 'Bisheriges (vorläufiges) Passwort' : 'Bisheriges Passwort'}</label>
        <PasswordInput id="pw-old" autoComplete="current-password" value={oldPw} onChange={(e) => setOldPw(e.target.value)} required />
      </div>
      <div className="field">
        <label htmlFor="pw-new">Neues Passwort</label>
        <PasswordInput id="pw-new" autoComplete="new-password" value={newPw} onChange={(e) => setNewPw(e.target.value)} aria-describedby="pw-hints" required />
        <span className="hint" id="pw-hints" aria-live="polite">
          {newPw && hints.length ? `Empfehlung: ${hints.join(', ')}` : newPw ? 'Sieht gut aus.' : 'Empfehlung: mindestens 10 Zeichen, Groß-/Kleinbuchstaben und Ziffern.'}
        </span>
      </div>
      <div className="field">
        <label htmlFor="pw-rep">Neues Passwort wiederholen</label>
        <PasswordInput id="pw-rep" autoComplete="new-password" value={repeat} onChange={(e) => setRepeat(e.target.value)} aria-invalid={mismatch} required />
        {mismatch && <span className="error-text">Die Passwörter stimmen nicht überein.</span>}
      </div>
      <div className="row-end">
        <button type="submit" className="btn btn-primary" disabled={busy || !newPw || mismatch || !repeat}>
          {busy ? 'Speichern …' : 'Passwort ändern'}
        </button>
      </div>
    </form>
  );
}

export default function ChangePasswordPage() {
  useTitle('Passwort ändern');
  const user = useUser();
  const { refresh, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <div className="login-wrap">
      <main className="card login-card">
        <h1>Neues Passwort festlegen</h1>
        {user.must_change_password ? (
          <p>Bitte legen Sie ein eigenes Passwort fest.</p>
        ) : null}
        <PasswordForm
          forced
          onDone={async () => {
            await refresh();
            navigate(homePath(user), { replace: true });
          }}
        />
        <div className="row-end" style={{ marginTop: 12 }}>
          <button type="button" className="btn btn-ghost" onClick={() => void logout()}>
            Abmelden
          </button>
        </div>
      </main>
    </div>
  );
}

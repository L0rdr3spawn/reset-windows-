/**
 * Gemeinsame Formularbausteine des Features „konto“ (§11.2).
 *
 * Passwort-Manager (Chrome/Google, Safari/iCloud-Schlüsselbund, Edge/Microsoft, Firefox): echte `<form>`-Elemente,
 * `autocomplete` = `username` / `new-password` / `current-password` / `one-time-code` / `email` / `tel`, und beim
 * Neusetzen ein Benutzername-Feld im selben Formular – so speichert der Manager das neue Passwort beim richtigen Konto.
 */
import { useId, useState, type FormEvent } from 'react';
import { errorMessage } from '../../api/client';
import { Icon } from '../../components/Icon';
import { PasswordInput } from '../../components/PasswordInput';
import { Alert } from '../../components/ui';
import { CODE_LENGTH, passwordIssues } from './logic';

/** Eingabefeld für einen 6-stelligen Code (SMS-Code-Vorschlag auf dem Handy über `one-time-code`). */
export function CodeInput({ id, value, onChange, label = 'Code', hint }: { id: string; value: string; onChange: (v: string) => void; label?: string; hint?: string }) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        name="one-time-code"
        className="ko-code-input"
        type="text"
        inputMode="numeric"
        autoComplete="one-time-code"
        pattern="[0-9 \-]*"
        maxLength={CODE_LENGTH + 2}
        required
        value={value}
        onChange={(e) => onChange(e.target.value.replace(/[^\d\s-]/g, ''))}
        aria-describedby={hint ? `${id}-hint` : undefined}
      />
      {hint && (
        <span className="hint" id={`${id}-hint`}>
          {hint}
        </span>
      )}
    </div>
  );
}

/**
 * Neues Passwort festlegen (mit Wiederholung und Regeln). `username` steht schreibgeschützt im Formular, damit
 * Passwort-Manager das neue Passwort dem richtigen Konto zuordnen.
 */
export function NewPasswordForm({
  username,
  minLength,
  onSubmit,
  submitLabel = 'Passwort speichern',
}: {
  username: string;
  minLength: number;
  onSubmit: (password: string) => Promise<void>;
  submitLabel?: string;
}) {
  const id = useId();
  const [pw, setPw] = useState('');
  const [repeat, setRepeat] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const issues = passwordIssues(pw, minLength, username);
  const mismatch = repeat.length > 0 && repeat !== pw;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (pw !== repeat) {
      setError('Die Passwörter stimmen nicht überein.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await onSubmit(pw);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="stack" onSubmit={submit} noValidate>
      {error && <Alert kind="error">{error}</Alert>}
      <div className="field">
        <label htmlFor={`${id}-user`}>Benutzername</label>
        <input id={`${id}-user`} name="username" type="text" autoComplete="username" value={username} readOnly className="ko-readonly" />
      </div>
      <div className="field">
        <label htmlFor={`${id}-pw`}>Neues Passwort</label>
        <PasswordInput
          id={`${id}-pw`}
          name="new-password"
          autoComplete="new-password"
          minLength={minLength}
          required
          value={pw}
          onChange={(e) => setPw(e.target.value)}
          aria-describedby={`${id}-rules`}
          autoFocus
        />
        <span className="hint" id={`${id}-rules`} aria-live="polite">
          {pw && issues.length ? `Noch nötig: ${issues.join(', ')}.` : pw ? 'Sieht gut aus.' : `Mindestens ${minLength} Zeichen, nicht leicht zu erraten, ohne Ihren Benutzernamen.`}
        </span>
      </div>
      <div className="field">
        <label htmlFor={`${id}-rep`}>Neues Passwort wiederholen</label>
        <PasswordInput
          id={`${id}-rep`}
          name="new-password-repeat"
          autoComplete="new-password"
          required
          value={repeat}
          onChange={(e) => setRepeat(e.target.value)}
          aria-invalid={mismatch}
        />
        {mismatch && <span className="error-text">Die Passwörter stimmen nicht überein.</span>}
      </div>
      <button type="submit" className="btn btn-primary w-100" disabled={busy || !pw || !repeat || mismatch || issues.length > 0}>
        <Icon name="key" /> {busy ? 'Speichern …' : submitLabel}
      </button>
    </form>
  );
}

/** Hinweis auf den Test-Postausgang (nur Entwicklung/Vorschau). */
export function DevOutboxHint() {
  return (
    <p className="small ko-dev-hint">
      <Icon name="info" /> Test-Umgebung: Nachrichten erscheinen im{' '}
      <a href="/test-postausgang" target="_blank" rel="noopener">
        Test-Postausgang
      </a>
      .
    </p>
  );
}

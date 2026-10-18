/**
 * Wiederverwendbare Bausteine der Zugangsbriefe (§11.3) – auch für Benutzerverwaltung und Klassen-Seite:
 * * `LetterBatchActions` – Knöpfe „Alle Briefe (PDF)“, „Einzelne PDFs (ZIP)“, „Zugangsdaten-Seite“.
 * * `PasswordPanel`/`PasswordDialog` – „Auf Startpasswort zurücksetzen“ bzw. „Neues Passwort selbst setzen“.
 */
import { useId, useState } from 'react';
import { Link } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { PasswordInput } from '../../components/PasswordInput';
import { HelpTip } from '../../components/HelpTip';
import { Alert, AsyncButton, ErrorBox, Field, Loading } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { formatDateTime } from '../../lib/dates';
import { lettersApi, passwordsApi } from './api';
import type { LetterBatchRef, PasswordResult } from './types';
import './zugangsdaten.css';

/** Download-/Seiten-Knöpfe zu einem Brief-Stapel. Bei nur einem Brief kein ZIP. */
export function LetterBatchActions({ batch, page = true, small = true }: { batch: LetterBatchRef; page?: boolean; small?: boolean }) {
  const cls = `btn${small ? ' btn-sm' : ''}`;
  const single = batch.count === 1;
  return (
    <span className="zd-actions">
      <a className={`${cls} btn-primary`} href={lettersApi.pdfUrl(batch.id)} download>
        <Icon name="download" /> {single ? 'Brief als PDF' : 'Alle Briefe (PDF)'}
      </a>
      {!single && (
        <a className={cls} href={lettersApi.zipUrl(batch.id)} download>
          <Icon name="download" /> Einzelne PDFs (ZIP)
        </a>
      )}
      {page && (
        <Link className={cls} to={`/zugangsdaten/${encodeURIComponent(batch.id)}`}>
          <Icon name="mail" /> Zugangsdaten-Seite{single ? '' : ' (E-Mail)'}
        </Link>
      )}
    </span>
  );
}

/**
 * Passwort eines Kontos zurücksetzen – für Verwaltung (users.manage) und Klassenleitungen (passwords.reset).
 * Alles beendet alle Sitzungen des Kontos. „Neues Einmalpasswort“ zeigt das Passwort **einmal** an (und als Brief-PDF);
 * Startpasswörter werden nicht aufbewahrt (nur Frist), ein altes lässt sich nicht wiederherstellen.
 */
export function PasswordPanel({
  userId,
  name,
  role,
  onDone,
}: {
  userId: number;
  name: string;
  /** für den Hinweis zur Mindestlänge (Schüler/innen 8, sonst 10 Zeichen) */
  role?: string;
  onDone?: (r: PasswordResult) => void;
}) {
  const info = useApi((signal) => passwordsApi.info(userId, signal), [userId]);
  const [result, setResult] = useState<PasswordResult | null>(null);
  const [pw, setPw] = useState('');
  const [mustChange, setMustChange] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pwId = useId();

  const done = (r: PasswordResult) => {
    setResult(r);
    setError(null);
    setPw('');
    onDone?.(r);
  };

  return (
    <div className="stack">
      {info.error ? <ErrorBox error={info.error} onRetry={info.reload} /> : null}
      {info.initialLoading && <Loading />}
      <div aria-live="polite">
        {result?.mode === 'new' && (
          <Alert kind="success" title="Neues Einmalpasswort erzeugt">
            <p style={{ margin: '0 0 8px' }}>
              Das Passwort wird nur jetzt angezeigt, drucken Sie am besten gleich den Brief:
              <HelpTip>Beim nächsten Anmelden muss ein eigenes Passwort festgelegt werden. Alle Sitzungen des Kontos wurden beendet.</HelpTip>
            </p>
            {result.temp_password && (
              <p style={{ margin: '0 0 8px' }}>
                <code className="mono" data-testid="temp-password" style={{ fontSize: '1.15em' }}>
                  {result.temp_password}
                </code>
              </p>
            )}
            {result.letter_batch && <LetterBatchActions batch={result.letter_batch} page={false} />}
          </Alert>
        )}
        {result?.mode === 'set' && (
          <Alert kind="success" title="Neues Passwort gesetzt">
            {result.must_change_password ? 'Beim nächsten Anmelden muss es geändert werden.' : 'Es gilt ab sofort.'} Alle Sitzungen des Kontos wurden beendet.
          </Alert>
        )}
        {error && (
          <Alert kind="error" title="Nicht möglich">
            {error}
          </Alert>
        )}
      </div>
      {info.data && (
        <>
          <section className="zd-section" aria-labelledby={`${pwId}-n`}>
            <h3 id={`${pwId}-n`}>
              Neues Einmalpasswort erzeugen
              <HelpTip>Erzeugt ein neues Einmalpasswort wie im Zugangsbrief und zeigt es einmal an, mit Brief zum Drucken (PDF). Beim nächsten Anmelden wird ein eigenes Passwort verlangt.</HelpTip>
            </h3>
            <AsyncButton
              className="btn btn-primary"
              confirm={`Neues Einmalpasswort für „${name}“ erzeugen? Das bisherige Passwort gilt dann nicht mehr, alle Sitzungen werden beendet.`}
              onClick={async () => {
                try {
                  done(await passwordsApi.resetToNew(userId));
                } catch (e) {
                  setError(errorMessage(e));
                }
              }}
            >
              <Icon name="key" /> Passwort zurücksetzen
            </AsyncButton>
          </section>
          <section className="zd-section" aria-labelledby={`${pwId}-a`}>
            <h3 id={`${pwId}-a`}>Startpasswort</h3>
            {info.data.initial_pending ? (
              <p className="small muted">
                {info.data.initial_expired ? 'Das Startpasswort ist abgelaufen' : 'Das Konto hat noch das Startpasswort aus dem Zugangsbrief'}
                {info.data.initial_expires_at ? ` (gültig bis ${formatDateTime(info.data.initial_expires_at)})` : ''}.
                <HelpTip>
                  {info.data.initial_expired ? 'Erzeugen Sie oben ein neues Einmalpasswort.' : 'Danach lässt es sich nicht mehr verwenden.'} Das Passwort selbst wird aus Sicherheitsgründen nicht aufbewahrt und lässt sich nicht erneut anzeigen.
                </HelpTip>
              </p>
            ) : (
              <p className="small muted">
                Das Konto hat kein offenes Startpasswort.
                <HelpTip>Das Passwort selbst wird nie aufbewahrt. Bei Bedarf erzeugen Sie oben ein neues Einmalpasswort.</HelpTip>
              </p>
            )}
          </section>
          <section className="zd-section" aria-labelledby={`${pwId}-b`}>
            <h3 id={`${pwId}-b`}>Neues Passwort selbst setzen</h3>
            <form
              className="stack-sm"
              onSubmit={async (e) => {
                e.preventDefault();
                try {
                  done(await passwordsApi.set(userId, pw, mustChange));
                } catch (err) {
                  setError(errorMessage(err));
                }
              }}
            >
              <Field label="Neues Passwort" htmlFor={pwId} hint={`mindestens ${role === 'schueler' ? 8 : 10} Zeichen, nicht der Benutzername`}>
                <PasswordInput id={pwId} autoComplete="new-password" value={pw} onChange={(e) => setPw(e.target.value)} />
              </Field>
              <label className="check">
                <input type="checkbox" checked={mustChange} onChange={(e) => setMustChange(e.target.checked)} /> beim nächsten Anmelden ändern
              </label>
              <div>
                <button type="submit" className="btn btn-primary" disabled={pw.length < 1}>
                  <Icon name="key" /> Passwort setzen
                </button>
              </div>
            </form>
          </section>
        </>
      )}
    </div>
  );
}

/** {@link PasswordPanel} als Dialog (Klassen-Seite). In anderen Dialogen das Panel direkt einbetten. */
export function PasswordDialog({
  userId,
  name,
  role,
  onClose,
  onDone,
}: {
  userId: number;
  name: string;
  role?: string;
  onClose: () => void;
  onDone?: (r: PasswordResult) => void;
}) {
  return (
    <Modal
      title={`Passwort: ${name}`}
      onClose={onClose}
      footer={
        <button type="button" className="btn" onClick={onClose}>
          Schließen
        </button>
      }
    >
      <PasswordPanel userId={userId} name={name} role={role} onDone={onDone} />
    </Modal>
  );
}

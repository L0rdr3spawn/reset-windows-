/**
 * `/lizenz` – Lizenz der Schule (Recht `license.manage`: Administration, Schulleitung): Schule, dieser Server (Bezeichnung,
 * Schlüssel nur mit den letzten 4 Zeichen), Abo aktiv bis, Konten, letzte Prüfung beim Anbieter, „bestätigt bis“ und die
 * anderen Server der Schule; Aktionen „Jetzt prüfen“ und „Schlüssel ändern“. Die Seite ist auch bei gesperrter Lizenz
 * erreichbar (`pages/LicenseLockedPage.tsx` bettet sie dann mit `embedded` ein); nach dem Eintragen aktiviert der Server den
 * Schlüssel sofort beim Lizenzserver, das Konto wird neu geladen und die Sperre fällt (`onInstalled`: die Begrüßungsseite
 * einer frischen Instanz springt danach in den Einrichtungsassistenten).
 */
import { useState } from 'react';
import { http } from '../api/client';
import { HelpTip } from '../components/HelpTip';
import { Icon } from '../components/Icon';
import { Alert, AsyncButton, ErrorBox, Loading } from '../components/ui';
import { useToast } from '../context/ToastContext';
import { useAuth } from '../context/AuthContext';
import { useApi } from '../hooks/useApi';
import { useTitle } from '../hooks/misc';
import { formatDate, formatDateTime } from '../lib/dates';
import { PROVIDER_STATUS, SERVER_STATE, stateLabel } from '../lib/license';

interface ServerEntry {
  label: string;
  key_last4: string;
  state: string;
  url?: string | null;
  version?: string | null;
  last_check_at?: string | null;
}

interface LicenseStatus {
  state: 'valid' | 'grace' | 'locked';
  stage?: string;
  reason?: string;
  enforced: boolean;
  read_only: boolean;
  locked?: boolean;
  message: string;
  warning: string;
  days_left?: number | null;
  grace_until?: string | null;
  licensee?: string | null;
  valid_until?: string | null;
  key_last4?: string | null;
  server_label?: string | null;
  group_id?: string | null;
  servers?: ServerEntry[] | null;
  servers_booked?: number | null;
  max_users?: number | null;
  max_students?: number | null;
  counts?: { students: number | null; users: number | null };
  confirmed_until?: string | null;
  last_ok_at?: string | null;
  last_status?: string | null;
  last_attempt_at?: string | null;
  last_error?: string | null;
  instance_id?: string;
  base_url?: string;
}

export default function LicensePage({ embedded = false, onInstalled }: { embedded?: boolean; onInstalled?: (st: { state: string; locked?: boolean }) => void }) {
  useTitle('Lizenz');
  const toast = useToast();
  const { refresh } = useAuth();
  const q = useApi((signal) => http.get<LicenseStatus>('/license', undefined, { signal }), []);
  const [key, setKey] = useState('');
  const [changing, setChanging] = useState(false);
  const st = q.data;
  const hasKey = !!st?.key_last4;
  const showForm = !hasKey || changing;
  const apply = async (next: LicenseStatus, installed = false) => {
    q.setData(next);
    if (installed && !next.locked && onInstalled) onInstalled(next);
    else await refresh(); // Konto neu laden: Sperrseite bzw. Hinweis-Balken passen sich sofort an
  };
  const [label, cls] = stateLabel(st?.state);
  return (
    <div className={embedded ? 'stack' : 'page page-narrow stack'}>
      {!embedded && (
        <div className="page-head">
          <h1>
            Lizenz{' '}
            <HelpTip>
              Ihre Lizenz gehört zu einem Lizenzschlüssel, den Sie vom Anbieter erhalten haben. Dieser Server fragt täglich beim Anbieter nach (zusätzlich kurz alle 15 Minuten); ist der Anbieter einmal nicht
              erreichbar, läuft alles weiter, solange die letzte Bestätigung gilt. Läuft das Abo aus oder wird es pausiert, gibt es eine Kulanzzeit, in der alles nur lesbar ist, danach ist die Anwendung gesperrt.
              Mit einem gültigen Schlüssel geht es sofort weiter.
            </HelpTip>
          </h1>
        </div>
      )}
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!st && !q.error && <Loading />}
      {st && hasKey && (
        <section className="card stack-sm" aria-labelledby="lz-h">
          <div className="row-between">
            <h2 id="lz-h" style={{ margin: 0 }}>
              {st.licensee ?? 'Lizenz'}
            </h2>
            <span className={`badge ${cls}`}>{label}</span>
          </div>
          {st.message && <Alert kind={st.locked ? 'error' : st.read_only ? 'warning' : 'info'}>{st.message}</Alert>}
          {st.warning && <Alert kind="warning">{st.warning}</Alert>}
          {!st.enforced && <p className="small muted">Die Lizenzprüfung ist für diese Installation nicht verpflichtend (Test-/Entwicklungsbetrieb).</p>}
          <dl className="kv">
            <dt>Schule</dt>
            <dd>{st.licensee ?? '–'}</dd>
            <dt>Dieser Server</dt>
            <dd>
              {st.server_label ?? '–'} <span className="muted mono">· Schlüssel …{st.key_last4}</span>
            </dd>
            <dt>Abo aktiv bis</dt>
            <dd>
              {st.valid_until ? formatDate(st.valid_until) : 'unbegrenzt'}
              {typeof st.days_left === 'number' && st.days_left >= 0 ? <span className="muted"> · noch {st.days_left} Tag(e)</span> : null}
            </dd>
            <dt>Aktive Konten</dt>
            <dd>
              {st.counts?.users ?? '–'} {st.max_users ? `von ${st.max_users} erlaubt` : '(unbegrenzt)'}
            </dd>
            <dt>Schüler/innen</dt>
            <dd>
              {st.counts?.students ?? '–'} {st.max_students ? `von ${st.max_students} erlaubt` : '(unbegrenzt)'}
            </dd>
            <dt>
              Letzte Prüfung{' '}
              <HelpTip>Dieser Server fragt täglich beim Anbieter nach. Die Bestätigung gilt einige Tage; erreicht der Server den Anbieter länger nicht, beginnt eine Kulanzzeit, danach ist die Anwendung gesperrt.</HelpTip>
            </dt>
            <dd>
              {st.last_ok_at ? formatDateTime(st.last_ok_at) : 'noch nie'}
              {st.last_status ? <span className="muted"> · {PROVIDER_STATUS[st.last_status] ?? st.last_status}</span> : null}
              {st.last_error ? (
                <span className="small" style={{ color: 'var(--danger)' }}>
                  {' '}
                  · {st.last_error}
                </span>
              ) : null}
            </dd>
            <dt>Bestätigt bis</dt>
            <dd>{st.confirmed_until ? formatDateTime(st.confirmed_until) : '–'}</dd>
            <dt>Adresse dieses Servers</dt>
            <dd className="small">{st.base_url ?? '–'}</dd>
          </dl>
          <div className="row" style={{ gap: 'var(--space-2)', flexWrap: 'wrap' }}>
            <AsyncButton
              className="btn"
              onClick={async () => {
                try {
                  await apply(await http.post<LicenseStatus>('/license/check', {}));
                  toast.success('Lizenz geprüft');
                } catch (e) {
                  toast.error(e, 'Lizenz');
                }
              }}
            >
              <Icon name="refresh" /> Jetzt prüfen
            </AsyncButton>
            {!changing && (
              <button type="button" className="btn" onClick={() => setChanging(true)}>
                <Icon name="edit" /> Schlüssel ändern
              </button>
            )}
          </div>
        </section>
      )}
      {st && hasKey && st.servers && st.servers.length > 0 && (
        <section className="card stack-sm" aria-labelledby="lz-srv">
          <h2 id="lz-srv" style={{ margin: 0 }}>
            Weitere Server dieser Schule{' '}
            <HelpTip>Eine Schule kann mehrere Server haben, jeder mit eigenem Schlüssel. Hier sehen Sie, ob die anderen Server beim Anbieter angemeldet sind.</HelpTip>
          </h2>
          <div className="table-wrap">
            <table className="table table-compact">
              <thead>
                <tr>
                  <th>Server</th>
                  <th>Status</th>
                  <th>Adresse</th>
                  <th>Version</th>
                  <th>Letzte Prüfung</th>
                </tr>
              </thead>
              <tbody>
                {st.servers.map((s) => {
                  const [text, badge] = SERVER_STATE[s.state] ?? [s.state, 'badge'];
                  return (
                    <tr key={s.key_last4}>
                      <td>
                        {s.label} <span className="muted mono small">…{s.key_last4}</span>
                      </td>
                      <td>
                        <span className={`badge ${badge}`}>{text}</span>
                      </td>
                      <td className="small">{s.url ?? '–'}</td>
                      <td>{s.version ?? '–'}</td>
                      <td>{s.last_check_at ? formatDateTime(s.last_check_at) : '–'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}
      {st && showForm && (
        <section className="card stack-sm" aria-labelledby="lz-new">
          <h2 id="lz-new" style={{ margin: 0 }}>
            {hasKey ? 'Schlüssel ändern' : 'Lizenzschlüssel eintragen'}{' '}
            <HelpTip>
              Den Schlüssel haben Sie vom Anbieter erhalten (Aufbau SPUL-XXXX-XXXX-XXXX-XXXX). Beim Eintragen wird er an diesen Server gebunden; ein zweiter Server mit demselben Schlüssel wird abgelehnt. Bei einem
              Serverumzug bitten Sie den Anbieter, die Bindung zu lösen.
            </HelpTip>
          </h2>
          <label className="stack-xs">
            <span className="small muted">Lizenzschlüssel</span>
            <input
              type="text"
              className="mono"
              value={key}
              onChange={(e) => setKey(e.target.value.toUpperCase())}
              placeholder="SPUL-XXXX-XXXX-XXXX-XXXX"
              autoComplete="off"
              autoCapitalize="characters"
              spellCheck={false}
              maxLength={40}
              aria-label="Lizenzschlüssel"
            />
          </label>
          <div className="row" style={{ gap: 'var(--space-2)' }}>
            <AsyncButton
              className="btn btn-primary"
              disabled={key.trim().length < 10}
              onClick={async () => {
                try {
                  await apply(await http.put<LicenseStatus>('/license', { key }), true);
                  setKey('');
                  setChanging(false);
                  toast.success('Lizenz aktiviert');
                } catch (e) {
                  toast.error(e, 'Lizenz');
                }
              }}
            >
              <Icon name="check" /> Aktivieren
            </AsyncButton>
            {changing && (
              <button type="button" className="btn btn-ghost" onClick={() => setChanging(false)}>
                Abbrechen
              </button>
            )}
          </div>
        </section>
      )}
    </div>
  );
}

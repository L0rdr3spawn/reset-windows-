import { useState } from 'react';
import { admin } from '../api/endpoints';
import type { BackupInfo } from '../api/types';
import { HelpTip } from '../components/HelpTip';
import { Icon } from '../components/Icon';
import { Alert, AsyncButton, ErrorBox, Field, Loading } from '../components/ui';
import { useToast } from '../context/ToastContext';
import { useApi } from '../hooks/useApi';
import { invalidateAll } from '../hooks/useCollection';
import { useTitle } from '../hooks/misc';
import { formatDateTime } from '../lib/dates';
import { formatBytes } from '../lib/format';

function renderValue(v: unknown): string {
  if (v === null || v === undefined) return '–';
  if (typeof v === 'boolean') return v ? 'ja' : 'nein';
  if (typeof v === 'object') return JSON.stringify(v);
  return String(v);
}

const MAINTENANCE_LABELS: Record<string, string> = {
  sessions: 'abgelaufene Sitzungen',
  api_tokens: 'abgelaufene API-Tokens',
  login_attempts: 'alte Anmeldeversuche',
  files_orphaned: 'nicht verwendete Uploads',
  files_purged: 'gelöschte Dateien endgültig entfernt',
  file_blobs_removed: 'Dateiinhalte entfernt',
  file_blobs_gc: 'verwaiste Dateiinhalte',
  student_documents: 'abgelaufene Atteste/Dokumente',
};

/** „3 abgelaufene Sitzungen, 1 nicht verwendeter Upload …“ bzw. „nichts zu bereinigen“ */
function maintenanceText(v: unknown): string {
  if (!v || typeof v !== 'object') return renderValue(v);
  const parts = Object.entries(v as Record<string, unknown>)
    .filter(([, n]) => typeof n === 'number' && n > 0)
    .map(([k, n]) => `${n} ${MAINTENANCE_LABELS[k] ?? k}`);
  return parts.length ? parts.join(', ') : 'nichts zu bereinigen';
}

const LABELS: Record<string, string> = {
  version: 'Version',
  python: 'Python',
  db: 'Datenbank',
  db_revision: 'Schema-Revision',
  users: 'Benutzerkonten',
  active_sessions: 'aktive Sitzungen',
  versions: 'gespeicherte Versionen',
  plan_version: 'aktuelle Planversion',
  plan_updated_at: 'zuletzt geändert',
  school_name: 'Schule',
  uptime_seconds: 'Laufzeit (s)',
  sse_clients: 'Live-Verbindungen',
  backups: 'Sicherungen',
};

export default function AdminPage() {
  useTitle('System');
  const toast = useToast();
  const sys = useApi(() => admin.system(), []);
  const backups = useApi<BackupInfo[]>(() => admin.backups(), []);
  const [demoTime, setDemoTime] = useState(20);
  const [demoClasses, setDemoClasses] = useState(14);
  const [demoAccounts, setDemoAccounts] = useState(true);
  const [demoResult, setDemoResult] = useState<{ username: string; password?: string; role?: string }[] | null>(null);

  const s = sys.data ?? {};
  const counts = (s.counts ?? null) as Record<string, number> | null;
  const byRole = (s.users_by_role ?? null) as Record<string, number> | null;
  const cfg = (s.config ?? null) as Record<string, unknown> | null;

  return (
    <div className="page stack">
      <div className="page-head">
        <h1>System</h1>
        <button type="button" className="btn btn-sm" onClick={sys.reload}>
          <Icon name="refresh" /> Aktualisieren
        </button>
      </div>
      {sys.error ? <ErrorBox error={sys.error} onRetry={sys.reload} /> : null}
      {sys.initialLoading && <Loading />}
      {sys.data && (
        <div className="grid grid-2">
          <section className="card">
            <h2>Systeminformationen</h2>
            <dl className="kv small">
              {Object.entries(s)
                .filter(([, v]) => typeof v !== 'object' || v === null)
                .map(([k, v]) => (
                  <div key={k} style={{ display: 'contents' }}>
                    <dt>{LABELS[k] ?? k}</dt>
                    <dd>{k.endsWith('_at') ? formatDateTime(String(v)) : renderValue(v)}</dd>
                  </div>
                ))}
            </dl>
          </section>
          <section className="card">
            <h2>Daten</h2>
            {counts && (
              <dl className="kv small">
                {Object.entries(counts).map(([k, v]) => (
                  <div key={k} style={{ display: 'contents' }}>
                    <dt>{k}</dt>
                    <dd>{v}</dd>
                  </div>
                ))}
              </dl>
            )}
            {byRole && (
              <>
                <h3 style={{ marginTop: 12 }}>Konten je Rolle</h3>
                <dl className="kv small">
                  {Object.entries(byRole).map(([k, v]) => (
                    <div key={k} style={{ display: 'contents' }}>
                      <dt>{k}</dt>
                      <dd>{v}</dd>
                    </div>
                  ))}
                </dl>
              </>
            )}
            <div style={{ marginTop: 12 }}>
              <AsyncButton
                className="btn btn-sm"
                onClick={async () => {
                  try {
                    const r = await admin.maintenance();
                    toast.success(`Wartung ausgeführt: ${maintenanceText(r.deleted)}`);
                  } catch (e) {
                    toast.error(e);
                  }
                }}
              >
                Wartung jetzt ausführen
              </AsyncButton>
            </div>
          </section>
          {cfg && (
            <section className="card">
              <details className="disclosure">
                <summary>Konfiguration (ohne Geheimnisse)</summary>
                <dl className="kv small">
                  {Object.entries(cfg).map(([k, v]) => (
                    <div key={k} style={{ display: 'contents' }}>
                      <dt className="mono">{k}</dt>
                      <dd className="mono">{renderValue(v)}</dd>
                    </div>
                  ))}
                </dl>
              </details>
            </section>
          )}
        </div>
      )}

      <section className="card">
        <div className="card-head">
          <h2>
            Sicherungen
            <HelpTip>Datenbank-Dumps (PostgreSQL) erstellt zusätzlich der Backup-Dienst des Servers, siehe Betriebsdokumentation.</HelpTip>
          </h2>
          <AsyncButton
            className="btn btn-primary"
            onClick={async () => {
              try {
                const b = await admin.createBackup();
                toast.success(`Sicherung ${b.name ?? ''} erstellt`);
                backups.reload();
              } catch (e) {
                toast.error(e, 'Sicherung');
              }
            }}
          >
            <Icon name="plus" /> Sicherung erstellen
          </AsyncButton>
        </div>
        {backups.error ? <ErrorBox error={backups.error} onRetry={backups.reload} /> : null}
        {backups.data && backups.data.length === 0 && <p className="muted small">Noch keine Sicherungen.</p>}
        {backups.data && backups.data.length > 0 && (
          <div className="table-wrap">
            <table className="table table-compact">
              <thead>
                <tr>
                  <th scope="col">Datei</th>
                  <th scope="col">Erstellt</th>
                  <th scope="col" className="num">
                    Größe
                  </th>
                  <th scope="col">
                    <span className="sr-only">Aktionen</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {backups.data.map((b) => (
                  <tr key={b.name}>
                    <td className="mono small">{b.name}</td>
                    <td>{formatDateTime(b.created_at)}</td>
                    <td className="num">{formatBytes(b.size)}</td>
                    <td className="actions">
                      <a className="btn btn-sm" href={admin.backupUrl(b.name)} download>
                        <Icon name="download" /> Laden
                      </a>
                      <AsyncButton
                        className="btn btn-ghost btn-sm"
                        confirm={`Sicherung ${b.name} löschen?`}
                        onClick={async () => {
                          try {
                            await admin.deleteBackup(b.name);
                            backups.reload();
                          } catch (e) {
                            toast.error(e);
                          }
                        }}
                      >
                        <Icon name="trash" />
                        <span className="sr-only">löschen</span>
                      </AsyncButton>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {cfg?.mode !== 'production' && (
        <section className="card">
          <h2>
            Demo-Schule laden
            <HelpTip>
              Enthält etwa 2600 Schüler/innen, 2 Standorte, Rhythmus-Beispiele für Berufsschulklassen und Lehrkräfte sowie einen berechneten Stundenplan. Die Dauer entspricht ungefähr der eingestellten Rechenzeit.
            </HelpTip>
          </h2>
          <Alert kind="warning">Ersetzt alle Planungsdaten. Rückgängig über „Verlauf“ möglich.</Alert>
          <div className="form-grid">
            <Field label="Rechenzeit (s)" htmlFor="demo-time">
              <input id="demo-time" type="number" min={5} max={600} value={demoTime} onChange={(e) => setDemoTime(Number(e.target.value))} />
            </Field>
            <Field label="Klassen je Jahrgang" htmlFor="demo-cls">
              <input id="demo-cls" type="number" min={1} max={23} value={demoClasses} onChange={(e) => setDemoClasses(Number(e.target.value))} />
            </Field>
            <div className="field">
              <span className="field-label">Demo-Konten</span>
              <label className="check">
                <input type="checkbox" checked={demoAccounts} onChange={(e) => setDemoAccounts(e.target.checked)} /> anlegen
              </label>
            </div>
          </div>
          <div className="row" style={{ marginTop: 12 }}>
            <AsyncButton
              className="btn btn-danger"
              confirm="Wirklich alle Planungsdaten durch die Demo-Schule ersetzen?"
              onClick={async () => {
                try {
                  const r = await admin.loadDemo({ time_limit: demoTime, classes_per_grade: demoClasses, accounts: demoAccounts });
                  setDemoResult(r.accounts ?? []);
                  invalidateAll();
                  toast.success('Demo-Schule geladen');
                  sys.reload();
                } catch (e) {
                  toast.error(e, 'Demo');
                }
              }}
            >
              <Icon name="sparkles" /> Demo laden
            </AsyncButton>
          </div>
          {demoResult && demoResult.length > 0 && (
            <div className="table-wrap" style={{ marginTop: 12 }}>
              <table className="table table-compact">
                <thead>
                  <tr>
                    <th scope="col">Benutzer</th>
                    <th scope="col">Rolle</th>
                    <th scope="col">Passwort</th>
                  </tr>
                </thead>
                <tbody>
                  {demoResult.map((a) => (
                    <tr key={a.username}>
                      <td className="mono">{a.username}</td>
                      <td>{a.role ?? ''}</td>
                      <td className="mono">{a.password ?? '(unverändert)'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </div>
  );
}

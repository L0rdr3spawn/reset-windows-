/**
 * `/betrieb` – Status und Betrieb für die Administration: Prüfliste (Datenbank, Schema, Speicher, Sicherung, Mail,
 * Verschlüsselung, Lizenz, Wartung), Zahlen, Sicherungen mit Test-Restore und das Fehlerprotokoll.
 * Daten: `GET /admin/status`, `GET/DELETE /admin/errors`, `GET/POST /admin/backups`, `POST /admin/backups/{n}/verify`.
 */
import { useState } from 'react';
import { http } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { AsyncButton, ErrorBox, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useTitle } from '../../hooks/misc';
import { formatDateTime } from '../../lib/dates';
import { formatBytes } from '../../lib/format';
import { UpdatesCard } from './UpdatesCard';
import {
  LEVEL_BADGE,
  LEVEL_TEXT,
  MODE_LABELS,
  ageText,
  summary,
  uptimeText,
  verifyText,
  type BackupItem,
  type ErrorEntry,
  type Status,
  type VerifyResult,
} from './logic';

function Kv({ rows }: { rows: [string, React.ReactNode][] }) {
  return (
    <dl className="kv small">
      {rows.map(([k, v]) => (
        <div key={k} style={{ display: 'contents' }}>
          <dt>{k}</dt>
          <dd>{v}</dd>
        </div>
      ))}
    </dl>
  );
}

function Backups({ status, reloadStatus }: { status: Status; reloadStatus: () => void }) {
  const toast = useToast();
  const list = useApi(() => http.get<BackupItem[]>('/admin/backups'), []);
  const [results, setResults] = useState<Record<string, VerifyResult>>({});
  return (
    <section className="card stack-sm">
      <div className="card-head">
        <h2>
          Sicherungen{' '}
          <HelpTip>
            App-Sicherungen liegen im Datenverzeichnis. Zusätzlich sichert der Backup-Dienst der Installation täglich die Datenbank und die Dateien (siehe Betriebshandbuch, Abschnitt Backup und Restore). „Prüfen“ spielt die Sicherung in eine Wegwerf-Kopie ein und kontrolliert sie – die Live-Daten bleiben unberührt. Machen Sie das regelmäßig, mindestens monatlich.
          </HelpTip>
        </h2>
        <AsyncButton
          className="btn btn-primary"
          onClick={async () => {
            const b = await http.post<{ name: string }>('/admin/backups');
            toast.success(`Sicherung ${b.name} erstellt`);
            list.reload();
            reloadStatus();
          }}
        >
          <Icon name="plus" /> Sicherung erstellen
        </AsyncButton>
      </div>
      <p className="small muted" style={{ margin: 0 }}>
        Letzte Sicherung: {ageText(status.backup.last?.created_at)} · {status.backup.count} gespeichert (behalten werden {status.backup.keep})
        {status.backup.auto_hours > 0 ? ` · automatisch alle ${status.backup.auto_hours} Std.` : ''}
      </p>
      {list.error ? <ErrorBox error={list.error} onRetry={list.reload} /> : null}
      {list.data && list.data.length === 0 && <p className="muted small">Noch keine Sicherungen.</p>}
      {list.data && list.data.length > 0 && (
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
              {list.data.slice(0, 10).map((b) => (
                <tr key={b.name}>
                  <td className="mono small">
                    {b.name}
                    {results[b.name] && (
                      <div className={results[b.name].ok ? 'small' : 'error-text'} role="status">
                        <Icon name={results[b.name].ok ? 'check' : 'alert'} /> {verifyText(results[b.name])}
                      </div>
                    )}
                  </td>
                  <td>{formatDateTime(b.created_at)}</td>
                  <td className="num">{formatBytes(b.size)}</td>
                  <td className="actions">
                    <AsyncButton
                      className="btn btn-sm"
                      onClick={async () => {
                        const r = await http.post<VerifyResult>(`/admin/backups/${encodeURIComponent(b.name)}/verify`);
                        setResults((x) => ({ ...x, [b.name]: r }));
                      }}
                    >
                      <Icon name="shield" /> Prüfen
                    </AsyncButton>
                    <a className="btn btn-sm" href={`/api/v1/admin/backups/${encodeURIComponent(b.name)}`} download>
                      <Icon name="download" /> Laden
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function ErrorLog({ onChanged }: { onChanged: () => void }) {
  const toast = useToast();
  const [level, setLevel] = useState('');
  const q = useApi(
    (signal) => http.get<{ total: number; items: ErrorEntry[] }>('/admin/errors', { limit: 50, level: level || undefined }, { signal }),
    [level],
  );
  return (
    <section className="card stack-sm">
      <div className="card-head">
        <h2>
          Fehlerprotokoll{' '}
          <HelpTip>Hier stehen unerwartete Fehler der Anwendung der letzten 30 Tage (höchstens 1000). Die Fehlernummer erscheint auch in der Meldung, die Nutzer/innen sehen. Der Server speichert hier keine Passwörter oder Nachrichteninhalte.</HelpTip>
        </h2>
        <div className="row" style={{ gap: 8 }}>
          <select aria-label="Stufe filtern" value={level} onChange={(e) => setLevel(e.target.value)}>
            <option value="">alle Stufen</option>
            <option value="ERROR">Fehler</option>
            <option value="CRITICAL">kritisch</option>
          </select>
          <button type="button" className="btn btn-sm" onClick={q.reload}>
            <Icon name="refresh" /> Aktualisieren
          </button>
          <AsyncButton
            className="btn btn-ghost btn-sm"
            disabled={!q.data?.total}
            confirm="Das gesamte Fehlerprotokoll leeren?"
            onClick={async () => {
              const r = await http.del<{ removed: number }>('/admin/errors');
              toast.success(`${r.removed} Einträge gelöscht`);
              q.reload();
              onChanged();
            }}
          >
            <Icon name="trash" /> Leeren
          </AsyncButton>
        </div>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.data && q.data.items.length === 0 && <p className="muted small">Keine Fehler protokolliert.</p>}
      {q.data && q.data.items.length > 0 && (
        <ul className="list-plain stack-sm" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {q.data.items.map((e) => (
            <li key={e.id} className="card card-flat">
              <div className="row-between small" style={{ gap: 8, flexWrap: 'wrap' }}>
                <span>
                  <span className={`badge ${e.level === 'CRITICAL' ? 'badge-danger' : 'badge-warning'}`}>{e.level === 'CRITICAL' ? 'kritisch' : 'Fehler'}</span>{' '}
                  {formatDateTime(e.created_at)}
                </span>
                <span className="mono muted">{e.request_id ? `Nr. ${e.request_id}` : e.logger}</span>
              </div>
              <div style={{ overflowWrap: 'anywhere' }}>{e.message}</div>
              {e.trace && (
                <details className="disclosure">
                  <summary>Technische Details</summary>
                  <pre className="mono xsmall" style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{e.trace}</pre>
                </details>
              )}
            </li>
          ))}
        </ul>
      )}
      {q.data && q.data.total > q.data.items.length && <p className="xsmall muted">Angezeigt: die neuesten {q.data.items.length} von {q.data.total}.</p>}
    </section>
  );
}

export default function BetriebPage() {
  useTitle('Betrieb und Status');
  const toast = useToast();
  const q = useApi((signal) => http.get<Status>('/admin/status', undefined, { signal }), []);
  const s = q.data;
  const sum = s ? summary(s.checks) : null;
  return (
    <div className="page stack">
      <div className="page-head">
        <h1>
          Betrieb und Status{' '}
          <HelpTip>Zustand dieser Installation auf einen Blick. Hinweise sind keine Störung, sondern Empfehlungen für den sicheren Betrieb. Anleitungen zu Sicherung, Update und Wiederherstellung: Betriebshandbuch (docs/BETRIEB.md).</HelpTip>
        </h1>
        <div className="row" style={{ gap: 8 }}>
          {s && <span className="badge">{MODE_LABELS[s.mode]}</span>}
          {sum && <span className={`badge ${LEVEL_BADGE[sum.level]}`}>{sum.text}</span>}
          <button type="button" className="btn btn-sm" onClick={q.reload}>
            <Icon name="refresh" /> Aktualisieren
          </button>
        </div>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {s && (
        <>
          <section className="card stack-sm" aria-label="Prüfliste">
            <h2>Prüfliste</h2>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }} className="stack-sm">
              {s.checks.map((c) => (
                <li key={c.key} className="row" style={{ gap: 8, alignItems: 'baseline', flexWrap: 'wrap' }}>
                  <span className={`badge ${LEVEL_BADGE[c.level]}`}>{LEVEL_TEXT[c.level]}</span>
                  <strong>{c.label}</strong>
                  <span className="small muted">{c.detail}</span>
                </li>
              ))}
            </ul>
          </section>

          <div className="grid grid-2">
            <section className="card">
              <h2>System</h2>
              <Kv
                rows={[
                  ['Version', s.version],
                  ['Betriebsmodus', MODE_LABELS[s.mode]],
                  ['Schule', s.school_name],
                  ['Laufzeit', uptimeText(s.uptime_seconds)],
                  ['Datenbank', s.database.kind === 'postgresql' ? 'PostgreSQL' : 'SQLite'],
                  ['Datenbankstand', <span className="mono" key="rev">{s.database.revision ?? '–'}</span>],
                  ['Schema aktuell', s.database.up_to_date ? 'ja' : 'nein – Migration ausführen'],
                ]}
              />
            </section>
            <section className="card">
              <h2>Speicher</h2>
              <Kv
                rows={[
                  ['Freier Platz', s.storage.disk.free != null ? `${formatBytes(s.storage.disk.free)} von ${formatBytes(s.storage.disk.total)} (${s.storage.disk.free_percent} %)` : '–'],
                  ['Datenbankdatei', s.database.file_bytes != null ? formatBytes(s.database.file_bytes) : 'extern (PostgreSQL)'],
                  ['Hochgeladene Dateien', formatBytes(s.storage.files_bytes)],
                  ['App-Sicherungen', formatBytes(s.storage.backups_bytes)],
                  ['Datenverzeichnis', <span className="mono" key="dir">{s.storage.data_dir}</span>],
                ]}
              />
            </section>
            <section className="card">
              <h2>E-Mail</h2>
              <Kv
                rows={[
                  ['Versand', s.mail.dev_outbox ? 'Test-Postausgang (keine Zustellung)' : s.mail.smtp ? 'eingerichtet' : 'nicht eingerichtet'],
                  ['Warteschlange', `${s.mail.pending} wartend`],
                  ['Nicht zustellbar', s.mail.failed],
                  ['Zuletzt gesendet', s.mail.last_sent ? formatDateTime(s.mail.last_sent) : '–'],
                ]}
              />
            </section>
            <section className="card">
              <h2>
                Verschlüsselung{' '}
                <HelpTip>Nachrichten, Atteste und Dateien sind mit diesem Schlüsselring verschlüsselt. Bewahren Sie die Schlüssel getrennt von den Sicherungen auf (Passwort-Tresor und Ausdruck im Safe) – ohne sie sind verschlüsselte Inhalte nach einer Wiederherstellung unlesbar. Angezeigt werden nur Namen und Fingerabdrücke.</HelpTip>
              </h2>
              <Kv
                rows={[
                  ['Aktiver Schlüssel', <span className="mono" key="a">{s.encryption.active}</span>],
                  ...s.encryption.keys.map((k): [string, React.ReactNode] => [`Schlüssel ${k.id}`, <span className="mono" key={k.id}>{k.fingerprint}</span>]),
                ]}
              />
            </section>
            <section className="card stack-sm">
              <h2>Wartung</h2>
              <Kv
                rows={[
                  ['Letzter Lauf', s.maintenance.last ? `${formatDateTime(s.maintenance.last)} (${ageText(s.maintenance.last)})` : 'noch nicht gelaufen'],
                  ['Rhythmus', s.maintenance.interval_seconds > 0 ? `alle ${Math.round(s.maintenance.interval_seconds / 60)} Min.` : 'aus'],
                  ['Fehler (24 Std.)', s.errors.last_24h],
                ]}
              />
              <div>
                <AsyncButton
                  className="btn btn-sm"
                  onClick={async () => {
                    await http.post('/admin/maintenance');
                    toast.success('Wartung ausgeführt');
                    q.reload();
                  }}
                >
                  Wartung jetzt ausführen
                </AsyncButton>
              </div>
            </section>
          </div>

          <UpdatesCard />
          <Backups status={s} reloadStatus={q.reload} />
          <ErrorLog onChanged={q.reload} />
        </>
      )}
    </div>
  );
}

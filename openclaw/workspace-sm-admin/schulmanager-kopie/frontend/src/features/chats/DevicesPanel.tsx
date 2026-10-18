/**
 * „Geräte & Schlüssel“ der Chats: Geräteübersicht, Verlauf auf ein neues Gerät übertragen (Code/QR + Fingerabdruck),
 * Wiederherstellung mit Passwort (optional) und neue Schlüssel erzeugen. Die Kryptografie steht in `keys.ts`;
 * der Server sieht nur verpackte Schlüssel (siehe docs/SICHERHEIT.md, Abschnitt Chats).
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { errorMessage } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { QrCode } from '../../components/QrCode';
import { Alert, AsyncButton, CopyField, ErrorBox, ProgressBar, Tabs } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { formatDateTime } from '../../lib/dates';
import { chatsApi, type DeviceInfo, type LinkInfo } from './api';
import { fingerprint, forgetDevice, type LocalDevice } from './crypto';
import {
  changeBackupSecret,
  enableBackup,
  formatLinkCode,
  generateRecoveryCode,
  linkUrl,
  parseLinkCode,
  passwordProblem,
  rekeyThisDevice,
  resetAllDevices,
  restoreFromBackup,
  sendHistory,
} from './keys';

export type DevicesTab = 'geraete' | 'verlauf' | 'backup' | 'schluessel';

const isAbort = (e: unknown) => e instanceof DOMException && e.name === 'AbortError';

function Fingerprint({ publicKey }: { publicKey: string }) {
  return <code className="mono ch-fp">{fingerprint(publicKey)}</code>;
}

/** Fortschritt einer laufenden Übertragung. */
interface Run {
  processed: number;
  total: number;
}

function RunBar({ run, label }: { run: Run; label: string }) {
  return <ProgressBar value={run.total > 0 ? run.processed / run.total : 0} label={`${label} (${run.processed}${run.total ? ` von ${run.total}` : ''})`} />;
}

// ---------------------------------------------------------------------------------------------- Geräte
function DevicesTabView({ device, onTransfer }: { device: LocalDevice; onTransfer: () => void }) {
  const toast = useToast();
  const q = useApi((signal) => chatsApi.myDevices(signal), [], { live: ['chats'] });
  const [run, setRun] = useState<{ id: number; r: Run } | null>(null);
  const abort = useRef<AbortController | null>(null);

  const send = async (d: DeviceInfo) => {
    abort.current = new AbortController();
    setRun({ id: d.id, r: { processed: 0, total: 0 } });
    try {
      const link = await chatsApi.createLink(d.id, device.deviceId);
      const info = await chatsApi.getLink(link.id);
      const todo = Math.max(0, (info.total ?? 0) - (info.done ?? 0));
      const res = await sendHistory(device, d.id, d.public_key, abort.current.signal, (n) => setRun({ id: d.id, r: { processed: n, total: todo } }));
      toast.success(`${res.added} Nachrichten an „${d.label || 'Gerät'}“ übertragen.`);
    } catch (e) {
      if (!isAbort(e)) toast.error(e, 'Verlauf übertragen');
    } finally {
      setRun(null);
    }
  };

  return (
    <div className="stack-sm">
      <p className="small">
        Jedes Gerät hat einen eigenen Schlüssel, der es nie verlässt.
        <HelpTip>
          Der Fingerabdruck identifiziert den Schlüssel des Geräts. Vergleichen Sie ihn, wenn Sie ein neues Gerät einrichten: stimmt er auf beiden Geräten überein, ist es wirklich Ihr Gerät.
          Ein neues Gerät liest zunächst nur Nachrichten ab der Einrichtung – den früheren Verlauf überträgt ein eingerichtetes Gerät auf Ihren Wunsch („Verlauf senden“) oder die Wiederherstellung per Passwort.
        </HelpTip>
      </p>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      <ul className="pf-list">
        {(q.data?.devices ?? []).map((d) => {
          const mine = d.id === device.deviceId;
          return (
            <li key={d.id} className="ch-member ch-device">
              <Icon name={mine ? 'check' : 'lock'} />
              <span className="ch-member-main">
                <strong>
                  {d.label || 'Gerät'} {mine && <span className="badge badge-success">dieses Gerät</span>}{' '}
                  {!d.acked && !mine && <span className="badge badge-warning">neu</span>}
                </strong>
                <span className="xsmall muted">
                  Schlüssel <Fingerprint publicKey={d.public_key} />
                </span>
                <span className="xsmall muted">
                  eingerichtet {formatDateTime(d.created_at)}
                  {d.last_seen_at ? ` · zuletzt aktiv ${formatDateTime(d.last_seen_at)}` : ''}
                </span>
                {run?.id === d.id && <RunBar run={run.r} label="Verlauf wird übertragen" />}
              </span>
              <span className="ch-device-actions">
                {!mine && !d.acked && (
                  <AsyncButton className="btn btn-sm" onClick={async () => { await chatsApi.ackDevice(d.id, device.deviceId); q.reload(); }}>
                    Das bin ich
                  </AsyncButton>
                )}
                {!mine && run?.id !== d.id && (
                  <button type="button" className="btn btn-sm" disabled={!!run} onClick={() => void send(d)} title="Fingerabdruck vorher mit dem anderen Gerät vergleichen">
                    Verlauf senden
                  </button>
                )}
                {run?.id === d.id && (
                  <button type="button" className="btn btn-sm" onClick={() => abort.current?.abort()}>
                    Abbrechen
                  </button>
                )}
                <AsyncButton
                  className="btn btn-sm btn-ghost"
                  confirm={mine ? 'Dieses Gerät abmelden? Bisherige Nachrichten sind hier danach nicht mehr lesbar.' : 'Gerät entfernen? Es kann danach keine neuen Nachrichten mehr lesen.'}
                  onClick={async () => {
                    await chatsApi.revokeDevice(d.id);
                    if (mine) {
                      forgetDevice(device.userId);
                      window.location.reload();
                    }
                    q.reload();
                  }}
                >
                  Entfernen
                </AsyncButton>
              </span>
            </li>
          );
        })}
      </ul>
      <p className="small">
        Dieses Gerät kann ältere Nachrichten nicht lesen?{' '}
        <button type="button" className="kr-linkbtn" onClick={onTransfer}>
          Verlauf übertragen
        </button>
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------- Verknüpfen
/** Neues Gerät: Code und QR anzeigen, Fingerabdruck, auf Freigabe warten. */
function LinkThisDevice({ device }: { device: LocalDevice }) {
  const [link, setLink] = useState<LinkInfo | null>(null);
  const [live, setLive] = useState<LinkInfo | null>(null);
  const [error, setError] = useState<unknown>(null);

  const start = useCallback(async () => {
    setError(null);
    try {
      const l = await chatsApi.createLink(device.deviceId);
      setLink(l);
      setLive(l);
    } catch (e) {
      setError(e);
    }
  }, [device.deviceId]);

  useEffect(() => {
    if (!link) return undefined;
    const t = window.setInterval(() => {
      chatsApi.getLink(link.id).then(setLive, () => undefined);
    }, 2500);
    return () => window.clearInterval(t);
  }, [link]);

  const status = live?.status;
  const done = live && live.total ? (live.done ?? 0) / live.total : 0;
  return (
    <section className="card ch-card" aria-label="Dieses Gerät verknüpfen">
      <h3>
        Dieses Gerät erhält den Verlauf
        <HelpTip>Zeigen Sie hier einen Code an und geben Sie ihn auf einem Gerät frei, auf dem Sie die Chats schon lesen können.</HelpTip>
      </h3>
      {!link || status === 'cancelled' || status === 'expired' ? (
        <div className="stack-sm">
          {status === 'expired' && <p className="small">Der letzte Code ist abgelaufen.</p>}
          <div>
            <button type="button" className="btn btn-primary" onClick={() => void start()}>
              <Icon name="lock" /> Code anzeigen
            </button>
          </div>
          {error ? <Alert kind="error">{errorMessage(error)}</Alert> : null}
        </div>
      ) : (
        <div className="stack-sm">
          {status === 'pending' && (
            <>
              <p className="small">
                Code auf dem anderen Gerät eingeben oder QR-Code scannen.
                <HelpTip>Öffnen Sie auf dem anderen Gerät „Geräte → Verlauf übertragen“ und geben Sie diesen Code ein, oder scannen Sie den QR-Code mit dem Handy.</HelpTip>
              </p>
              <div className="ch-code" aria-live="polite">
                {formatLinkCode(link.code ?? '')}
              </div>
              <QrCode text={linkUrl(link.code ?? '')} size={160} label="QR-Code zum Freigeben dieses Geräts" />
              <p className="small">
                Fingerabdruck dieses Geräts: <Fingerprint publicKey={device.publicKey} />
                <HelpTip>Das andere Gerät zeigt Ihnen vor der Freigabe diesen Fingerabdruck. Geben Sie nur frei, wenn beide übereinstimmen.</HelpTip>
              </p>
              <p className="xsmall muted">Der Code gilt 15 Minuten.</p>
            </>
          )}
          {status === 'approved' && (
            <>
              <Alert kind="success">Freigegeben, der Verlauf wird übertragen.</Alert>
              {live && (live.total ?? 0) > 0 && <ProgressBar value={done} label={`Verlauf (${live.done ?? 0} von ${live.total})`} />}
            </>
          )}
          <div>
            <AsyncButton
              className="btn btn-sm"
              onClick={async () => {
                await chatsApi.cancelLink(link.id);
                setLink(null);
                setLive(null);
              }}
            >
              {status === 'approved' ? 'Beenden' : 'Abbrechen'}
            </AsyncButton>
          </div>
        </div>
      )}
    </section>
  );
}

/** Eingerichtetes Gerät: Code eingeben, Fingerabdruck vergleichen, Verlauf übertragen. */
function ApproveOther({ device, initialCode }: { device: LocalDevice; initialCode: string }) {
  const toast = useToast();
  const [code, setCode] = useState(initialCode);
  const [found, setFound] = useState<LinkInfo | null>(null);
  const [run, setRun] = useState<Run | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const abort = useRef<AbortController | null>(null);

  const lookup = useCallback(async (value: string) => {
    setResult(null);
    try {
      setFound(await chatsApi.lookupLink(parseLinkCode(value)));
    } catch (e) {
      setFound(null);
      toast.error(e, 'Code');
    }
  }, [toast]);

  useEffect(() => {
    if (initialCode) void lookup(initialCode);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const transfer = async () => {
    if (!found) return;
    abort.current = new AbortController();
    setRun({ processed: 0, total: 0 });
    try {
      const approved = await chatsApi.approveLink(found.id, device.deviceId);
      const todo = Math.max(0, (approved.total ?? 0) - (approved.done ?? 0));
      const res = await sendHistory(device, found.device_id, found.public_key, abort.current.signal, (n) => setRun({ processed: n, total: todo }));
      setResult(`${res.added} Nachrichten übertragen.${res.unreadable ? ` ${res.unreadable} ließen sich nicht öffnen.` : ''}`);
      setFound(null);
      setCode('');
    } catch (e) {
      if (isAbort(e)) setResult('Abgebrochen – Sie können später fortsetzen: Code erneut eingeben, es werden nur fehlende Nachrichten übertragen.');
      else toast.error(e, 'Verlauf übertragen');
    } finally {
      setRun(null);
    }
  };

  return (
    <section className="card ch-card" aria-label="Anderes Gerät freigeben">
      <h3>Anderes Gerät freigeben</h3>
      <div className="stack-sm">
        <div className="field">
          <label htmlFor="ch-link-code">Code vom neuen Gerät</label>
          <div className="copy-field">
            <input id="ch-link-code" value={code} maxLength={80} autoComplete="off" spellCheck={false} placeholder="XXXX-XXXX" onChange={(e) => setCode(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && void lookup(code)} />
            <button type="button" className="btn" onClick={() => void lookup(code)} disabled={!!run}>
              Prüfen
            </button>
          </div>
        </div>
        {found && (
          <div className="stack-sm">
            <Alert kind="warning" title={`Gerät „${found.label || 'Gerät'}“ möchte den Verlauf`}>
              Fingerabdruck auf dem neuen Gerät: <Fingerprint publicKey={found.public_key} />
              <br />
              Geben Sie nur frei, wenn dieser Fingerabdruck dort angezeigt wird.
            </Alert>
            {run ? (
              <>
                <RunBar run={run} label="Verlauf wird übertragen" />
                <div>
                  <button type="button" className="btn btn-sm" onClick={() => abort.current?.abort()}>
                    Abbrechen
                  </button>
                </div>
              </>
            ) : (
              <div className="row">
                <button type="button" className="btn btn-primary" onClick={() => void transfer()}>
                  <Icon name="check" /> Fingerabdruck stimmt – Verlauf übertragen
                </button>
                <AsyncButton className="btn" onClick={async () => { await chatsApi.cancelLink(found.id); setFound(null); }}>
                  Ablehnen
                </AsyncButton>
              </div>
            )}
          </div>
        )}
        {result && <Alert kind="info">{result}</Alert>}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------------------------- Backup
function SecretChoice({ onSecret }: { onSecret: (secret: string | null) => void }) {
  const [mode, setMode] = useState<'code' | 'own'>('code');
  const [code, setCode] = useState(() => generateRecoveryCode());
  const [own, setOwn] = useState('');
  const [saved, setSaved] = useState(false);
  const problem = mode === 'own' && own ? passwordProblem(own) : null;
  useEffect(() => {
    onSecret(saved && (mode === 'code' || (own && !passwordProblem(own))) ? (mode === 'code' ? code : own) : null);
  }, [saved, mode, code, own, onSecret]);
  return (
    <div className="stack-sm">
      <div className="row">
        <label className="row">
          <input type="radio" name="ch-secret" checked={mode === 'code'} onChange={() => setMode('code')} /> Erzeugter Code (empfohlen)
        </label>
        <label className="row">
          <input type="radio" name="ch-secret" checked={mode === 'own'} onChange={() => setMode('own')} /> Eigenes Passwort
        </label>
      </div>
      {mode === 'code' ? (
        <>
          <CopyField value={code} label="Ihr Wiederherstellungscode" />
          <div>
            <button type="button" className="btn btn-sm" onClick={() => setCode(generateRecoveryCode())}>
              Neuen Code erzeugen
            </button>
          </div>
        </>
      ) : (
        <div className="field">
          <label htmlFor="ch-own-pw">Wiederherstellungs-Passwort</label>
          <input id="ch-own-pw" type="password" autoComplete="new-password" value={own} onChange={(e) => setOwn(e.target.value)} />
          {problem && <span className="field-error">{problem}</span>}
        </div>
      )}
      <label className="row">
        <input type="checkbox" checked={saved} onChange={(e) => setSaved(e.target.checked)} /> Ich habe {mode === 'code' ? 'den Code' : 'das Passwort'} sicher notiert (Passwortmanager oder Ausdruck).
      </label>
      <p className="xsmall muted">Ohne {mode === 'code' ? 'diesen Code' : 'dieses Passwort'} gibt es keine Wiederherstellung.</p>
    </div>
  );
}

function BackupTab({ device }: { device: LocalDevice }) {
  const toast = useToast();
  const info = useApi((signal) => chatsApi.backup(signal), [], { live: ['chats'] });
  const [secret, setSecret] = useState<string | null>(null);
  const [run, setRun] = useState<Run | null>(null);
  const [restoreSecret, setRestoreSecret] = useState('');
  const [oldSecret, setOldSecret] = useState('');
  const [changing, setChanging] = useState(false);
  const onSecret = useCallback((s: string | null) => setSecret(s), []);
  const abort = useRef<AbortController | null>(null);
  const enabled = info.data?.enabled === true;

  return (
    <div className="stack-sm">
      <p className="small">
        Optional: Mit Code oder Passwort holen Sie den Verlauf auch ohne Geräte zurück.
        <HelpTip>
          Es wird ein zusätzlicher Schlüssel für Ihr Konto erzeugt. Alle Gesprächspartner packen Nachrichten künftig auch für diesen Schlüssel ein; er selbst liegt nur verschlüsselt (mit Ihrem Code/Passwort) auf dem Server.
          Wer Code/Passwort kennt, kann Ihren Verlauf lesen – bewahren Sie ihn wie ein Passwort auf. Vergessen Sie ihn, ist das Backup nutzlos; es lässt sich dann nur löschen und neu einrichten.
        </HelpTip>
      </p>
      {info.error ? <ErrorBox error={info.error} onRetry={info.reload} /> : null}
      {info.data && !enabled && (
        <section className="card ch-card" aria-label="Backup einrichten">
          <h3>Backup einrichten</h3>
          <div className="stack-sm">
            <SecretChoice onSecret={onSecret} />
            {run && <RunBar run={run} label="Bisheriger Verlauf wird gesichert" />}
            <div>
              <AsyncButton
                className="btn btn-primary"
                disabled={!secret || !!run}
                onClick={async () => {
                  if (!secret) return;
                  setRun({ processed: 0, total: 0 });
                  try {
                    const res = await enableBackup(device, secret, (n) => setRun({ processed: n, total: 0 }));
                    toast.success(`Backup eingerichtet (${res.added} Nachrichten gesichert).`);
                    info.reload();
                  } finally {
                    setRun(null);
                  }
                }}
              >
                <Icon name="lock" /> Backup einrichten
              </AsyncButton>
            </div>
          </div>
        </section>
      )}
      {enabled && (
        <>
          <Alert kind="success" title="Wiederherstellungs-Backup ist aktiv">
            Seit {info.data?.created_at ? formatDateTime(info.data.created_at) : '—'}
            {info.data?.updated_at && info.data.updated_at !== info.data.created_at ? ` · Passwort zuletzt geändert ${formatDateTime(info.data.updated_at)}` : ''}.
          </Alert>
          <section className="card ch-card" aria-label="Verlauf wiederherstellen">
            <h3>Verlauf auf diesem Gerät wiederherstellen</h3>
            <div className="stack-sm">
              <div className="field">
                <label htmlFor="ch-restore">Code oder Passwort</label>
                <input id="ch-restore" type="password" autoComplete="off" value={restoreSecret} onChange={(e) => setRestoreSecret(e.target.value)} />
              </div>
              {run && <RunBar run={run} label="Verlauf wird wiederhergestellt" />}
              <div className="row">
                <AsyncButton
                  className="btn btn-primary"
                  disabled={!restoreSecret || !!run}
                  onClick={async () => {
                    abort.current = new AbortController();
                    setRun({ processed: 0, total: 0 });
                    try {
                      const res = await restoreFromBackup(device, restoreSecret, abort.current.signal, (n) => setRun({ processed: n, total: 0 }));
                      if (!res) toast.error(new Error('Code oder Passwort stimmt nicht.'), 'Wiederherstellung');
                      else {
                        toast.success(`${res.added} Nachrichten wiederhergestellt.`);
                        setRestoreSecret('');
                      }
                    } catch (e) {
                      if (!isAbort(e)) throw e;
                    } finally {
                      setRun(null);
                    }
                  }}
                >
                  Wiederherstellen
                </AsyncButton>
                {run && (
                  <button type="button" className="btn" onClick={() => abort.current?.abort()}>
                    Abbrechen
                  </button>
                )}
              </div>
            </div>
          </section>
          <section className="card ch-card" aria-label="Passwort ändern">
            <h3>Code oder Passwort ändern</h3>
            {!changing ? (
              <button type="button" className="btn" onClick={() => setChanging(true)}>
                Ändern …
              </button>
            ) : (
              <div className="stack-sm">
                <div className="field">
                  <label htmlFor="ch-old-pw">Bisheriger Code oder bisheriges Passwort</label>
                  <input id="ch-old-pw" type="password" autoComplete="off" value={oldSecret} onChange={(e) => setOldSecret(e.target.value)} />
                </div>
                <SecretChoice onSecret={onSecret} />
                <div className="row">
                  <AsyncButton
                    className="btn btn-primary"
                    disabled={!secret || !oldSecret}
                    onClick={async () => {
                      if (!secret) return;
                      if (await changeBackupSecret(oldSecret, secret)) {
                        toast.success('Neuer Code bzw. neues Passwort gespeichert.');
                        setChanging(false);
                        setOldSecret('');
                        info.reload();
                      } else toast.error(new Error('Der bisherige Code oder das Passwort stimmt nicht.'), 'Ändern');
                    }}
                  >
                    Speichern
                  </AsyncButton>
                  <button type="button" className="btn" onClick={() => setChanging(false)}>
                    Abbrechen
                  </button>
                </div>
              </div>
            )}
          </section>
          <section className="card ch-card" aria-label="Backup löschen">
            <h3>
              Backup löschen
              <HelpTip>Der Archivschlüssel wird vom Server entfernt; die Wiederherstellung ist danach nicht mehr möglich.</HelpTip>
            </h3>
            <AsyncButton
              className="btn btn-danger"
              confirm="Backup wirklich löschen? Eine Wiederherstellung mit Code/Passwort ist danach nicht mehr möglich."
              onClick={async () => {
                await chatsApi.deleteBackup();
                info.reload();
              }}
            >
              Backup löschen
            </AsyncButton>
          </section>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------------------------- Neue Schlüssel
function NewKeysTab({ device }: { device: LocalDevice }) {
  const toast = useToast();
  const [keepHistory, setKeepHistory] = useState(true);
  const [keepBackup, setKeepBackup] = useState(true);
  const [run, setRun] = useState<Run | null>(null);
  return (
    <div className="stack-sm">
      <section className="card ch-card" aria-label="Dieses Gerät neu einrichten">
        <h3>
          Dieses Gerät neu einrichten
          <HelpTip>
            Erzeugt einen neuen Schlüssel für diesen Browser und widerruft den alten. Gesprächspartner sehen den Wechsel („Sicherheitsschlüssel hat sich geändert“).
          </HelpTip>
        </h3>
        <div className="stack-sm">
          <label className="row">
            <input type="checkbox" checked={keepHistory} onChange={(e) => setKeepHistory(e.target.checked)} /> Bisherigen Verlauf auf den neuen Schlüssel übernehmen
          </label>
          {run && <RunBar run={run} label="Verlauf wird übernommen" />}
          <div>
            <AsyncButton
              className="btn"
              disabled={!!run}
              confirm="Neuen Schlüssel für dieses Gerät erzeugen?"
              onClick={async () => {
                setRun({ processed: 0, total: 0 });
                try {
                  await rekeyThisDevice(device, keepHistory, (n) => setRun({ processed: n, total: 0 }));
                  window.location.reload();
                } finally {
                  setRun(null);
                }
              }}
            >
              Neuen Schlüssel erzeugen
            </AsyncButton>
          </div>
        </div>
      </section>
      <section className="card ch-card" aria-label="Alle Geräte zurücksetzen">
        <h3>
          Alle Geräte zurücksetzen
          <HelpTip>
            Für den Fall, dass ein Gerät verloren ging oder Dritte Zugriff hatten: Alle Schlüssel Ihrer Geräte werden widerrufen, dieses Gerät bekommt einen neuen. Der Verlauf ist danach nur noch über das Wiederherstellungs-Backup oder ein Gerät lesbar, das Sie danach neu verknüpfen. Bisher verknüpfte Geräte verlieren den Zugriff.
          </HelpTip>
        </h3>
        <div className="stack-sm">
          <label className="row">
            <input type="checkbox" checked={keepBackup} onChange={(e) => setKeepBackup(e.target.checked)} /> Wiederherstellungs-Backup behalten (falls eingerichtet)
          </label>
          <div>
            <AsyncButton
              className="btn btn-danger"
              confirm="Wirklich ALLE Geräte zurücksetzen? Der bisherige Verlauf ist danach auf diesem Gerät nicht mehr lesbar – nur über Backup oder Verknüpfung."
              onClick={async () => {
                try {
                  await resetAllDevices(device.userId, keepBackup);
                  window.location.reload();
                } catch (e) {
                  toast.error(e, 'Zurücksetzen');
                }
              }}
            >
              Alle Geräte zurücksetzen
            </AsyncButton>
          </div>
        </div>
      </section>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------- Dialog
export function DevicesModal({ device, initialTab = 'geraete', initialCode = '', onClose }: { device: LocalDevice; initialTab?: DevicesTab; initialCode?: string; onClose: () => void }) {
  const [tab, setTab] = useState<DevicesTab>(initialCode ? 'verlauf' : initialTab);
  return (
    <Modal title="Geräte & Schlüssel" onClose={onClose} size="lg">
      <div className="stack-sm">
        <Tabs
          label="Bereich"
          active={tab}
          onChange={setTab}
          tabs={[
            { key: 'geraete', label: 'Geräte' },
            { key: 'verlauf', label: 'Verlauf übertragen' },
            { key: 'backup', label: 'Wiederherstellung' },
            { key: 'schluessel', label: 'Neue Schlüssel' },
          ]}
        />
        {tab === 'geraete' && <DevicesTabView device={device} onTransfer={() => setTab('verlauf')} />}
        {tab === 'verlauf' && (
          <div className="stack-sm">
            <LinkThisDevice device={device} />
            <ApproveOther device={device} initialCode={initialCode} />
          </div>
        )}
        {tab === 'backup' && <BackupTab device={device} />}
        {tab === 'schluessel' && <NewKeysTab device={device} />}
      </div>
    </Modal>
  );
}

/** Hinweis „Neues Gerät eingerichtet – waren Sie das?“ (nur für die *anderen* Geräte des Kontos). */
export function NewDeviceBanner({ device, onOpen }: { device: LocalDevice; onOpen: () => void }) {
  const q = useApi((signal) => chatsApi.myDevices(signal), [device.deviceId], { live: ['chats'] });
  const fresh = (q.data?.devices ?? []).filter((d) => !d.acked && d.id !== device.deviceId);
  if (!fresh.length) return null;
  const d = fresh[0];
  return (
    <Alert
      kind="warning"
      title="Neues Gerät für Ihre Chats"
      action={
        <span className="row">
          <AsyncButton className="btn btn-sm" onClick={async () => { await chatsApi.ackDevice(d.id, device.deviceId); q.reload(); }}>
            Das war ich
          </AsyncButton>
          <AsyncButton className="btn btn-sm btn-danger" confirm="Dieses Gerät entfernen?" onClick={async () => { await chatsApi.revokeDevice(d.id); q.reload(); }}>
            Das war ich nicht – entfernen
          </AsyncButton>
        </span>
      }
    >
      „{d.label || 'Gerät'}“ (Schlüssel <Fingerprint publicKey={d.public_key} />) wurde {formatDateTime(d.created_at)} eingerichtet.{fresh.length > 1 ? ` (${fresh.length - 1} weitere)` : ''}{' '}
      <button type="button" className="kr-linkbtn" onClick={onOpen}>
        Geräte ansehen
      </button>
    </Alert>
  );
}

/**
 * Updates unter `/betrieb`: Stand des Update-Agenten, anstehendes Update mit Zeitfenster, einmal verschieben,
 * „Jetzt installieren“, Modus (automatisch / nur manuell) und – falls der Anbieter es erlaubt – die Reihenfolge der Server.
 * Daten: `GET /admin/updates`, `POST /admin/updates/postpone|install-now`, `PUT /admin/updates/mode|strategy`.
 */
import { useState } from 'react';
import { http } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { AsyncButton, ErrorBox } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { formatDateTime } from '../../lib/dates';
import {
  UPDATE_STATE_BADGE,
  UPDATE_STATE_LABELS,
  migrationText,
  windowText,
  type UpdatesOverview,
} from './updates';

export function UpdatesCard() {
  const toast = useToast();
  const q = useApi((signal) => http.get<UpdatesOverview>('/admin/updates', undefined, { signal }), []);
  const [days, setDays] = useState(2);
  const o = q.data;
  const st = o?.status ?? null;
  const offer = st?.offered ?? null;

  return (
    <section className="card stack-sm" aria-label="Updates">
      <div className="card-head">
        <h2>
          Updates{' '}
          <HelpTip>
            Ihr Anbieter spielt Updates in einem vereinbarten Zeitfenster ein, meist nachts oder am Wochenende. Vor jedem Update wird automatisch eine Sicherung erstellt; läuft die neue Version nicht einwandfrei, kehrt der Server selbstständig zur alten zurück. Ein Update können Sie einmal um bis zu {o?.max_postpone_days ?? 7} Tage verschieben – dringende Sicherheitsupdates nicht.
          </HelpTip>
        </h2>
        <button type="button" className="btn btn-sm" onClick={q.reload}>
          <Icon name="refresh" /> Aktualisieren
        </button>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {o && !o.agent && (
        <p className="small muted">
          Automatische Updates: nicht eingerichtet{' '}
          <HelpTip>Updates spielt dann Ihre IT bzw. der Anbieter manuell ein (Betriebshandbuch, Abschnitt Updates).</HelpTip>
        </p>
      )}
      {o && o.agent && st && (
        <>
          {o.agent_stale && <p className="small" role="alert">Update-Dienst seit über 1 Stunde ohne Meldung <HelpTip>Bitte prüfen Sie, ob der Dienst auf dem Server läuft.</HelpTip></p>}
          <dl className="kv small">
            <dt>Installierte Version</dt>
            <dd>{st.version || o.version}</dd>
            <dt>Stand</dt>
            <dd>
              <span className={`badge ${UPDATE_STATE_BADGE[st.state] ?? 'badge-info'}`}>{UPDATE_STATE_LABELS[st.state] ?? st.state}</span>
              {st.detail ? <span className="muted"> {st.detail}</span> : null}
            </dd>
            <dt>Modus</dt>
            <dd>{st.mode === 'manual' ? 'nur manuell' : 'automatisch im geplanten Zeitfenster'}{st.contract_manual ? ' (vertraglich vereinbart)' : ''}</dd>
            {st.last_ok_at && (
              <>
                <dt>Letzte Anfrage beim Anbieter</dt>
                <dd>{formatDateTime(st.last_ok_at)}</dd>
              </>
            )}
          </dl>

          {offer ? (
            <div className="card card-flat stack-sm">
              <div className="row-between" style={{ gap: 8, flexWrap: 'wrap' }}>
                <strong>Update auf Version {offer.version}</strong>
                {st.urgent && <span className="badge badge-danger">dringendes Sicherheitsupdate</span>}
              </div>
              {offer.notes ? <p className="small" style={{ overflowWrap: 'anywhere' }}>{offer.notes}</p> : null}
              <p className="small">
                <strong>Zeitfenster:</strong> {windowText(st.window)}
                {st.postponed_until ? <> · verschoben bis {formatDateTime(st.postponed_until)}</> : null}
              </p>
              <p className="small muted">{migrationText(offer.migration)}</p>
              {st.announce ? <p className="small">{st.announce}</p> : null}
              <div className="row" style={{ gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                <AsyncButton
                  className="btn btn-primary btn-sm"
                  confirm={`Version ${offer.version} jetzt installieren? Die Anwendung ist dabei kurz nicht erreichbar.`}
                  confirmLabel="Jetzt installieren"
                  onClick={async () => {
                    await http.post('/admin/updates/install-now', { version: offer.version });
                    toast.success('Auftrag erteilt – der Update-Dienst beginnt in wenigen Minuten.');
                    q.reload();
                  }}
                >
                  Jetzt installieren
                </AsyncButton>
                {st.can_postpone && !st.urgent && (
                  <>
                    <label className="small" htmlFor="upd-days">Verschieben um</label>
                    <select id="upd-days" value={days} onChange={(e) => setDays(Number(e.target.value))}>
                      {Array.from({ length: o.max_postpone_days }, (_, i) => i + 1).map((d) => (
                        <option key={d} value={d}>{d === 1 ? '1 Tag' : `${d} Tage`}</option>
                      ))}
                    </select>
                    <AsyncButton
                      className="btn btn-sm"
                      confirm={`Das Update einmalig um ${days} ${days === 1 ? 'Tag' : 'Tage'} verschieben?`}
                      confirmLabel="Verschieben"
                      onClick={async () => {
                        await http.post('/admin/updates/postpone', { version: offer.version, days });
                        toast.success('Update verschoben');
                        q.reload();
                      }}
                    >
                      Verschieben
                    </AsyncButton>
                  </>
                )}
                {!st.can_postpone && !st.urgent && st.postponed_until && <span className="small muted">Bereits einmal verschoben.</span>}
              </div>
            </div>
          ) : (
            <p className="small muted">Zurzeit ist kein Update angekündigt.</p>
          )}

          <div className="row" style={{ gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
            {!st.contract_manual && (
              <AsyncButton
                className="btn btn-sm"
                onClick={async () => {
                  await http.put('/admin/updates/mode', { mode: st.mode === 'manual' ? 'auto' : 'manual' });
                  toast.success(st.mode === 'manual' ? 'Updates laufen wieder automatisch' : 'Updates nur noch auf Ihre Freigabe');
                  q.reload();
                }}
              >
                {st.mode === 'manual' ? 'Auf automatische Updates umstellen' : 'Nur noch manuell aktualisieren'}
              </AsyncButton>
            )}
            {st.may_choose_strategy && (st.nodes ?? 1) > 1 && (
              <>
                <label className="small" htmlFor="upd-strategy">Mehrere Server</label>
                <select
                  id="upd-strategy"
                  value={o.plan.strategy ?? st.strategy ?? 'rolling'}
                  onChange={async (e) => {
                    await http.put('/admin/updates/strategy', { strategy: e.target.value });
                    toast.success('Reihenfolge gespeichert');
                    q.reload();
                  }}
                >
                  <option value="rolling">nacheinander (immer ein Server bleibt erreichbar)</option>
                  <option value="simultaneous">gleichzeitig (kurze Ausfallzeit)</option>
                </select>
              </>
            )}
          </div>

          {st.failed && Object.keys(st.failed).length > 0 && (
            <p className="small" role="alert">
              Letzter Fehler: {Object.entries(st.failed).map(([v, why]) => `Version ${v}: ${why}`).join(' · ')}. Ihr Anbieter wurde informiert.
            </p>
          )}
          {st.log.length > 0 && (
            <details className="disclosure">
              <summary>Protokoll des Update-Dienstes</summary>
              <ul className="xsmall" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {[...st.log].reverse().map((l, i) => (
                  <li key={`${l.ts}-${i}`}>
                    <span className="muted">{formatDateTime(l.ts)}</span> {l.text}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </>
      )}
    </section>
  );
}

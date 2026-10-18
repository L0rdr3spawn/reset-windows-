import { useState } from 'react';
import { Link } from 'react-router-dom';
import { planning, settings as settingsApi } from '../../api/endpoints';
import type { Settings } from '../../api/types';
import { AbbrList } from '../../components/Abbr';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Alert, AsyncButton, ErrorBox, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { ProposalsList, useProposals } from '../../features/planpruefung/ProposalsView';
import { invalidate, useSettings } from '../../hooks/useCollection';
import { formatDateTime } from '../../lib/dates';

const KIND: Record<string, 'success' | 'info' | 'warning' | 'error'> = {
  ok: 'success',
  applied: 'success',
  covered: 'success',
  proposal: 'warning',
  partial: 'warning',
  unsolved: 'warning',
  running: 'info',
  waiting: 'info',
  off: 'info',
  idle: 'info',
  error: 'error',
};

/**
 * „Plan prüfen“: Status der Dauerprüfung („Plan in Ordnung / N Probleme“), offene Vorschlagspakete mit Variantenvergleich
 * und die zugehörigen Einstellungen. Ersetzt die frühere Karte „Automatische Neuplanung“ im Generator.
 */
export function PlanCheckPanel({ canDecide, canGenerate, canSettings }: { canDecide: boolean; canGenerate: boolean; canSettings: boolean }) {
  const toast = useToast();
  const q = useProposals();
  const settings = useSettings(canSettings);
  const [busy, setBusy] = useState(false);

  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!q.data) return <Loading />;
  const { check } = q.data;
  const off = !check.setting || !check.enabled;
  const open = check.open_count;
  const last = check.last;
  const heading = off
    ? 'Dauerprüfung ausgeschaltet'
    : open === 0
      ? 'Plan in Ordnung'
      : `${open} Problem${open === 1 ? '' : 'e'} im Stundenplan`;

  const patchSettings = async (patch: Partial<Settings>) => {
    try {
      await settingsApi.put(patch as Settings);
      invalidate('settings');
      q.reload();
      toast.success('Einstellung gespeichert');
    } catch (e) {
      toast.error(e, 'Einstellung');
    }
  };

  return (
    <div className="stack">
      <section className="card" aria-labelledby="pc-status">
        <div className="row-between">
          <h2 id="pc-status" style={{ margin: 0 }}>
            <Icon name="sparkles" /> Plan prüfen{' '}
            <HelpTip label="Hilfe zur Dauerprüfung">
              Nach jeder Änderung, die den Stundenplan betrifft (Lehrkraft, Raum, Klasse, Kurs, Stundentafel, Einstellungen), prüft das System im Hintergrund, ob der
              Plan noch gültig ist. Gibt es Probleme, rechnet es mehrere Lösungen aus – die Berechtigten entscheiden. Krankmeldungen und Raumsperren für einzelne
              Tage regelt der Vertretungsplan sofort selbst. Den Plan zum Schuljahr komplett neu aufbauen Sie im Tab „Neuaufbau“.
            </HelpTip>
          </h2>
          {canGenerate && check.enabled && check.setting && (
            <AsyncButton
              className="btn btn-sm"
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                try {
                  await planning.autoplanRun();
                  q.reload();
                } catch (e) {
                  toast.error(e, 'Plan prüfen');
                } finally {
                  setBusy(false);
                }
              }}
            >
              <Icon name="refresh" /> Jetzt prüfen
            </AsyncButton>
          )}
        </div>
        {off ? (
          <Alert kind="info" title={heading}>
            {!check.enabled ? 'Auf diesem Server ist die Dauerprüfung abgeschaltet.' : 'Unten unter „Einstellungen“ einschalten.'}
          </Alert>
        ) : (
          <Alert kind={open === 0 ? 'success' : (KIND[check.status] ?? 'warning')} title={heading}>
            {open > 0 && <div>{check.message}</div>}
            {check.checked_at && <div className="xsmall muted">zuletzt geprüft {formatDateTime(check.checked_at)}</div>}
          </Alert>
        )}
        {open > 0 && (
          <details className="disclosure" open={check.status === 'unsolved' || check.status === 'off'}>
            <summary>Probleme anzeigen ({open})</summary>
            <ul className="warning-list small">
              {check.open_problems.map((p, i) => (
                <li key={i}>{p}</li>
              ))}
            </ul>
          </details>
        )}
        <p className="xsmall muted" style={{ margin: 0 }}>
          Den kompletten Plan neu aufbauen: <Link to="/planung/generator">Neuaufbau (Generator)</Link>.
        </p>
      </section>

      {canDecide && <ProposalsList data={q.data} reload={q.reload} canDecide={canDecide} />}

      {last && (
        <details className="disclosure">
          <summary>
            Letzte automatische Änderung ({formatDateTime(last.at)}): {last.fixed ?? 0} Problem(e) behoben
          </summary>
          {last.reasons?.length > 0 && (
            <ul className="small">
              {last.reasons.slice(0, 10).map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          )}
          {last.room_changes?.length > 0 && (
            <ul className="small">
              {last.room_changes.slice(0, 40).map((c, i) => (
                <li key={i}>
                  {c.course}: {c.old ?? '–'} → {c.new}
                </li>
              ))}
            </ul>
          )}
          {last.changes?.length > 0 && (
            <ul className="small">
              {last.changes.slice(0, 40).map((c, i) => (
                <li key={i}>
                  <strong>{c.label}</strong> {c.classes?.length ? <AbbrList kind="class" ids={c.classes} /> : ''}: {c.from.join(', ') || '–'} → {c.to.join(', ') || '–'}
                </li>
              ))}
            </ul>
          )}
        </details>
      )}

      {canSettings && settings.data && (
        <section className="card" aria-labelledby="pc-settings">
          <h2 id="pc-settings">
            Einstellungen{' '}
            <HelpTip label="Hilfe zu den Einstellungen">
              „Dauerprüfung“ schaltet die Prüfung nach Änderungen ein oder aus. Standardmäßig ändert das System den Stundenplan nie ohne Entscheidung. Nur wenn Sie
              „Reine Raumänderungen ohne Rückfrage übernehmen“ einschalten, werden Fälle, in denen nur ein Raum angepasst werden muss und kein Unterricht wandert,
              sofort umgesetzt (sichtbar und rückgängig unter „Verlauf &amp; Audit“).
            </HelpTip>
          </h2>
          <div className="stack-sm" style={{ marginTop: 8 }}>
          <label className="check">
            <input type="checkbox" checked={settings.data.auto_replan !== false} onChange={(e) => void patchSettings({ auto_replan: e.target.checked })} /> Dauerprüfung nach Änderungen
          </label>
          <label className="check">
            <input
              type="checkbox"
              checked={settings.data.plan_auto_apply === 'raeume'}
              disabled={settings.data.auto_replan === false}
              onChange={(e) => void patchSettings({ plan_auto_apply: e.target.checked ? 'raeume' : 'aus' })}
            />{' '}
            Reine Raumänderungen ohne Rückfrage übernehmen
          </label>
          </div>
        </section>
      )}
    </div>
  );
}

/**
 * Vorher/Nachher: Der Generator rechnet einen Entwurf mit den (ungespeicherten) Regeln dieses Entwurfs und die
 * Kennzahlen werden mit dem aktuellen Stundenplan verglichen. Es wird nichts übernommen – der Entwurf liegt danach
 * wie jeder Generatorlauf im Tab „Generator“ und kann dort übernommen werden.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { planning } from '../../../api/endpoints';
import type { Job, PlanningReport } from '../../../api/types';
import { Icon } from '../../../components/Icon';
import { HelpTip } from '../../../components/HelpTip';
import { Alert, AsyncButton, ProgressBar } from '../../../components/ui';
import { useToast } from '../../../context/ToastContext';
import { useJobEvents } from '../../../hooks/useLive';
import { rulesApi } from './api';
import { compareStats, type RulesDraft } from './model';

const RUNNING = new Set(['queued', 'pending', 'running', 'applying']);
const fmt = (n: number) => n.toLocaleString('de-DE', { maximumFractionDigits: 1 });

export function Simulation({ draft, dirty, canGenerate }: { draft: RulesDraft; dirty: boolean; canGenerate: boolean }) {
  const toast = useToast();
  const [seconds, setSeconds] = useState(30);
  const [job, setJob] = useState<Job | null>(null);
  const [report, setReport] = useState<PlanningReport | null>(null);
  const pollRef = useRef<number | null>(null);

  const refresh = useCallback(async (id: string) => {
    try {
      const j = await planning.job(id);
      setJob(j);
      return j;
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    if (!job || !RUNNING.has(job.status)) return undefined;
    pollRef.current = window.setInterval(() => void refresh(job.id), 2500);
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [job?.id, job?.status, refresh]); // eslint-disable-line react-hooks/exhaustive-deps

  useJobEvents(job?.id ?? null, (ev) => {
    setJob((j) => (j && j.id === ev.id ? { ...j, status: ev.status, progress: ev.progress, message: ev.message } : j));
    if (!RUNNING.has(ev.status)) void refresh(ev.id);
  });

  const start = async () => {
    try {
      const [r, rep] = await Promise.all([rulesApi.simulate(draft, seconds), planning.report()]);
      setReport(rep);
      setJob(r.job ?? { id: r.job_id, status: 'queued', progress: 0, message: 'Gestartet' });
      toast.info('Probelauf gestartet – der Stundenplan bleibt unverändert');
    } catch (e) {
      toast.error(e, 'Probelauf');
    }
  };

  if (!canGenerate) return null;
  const running = !!job && RUNNING.has(job.status);
  const done = !!job && (job.status === 'done' || job.status === 'applied');
  const after = job?.stats ?? job?.result?.stats;
  const rows = done ? compareStats(report?.stats, after) : [];

  return (
    <section className="card">
      <h2>
        <Icon name="sparkles" /> Wirkung vorab prüfen{' '}
        <HelpTip label="Erklärung: Wirkung vorab prüfen">
          {`Der Generator rechnet einen Entwurf mit ${dirty ? 'den hier geänderten (noch nicht gespeicherten)' : 'den aktuellen'} Regeln. Verglichen werden die Kennzahlen des Entwurfs mit dem gültigen Stundenplan. Nichts wird übernommen; das geht danach im Tab „Generator“.`}
        </HelpTip>
      </h2>
      <div className="row" style={{ flexWrap: 'wrap', alignItems: 'end' }}>
        <div className="field" style={{ maxWidth: 320 }}>
          <label htmlFor="rules-sim-time">
            Rechenzeit: <strong>{seconds} s</strong>
          </label>
          <input id="rules-sim-time" type="range" min={10} max={180} step={10} value={seconds} disabled={running} onChange={(e) => setSeconds(Number(e.target.value))} />
        </div>
        <AsyncButton className="btn btn-primary" onClick={start} disabled={running}>
          <Icon name="play" /> Probelauf mit diesen Regeln
        </AsyncButton>
        {running && job && (
          <AsyncButton
            className="btn"
            onClick={async () => {
              try {
                setJob(await planning.cancel(job.id));
              } catch (e) {
                toast.error(e);
              }
            }}
          >
            <Icon name="stop" /> Abbrechen
          </AsyncButton>
        )}
      </div>
      {job && running && (
        <div style={{ marginTop: 12 }}>
          <ProgressBar value={job.progress} label={job.message || job.status} />
        </div>
      )}
      {job?.status === 'failed' && <Alert kind="error" title="Probelauf fehlgeschlagen">{job.error ?? job.message}</Alert>}
      {done && (
        <div className="stack-sm" style={{ marginTop: 12 }}>
          <div className="table-wrap">
            <table className="table table-compact rule-compare">
              <caption className="sr-only">Vergleich aktueller Plan und Entwurf</caption>
              <thead>
                <tr>
                  <th scope="col">Kennzahl</th>
                  <th scope="col" className="num">
                    aktuell
                  </th>
                  <th scope="col" className="num">
                    Entwurf
                  </th>
                  <th scope="col" className="num">
                    Änderung
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.key}>
                    <td>{r.title}</td>
                    <td className="num">{r.before === null ? '–' : fmt(r.before)}</td>
                    <td className="num">{r.after === null ? '–' : fmt(r.after)}</td>
                    <td className={`num${r.delta === null || r.delta === 0 ? '' : r.delta < 0 ? ' better' : ' worse'}`}>
                      {r.delta === null ? '–' : r.delta === 0 ? '±0' : r.delta > 0 ? `+${fmt(r.delta)}` : fmt(r.delta)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="small" style={{ margin: 0 }}>
            Weniger ist besser.{' '}
            <HelpTip label="Erklärung: Vergleich">
              {`Ein Entwurf ist immer auch Zufall, und kurze Rechenzeiten liefern gröbere Pläne als der gültige Stundenplan. Vergleichen Sie mit ähnlicher Rechenzeit wie beim letzten „Generieren“ oder lassen Sie zwei Probeläufe gegeneinander antreten. Der Entwurf steht im Tab „Generator“ und wird nur dort mit „Übernehmen“ zum neuen Stundenplan.${dirty ? ' Die hier geänderten Regeln gelten erst nach „Speichern“ auch für künftige Läufe.' : ''}`}
            </HelpTip>{' '}
            <Link to="/planung/generator">Zum Generator</Link>
          </p>
        </div>
      )}
    </section>
  );
}

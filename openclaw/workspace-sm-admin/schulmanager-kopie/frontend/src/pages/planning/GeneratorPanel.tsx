import { useCallback, useEffect, useRef, useState } from 'react';
import { planning } from '../../api/endpoints';
import type { Job, RebuildResult, WarningsResponse } from '../../api/types';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Alert, AsyncButton, Field, ProgressBar } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { invalidate } from '../../hooks/useCollection';
import { useJobEvents } from '../../hooks/useLive';
import { formatDateTime } from '../../lib/dates';
import { GeneratorResult, type GenJob } from './generator/GeneratorResult';
import { genApi } from './generator/api';
import { plural } from './generator/logic';
import { ClearPlanButton, SnapshotsPanel } from './generator/SnapshotsPanel';
import { PeriodJobNote, usePlanPeriod } from './PeriodPicker';
import { RebuildCourses, RebuildResultView } from './RebuildCourses';

const RUNNING = new Set(['queued', 'pending', 'running', 'applying']);
const STAT_LABELS: Record<string, string> = {
  lessons: 'Unterrichtsblöcke',
  placed: 'verplant',
  unplaced: 'unverplant',
  unplaced_hours: 'unverplante Stunden',
  class_gaps: 'Hohlstunden Klassen (Ø je Woche)',
  teacher_gaps: 'Springstunden Lehrkräfte (Ø je Woche)',
  site_changes: 'Standortwechsel (Ø je Woche)',
  core_late: 'Hauptfächer spät',
  score: 'Bewertung (niedriger = besser)',
  cost: 'Kosten (niedriger = besser)',
  seconds: 'Rechenzeit (s)',
  runs: 'parallele Läufe',
  seed: 'Startwert',
  hours_per_week: 'Stunden je Woche (Durchschnitt)',
  iterations: 'Optimierungsschritte',
  variants: 'Wochenmuster',
  best_seed: 'Startwert des besten Laufs',
};

function WarningsBox({ title, res }: { title: string; res: WarningsResponse }) {
  const warnings = res.warnings ?? [];
  const extra = Object.entries(res)
    .filter(([k, v]) => k !== 'warnings' && (typeof v === 'number' || typeof v === 'string'))
    .map(([k, v]) => `${k}: ${String(v)}`);
  return (
    <Alert kind={warnings.length ? 'warning' : 'success'} title={title}>
      {extra.length > 0 && <div className="small">{extra.join(' · ')}</div>}
      {warnings.length > 0 && (
        <ul className="small">
          {warnings.slice(0, 20).map((w, i) => (
            <li key={i}>{w}</li>
          ))}
          {warnings.length > 20 && <li>… {warnings.length - 20} weitere</li>}
        </ul>
      )}
    </Alert>
  );
}

function JobResult({ job }: { job: Job }) {
  const stats = job.stats ?? job.result?.stats ?? {};
  const unplaced = job.unplaced ?? job.result?.unplaced ?? [];
  const warnings = job.warnings ?? job.result?.warnings ?? [];
  return (
    <div className="stack">
      <div className="grid grid-4">
        {Object.entries(stats)
          .filter(([, v]) => typeof v === 'number' || typeof v === 'string')
          .slice(0, 12)
          .map(([k, v]) => (
            <div key={k} className="card kpi">
              <span className="kpi-value" style={{ fontSize: 'var(--fs-xl)' }}>
                {typeof v === 'number' ? Math.round(v * 100) / 100 : v}
              </span>
              <span className="kpi-label">{STAT_LABELS[k] ?? k}</span>
            </div>
          ))}
      </div>
      {unplaced.length > 0 ? (
        <Alert kind="warning" title={`${unplaced.length} Unterrichtseinheiten konnten nicht verplant werden`}>
          <ul className="small">
            {unplaced.slice(0, 30).map((u, i) => (
              <li key={i}>
                {[u.course_id ?? (u as { course?: string }).course, u.classes?.join(', '), u.subject, u.hours ? `${u.hours} Std.` : null, u.reason]
                  .filter(Boolean)
                  .join(' · ') || JSON.stringify(u)}
              </li>
            ))}
          </ul>
        </Alert>
      ) : (
        <Alert kind="success" title="Alle Stunden wurden verplant." />
      )}
      {warnings.length > 0 && (
        <details className="disclosure">
          <summary>{plural(warnings.length, 'Hinweis', 'Hinweise')}</summary>
          <ul className="warning-list small">
            {warnings.slice(0, 100).map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

/** Kurse erzeugen, Lehrkräfte zuweisen, Stundenplan generieren (Fortschritt live) und übernehmen. */
export function GeneratorPanel({ canEdit, canGenerate }: { canEdit: boolean; canGenerate: boolean }) {
  const toast = useToast();
  const [prep, setPrep] = useState<{ title: string; res: WarningsResponse } | null>(null);
  const [timeLimit, setTimeLimit] = useState(60);
  const [keepLocked, setKeepLocked] = useState(true);
  const [seed, setSeed] = useState(1);
  const [workers, setWorkers] = useState(0);
  const [variants, setVariants] = useState(1);
  const [job, setJob] = useState<Job | null>(null);
  const [otherJob, setOtherJob] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);
  const genRef = useRef<HTMLElement | null>(null);
  const [rebuilt, setRebuilt] = useState<RebuildResult | null>(null);
  const planPeriod = usePlanPeriod(!!job && RUNNING.has(job.status));

  const refreshJob = useCallback(async (id: string) => {
    try {
      const j = await planning.job(id);
      setJob(j);
      return j;
    } catch {
      return null;
    }
  }, []);

  // laufenden/letzten Job nach Neuladen der Seite wieder aufnehmen
  useEffect(() => {
    if (!canGenerate) return;
    planning
      .jobs()
      .then((jobs) => {
        const sorted = jobs.slice().sort((a, b) => String(b.created_at ?? b.started_at ?? '').localeCompare(String(a.created_at ?? a.started_at ?? '')));
        // Neuplanungen einzelner Lehrkräfte gehören zur Seite „Anträge von Lehrkräften“
        const replan = sorted.find((x) => x.kind === 'replan_teacher' && RUNNING.has(x.status));
        setOtherJob(replan ? String((replan as Job & { params?: { teacher_name?: string } }).params?.teacher_name ?? '') || 'eine Lehrkraft' : null);
        // Läufe der Plan-Prüfung gehören zu den Vorschlägen (Tab „Plan prüfen“)
        const own = sorted.filter((x) => x.kind !== 'replan_teacher' && x.kind !== 'autoplan' && x.kind !== 'proposal');
        const j = own.find((x) => RUNNING.has(x.status)) ?? own.find((x) => x.status === 'done');
        if (j) void refreshJob(j.id);
      })
      .catch(() => undefined);
  }, [canGenerate, refreshJob]);

  // Polling als Rückfallebene zu SSE
  useEffect(() => {
    if (!job || !RUNNING.has(job.status)) return undefined;
    pollRef.current = window.setInterval(() => void refreshJob(job.id), 2500);
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [job?.id, job?.status, refreshJob]); // eslint-disable-line react-hooks/exhaustive-deps

  useJobEvents(job?.id ?? null, (ev) => {
    setJob((j) => (j && j.id === ev.id ? { ...j, status: ev.status, progress: ev.progress, message: ev.message } : j));
    if (!RUNNING.has(ev.status)) void refreshJob(ev.id);
  });

  const start = async () => {
    try {
      const r = await genApi.generate({ time_limit: timeLimit, keep_locked: keepLocked, seed, workers, variants, ...planPeriod.params });
      setJob(r.job ?? { id: r.job_id, status: 'queued', progress: 0, message: 'Gestartet' });
      toast.info('Generierung gestartet');
    } catch (e) {
      toast.error(e, 'Generator');
    }
  };

  const running = !!job && RUNNING.has(job.status);
  const etaText = running && job ? `ca. ${Math.max(0, Math.round(timeLimit * (1 - job.progress)))} s verbleibend` : '';

  return (
    <div className="stack">
      {canEdit && (
        <section className="card">
          <h2>1. Vorbereitung</h2>
          <div className="row" style={{ marginTop: 12, flexWrap: 'wrap' }}>
            <RebuildCourses
              onDone={(r) => {
                setRebuilt(r);
                if (r) setPrep(null);
              }}
            />
            <AsyncButton
              className="btn"
              onClick={async () => {
                try {
                  const res = await planning.assignTeachers();
                  setPrep({ title: 'Lehrkräfte zugewiesen', res });
                  invalidate('courses');
                } catch (e) {
                  toast.error(e);
                }
              }}
            >
              <Icon name="users" /> Lehrkräfte zuweisen
            </AsyncButton>
          </div>
          {rebuilt && (
            <div style={{ marginTop: 12 }}>
              <RebuildResultView
                result={rebuilt}
                onReplan={
                  canGenerate
                    ? () => {
                        genRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        if (!running) void start();
                      }
                    : undefined
                }
              />
            </div>
          )}
          {prep && (
            <div style={{ marginTop: 12 }}>
              <WarningsBox title={prep.title} res={prep.res} />
            </div>
          )}
        </section>
      )}

      {canGenerate && (
        <section className="card" ref={genRef}>
          <h2>
            2. Stundenplan berechnen{' '}
            <HelpTip label="Erklärung: Stundenplan berechnen">
              Der Generator verteilt alle Kurse unter Beachtung harter Regeln (keine Doppelbelegung, Sperrzeiten und Rhythmus, Fachräume, Wegezeiten) und optimiert die weichen Ziele aus „Prioritäten & Regeln“. Mehr Rechenzeit ergibt meist weniger Hohl- und Springstunden. Der Entwurf ersetzt den aktuellen Plan erst nach „Übernehmen“.
            </HelpTip>
          </h2>
          <div className="form-grid" style={{ marginTop: 12 }}>
            <div className="field span-all">
              <label htmlFor="gen-time">
                Rechenzeit: <strong>{timeLimit} s</strong> ({(timeLimit / 60).toLocaleString('de-DE', { maximumFractionDigits: 1 })} min){' '}
                <HelpTip label="Erklärung: Rechenzeit">30 bis 120 Sekunden genügen für schnelle Entwürfe, 180 bis 300 Sekunden für den endgültigen Plan.</HelpTip>
              </label>
              <input id="gen-time" type="range" min={10} max={300} step={10} value={timeLimit} disabled={running} onChange={(e) => setTimeLimit(Number(e.target.value))} />
            </div>
            <div className="field">
              <span className="field-label">Fixierte Stunden</span>
              <label className="check">
                <input type="checkbox" checked={keepLocked} disabled={running} onChange={(e) => setKeepLocked(e.target.checked)} /> beibehalten
              </label>
            </div>
            <Field label="Startwert (Seed)" htmlFor="gen-seed" hint="Anderer Wert = andere Lösungsvariante">
              <input id="gen-seed" type="number" min={0} value={seed} disabled={running} onChange={(e) => setSeed(Math.max(0, parseInt(e.target.value || '0', 10)))} />
            </Field>
            <Field label="Parallele Läufe" htmlFor="gen-workers" hint="0 = automatisch (CPU-Kerne)">
              <input id="gen-workers" type="number" min={0} max={16} value={workers} disabled={running} onChange={(e) => setWorkers(Math.max(0, Math.min(16, parseInt(e.target.value || '0', 10))))} />
            </Field>
            {planPeriod.node}
            <Field label="Varianten" htmlFor="gen-variants" help="Jede Variante rechnet nacheinander mit einem anderen Startwert und der eingestellten Rechenzeit. Anschließend vergleichen Sie die Ergebnisse. Bis zu 5.">
              <input id="gen-variants" type="number" min={1} max={5} value={variants} disabled={running} onChange={(e) => setVariants(Math.max(1, Math.min(5, parseInt(e.target.value || '1', 10))))} />
            </Field>
          </div>
          {otherJob && !running && (
            <Alert kind="info" title="Neuplanung läuft">
              Gerade wird der Stundenplan für {otherJob} neu geplant (Seite „Anträge von Lehrkräften“). Ein neuer Lauf ist erst danach möglich.
            </Alert>
          )}
          <div className="row" style={{ marginTop: 12 }}>
            <AsyncButton className="btn btn-primary" onClick={start} disabled={running || !planPeriod.ready}>
              <Icon name="play" /> Generieren
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
            <ClearPlanButton disabled={running} period={planPeriod.period} />
          </div>

          {job && (
            <div className="stack" style={{ marginTop: 16 }}>
              <ProgressBar value={job.progress} label={`${job.message || job.status}${etaText ? ` – ${etaText}` : ''}`} />
              <p className="xsmall muted">
                Job {job.id} · Status: {job.status}
                {job.finished_at ? ` · fertig ${formatDateTime(job.finished_at)}` : ''}
              </p>
              {(job as Job & { params?: { rules_preview?: boolean } }).params?.rules_preview && (
                <Alert kind="info" title="Probelauf mit geänderten Regeln">
                  Dieser Entwurf wurde im Tab „Regeln“ mit dort geänderten Regeln gerechnet. Übernehmen Sie ihn nur, wenn Sie diese Regeln auch gespeichert haben –
                  sonst rechnet die automatische Neuplanung später mit den alten Regeln.
                </Alert>
              )}
              <PeriodJobNote params={(job as Job & { params?: { period?: string; copy_from?: string } }).params} periods={planPeriod.periods} />
              {job.status === 'failed' && <Alert kind="error" title="Generierung fehlgeschlagen">{job.error ?? job.message}</Alert>}
              {job.status === 'cancelled' && <Alert kind="info">Die Generierung wurde abgebrochen.</Alert>}
              {(job.status === 'done' || job.status === 'applied') && (
                <>
                  <h3>Ergebnis</h3>
                  {job.outdated && (
                    <Alert kind="warning" title="Planungsdaten wurden inzwischen geändert">
                      Der Entwurf basiert auf einem älteren Stand. Beim Übernehmen gehen zwischenzeitliche Stundenplan-Änderungen verloren – ggf. neu generieren.
                    </Alert>
                  )}
                  <GeneratorResult job={job as unknown as GenJob} periods={planPeriod.periods} onApplied={() => void refreshJob(job.id)} legacy={<JobResult job={job} />} />
                </>
              )}
            </div>
          )}
        </section>
      )}
      {canGenerate && <SnapshotsPanel />}
    </div>
  );
}

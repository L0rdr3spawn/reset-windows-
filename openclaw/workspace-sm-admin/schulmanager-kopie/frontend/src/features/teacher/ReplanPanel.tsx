/**
 * „Stundenplan für diese Lehrkraft neu planen“ (§9.3, dynamische Anpassung): startet einen Generator-Job, bei dem
 * alle übrigen Stunden fixiert bleiben, zeigt den Fortschritt live und übernimmt den Entwurf auf Wunsch.
 */
import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { Icon } from '../../components/Icon';
import { HelpTip } from '../../components/HelpTip';
import { Alert, AsyncButton, Field, ProgressBar } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { invalidate } from '../../hooks/useCollection';
import { useJobEvents } from '../../hooks/useLive';
import { formatDateTime } from '../../lib/dates';
import { replanApi } from './api';
import { JOB_RUNNING, pickReplanJob } from './replan';
import type { ReplanJob } from './types';

const RUNNING = JOB_RUNNING;

export function ReplanPanel({ teacherId, teacherName, outsideCount = 0 }: { teacherId: string; teacherName: string; outsideCount?: number }) {
  const toast = useToast();
  const id = useId();
  const [timeLimit, setTimeLimit] = useState(15);
  const [scope, setScope] = useState<'teacher' | 'classes'>('teacher');
  const [job, setJob] = useState<ReplanJob | null>(null);
  const poll = useRef<number | null>(null);

  const refresh = useCallback(async (jobId: string) => {
    try {
      const j = await replanApi.job(jobId);
      setJob(j);
      return j;
    } catch {
      return null;
    }
  }, []);

  // laufenden/fertigen Entwurf dieser Lehrkraft nach Neuladen wieder aufnehmen
  useEffect(() => {
    let alive = true;
    setJob(null);
    replanApi
      .jobs()
      .then((jobs) => {
        const j = pickReplanJob(jobs, teacherId);
        if (alive && j) void refresh(j.id);
      })
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, [teacherId, refresh]);

  // Polling als Rückfallebene zu SSE
  useEffect(() => {
    if (!job || !RUNNING.has(job.status)) return undefined;
    poll.current = window.setInterval(() => void refresh(job.id), 2500);
    return () => {
      if (poll.current) window.clearInterval(poll.current);
    };
  }, [job?.id, job?.status, refresh]); // eslint-disable-line react-hooks/exhaustive-deps

  useJobEvents(job?.id ?? null, (ev) => {
    setJob((j) => (j && j.id === ev.id ? { ...j, status: ev.status, progress: ev.progress, message: ev.message } : j));
    if (!RUNNING.has(ev.status)) void refresh(ev.id);
  });

  const running = !!job && RUNNING.has(job.status);
  const start = async () => {
    try {
      const r = await replanApi.start(teacherId, { time_limit: timeLimit, scope });
      setJob(r.job ?? ({ id: r.job_id, status: 'queued', progress: 0, message: 'Gestartet' } as ReplanJob));
      toast.info(`Neuplanung für ${teacherName} gestartet`);
    } catch (e) {
      toast.error(e, 'Neuplanung');
    }
  };

  const stats = job?.stats ?? {};
  const changes = job?.changes ?? [];
  const unplaced = job?.unplaced ?? [];
  const warnings = job?.warnings ?? [];

  return (
    <section className="card stack" aria-labelledby={`${id}-h`}>
      <h3 id={`${id}-h`} style={{ margin: 0 }}>
        Stundenplan für diese Lehrkraft neu planen
        <HelpTip>
          Der Generator plant nur die Stunden von {teacherName} neu (auf Wunsch auch die übrigen Stunden ihrer Klassen); alle anderen Stunden bleiben fest. Neue Zeitfenster und Sperrzeiten gelten dabei als harte Regeln. Der Entwurf ändert den Plan
          erst nach „Übernehmen“.
        </HelpTip>
      </h3>
      {outsideCount > 0 && (
        <Alert kind="warning">
          {outsideCount} {outsideCount === 1 ? 'Unterrichtsblock liegt' : 'Unterrichtsblöcke liegen'} außerhalb der Zeitfenster – eine Neuplanung wird empfohlen.
        </Alert>
      )}
      <div className="form-grid">
        <div className="field">
          <label htmlFor={`${id}-t`}>
            Rechenzeit: <strong>{timeLimit} s</strong>
          </label>
          <input id={`${id}-t`} type="range" min={5} max={120} step={5} value={timeLimit} disabled={running} onChange={(e) => setTimeLimit(Number(e.target.value))} />
        </div>
        <Field label="Umfang" htmlFor={`${id}-s`} hint="Mehr Spielraum = bessere Lösung, aber mehr geänderte Stunden">
          <select id={`${id}-s`} value={scope} disabled={running} onChange={(e) => setScope(e.target.value === 'classes' ? 'classes' : 'teacher')}>
            <option value="teacher">nur Stunden dieser Lehrkraft</option>
            <option value="classes">auch übrige Stunden ihrer Klassen</option>
          </select>
        </Field>
      </div>
      <div className="row">
        <AsyncButton className="btn btn-primary" onClick={start} disabled={running}>
          <Icon name="sparkles" /> Neu planen
        </AsyncButton>
        {running && job && (
          <AsyncButton
            className="btn"
            onClick={async () => {
              try {
                setJob(await replanApi.cancel(job.id));
              } catch (e) {
                toast.error(e);
              }
            }}
          >
            <Icon name="stop" /> Abbrechen
          </AsyncButton>
        )}
      </div>
      {job && (
        <div className="stack-sm" aria-live="polite">
          <ProgressBar value={job.progress} label={job.message || job.status} />
          <p className="xsmall muted" style={{ margin: 0 }}>
            Job {job.id} · {job.status}
            {job.finished_at ? ` · fertig ${formatDateTime(job.finished_at)}` : ''}
          </p>
          {job.status === 'failed' && <Alert kind="error" title="Neuplanung fehlgeschlagen">{job.error ?? job.message}</Alert>}
          {job.status === 'cancelled' && <Alert kind="info">Die Neuplanung wurde abgebrochen.</Alert>}
          {(job.status === 'done' || job.status === 'applied') && (
            <>
              <div className="grid grid-3">
                <div className="card kpi">
                  <span className="kpi-value">{Number(stats.moved ?? 0)}</span>
                  <span className="kpi-label">verlegte Blöcke</span>
                </div>
                <div className="card kpi">
                  <span className="kpi-value">{Number(stats.changed_courses ?? changes.length)}</span>
                  <span className="kpi-label">geänderte Kurse</span>
                </div>
                <div className={`card kpi${unplaced.length ? ' bad' : ' good'}`}>
                  <span className="kpi-value">{unplaced.length}</span>
                  <span className="kpi-label">nicht verplant</span>
                </div>
              </div>
              {changes.length > 0 ? (
                <details className="disclosure" open={changes.length <= 8}>
                  <summary>{changes.length} Änderungen anzeigen</summary>
                  <ul className="small tp-changes">
                    {changes.map((c) => (
                      <li key={c.course_id}>
                        <strong>{c.classes.join(', ') || c.course_id}</strong> · {c.label}: {c.from.length ? c.from.join(', ') : '–'} → {c.to.length ? c.to.join(', ') : '–'}
                      </li>
                    ))}
                  </ul>
                </details>
              ) : (
                <p className="small muted">Der Generator hat keine bessere Lage gefunden – der Plan bleibt unverändert.</p>
              )}
              {unplaced.length > 0 && (
                <Alert kind="warning" title={`${unplaced.length} Einheiten ließen sich nicht verplanen`}>
                  Bitte Zeitfenster, Sperrzeiten oder Deputat prüfen – oder mit größerem Umfang erneut planen.
                </Alert>
              )}
              {warnings.length > 0 && (
                <details className="disclosure">
                  <summary>{warnings.length} Hinweise</summary>
                  <ul className="warning-list small">
                    {warnings.slice(0, 50).map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                </details>
              )}
              {job.status === 'done' ? (
                <div className="row">
                  <AsyncButton
                    className="btn btn-primary"
                    disabled={changes.length === 0}
                    confirm={`Neuen Plan für ${teacherName} übernehmen? (Rückgängig über „Verlauf“ möglich)`}
                    onClick={async () => {
                      try {
                        const r = await replanApi.apply(job.id);
                        toast.success(`Neuer Stundenplan für ${teacherName} übernommen (${r.lessons} Blöcke)`);
                        invalidate('courses');
                        await refresh(job.id);
                      } catch (e) {
                        toast.error(e, 'Übernehmen');
                      }
                    }}
                  >
                    <Icon name="check" /> Übernehmen
                  </AsyncButton>
                </div>
              ) : (
                <Alert kind="success">Dieser Entwurf wurde übernommen.</Alert>
              )}
            </>
          )}
        </div>
      )}
    </section>
  );
}

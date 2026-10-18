/**
 * Planung › „Zeitraster & Schuljahr“ › Planzeiträume: je Zeitraum (z. B. 1. und 2. Halbjahr) ein eigener Stundenplan.
 * Zeiträume anlegen, umbenennen, Grenzen ändern, löschen (mit Plan nur nach Bestätigung); Überblick, welcher Zeitraum
 * einen Plan hat; Plan aus einem anderen Zeitraum übernehmen oder leeren. Der Generator rechnet je Zeitraum
 * (`GeneratorPanel`), Ansichten zeigen in Wochen ohne Plan einen Hinweis (`components/PlanNotice`).
 * Serverseite: `schulmanager/plan_periods.py`, `PUT /calendar/plan-periods`.
 */
import { useEffect, useMemo, useState } from 'react';
import { calendar } from '../../api/endpoints';
import type { PlanPeriod, PlanPeriodsResponse } from '../../api/types';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Alert, AsyncButton, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { invalidate } from '../../hooks/useCollection';
import { addDays } from '../../lib/dates';
import { periodErrors, periodSpan, removedWithPlan, rowsBody, sameRows, toRows, type PeriodRow } from '../../lib/planPeriods';

type Adopt = 'all' | 'none' | string;

function PlanBadge({ p }: { p: Pick<PlanPeriod, 'has_plan' | 'lessons'> }) {
  return p.has_plan ? (
    <span className="badge badge-success">Stundenplan vorhanden{p.lessons ? ` (${p.lessons} Blöcke)` : ''}</span>
  ) : (
    <span className="badge badge-warning">Noch kein Stundenplan</span>
  );
}

export function PlanPeriodsPanel({ canEdit, canPlan }: { canEdit: boolean; canPlan: boolean }) {
  const toast = useToast();
  const q = useApi<PlanPeriodsResponse>((signal) => calendar.planPeriods(signal), [], { live: ['settings', 'timetable'] });
  const data = q.data;
  const base = useMemo(() => (data ? toRows(data.active ? data.periods : data.suggested) : []), [data]);
  const [rows, setRows] = useState<PeriodRow[]>([]);
  const [dirty, setDirty] = useState(false);
  const [adopt, setAdopt] = useState<Adopt>('all');
  const [from, setFrom] = useState<Record<string, string>>({});
  useEffect(() => {
    if (data && !dirty) setRows(structuredClone(base));
  }, [data, base, dirty]);
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!data) return <Loading />;

  const active = data.active;
  const saved = data.periods;
  const errors = periodErrors(rows);
  const removed = active ? removedWithPlan(saved, rows) : [];
  const changed = !sameRows(rows, base) || !active;
  const edit = (i: number, patch: Partial<PeriodRow>) => {
    setRows((r) => r.map((x, j) => (j === i ? { ...x, ...patch } : x)));
    setDirty(true);
  };
  const add = () => {
    const last = rows[rows.length - 1];
    const start = last?.date_to ? addDays(last.date_to, 1) : '';
    setRows((r) => [...r, { name: `Zeitraum ${r.length + 1}`, date_from: start, date_to: start ? addDays(start, 83) : '' }]);
    setDirty(true);
  };
  const remove = (i: number) => {
    setRows((r) => r.filter((_, j) => j !== i));
    setDirty(true);
  };
  const reset = () => {
    setRows(structuredClone(base));
    setDirty(false);
  };
  const done = (r: PlanPeriodsResponse) => {
    q.setData(r);
    setDirty(false);
    invalidate('settings');
  };
  const save = async () => {
    if (errors.length) {
      toast.warning('Bitte die Eingaben prüfen', errors);
      return;
    }
    try {
      const r = await calendar.savePlanPeriods({ periods: rowsBody(rows), adopt: active ? undefined : adopt, confirm_delete: removed.length > 0 });
      done(r);
      toast.success(active ? 'Zeiträume gespeichert' : 'Zeiträume eingerichtet');
    } catch (e) {
      toast.error(e, 'Speichern');
    }
  };
  const copy = async (to: PlanPeriod) => {
    const src = from[to.id];
    if (!src) return;
    try {
      const r = await calendar.copyPlanPeriod(to.id, src, to.has_plan);
      done(r);
      toast.success(`${r.copied} Blöcke übernommen${r.skipped ? `, ${r.skipped} ohne passende Wochen ausgelassen` : ''}`);
    } catch (e) {
      toast.error(e, 'Plan übernehmen');
    }
  };
  const clear = async (p: PlanPeriod) => {
    try {
      const r = await calendar.clearPlanPeriod(p.id);
      done(r);
      toast.success(`Plan von ${p.name} geleert`);
    } catch (e) {
      toast.error(e, 'Plan leeren');
    }
  };

  return (
    <section className="card stack-sm" aria-labelledby="pp-head">
      <h2 id="pp-head">
        Planzeiträume{' '}
        <HelpTip>
          Jeder Zeitraum hat einen eigenen Stundenplan, zum Beispiel je Halbjahr. Der Generator rechnet für einen Zeitraum, Ansichten zeigen nur den Plan, der in der Woche gilt. Zeiträume umfassen ganze Wochen und dürfen
          sich nicht überschneiden. Ohne Zeiträume gilt ein Plan für das ganze Schuljahr.
        </HelpTip>
      </h2>
      {!active && (
        <Alert kind="info" title="Noch keine Zeiträume eingerichtet">
          Der Stundenplan gilt für das ganze Schuljahr.
        </Alert>
      )}
      {rows.map((r, i) => {
        const p = active && r.id ? saved.find((x) => x.id === r.id) : undefined;
        const others = saved.filter((x) => x.id !== r.id && x.lessons > 0);
        return (
          <div key={r.id ?? `neu-${i}`} className="stack-sm" role="group" aria-label={r.name || `Zeitraum ${i + 1}`}>
            <div className="row" style={{ alignItems: 'flex-end' }}>
              <Field label="Name" htmlFor={`pp-n-${i}`} className="grow">
                <input id={`pp-n-${i}`} type="text" value={r.name} maxLength={60} disabled={!canEdit} onChange={(e) => edit(i, { name: e.target.value })} />
              </Field>
              <Field label="Beginn" htmlFor={`pp-a-${i}`}>
                <input id={`pp-a-${i}`} type="date" value={r.date_from} disabled={!canEdit} onChange={(e) => edit(i, { date_from: e.target.value })} />
              </Field>
              <Field label="Ende" htmlFor={`pp-b-${i}`}>
                <input id={`pp-b-${i}`} type="date" value={r.date_to} disabled={!canEdit} onChange={(e) => edit(i, { date_to: e.target.value })} />
              </Field>
              {canEdit && rows.length > 1 && (
                <button type="button" className="btn btn-ghost btn-icon" onClick={() => remove(i)} aria-label={`${r.name || 'Zeitraum'} entfernen`}>
                  <Icon name="trash" />
                </button>
              )}
            </div>
            {p && (
              <div className="row">
                <PlanBadge p={p} />
                <span className="small muted">{periodSpan(p)}</span>
                {canPlan && others.length > 0 && (
                  <>
                    <label className="sr-only" htmlFor={`pp-c-${i}`}>
                      Plan übernehmen aus
                    </label>
                    <select id={`pp-c-${i}`} value={from[p.id] ?? ''} onChange={(e) => setFrom((f) => ({ ...f, [p.id]: e.target.value }))}>
                      <option value="">Plan übernehmen aus …</option>
                      {others.map((o) => (
                        <option key={o.id} value={o.id}>
                          {o.name}
                        </option>
                      ))}
                    </select>
                    <AsyncButton
                      className="btn btn-sm"
                      disabled={!from[p.id] || dirty}
                      confirm={p.has_plan ? `Der bisherige Plan von ${p.name} wird ersetzt. Fortfahren?` : undefined}
                      onClick={() => copy(p)}
                    >
                      Übernehmen
                    </AsyncButton>
                  </>
                )}
                {canPlan && p.lessons > 0 && (
                  <AsyncButton className="btn btn-sm" confirm={`Den Stundenplan von ${p.name} leeren? Die ${p.lessons} Blöcke werden entfernt.`} confirmLabel="Plan leeren" disabled={dirty} onClick={() => clear(p)}>
                    Plan leeren
                  </AsyncButton>
                )}
              </div>
            )}
          </div>
        );
      })}
      {!active && canEdit && (
        <Field label="Bisheriger Plan" htmlFor="pp-adopt" help="Der vorhandene Stundenplan wird beim Einrichten übernommen: in jeden Zeitraum (jeder Zeitraum behält danach seinen eigenen Plan) oder nur in einen.">
          <select id="pp-adopt" value={adopt} onChange={(e) => setAdopt(e.target.value)}>
            <option value="all">In jeden Zeitraum übernehmen</option>
            {rows.map((r) => (
              <option key={r.id ?? r.name} value={r.id ?? ''} disabled={!r.id}>
                Nur in {r.name || 'Zeitraum'}
              </option>
            ))}
            <option value="none">Ohne Zeitraum belassen (gilt überall)</option>
          </select>
        </Field>
      )}
      {errors.length > 0 && dirty && (
        <Alert kind="warning" title="Bitte die Eingaben prüfen">
          <ul>
            {errors.map((e) => (
              <li key={e}>{e}</li>
            ))}
          </ul>
        </Alert>
      )}
      {canEdit && (
        <div className="row-end">
          <button type="button" className="btn btn-sm" onClick={add} disabled={rows.length >= 12}>
            <Icon name="plus" /> Zeitraum hinzufügen
          </button>
          {dirty && (
            <button type="button" className="btn btn-sm" onClick={reset}>
              Verwerfen
            </button>
          )}
          <AsyncButton
            className="btn btn-primary btn-sm"
            disabled={!changed || errors.length > 0}
            confirm={removed.length ? `Der Stundenplan von ${removed.map((p) => p.name).join(', ')} wird mit dem Zeitraum gelöscht. Fortfahren?` : undefined}
            confirmLabel="Löschen"
            onClick={save}
          >
            {active ? 'Zeiträume speichern' : 'Zeiträume einrichten'}
          </AsyncButton>
        </div>
      )}
    </section>
  );
}

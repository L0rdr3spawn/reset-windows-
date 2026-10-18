/** Lernplan / Wochenplan einer Schülerin/eines Schülers: Ziele aus dem Raster, Woche, Fälligkeit, Status. */
import { useState } from 'react';
import { AsyncButton, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { formatDate, mondayOf, todayISO } from '../../lib/dates';
import { compApi, type Plan, type PlanStatus } from './api';
import { groupPlans, planProgress, STATUS_LABEL, weekRangeText } from './logic';

export interface CompetencyOption {
  id: number;
  title: string;
  area: string;
  framework: string;
}

const STATUSES: PlanStatus[] = ['offen', 'in_arbeit', 'erledigt'];

export function PlanView({ studentId, options, pupil }: { studentId: string; options: CompetencyOption[]; pupil: boolean }) {
  const toast = useToast();
  const q = useApi((signal) => compApi.plans(studentId, signal), [studentId], { live: ['competency'] });
  const [title, setTitle] = useState('');
  const [competency, setCompetency] = useState('');
  const [week, setWeek] = useState<string>('');
  const [due, setDue] = useState('');
  const [note, setNote] = useState('');
  const data = q.data;
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!data) return <Loading />;
  const canAdd = data.kind === 'self' || (data.kind === 'staff' && data.can_assess);
  const prog = planProgress(data.plans);
  const groups = groupPlans(data.plans, data.current_week);
  const weekValue = week || data.current_week;
  const byArea = new Map<string, CompetencyOption[]>();
  for (const o of options) byArea.set(`${o.framework}: ${o.area}`, [...(byArea.get(`${o.framework}: ${o.area}`) ?? []), o]);

  const add = async () => {
    const compId = competency ? Number(competency) : null;
    if (!title.trim() && compId === null) {
      toast.warning('Bitte ein Ziel eintragen oder eine Kompetenz wählen.');
      return;
    }
    await compApi.createPlans({ student_id: studentId, competency_id: compId, title: title.trim(), note: note.trim(), week_start: weekValue === 'none' ? null : mondayOf(weekValue), due_date: due || null });
    setTitle('');
    setCompetency('');
    setNote('');
    setDue('');
    toast.success('Ziel hinzugefügt');
    q.reload();
  };

  const patch = async (p: Plan, status: PlanStatus) => {
    await compApi.patchPlan(p.id, { status });
    q.reload();
  };

  return (
    <div className="stack">
      <div className="row-between">
        <h3 className="cp-h">{pupil ? 'Mein Wochenplan' : 'Lernplan'}</h3>
        <span className="small">
          {prog.done} von {prog.total} erledigt
        </span>
      </div>
      {canAdd && (
        <form
          className="card cp-plan-form"
          onSubmit={(e) => {
            e.preventDefault();
          }}
        >
          <Field label="Ziel" htmlFor="cp-pl-title" help="Ohne Text wird die Kompetenz als Ziel übernommen.">
            <input id="cp-pl-title" value={title} maxLength={300} onChange={(e) => setTitle(e.target.value)} />
          </Field>
          <Field label="Kompetenz" htmlFor="cp-pl-comp" help="Verknüpft das Ziel mit dem Kompetenzraster.">
            <select id="cp-pl-comp" value={competency} onChange={(e) => setCompetency(e.target.value)}>
              <option value="">Keine</option>
              {[...byArea.entries()].map(([group, items]) => (
                <optgroup key={group} label={group}>
                  {items.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.title}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </Field>
          <Field label="Woche" htmlFor="cp-pl-week" help="Die Woche, in der das Ziel bearbeitet wird (Montag). Leer lassen für „ohne feste Woche“.">
            <input id="cp-pl-week" type="date" value={week === 'none' ? '' : weekValue} onChange={(e) => setWeek(e.target.value || 'none')} />
          </Field>
          <Field label="Fällig bis" htmlFor="cp-pl-due">
            <input id="cp-pl-due" type="date" value={due} onChange={(e) => setDue(e.target.value)} />
          </Field>
          <Field label="Notiz" htmlFor="cp-pl-note">
            <input id="cp-pl-note" value={note} maxLength={1000} onChange={(e) => setNote(e.target.value)} />
          </Field>
          <div className="cp-plan-add">
            <AsyncButton className="btn btn-primary" onClick={add}>
              Hinzufügen
            </AsyncButton>
          </div>
        </form>
      )}
      {!groups.length && <p className="muted">{pupil ? 'In Ihrem Wochenplan steht noch nichts.' : 'Noch keine Ziele im Lernplan.'}</p>}
      {groups.map((g) => (
        <section key={g.key} aria-label={g.title} className="card">
          <h4 className="cp-h">
            {g.title}
            {g.key === 'diese' && <span className="small muted"> · {weekRangeText(data.current_week)}</span>}
          </h4>
          <ul className="cp-plans">
            {g.plans.map((p) => (
              <li key={p.id} className={`cp-plan cp-plan-${p.status}`}>
                <div className="cp-plan-main">
                  <span className="cp-title">{p.title}</span>
                  {p.competency_title && p.competency_title !== p.title && <span className="small muted"> · {p.competency_title}</span>}
                  {p.note && <div className="small muted">{p.note}</div>}
                  <div className="xsmall muted">
                    {p.week_start && g.key !== 'diese' ? `Woche ${weekRangeText(p.week_start)}` : null}
                    {p.due_date ? `${p.week_start && g.key !== 'diese' ? ' · ' : ''}fällig ${formatDate(p.due_date)}` : null}
                    {p.source === 'schueler' && data.kind !== 'self' ? ' · selbst eingetragen' : ''}
                  </div>
                </div>
                <div className="cp-plan-side">
                  {p.overdue && <span className="badge badge-danger">Überfällig</span>}
                  {p.due_date && !p.overdue && p.status !== 'erledigt' && p.due_date <= todayISO() && <span className="badge badge-warning">Heute</span>}
                  <select aria-label={`Status: ${p.title}`} value={p.status} disabled={!p.can_status} onChange={(e) => void patch(p, e.target.value as PlanStatus)}>
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {STATUS_LABEL[s]}
                      </option>
                    ))}
                  </select>
                  {p.can_edit && (
                    <AsyncButton
                      className="btn btn-sm"
                      confirm="Dieses Ziel löschen?"
                      onClick={async () => {
                        await compApi.deletePlan(p.id);
                        q.reload();
                      }}
                    >
                      Löschen
                    </AsyncButton>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

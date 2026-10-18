/**
 * Planzeiträume: Hinweis „Für diesen Zeitraum ist noch kein Stundenplan festgelegt“ (mit Zeitraum und, für Planende,
 * einem Knopf zum Generator) und die Kennzeichen des Zeitraums in der Wochennavigation. Die Felder des Rasters
 * selbst kommen über `lib/planPeriods.ts` (`noPlanBlocked`) in `DayPeriodGrid`/`TimetableGrid`.
 */
import { Link } from 'react-router-dom';
import type { PlanState } from '../api/types';
import { useUser } from '../context/AuthContext';
import { can } from '../lib/permissions';
import { noPlanDetail, noPlanTitle, periodEdge, planMissing } from '../lib/planPeriods';
import { Alert } from './ui';

export function NoPlanNotice({ plan }: { plan: PlanState | null | undefined }) {
  const user = useUser();
  if (!planMissing(plan)) return null;
  const detail = noPlanDetail(plan);
  const planner = can(user, 'timetable.generate');
  const to = plan?.period ? `/planung/generator?zeitraum=${encodeURIComponent(plan.period.id)}` : '/planung/zeitraster';
  return (
    <Alert
      kind="info"
      title={noPlanTitle(plan)}
      action={
        planner || can(user, 'settings.edit') ? (
          <Link className="btn btn-sm" to={planner ? to : '/planung/zeitraster'}>
            {planner ? 'Zum Generator' : 'Zeiträume'}
          </Link>
        ) : undefined
      }
    >
      {detail || undefined}
    </Alert>
  );
}

/** Zeitraum der Woche, Beginn/Ende des Zeitraums und „kein Plan“ als kleine Abzeichen neben dem Wochentext */
export function PlanBadges({ plan, weekStart }: { plan: PlanState | null | undefined; weekStart: string }) {
  if (!plan?.active) return null;
  const edge = periodEdge(plan, weekStart);
  const name = plan.period?.name;
  return (
    <>
      {name && <span className="badge">{name}</span>}
      {edge === 'start' && name && <span className="badge badge-info">Beginn {name}</span>}
      {edge === 'end' && name && <span className="badge badge-info">Ende {name}</span>}
      {planMissing(plan) && <span className="badge badge-warning">Kein Stundenplan</span>}
    </>
  );
}

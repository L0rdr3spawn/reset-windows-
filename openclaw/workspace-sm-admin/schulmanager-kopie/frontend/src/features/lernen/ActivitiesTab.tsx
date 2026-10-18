/**
 * Kursraum-Bereich „Tests & Umfragen“: Abstimmungen, Umfragen, Selbsttests und (für Lehrende) die Fragensammlung.
 * Der Unterbereich steht in der Adresse (`?tab=tests&bereich=selbsttests`).
 */
import { lazy, Suspense } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Loading, SegmentedControl } from '../../components/ui';
import type { ChannelDetail } from '../channels/types';
import './lernen.css';

const PollsPanel = lazy(() => import('./PollsPanel'));
const SurveysPanel = lazy(() => import('./SurveysPanel'));
const SelftestsPanel = lazy(() => import('./SelftestsPanel'));
const QuestionsPanel = lazy(() => import('./QuestionsPanel'));

export type Area = 'abstimmungen' | 'umfragen' | 'selbsttests' | 'fragen';

const LABELS: Record<Area, string> = { abstimmungen: 'Abstimmungen', umfragen: 'Umfragen', selbsttests: 'Selbsttests', fragen: 'Fragensammlung' };

/** Welche Unterbereiche sieht diese Rolle? Eltern: nur Abstimmungen (lesend). */
export function areasFor(role: string | null | undefined): Area[] {
  if (role === 'teacher') return ['selbsttests', 'umfragen', 'abstimmungen', 'fragen'];
  if (role === 'student') return ['selbsttests', 'umfragen', 'abstimmungen'];
  return ['abstimmungen'];
}

export default function ActivitiesTab({ detail }: { detail: ChannelDetail }) {
  const [params, setParams] = useSearchParams();
  const role = detail.channel.role;
  const areas = areasFor(role);
  const wanted = params.get('bereich') as Area | null;
  const area: Area = wanted && areas.includes(wanted) ? wanted : (areas[0] as Area);
  const id = detail.channel.id;
  const choose = (a: Area) => {
    const next = new URLSearchParams(params);
    next.set('bereich', a);
    setParams(next, { replace: true });
  };
  return (
    <div className="stack ln-tab">
      {areas.length > 1 && <SegmentedControl<Area> label="Bereich" value={area} onChange={choose} options={areas.map((a) => ({ value: a, label: LABELS[a] }))} />}
      <Suspense fallback={<Loading />}>
        {area === 'abstimmungen' && <PollsPanel channelId={id} childId={detail.child?.id} />}
        {area === 'umfragen' && <SurveysPanel channelId={id} student={role === 'student'} />}
        {area === 'selbsttests' && <SelftestsPanel channelId={id} student={role === 'student'} teacher={role === 'teacher'} />}
        {area === 'fragen' && <QuestionsPanel channelId={id} />}
      </Suspense>
    </div>
  );
}

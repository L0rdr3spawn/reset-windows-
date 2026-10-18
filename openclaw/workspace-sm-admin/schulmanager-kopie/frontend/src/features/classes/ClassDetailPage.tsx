/**
 * Klasse im Detail (`/klassen/:id`): Kopf (Raum/Klassenleitung inline änderbar) und Reiter
 * Wochenplan / Lehrkräfte / Schüler/innen / Stundentafel. Reiter und Datum stehen in der Adresse (`?tab=&datum=`).
 */
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { ApiError, errorMessage } from '../../api/client';
import { Icon } from '../../components/Icon';
import { FeatureBoundary } from '../../components/Layout';
import { Alert, ErrorBox, Loading, Tabs } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { useSettings } from '../../hooks/useCollection';
import { useTitle } from '../../hooks/misc';
import { currentSchoolDay, isValidISO } from '../../lib/dates';
import { schoolDaysOf } from '../../lib/weeks';
import { classesApi } from './api';
import { ClassHeader } from './ClassHeader';
import { useClassNames } from './components';
import { TeachersTab } from './PeopleTabs';
import { StudentsWithAccounts } from './StudentAccounts';
import { RegisterOverview } from './RegisterOverview';
import { WeekTab } from './WeekTab';
import { CurriculumTab } from './CurriculumTab';
import './classes.css';

type TabKey = 'wochenplan' | 'lehrkraefte' | 'schueler' | 'klassenbuch' | 'stundentafel';
const TABS: readonly TabKey[] = ['wochenplan', 'lehrkraefte', 'schueler', 'klassenbuch', 'stundentafel'];
const TAB_LABEL: Record<TabKey, string> = {
  wochenplan: 'Diese Woche',
  lehrkraefte: 'Lehrkräfte',
  schueler: 'Schüler/innen',
  klassenbuch: 'Klassenbuch',
  stundentafel: 'Stundentafel',
};

export default function ClassDetailPage() {
  const { id = '' } = useParams();
  const [params, setParams] = useSearchParams();
  const { data: settings } = useSettings();
  const q = useApi((signal) => classesApi.get(id, signal), [id], {
    live: ['classes', 'students', 'courses', 'rooms', 'teachers', 'timetable'],
    keepPrevious: true,
  });
  // beim Wechsel der Klasse keine alten Daten zeigen
  const detail = q.data && q.data.class.id === id ? q.data : undefined;
  const names = useClassNames(detail);
  useTitle(detail ? `Klasse ${detail.class.name}` : 'Klasse');

  const rawTab = params.get('tab') as TabKey | null;
  const showStudents = detail?.students !== null;
  const tab: TabKey = rawTab && TABS.includes(rawTab) && (rawTab !== 'schueler' || showStudents) ? rawTab : 'wochenplan';
  const rawDate = params.get('datum');
  const date = isValidISO(rawDate) ? rawDate : currentSchoolDay(new Date(), schoolDaysOf(settings));

  const setParam = (key: string, value: string | null) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
  };

  if (q.error && !detail) {
    const status = q.error instanceof ApiError ? q.error.status : 0;
    return (
      <div className="page stack kl-page">
        {status === 403 || status === 404 ? (
          <Alert kind="warning" title={status === 404 ? 'Klasse nicht gefunden' : 'Kein Zugriff auf diese Klasse'}>
            {errorMessage(q.error)} <Link to="/klassen">Zur Klassenliste</Link>
          </Alert>
        ) : (
          <ErrorBox error={q.error} onRetry={q.reload} />
        )}
      </div>
    );
  }
  if (!detail) return <Loading label="Klasse wird geladen …" />;
  const cls = detail.class;

  return (
    <div className="page stack kl-page">
      <div className="page-head">
        <div style={{ minWidth: 0 }}>
          <nav aria-label="Pfad" className="small">
            <Link to="/klassen">Klassen</Link> <span aria-hidden="true">›</span> <span className="muted">{cls.name}</span>
          </nav>
          <h1 className="kl-title">Klasse {cls.name}</h1>
        </div>
        <div className="row">
          <Link className="btn btn-sm" to="/klassen">
            <Icon name="chevronLeft" /> Alle Klassen
          </Link>
        </div>
      </div>

      <ClassHeader detail={detail} onSaved={q.reload} />

      <div>
        <Tabs<TabKey>
          label={`Bereiche der Klasse ${cls.name}`}
          active={tab}
          onChange={(t) => setParam('tab', t === 'wochenplan' ? null : t)}
          tabs={[
            { key: 'wochenplan', label: TAB_LABEL.wochenplan },
            { key: 'lehrkraefte', label: TAB_LABEL.lehrkraefte },
            { key: 'schueler', label: TAB_LABEL.schueler, hidden: !showStudents },
            { key: 'klassenbuch', label: TAB_LABEL.klassenbuch, hidden: !showStudents },
            { key: 'stundentafel', label: TAB_LABEL.stundentafel },
          ]}
        />
        <div role="tabpanel" aria-label={TAB_LABEL[tab]} className="kl-panel">
          <FeatureBoundary label={`klassen-${tab}`} resetKey={`${id}-${tab}`}>
            {tab === 'wochenplan' && <WeekTab detail={detail} names={names} date={date} onDate={(d) => setParam('datum', d)} />}
            {tab === 'lehrkraefte' && <TeachersTab detail={detail} names={names} />}
            {tab === 'schueler' && <StudentsWithAccounts detail={detail} onChanged={q.reload} />}
            {tab === 'klassenbuch' && <RegisterOverview classId={id} date={date} onDate={(d) => setParam('datum', d)} />}
            {tab === 'stundentafel' && <CurriculumTab classId={id} />}
          </FeatureBoundary>
        </div>
      </div>
    </div>
  );
}

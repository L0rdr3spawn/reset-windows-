/** `/kompetenzen` – Lehrkräfte und Leitung: Klassenübersicht, Lernstand je Kind, Rahmen, Abzeichen. */
import './kompetenzen.css';
import { useSearchParams } from 'react-router-dom';
import { PageHelp } from '../../components/Help';
import { Tabs } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useTitle } from '../../hooks/misc';
import { can } from '../../lib/permissions';
import { BadgesTab } from './BadgesTab';
import { FrameworksTab } from './FrameworksTab';
import { OverviewTab } from './OverviewTab';
import { StudentTab } from './StudentTab';

type Tab = 'uebersicht' | 'kind' | 'rahmen' | 'abzeichen';
const TABS: Tab[] = ['uebersicht', 'kind', 'rahmen', 'abzeichen'];

export default function CompetencyPage() {
  useTitle('Kompetenzen');
  const user = useUser();
  const [params, setParams] = useSearchParams();
  const canRead = can(user, 'competency.read');
  const canAssess = can(user, 'competency.assess');
  const canManage = can(user, 'competency.manage');
  const wanted = params.get('tab') as Tab | null;
  const fallback: Tab = canRead ? 'uebersicht' : 'rahmen';
  const tab: Tab = wanted && TABS.includes(wanted) && (canRead || wanted === 'rahmen' || wanted === 'abzeichen') ? wanted : fallback;
  const classId = params.get('klasse');
  const studentId = params.get('kind');

  const go = (patch: Record<string, string | null>) => {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(patch)) {
      if (v === null) next.delete(k);
      else next.set(k, v);
    }
    setParams(next, { replace: false });
  };

  return (
    <div className="page stack">
      <div className="page-head">
        <h1>Kompetenzen</h1>
        <PageHelp label="Hilfe zu Kompetenzen">
          Der Kompetenzrahmen gliedert Fächer in Bereiche und „Ich kann …“-Aussagen mit Niveaustufen. Sie schätzen Kinder je Kompetenz ein, die Kinder schätzen sich selbst ein, und Sie bestätigen. Der Verlauf bleibt erhalten.
        </PageHelp>
      </div>
      <Tabs<Tab>
        label="Kompetenzen"
        active={tab}
        onChange={(t) => go({ tab: t })}
        tabs={[
          { key: 'uebersicht', label: 'Klassenübersicht', hidden: !canRead },
          { key: 'kind', label: 'Schüler/in', hidden: !canRead },
          { key: 'rahmen', label: 'Rahmen' },
          { key: 'abzeichen', label: 'Abzeichen' },
        ]}
      />
      {tab === 'uebersicht' && <OverviewTab canAssess={canAssess} onOpenStudent={(id, cls) => go({ tab: 'kind', kind: id, klasse: cls })} />}
      {tab === 'kind' && <StudentTab classId={classId} studentId={studentId} onSelect={(c, s) => go({ klasse: c, kind: s })} />}
      {tab === 'rahmen' && <FrameworksTab canManage={canManage} />}
      {tab === 'abzeichen' && <BadgesTab canManage={canManage} canAssess={canAssess} />}
    </div>
  );
}

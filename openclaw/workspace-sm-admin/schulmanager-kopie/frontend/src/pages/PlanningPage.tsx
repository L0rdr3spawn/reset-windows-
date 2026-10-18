import { useNavigate, useParams } from 'react-router-dom';
import { Tabs } from '../components/ui';
import { useUser } from '../context/AuthContext';
import { useTitle } from '../hooks/misc';
import { can } from '../lib/permissions';
import { CoursesEditor } from './planning/CoursesEditor';
import { CurriculaEditor } from './planning/CurriculaEditor';
import { GeneratorPanel } from './planning/GeneratorPanel';
import { PlanCheckPanel } from './planning/PlanCheckPanel';
import { RulesPanel } from './planning/rules/RulesPanel';
import { ReportPanel, SchoolSettingsPanel, WeightsPanel } from './planning/SettingsPanels';

type TabKey = 'pruefung' | 'stundentafeln' | 'kurse' | 'generator' | 'bericht' | 'regeln' | 'vertretung' | 'zeitraster';

const TAB_LABELS: Record<TabKey, string> = {
  stundentafeln: 'Stundentafeln',
  kurse: 'Kurse & Kopplungen',
  pruefung: 'Plan prüfen',
  generator: 'Neuaufbau (Generator)',
  bericht: 'Qualitätsbericht',
  regeln: 'Regeln',
  vertretung: 'Vertretung & Abwesenheit',
  zeitraster: 'Zeitraster & Schuljahr',
};

export default function PlanningPage() {
  useTitle('Planung');
  const user = useUser();
  const navigate = useNavigate();
  const { tab } = useParams<{ tab: string }>();
  const canTt = can(user, 'timetable.edit');
  const canGen = can(user, 'timetable.generate');
  const canSettings = can(user, 'settings.edit');
  const canRead = can(user, ['plans.read_all', 'timetable.edit', 'timetable.generate']);

  // „Plan prüfen“ zuerst (Startansicht: Status und offene Vorschläge); die übrigen Tabs sind weiter unter /planung/<tab> erreichbar
  const tabs: { key: TabKey; label: string; hidden?: boolean }[] = [
    { key: 'pruefung', label: TAB_LABELS.pruefung, hidden: !(canGen || canTt || canSettings) },
    { key: 'bericht', label: TAB_LABELS.bericht, hidden: !canRead },
    { key: 'stundentafeln', label: TAB_LABELS.stundentafeln, hidden: !canRead },
    { key: 'kurse', label: TAB_LABELS.kurse, hidden: !canRead },
    { key: 'generator', label: TAB_LABELS.generator, hidden: !(canTt || canGen) },
    // Regeln lesen dürfen alle, die planen; ändern nur mit „Einstellungen bearbeiten“
    { key: 'regeln', label: TAB_LABELS.regeln, hidden: !(canSettings || canTt || canGen) },
    { key: 'vertretung', label: TAB_LABELS.vertretung, hidden: !canSettings },
    { key: 'zeitraster', label: TAB_LABELS.zeitraster, hidden: !canSettings },
  ];
  const visible = tabs.filter((t) => !t.hidden);
  const active = (visible.find((t) => t.key === tab)?.key ?? visible[0]?.key ?? 'bericht') as TabKey;

  return (
    <div className="page">
      <div className="page-head">
        <h1>Planung</h1>
      </div>
      <Tabs label="Planungsbereiche" tabs={tabs} active={active} onChange={(k) => navigate(`/planung/${k}`)} />
      <div role="tabpanel" aria-label={TAB_LABELS[active]}>
        {active === 'pruefung' && <PlanCheckPanel canDecide={canGen || canTt || canSettings} canGenerate={canGen} canSettings={canSettings} />}
        {active === 'stundentafeln' && <CurriculaEditor canEdit={canTt} />}
        {active === 'kurse' && <CoursesEditor canEdit={canTt} />}
        {active === 'generator' && <GeneratorPanel canEdit={canTt} canGenerate={canGen} />}
        {active === 'bericht' && <ReportPanel />}
        {active === 'regeln' && <RulesPanel canEdit={canSettings} canGenerate={canGen} />}
        {active === 'vertretung' && <WeightsPanel canEdit={canSettings} />}
        {active === 'zeitraster' && <SchoolSettingsPanel canEdit={canSettings} />}
      </div>
    </div>
  );
}

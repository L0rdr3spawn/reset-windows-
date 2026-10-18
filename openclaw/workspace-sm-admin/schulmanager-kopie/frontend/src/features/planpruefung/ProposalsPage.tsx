import { useTitle } from '../../hooks/misc';
import { useUser } from '../../context/AuthContext';
import { can } from '../../lib/permissions';
import { PROPOSAL_RIGHTS } from './badge';
import { PlanCheckPanel } from '../../pages/planning/PlanCheckPanel';

/** Seite „Planvorschläge“ (`/planung/vorschlaege`): Status der Dauerprüfung und offene Vorschläge. */
export default function ProposalsPage() {
  useTitle('Planvorschläge');
  const user = useUser();
  return (
    <div className="page">
      <div className="page-head">
        <h1>Planvorschläge</h1>
      </div>
      <PlanCheckPanel canDecide={can(user, [...PROPOSAL_RIGHTS])} canGenerate={can(user, 'timetable.generate')} canSettings={can(user, 'settings.edit')} />
    </div>
  );
}

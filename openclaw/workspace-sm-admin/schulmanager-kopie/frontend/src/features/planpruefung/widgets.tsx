import { Link } from 'react-router-dom';
import { Icon } from '../../components/Icon';
import { useUser } from '../../context/AuthContext';
import { can } from '../../lib/permissions';
import { formatDateTime } from '../../lib/dates';
import { PROPOSAL_RIGHTS, useProposalSummary } from './badge';

/** Startseiten-Kachel: erscheint nur, wenn Vorschläge zur Entscheidung vorliegen oder gerade berechnet werden. */
export default function ProposalsWidget() {
  const user = useUser();
  const enabled = can(user, [...PROPOSAL_RIGHTS]);
  const q = useProposalSummary(enabled);
  const s = q.data;
  if (!enabled || !s || (s.open === 0 && s.computing === 0)) return null;
  return (
    <section className="card" aria-labelledby="pp-widget-h">
      <div className="card-head">
        <h2 id="pp-widget-h">
          <Icon name="sparkles" /> Planvorschläge
        </h2>
        <Link to="/planung/vorschlaege" className="btn btn-primary btn-sm">
          {s.open > 0 ? 'Vergleichen & entscheiden' : 'Ansehen'}
        </Link>
      </div>
      {s.open > 0 ? (
        <p style={{ margin: 0 }}>
          <strong>{s.open}</strong> {s.open === 1 ? 'Vorschlag wartet' : 'Vorschläge warten'} auf Ihre Entscheidung
          {s.newest ? `: ${s.newest.title} (${formatDateTime(s.newest.created_at)})` : ''}.
        </p>
      ) : (
        <p className="muted" style={{ margin: 0 }}>
          Lösungen für Probleme im Stundenplan werden berechnet …
        </p>
      )}
    </section>
  );
}

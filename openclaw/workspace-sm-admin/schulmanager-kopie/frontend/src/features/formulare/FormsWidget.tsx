import { Link } from 'react-router-dom';
import { Icon } from '../../components/Icon';
import { useApi } from '../../hooks/useApi';
import { formsApi } from './api';
import './formulare.css';

/** Startseiten-Kachel: erscheint nur, wenn Formulare warten (Entscheidung) oder Rückmeldungen fehlen. */
export default function FormsWidget() {
  const q = useApi((signal) => formsApi.summary(signal), [], { live: ['forms'] });
  const s = q.data;
  if (!s || (s.to_decide === 0 && s.to_fill === 0)) return null;
  return (
    <section className="card fm-widget" aria-label="Formulare">
      <div className="card-head">
        <h2>Formulare</h2>
        <Link className="btn btn-sm" to="/formulare">
          <Icon name="list" /> Öffnen
        </Link>
      </div>
      <ul className="fm-widget-list">
        {s.to_decide > 0 && (
          <li>
            <strong>{s.to_decide}</strong> {s.to_decide === 1 ? 'Einreichung wartet' : 'Einreichungen warten'} auf Ihre Entscheidung
            {s.overdue > 0 ? <span className="badge badge-danger"> {s.overdue} überfällig</span> : null}
          </li>
        )}
        {s.to_fill > 0 && (
          <li>
            <strong>{s.to_fill}</strong> {s.to_fill === 1 ? 'Rückmeldung fehlt' : 'Rückmeldungen fehlen'} noch
          </li>
        )}
      </ul>
    </section>
  );
}

/**
 * Startseiten-Kacheln der Lehrer-Selbstverwaltung (werden erst bei Bedarf geladen, siehe module.tsx):
 * Lehrkräfte sehen den Stand ihres Profils/Antrags, Planung/Schulleitung die offenen Anträge.
 */
import { Link } from 'react-router-dom';
import { ApiError } from '../../api/client';
import { Icon } from '../../components/Icon';
import { ErrorBox, Loading } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { formatDateTime } from '../../lib/dates';
import { teacherProfileApi, teacherRequestsApi } from './api';
import { StatusBadge } from './components';
import type { MyProfileResponse, RequestsSummary } from './types';

/** Kachel für Planung/Schulleitung: offene Anträge. */
export function RequestsWidget() {
  const q = useApi<RequestsSummary>(() => teacherRequestsApi.summary(), [], { live: ['teacher_requests'] });
  const s = q.data;
  return (
    <section className="card" aria-labelledby="tw-req-h">
      <div className="card-head">
        <h2 id="tw-req-h">Anträge von Lehrkräften</h2>
        <Link to="/planung/antraege" className="small">
          Alle anzeigen
        </Link>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {s && (
        <div className="stack-sm">
          <p style={{ margin: 0 }}>
            <span className="tp-widget-count">{s.open}</span> <span className="muted">{s.open === 1 ? 'offener Antrag' : 'offene Anträge'}</span>
          </p>
          {s.latest.length > 0 ? (
            <ul className="list-plain small">
              {s.latest.map((r) => (
                <li key={r.id}>
                  <Link to={`/planung/antraege?antrag=${r.id}`}>{r.teacher_name}</Link> <span className="muted">· {formatDateTime(r.created_at)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="small muted" style={{ margin: 0 }}>
              Keine offenen Anträge – Profiländerungen der Lehrkräfte erscheinen hier zur Prüfung.
            </p>
          )}
        </div>
      )}
    </section>
  );
}

/** Kachel für Lehrkräfte: eigenes Profil (Zeitfenster, Deputat) und Antragsstatus. */
export function ProfileWidget() {
  const q = useApi<MyProfileResponse>(() => teacherProfileApi.mine(), [], { live: ['teacher_requests', 'teacher_profile', 'teachers'] });
  // Konto ohne verknüpfte Lehrkraft: keine Kachel (Hinweis steht auf der Profilseite)
  if (q.error instanceof ApiError && q.error.status === 409) return null;
  const d = q.data;
  const last = d?.requests.find((r) => r.status === 'genehmigt' || r.status === 'abgelehnt');
  return (
    <section className="card" aria-labelledby="tw-prof-h">
      <div className="card-head">
        <h2 id="tw-prof-h">Mein Profil als Lehrkraft</h2>
        <Link to="/lehrkraft/profil" className="small">
          Bearbeiten
        </Link>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {d && (
        <div className="stack-sm small">
          <p style={{ margin: 0 }}>
            <Icon name="clock" /> {d.description}
          </p>
          <p style={{ margin: 0 }}>
            Deputat {d.profile.max_hours} Std. · zurzeit {d.load.hours} Std. in {d.load.courses.length} Kursen
          </p>
          {d.pending ? (
            <p className="row" style={{ margin: 0, gap: 6 }}>
              <StatusBadge status="offen" label="Antrag wird geprüft" /> <span className="muted">seit {formatDateTime(d.pending.created_at)}</span>
            </p>
          ) : last ? (
            <p className="row" style={{ margin: 0, gap: 6 }}>
              <StatusBadge status={last.status} label={last.auto ? 'direkt übernommen' : `Antrag ${last.status_label}`} />
              <span className="muted">{formatDateTime(last.decided_at)}</span>
            </p>
          ) : null}
          {last?.status === 'abgelehnt' && last.review_comment && !d.pending && <p className="tp-note">{last.review_comment}</p>}
          {d.conflicts.outside_windows.length > 0 && (
            <p className="badge badge-warning" style={{ margin: 0, justifySelf: 'start' }}>
              {d.conflicts.outside_windows.length} Unterrichtsblöcke außerhalb Ihrer Zeitfenster
            </p>
          )}
        </div>
      )}
    </section>
  );
}

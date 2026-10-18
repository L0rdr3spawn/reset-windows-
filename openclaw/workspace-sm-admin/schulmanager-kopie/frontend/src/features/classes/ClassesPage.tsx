/**
 * Klassen suchen (`/klassen`): Suchfeld (Klasse, Klassenleitung, Raum), Filter Standort, Liste nach Jahrgang.
 * Suche und Filter stehen in der Adresse (`?q=&standort=`), damit „Zurück“ aus der Detailseite sie behält.
 */
import { useId, useMemo } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Icon } from '../../components/Icon';
import { Empty, ErrorBox, Loading } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { useCollection } from '../../hooks/useCollection';
import { useDebounced, useTitle } from '../../hooks/misc';
import { sortBy } from '../../lib/format';
import { classesApi } from './api';
import { countsText, filterClasses, groupByGrade } from './logic';
import './classes.css';
import type { ClassListItem } from './types';

function ClassRow({ c, showSite }: { c: ClassListItem; showSite: boolean }) {
  return (
    <li>
      <Link to={`/klassen/${encodeURIComponent(c.id)}`} className="kl-class">
        <span className="kl-class-name">{c.name}</span>
        <span className="kl-class-main">
          <span>
            <span className="muted">Klassenleitung:</span> {c.class_teacher?.name ?? <em className="muted">nicht gesetzt</em>}
          </span>
          <span>
            <span className="muted">Klassenraum:</span> {c.home_room?.name ?? <em className="muted">keiner</em>}
            {showSite && c.site_name ? <span className="muted"> · {c.site_name}</span> : null}
          </span>
          <span className="small muted">{countsText(c)}</span>
        </span>
        <Icon name="chevronRight" className="icon kl-class-go" />
      </Link>
    </li>
  );
}

export default function ClassesPage() {
  useTitle('Klassen');
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const q = params.get('q') ?? '';
  const site = params.get('standort') ?? '';
  const debounced = useDebounced(q, 250);
  const searchId = useId();
  const siteId = useId();
  const sites = useCollection('sites');
  const list = useApi((signal) => classesApi.list({ q: debounced, site }, signal), [debounced, site], {
    live: ['classes', 'students', 'courses', 'rooms', 'teachers'],
    keepPrevious: true,
  });

  const setParam = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
  };

  // zusätzlich im Browser filtern: reagiert sofort beim Tippen
  const shown = useMemo(() => filterClasses(list.data?.classes ?? [], q, site), [list.data, q, site]);
  const groups = useMemo(() => groupByGrade(shown), [shown]);
  const siteOptions = useMemo(() => sortBy(sites.data ?? [], (s) => s.name), [sites.data]);
  const showSite = !site && siteOptions.length > 1;

  return (
    <div className="page stack kl-page">
      <div className="page-head">
        <h1>Klassen</h1>
        {list.data?.can_edit && (
          <div className="actions">
            <Link className="btn btn-primary" to="/klassen/neu">
              <Icon name="plus" /> Neue Klasse
            </Link>
          </div>
        )}
      </div>
      <form
        className="toolbar kl-toolbar"
        role="search"
        aria-label="Klassen suchen"
        onSubmit={(e) => {
          e.preventDefault();
          const first = shown[0];
          if (first) navigate(`/klassen/${encodeURIComponent(first.id)}`);
        }}
      >
        <div className="field wide">
          <label htmlFor={searchId}>Klasse suchen</label>
          <input
            id={searchId}
            type="search"
            value={q}
            placeholder="z. B. 7b, Name der Klassenleitung oder Raum"
            autoComplete="off"
            onChange={(e) => setParam('q', e.target.value)}
            aria-describedby={`${searchId}-hint`}
          />
          <span className="hint" id={`${searchId}-hint`}>
            Eingabetaste öffnet den ersten Treffer.
          </span>
        </div>
        {siteOptions.length > 1 && (
          <div className="field">
            <label htmlFor={siteId}>Standort</label>
            <select id={siteId} value={site} onChange={(e) => setParam('standort', e.target.value)}>
              <option value="">Alle Standorte</option>
              {siteOptions.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </form>

      {list.error ? <ErrorBox error={list.error} onRetry={list.reload} /> : null}
      {list.initialLoading && <Loading />}
      {list.data && (
        <p className="small muted" aria-live="polite" style={{ margin: 0 }}>
          {shown.length === 1 ? '1 Klasse' : `${shown.length} Klassen`}
          {q || site ? ' gefunden' : ''}
        </p>
      )}
      {list.data && shown.length === 0 && (
        <Empty icon="search">{q || site ? 'Keine Klasse passt zur Suche.' : 'Für Ihr Konto sind keine Klassen freigegeben.'}</Empty>
      )}
      {groups.map((g) => (
        <section key={g.grade} className="card" aria-labelledby={`kl-grade-${g.grade}`}>
          <div className="card-head">
            <h2 id={`kl-grade-${g.grade}`}>{g.label}</h2>
            <span className="badge">{g.classes.length === 1 ? '1 Klasse' : `${g.classes.length} Klassen`}</span>
          </div>
          <ul className="kl-class-list">
            {g.classes.map((c) => (
              <ClassRow key={c.id} c={c} showSite={showSite} />
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

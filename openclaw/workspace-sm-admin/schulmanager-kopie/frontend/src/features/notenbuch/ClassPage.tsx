/**
 * `/notenbuch/klasse/:classId` – Klassenübersicht Schüler/in × Fächer mit Halbjahres- bzw. Vorschlagsnoten, Warnung bei
 * gefährdeter Versetzung und Notenkonferenz-Liste als PDF (Klassenleitung lesend, Schulleitung).
 */
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { Abbr } from '../../components/Abbr';
import { Icon } from '../../components/Icon';
import { Empty, ErrorBox, Loading } from '../../components/ui';
import { useTitle } from '../../hooks/misc';
import { useApi } from '../../hooks/useApi';
import { gbApi } from './api';
import { gradeTone } from './logic';
import './notenbuch.css';

export default function ClassPage() {
  const { classId = '' } = useParams();
  const [sp, setSp] = useSearchParams();
  const nav = useNavigate();
  const meta = useApi((signal) => gbApi.meta(signal), []);
  const term = sp.get('term') || meta.data?.term || '';
  const q = useApi((signal) => gbApi.classOverview(classId, term || undefined, signal), [classId, term], { live: ['gradebook'], enabled: !!meta.data });
  const d = q.data;
  useTitle(`Noten ${classId}`);
  if (meta.error) return <div className="page"><ErrorBox error={meta.error} onRetry={meta.reload} /></div>;
  if (!meta.data) return <div className="page"><Loading /></div>;
  return (
    <div className="page stack">
      <div className="page-head">
        <div>
          <p className="small muted">
            <Link to="/notenbuch">Notenbuch</Link>
          </p>
          <h1>Noten Klasse {classId}</h1>
        </div>
        <div className="gbk-bar">
          <select aria-label="Klasse" value={classId} onChange={(e) => nav(`/notenbuch/klasse/${encodeURIComponent(e.target.value)}?term=${encodeURIComponent(term)}`)}>
            {meta.data.classes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <select aria-label="Halbjahr" value={term} onChange={(e) => setSp({ term: e.target.value })}>
            {meta.data.terms.map((t) => (
              <option key={t.id} value={t.id}>
                {t.label}
              </option>
            ))}
          </select>
          {d && (
            <a className="btn" href={gbApi.conferenceUrl(classId, d.term)} target="_blank" rel="noreferrer">
              <Icon name="print" /> Notenkonferenz-Liste (PDF)
            </a>
          )}
        </div>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!d && q.loading && <Loading />}
      {d && d.students.length === 0 && <Empty icon="users">In dieser Klasse gibt es keine Schüler/innen.</Empty>}
      {d && d.students.length > 0 && (
        <>
          <div className="gbk-chips">
            <span className="badge">{d.term_label}</span>
            {d.locked_all ? <span className="badge badge-success">alle Notenbücher gesperrt</span> : <span className="badge badge-warning">noch nicht alles festgelegt</span>}
            {d.warning_count > 0 ? <span className="badge badge-danger">{d.warning_count} mit gefährdeter Versetzung</span> : <span className="badge badge-success">keine Warnung</span>}
            <Abbr text={<span className="small muted">kursiv = Vorschlag</span>} full="Kursive Noten sind Vorschläge aus dem Notenbuch; die Lehrkraft hat noch keine Note festgelegt." />
          </div>
          <div className="gbk-scroll" role="region" aria-label="Notenübersicht" tabIndex={0}>
            <table className="gbk-table gbk-ov">
              <thead>
                <tr>
                  <th className="gbk-name" scope="col">
                    Schüler/in
                  </th>
                  {d.subjects.map((s) => (
                    <th key={s.id} scope="col" title={s.name}>
                      {s.id}
                      {s.core ? <span className="gbk-head-meta"> Hauptfach</span> : null}
                    </th>
                  ))}
                  <th scope="col">Hinweis</th>
                </tr>
              </thead>
              <tbody>
                {d.students.map((s) => (
                  <tr key={s.student_id}>
                    <th scope="row" className="gbk-name">
                      {s.name}
                    </th>
                    {d.subjects.map((sub) => {
                      const c = s.cells[sub.id];
                      if (!c) return <td key={sub.id}>–</td>;
                      const tone = gradeTone(c.value, c.scale);
                      return (
                        <td key={sub.id} className={`${tone === 'none' ? '' : `gbk-tone-${tone}`}${c.deficit ? ' gbk-deficit' : ''}`}>
                          <span className={c.final ? undefined : 'gbk-prov'} title={c.final ? (c.overridden ? 'festgelegt, weicht vom Vorschlag ab' : 'festgelegt') : 'Vorschlag'}>
                            {c.value}
                          </span>
                          {c.overridden ? <span className="gbk-sub">überschr.</span> : null}
                        </td>
                      );
                    })}
                    <td className="gbk-warn">{s.warnings.join('; ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="small muted">
            Defizit: {d.risk.enabled ? `Note ${d.risk.min_grade} oder schlechter bzw. höchstens ${d.risk.max_points} Punkte` : 'Warnung ausgeschaltet'}.
          </p>
        </>
      )}
    </div>
  );
}

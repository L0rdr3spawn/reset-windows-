/**
 * Klassenbuch-Übersicht der Klassenleitung (Tab „Klassenbuch“ auf der Klassenseite): Schüler/innen untereinander,
 * die Unterrichtsstunden der Woche nebeneinander – da / fehlt / zu spät / gemeldet / nicht eingetragen, dazu Summen.
 */
import { Fragment } from 'react';
import { Link } from 'react-router-dom';
import { http } from '../../api/client';
import type { AbsenceLogEvent } from '../../api/types';
import { SubjectAbbr } from '../../components/Abbr';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { ErrorBox, Loading } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { addDays, formatShort } from '../../lib/dates';
import { AbsenceHistory, reportLine } from '../students/AbsenceHistory';

type Status = 'present' | 'absent' | 'late' | 'left' | 'reported' | null;
interface Overview {
  class: { id: string; name: string };
  from: string;
  to: string;
  students: { id: string; name: string }[];
  slots: { key: string; date: string; period: number; part: number; subject: string | null; entered: boolean }[];
  cells: Record<string, Record<string, Status>>;
  totals: Record<string, { absent: number; late: number; reported: number; open: number }>;
  /** Meldungen der Woche je Schüler/in mit Zeitpunkt, Person, Kanal und Verlauf (Meldungsprotokoll) */
  reports?: Record<
    string,
    {
      absence_id: number;
      kind_label: string;
      date_from: string;
      date_to: string;
      periods: number[];
      status_label: string;
      reported_at: string | null;
      channel_label: string;
      reported_by_name?: string;
      reported_by_role?: string;
      history: AbsenceLogEvent[];
    }[]
  >;
}

const MARK: Record<Exclude<Status, null>, [string, string]> = {
  present: ['✓', 'da'],
  absent: ['✗', 'fehlt'],
  left: ['✗', 'gegangen'],
  late: ['⏱', 'zu spät'],
  reported: ['K', 'gemeldet (z. B. krank)'],
};

function monday(iso: string): string {
  const d = new Date(`${iso}T12:00:00`);
  return addDays(iso, -((d.getDay() + 6) % 7));
}

export function RegisterOverview({ classId, date, onDate }: { classId: string; date: string; onDate: (d: string) => void }) {
  const from = monday(date);
  const q = useApi((signal) => http.get<Overview>('/register/overview', { class_id: classId, from, to: addDays(from, 6) }, { signal }), [classId, from], {
    live: ['register', 'student_absences'],
    keepPrevious: true,
  });
  const data = q.data;
  const days = data ? Array.from(new Set(data.slots.map((s) => s.date))) : [];
  return (
    <div className="stack-sm">
      <div className="row" role="group" aria-label="Woche wählen" style={{ flexWrap: 'wrap', gap: 8 }}>
        <button type="button" className="btn btn-icon" aria-label="Vorherige Woche" onClick={() => onDate(addDays(from, -7))}>
          <Icon name="chevronLeft" />
        </button>
        <strong>
          {formatShort(from)} – {formatShort(addDays(from, 6))}
        </strong>
        <button type="button" className="btn btn-icon" aria-label="Nächste Woche" onClick={() => onDate(addDays(from, 7))}>
          <Icon name="chevronRight" />
        </button>
        <HelpTip>
          ✓ da · ✗ fehlt · ⏱ zu spät · K gemeldet (krank, beurlaubt) · leer = nicht eingetragen. Grau hinterlegte Stunden sind noch gar nicht eingetragen. Klick auf einen Tag öffnet das Klassenbuch dieses Tages.
        </HelpTip>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!data && !q.error && <Loading />}
      {data && data.slots.length === 0 && <p className="muted small">In dieser Woche hat die Klasse keinen Unterricht.</p>}
      {data && data.slots.length > 0 && (
        <div className="table-wrap">
          <table className="table kb-overview">
            <thead>
              <tr>
                <th rowSpan={2}>Schüler/in</th>
                {days.map((d) => (
                  <th key={d} colSpan={data.slots.filter((s) => s.date === d).length} className="kb-day">
                    <Link to={`/klassenbuch?klasse=${encodeURIComponent(classId)}&datum=${d}`}>{formatShort(d)}</Link>
                  </th>
                ))}
                <th rowSpan={2} title="fehlt / zu spät / gemeldet">
                  ✗ / ⏱ / K
                </th>
              </tr>
              <tr>
                {data.slots.map((s, i) => (
                  <th key={s.key} className={`kb-slot${!s.entered ? ' kb-open' : ''}${i > 0 && data.slots[i - 1].date !== s.date ? ' kb-daystart' : ''}`} title={`${s.period + 1}. Stunde ${s.subject ?? ''}`}>
                    {s.period + 1}
                    <div className="xsmall muted">{s.subject ? <SubjectAbbr id={s.subject} /> : null}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.students.map((st) => {
                const t = data.totals[st.id];
                return (
                  <tr key={st.id}>
                    <th scope="row" className="nowrap">
                      {st.name}
                    </th>
                    {data.slots.map((s, i) => {
                      const v = data.cells[st.id]?.[s.key];
                      const mark = v ? MARK[v] : null;
                      return (
                        <td
                          key={s.key}
                          className={`kb-cell${v ? ` kb-${v}` : ''}${!s.entered ? ' kb-open' : ''}${i > 0 && data.slots[i - 1].date !== s.date ? ' kb-daystart' : ''}`}
                          title={mark ? mark[1] : s.key in (data.cells[st.id] ?? {}) ? 'nicht eingetragen' : 'nicht in dieser Stunde'}
                        >
                          {mark ? mark[0] : ''}
                        </td>
                      );
                    })}
                    <td className="nowrap small">
                      <Fragment>
                        {t.absent} / {t.late} / {t.reported}
                      </Fragment>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {data && data.students.some((st) => data.reports?.[st.id]?.length) && (
        <section className="stack-sm" aria-labelledby="kb-reports-h">
          <h3 id="kb-reports-h" style={{ margin: 0 }}>
            Meldungen &amp; Verlauf
          </h3>
          <ul className="st-list">
            {data.students
              .filter((st) => data.reports?.[st.id]?.length)
              .map((st) => (
                <li key={st.id} className="st-row">
                  <div className="st-row-main">
                    <strong>
                      <Link to={`/fehlzeiten/${encodeURIComponent(st.id)}`}>{st.name}</Link>
                    </strong>
                    {(data.reports?.[st.id] ?? []).map((r) => (
                      <div key={r.absence_id}>
                        <span className="small">
                          {formatShort(r.date_from)}
                          {r.date_to !== r.date_from ? ` – ${formatShort(r.date_to)}` : ''}
                          {r.periods.length ? ` (${r.periods.map((p) => p + 1).join(', ')}. Std.)` : ''}: {reportLine(r)} · {r.status_label}
                        </span>
                        <AbsenceHistory events={r.history} />
                      </div>
                    ))}
                  </div>
                </li>
              ))}
          </ul>
        </section>
      )}
    </div>
  );
}

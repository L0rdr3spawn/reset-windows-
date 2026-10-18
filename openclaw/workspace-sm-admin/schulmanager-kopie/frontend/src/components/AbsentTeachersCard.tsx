import type { AbsentTeacherDetail } from '../api/types';
import { formatDate } from '../lib/dates';
import { casesLabel, periodsLabel } from '../lib/substitution';
import { HelpText } from './Help';

/**
 * Karte „Abwesende Lehrkräfte“ (B-04, A-56): eine Zeile je Person (Kürzel · Name · Stunden · Fälle). Ein Klick auf
 * eine Zeile wählt die Lehrkraft als Filter (`onSelect(Kürzel)`), ein zweiter Klick hebt ihn auf (`onSelect(null)`).
 */
export function AbsentTeachersCard({
  details,
  selected,
  onSelect,
  date,
}: {
  details: readonly AbsentTeacherDetail[];
  selected: string;
  onSelect: (teacher: string | null) => void;
  date: string;
}) {
  if (details.length === 0) return null;
  return (
    <section className="card" aria-labelledby="absent-teachers-h">
      <div className="card-head">
        <h2 id="absent-teachers-h">
          <HelpText help="Ein Klick auf eine Zeile zeigt nur die Einträge dieser Lehrkraft, ein zweiter Klick wieder alle. Fälle: vertretene, betreute oder entfallene Stunden und vertretene Aufsichten.">
            Abwesende Lehrkräfte
          </HelpText>{' '}
          <span className="badge">{details.length}</span>
        </h2>
      </div>
      <div className="table-wrap">
        <table className="table table-compact">
          <caption className="sr-only">Abwesende Lehrkräfte am {formatDate(date)}</caption>
          <thead>
            <tr>
              <th scope="col">Kürzel</th>
              <th scope="col">Name</th>
              <th scope="col">Stunden</th>
              <th scope="col" className="num">
                Fälle
              </th>
            </tr>
          </thead>
          <tbody>
            {details.map((d) => {
              const on = selected === d.teacher;
              return (
                <tr key={d.teacher} className={`clickable${on ? ' selected' : ''}`} onClick={() => onSelect(on ? null : d.teacher)}>
                  <td className="nowrap">
                    <button type="button" className="btn btn-ghost btn-sm mono" aria-pressed={on} aria-label={`Nach Lehrkraft filtern: ${[d.teacher, d.name].filter(Boolean).join(', ')}`}>
                      {d.teacher}
                    </button>
                  </td>
                  <td>{d.name}</td>
                  <td className="nowrap">{periodsLabel(d.periods, d.full_day)}</td>
                  <td className="num nowrap">{casesLabel(d.cases)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

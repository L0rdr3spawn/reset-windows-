/**
 * Bausteine der Lehrer-Selbstverwaltung: Statusabzeichen, Konflikte, Vergleich alt/neu (Verfügbarkeit: `AvailabilityEditor`).
 */
import { Link } from 'react-router-dom';
import { Alert } from '../../components/ui';
import type { Conflicts, DiffRow } from './types';
import { STATUS_TONE } from './windows';
import './teacher.css';

export function StatusBadge({ status, label }: { status: string; label?: string }) {
  const tone = STATUS_TONE[status] ?? '';
  return <span className={`badge${tone ? ` badge-${tone}` : ''}`}>{label ?? status}</span>;
}

/** Konfliktanzeige einer (geplanten) Profiländerung. */
export function ConflictList({ conflicts, title = 'Auswirkungen auf den Stundenplan' }: { conflicts: Conflicts | null | undefined; title?: string }) {
  if (!conflicts) return null;
  const hard = conflicts.count > 0;
  const outside = conflicts.outside_windows ?? [];
  return (
    <div className="tp-conflicts" aria-live="polite">
      <Alert kind={hard ? 'warning' : 'success'} title={hard ? `${title}: ${conflicts.count} Konflikt${conflicts.count === 1 ? '' : 'e'}` : `${title}: keine Konflikte`}>
        {conflicts.messages.length > 0 && (
          <ul>
            {conflicts.messages.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        )}
        {outside.length > 0 && (
          <details className="disclosure" style={{ marginTop: 6 }}>
            <summary>{outside.length} betroffene Unterrichtsblöcke anzeigen</summary>
            <ul>
              {outside.slice(0, 60).map((c) => (
                <li key={c.lesson_id}>{c.text}</li>
              ))}
            </ul>
          </details>
        )}
        {(conflicts.suggestions?.length ?? 0) > 0 && (
          <div style={{ marginTop: 6 }}>
            <strong className="small">Lösungsvorschläge (nichts davon geschieht automatisch)</strong>
            <ul>
              {conflicts.suggestions?.map((sg, i) => (
                <li key={i}>
                  {sg.text}
                  {sg.link ? (
                    <>
                      {' '}
                      <Link to={sg.link}>Öffnen</Link>
                    </>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        )}
        <p className="small" style={{ margin: '6px 0 0' }}>
          Deputat: Ist {conflicts.hours.current} Std. · Soll {conflicts.hours.max_hours} Std.
          {conflicts.hours.status === 'ueber' && <strong> – überschritten</strong>}
          {conflicts.hours.status === 'unter' && <span> – nicht ausgeschöpft</span>}
        </p>
      </Alert>
    </div>
  );
}

/** Vergleich alt/neu. */
export function DiffTable({ diff, caption = 'Vergleich bisher / neu' }: { diff: DiffRow[]; caption?: string }) {
  if (!diff.length) return <p className="small muted">Keine inhaltlichen Änderungen.</p>;
  return (
    <table className="tp-diff">
      <caption className="sr-only">{caption}</caption>
      <thead>
        <tr>
          <th scope="col">Angabe</th>
          <th scope="col">bisher</th>
          <th scope="col">neu</th>
        </tr>
      </thead>
      <tbody>
        {diff.map((d) => (
          <tr key={d.field}>
            <th scope="row">{d.label}</th>
            <td className="old">{d.old_text}</td>
            <td className="new">{d.new_text}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

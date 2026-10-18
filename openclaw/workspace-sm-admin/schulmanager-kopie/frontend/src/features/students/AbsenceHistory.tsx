/**
 * Meldungsprotokoll der Fehlzeiten: „krank gemeldet am … von … (Kanal)“ und der Verlauf (nur anhängend).
 * Die volle Sicht (Klassenleitung, Sekretariat, Schulleitung) zeigt Person, Rolle und jede Änderung; Fachlehrkräfte
 * bekommen vom Server nur „abwesend gemeldet“ mit Zeitpunkt und Kanal.
 */
import type { AbsenceLogEvent } from '../../api/types';
import { formatDateTime } from '../../lib/dates';
import './students.css';

/** Eine Zeile: „gemeldet am 12.10.2026, 07:41 von Frau Müller (Eltern) · online im Schulpuls“ */
type LineInfo = { reported_at?: string | null; channel_label?: string; reported_by_name?: string | null; reported_by_role?: string; kind_label?: string };

export function reportLine(info: LineInfo, verb = 'gemeldet'): string {
  const who = info.reported_by_name ? ` von ${info.reported_by_name}${info.reported_by_role ? ` (${info.reported_by_role})` : ''}` : '';
  const how = info.channel_label ? ` · ${info.channel_label}` : '';
  return `${info.kind_label ? `${info.kind_label} ` : ''}${verb} am ${formatDateTime(info.reported_at)}${who}${how}`;
}

export function AbsenceTimeline({ events }: { events: AbsenceLogEvent[] }) {
  if (!events.length) return <p className="xsmall muted">Kein Protokoll vorhanden.</p>;
  return (
    <ol className="al-timeline">
      {events.map((e) => (
        <li key={e.id}>
          <span className="al-when">{formatDateTime(e.at)}</span> <span>{e.text}</span>
          <span className="xsmall muted">
            {e.actor_name ? ` · ${e.actor_name}${e.actor_role ? ` (${e.actor_role})` : ''}` : ''}
            {e.channel_label ? ` · ${e.channel_label}` : ''}
          </span>
        </li>
      ))}
    </ol>
  );
}

/** Aufklappbarer Verlauf einer Meldung. */
export function AbsenceHistory({ events, label = 'Verlauf' }: { events?: AbsenceLogEvent[]; label?: string }) {
  if (!events?.length) return null;
  return (
    <details className="al-history">
      <summary className="small">
        {label} ({events.length})
      </summary>
      <AbsenceTimeline events={events} />
    </details>
  );
}

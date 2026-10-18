/** Ergänzungen der Schüler-/Elternansicht einer Aufgabe: Frist-Verlängerung, Gruppe, Bewertungskriterien, Ergebnis. */
import { Alert } from '../../../components/ui';
import { formatWhen } from '../logic';
import type { MySubmissionResponse, Submission } from '../types';
import { VersionList } from './GradingTable';
import { fmtPoints, percentText } from './logic';
import { RubricPreview, RubricView } from './RubricGrader';
import type { AssignSettings } from './types';
import './aufgaben.css';

export function StudentInfo({ data }: { data: MySubmissionResponse }) {
  const sub = data.submission;
  const settings = data.settings;
  return (
    <>
      {data.needs_group && (
        <Alert kind="warning" title="Noch keine Gruppe">
          Sie sind noch keiner Gruppe zugeordnet. Bitte fragen Sie Ihre Lehrkraft.
        </Alert>
      )}
      {data.group && (
        <section className="card au-group stack-sm" aria-label="Gruppe">
          <div className="row-between">
            <strong>Gruppe: {data.group.name}</strong>
            <span className="xsmall muted">Die Abgabe gilt für alle Mitglieder.</span>
          </div>
          <div className="row">
            {data.group.members.map((m) => (
              <span key={m.user_id} className="badge">
                {m.name}
              </span>
            ))}
          </div>
        </section>
      )}
      {data.extension && data.effective_due_at && (
        <p className="au-ext" role="note">
          Ihre Frist wurde verlängert bis <strong>{formatWhen(data.effective_due_at)}</strong>
          {data.extension.reason ? ` (${data.extension.reason})` : ''}.
        </p>
      )}
      {sub && sub.attempt > 1 && (
        <p className="au-ext" role="note">
          Überarbeitung (Version {sub.attempt}){sub.revision_due_at ? ` – abgeben bis ${formatWhen(sub.revision_due_at)}` : ''}.
        </p>
      )}
      {settings.rubric && !(sub && sub.rubric) && (
        <details className="card au-criteria" open={!sub}>
          <summary>
            {settings.rubric.kind === 'guide' ? 'Bewertungsleitfaden' : 'Bewertungsraster'}
            {settings.rubric_title ? `: ${settings.rubric_title}` : ''} · {fmtPoints(settings.max_points)} Punkte
          </summary>
          <RubricPreview rubric={settings.rubric} />
        </details>
      )}
      {!settings.rubric && settings.max_points ? <p className="small muted">Höchstens {fmtPoints(settings.max_points)} Punkte.</p> : null}
    </>
  );
}

/** Punkte und ausgefülltes Raster in der Rückmeldung (für Eltern nur bei Freigabe vorhanden) */
export function FilledResult({ sub, settings }: { sub: Submission; settings: AssignSettings }) {
  return (
    <>
      {sub.points !== null && (
        <p style={{ margin: 0 }}>
          Punkte:{' '}
          <strong>
            {fmtPoints(sub.points)} von {fmtPoints(sub.max_points)}
          </strong>{' '}
          <span className="muted">({percentText(sub.points, sub.max_points)})</span>
        </p>
      )}
      {sub.rubric && settings.rubric && <RubricView rubric={settings.rubric} fill={sub.rubric} />}
    </>
  );
}

export function StudentVersions({ sub, settings }: { sub: Submission; settings: AssignSettings }) {
  return <VersionList versions={sub.versions} settings={settings} />;
}

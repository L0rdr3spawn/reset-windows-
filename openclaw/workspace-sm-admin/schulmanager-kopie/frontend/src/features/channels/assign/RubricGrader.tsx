/**
 * Bewertungsraster beim Bewerten (Stufen anklicken bzw. Punkte je Kriterium eintragen) und als Ansicht für
 * Schüler/innen und Eltern (ausgefülltes Raster).
 */
import { useState } from 'react';
import { fmtPoints, rubricMax, rubricTotal, setComment, setCriterionPoints, setLevel } from './logic';
import type { Rubric, RubricFill } from './types';
import './aufgaben.css';

export function RubricGrader({ rubric, fill, onChange, disabled = false, idPrefix }: { rubric: Rubric; fill: RubricFill; onChange: (f: RubricFill) => void; disabled?: boolean; idPrefix: string }) {
  const total = rubricTotal(rubric, fill);
  const max = rubricMax(rubric);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  return (
    <div className="au-grader stack-sm">
      {rubric.criteria.map((c) => {
        const f = fill[c.id] ?? {};
        const cid = `${idPrefix}-${c.id}`;
        return (
          <div key={c.id} className="au-grade-row" role="group" aria-labelledby={`${cid}-t`}>
            <div className="au-grade-head">
              <strong id={`${cid}-t`}>{c.title}</strong>
              {rubric.kind === 'guide' && <span className="xsmall muted">von {fmtPoints(c.max_points)} Punkten</span>}
            </div>
            {c.description && <p className="small muted au-grade-desc">{c.description}</p>}
            {rubric.kind === 'rubric' ? (
              <div className="au-levels-pick">
                {(c.levels ?? []).map((l) => (
                  <button key={l.id} type="button" className={`au-pick${f.level === l.id ? ' on' : ''}`} aria-pressed={f.level === l.id} disabled={disabled} onClick={() => onChange(setLevel(fill, c.id, l.id))} title={l.description || undefined}>
                    <span className="au-pick-title">{l.title}</span>
                    <span className="au-pick-pts">{fmtPoints(l.points)} P.</span>
                  </button>
                ))}
              </div>
            ) : (
              <label className="au-points-in">
                <span className="sr-only">Punkte für {c.title}</span>
                <input
                  inputMode="decimal"
                  disabled={disabled}
                  value={f.points === undefined ? '' : fmtPoints(f.points)}
                  placeholder="Punkte"
                  onChange={(e) => onChange(setCriterionPoints(fill, c.id, e.target.value))}
                />
                <span className="xsmall muted"> / {fmtPoints(c.max_points)}</span>
              </label>
            )}
            {open[c.id] || f.comment ? (
              <input aria-label={`Anmerkung zu ${c.title}`} placeholder="Anmerkung (optional)" value={f.comment ?? ''} maxLength={2000} disabled={disabled} onChange={(e) => onChange(setComment(fill, c.id, e.target.value))} />
            ) : (
              !disabled && (
                <button type="button" className="btn btn-sm btn-ghost au-note-btn" onClick={() => setOpen({ ...open, [c.id]: true })}>
                  Anmerkung
                  <span className="sr-only"> zu {c.title}</span>
                </button>
              )
            )}
          </div>
        );
      })}
      <p className="au-sum" aria-live="polite">
        Summe: <strong>{fmtPoints(total.points) || '0'}</strong> von {fmtPoints(max)} Punkten
        {!total.complete && <span className="xsmall muted"> · {rubric.criteria.length - total.done} Kriterium/Kriterien offen</span>}
      </p>
    </div>
  );
}

/** Ausgefülltes Raster (nur lesen): gewählte Stufe bzw. Punkte je Kriterium mit Anmerkung */
export function RubricView({ rubric, fill }: { rubric: Rubric; fill: RubricFill }) {
  return (
    <ul className="au-view">
      {rubric.criteria.map((c) => {
        const f = fill[c.id];
        const level = rubric.kind === 'rubric' ? (c.levels ?? []).find((l) => l.id === f?.level) : undefined;
        return (
          <li key={c.id}>
            <div className="au-view-head">
              <strong>{c.title}</strong>
              <span>
                {rubric.kind === 'rubric'
                  ? level
                    ? `${level.title} · ${fmtPoints(level.points)} P.`
                    : '–'
                  : f?.points !== undefined
                    ? `${fmtPoints(f.points)} von ${fmtPoints(c.max_points)} P.`
                    : '–'}
              </span>
            </div>
            {rubric.kind === 'rubric' && (
              <div className="au-view-levels" aria-hidden="true">
                {(c.levels ?? []).map((l) => (
                  <span key={l.id} className={`au-chip${f?.level === l.id ? ' on' : ''}`}>
                    {l.title}
                  </span>
                ))}
              </div>
            )}
            {f?.comment && <p className="small au-view-comment">{f.comment}</p>}
          </li>
        );
      })}
    </ul>
  );
}

/** Bewertungskriterien vorab (ohne Ausfüllung): Kriterium, Stufen mit Punkten bzw. Erwartung und Höchstpunkte */
export function RubricPreview({ rubric }: { rubric: Rubric }) {
  return (
    <ul className="au-view">
      {rubric.criteria.map((c) => (
        <li key={c.id}>
          <div className="au-view-head">
            <strong>{c.title}</strong>
            {rubric.kind === 'guide' && <span>bis {fmtPoints(c.max_points)} P.</span>}
          </div>
          {c.description && <p className="small muted au-view-comment">{c.description}</p>}
          {rubric.kind === 'rubric' && (
            <div className="au-view-levels">
              {(c.levels ?? []).map((l) => (
                <span key={l.id} className="au-chip" title={l.description || undefined}>
                  {l.title} · {fmtPoints(l.points)} P.
                </span>
              ))}
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}

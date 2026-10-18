/**
 * Kompetenzen einer Schülerin/eines Schülers: je Bereich Fortschritt, je Kompetenz Stufenbalken mit Einschätzung der
 * Lehrkraft und Selbsteinschätzung nebeneinander. Gemeinsam für Lehrkraft (einschätzen, bestätigen), Schüler/in
 * (selbst einschätzen) und Eltern (nur ansehen).
 */
import './kompetenzen.css';
import { Link } from 'react-router-dom';
import { SegmentedControl } from '../../components/ui';
import { formatDate } from '../../lib/dates';
import type { AssessmentEntry, CompetencyState, FrameworkState, ViewKind } from './api';
import { EVIDENCE_LABEL, evidenceHref, levelBucket, levelLabel, levelSummary, percent } from './logic';

export function LevelBar({ levels, teacher, own, large }: { levels: readonly string[]; teacher: number | null; own: number | null; large?: boolean }) {
  const n = levels.length;
  const bucket = levelBucket(teacher, n);
  const desc = [levelSummary(levels, teacher), own ? `Selbsteinschätzung: ${levelLabel(levels, own)}` : ''].filter(Boolean).join('. ');
  return (
    <span className={`cp-bar${large ? ' cp-bar-lg' : ''}`} role="img" aria-label={desc}>
      {levels.map((l, i) => (
        <span key={l + i} className={`cp-seg${teacher && i < teacher ? ` cp-b${bucket} on` : ''}`}>
          {own === i + 1 && <span className="cp-self-dot" />}
        </span>
      ))}
    </span>
  );
}

function EntryLine({ e, levels, who }: { e: AssessmentEntry; levels: readonly string[]; who: string }) {
  const href = evidenceHref(e.evidence_type, e.evidence_ref, e.evidence);
  return (
    <li className="cp-hist-item">
      <span className="small">
        <strong>{formatDate(e.date)}</strong> · {who}: {levelLabel(levels, e.level)}
        {e.by && e.kind === 'teacher' ? ` (${e.by})` : ''}
      </span>
      {e.comment && <div className="small">{e.comment}</div>}
      {e.evidence_type && (
        <div className="small muted">
          {EVIDENCE_LABEL[e.evidence_type]}
          {href ? (
            href.startsWith('/') ? (
              <>
                : <Link to={href}>{e.evidence || 'öffnen'}</Link>
              </>
            ) : (
              <>
                : <a href={href} target="_blank" rel="noopener noreferrer">{e.evidence}</a>
              </>
            )
          ) : e.evidence ? (
            `: ${e.evidence}`
          ) : null}
        </div>
      )}
    </li>
  );
}

export interface LevelsViewProps {
  fw: FrameworkState;
  mode: ViewKind;
  /** Lehrkraft */
  onAssess?: (c: CompetencyState) => void;
  onConfirm?: (c: CompetencyState) => void;
  /** Schüler/in */
  onSelf?: (c: CompetencyState, level: number) => void;
  filterSupport?: boolean;
}

export function LevelsView({ fw, mode, onAssess, onConfirm, onSelf, filterSupport }: LevelsViewProps) {
  const kid = mode !== 'staff';
  return (
    <div className="stack">
      {fw.areas.map((area) => {
        const comps = filterSupport ? area.competencies.filter((c) => c.support) : area.competencies;
        if (!comps.length) return null;
        return (
          <section key={area.id} className="card cp-area" aria-labelledby={`cp-a-${area.id}`}>
            <div className="card-head">
              <h3 id={`cp-a-${area.id}`}>{area.name}</h3>
              <span className="cp-progress-wrap">
                <progress className="cp-progress" max={100} value={Math.round(area.progress * 100)} aria-label={`Fortschritt ${area.name}`} />
                <span className="small mono">{percent(area.progress)}</span>
              </span>
            </div>
            <ul className="cp-list">
              {comps.map((c) => (
                <li key={c.id} className={`cp-comp${c.support ? ' cp-support' : ''}`}>
                  <div className="cp-comp-main">
                    {c.code && <span className="cp-code mono xsmall">{c.code}</span>}
                    <span className="cp-title">{c.title}</span>
                    {c.support && <span className="badge badge-warning">Unterstützung</span>}
                    {c.pending && mode === 'staff' && <span className="badge badge-info">Selbsteinschätzung offen</span>}
                  </div>
                  <LevelBar levels={fw.levels} teacher={c.teacher?.level ?? null} own={c.self?.level ?? null} large={kid} />
                  <div className="cp-values small">
                    <span>
                      <span className="muted">{kid ? 'Lehrkraft' : 'Lehrkraft'}: </span>
                      {c.teacher ? `${levelLabel(fw.levels, c.teacher.level)} (${formatDate(c.teacher.date)})` : 'noch nicht eingeschätzt'}
                    </span>
                    <span>
                      <span className="muted">{mode === 'self' ? 'Ich' : 'Selbst'}: </span>
                      {c.self ? levelLabel(fw.levels, c.self.level) : 'noch nicht eingeschätzt'}
                      {c.self && c.pending && mode !== 'staff' && <span className="muted"> (wartet auf die Lehrkraft)</span>}
                      {c.self && !c.pending && c.self.confirmed && <span className="muted"> (bestätigt)</span>}
                    </span>
                  </div>
                  {c.teacher?.comment && <div className="cp-comment small">{c.teacher.comment}</div>}
                  <div className="cp-actions">
                    {mode === 'staff' && onAssess && (
                      <button type="button" className="btn btn-sm" onClick={() => onAssess(c)}>
                        Einschätzen
                      </button>
                    )}
                    {mode === 'staff' && onConfirm && c.self && c.pending && (
                      <button type="button" className="btn btn-sm btn-primary" onClick={() => onConfirm(c)}>
                        Bestätigen
                      </button>
                    )}
                    {mode === 'self' && onSelf && (
                      <SegmentedControl
                        label={`So schätze ich mich ein: ${c.title}`}
                        value={c.self?.level ?? 0}
                        onChange={(v) => onSelf(c, v)}
                        options={fw.levels.map((l, i) => ({ value: i + 1, label: String(i + 1), title: l }))}
                      />
                    )}
                  </div>
                  {mode === 'self' && onSelf && <div className="xsmall muted">1 = {fw.levels[0]} · {fw.levels.length} = {fw.levels[fw.levels.length - 1]}</div>}
                  {c.history.length > 0 && (
                    <details className="cp-history">
                      <summary className="small">Verlauf ({c.history.length})</summary>
                      <ul className="cp-hist">
                        {c.history.map((e) => (
                          <EntryLine key={e.id} e={e} levels={fw.levels} who={e.kind === 'teacher' ? 'Lehrkraft' : mode === 'self' ? 'Ich' : 'Selbst'} />
                        ))}
                      </ul>
                    </details>
                  )}
                  {mode === 'staff' && c.links.length > 0 && (
                    <div className="xsmall muted">
                      Zugeordnet: {c.links.map((l) => l.title || `${l.item_type} ${l.item_id}`).join(', ')}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}

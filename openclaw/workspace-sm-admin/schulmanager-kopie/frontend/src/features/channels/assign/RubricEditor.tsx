/**
 * Bewertungsraster bearbeiten: Kriterien mit Stufen und Punkten (Raster) oder mit Freitext und Höchstpunkten
 * (Bewertungsleitfaden). Arbeitet mit Texteingaben (`RubricDraft`), die `draftToRubric` prüft.
 */
import { Icon } from '../../../components/Icon';
import { SegmentedControl } from '../../../components/ui';
import { newCriterion, switchKind, type CriterionDraft, type LevelDraft, type RubricDraft } from './logic';
import type { RubricKind } from './types';
import './aufgaben.css';

const KIND_OPTIONS: { value: RubricKind; label: string }[] = [
  { value: 'rubric', label: 'Raster (Stufen)' },
  { value: 'guide', label: 'Leitfaden (Freitext + Punkte)' },
];

export function RubricEditor({ value, onChange, disabled = false }: { value: RubricDraft; onChange: (d: RubricDraft) => void; disabled?: boolean }) {
  const setCriterion = (i: number, patch: Partial<CriterionDraft>) =>
    onChange({ ...value, criteria: value.criteria.map((c, k) => (k === i ? { ...c, ...patch } : c)) });
  const setLevel = (i: number, j: number, patch: Partial<LevelDraft>) =>
    setCriterion(i, { levels: value.criteria[i].levels.map((l, k) => (k === j ? { ...l, ...patch } : l)) });
  const move = (i: number, dir: -1 | 1) => {
    const to = i + dir;
    if (to < 0 || to >= value.criteria.length) return;
    const next = [...value.criteria];
    [next[i], next[to]] = [next[to], next[i]];
    onChange({ ...value, criteria: next });
  };
  return (
    <div className="au-editor stack-sm">
      <SegmentedControl<RubricKind> label="Art der Bewertung" value={value.kind} onChange={(k) => !disabled && onChange(switchKind(value, k))} options={KIND_OPTIONS} />
      {value.criteria.map((c, i) => (
        <fieldset key={c.id ?? `n${i}`} className="au-criterion" disabled={disabled}>
          <legend className="sr-only">Kriterium {i + 1}</legend>
          <div className="au-crit-head">
            <input aria-label={`Kriterium ${i + 1}: Name`} placeholder="Kriterium, z. B. Inhalt" value={c.title} maxLength={200} onChange={(e) => setCriterion(i, { title: e.target.value })} />
            {value.kind === 'guide' && (
              <label className="au-points">
                <span className="xsmall muted">max. Punkte</span>
                <input aria-label={`Kriterium ${i + 1}: Höchstpunkte`} inputMode="decimal" value={c.maxPoints} onChange={(e) => setCriterion(i, { maxPoints: e.target.value })} />
              </label>
            )}
            <div className="row" style={{ gap: 2 }}>
              <button type="button" className="btn btn-sm btn-ghost" onClick={() => move(i, -1)} disabled={i === 0} aria-label={`Kriterium ${i + 1} nach oben`}>
                ↑
              </button>
              <button type="button" className="btn btn-sm btn-ghost" onClick={() => move(i, 1)} disabled={i === value.criteria.length - 1} aria-label={`Kriterium ${i + 1} nach unten`}>
                ↓
              </button>
              <button type="button" className="btn btn-sm btn-ghost" onClick={() => onChange({ ...value, criteria: value.criteria.filter((_, k) => k !== i) })} disabled={value.criteria.length <= 1} aria-label={`Kriterium ${i + 1} entfernen`}>
                <Icon name="trash" />
              </button>
            </div>
          </div>
          <textarea
            className="au-desc"
            aria-label={`Kriterium ${i + 1}: ${value.kind === 'guide' ? 'Erwartung (Freitext)' : 'Beschreibung'}`}
            placeholder={value.kind === 'guide' ? 'Was wird erwartet? (Freitext)' : 'Beschreibung (optional)'}
            rows={value.kind === 'guide' ? 2 : 1}
            value={c.description}
            maxLength={2000}
            onChange={(e) => setCriterion(i, { description: e.target.value })}
          />
          {value.kind === 'rubric' && (
            <div className="au-levels">
              {c.levels.map((l, j) => (
                <div key={l.id ?? `l${j}`} className="au-level">
                  <input aria-label={`Kriterium ${i + 1}, Stufe ${j + 1}: Name`} placeholder="Stufe" value={l.title} maxLength={200} onChange={(e) => setLevel(i, j, { title: e.target.value })} />
                  <input
                    className="au-level-points"
                    aria-label={`Kriterium ${i + 1}, Stufe ${j + 1}: Punkte`}
                    inputMode="decimal"
                    placeholder="Pkt."
                    value={l.points}
                    onChange={(e) => setLevel(i, j, { points: e.target.value })}
                  />
                  <input
                    aria-label={`Kriterium ${i + 1}, Stufe ${j + 1}: Beschreibung`}
                    placeholder="Beschreibung (optional)"
                    value={l.description}
                    maxLength={2000}
                    onChange={(e) => setLevel(i, j, { description: e.target.value })}
                  />
                  <button type="button" className="btn btn-sm btn-ghost" onClick={() => setCriterion(i, { levels: c.levels.filter((_, k) => k !== j) })} disabled={c.levels.length <= 2} aria-label={`Stufe ${j + 1} entfernen`}>
                    <Icon name="close" />
                  </button>
                </div>
              ))}
              <button type="button" className="btn btn-sm btn-ghost" onClick={() => setCriterion(i, { levels: [...c.levels, { title: '', points: '0', description: '' }] })} disabled={c.levels.length >= 10}>
                <Icon name="plus" /> Stufe
              </button>
            </div>
          )}
        </fieldset>
      ))}
      <div>
        <button type="button" className="btn btn-sm" onClick={() => onChange({ ...value, criteria: [...value.criteria, newCriterion(value.kind)] })} disabled={disabled || value.criteria.length >= 30}>
          <Icon name="plus" /> Kriterium hinzufügen
        </button>
      </div>
    </div>
  );
}

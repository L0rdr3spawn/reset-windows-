import { Icon } from '../../../components/Icon';
import { HelpTip } from '../../../components/HelpTip';
import { bestPerKpi, fmt } from './logic';
import type { VariantSummary } from './types';
import './generator.css';

const SHORT: Record<string, string> = {
  class_gaps: 'Hohlstunden Klassen',
  teacher_gaps: 'Springstunden Lehrkräfte',
  site_changes: 'Standortwechsel',
  core_late: 'Hauptfächer spät',
  unplaced_hours: 'Unverplant',
  conflicts: 'Konflikte',
  cost: 'Strafpunkte',
};

/** Vergleichstabelle der Varianten: Kennzahlen nebeneinander, beste je Kennzahl und insgesamt markiert. */
export function VariantsTable({
  variants,
  best,
  selected,
  done,
  onSelect,
  onPreview,
  onApply,
  periodLabel,
}: {
  variants: VariantSummary[];
  best: number;
  selected: number;
  done: boolean;
  onSelect: (i: number) => void;
  onPreview: (i: number) => void;
  onApply: (i: number) => void;
  /** Zeitraum, für den die Varianten gerechnet wurden (nur mit Planzeiträumen) */
  periodLabel?: string;
}) {
  const bests = bestPerKpi(variants);
  const keys = variants[0]?.kpis.map((k) => k.key) ?? [];
  return (
    <div className="stack">
      <h3>
        Varianten vergleichen{' '}
        <HelpTip label="Erklärung: Varianten">
          Jede Variante rechnet mit einem anderen Startwert. Die beste hat die wenigsten Konflikte, dann die wenigsten unverplanten Stunden, dann die wenigsten Strafpunkte. Grün markiert den besten Wert je Kennzahl.
        </HelpTip>
      </h3>
      {periodLabel && (
        <p className="gv-period">
          <strong>Zeitraum:</strong> {periodLabel}
        </p>
      )}
      <div className="table-wrap">
        <table className="table table-compact gv-table">
          <thead>
            <tr>
              <th scope="col">Variante</th>
              <th scope="col" className="gr-numeric">
                Startwert
              </th>
              {keys.map((k) => (
                <th key={k} scope="col" className="gr-numeric">
                  {SHORT[k] ?? k}
                </th>
              ))}
              <th scope="col" className="gr-numeric">
                Geänderte Blöcke
              </th>
              <th scope="col">Aktion</th>
            </tr>
          </thead>
          <tbody>
            {variants.map((v) => (
              <tr key={v.index} className={v.index === selected ? 'gv-row-sel' : undefined}>
                <th scope="row">
                  {v.index + 1}{' '}
                  {v.index === best && (
                    <span className="gv-badge">
                      <Icon name="check" /> Beste
                    </span>
                  )}
                </th>
                <td className="gr-numeric">{String(v.stats.seed ?? v.seed)}</td>
                {v.kpis.map((k) => {
                  const isBest = bests[k.key]?.has(v.index);
                  return (
                    <td key={k.key} className={`gr-numeric${isBest ? ' gv-best' : ''}`}>
                      {fmt(k.after)}
                      {isBest && <span className="sr-only"> (bester Wert)</span>}
                    </td>
                  );
                })}
                <td className="gr-numeric">{v.moved}</td>
                <td>
                  <div className="row" style={{ flexWrap: 'nowrap' }}>
                    <button type="button" className="btn btn-sm" aria-pressed={v.index === selected} onClick={() => onSelect(v.index)}>
                      Auswerten
                    </button>
                    <button type="button" className="btn btn-sm" onClick={() => onPreview(v.index)}>
                      Ansehen
                    </button>
                    {done && (
                      <button type="button" className="btn btn-sm" onClick={() => onApply(v.index)}>
                        Übernehmen
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

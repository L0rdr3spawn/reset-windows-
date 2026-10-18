import type { ReactNode } from 'react';
import type { TimeRule } from '../api/types';
import { WEEKDAYS_SHORT } from '../lib/dates';
import { describeRule, emptyRule, ruleWeekGroups, toggleNum } from '../lib/rules';
import { DayPeriodGrid } from './grid/DayPeriodGrid';
import { HelpText } from './Help';
import { Icon } from './Icon';
import { WeekPatternInput } from './WeekPatternInput';

function ToggleRow({ label, count, values, render, onToggle }: { label: string; count: number; values: number[]; render: (i: number) => string; onToggle: (i: number) => void }) {
  return (
    <div role="group" aria-label={label}>
      <div className="small muted" style={{ marginBottom: 2 }}>
        {label} <span className="faint">(keine Auswahl = alle)</span>
      </div>
      <div className="toggle-grid">
        {Array.from({ length: count }, (_, i) => (
          <button key={i} type="button" className="toggle" aria-pressed={values.includes(i)} onClick={() => onToggle(i)}>
            {render(i)}
          </button>
        ))}
      </div>
    </div>
  );
}

/**
 * Editor für Sperr-/Rhythmusregeln (TimeRule): Wochen (jede Woche / ausgewählte Wochen / Rhythmus), Tage Mo–So,
 * Stunden. Beispiel: „Woche 1 Mittwoch weg“ = Ausgewählte Wochen 1 + Mi, Stunden leer; „jede 3. Woche ab Woche 2“ =
 * Rhythmus. Die Vorschau zeigt nur die unterschiedlichen Wochen statt einer Spalte je Woche.
 */
export function RuleEditor({
  rules,
  onChange,
  days,
  periods,
  label,
  addLabel = 'Regel hinzufügen',
  yearWeeks = 52,
  help,
}: {
  rules: TimeRule[];
  onChange: (rules: TimeRule[]) => void;
  /** Anzahl der Tage ab Montag (7 = Mo–So) */
  days: number;
  periods: number;
  label: string;
  addLabel?: string;
  /** Wochen des Schuljahres (Chips und Vorschau) */
  yearWeeks?: number;
  /** Hilfe an der Beschriftung (statt Erklärtext) */
  help?: ReactNode;
}) {
  const update = (i: number, r: TimeRule) => onChange(rules.map((x, j) => (j === i ? r : x)));
  const groups = rules.length ? ruleWeekGroups(rules, days, periods, yearWeeks) : [];
  return (
    <fieldset>
      <legend>{help ? <HelpText help={help}>{label}</HelpText> : label}</legend>
      {rules.length === 0 && <p className="small muted">Keine Regeln – immer verfügbar.</p>}
      {rules.map((r, i) => (
        <div className="rule-row" key={i}>
          <div className="row-between">
            <strong className="small">{describeRule(r)}</strong>
            <button type="button" className="btn btn-sm btn-ghost" onClick={() => onChange(rules.filter((_, j) => j !== i))} aria-label={`Regel ${i + 1} entfernen`}>
              <Icon name="trash" /> Entfernen
            </button>
          </div>
          <WeekPatternInput
            value={{ weeks: r.weeks, rhythm: r.rhythm ?? null }}
            onChange={(v) => update(i, { ...r, weeks: v.weeks, rhythm: v.rhythm ?? null })}
            yearWeeks={yearWeeks}
          />
          <ToggleRow label="Tage" count={days} values={r.days} render={(d) => WEEKDAYS_SHORT[d] ?? String(d + 1)} onToggle={(d) => update(i, { ...r, days: toggleNum(r.days, d) })} />
          <ToggleRow label="Stunden" count={periods} values={r.periods} render={(p) => `${p + 1}.`} onToggle={(p) => update(i, { ...r, periods: toggleNum(r.periods, p) })} />
          <div className="field">
            <label htmlFor={`rule-note-${label}-${i}`}>Notiz</label>
            <input id={`rule-note-${label}-${i}`} type="text" value={r.note} placeholder="z. B. Praxistag, Berufsschule" onChange={(e) => update(i, { ...r, note: e.target.value })} />
          </div>
        </div>
      ))}
      <div className="row" style={{ marginTop: 8 }}>
        <button type="button" className="btn btn-sm" onClick={() => onChange([...rules, emptyRule()])}>
          <Icon name="plus" /> {addLabel}
        </button>
      </div>
      {groups.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div className="small muted">Vorschau (rot = nicht verfügbar)</div>
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(10rem, 1fr))', gap: 12 }}>
            {groups.map((g) => (
              <div key={g.weeks.join(',')} aria-hidden="true">
                <div className="xsmall muted">{g.label}</div>
                <DayPeriodGrid
                  days={Array.from({ length: days }, (_, d) => ({ key: d, name: WEEKDAYS_SHORT[d] ?? String(d + 1) }))}
                  rows={Array.from({ length: periods }, (_, p) => ({ key: p, label: String(p + 1) }))}
                  label={`Vorschau: ${g.label}`}
                  gridClassName="mini"
                  columnTemplate={`1.6rem repeat(${days}, minmax(0, 1fr))`}
                  rowHeight={14}
                  minWidth={0}
                  cell={(d, p) => ({ blocked: false, tone: g.blocked.has(`${d}:${p}`) ? 'bad' : 'free' })}
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </fieldset>
  );
}

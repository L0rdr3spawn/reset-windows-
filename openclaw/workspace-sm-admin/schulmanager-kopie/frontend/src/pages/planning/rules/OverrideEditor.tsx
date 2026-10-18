/**
 * Ausnahmen (Gültigkeit) eines Bausteins: „Für Jahrgang 11–13: Nett“, „In Woche 1–2: Aus“ …
 * Jede Ausnahme hat eine Stufe, eine Gültigkeit (Jahrgänge, Klassen, Fächer, Lehrkräfte – je nach Baustein) und
 * optional Wochen (jede Woche, ausgewählte Wochen oder Rhythmus) sowie überschreibbare Parameter.
 */
import { useId } from 'react';
import { Icon } from '../../../components/Icon';
import { MultiSelect } from '../../../components/SearchSelect';
import { Field } from '../../../components/ui';
import { WeekPatternInput } from '../../../components/WeekPatternInput';
import { describeSelection } from '../../../lib/weeks';
import { LevelPicker } from './LevelPicker';
import { emptyOverride, scopeText, type RuleDef, type RuleOverride, type RulesState } from './model';

export function OverrideEditor({
  def,
  overrides,
  onChange,
  options,
  disabled,
}: {
  def: RuleDef;
  overrides: RuleOverride[];
  onChange: (next: RuleOverride[]) => void;
  options: RulesState['options'];
  disabled?: boolean;
}) {
  const id = useId();
  const names = {
    classes: new Map(options.classes.map((c) => [c.id, c.name])),
    subjects: new Map(options.subjects.map((s) => [s.id, s.name])),
    teachers: new Map(options.teachers.map((t) => [t.id, t.name])),
  };
  const update = (i: number, ov: RuleOverride) => onChange(overrides.map((x, j) => (j === i ? ov : x)));
  return (
    <div className="stack-sm">
      {overrides.length === 0 && <p className="small muted" style={{ margin: 0 }}>Keine Ausnahmen – der Baustein gilt überall gleich.</p>}
      {overrides.map((ov, i) => {
        const weeks = ov.weeks.length || ov.rhythm ? describeSelection({ weeks: ov.weeks, rhythm: ov.rhythm }) : 'jede Woche';
        return (
          <div key={i} className="rule-override stack-sm">
            <div className="row-between">
              <strong className="small">
                {scopeText(ov, names)} · {weeks}
              </strong>
              {!disabled && (
                <button type="button" className="btn btn-sm btn-ghost" onClick={() => onChange(overrides.filter((_, j) => j !== i))} aria-label={`Ausnahme ${i + 1} entfernen`}>
                  <Icon name="trash" /> Entfernen
                </button>
              )}
            </div>
            <LevelPicker value={ov.level} onChange={(level) => update(i, { ...ov, level })} label={`Wichtigkeit der Ausnahme ${i + 1}`} hard={def.hard} disabled={disabled} />
            {def.scope.includes('grades') && options.grades.length > 0 && (
              <div role="group" aria-label="Jahrgänge">
                <div className="small muted" style={{ marginBottom: 2 }}>
                  Jahrgänge <span className="faint">(keine Auswahl = alle)</span>
                </div>
                <div className="rule-grade-chips">
                  {options.grades.map((g) => (
                    <button
                      key={g}
                      type="button"
                      className="toggle"
                      aria-pressed={ov.grades.includes(g)}
                      disabled={disabled}
                      onClick={() => update(i, { ...ov, grades: ov.grades.includes(g) ? ov.grades.filter((x) => x !== g) : [...ov.grades, g].sort((a, b) => a - b) })}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {!disabled && def.scope.includes('classes') && (
              <MultiSelect label="Klassen" values={ov.classes} onChange={(classes) => update(i, { ...ov, classes })} options={options.classes.map((c) => ({ value: c.id, label: c.name, sub: `Jahrgang ${c.grade}` }))} />
            )}
            {!disabled && def.scope.includes('subjects') && (
              <MultiSelect label="Fächer" values={ov.subjects} onChange={(subjects) => update(i, { ...ov, subjects })} options={options.subjects.map((s) => ({ value: s.id, label: s.name, sub: s.core ? 'Hauptfach' : undefined }))} />
            )}
            {!disabled && def.scope.includes('teachers') && (
              <MultiSelect label="Lehrkräfte" values={ov.teachers} onChange={(teachers) => update(i, { ...ov, teachers })} options={options.teachers.map((t) => ({ value: t.id, label: t.name, keywords: t.id }))} />
            )}
            <WeekPatternInput value={{ weeks: ov.weeks, rhythm: ov.rhythm }} onChange={(v) => update(i, { ...ov, weeks: v.weeks, rhythm: v.rhythm ?? null })} yearWeeks={options.year_weeks} disabled={disabled} />
            {def.params
              .filter((p) => p.overridable)
              .map((p) => {
                const v = ov.params[p.key];
                const own = v !== undefined && v !== null;
                return (
                  <div key={p.key} className="field">
                    <label className="check">
                      <input type="checkbox" checked={own} disabled={disabled} onChange={(e) => update(i, { ...ov, params: e.target.checked ? { ...ov.params, [p.key]: p.min ?? 0 } : Object.fromEntries(Object.entries(ov.params).filter(([k]) => k !== p.key)) })} />
                      {' '}
                      „{p.label}“ in dieser Ausnahme anders
                    </label>
                    {own && p.kind === 'int' && (
                      <Field label={p.label} htmlFor={`${id}-${i}-${p.key}`}>
                        <input
                          id={`${id}-${i}-${p.key}`}
                          type="number"
                          min={(p.min ?? 0) + (p.one_based ? 1 : 0)}
                          max={(p.max ?? 99) + (p.one_based ? 1 : 0)}
                          value={Number(v) + (p.one_based ? 1 : 0)}
                          disabled={disabled}
                          onChange={(e) => update(i, { ...ov, params: { ...ov.params, [p.key]: Math.max(p.min ?? 0, parseInt(e.target.value || '0', 10) - (p.one_based ? 1 : 0)) } })}
                        />
                      </Field>
                    )}
                  </div>
                );
              })}
            <Field label="Notiz" htmlFor={`${id}-${i}-note`}>
              <input id={`${id}-${i}-note`} type="text" maxLength={120} value={ov.note} disabled={disabled} placeholder="z. B. Oberstufe, Praktikumswochen" onChange={(e) => update(i, { ...ov, note: e.target.value })} />
            </Field>
          </div>
        );
      })}
      {!disabled && (
        <div>
          <button type="button" className="btn btn-sm" onClick={() => onChange([...overrides, emptyOverride()])}>
            <Icon name="plus" /> Ausnahme hinzufügen
          </button>
        </div>
      )}
    </div>
  );
}

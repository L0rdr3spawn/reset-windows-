/**
 * Ein Baustein: Titel, Wichtigkeit, Wirkung („betrifft 12 Klassen · aktuell 5 Verstöße → Bericht“) und – aufklappbar –
 * Parameter, eigener Zahlenwert und Ausnahmen (Gültigkeit).
 */
import { useId, useState } from 'react';
import { Link } from 'react-router-dom';
import { HelpTip } from '../../../components/HelpTip';
import { Icon } from '../../../components/Icon';
import { Field } from '../../../components/ui';
import { LevelPicker } from './LevelPicker';
import { OverrideEditor } from './OverrideEditor';
import { levelForWeight, LEVEL_LABEL, weightFor, type Level, type RuleDef, type RuleItem, type RulesState } from './model';

function formatWeight(w: number): string {
  return w.toLocaleString('de-DE', { maximumFractionDigits: 2 });
}

export function RuleCard({
  def,
  item,
  onChange,
  options,
  disabled,
  advanced,
}: {
  def: RuleDef;
  item: RuleItem;
  onChange: (next: RuleItem) => void;
  options: RulesState['options'];
  disabled?: boolean;
  advanced: boolean;
}) {
  const id = useId();
  const [open, setOpen] = useState(item.overrides.length > 0);
  const isSwitch = def.control === 'switch';
  const level = item.level as Level;
  const off = item.level === 'aus';
  const weight = isSwitch ? null : weightFor(def.base, level, item.weight);
  const custom = !isSwitch && item.weight !== null && item.weight !== undefined && !levelForWeight(def.base, item.weight).exact;
  const violations = def.violations;
  const reportLink = def.report ? `/planung/bericht?detail=${def.report}` : null;
  return (
    <section className={`rule-card${off ? ' off' : ''}`} aria-labelledby={`${id}-t`}>
      <div className="rule-card-head">
        <h3 id={`${id}-t`}>
          {def.title} <HelpTip label={`Erklärung: ${def.title}`}>{def.text}{def.hard ? ` „Muss“: ${def.hard_text}` : ''}</HelpTip>
        </h3>
        {isSwitch ? (
          <label className="check">
            <input type="checkbox" checked={item.level !== 'aus'} disabled={disabled} onChange={(e) => onChange({ ...item, level: e.target.checked ? 'an' : 'aus' })} /> {item.level !== 'aus' ? 'An' : 'Aus'}
          </label>
        ) : (
          <LevelPicker value={level} onChange={(l) => onChange({ ...item, level: l, weight: null })} label={`Wichtigkeit: ${def.title}`} hard={def.hard} disabled={disabled} />
        )}
      </div>
      {!def.relevant && <p className="small muted" style={{ margin: '6px 0 0' }}>Kein Datenbezug: {def.requires_text}</p>}
      <div className="rule-effect">
        {def.affects_text && <span>betrifft {def.affects_text}</span>}
        {violations !== null && violations !== undefined && (
          <span>
            aktuell {violations.toLocaleString('de-DE')} {violations === 1 ? 'Verstoß' : 'Verstöße'}
            {reportLink && violations > 0 ? (
              <>
                {' · '}
                <Link to={reportLink}>im Qualitätsbericht ansehen</Link>
              </>
            ) : null}
          </span>
        )}
        {item.overrides.length > 0 && (
          <span>
            {item.overrides.length} Ausnahme{item.overrides.length !== 1 ? 'n' : ''}
          </span>
        )}
        {custom && weight !== null && <span>eigener Wert {formatWeight(weight)}</span>}
        {level === 'muss' && def.hard && <span>harte Regel</span>}
      </div>
      {!isSwitch && (
        <details className="disclosure" open={open} onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)} style={{ marginTop: 8 }}>
          <summary>
            Einstellungen und Ausnahmen
            {def.params.length ? ` · ${def.params.length} Einstellung${def.params.length !== 1 ? 'en' : ''}` : ''}
          </summary>
          <div className="stack-sm" style={{ marginTop: 8 }}>
            {def.params.map((p) => {
              const v = item.params[p.key];
              if (p.kind === 'bool')
                return (
                  <label key={p.key} className="check">
                    <input type="checkbox" checked={!!v} disabled={disabled} onChange={(e) => onChange({ ...item, params: { ...item.params, [p.key]: e.target.checked } })} /> {p.label}
                    {p.help && <HelpTip>{p.help}</HelpTip>}
                  </label>
                );
              if (p.kind === 'choice')
                return (
                  <Field key={p.key} label={p.label} htmlFor={`${id}-${p.key}`} help={p.help || undefined}>
                    <select id={`${id}-${p.key}`} value={String(v ?? '')} disabled={disabled} onChange={(e) => onChange({ ...item, params: { ...item.params, [p.key]: e.target.value } })}>
                      {p.choices.map(([k, label]) => (
                        <option key={k} value={k}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </Field>
                );
              const shown = Number(v ?? 0) + (p.one_based ? 1 : 0);
              return (
                <Field key={p.key} label={p.label} htmlFor={`${id}-${p.key}`} help={p.help || undefined}>
                  <input
                    id={`${id}-${p.key}`}
                    type="number"
                    min={(p.min ?? 0) + (p.one_based ? 1 : 0)}
                    max={Math.min(p.max ?? 99, p.key === 'core_latest_period' ? options.periods - 1 : p.max ?? 99) + (p.one_based ? 1 : 0)}
                    value={shown}
                    disabled={disabled}
                    onChange={(e) => onChange({ ...item, params: { ...item.params, [p.key]: Math.max(p.min ?? 0, parseInt(e.target.value || '0', 10) - (p.one_based ? 1 : 0)) } })}
                  />
                </Field>
              );
            })}
            {advanced && (
              <Field
                label="Eigener Zahlenwert (Feinsteuerung)"
                htmlFor={`${id}-w`}
                help={`Gewicht in der Kostenfunktion des Generators. „${LEVEL_LABEL.wichtig}“ entspricht ${formatWeight(def.base)}; die Stufen sind Vielfache davon (Aus 0, Nett ¼, Sehr wichtig ×4, Muss ×20). Leer = Wert der Stufe.`}
              >
                <input
                  id={`${id}-w`}
                  type="number"
                  min={0}
                  step="any"
                  value={item.weight ?? ''}
                  placeholder={weight !== null ? formatWeight(weight) : ''}
                  disabled={disabled}
                  onChange={(e) => {
                    const raw = e.target.value;
                    if (raw === '') return onChange({ ...item, weight: null });
                    const n = Math.max(0, Number(raw));
                    onChange({ ...item, weight: n, level: levelForWeight(def.base, n).level });
                  }}
                />
              </Field>
            )}
            {def.scope.length > 0 && (
              <div>
                <div className="small" style={{ marginBottom: 4 }}>
                  <strong>Ausnahmen</strong>{' '}
                  <HelpTip>
                    Hier gilt der Baustein anders als oben eingestellt – z. B. „Hohlstunden“ für die Oberstufe nur „Nett“, oder ein Baustein in den Praktikumswochen „Aus“. Mehrere Ausnahmen werden der Reihe nach angewendet, die letzte passende gewinnt.
                  </HelpTip>
                </div>
                <OverrideEditor def={def} overrides={item.overrides} onChange={(overrides) => onChange({ ...item, overrides })} options={options} disabled={disabled} />
              </div>
            )}
            {!disabled && (item.overrides.length > 0 || custom) && (
              <div>
                <button type="button" className="btn btn-sm btn-ghost" onClick={() => onChange({ ...item, overrides: [], weight: null })}>
                  <Icon name="refresh" /> Ausnahmen und eigenen Wert zurücksetzen
                </button>
              </div>
            )}
          </div>
        </details>
      )}
    </section>
  );
}

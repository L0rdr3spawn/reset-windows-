/**
 * Pendeln einer Lehrkraft zwischen Standorten (nur bei Schulen mit mehr als einem Standort eingeblendet):
 * nie · höchstens 1× am Tag · beliebig, dazu die Mindestpause beim Wechsel. Die Wegezeit je Standortpaar steht in den
 * Planungs-Einstellungen. Stundenplan-Generator und Vertretung halten sich daran; der Qualitätsbericht zählt Verstöße.
 */
import { Field } from '../../components/ui';

export type CommuteMode = 'never' | 'once' | 'free';

export const COMMUTE_OPTIONS: { value: CommuteMode; label: string }[] = [
  { value: 'never', label: 'nie pendeln (an einem Tag nur ein Standort)' },
  { value: 'once', label: 'höchstens 1× am Tag den Standort wechseln' },
  { value: 'free', label: 'beliebig pendeln' },
];

export function CommuteField({ mode, gap, onChange, disabled }: { mode: string; gap: number; onChange: (mode: CommuteMode, gap: number) => void; disabled?: boolean }) {
  const current: CommuteMode = mode === 'never' || mode === 'once' ? mode : 'free';
  return (
    <fieldset className="span-all stack-sm" disabled={disabled}>
      <legend>Pendeln zwischen Standorten</legend>
      <div className="form-grid">
        <Field label="Standortwechsel am selben Tag" htmlFor="md-commute-mode">
          <select id="md-commute-mode" value={current} onChange={(e) => onChange(e.target.value as CommuteMode, gap)}>
            {COMMUTE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </Field>
        <Field
          label="Mindestpause beim Wechsel (Minuten)"
          htmlFor="md-commute-gap"
          hint="Zwischen Ende der einen und Beginn der nächsten Stunde (Pausen und Freistunden zählen mit). 0 = nur die Wegezeit zwischen den Standorten."
        >
          <input
            id="md-commute-gap"
            type="number"
            min={0}
            max={240}
            step={5}
            value={gap}
            disabled={current === 'never'}
            onChange={(e) => onChange(current, Math.max(0, Math.min(240, parseInt(e.target.value || '0', 10) || 0)))}
          />
        </Field>
      </div>
    </fieldset>
  );
}

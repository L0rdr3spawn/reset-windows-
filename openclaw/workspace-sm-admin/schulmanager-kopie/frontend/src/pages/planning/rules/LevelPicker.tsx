/** Wichtigkeit eines Bausteins: Aus · Nett · Wichtig · Sehr wichtig · Muss (statt nackter Zahlen). */
import { LEVEL_LABEL, LEVELS, type Level } from './model';

const LEVEL_TITLE: Record<Level, string> = {
  aus: 'wird nicht beachtet',
  nett: 'zählt wenig – andere Ziele gehen vor',
  wichtig: 'normales Gewicht (Standard)',
  sehr_wichtig: 'zählt viermal so stark wie „Wichtig“',
  muss: 'zählt zwanzigmal so stark – praktisch eine harte Regel',
};

export function LevelPicker({ value, onChange, label, hard, disabled }: { value: Level; onChange: (l: Level) => void; label: string; hard?: boolean; disabled?: boolean }) {
  return (
    <div className="rule-levels" role="group" aria-label={label}>
      {LEVELS.map((l) => (
        <button
          key={l}
          type="button"
          className="toggle"
          aria-pressed={value === l}
          disabled={disabled}
          title={l === 'muss' && hard ? 'harte Regel – wird nie verletzt' : LEVEL_TITLE[l]}
          onClick={() => onChange(l)}
        >
          {LEVEL_LABEL[l]}
        </button>
      ))}
    </div>
  );
}

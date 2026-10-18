/**
 * Wochenangabe-Editor: „Jede Woche“ · „Ausgewählte Wochen“ (Chips 1 … Schuljahreswochen) · „Rhythmus“.
 *
 * Gilt überall, wo etwas nicht jede Woche stattfindet (Kurse, Stunden, Sperrzeiten, Wünsche, Zeitfenster,
 * Aufsichten). Der Rhythmus „alle k Wochen ab Woche s (bis e)“ zählt in laufenden Wochen 1 … 52 und wird als
 * `rhythm {every, from_week, to_week}` gespeichert (`weeks` ist dann leer); ausgewählte Wochen als `weeks`.
 *
 * Angezeigt und eingegeben werden Kalenderwochen (KW), solange der Schuljahreskalender im KW-Modus ist (`lib/weeks.ts`):
 * die Chips zeigen die KW der laufenden Woche, „Ab/Bis KW“ werden in laufende Wochen umgerechnet.
 */
import { useEffect, useId, useRef, useState, type KeyboardEvent } from 'react';
import type { WeekRhythm } from '../api/types';
import { DAY_CHIPS, MAX_WEEKS, normalizeWeeks, rhythmErrors, selectionWeeks, specFromWeeks, weekFromNumber, weekNumberOf, weekWord, weeksPreview } from '../lib/weeks';
import { Field, SegmentedControl } from './ui';
import './weeks.css';

export type WeekMode = 'all' | 'specific' | 'rhythm';

export interface WeekSelection {
  weeks: number[];
  rhythm?: WeekRhythm | null;
}

/** Anfangsmodus aus gespeicherten Daten: Rhythmus, ausgewählte Wochen oder jede Woche. */
export function initialWeekMode(sel: WeekSelection): WeekMode {
  if (sel.rhythm) return 'rhythm';
  return normalizeWeeks(sel.weeks).length ? 'specific' : 'all';
}

export const WEEK_MODES: WeekMode[] = ['all', 'specific', 'rhythm'];

const MODE_LABELS: Record<WeekMode, string> = { all: 'Jede Woche', specific: 'Ausgewählte Wochen', rhythm: 'Rhythmus' };

/** Eingabe der Rhythmus-Felder (`to` 0 = offen); `from`/`to` sind Anzeigenummern (KW im KW-Modus, sonst laufende Wochen). */
export interface PatternFields {
  every: number;
  from: number;
  to: number;
}

/** Rhythmus aus den Feldern; `null`, solange die Eingabe fehlerhaft ist (dann bleibt der alte Wert). */
export function selectionForPattern(p: PatternFields): WeekSelection | null {
  const { rhythm, errors } = patternRhythm(p);
  return errors.length || !rhythm ? null : { weeks: [], rhythm };
}

/** Rhythmus (laufende Wochen) und Fehlertexte aus den Eingabefeldern (KW → laufende Woche). */
export function patternRhythm(p: PatternFields): { rhythm: WeekRhythm | null; errors: string[] } {
  const word = weekWord();
  const errors: string[] = [];
  const from = weekFromNumber(p.from);
  const to = p.to ? weekFromNumber(p.to, true) : 0;
  if (word === 'KW') {
    if (p.from && from === null) errors.push(`KW ${p.from} gibt es in diesem Schuljahr nicht.`);
    if (p.to && to === null) errors.push(`KW ${p.to} gibt es in diesem Schuljahr nicht.`);
  }
  const r: WeekRhythm = { every: p.every, from_week: from ?? p.from, ...(p.to ? { to_week: to ?? p.to } : {}) };
  if (!errors.length) errors.push(...rhythmErrors(r, MAX_WEEKS));
  return { rhythm: errors.length ? null : r, errors };
}

/** Wert nach einem Moduswechsel. */
export function selectionForMode(m: WeekMode, value: WeekSelection, p: PatternFields): WeekSelection | null {
  if (m === 'all') return { weeks: [], rhythm: null };
  if (m === 'specific') {
    const kept = normalizeWeeks(value.weeks);
    // vom Rhythmus zu ausgewählten Wochen: die Wochen des Rhythmus als Ausgangsliste
    if (!kept.length && value.rhythm) return { weeks: normalizeWeeks(selectionWeeks(value, 52)), rhythm: null };
    return { weeks: kept, rhythm: null };
  }
  return selectionForPattern(p);
}

/** Wert nach Antippen eines Wochen-Chips (`total` = Wochen des Schuljahres; die letzte Woche lässt sich nicht abwählen). */
export function toggleWeekChip(value: WeekSelection, w: number, total: number): WeekSelection | null {
  const shown = value.weeks.length ? normalizeWeeks(value.weeks) : Array.from({ length: total }, (_, i) => i + 1);
  const next = shown.includes(w) ? shown.filter((x) => x !== w) : [...shown, w];
  if (!next.length) return null;
  // alle Wochen des Schuljahres ausgewählt = jede Woche
  return { weeks: next.length >= total ? [] : normalizeWeeks(next), rhythm: null };
}

/** Ausgewählte Wochen → bei regelmäßigem Abstand als Rhythmus anbieten (Vorschlag, nicht automatisch). */
export function suggestRhythm(weeks: readonly number[], total = 52): WeekRhythm | null {
  return specFromWeeks(weeks, total, total).rhythm;
}

function num(v: string): number {
  const n = parseInt(v, 10);
  return Number.isFinite(n) ? n : 0;
}

/** Chips 1 … n (laufende Wochen) mit Pfeiltasten (eine Tab-Station für die ganze Reihe). */
export function WeekChips({
  n,
  selected,
  onToggle,
  label,
  disabled,
}: {
  n: number;
  selected: readonly number[];
  onToggle: (w: number) => void;
  label: string;
  disabled?: boolean;
}) {
  const [focus, setFocus] = useState(0);
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  useEffect(() => {
    if (focus >= n) setFocus(0);
  }, [focus, n]);
  const move = (e: KeyboardEvent<HTMLButtonElement>, i: number) => {
    const next = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? i + 1 : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? i - 1 : e.key === 'Home' ? 0 : e.key === 'End' ? n - 1 : null;
    if (next === null) return;
    e.preventDefault();
    const t = Math.min(n - 1, Math.max(0, next));
    setFocus(t);
    refs.current[t]?.focus();
  };
  return (
    <div className="week-chips" role="group" aria-label={label}>
      {Array.from({ length: n }, (_, i) => {
        const w = i + 1;
        return (
          <button
            key={w}
            ref={(el) => {
              refs.current[i] = el;
            }}
            type="button"
            className="toggle"
            aria-pressed={selected.includes(w)}
            aria-label={`${weekWord()} ${weekNumberOf(w)}`}
            tabIndex={i === focus ? 0 : -1}
            disabled={disabled}
            onFocus={() => setFocus(i)}
            onKeyDown={(e) => move(e, i)}
            onClick={() => onToggle(w)}
          >
            {weekNumberOf(w)}
          </button>
        );
      })}
    </div>
  );
}

export function WeekPatternInput({
  value,
  onChange,
  yearWeeks = 52,
  label = 'Wochen',
  disabled,
}: {
  value: WeekSelection;
  onChange: (v: WeekSelection) => void;
  /** Wochen des Schuljahres (52 oder 53): Anzahl der Wochen-Chips und Vorschau des Rhythmus */
  yearWeeks?: number;
  label?: string;
  disabled?: boolean;
}) {
  const id = useId();
  const total = Math.max(1, Math.min(MAX_WEEKS, yearWeeks || 52));
  const [mode, setMode] = useState<WeekMode>(() => initialWeekMode(value));
  const [pattern, setPattern] = useState<PatternFields>(() =>
    value.rhythm
      ? { every: value.rhythm.every, from: weekNumberOf(value.rhythm.from_week), to: value.rhythm.to_week ? weekNumberOf(value.rhythm.to_week) : 0 }
      : { every: 2, from: weekNumberOf(1), to: 0 },
  );

  const { rhythm, errors } = patternRhythm(pattern);
  const word = weekWord();

  const emitPattern = (p: PatternFields) => {
    setPattern(p);
    const next = selectionForPattern(p);
    if (next) onChange(next);
  };

  const switchMode = (m: WeekMode) => {
    setMode(m);
    const next = selectionForMode(m, value, pattern);
    if (next) onChange(next);
  };

  const shown = mode === 'specific' ? (value.weeks.length ? normalizeWeeks(value.weeks) : Array.from({ length: total }, (_, i) => i + 1)) : [];
  const preview = mode === 'rhythm' && !errors.length && rhythm ? weeksPreview(selectionWeeks({ rhythm }, total), total) : '';

  return (
    <fieldset className="week-pattern" disabled={disabled}>
      <legend>{label}</legend>
      <SegmentedControl label={label} value={mode} options={WEEK_MODES.map((m) => ({ value: m, label: MODE_LABELS[m] }))} onChange={switchMode} />
      {mode === 'specific' && (
        <WeekChips
          n={total}
          selected={shown}
          label="Wochen des Schuljahres"
          disabled={disabled}
          onToggle={(w) => {
            const next = toggleWeekChip(value, w, total);
            if (next) onChange(next);
          }}
        />
      )}
      {mode === 'rhythm' && (
        <>
          <div className="week-rhythm">
            <Field label="Abstand (Wochen)" htmlFor={`${id}-every`} help="2 = jede zweite Woche, 3 = jede dritte Woche …">
              <input id={`${id}-every`} type="number" min={1} max={MAX_WEEKS} value={pattern.every} onChange={(e) => emitPattern({ ...pattern, every: num(e.target.value) })} />
            </Field>
            <Field label={`Ab ${word}`} htmlFor={`${id}-from`}>
              <input id={`${id}-from`} type="number" min={1} max={MAX_WEEKS} value={pattern.from} onChange={(e) => emitPattern({ ...pattern, from: num(e.target.value) })} />
            </Field>
            <Field label={`Bis ${word} (optional)`} htmlFor={`${id}-to`}>
              <input
                id={`${id}-to`}
                type="number"
                min={0}
                max={MAX_WEEKS}
                value={pattern.to || ''}
                onChange={(e) => emitPattern({ ...pattern, to: num(e.target.value) })}
              />
            </Field>
          </div>
          {errors.map((m) => (
            <span key={m} className="error-text" role="alert">
              {m}
            </span>
          ))}
          {!errors.length && preview && (
            <span className="week-preview" aria-live="polite">
              {preview}
            </span>
          )}
        </>
      )}
    </fieldset>
  );
}

/** Unterrichtstage Mo … So als Chips (`aria-label` „Montag“ …), z. B. für Schule und Klasse. */
export function DayChips({
  value,
  onChange,
  label,
  disabled,
}: {
  value: readonly number[];
  onChange: (days: number[]) => void;
  label: string;
  disabled?: boolean;
}) {
  return (
    <div className="week-chips" role="group" aria-label={label}>
      {DAY_CHIPS.map((c) => (
        <button
          key={c.day}
          type="button"
          className="toggle"
          aria-pressed={value.includes(c.day)}
          aria-label={c.name}
          disabled={disabled}
          onClick={() => {
            const next = value.includes(c.day) ? value.filter((d) => d !== c.day) : [...value, c.day].sort((a, b) => a - b);
            if (next.length) onChange(next);
          }}
        >
          {c.short}
        </button>
      ))}
    </div>
  );
}

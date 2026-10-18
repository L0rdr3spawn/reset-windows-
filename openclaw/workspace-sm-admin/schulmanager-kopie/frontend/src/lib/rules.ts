/**
 * Rhythmus-/Sperrregeln (TimeRule): Beschreibung & Auswertung (rein, testbar).
 */
import type { TimeRule } from '../api/types';
import { daysText, describeSelection, specActive, specFromWeeks } from './weeks';

export function emptyRule(): TimeRule {
  return { weeks: [], days: [], periods: [], note: '' };
}

/**
 * Trifft die Regel die laufende Woche `weekNo` (1-basiert), den Tag und die Stunde? Ohne `weekNo` (unbekannt) zählt
 * die Wochenangabe als erfüllt.
 */
export function ruleMatches(r: TimeRule, weekNo: number | null | undefined, day: number, period: number): boolean {
  return specActive(r, weekNo) && (!r.days.length || r.days.includes(day)) && (!r.periods.length || r.periods.includes(period));
}

function ranges(nums: number[]): string {
  const s = [...new Set(nums)].sort((a, b) => a - b);
  const out: string[] = [];
  let i = 0;
  while (i < s.length) {
    let j = i;
    while (j + 1 < s.length && (s[j + 1] as number) === (s[j] as number) + 1) j++;
    const a = (s[i] as number) + 1;
    const b = (s[j] as number) + 1;
    out.push(j > i ? `${a}.–${b}.` : `${a}.`);
    i = j + 1;
  }
  return out.join(', ');
}

/** „Woche 1 · Mi · ganztägig“, „jede 2. Woche ab Woche 10 · Mo–Fr · 1.–3. Stunde“ */
export function describeRule(r: TimeRule): string {
  const weeks = r.rhythm || r.weeks.length ? describeSelection(r) : '';
  const days = r.days.length ? daysText(r.days) : 'jeden Tag';
  const periods = r.periods.length ? `${ranges(r.periods)} Stunde` : 'ganztägig';
  return [weeks, days, periods].filter(Boolean).join(' · ') + (r.note ? ` (${r.note})` : '');
}

/** Gesperrte Felder für eine Woche: Set „Tag:Stunde“ (`weekNo` = laufende Woche). */
export function blockedSlots(rules: readonly TimeRule[], weekNo: number | null | undefined, days: number, periods: number): Set<string> {
  const out = new Set<string>();
  for (let d = 0; d < days; d++)
    for (let p = 0; p < periods; p++) if (rules.some((r) => ruleMatches(r, weekNo, d, p))) out.add(`${d}:${p}`);
  return out;
}

export interface RuleWeekGroup {
  /** laufende Wochen (1-basiert) der Gruppe */
  weeks: number[];
  /** „jede Woche“, „Woche 1, 3“, „jede 2. Woche ab Woche 10“ */
  label: string;
  blocked: Set<string>;
}

/**
 * Vorschau des Regel-Editors: nur die unterschiedlichen Wochen (statt einer Spalte je Woche) – gerechnet über die
 * laufenden Wochen 1 … `yearWeeks`.
 */
export function ruleWeekGroups(rules: readonly TimeRule[], days: number, periods: number, yearWeeks = 52): RuleWeekGroup[] {
  const total = Math.max(1, yearWeeks);
  const groups = new Map<string, RuleWeekGroup>();
  for (let l = 1; l <= total; l++) {
    const set = blockedSlots(rules, l, days, periods);
    const key = [...set].sort().join('|');
    const g = groups.get(key);
    if (g) g.weeks.push(l);
    else groups.set(key, { weeks: [l], label: '', blocked: set });
  }
  const list = [...groups.values()];
  for (const g of list) {
    const spec = specFromWeeks(g.weeks, total, total);
    g.label = list.length === 1 ? 'jede Woche' : describeSelection(spec);
  }
  return list;
}

/** Schaltet einen Wert in einer sortierten Zahlenliste um. */
export function toggleNum(list: readonly number[], n: number): number[] {
  return list.includes(n) ? list.filter((x) => x !== n) : [...list, n].sort((a, b) => a - b);
}

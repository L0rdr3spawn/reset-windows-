/**
 * Verfügbarkeit einer Lehrkraft als EINE Bedienung (reine Funktionen, testbar).
 *
 * Gespeichert werden weiterhin Regeln (`TimeRule`: Tage × Stunden, Rhythmus, „gilt ab“) – harte Sperrzeiten
 * (`unavailable`) und weiche Wünsche (`wishes`). Die Oberfläche zeigt sie als **Blöcke**: ein Block = Raster zum
 * Antippen (beliebige Felder Tag × Stunde) + Rhythmus + „gilt ab“ + Art (Sperre/Wunsch) + Notiz. Aus einem Block
 * entstehen beim Speichern eine oder mehrere Regeln (Tage mit gleichen Stunden werden gebündelt); beim Laden werden
 * Regeln mit gleicher Wochenangabe, gleichem Datum, gleicher Art und Notiz wieder zu einem Block vereint. Das ist
 * verlustfrei: die gesperrten Felder je Woche bleiben exakt erhalten.
 *
 * Altformate (Zeitfenster, Arbeitszeiten-Raster) liefert der Server schon als normale Regeln; deren reservierte Notiz
 * „Zeitfenster …“ wird zu „Arbeitszeit …“ (`detachRules`), damit sie frei bearbeitbar sind.
 */
import type { TimeRule, WeekRhythm } from '../../api/types';
import { normalizeWeeks, rhythmErrors } from '../../lib/weeks';
import { ruleWeekGroups } from '../../lib/rules';

const WINDOW_NOTE = 'Zeitfenster';

export type AvKind = 'hard' | 'wish';

export interface AvBlock {
  /** stabiler Schlüssel für React (nicht gespeichert) */
  id: string;
  kind: AvKind;
  /** ausgewählte Wochen (leer = Rhythmus bzw. jede Woche) */
  weeks: number[];
  rhythm: WeekRhythm | null;
  /** gilt ab Datum (ISO), leer = von Anfang des Schuljahres */
  valid_from: string;
  note: string;
  /** gesperrte bzw. gewünscht freie Felder „Tag:Stunde“ (0-basiert) */
  cells: Set<string>;
}

export const cellKey = (day: number, period: number) => `${day}:${period}`;

/** Notiz einer aus Zeitfenstern/Raster erzeugten Regel → normale Notiz (wie `teacher_profile.detach_note`). */
export function detachNote(note: string): string {
  const text = (note ?? '').trim();
  if (!text.startsWith(WINDOW_NOTE)) return text;
  const rest = text.slice(WINDOW_NOTE.length).replace(/^[:\s]+/, '').replace('Arbeitszeiten – ', '');
  return `Arbeitszeit: ${rest}`.replace(/[:\s]+$/, '');
}

export function detachRules(rules: readonly TimeRule[]): TimeRule[] {
  return rules.map((r) => ({ ...r, note: detachNote(r.note) }));
}

/** Größte Tage-/Stundenzahl, die die Regeln brauchen (damit beim Umrechnen nichts verloren geht). */
export function fitDims(rules: readonly TimeRule[], days: number, periods: number): { days: number; periods: number } {
  let d = days;
  let p = periods;
  for (const r of rules) {
    for (const x of r.days) d = Math.max(d, x + 1);
    for (const x of r.periods) p = Math.max(p, x + 1);
  }
  return { days: d, periods: p };
}

function sortedNums(list: readonly number[]): number[] {
  return [...new Set(list)].sort((a, b) => a - b);
}

function rhythmOf(r: TimeRule): WeekRhythm | null {
  return r.rhythm ? { every: r.rhythm.every, from_week: r.rhythm.from_week, to_week: r.rhythm.to_week ?? 0 } : null;
}

/** Gleiche Wochenangabe + Datum + Notiz + Art → gleicher Block. */
function blockKey(r: TimeRule, kind: AvKind): string {
  return JSON.stringify([kind, r.rhythm ? null : sortedNums(r.weeks), rhythmOf(r), r.valid_from ?? '', r.note ?? '']);
}

/** Felder, die eine Regel sperrt (leere Tage/Stunden = alle). */
export function ruleCells(r: TimeRule, days: number, periods: number): string[] {
  const ds = r.days.length ? r.days : Array.from({ length: days }, (_, i) => i);
  const ps = r.periods.length ? r.periods : Array.from({ length: periods }, (_, i) => i);
  const out: string[] = [];
  for (const d of ds) for (const p of ps) out.push(cellKey(d, p));
  return out;
}

let counter = 0;
export function newBlockId(): string {
  counter += 1;
  return `av${counter}`;
}

export function emptyBlock(kind: AvKind, validFrom = ''): AvBlock {
  return { id: newBlockId(), kind, weeks: [], rhythm: null, valid_from: validFrom, note: '', cells: new Set() };
}

/** Regeln → Blöcke (Sperren zuerst, dann Wünsche; Reihenfolge der ersten Regel bleibt erhalten). */
export function blocksFromRules(hard: readonly TimeRule[], wishes: readonly TimeRule[], days: number, periods: number): AvBlock[] {
  const out = new Map<string, AvBlock>();
  const add = (rules: readonly TimeRule[], kind: AvKind) => {
    for (const r of rules) {
      const key = blockKey(r, kind);
      let b = out.get(key);
      if (!b) {
        b = {
          id: newBlockId(),
          kind,
          weeks: r.rhythm ? [] : sortedNums(r.weeks),
          rhythm: rhythmOf(r),
          valid_from: r.valid_from ?? '',
          note: r.note ?? '',
          cells: new Set(),
        };
        out.set(key, b);
      }
      for (const c of ruleCells(r, days, periods)) b.cells.add(c);
    }
  };
  add(hard, 'hard');
  add(wishes, 'wish');
  return [...out.values()];
}

/** Block → Regeln: Tage mit gleichen Stunden werden zu einer Regel gebündelt. */
export function rulesFromBlock(b: AvBlock, periods: number): TimeRule[] {
  const byDay = new Map<number, number[]>();
  for (const key of b.cells) {
    const [d, p] = key.split(':').map(Number) as [number, number];
    const list = byDay.get(d) ?? [];
    list.push(p);
    byDay.set(d, list);
  }
  const byPeriods = new Map<string, { periods: number[]; days: number[] }>();
  for (const [d, ps] of [...byDay.entries()].sort((x, y) => x[0] - y[0])) {
    const list = sortedNums(ps);
    const key = list.join(',');
    const g = byPeriods.get(key) ?? { periods: list, days: [] };
    g.days.push(d);
    byPeriods.set(key, g);
  }
  return [...byPeriods.values()].map((g) => {
    const rule: TimeRule = {
      weeks: b.rhythm ? [] : [...b.weeks],
      days: g.days,
      periods: g.periods.length >= periods ? [] : g.periods,
      note: b.note,
      rhythm: b.rhythm ? { ...b.rhythm, to_week: b.rhythm.to_week ?? 0 } : null,
    };
    if (b.valid_from) rule.valid_from = b.valid_from;
    return rule;
  });
}

export function rulesFromBlocks(blocks: readonly AvBlock[], periods: number): { unavailable: TimeRule[]; wishes: TimeRule[] } {
  const unavailable: TimeRule[] = [];
  const wishes: TimeRule[] = [];
  for (const b of blocks) (b.kind === 'hard' ? unavailable : wishes).push(...rulesFromBlock(b, periods));
  return { unavailable, wishes };
}

// ------------------------------------------------------------------ Rhythmus-Auswahl
export type RhythmChoice = 'weekly' | 'every2' | 'every3' | 'every4' | 'custom' | 'weeks';

export const RHYTHM_LABELS: Record<RhythmChoice, string> = {
  weekly: 'Jede Woche',
  every2: 'Alle 2 Wochen',
  every3: 'Alle 3 Wochen',
  every4: 'Alle 4 Wochen',
  custom: 'Anderer Abstand …',
  weeks: 'Nur bestimmte Wochen (z. B. einmalig)',
};

/** Auswahlwert zu den gespeicherten Wochenangaben. */
export function rhythmChoice(b: Pick<AvBlock, 'weeks' | 'rhythm'>): RhythmChoice {
  if (b.rhythm) {
    if (b.rhythm.every <= 1) return 'weekly';
    if (b.rhythm.every === 2) return 'every2';
    if (b.rhythm.every === 3) return 'every3';
    if (b.rhythm.every === 4) return 'every4';
    return 'custom';
  }
  return normalizeWeeks(b.weeks).length ? 'weeks' : 'weekly';
}

/** Neue Wochenangabe nach Wechsel der Auswahl; `null`, wenn nichts zu ändern ist. */
export function applyRhythmChoice(b: Pick<AvBlock, 'weeks' | 'rhythm'>, choice: RhythmChoice): Pick<AvBlock, 'weeks' | 'rhythm'> {
  if (choice === 'weekly') return { weeks: [], rhythm: null };
  if (choice === 'weeks') return { weeks: b.weeks.length ? b.weeks : [1], rhythm: null };
  const every = choice === 'every2' ? 2 : choice === 'every3' ? 3 : choice === 'every4' ? 4 : Math.max(5, b.rhythm?.every ?? 5);
  const from = b.rhythm?.from_week ?? 1;
  return { weeks: [], rhythm: { every, from_week: from, to_week: b.rhythm?.to_week ?? 0 } };
}

/** Fehlermeldung zur Wochenangabe eines Blocks (oder `null`). */
export function blockError(b: AvBlock): string | null {
  if (b.rhythm) return rhythmErrors(b.rhythm)[0] ?? null;
  return null;
}

// ------------------------------------------------------------------ Texte, Vergleich, Kennzahlen
const DAY_SHORT = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

/** „Mo, Mi 1.–2. Std.“ – kompakte Beschreibung der Felder eines Blocks. */
export function describeCells(cells: ReadonlySet<string>, periods: number): string {
  const byDay = new Map<number, number[]>();
  for (const key of cells) {
    const [d, p] = key.split(':').map(Number) as [number, number];
    byDay.set(d, [...(byDay.get(d) ?? []), p]);
  }
  const groups = new Map<string, number[]>();
  for (const [d, ps] of [...byDay.entries()].sort((a, b) => a[0] - b[0])) {
    const key = sortedNums(ps).join(',');
    groups.set(key, [...(groups.get(key) ?? []), d]);
  }
  const parts: string[] = [];
  for (const [key, ds] of groups) {
    const ps = key.split(',').map(Number);
    const runs: string[] = [];
    let i = 0;
    while (i < ps.length) {
      let j = i;
      while (j + 1 < ps.length && (ps[j + 1] as number) === (ps[j] as number) + 1) j++;
      runs.push(i === j ? `${(ps[i] as number) + 1}.` : `${(ps[i] as number) + 1}.–${(ps[j] as number) + 1}.`);
      i = j + 1;
    }
    const when = ps.length >= periods ? 'ganztägig' : `${runs.join(', ')} Std.`;
    parts.push(`${ds.map((d) => DAY_SHORT[d] ?? String(d + 1)).join(', ')} ${when}`);
  }
  return parts.join('; ') || 'noch nichts markiert';
}

/** Kanonische Form einer Regel für den Vergleich (Reihenfolge, doppelte Werte und Notizen mit Zeitfenster-Präfix egal). */
function canon(r: TimeRule): string {
  return JSON.stringify([sortedNums(r.weeks), sortedNums(r.days), sortedNums(r.periods), detachNote(r.note), rhythmOf(r), r.valid_from ?? '']);
}

export function rulesEqual(a: readonly TimeRule[] | undefined, b: readonly TimeRule[] | undefined): boolean {
  const x = (a ?? []).map(canon).sort();
  const y = (b ?? []).map(canon).sort();
  return x.length === y.length && x.every((v, i) => v === y[i]);
}

/** Wenigste freie Stunden pro Woche über alle Wochengruppen (nur harte Sperren) – für den Deputat-Hinweis. */
export function minFreePerWeek(hard: readonly TimeRule[], days: number, periods: number, yearWeeks = 52): number {
  if (!hard.length) return days * periods;
  const groups = ruleWeekGroups(hard, days, periods, yearWeeks);
  return Math.min(...groups.map((g) => days * periods - g.blocked.size));
}

/** Heutiges Datum als ISO (lokal). */
export function todayISO(): string {
  const d = new Date();
  const m = `${d.getMonth() + 1}`.padStart(2, '0');
  const day = `${d.getDate()}`.padStart(2, '0');
  return `${d.getFullYear()}-${m}-${day}`;
}

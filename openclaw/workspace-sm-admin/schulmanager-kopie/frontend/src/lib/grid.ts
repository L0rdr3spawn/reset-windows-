/**
 * Rasteraufbau für den Stundenplan (rein, testbar).
 *
 * Jeder Tag bekommt so viele „Spuren“ (Unterspalten), wie gleichzeitig liegende
 * Blöcke nötig sind (z. B. Raumdoppelbelegung, Lehreransicht mit Kopplungen). Blöcke ohne Überschneidung werden in freie Spuren
 * rechts daneben verbreitert. Doppelstunden erhalten eine größere Zeilenspanne.
 */
import type { Cell, MoveOption } from '../api/types';
import { specActive } from './weeks';

export interface PlacedCell {
  cell: Cell;
  day: number;
  /** 0-basierte Startstunde */
  start: number;
  /** Anzahl Stunden (≥ 1) */
  length: number;
  /** 0-basierte Spur innerhalb des Tages */
  lane: number;
  /** Anzahl belegter Spuren (Verbreiterung) */
  laneSpan: number;
  /** CSS-Grid-Positionen (1-basiert) */
  gridRow: string;
  gridColumn: string;
}

export interface GridLayout {
  days: number;
  periods: number;
  dayLanes: number[];
  /** erste Spalte (1-basiert) je Tag */
  dayColumnStart: number[];
  columnTemplate: string;
  placed: PlacedCell[];
}

/**
 * Behält Zellen, die in der laufenden Woche `weekNo` liegen (jede Woche, ausgewählte Wochen oder Rhythmus). Nur für
 * Antworten ohne `week_info`: sonst enthält `TimetableView` nur die in der Woche aktiven Zellen.
 */
export function filterWeek(cells: readonly Cell[], weekNo: number | null | undefined): Cell[] {
  if (weekNo === null || weekNo === undefined || weekNo < 1) return [...cells];
  return cells.filter((c) => specActive({ weeks: c.weeks, rhythm: c.rhythm }, weekNo));
}

function sortCells(a: Cell, b: Cell): number {
  return a.start - b.start || b.length - a.length || a.subject.localeCompare(b.subject) || a.lesson_id.localeCompare(b.lesson_id);
}

/** Zellen der angezeigten Woche: der Server filtert, Antworten ohne `week_info` filtert `filterWeek`. */
export function weekCells(view: { cells: readonly Cell[]; week_no?: number | null; week_info?: unknown }): Cell[] {
  return view.week_info ? [...view.cells] : filterWeek(view.cells, view.week_no);
}

/**
 * `narrowDays`: Tage ohne Unterricht (Sa/So, `day_kind = kein_unterrichtstag`) bekommen eine schmale Spalte, solange
 * dort keine Zelle liegt (§16 E2).
 */
export function layoutTimetable(cells: readonly Cell[], days: number, periods: number, opts: { narrowDays?: Iterable<number> } = {}): GridLayout {
  const narrow = new Set(opts.narrowDays ?? []);
  const nDays = Math.max(1, days, ...cells.map((c) => c.day + 1));
  const nPeriods = Math.max(1, periods, ...cells.map((c) => c.start + Math.max(1, c.length)));
  const byDay: Cell[][] = Array.from({ length: nDays }, () => []);
  for (const c of cells) {
    if (c.day >= 0 && c.start >= 0) byDay[c.day]?.push(c);
  }

  const dayLanes: number[] = [];
  const temp: { cell: Cell; day: number; start: number; length: number; lane: number; laneSpan: number }[] = [];

  for (let d = 0; d < nDays; d++) {
    const list = (byDay[d] ?? []).slice().sort(sortCells);
    const occ: boolean[][] = [];
    const free = (lane: number, s: number, len: number) => {
      const row = occ[lane];
      if (!row) return true;
      for (let p = s; p < s + len; p++) if (row[p]) return false;
      return true;
    };
    const mark = (lane: number, s: number, len: number) => {
      if (!occ[lane]) occ[lane] = new Array<boolean>(nPeriods).fill(false);
      const row = occ[lane] as boolean[];
      for (let p = s; p < s + len; p++) row[p] = true;
    };
    const dayItems: (typeof temp)[number][] = [];
    for (const c of list) {
      const len = Math.max(1, c.length || 1);
      let lane = 0;
      while (!free(lane, c.start, len)) lane++;
      mark(lane, c.start, len);
      dayItems.push({ cell: c, day: d, start: c.start, length: len, lane, laneSpan: 1 });
    }
    const lanes = Math.max(1, occ.length);
    // nach rechts verbreitern, solange frei
    for (const it of dayItems) {
      while (it.lane + it.laneSpan < lanes && free(it.lane + it.laneSpan, it.start, it.length)) {
        mark(it.lane + it.laneSpan, it.start, it.length);
        it.laneSpan++;
      }
    }
    dayLanes.push(lanes);
    temp.push(...dayItems);
  }

  const dayColumnStart: number[] = [];
  let col = 2; // Spalte 1 = Zeiten
  for (let d = 0; d < nDays; d++) {
    dayColumnStart.push(col);
    col += dayLanes[d] ?? 1;
  }

  const parts: string[] = ['minmax(3.6rem, max-content)'];
  for (let d = 0; d < nDays; d++) {
    const l = dayLanes[d] ?? 1;
    if (narrow.has(d) && !(byDay[d] ?? []).length) {
      parts.push('minmax(2.5rem, 0.3fr)');
      continue;
    }
    const fr = +(1 / l).toFixed(4);
    for (let i = 0; i < l; i++) parts.push(`minmax(0, ${fr}fr)`);
  }

  const placed: PlacedCell[] = temp.map((t) => ({
    ...t,
    gridRow: `${t.start + 2} / span ${t.length}`,
    gridColumn: `${(dayColumnStart[t.day] ?? 2) + t.lane} / span ${t.laneSpan}`,
  }));

  return { days: nDays, periods: nPeriods, dayLanes, dayColumnStart, columnTemplate: parts.join(' '), placed };
}

export type SlotState = 'ok' | 'conflict' | 'unknown' | 'origin';

/** Zustand eines Zielfelds beim Ziehen (grün/rot). */
export function slotState(
  options: readonly MoveOption[] | null | undefined,
  day: number,
  start: number,
  origin?: { day: number; start: number } | null,
): SlotState {
  if (origin && origin.day === day && origin.start === start) return 'origin';
  if (!options) return 'unknown';
  const o = options.find((x) => x.day === day && x.start === start);
  if (!o) return 'unknown';
  return o.ok ? 'ok' : 'conflict';
}

export function findOption(options: readonly MoveOption[] | null | undefined, day: number, start: number): MoveOption | undefined {
  return options?.find((x) => x.day === day && x.start === start);
}

/** Zellen nach Tagen gruppiert und sortiert (Listen-/Handyansicht). */
export function cellsByDay(cells: readonly Cell[], days: number): Cell[][] {
  const out: Cell[][] = Array.from({ length: Math.max(days, ...cells.map((c) => c.day + 1), 0) }, () => []);
  for (const c of cells) out[c.day]?.push(c);
  for (const list of out) list.sort(sortCells);
  return out;
}

/** Text für Stundenangabe, z. B. „3.“ oder „3.–4.“ */
export function periodRangeLabel(start: number, length: number): string {
  return length > 1 ? `${start + 1}.–${start + length}.` : `${start + 1}.`;
}

/** Zeile wie „M · MUE · R101“ */
export function cellSummary(c: Pick<Cell, 'subject' | 'teachers' | 'rooms' | 'label'>): string {
  return [c.label || c.subject, c.teachers.join(', '), c.rooms.join(', ')].filter(Boolean).join(' · ');
}

/** Hat der Block mehrere parallele Teile (Kopplung)? */
export function isCoupled(c: Pick<Cell, 'parts'>): boolean {
  return (c.parts?.length ?? 0) > 1;
}

/** Vereinheitlicht `periods` (Strings oder {index,label,time}). */
export function normalizePeriods(periods: readonly (string | { index?: number; label?: string; time?: string })[] | null | undefined): {
  label: string;
  time: string;
}[] {
  return (periods ?? []).map((p, i) => {
    if (typeof p === 'string') return { label: `${i + 1}.`, time: p };
    return { label: p.label || `${i + 1}.`, time: p.time ?? '' };
  });
}

/** Menge gesperrter Felder „Tag:Stunde“ → Hinweistext. */
export function blockedMap(blocked: readonly { day: number; period: number; note: string }[] | null | undefined): Map<string, string> {
  const m = new Map<string, string>();
  for (const b of blocked ?? []) m.set(`${b.day}:${b.period}`, b.note);
  return m;
}

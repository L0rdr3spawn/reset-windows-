import { describe, expect, it } from 'vitest';
import type { Cell } from '../../api/types';
import { blockedMap, cellsByDay, filterWeek, layoutTimetable, normalizePeriods, periodRangeLabel, slotState } from '../grid';

function cell(id: string, day: number, start: number, length = 1, extra: Partial<Cell> = {}): Cell {
  return {
    lesson_id: id,
    course_id: `C${id}`,
    day,
    start,
    length,
    weeks: [],
    subject: 'M',
    subject_name: 'Mathe',
    color: '#4f86c6',
    teachers: ['MUE'],
    rooms: ['R1'],
    classes: ['5a'],
    label: '',
    locked: false,
    parts: [{ subject: 'M', teacher: 'MUE', room: 'R1', label: '' }],
    ...extra,
  };
}

describe('layoutTimetable', () => {
  it('legt Einzel- und Doppelstunden ohne Überschneidung in eine Spur', () => {
    const l = layoutTimetable([cell('a', 0, 0), cell('b', 0, 1, 2), cell('c', 1, 3)], 5, 8);
    expect(l.dayLanes).toEqual([1, 1, 1, 1, 1]);
    const b = l.placed.find((p) => p.cell.lesson_id === 'b');
    expect(b?.gridRow).toBe('3 / span 2');
    expect(b?.gridColumn).toBe('2 / span 1'); // Montag
    // Tag 1 beginnt in Spalte 3 (Spalte 1 = Zeiten, Spalte 2 = Montag)
    expect(l.dayColumnStart).toEqual([2, 3, 4, 5, 6]);
  });

  it('verteilt gleichzeitige Blöcke auf Spuren und verbreitert freie', () => {
    const l = layoutTimetable([cell('a', 0, 0), cell('b', 0, 0), cell('c', 0, 2)], 2, 6);
    expect(l.dayLanes[0]).toBe(2);
    const a = l.placed.find((p) => p.cell.lesson_id === 'a');
    const b = l.placed.find((p) => p.cell.lesson_id === 'b');
    const c = l.placed.find((p) => p.cell.lesson_id === 'c');
    expect(a?.lane).not.toBe(b?.lane);
    expect(c?.laneSpan).toBe(2); // allein → volle Breite
    expect(l.dayColumnStart).toEqual([2, 4]);
    expect(l.columnTemplate.split(') ').length).toBe(4); // Zeit + 2 Spuren + 1
  });

  it('erweitert das Raster bei Blöcken außerhalb der Stundenzahl', () => {
    const l = layoutTimetable([cell('x', 0, 9, 2)], 5, 8);
    expect(l.periods).toBe(11);
  });
});

describe('Hilfsfunktionen', () => {
  it('filterWeek (Antworten ohne week_info) berücksichtigt Wochenlisten und Rhythmus', () => {
    const cells = [cell('a', 0, 0, 1, { weeks: [1] }), cell('b', 0, 1, 1, { weeks: [2] }), cell('c', 0, 2), cell('d', 0, 3, 1, { rhythm: { every: 2, from_week: 2 } })];
    expect(filterWeek(cells, 1).map((c) => c.lesson_id)).toEqual(['a', 'c']);
    expect(filterWeek(cells, 2).map((c) => c.lesson_id)).toEqual(['b', 'c', 'd']);
    expect(filterWeek(cells, null).map((c) => c.lesson_id)).toEqual(['a', 'b', 'c', 'd']);
  });

  it('slotState liefert grün/rot/Ursprung', () => {
    const opts = [
      { day: 0, start: 1, ok: true, conflicts: [] },
      { day: 0, start: 2, ok: false, conflicts: ['Lehrkraft belegt'] },
    ];
    expect(slotState(opts, 0, 1)).toBe('ok');
    expect(slotState(opts, 0, 2)).toBe('conflict');
    expect(slotState(opts, 0, 3)).toBe('unknown');
    expect(slotState(opts, 0, 1, { day: 0, start: 1 })).toBe('origin');
    expect(slotState(null, 0, 1)).toBe('unknown');
  });

  it('normalizePeriods akzeptiert Strings und Objekte', () => {
    expect(normalizePeriods(['07:55', { index: 1, label: '2.', time: '08:45' }])).toEqual([
      { label: '1.', time: '07:55' },
      { label: '2.', time: '08:45' },
    ]);
  });

  it('cellsByDay sortiert nach Beginn', () => {
    const d = cellsByDay([cell('b', 1, 3), cell('a', 1, 0)], 5);
    expect(d[1]?.map((c) => c.lesson_id)).toEqual(['a', 'b']);
  });

  it('blockedMap und periodRangeLabel', () => {
    expect(blockedMap([{ day: 2, period: 0, note: 'Praxistag' }]).get('2:0')).toBe('Praxistag');
    expect(periodRangeLabel(2, 2)).toBe('3.–4.');
    expect(periodRangeLabel(0, 1)).toBe('1.');
  });
});

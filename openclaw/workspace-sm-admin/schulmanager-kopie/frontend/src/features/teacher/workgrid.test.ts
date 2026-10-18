import { describe, expect, it } from 'vitest';
import { asGrid, describeGrid, gridBlocked, gridEqual, gridFromWindows, gridKey, gridOut, setGridDay, setGridWeeks, toggleGridCell } from './windows';

const TIMES = ['07:55', '08:45', '09:50', '10:40', '11:45', '12:35'];

describe('Arbeitszeiten-Raster', () => {
  it('Stunde antippen sperrt, nochmal antippen gibt frei', () => {
    let g = asGrid({});
    g = toggleGridCell(g, 0, 0, 0);
    expect(g.blocked).toEqual([{ week: 0, day: 0, periods: [0] }]);
    expect(describeGrid(g)).toBe('jede Woche, 1 Stunde gesperrt');
    g = toggleGridCell(g, 0, 0, 0);
    expect(g.blocked).toEqual([]);
    expect(gridOut(g)).toEqual({});
  });

  it('ganzen Tag sperren und freigeben', () => {
    const g = setGridDay(asGrid({}), 0, 4, 6, true);
    expect(g.blocked[0]?.periods).toEqual([0, 1, 2, 3, 4, 5]);
    expect(setGridDay(g, 0, 4, 6, false).blocked).toEqual([]);
  });

  it('Woche hinzufügen übernimmt das Muster, danach Woche 2 einzeln ändern', () => {
    let g = toggleGridCell(asGrid({}), 0, 0, 0);
    g = setGridWeeks(g, 2);
    expect(g.weeks).toBe(2);
    expect(gridBlocked(g).has(gridKey(1, 0, 0))).toBe(true);
    g = toggleGridCell(g, 1, 0, 0);
    expect(gridBlocked(g).has(gridKey(1, 0, 0))).toBe(false);
    expect(describeGrid(g)).toBe('Wechsel über 2 Wochen, 1 Stunde gesperrt');
    // bis 52 Wochen, nicht mehr
    expect(setGridWeeks(g, 60).weeks).toBe(52);
    // Wochen entfernen schneidet ab
    expect(setGridWeeks(setGridWeeks(g, 4), 1).blocked).toEqual([{ week: 0, day: 0, periods: [0] }]);
  });

  it('alte Zeitfenster werden zum Raster', () => {
    const g = gridFromWindows([{ days: [0, 1, 2, 3, 4], start: '10:00', end: '18:00', weeks: [] }], TIMES, 45, 5);
    expect(g.weeks).toBe(1);
    expect(g.blocked.find((b) => b.day === 0)?.periods).toEqual([0, 1, 2]);
    expect(gridEqual({}, { weeks: 1, blocked: [] })).toBe(true);
  });
});

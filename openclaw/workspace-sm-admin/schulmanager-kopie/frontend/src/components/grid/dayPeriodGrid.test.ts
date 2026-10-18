import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { DayPeriodGrid, dayColumnStarts, rowLine, type GridCell, type GridDay, type GridRow } from './DayPeriodGrid';

const days: GridDay[] = [
  { key: 'mo', name: 'Montag', date: '12.10.', today: true },
  { key: 'di', name: 'Dienstag', lanes: 2 },
  { key: 'sa', name: 'Samstag', short: 'Sa', off: true, divider: true },
];
const rows: GridRow[] = [
  { key: 0, label: '1.', time: '08:00', heading: 'Pause 1' },
  { key: 1, label: '2.', breakAfter: true },
];

describe('DayPeriodGrid', () => {
  it('Achsen: Spaltenstart, Zeilennummer mit Gruppenüberschrift', () => {
    expect(dayColumnStarts(days)).toEqual([2, 3, 5]);
    expect(rowLine(rows, 0)).toBe(3);
    expect(rowLine(rows, 1)).toBe(4);
  });

  it('Kopf, Zeit, Pause, Wochenende, Zellzustände und Ganztagsfeld', () => {
    const html = renderToStaticMarkup(
      createElement(DayPeriodGrid, {
        days: [...days.slice(0, 2), { ...days[2]!, fill: 'frei' }],
        rows,
        label: 'Test',
        cell: (d: number, r: number): GridCell | null => (d === 0 && r === 0 ? { tone: 'good' as const, content: 'x', title: 'T' } : d === 1 && r === 1 ? { blocked: true, heat: 0.5 } : null),
      }),
    );
    expect(html).toContain('aria-label="Test"');
    expect(html).toContain('tt-head today');
    expect(html).toContain('aria-current="date"');
    expect(html).toContain('tt-time break-after');
    expect(html).toContain('tt-group');
    expect(html).toContain('tone-good');
    expect(html).toContain('blocked');
    expect(html).toContain('--heat:0.5');
    expect(html).toContain('tt-day-fill');
    expect(html).toContain('<abbr title="Samstag – Kein Unterricht">Sa</abbr>');
    expect(html).toContain('day-divider');
  });
});

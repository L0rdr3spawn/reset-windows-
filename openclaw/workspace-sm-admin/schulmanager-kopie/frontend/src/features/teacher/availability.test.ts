import { describe, expect, it } from 'vitest';
import type { TimeRule } from '../../api/types';
import {
  applyRhythmChoice,
  blocksFromRules,
  cellKey,
  describeCells,
  detachNote,
  detachRules,
  emptyBlock,
  fitDims,
  minFreePerWeek,
  rhythmChoice,
  rulesEqual,
  rulesFromBlocks,
} from './availability';
import { periodsFromRange } from './ExceptionCard';

const rule = (p: Partial<TimeRule>): TimeRule => ({ weeks: [], days: [], periods: [], note: '', ...p });

describe('Verfügbarkeit: Blöcke ↔ Regeln', () => {
  it('Regeln mit gleicher Wochenangabe werden ein Block und verlustfrei zurückgerechnet', () => {
    const hard = [rule({ days: [0, 2], periods: [0, 1] }), rule({ days: [4], periods: [5] }), rule({ days: [1], rhythm: { every: 2, from_week: 2, to_week: 0 } })];
    const blocks = blocksFromRules(hard, [], 5, 8);
    expect(blocks).toHaveLength(2);
    expect(blocks[0]?.cells.has(cellKey(0, 1))).toBe(true);
    expect(blocks[1]?.cells.size).toBe(8); // ganzer Dienstag
    const back = rulesFromBlocks(blocks, 8).unavailable;
    const again = rulesFromBlocks(blocksFromRules(back, [], 5, 8), 8).unavailable;
    expect(rulesEqual(back, again)).toBe(true);
    const cells = (rs: TimeRule[]) => new Set(blocksFromRules(rs, [], 5, 8).flatMap((b) => [...b.cells].map((c) => `${b.rhythm?.every ?? 1}|${c}`)));
    expect(cells(back)).toEqual(cells(hard));
    expect(back.find((r) => r.rhythm)?.periods).toEqual([]); // ganzer Tag
  });

  it('Sperre und Wunsch bleiben getrennt, „gilt ab“ und Notiz trennen Blöcke', () => {
    const blocks = blocksFromRules(
      [rule({ days: [2], valid_from: '2026-11-02' }), rule({ days: [2] })],
      [rule({ days: [2] })],
      5,
      6,
    );
    expect(blocks.map((b) => [b.kind, b.valid_from])).toEqual([
      ['hard', '2026-11-02'],
      ['hard', ''],
      ['wish', ''],
    ]);
    const out = rulesFromBlocks(blocks, 6);
    expect(out.unavailable[0]?.valid_from).toBe('2026-11-02');
    expect(out.unavailable[1]?.valid_from).toBeUndefined();
    expect(out.wishes).toHaveLength(1);
  });

  it('beliebige Felder ergeben gebündelte Regeln; leerer Block erzeugt nichts', () => {
    const b = emptyBlock('hard');
    b.cells = new Set([cellKey(0, 0), cellKey(1, 0), cellKey(2, 3)]);
    const rules = rulesFromBlocks([b], 8).unavailable;
    expect(rules).toHaveLength(2);
    expect(rules.find((r) => r.periods.includes(0))?.days).toEqual([0, 1]);
    expect(rulesFromBlocks([emptyBlock('wish')], 8).wishes).toEqual([]);
    expect(describeCells(b.cells, 8)).toBe('Mo, Di 1. Std.; Mi 4. Std.');
  });

  it('Regeln außerhalb der Tabelle vergrößern sie (nichts geht verloren)', () => {
    expect(fitDims([rule({ days: [6], periods: [9] })], 5, 8)).toEqual({ days: 7, periods: 10 });
  });
});

describe('Verfügbarkeit: Rhythmus, Notizen, Vergleich', () => {
  it('Rhythmus-Auswahl', () => {
    expect(rhythmChoice({ weeks: [], rhythm: null })).toBe('weekly');
    expect(rhythmChoice({ weeks: [3], rhythm: null })).toBe('weeks');
    expect(rhythmChoice({ weeks: [], rhythm: { every: 3, from_week: 1, to_week: 0 } })).toBe('every3');
    expect(rhythmChoice({ weeks: [], rhythm: { every: 7, from_week: 1, to_week: 0 } })).toBe('custom');
    expect(applyRhythmChoice({ weeks: [], rhythm: null }, 'every2').rhythm).toEqual({ every: 2, from_week: 1, to_week: 0 });
    expect(applyRhythmChoice({ weeks: [], rhythm: { every: 2, from_week: 4, to_week: 0 } }, 'weekly')).toEqual({ weeks: [], rhythm: null });
  });

  it('Zeitfenster-Notizen werden zu normalen Notizen', () => {
    expect(detachNote('Zeitfenster: verfügbar 10:00–18:30')).toBe('Arbeitszeit: verfügbar 10:00–18:30');
    expect(detachNote('Zeitfenster: Arbeitszeiten – gesperrt')).toBe('Arbeitszeit: gesperrt');
    expect(detachNote('Praxistag')).toBe('Praxistag');
    expect(detachRules([rule({ days: [1], note: 'Zeitfenster: nicht verfügbar' })])[0]?.note).toBe('Arbeitszeit: nicht verfügbar');
  });

  it('Vergleich ignoriert Reihenfolge und doppelte Werte', () => {
    expect(rulesEqual([rule({ days: [1, 0] }), rule({ days: [4] })], [rule({ days: [4] }), rule({ days: [0, 1, 1] })])).toBe(true);
    expect(rulesEqual([rule({ days: [1] })], [rule({ days: [1], valid_from: '2026-11-02' })])).toBe(false);
  });

  it('engste Woche für den Deputat-Hinweis', () => {
    expect(minFreePerWeek([], 5, 8)).toBe(40);
    expect(minFreePerWeek([rule({ days: [2] })], 5, 8)).toBe(32);
    // jede 2. Woche zusätzlich Freitag weg: engste Woche hat 24 freie Stunden
    expect(minFreePerWeek([rule({ days: [2] }), rule({ days: [4], rhythm: { every: 2, from_week: 1, to_week: 0 } })], 5, 8)).toBe(24);
  });
});

describe('Ausnahme: Stunden', () => {
  it('von/bis → 0-basierte Liste', () => {
    expect(periodsFromRange(null, null, 8)).toEqual([]);
    expect(periodsFromRange(5, null, 8)).toEqual([4, 5, 6, 7]);
    expect(periodsFromRange(2, 3, 8)).toEqual([1, 2]);
  });
});

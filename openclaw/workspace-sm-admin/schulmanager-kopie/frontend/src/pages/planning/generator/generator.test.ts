import { describe, expect, it } from 'vitest';
import { bestPerKpi, bestVariant, beforeAfter, clip, compact, deltaText, filterMoves, fmt, niceMax, niceRange, penaltyParts, plural, recommendation, ticks, verdict } from './logic';
import type { Kpi, MoveItem, VariantSummary } from './types';

const kpi = (key: string, after: number): Kpi => ({ key, label: key, unit: '', before: 10, after, delta: after - 10, better: after < 10 });
const variant = (index: number, conflicts: number, unplaced: number, cost: number): Pick<VariantSummary, 'index' | 'kpis'> => ({
  index,
  kpis: [kpi('conflicts', conflicts), kpi('unplaced_hours', unplaced), kpi('cost', cost)],
});

describe('Zahlen und Texte', () => {
  it('formatiert deutsch mit einer Nachkommastelle', () => {
    expect(fmt(5.5)).toBe('5,5');
    expect(fmt(622)).toBe('622');
    expect(fmt(null)).toBe('–');
  });
  it('Einzahl und Mehrzahl', () => {
    expect(plural(1, 'Hinweis', 'Hinweise')).toBe('1 Hinweis');
    expect(plural(2, 'Hinweis', 'Hinweise')).toBe('2 Hinweise');
    expect(plural(0, 'Hinweis', 'Hinweise')).toBe('0 Hinweise');
  });
  it('Vorher-Nachher und Veränderung', () => {
    expect(beforeAfter({ before: 11, after: 5.5 })).toBe('11 → 5,5');
    expect(verdict(-2)).toBe('besser');
    expect(verdict(3)).toBe('schlechter');
    expect(verdict(0)).toBe('gleich');
    expect(deltaText(-5.5)).toBe('−5,5 (besser)');
    expect(deltaText(0)).toBe('unverändert');
  });
  it('kürzt lange Beschriftungen', () => {
    expect(clip('Mathematik 10a', 8)).toBe('Mathema…');
    expect(clip('kurz', 8)).toBe('kurz');
  });
});

describe('Achsen', () => {
  it('rundet auf runde Obergrenzen', () => {
    expect(niceMax(0)).toBe(1);
    expect(niceMax(7)).toBe(10);
    expect(niceMax(311)).toBe(500);
    expect(niceMax(622)).toBe(1000);
    expect(niceMax(1.8)).toBe(2);
  });
  it('liefert gleichmäßige Achsenwerte', () => {
    expect(ticks(7, 5)).toEqual([0, 2, 4, 6, 8, 10]);
    expect(ticks(2352)).toEqual([0, 500, 1000, 1500, 2000, 2500]);
    expect(ticks(311, 5)).toEqual([0, 100, 200, 300, 400, 500]);
  });
  it('Linienachse muss nicht bei 0 beginnen', () => {
    const r = niceRange(36437, 49000, 4);
    expect(r.lo).toBeLessThanOrEqual(36437);
    expect(r.hi).toBeGreaterThanOrEqual(49000);
    expect(r.ticks[0]).toBe(r.lo);
    expect(r.ticks[r.ticks.length - 1]).toBe(r.hi);
    expect(niceRange(5, 5).ticks[0]).toBe(0);
  });
  it('kompakt ab Tausend', () => {
    expect(compact(950)).toBe('950');
    expect(compact(1500)).toBe('1,5 Tsd.');
  });
});

describe('Varianten', () => {
  it('beste Variante: Konflikte vor unverplant vor Kosten', () => {
    expect(bestVariant([variant(0, 0, 4, 100), variant(1, 0, 2, 500), variant(2, 1, 0, 10)])).toBe(1);
    expect(bestVariant([variant(0, 0, 2, 300), variant(1, 0, 2, 200)])).toBe(1);
    expect(bestVariant([variant(0, 0, 0, 5)])).toBe(0);
  });
  it('markiert je Kennzahl nur bei Unterschied', () => {
    const best = bestPerKpi([variant(0, 0, 2, 300), variant(1, 0, 2, 200)]);
    expect(best.conflicts).toBeUndefined();
    expect(best.unplaced_hours).toBeUndefined();
    expect([...(best.cost ?? [])]).toEqual([1]);
  });
});

describe('Verschiebungen filtern', () => {
  const item = (kind: MoveItem['kind'], changes: string[], classes: string[]): MoveItem => ({
    course: 'x',
    label: 'x',
    classes,
    teachers: [],
    kind,
    changes,
    from: null,
    to: null,
  });
  const items = [item('moved', ['Tag'], ['5a']), item('moved', ['Stunde', 'Raum'], ['5b']), item('room', ['Raum'], ['5a']), item('added', [], ['5a'])];
  it('nach Art, Änderung und Klasse', () => {
    expect(filterMoves(items, { kind: 'all', change: '', classId: '' })).toHaveLength(4);
    expect(filterMoves(items, { kind: 'moved', change: '', classId: '' })).toHaveLength(2);
    expect(filterMoves(items, { kind: 'moved', change: 'Raum', classId: '' })).toHaveLength(1);
    expect(filterMoves(items, { kind: 'all', change: '', classId: '5a' })).toHaveLength(3);
  });
});

describe('Empfehlung und Strafpunkte', () => {
  const k = (key: string, label: string, before: number, after: number): Kpi => ({ key, label, unit: '', before, after, delta: after - before, better: after === before ? null : after < before });
  it('schlechterer Entwurf: nicht übernehmen, mit Gründen', () => {
    const r = recommendation([k('class_gaps', 'Hohlstunden Klassen', 19, 22.5), k('conflicts', 'Konflikte', 0, 0), k('cost', 'Strafpunkte', 33748, 36437)]);
    expect(r.tone).toBe('bad');
    expect(r.title).toMatch(/^Nicht übernehmen/);
    expect(r.worse).toEqual(['Hohlstunden Klassen: 19 → 22,5']);
    expect(r.advice).toMatch(/Rechenzeit/);
  });
  it('mehr Konflikte sprechen immer dagegen', () => {
    expect(recommendation([k('conflicts', 'Konflikte', 0, 2), k('cost', 'Strafpunkte', 10, 5)]).tone).toBe('bad');
  });
  it('besserer Entwurf und gleich', () => {
    expect(recommendation([k('class_gaps', 'Hohlstunden Klassen', 19, 10), k('cost', 'Strafpunkte', 100, 50)]).tone).toBe('good');
    expect(recommendation([k('cost', 'Strafpunkte', 100, 100)]).tone).toBe('neutral');
  });
  it('Strafpunkte je Ziel: Verstöße mal Gewicht', () => {
    const rule = (id: string, w: number | null, b: number | null, a: number | null) => ({ id, title: id, group: '', level: 'wichtig', level_label: 'Wichtig', weight: w, before: b, after: a, delta: null, hard: false });
    const parts = penaltyParts([rule('teacher_gap', 5, 400, 311), rule('x', null, 1, 1), rule('y', 3, 0, 0)], 0, 3);
    expect(parts.map((p) => p.id)).toEqual(['unplaced', 'teacher_gap']);
    expect(parts[1]).toMatchObject({ afterPoints: 1555, beforePoints: 2000 });
    expect(parts[0]?.afterPoints).toBe(3000);
  });
});

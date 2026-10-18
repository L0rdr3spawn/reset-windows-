import { describe, expect, it } from 'vitest';
import { importSummary, logoProblem, nextOpen, progress, type SetupStep } from './setupLogic';

const step = (key: string, o: Partial<SetupStep> = {}): SetupStep => ({
  key,
  done: false,
  skipped: false,
  optional: false,
  auto: false,
  marked: null,
  ...o,
});

describe('Einrichtungsassistent', () => {
  const steps = [step('a', { done: true }), step('b', { skipped: true }), step('c'), step('d')];

  it('zählt Fortschritt', () => {
    expect(progress(steps)).toEqual({ done: 1, skipped: 1, total: 4, percent: 50 });
    expect(progress([])).toEqual({ done: 0, skipped: 0, total: 0, percent: 0 });
  });

  it('findet den nächsten offenen Schritt, auch von vorn', () => {
    expect(nextOpen(steps)).toBe('c');
    expect(nextOpen(steps, 'c')).toBe('d');
    expect(nextOpen(steps, 'd')).toBe('c');
    expect(nextOpen([step('a', { done: true })])).toBeNull();
  });

  it('prüft das Logo', () => {
    expect(logoProblem({ type: 'image/png', size: 1000 })).toBeNull();
    expect(logoProblem({ type: 'image/svg+xml', size: 1000 })).toMatch(/PNG/);
    expect(logoProblem({ type: 'image/jpeg', size: 400_000 })).toMatch(/300 kB/);
  });

  it('fasst Importzähler zusammen', () => {
    expect(importSummary({ classes: 3, students: 90 })).toBe(
      'Fächer: 0 · Räume: 0 · Klassen: 3 · Lehrkräfte: 0 · Schüler/innen: 90',
    );
  });
});

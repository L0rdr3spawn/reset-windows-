/**
 * T3 (Entwurf KALENDER-ZEITRASTER §15.7, ersetzt R3-A2 Nr. 6): keine Wochenbuchstaben in der Oberfläche (G1).
 * Gleicher Suchausdruck wie `tests/test_weeks.py::test_keine_wochenbuchstaben`; erlaubt sind nur Tests mit
 * „altformat“ im Dateinamen (Lesen alter Daten) und diese Datei selbst.
 */
import { describe, expect, it } from 'vitest';

const SOURCES: Record<string, string> = Object.fromEntries(
  Object.entries(import.meta.glob(['../../**/*.ts', '../../**/*.tsx'], { query: '?raw', import: 'default', eager: true }) as Record<string, string>).map(
    ([path, text]) => [path.replace(/^\.\.\/\.\.\//, ''), text],
  ),
);

const PATTERNS: RegExp[] = [
  /A\/B/,
  /Woche [A-Z]\b/,
  /\b[A-Z]-Woche/,
  /chr\((65|ord\("A"\))/,
  /fromCharCode\(65/,
  // kein Schul-Wochenzyklus mehr: Wochenangaben sind jede Woche / ausgewählte Wochen / Rhythmus
  /Wochenzyklus|Zykluswoche|cycle_weeks|cycleWeeks|cycle_week\b|week_label|weekLabel|Kurszyklus/,
];

function hits(text: string): string[] {
  return text
    .split('\n')
    .map((line, i) => ({ line, i }))
    .filter(({ line }) => PATTERNS.some((p) => p.test(line)))
    .map(({ line, i }) => `${i + 1}: ${line.trim()}`);
}

describe('Keine Wochenbuchstaben (T3)', () => {
  it('frontend/src ohne „A/B“, „Woche A“, „A-Woche“, fromCharCode(65), Wochenzyklus', () => {
    expect(Object.keys(SOURCES).length).toBeGreaterThan(100);
    const found: string[] = [];
    for (const [rel, text] of Object.entries(SOURCES)) {
      if (/altformat/i.test(rel) || rel.endsWith('noWeekLetters.test.ts')) continue;
      for (const h of hits(text)) found.push(`${rel}:${h}`);
    }
    expect(found).toEqual([]);
  });

  it('DESIGN.md ohne Wochenbuchstaben', async () => {
    const fs = (await import(/* @vite-ignore */ `node:${'fs'}`)) as { readFileSync: (p: URL, enc: 'utf8') => string };
    const text = fs.readFileSync(new URL('../../../../docs/DESIGN.md', import.meta.url), 'utf8');
    expect(hits(text)).toEqual([]);
  });

  it('der Suchausdruck findet die alten Formen', () => {
    expect(hits('Woche A · Mi')).toHaveLength(1);
    expect(hits('A/B-Wochen')).toHaveLength(1);
    expect(hits('B-Woche')).toHaveLength(1);
    expect(hits('String.fromCharCode(65 + w)')).toHaveLength(1);
    expect(hits('Zykluswoche 2 von 2')).toHaveLength(1);
    expect(hits('cycle_weeks: 2')).toHaveLength(1);
    expect(hits('Woche 12 · KW 45')).toHaveLength(0);
  });
});

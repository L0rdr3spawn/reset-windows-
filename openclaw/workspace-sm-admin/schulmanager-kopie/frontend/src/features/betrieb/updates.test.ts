import { describe, expect, it } from 'vitest';
import { migrationText, windowText } from './updates';

describe('Updates unter /betrieb', () => {
  it('zeigt das Zeitfenster in Ortszeit (Sommer- und Winterzeit)', () => {
    // 21.05.2026 00:00 bis 06:00 Berlin = 20.05. 22:00 bis 04:00 UTC (Sommerzeit)
    expect(windowText({ start: '2026-05-20T22:00:00Z', end: '2026-05-21T04:00:00Z' })).toContain('00:00 bis 06:00 Uhr');
    // Winter: 01.12.2026 00:00 Berlin = 30.11. 23:00 UTC
    expect(windowText({ start: '2026-11-30T23:00:00Z', end: '2026-12-01T05:00:00Z' })).toContain('00:00 bis 06:00 Uhr');
    expect(windowText(null)).toBe('–');
    expect(windowText({ label: 'Sa 02:00–05:00' })).toBe('Sa 02:00–05:00');
  });

  it('erklärt die Migration', () => {
    expect(migrationText(null)).toMatch(/Keine/);
    expect(migrationText({ present: true, backward_compatible: true })).toMatch(/abwärtskompatibel/);
    expect(migrationText({ present: true, backward_compatible: false })).toMatch(/gemeinsam/);
  });
});

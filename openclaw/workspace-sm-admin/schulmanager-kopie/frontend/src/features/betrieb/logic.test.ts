import { describe, expect, it } from 'vitest';
import { ageText, summary, uptimeText, verifyText, type Check } from './logic';

const c = (level: Check['level']): Check => ({ key: level, label: level, level, detail: '' });

describe('Betriebsstatus', () => {
  it('fasst Prüfungen zusammen', () => {
    expect(summary([c('ok'), c('ok')])).toEqual({ level: 'ok', text: 'Alles in Ordnung' });
    expect(summary([c('ok'), c('warn')])).toEqual({ level: 'warn', text: '1 Hinweis' });
    expect(summary([c('warn'), c('warn'), c('error')]).level).toBe('error');
  });

  it('formatiert Laufzeit und Alter', () => {
    expect(uptimeText(59)).toBe('0 Min.');
    expect(uptimeText(3 * 3600 + 120)).toBe('3 Std. 2 Min.');
    expect(uptimeText(2 * 86400 + 5 * 3600)).toBe('2 Tage 5 Std.');
    const now = new Date('2026-10-16T12:00:00Z').getTime();
    expect(ageText(null, now)).toBe('noch nie');
    expect(ageText('2026-10-16T11:59:30Z', now)).toBe('gerade eben');
    expect(ageText('2026-10-16T09:00:00Z', now)).toBe('vor 3 Std.');
    expect(ageText('2026-10-14T12:00:00Z', now)).toBe('vor 2 Tagen');
  });

  it('beschreibt das Prüfergebnis einer Sicherung', () => {
    const ok = { name: 'x', ok: true, integrity: 'ok', users: 4, plan_versions: 2, revision: 'r', seconds: 0.4 };
    expect(verifyText(ok)).toContain('4 Konten');
    expect(verifyText({ ...ok, ok: false, integrity: 'kaputt' })).toContain('kaputt');
  });
});

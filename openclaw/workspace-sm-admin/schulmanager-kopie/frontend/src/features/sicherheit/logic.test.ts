import { describe, expect, it } from 'vitest';
import { formatMinutes, formatWait, lockTitle, toggleRole } from './logic';

describe('Sicherheit', () => {
  it('formatiert Dauern', () => {
    expect(formatMinutes(720)).toBe('12 Stunden');
    expect(formatMinutes(60)).toBe('1 Stunde');
    expect(formatMinutes(30)).toBe('30 Minuten');
    expect(formatMinutes(2880)).toBe('2 Tage');
  });
  it('formatiert Wartezeiten', () => {
    expect(formatWait(30)).toBe('30 Sekunden');
    expect(formatWait(0)).toBe('1 Sekunden');
    expect(formatWait(240)).toBe('4 Minuten');
  });
  it('beschreibt Drosselungen', () => {
    const base = { failures: 5, wait: 30, last_failure: null };
    expect(lockTitle({ ...base, kind: 'user', username: 'sek', ip: '1.2.3.4' })).toBe('sek von 1.2.3.4');
    expect(lockTitle({ ...base, kind: 'ip', username: null, ip: '1.2.3.4' })).toBe('Anschluss 1.2.3.4');
    expect(lockTitle({ ...base, kind: 'account', username: 'sek', ip: null })).toContain('viele Anschlüsse');
  });
  it('schaltet Rollen um und behält die Reihenfolge', () => {
    const order = ['admin', 'schulleitung', 'sekretariat', 'lehrer'];
    expect(toggleRole(['admin', 'sekretariat'], 'schulleitung', order)).toEqual(['admin', 'schulleitung', 'sekretariat']);
    expect(toggleRole(['admin', 'lehrer'], 'admin', order)).toEqual(['lehrer']);
  });
});

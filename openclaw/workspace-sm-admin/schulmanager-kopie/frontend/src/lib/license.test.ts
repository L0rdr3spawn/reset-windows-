import { describe, expect, it } from 'vitest';
import type { LicenseBrief } from '../api/types';
import { canManageLicense, licenseBanner, lockedTitle, stateLabel } from './license';

const base: LicenseBrief = { state: 'valid', read_only: false, message: '', warning: '', enforced: true };

describe('Lizenz-Hinweise', () => {
  it('Kulanzzeit: Hinweis für alle, Link nur für Berechtigte', () => {
    const lic = { ...base, state: 'grace', read_only: true, message: 'Lizenz abgelaufen.' };
    expect(licenseBanner(lic, false)).toEqual({ kind: 'error', text: 'Nur Lesen: Lizenz abgelaufen.', link: false });
    expect(licenseBanner(lic, true)?.link).toBe(true);
  });
  it('Vorwarnung nur für Berechtigte', () => {
    const lic = { ...base, warning: 'Die Lizenz läuft in 7 Tag(en) ab.' };
    expect(licenseBanner(lic, false)).toBeNull();
    expect(licenseBanner(lic, true)).toEqual({ kind: 'warning', text: 'Die Lizenz läuft in 7 Tag(en) ab.', link: true });
  });
  it('ohne Durchsetzung oder ohne Lizenzdaten kein Hinweis', () => {
    expect(licenseBanner({ ...base, enforced: false, warning: 'x' }, true)).toBeNull();
    expect(licenseBanner(null, true)).toBeNull();
    expect(licenseBanner(base, true)).toBeNull();
  });
  it('Überschrift der Sperrseite und Recht', () => {
    expect(lockedTitle('expired')).toBe('Die Lizenz dieser Schule ist abgelaufen');
    expect(lockedTitle('missing')).toBe('Willkommen – bitte Lizenz eingeben');
    expect(lockedTitle('blocked')).toBe('Die Lizenz dieser Schule wurde gesperrt');
    expect(lockedTitle('cancelled')).toBe('Die Lizenz dieser Schule wurde gesperrt');
    expect(lockedTitle('paused')).toBe('Die Lizenz dieser Schule ist pausiert');
    expect(lockedTitle('offline')).toBe('Die Lizenz konnte nicht bestätigt werden');
    expect(canManageLicense({ permissions: ['license.manage'] })).toBe(true);
    expect(canManageLicense({ permissions: ['system.admin'] })).toBe(false);
    expect(canManageLicense(null)).toBe(false);
    expect(stateLabel('locked')[0]).toBe('gesperrt');
  });
});

import { describe, expect, it } from 'vitest';
import {
  anyChannel,
  channelList,
  contactWays,
  cleanCode,
  extractCodes,
  extractLinks,
  formatBytes,
  formatPhone,
  identifierKind,
  internalAppPath,
  isCompleteCode,
  isValidEmail,
  managedByStaffNote,
  maskEmail,
  maskPhone,
  minutesLeft,
  normalizePhone,
  passwordIssues,
  resetUsable,
} from './logic';

describe('konto: Telefonnummern', () => {
  it('normalisiert deutsche und internationale Eingaben wie das Backend', () => {
    expect(normalizePhone('0171 1234567')).toBe('+491711234567');
    expect(normalizePhone('0171/123 45 67')).toBe('+491711234567');
    expect(normalizePhone('+49 (0)171 1234567')).toBe('+491711234567');
    expect(normalizePhone('+49 (171) 1234567')).toBe('+491711234567');
    expect(normalizePhone('+490171 1234567')).toBe('+491711234567');
    expect(normalizePhone('0049 171 1234567')).toBe('+491711234567');
    expect(normalizePhone('+43 664 1234567')).toBe('+436641234567');
    expect(normalizePhone('1711234567')).toBeNull();
    expect(normalizePhone('0171')).toBeNull();
    expect(normalizePhone('+49 171 12a4567')).toBeNull();
    expect(normalizePhone('+1234567890123456')).toBeNull();
  });

  it('formatiert und maskiert', () => {
    expect(formatPhone('+491711234567')).toBe('+49 171 1234567');
    expect(maskPhone('+491711234567')).toBe('+49 171 •••••67');
    expect(maskPhone(null)).toBe('•••');
    expect(maskEmail('maria@schule.de')).toBe('m•••@schule.de');
    expect(maskEmail('kaputt')).toBe('•••');
  });
});

describe('konto: Eingaben', () => {
  it('prüft E-Mail-Adressen', () => {
    expect(isValidEmail('a.b@schule.de')).toBe(true);
    expect(isValidEmail(' a.b@schule.de ')).toBe(true);
    expect(isValidEmail('a@b')).toBe(false);
    expect(isValidEmail('a b@c.de')).toBe(false);
    expect(isValidEmail('x@y.de, z@q.de')).toBe(false);
  });

  it('säubert Codes', () => {
    expect(cleanCode('123 456')).toBe('123456');
    expect(cleanCode('12-34-56-78')).toBe('123456');
    expect(isCompleteCode('123 456')).toBe(true);
    expect(isCompleteCode('12345')).toBe(false);
  });

  it('erkennt die Art der Kennung', () => {
    expect(identifierKind('')).toBe('empty');
    expect(identifierKind('maria@schule.de')).toBe('email');
    expect(identifierKind('0171 1234567')).toBe('phone');
    expect(identifierKind('+49 171 1234567')).toBe('phone');
    expect(identifierKind('mueller.anna')).toBe('username');
    expect(identifierKind('anna2')).toBe('username');
  });

  it('nennt Kanäle und Passwort-Hinweise', () => {
    expect(channelList(['email', 'sms'])).toBe('E-Mail und SMS');
    expect(channelList(['sms'])).toBe('SMS');
    expect(channelList([])).toBe('');
    expect(passwordIssues('kurz', 10)).toEqual(['mindestens 10 Zeichen']);
    expect(passwordIssues('aaaaaaaaaa', 8)).toEqual(['nicht so gleichförmig']);
    expect(passwordIssues('xx-mueller-2024', 8, 'mueller')).toEqual(['ohne den Benutzernamen']);
    expect(passwordIssues('Sommer-Wiese-42', 10, 'anna')).toEqual([]);
  });
});

describe('konto: Test-Postausgang', () => {
  const text = 'Code: 123456\nLink: http://localhost:8000/passwort-zuruecksetzen?token=abc_DEF-1.\nTel 0171 1234567';

  it('findet Codes und Links', () => {
    expect(extractCodes(text)).toEqual(['123456']);
    expect(extractCodes('1234567 und 654321 und 654321')).toEqual(['654321']);
    expect(extractLinks(text)).toEqual(['http://localhost:8000/passwort-zuruecksetzen?token=abc_DEF-1']);
  });

  it('macht nur App-Seiten zu internen Pfaden (kein Open Redirect)', () => {
    expect(internalAppPath('http://localhost:8000/passwort-zuruecksetzen?token=abc')).toBe('/passwort-zuruecksetzen?token=abc');
    expect(internalAppPath('https://schule.example/profil?kontakt=x')).toBe('/profil?kontakt=x');
    expect(internalAppPath('https://evil.example/anderes')).toBeNull();
    expect(internalAppPath('javascript:alert(1)')).toBeNull();
    expect(internalAppPath('kein link')).toBeNull();
  });

  it('rechnet Restzeit und Größen', () => {
    const now = new Date('2026-10-10T10:00:00Z');
    expect(minutesLeft('2026-10-10T10:14:30Z', now)).toBe(15);
    expect(minutesLeft('2026-10-10T09:00:00Z', now)).toBe(0);
    expect(minutesLeft(null, now)).toBe(0);
    expect(formatBytes(500)).toBe('500 B');
    expect(formatBytes(1536)).toBe('1,5 KB');
  });
});

describe('konto: Fähigkeiten des Servers', () => {
  const caps = (email: boolean, sms: boolean, selfReset: Record<string, boolean> = { schueler: false, eltern: true, lehrer: true }) => ({
    email,
    sms,
    channels: { email, sms },
    self_reset: selfReset,
    code_minutes: 15,
    dev_outbox: false,
  });

  it('zeigt „Passwort vergessen“ nur, wenn Versand geht und eine Rolle es nutzen darf', () => {
    expect(resetUsable(caps(true, false))).toBe(true);
    expect(resetUsable(caps(false, false))).toBe(false);
    expect(resetUsable(caps(true, true, { schueler: false, eltern: false }))).toBe(false);
    expect(resetUsable(null)).toBe(false);
    expect(anyChannel(caps(false, true))).toBe(true);
    expect(anyChannel(undefined)).toBe(false);
  });

  it('nennt nur zustellbare Wege', () => {
    expect(contactWays(caps(true, false))).toBe('E-Mail-Adresse');
    expect(contactWays(caps(false, true))).toBe('Handynummer');
    expect(contactWays(caps(true, true))).toBe('E-Mail-Adresse oder Handynummer');
    expect(contactWays(caps(false, false))).toBe('');
  });

  it('weist Schüler/innen an die Klassenleitung', () => {
    expect(managedByStaffNote(caps(true, true))).toBe('Schüler/innen: Bitte wenden Sie sich an Ihre Klassenleitung.');
    expect(managedByStaffNote(caps(true, true, { schueler: false, eltern: false }))).toContain('Schüler/innen und Eltern');
    expect(managedByStaffNote(caps(true, true, { schueler: true, eltern: true }))).toBeNull();
    expect(managedByStaffNote(undefined)).toBeNull();
  });
});

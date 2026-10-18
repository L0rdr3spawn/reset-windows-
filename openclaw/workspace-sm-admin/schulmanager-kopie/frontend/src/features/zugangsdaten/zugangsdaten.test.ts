import { describe, expect, it } from 'vitest';
import { formatClock, loginHint, reachable, remainingLabel, secondsLeft, sendPreview, sendSummary } from './logic';
import type { BatchEntry } from './types';

const entry = (over: Partial<BatchEntry>): BatchEntry => ({
  user_id: 1,
  username: 'max',
  display_name: 'Max',
  role: 'schueler',
  class_id: '5a',
  class_name: '5a',
  student_id: 'S1',
  children: [],
  exists: true,
  has_email: false,
  parents: 0,
  parents_with_email: 0,
  password_printed: true,
  login_methods: [],
  required_links: [],
  filename: '5a_Max.pdf',
  title: 'Zugangsdaten für Max',
  ...over,
});

describe('Countdown', () => {
  it('secondsLeft/formatClock/remainingLabel', () => {
    const now = new Date('2026-10-10T10:00:00Z');
    expect(secondsLeft('2026-10-10T10:54:07Z', now)).toBe(3247);
    expect(secondsLeft('2026-10-10T09:00:00Z', now)).toBe(0);
    expect(secondsLeft('kaputt', now)).toBe(0);
    expect(formatClock(3247)).toBe('54:07');
    expect(formatClock(3723)).toBe('1:02:03');
    expect(formatClock(5)).toBe('0:05');
    expect(remainingLabel(3247)).toBe('noch 55 Minuten');
    expect(remainingLabel(40)).toBe('noch 40 Sekunden');
    expect(remainingLabel(0)).toBe('abgelaufen');
  });
});

describe('Versand', () => {
  it('reachable je Ziel', () => {
    const own = entry({ has_email: true });
    const viaParents = entry({ parents: 2, parents_with_email: 1 });
    const parent = entry({ role: 'eltern', has_email: true, student_id: null });
    expect([reachable(own, 'student'), reachable(own, 'parents'), reachable(own, 'both')]).toEqual([true, false, true]);
    expect([reachable(viaParents, 'student'), reachable(viaParents, 'parents')]).toEqual([false, true]);
    expect([reachable(parent, 'student'), reachable(parent, 'parents')]).toEqual([true, true]);
    // Volljährige: auch bei „an die Eltern“ nur an die eigene Adresse
    const adult = entry({ has_email: true, adult: true });
    expect([reachable(adult, 'parents'), reachable(entry({ adult: true }), 'parents')]).toEqual([true, false]);
    expect(sendPreview([own, viaParents, entry({})], 'both')).toEqual({ reachable: 2, missing: 1 });
  });

  it('sendSummary', () => {
    const row = { user_id: 1, display_name: 'A', role: 'schueler' };
    expect(sendSummary({ sent: [row, row], no_address: [row], unavailable: [] })).toBe('2 Briefe verschickt · 1 ohne E-Mail-Adresse');
    expect(sendSummary({ sent: [row], no_address: [], unavailable: [row] })).toBe('1 Brief verschickt · 1 nicht zustellbar');
  });

  it('loginHint', () => {
    expect(loginHint(entry({}))).toBe('Startpasswort');
    expect(loginHint(entry({ password_printed: false, login_methods: ['Microsoft'] }))).toBe('nur Microsoft');
    expect(loginHint(entry({ required_links: ['Apple'] }))).toBe('Startpasswort · muss Apple verbinden');
  });
});

/**
 * U-01: zentrale Sitzungs-Rücksetzung. Nachstellung aus docs/code/05-frontend-basis.md §8 ohne Browser:
 * Sekretariat lädt alle Schüler/innen, die Sitzung läuft ab (401), danach meldet sich lehrer1 im selben Tab an –
 * der Cache darf die Liste des Sekretariats nicht mehr liefern.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { http, onUnauthorized } from '../../api/client';
import { invalidateFileLimits, loadFileLimits } from '../../components/FileUpload';
import { overviewShared } from '../../features/channels/api';
import { clearToastsOnSessionReset } from '../../context/ToastContext';
import { getBadge, setBadge } from '../../features/registry';
import { clearCollectionCache, peekCollection, preloadCollection } from '../../hooks/useCollection';
import { onSessionReset, resetSession, sessionState, setSessionAccount } from '../session';

const TOAST_SRC =
  (import.meta.glob('../../context/ToastContext.tsx', { query: '?raw', import: 'default', eager: true }) as Record<string, string>)['../../context/ToastContext.tsx'] ?? '';

/** kleiner Server: Antwort hängt vom „Cookie“ (Konto) ab, ohne Konto 401 */
let account: 'sekretariat' | 'lehrer1' | null = null;
const STUDENTS = { sekretariat: 666, lehrer1: 317 } as const;
const calls: string[] = [];

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', 'X-Request-ID': 'a1b2c3d4e5f6' } });
}

beforeEach(() => {
  calls.length = 0;
  account = null;
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      const path = String(url).replace('/api/v1', '').split('?')[0] as string;
      calls.push(path);
      if (!account) return json({ detail: 'not_authenticated' }, 401);
      if (path === '/data/students') return json(Array.from({ length: STUDENTS[account] }, (_, i) => ({ id: `S${i}`, name: `S${i}` })));
      if (path === '/files/limits') return json({ max_bytes: 1, used_bytes: account === 'sekretariat' ? 900 : 10 });
      if (path === '/channels/overview') return json({ channels: [], owner: account });
      return json({});
    }),
  );
  setSessionAccount(null);
  clearCollectionCache();
  invalidateFileLimits();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

const studentCount = () => (peekCollection('students') as unknown[] | undefined)?.length;

describe('Sitzungs-Rücksetzung (U-01)', () => {
  it('Nachstellung: nach 401 und neuer Anmeldung sieht lehrer1 317, nicht 666 Schüler/innen', async () => {
    account = 'sekretariat';
    setSessionAccount('2:sekretariat');
    await preloadCollection('students');
    expect(studentCount()).toBe(666);

    // Sitzung läuft ab: nächste Anfrage → 401 → Cache sofort leer (auch ohne AuthContext)
    account = null;
    const seen = vi.fn();
    const off = onUnauthorized(seen);
    await http.get('/timetable/class/5a').catch(() => undefined);
    off();
    expect(seen).toHaveBeenCalledTimes(1);
    expect(studentCount()).toBeUndefined();

    // lehrer1 meldet sich im selben Tab an und öffnet die Krankmeldungen → neue Anfrage, eigener Umfang
    account = 'lehrer1';
    setSessionAccount('7:lehrer1');
    calls.length = 0;
    await preloadCollection('students');
    expect(calls).toContain('/data/students');
    expect(studentCount()).toBe(317);
  });

  it('Kontowechsel ohne Abmeldung setzt zurück, dasselbe Konto (refresh) nicht', async () => {
    account = 'sekretariat';
    setSessionAccount('2:sekretariat');
    await preloadCollection('students');
    const before = sessionState().resets;
    setSessionAccount('2:sekretariat');
    expect(sessionState().resets).toBe(before);
    expect(studentCount()).toBe(666);
    setSessionAccount('7:lehrer1');
    expect(sessionState().resets).toBe(before + 1);
    expect(studentCount()).toBeUndefined();
  });

  it('Abmeldung (resetSession) leert Sammlungen, Datei-Limits, Kursraum-Übersicht und Badges', async () => {
    account = 'sekretariat';
    setSessionAccount('2:sekretariat');
    await preloadCollection('students');
    const limitsA = await loadFileLimits('message');
    const overviewA = await overviewShared();
    setBadge('postfach.unread', 4);
    expect(getBadge('postfach.unread')).toBe(4);
    // ohne Rücksetzung kämen Limits und Übersicht aus dem Zwischenspeicher
    calls.length = 0;
    await loadFileLimits('message');
    await overviewShared();
    expect(calls).toEqual([]);

    resetSession();
    expect(studentCount()).toBeUndefined();
    expect(getBadge('postfach.unread')).toBeNull();

    account = 'lehrer1';
    setSessionAccount('7:lehrer1');
    const limitsB = await loadFileLimits('message');
    const overviewB = await overviewShared();
    expect(calls).toEqual(['/files/limits', '/channels/overview']);
    expect(limitsB).not.toEqual(limitsA);
    expect(overviewB).not.toEqual(overviewA);
  });

  it('Antwort einer Anfrage des vorigen Kontos landet nicht mehr im Cache', async () => {
    account = 'sekretariat';
    setSessionAccount('2:sekretariat');
    const pending = preloadCollection('students');
    resetSession(); // Abmeldung, während die Liste noch lädt
    await pending;
    expect(studentCount()).toBeUndefined();
  });

  it('eine fehlerhafte Rücksetz-Funktion hält die übrigen nicht auf', () => {
    const err = vi.spyOn(console, 'error').mockImplementation(() => undefined);
    const ok = vi.fn();
    const off1 = onSessionReset(() => {
      throw new Error('kaputt');
    });
    const off2 = onSessionReset(ok);
    resetSession();
    off1();
    off2();
    expect(ok).toHaveBeenCalledTimes(1);
    expect(err).toHaveBeenCalled();
    err.mockRestore();
  });

  it('offene Toasts des vorigen Kontos verschwinden bei Abmeldung, 401 und Kontowechsel', async () => {
    const set = vi.fn();
    const off = clearToastsOnSessionReset(set);
    resetSession(); // Abmeldung
    expect(set).toHaveBeenLastCalledWith([]);
    account = null;
    await http.get('/x').catch(() => undefined); // 401
    expect(set).toHaveBeenCalledTimes(2);
    setSessionAccount('2:sekretariat');
    setSessionAccount('7:lehrer1'); // Kontowechsel
    expect(set).toHaveBeenCalledTimes(3);
    off();
    resetSession();
    expect(set).toHaveBeenCalledTimes(3);
    // der Provider meldet die Rücksetzung beim Einhängen an (Effekt, vitest ohne DOM → Quelltext)
    expect(TOAST_SRC).toMatch(/useEffect\(\(\) => clearToastsOnSessionReset\(setToasts\), \[\]\)/);
  });

  it('Anmelde-Fehler (skipAuthRedirect, z. B. falsches Passwort) setzen nicht zurück', async () => {
    account = 'sekretariat';
    setSessionAccount('2:sekretariat');
    await preloadCollection('students');
    account = null;
    await http.post('/auth/login', {}, { skipAuthRedirect: true }).catch(() => undefined);
    expect(studentCount()).toBe(666);
  });
});

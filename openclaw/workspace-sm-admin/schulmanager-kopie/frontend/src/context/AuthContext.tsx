import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { ApiError, onLicenseLocked, onLinkRequired, onPasswordChangeRequired, onTotpSetupRequired, onUnauthorized, setCsrfToken } from '../api/client';
import { auth } from '../api/endpoints';
import { live } from '../api/events';
import type { MeResponse, Permission, User } from '../api/types';
// Laden registriert die Rücksetzung des Sammlungs-Caches (lib/session), auch wenn noch keine Seite ihn nutzt
import '../hooks/useCollection';
import { can } from '../lib/permissions';
import { resetSession, setSessionAccount } from '../lib/session';

/** Ziel nach dem Abmelden: Kontoauswahl, wenn in diesem Browser noch weitere Konten angemeldet sind, sonst Anmeldeseite. */
export function signedOutTarget(remainingAccounts: number): string {
  return remainingAccounts > 0 ? SIGNED_OUT_PATH : '/login';
}

export const SIGNED_OUT_PATH = '/abgemeldet';

export interface AuthContextValue {
  user: User | null;
  /** erster Ladevorgang (/auth/me) läuft */
  loading: boolean;
  /** Server beim Start nicht erreichbar */
  bootError: string | null;
  /** Sitzung ist abgelaufen (401 während der Nutzung) */
  expired: boolean;
  /** `null`: Passwort stimmt, das Konto verlangt noch den Bestätigungscode (Schritt 2, erneuter Aufruf mit `totp`) */
  login: (username: string, password: string, totp?: string) => Promise<User | null>;
  logout: () => Promise<void>;
  /** weiteres Konto anmelden (bisheriges bleibt angemeldet) bzw. zu einem angemeldeten Konto wechseln */
  addAccount: (username: string, password: string, totp?: string) => Promise<'code_needed' | 'done'>;
  switchAccount: (userId: number) => Promise<void>;
  refresh: () => Promise<void>;
  can: (perm: Permission | Permission[]) => boolean;
}

const Ctx = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [bootError, setBootError] = useState<string | null>(null);
  const [expired, setExpired] = useState(false);

  const apply = useCallback((res: MeResponse | null) => {
    if (res && res.user) {
      // anderes Konto als bisher → erst alle kontobezogenen Zwischenspeicher leeren
      setSessionAccount(`${res.user.id}:${res.user.username}`);
      setCsrfToken(res.csrf_token);
      setUser({ ...res.user, permissions: res.user.permissions ?? [] });
      setExpired(false);
      live.setEnabled(true);
    } else {
      setCsrfToken(null);
      setUser(null);
      live.setEnabled(false);
      resetSession();
    }
  }, []);

  const refresh = useCallback(async () => {
    try {
      const res = await auth.me();
      apply(res);
      setBootError(null);
    } catch (e) {
      if (e instanceof ApiError && (e.status === 401 || e.status === 403)) {
        apply(null);
        setBootError(null);
      } else {
        setBootError(e instanceof Error ? e.message : String(e));
      }
    } finally {
      setLoading(false);
    }
  }, [apply]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // „Zurück“ in eine aus dem Seitenspeicher (bfcache) wiederhergestellte Seite: Sitzung neu prüfen, nichts Altes zeigen
  useEffect(() => {
    const onShow = (e: PageTransitionEvent) => {
      if (e.persisted) void refresh();
    };
    window.addEventListener('pageshow', onShow);
    return () => window.removeEventListener('pageshow', onShow);
  }, [refresh]);

  useEffect(
    () =>
      onUnauthorized(() => {
        setUser((prev) => {
          if (prev) setExpired(true);
          return null;
        });
        setCsrfToken(null);
        live.setEnabled(false);
        // kontobezogene Zwischenspeicher leert schon api/client.ts beim 401 (resetSession, U-01)
      }),
    [],
  );

  useEffect(
    () => onPasswordChangeRequired(() => setUser((prev) => (prev && !prev.must_change_password ? { ...prev, must_change_password: true } : prev))),
    [],
  );
  useEffect(
    () => onTotpSetupRequired(() => setUser((prev) => (prev && !prev.totp_setup_required ? { ...prev, totp_setup_required: true } : prev))),
    [],
  );
  // Pflicht-Verknüpfung neu verlangt (Richtlinie während der Sitzung geändert) → Konto neu laden, Guard leitet weiter
  useEffect(() => onLinkRequired(() => void refresh()), [refresh]);
  // Lizenz während der Sitzung gesperrt → Konto neu laden, der Schutz der Routen zeigt die Sperrseite
  useEffect(() => onLicenseLocked(() => void refresh()), [refresh]);

  const login = useCallback(
    async (username: string, password: string, totp?: string) => {
      const res = await auth.login(username, password, totp);
      if (res && 'totp_required' in res) return null;
      if (res && res.user) {
        apply(res);
        return res.user;
      }
      // Fallback: Server liefert nur Cookie → /auth/me lesen
      const me = await auth.me();
      apply(me);
      return me.user;
    },
    [apply],
  );

  const logout = useCallback(async () => {
    let remaining = 0;
    try {
      remaining = (await auth.logout())?.accounts ?? 0;
    } catch {
      /* Abmelden lokal trotzdem */
    }
    // Zwischenspeicher/Live-Verbindung sofort leeren; `user` bleibt bis zum Neuladen, damit der Schutz der Routen
    // nicht noch eine Anmeldeseite in den Verlauf legt
    setCsrfToken(null);
    live.setEnabled(false);
    resetSession();
    // Kein automatischer Kontowechsel: Seite „Abgemeldet“ (Auswahl der übrigen Konten) bzw. Anmeldeseite. Vollständiges
    // Neuladen mit `replace`: kein Zustand des alten Kontos im Speicher, „Zurück“ führt nicht in die Sitzung.
    window.location.replace(signedOutTarget(remaining));
  }, []);

  const addAccount = useCallback(async (username: string, password: string, totp?: string) => {
    const res = await auth.login(username, password, totp, true);
    if (res && 'totp_required' in res) return 'code_needed';
    window.location.assign('/');
    return 'done';
  }, []);

  const switchAccount = useCallback(async (userId: number) => {
    await auth.switchAccount(userId);
    window.location.assign('/');
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, loading, bootError, expired, login, logout, addAccount, switchAccount, refresh, can: (p) => can(user, p) }),
    [user, loading, bootError, expired, login, logout, addAccount, switchAccount, refresh],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthContextValue {
  const v = useContext(Ctx);
  if (!v) throw new Error('useAuth außerhalb von AuthProvider');
  return v;
}

/** Angemeldeter Benutzer oder `null` (für Bausteine, die auch ohne Anmeldung vorkommen, z. B. Stundenplan-Raster). */
export function useOptionalUser(): User | null {
  return useContext(Ctx)?.user ?? null;
}

/** Angemeldeter Benutzer (nur innerhalb geschützter Routen verwenden). */
export function useUser(): User {
  const { user } = useAuth();
  if (!user) throw new Error('Nicht angemeldet');
  return user;
}

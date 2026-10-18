import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { ApiError, formErrors } from '../api/client';
import type { FieldLabels } from '../api/errors';
import { onSessionReset } from '../lib/session';

export type ToastKind = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: number;
  kind: ToastKind;
  title: string;
  details?: string[];
}

export interface ToastApi {
  show: (kind: ToastKind, title: string, details?: string[]) => void;
  success: (title: string) => void;
  info: (title: string) => void;
  warning: (title: string, details?: string[]) => void;
  /**
   * Fehler anzeigen: 409-Konflikte und mehrere Validierungsfehler als Liste, Feldcodes als Beschriftung (`labels`
   * ergänzt die allgemeine Zuordnung), Unerwartetes mit Fehlernummer.
   */
  error: (e: unknown, prefix?: string, opts?: { labels?: FieldLabels }) => void;
}

/** Text einer Fehlermeldung (ohne Präfix) bzw. Liste; 403 ohne doppeltes „Keine Berechtigung“ (U-75). */
export function toastErrorContent(e: unknown, labels?: FieldLabels): { title: string; details?: string[] } {
  if (e instanceof ApiError && e.conflicts.length) return { title: 'Konflikte – Änderung nicht möglich', details: e.conflicts };
  const f = formErrors(e, labels);
  if (f.issues.length > 1) return { title: 'Bitte die Eingaben prüfen.', details: f.issues.map((i) => i.summary) };
  let msg = f.message;
  if (e instanceof ApiError && e.status === 403 && !/berechtigung/i.test(msg)) msg = `Keine Berechtigung: ${msg}`;
  return { title: msg };
}

/**
 * Offene Meldungen gehören zum Konto (z. B. „Antrag von … genehmigt“): bei Abmeldung, 401 und Kontowechsel leeren,
 * sonst stehen sie noch auf der Anmeldeseite bzw. beim nächsten Konto (U-01). Rückgabe meldet wieder ab.
 */
export function clearToastsOnSessionReset(setToasts: (t: Toast[]) => void): () => void {
  return onSessionReset(() => setToasts([]));
}

const Ctx = createContext<ToastApi | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(1);
  useEffect(() => clearToastsOnSessionReset(setToasts), []);

  const dismiss = useCallback((id: number) => setToasts((t) => t.filter((x) => x.id !== id)), []);

  const show = useCallback(
    (kind: ToastKind, title: string, details?: string[]) => {
      const id = nextId.current++;
      setToasts((t) => [...t.slice(-4), { id, kind, title, details }]);
      const ms = kind === 'error' || (details && details.length) ? 9000 : 4500;
      window.setTimeout(() => dismiss(id), ms);
    },
    [dismiss],
  );

  const api = useMemo<ToastApi>(
    () => ({
      show,
      success: (t) => show('success', t),
      info: (t) => show('info', t),
      warning: (t, d) => show('warning', t, d),
      error: (e, prefix, opts) => {
        if (e instanceof DOMException && e.name === 'AbortError') return;
        if (e instanceof ApiError && e.conflicts.length) {
          show('error', prefix ? `${prefix}: Konflikte` : 'Konflikte – Änderung nicht möglich', e.conflicts);
          return;
        }
        const c = toastErrorContent(e, opts?.labels);
        show('error', prefix ? `${prefix}: ${c.title}` : c.title, c.details);
      },
    }),
    [show],
  );

  return (
    <Ctx.Provider value={api}>
      {children}
      <div className="toasts" role="region" aria-label="Benachrichtigungen">
        <div aria-live="polite" aria-atomic="false">
          {toasts.map((t) => (
            <div key={t.id} className={`toast toast-${t.kind}`} role={t.kind === 'error' ? 'alert' : 'status'}>
              <div className="toast-body">
                <strong>{t.title}</strong>
                {t.details && t.details.length > 0 && (
                  <ul>
                    {t.details.slice(0, 8).map((d, i) => (
                      <li key={i}>{d}</li>
                    ))}
                    {t.details.length > 8 && <li>… und {t.details.length - 8} weitere</li>}
                  </ul>
                )}
              </div>
              <button type="button" className="toast-close" onClick={() => dismiss(t.id)} aria-label="Meldung schließen">
                ×
              </button>
            </div>
          ))}
        </div>
      </div>
    </Ctx.Provider>
  );
}

/** Wie {@link useToast}, aber `null` außerhalb des Providers (Bausteine, die auch ohne App gerendert werden). */
export function useOptionalToast(): ToastApi | null {
  return useContext(Ctx);
}

export function useToast(): ToastApi {
  const v = useContext(Ctx);
  if (!v) throw new Error('useToast außerhalb von ToastProvider');
  return v;
}

/**
 * Ungespeicherte Änderungen ohne Browser-Popup:
 * - `UnsavedBar`: Leiste „Ungespeicherte Änderungen · Speichern · Verwerfen“ (statt `window.confirm` beim Wechseln).
 * - `useLeaveGuard(dirty, onLeave)`: fängt Klicks auf App-Links ab, solange `dirty` gilt. `onLeave` speichert den
 *   Entwurf selbst oder fragt per `confirmAsk()` im App-Stil; liefert es `false`, bleibt man auf der Seite.
 * `beforeunload` (Browser-Dialog beim Schließen/Neuladen) nur einsetzen, wenn wirklich Daten verloren gehen.
 */
import { useEffect, useRef, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { AsyncButton } from './ui';

export function UnsavedBar({ onSave, onDiscard, saveLabel = 'Speichern', children }: { onSave: () => Promise<unknown> | void; onDiscard: () => void; saveLabel?: string; children?: ReactNode }) {
  return (
    <div className="alert alert-warning row-between" role="status">
      <strong>{children ?? 'Ungespeicherte Änderungen'}</strong>
      <span className="row">
        <AsyncButton className="btn btn-sm btn-primary" onClick={onSave}>
          {saveLabel}
        </AsyncButton>
        <button type="button" className="btn btn-sm" onClick={onDiscard}>
          Verwerfen
        </button>
      </span>
    </div>
  );
}

export function useLeaveGuard(dirty: boolean, onLeave: () => Promise<boolean | void> | boolean | void): void {
  const navigate = useNavigate();
  const leave = useRef(onLeave);
  leave.current = onLeave;
  useEffect(() => {
    if (!dirty) return undefined;
    const onClick = (e: MouseEvent) => {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const a = (e.target as Element | null)?.closest?.('a[href]') as HTMLAnchorElement | null;
      if (!a || a.target === '_blank' || a.hasAttribute('download') || a.origin !== window.location.origin) return;
      if (a.pathname === window.location.pathname && a.search === window.location.search) return;
      e.preventDefault();
      e.stopPropagation();
      void Promise.resolve(leave.current()).then((ok) => {
        if (ok !== false) navigate(a.pathname + a.search + a.hash);
      });
    };
    document.addEventListener('click', onClick, true);
    return () => document.removeEventListener('click', onClick, true);
  }, [dirty, navigate]);
}

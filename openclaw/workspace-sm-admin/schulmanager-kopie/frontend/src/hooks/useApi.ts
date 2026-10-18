import { useCallback, useEffect, useRef, useState } from 'react';
import { useLive } from './useLive';

export interface UseApiOptions {
  /** Live-Scopes: bei passenden Änderungen neu laden */
  live?: string[];
  liveDates?: string[];
  /** false = nicht laden */
  enabled?: boolean;
  /** beim Neuladen alte Daten behalten (kein Flackern) */
  keepPrevious?: boolean;
}

export interface ApiState<T> {
  data: T | undefined;
  error: unknown;
  loading: boolean;
  /** true nur beim ersten Laden (noch keine Daten) */
  initialLoading: boolean;
  reload: () => void;
  setData: (fn: T | ((prev: T | undefined) => T)) => void;
}

/**
 * Lädt Daten über eine async-Funktion, mit Abbruch veralteter Anfragen,
 * manueller Neuladefunktion und optionaler Live-Aktualisierung.
 */
export function useApi<T>(fn: (signal: AbortSignal) => Promise<T>, deps: readonly unknown[], opts: UseApiOptions = {}): ApiState<T> {
  const [data, setDataState] = useState<T | undefined>(undefined);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(opts.enabled !== false);
  const [reloadKey, setReloadKey] = useState(0);
  const fnRef = useRef(fn);
  fnRef.current = fn;
  const enabled = opts.enabled !== false;
  const keepPrevious = opts.keepPrevious !== false;

  const { tick } = useLive(opts.live ?? null, undefined, { dates: opts.liveDates, enabled: enabled && !!opts.live });

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return undefined;
    }
    const ctrl = new AbortController();
    setLoading(true);
    if (!keepPrevious) setDataState(undefined);
    fnRef
      .current(ctrl.signal)
      .then((d) => {
        if (ctrl.signal.aborted) return;
        setDataState(d);
        setError(null);
        setLoading(false);
      })
      .catch((e: unknown) => {
        if (ctrl.signal.aborted || (e instanceof DOMException && e.name === 'AbortError')) return;
        setError(e);
        setLoading(false);
      });
    return () => ctrl.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, reloadKey, tick, enabled]);

  const reload = useCallback(() => setReloadKey((k) => k + 1), []);
  const setData = useCallback((v: T | ((prev: T | undefined) => T)) => {
    setDataState((prev) => (typeof v === 'function' ? (v as (p: T | undefined) => T)(prev) : v));
  }, []);

  return { data, error, loading, initialLoading: loading && data === undefined, reload, setData };
}

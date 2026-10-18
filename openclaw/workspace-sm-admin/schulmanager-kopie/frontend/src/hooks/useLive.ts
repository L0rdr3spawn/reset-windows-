import { useEffect, useRef, useState } from 'react';
import { live, type LiveStatus } from '../api/events';
import type { LiveChangeEvent, LiveJobEvent } from '../api/types';
import { eventRelevant } from '../lib/live';

export interface UseLiveOptions {
  /** nur Ereignisse, die eines dieser Daten betreffen (ISO) */
  dates?: string[];
  /** Entprellung in ms (mehrere Ereignisse kurz hintereinander → ein Aufruf) */
  debounce?: number;
  enabled?: boolean;
}

/**
 * Live-Aktualisierung über SSE.
 * Liefert einen Zähler `tick`, der bei passenden Änderungen (oder nach Wiederverbindung)
 * hochzählt – ideal als Abhängigkeit zum Neuladen. Optional Callback.
 */
export function useLive(
  scope: string | readonly string[] | null,
  onChange?: (ev: LiveChangeEvent | null) => void,
  opts: UseLiveOptions = {},
): { tick: number; status: LiveStatus } {
  const [tick, setTick] = useState(0);
  const cbRef = useRef(onChange);
  cbRef.current = onChange;
  const scopes = scope === null ? null : Array.isArray(scope) ? (scope as string[]) : [scope as string];
  const key = scopes ? scopes.join('|') : '';
  const datesKey = (opts.dates ?? []).join('|');
  const debounce = opts.debounce ?? 250;
  const enabled = opts.enabled !== false && scopes !== null;

  useEffect(() => {
    if (!enabled) return undefined;
    const wanted = key ? key.split('|') : [];
    const dates = datesKey ? datesKey.split('|') : undefined;
    let timer: number | null = null;
    let lastEv: LiveChangeEvent | null = null;
    const fire = (ev: LiveChangeEvent | null) => {
      lastEv = ev;
      if (timer !== null) window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        timer = null;
        setTick((t) => t + 1);
        cbRef.current?.(lastEv);
      }, debounce);
    };
    const unsub = live.subscribe({
      onChange: (ev) => {
        if (eventRelevant(ev, wanted, dates)) fire(ev);
      },
      onReconnect: () => fire(null),
    });
    return () => {
      if (timer !== null) window.clearTimeout(timer);
      unsub();
    };
  }, [enabled, key, datesKey, debounce]);

  return { tick, status: useLiveStatus() };
}

/** Verbindungsstatus der Live-Verbindung. */
export function useLiveStatus(): LiveStatus {
  const [status, setStatus] = useState<LiveStatus>(live.getStatus());
  useEffect(() => live.onStatus(setStatus), []);
  return status;
}

/** Job-Ereignisse (Generator-Fortschritt). */
export function useJobEvents(jobId: string | null, onJob: (ev: LiveJobEvent) => void): void {
  const cbRef = useRef(onJob);
  cbRef.current = onJob;
  useEffect(() => {
    if (!jobId) return undefined;
    return live.subscribe({
      onJob: (ev) => {
        if (ev.id === jobId) cbRef.current(ev);
      },
    });
  }, [jobId]);
}

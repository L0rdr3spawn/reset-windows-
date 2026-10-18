/**
 * Gemeinsamer Cache für Stammdaten-Sammlungen und Einstellungen.
 * Mehrere Komponenten teilen sich eine Anfrage; bei Live-Änderungen
 * (Scope = Sammlungsname oder „all“) wird automatisch neu geladen.
 */
import { useEffect, useMemo, useState, useSyncExternalStore } from 'react';
import { data as dataApi, settings as settingsApi } from '../api/endpoints';
import { live } from '../api/events';
import type { CollectionName, CollectionTypes, Settings } from '../api/types';
import { scopeMatches } from '../lib/live';
import { onSessionReset } from '../lib/session';

interface Entry<T> {
  data: T | undefined;
  error: unknown;
  loading: boolean;
  promise: Promise<void> | null;
  stale: boolean;
  version: number;
}

type Key = CollectionName | 'settings';

const entries = new Map<Key, Entry<unknown>>();
const listeners = new Map<Key, Set<() => void>>();
/** Versionen sind global eindeutig: ein nach dem Leeren neu angelegter Eintrag hat nie die Version des alten. */
let seq = 0;

function entry(key: Key): Entry<unknown> {
  let e = entries.get(key);
  if (!e) {
    e = { data: undefined, error: null, loading: false, promise: null, stale: true, version: ++seq };
    entries.set(key, e);
  }
  return e;
}

function notify(key: Key): void {
  listeners.get(key)?.forEach((fn) => fn());
}

function fetcher(key: Key): Promise<unknown> {
  return key === 'settings' ? settingsApi.get() : dataApi.list(key);
}

function load(key: Key, force = false): Promise<void> {
  const e = entry(key);
  if (e.promise && !force) return e.promise;
  e.loading = true;
  const p = fetcher(key)
    .then((d) => {
      e.data = d;
      e.error = null;
    })
    .catch((err: unknown) => {
      e.error = err;
    })
    .finally(() => {
      e.loading = false;
      e.stale = false;
      e.promise = null;
      e.version = ++seq;
      // nach einer Sitzungs-Rücksetzung gehört `e` nicht mehr zum Cache: Antwort des vorigen Kontos verwerfen
      if (entries.get(key) === e) notify(key);
    });
  e.promise = p;
  e.version = ++seq;
  notify(key);
  return p;
}

/** Sammlung vorab laden (ohne Komponente), z. B. vor dem Öffnen eines Dialogs. */
export function preloadCollection(key: Key): Promise<void> {
  const e = entry(key);
  return e.stale ? load(key) : Promise.resolve();
}

/** Aktueller Inhalt des Caches (ohne Laden) – für Tests und Diagnose. */
export function peekCollection(key: Key): unknown {
  return entries.get(key)?.data;
}

/** Markiert Sammlung(en) als veraltet und lädt sie neu, falls jemand zuhört. */
export function invalidate(...keys: Key[]): void {
  for (const k of keys) {
    const e = entry(k);
    e.stale = true;
    if (listeners.get(k)?.size) void load(k, true);
  }
}

export function invalidateAll(): void {
  invalidate(...(Array.from(entries.keys()) as Key[]));
}

/**
 * Leert den Cache (Abmeldung, 401, Kontowechsel – über `lib/session`). Laufende Anfragen des vorigen Kontos landen
 * nicht mehr im Cache; wer noch zuhört, zeichnet neu und lädt mit dem neuen Konto.
 */
export function clearCollectionCache(): void {
  entries.clear();
  listeners.forEach((_set, key) => notify(key));
}

onSessionReset(clearCollectionCache);

// Live-Abo: eine Verbindung für alle Sammlungen
let liveUnsub: (() => void) | null = null;
function ensureLive(): void {
  if (liveUnsub) return;
  liveUnsub = live.subscribe({
    onChange: (ev) => {
      for (const key of entries.keys()) {
        const wanted = key === 'settings' ? ['settings'] : [key];
        if (scopeMatches(ev.scope, wanted)) invalidate(key);
      }
    },
    onReconnect: () => invalidateAll(),
  });
}

function subscribe(key: Key, fn: () => void): () => void {
  let set = listeners.get(key);
  if (!set) {
    set = new Set();
    listeners.set(key, set);
  }
  set.add(fn);
  ensureLive();
  return () => {
    set?.delete(fn);
  };
}

export interface CollectionState<T> {
  data: T | undefined;
  error: unknown;
  loading: boolean;
  reload: () => void;
}

function useKey<T>(key: Key, enabled: boolean): CollectionState<T> {
  const version = useSyncExternalStore(
    (fn) => subscribe(key, fn),
    () => entry(key).version,
    () => entry(key).version, // statisches Rendern (Tests, Druck): ohne Server-Snapshot würde React hier abbrechen
  );
  useEffect(() => {
    if (!enabled) return;
    const e = entry(key);
    if (e.stale && !e.promise) void load(key);
  }, [key, enabled, version]);
  const e = entry(key);
  return useMemo(
    () => ({
      data: e.data as T | undefined,
      error: e.error,
      loading: e.loading || (enabled && e.data === undefined && !e.error),
      reload: () => void load(key, true),
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [version, enabled, key],
  );
}

export function useCollection<K extends CollectionName>(name: K, enabled = true): CollectionState<CollectionTypes[K][]> {
  return useKey<CollectionTypes[K][]>(name, enabled);
}

export function useSettings(enabled = true): CollectionState<Settings> {
  return useKey<Settings>('settings', enabled);
}

/** Map id → Objekt für schnelle Namensauflösung. */
export function useIndex<K extends CollectionName>(name: K, enabled = true): Map<string, CollectionTypes[K]> {
  const { data } = useCollection(name, enabled);
  return useMemo(() => {
    const m = new Map<string, CollectionTypes[K]>();
    for (const x of data ?? []) m.set((x as { id: string }).id, x);
    return m;
  }, [data]);
}

/** Einfacher Zustand für Komponenten, die eine Sammlung nur einmalig brauchen. */
export function useOnce<T>(fn: () => Promise<T>): { data: T | undefined; error: unknown } {
  const [state, setState] = useState<{ data: T | undefined; error: unknown }>({ data: undefined, error: null });
  useEffect(() => {
    let alive = true;
    fn()
      .then((d) => alive && setState({ data: d, error: null }))
      .catch((e: unknown) => alive && setState({ data: undefined, error: e }));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return state;
}

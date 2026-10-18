/**
 * Feature-Registry (Erweiterung 2, docs/ARCHITECTURE.md §9.2).
 *
 * Jedes Feature liegt in `src/features/<feature>/` und exportiert aus `module.tsx` als `default` ein
 * {@link FeatureModule}. Die Registry lädt alle Module per `import.meta.glob('./*\/module.tsx', { eager: true })`;
 * `App.tsx` (Routen + Guard), `lib/permissions.ts` (Menü, Zugriff) und `DashboardPage` (Widgets) lesen sie aus.
 * Anleitung und Beispiel: `src/features/README.md`.
 *
 * Hinweis Importzyklus: Vite stellt die Glob-Importe an den Anfang dieser Datei – Feature-Module werden also
 * ausgewertet, BEVOR der Rest dieser Datei läuft. Was Module schon beim Laden brauchen, ist deshalb als
 * (gehobene) Funktionsdeklaration umgesetzt: `defineFeature`, `setBadge`, `getBadge`, `badgeStore`.
 * Typen bitte mit `import type` holen.
 */
import { useSyncExternalStore, type ComponentType, type ReactNode } from 'react';
import type { Permission, Role, User } from '../api/types';
import { navAllowed, registerFeatureNav, registerFeatureRoutes, type NavGroup, type NavItem } from '../lib/permissions';
import { onSessionReset } from '../lib/session';

export type { NavGroup, NavItem } from '../lib/permissions';

/**
 * Eine Seite des Features (Pfad absolut, z. B. `/postfach` oder `/kursraeume/:id`).
 *
 * Rechte: Ohne eigene Regeln (`anyOf`/`roles`/`notRoles`) gelten die des Menüeintrags mit dem längsten passenden
 * Präfix (wie bei den Kernseiten). Mit eigenen Regeln gelten NUR diese – so kann z. B. `/planung/antraege`
 * andere Rechte verlangen als das Menü „Planung“.
 */
export interface FeatureRoute {
  path: string;
  element: ReactNode;
  /** mindestens eines dieser Rechte nötig */
  anyOf?: Permission[];
  /** nur diese Rollen */
  roles?: Role[];
  /** diese Rollen ausgeschlossen */
  notRoles?: Role[];
  /** Seitentitel in der Kopfzeile (Standard: Beschriftung des passenden Menüeintrags) */
  title?: string;
  /** `false` = ohne App-Rahmen (Vollbild, Druck); Standard: im Layout mit Menü */
  layout?: boolean;
}

/** Menüeintrag eines Features (Gruppe `kommunikation` für Postfach/Kursräume). */
export type FeatureNavItem = NavItem;

/** Kachel auf der Startseite. `order < 0` erscheint über den Standard-Bereichen der Rolle, sonst darunter. */
export interface FeatureWidget {
  id: string;
  element: ReactNode;
  order: number;
  roles?: Role[];
  notRoles?: Role[];
  anyOf?: Permission[];
  /** über die volle Breite statt einer halben Spalte (ab Tablet-Breite) */
  wide?: boolean;
}

export interface FeatureModule {
  /** eindeutig, klein, z. B. `postfach` */
  id: string;
  routes?: FeatureRoute[];
  nav?: FeatureNavItem[];
  widgets?: FeatureWidget[];
  /**
   * Optionale, unsichtbare Komponente, die im App-Rahmen dauerhaft gerendert wird (nur angemeldet), z. B. um
   * Badges per Live-Ereignis/Abfrage zu aktualisieren. Prüft Rechte selbst (`useUser()` + `can()`).
   */
  background?: ComponentType;
}

/** Typ-Hilfe für `module.tsx`: `export default defineFeature({ … })` (auch während des Ladens sicher). */
export function defineFeature(module: FeatureModule): FeatureModule {
  return module;
}

const ID_RE = /^[a-z][a-z0-9-]{0,39}$/;
const GROUPS: readonly NavGroup[] = ['alltag', 'kommunikation', 'planung', 'verwaltung', 'konto'];
/**
 * Pfade der Kernanwendung (App.tsx) – Features dürfen sie nicht überschreiben (Unterpfade sind erlaubt). Dazu gehören
 * auch die öffentlichen bzw. direkt verdrahteten Seiten (Passwort vergessen, Test-Postausgang, Konten verbinden).
 */
export const CORE_PATHS: ReadonlySet<string> = new Set([
  '/', '/login', '/passwort', '/zwei-faktor', '/monitor', '/druck', '/stundenplan', '/vertretung', '/planung',
  '/stammdaten', '/klausuren', '/aufsichten', '/mitteilungen', '/krankmeldungen', '/benutzer', '/daten', '/verlauf',
  '/profil', '/system', '/passwort-vergessen', '/passwort-zuruecksetzen', '/test-postausgang', '/konten-verbinden', '/abgemeldet',
]);

function warn(msg: string): void {
  if (typeof console !== 'undefined') console.warn(`[features] ${msg}`);
}

function isObject(x: unknown): x is Record<string, unknown> {
  return !!x && typeof x === 'object';
}

function normalizePath(path: string): string {
  return path.length > 1 ? path.replace(/\/+$/, '') : path;
}

/**
 * Prüft und normalisiert die per Glob geladenen Module (rein, testbar – Tests übergeben ein eigenes Objekt
 * im Format von `import.meta.glob`: `{ './demo/module.tsx': { default: modul } }`).
 * Ungültige Module/Einträge werden mit Warnung übersprungen, ebenso doppelte IDs und Pfade sowie Kernpfade.
 */
export function loadModules(entries: Record<string, unknown>): FeatureModule[] {
  const out: FeatureModule[] = [];
  const ids = new Set<string>();
  const paths = new Set<string>();
  for (const file of Object.keys(entries).sort()) {
    const raw = entries[file];
    const mod = isObject(raw) && 'default' in raw ? raw.default : raw;
    if (!isObject(mod) || typeof mod.id !== 'string' || !ID_RE.test(mod.id)) {
      warn(`${file}: kein gültiges Feature-Modul (default export mit id fehlt)`);
      continue;
    }
    if (ids.has(mod.id)) {
      warn(`${file}: Feature-ID „${mod.id}“ doppelt – übersprungen`);
      continue;
    }
    ids.add(mod.id);
    const routes: FeatureRoute[] = [];
    for (const r of Array.isArray(mod.routes) ? (mod.routes as unknown[]) : []) {
      if (!isObject(r) || typeof r.path !== 'string' || !r.path.startsWith('/') || r.path.startsWith('//')) {
        warn(`${mod.id}: Route ohne gültigen absoluten Pfad übersprungen`);
        continue;
      }
      const path = normalizePath(r.path);
      if (CORE_PATHS.has(path.toLowerCase())) {
        warn(`${mod.id}: Pfad ${path} gehört der Kernanwendung – übersprungen`);
        continue;
      }
      if (paths.has(path.toLowerCase())) {
        warn(`${mod.id}: Pfad ${path} ist schon vergeben – übersprungen`);
        continue;
      }
      paths.add(path.toLowerCase());
      routes.push({ ...(r as unknown as FeatureRoute), path });
    }
    const nav = (Array.isArray(mod.nav) ? (mod.nav as FeatureNavItem[]) : []).filter((n) => {
      const ok =
        isObject(n) &&
        typeof n.path === 'string' &&
        n.path.startsWith('/') &&
        typeof n.label === 'string' &&
        GROUPS.includes(n.group) &&
        (n.badge === undefined || typeof n.badge === 'function');
      if (!ok) warn(`${mod.id}: Menüeintrag ungültig (path/label/group/badge) – übersprungen`);
      return ok;
    });
    const widgets = (Array.isArray(mod.widgets) ? (mod.widgets as FeatureWidget[]) : []).filter((w) => {
      const ok = isObject(w) && typeof w.id === 'string' && typeof w.order === 'number' && Number.isFinite(w.order);
      if (!ok) warn(`${mod.id}: Widget ohne id/order übersprungen`);
      return ok;
    });
    out.push({
      id: mod.id,
      routes,
      nav,
      widgets,
      background: typeof mod.background === 'function' ? (mod.background as ComponentType) : undefined,
    });
  }
  return out;
}

type Who = (Pick<User, 'permissions' | 'role'> & Partial<User>) | null | undefined;

/** Alle Routen (Reihenfolge: Modul-Datei, dann Definition). */
export function featureRoutes(mods: readonly FeatureModule[] = FEATURES): FeatureRoute[] {
  return mods.flatMap((m) => m.routes ?? []);
}

/**
 * Darf der Benutzer die Route öffnen? Eigene Regeln der Route; ohne eigene Regeln `true` (dann prüft der Guard
 * in App.tsx bereits die Regeln des passenden Menüeintrags über `canAccessPath`).
 */
export function routeAllowed(user: Who, route: Pick<FeatureRoute, 'anyOf' | 'roles' | 'notRoles'>): boolean {
  return navAllowed(user, route);
}

/** Sichtbare Startseiten-Kacheln, sortiert nach `order` (stabil). */
export function widgetsFor(user: Who, mods: readonly FeatureModule[] = FEATURES): (FeatureWidget & { module: string })[] {
  if (!user) return [];
  return mods
    .flatMap((m) => (m.widgets ?? []).map((w) => ({ ...w, module: m.id })))
    .filter((w) => navAllowed(user, w))
    .map((w, idx) => ({ w, idx }))
    .sort((a, b) => a.w.order - b.w.order || a.idx - b.idx)
    .map(({ w }) => w);
}

/** Hintergrund-Komponenten aller Module. */
export function backgroundComponents(mods: readonly FeatureModule[] = FEATURES): { id: string; Component: ComponentType }[] {
  return mods.filter((m) => m.background).map((m) => ({ id: m.id, Component: m.background as ComponentType }));
}

/** Meldet Menüeinträge und Routenregeln der Module an `lib/permissions` (Menü, `canAccessPath`). */
export function registerModules(mods: readonly FeatureModule[]): void {
  registerFeatureNav(mods.flatMap((m) => m.nav ?? []));
  registerFeatureRoutes(
    featureRoutes(mods).map((r) => ({ path: r.path, anyOf: r.anyOf, roles: r.roles, notRoles: r.notRoles, title: r.title })),
  );
}

// ------------------------------------------------------------------ Badges (Zahlen am Menü)

export interface BadgeStore {
  /** Wert > 0 oder `null` */
  get(key: string): number | null;
  /** `null`/0/negativ entfernt den Badge; Kommazahlen werden abgerundet */
  set(key: string, value: number | null | undefined): void;
  /** alle Badges entfernen bzw. nur die mit diesem Präfix (z. B. `postfach.`) */
  clear(prefix?: string): void;
  subscribe(listener: () => void): () => void;
  /** steigt bei jeder Änderung (für `useSyncExternalStore`) */
  getVersion(): number;
}

/** Neuer, leerer Badge-Speicher (für Tests; die App nutzt den gemeinsamen über {@link badgeStore}). */
export function createBadgeStore(): BadgeStore {
  const values = new Map<string, number>();
  const listeners = new Set<() => void>();
  let version = 0;
  const emit = (): void => {
    version += 1;
    listeners.forEach((fn) => fn());
  };
  return {
    get(key) {
      const v = values.get(key);
      return v && v > 0 ? v : null;
    },
    set(key, value) {
      const next = typeof value === 'number' && Number.isFinite(value) && value > 0 ? Math.floor(value) : 0;
      if ((values.get(key) ?? 0) === next) return;
      if (next) values.set(key, next);
      else values.delete(key);
      emit();
    },
    clear(prefix) {
      const keys = [...values.keys()].filter((k) => !prefix || k.startsWith(prefix));
      if (!keys.length) return;
      keys.forEach((k) => values.delete(k));
      emit();
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    getVersion: () => version,
  };
}

// `var` (gehoben, anfangs undefined) statt `let`: Feature-Module dürfen Badges schon beim Laden setzen, also bevor
// diese Zeile ausgeführt wurde (siehe Hinweis Importzyklus oben).
// eslint-disable-next-line no-var
var sharedBadgeStore: BadgeStore | undefined;

/** Gemeinsamer Badge-Speicher der App (jederzeit sicher aufrufbar). */
export function badgeStore(): BadgeStore {
  if (!sharedBadgeStore) sharedBadgeStore = createBadgeStore();
  return sharedBadgeStore;
}

/** Badge setzen, z. B. `setBadge('postfach.unread', 3)`; `null`/0 entfernt ihn. */
export function setBadge(key: string, value: number | null | undefined): void {
  badgeStore().set(key, value);
}

/** Badge lesen, z. B. im Menüeintrag: `badge: () => getBadge('postfach.unread')`. */
export function getBadge(key: string): number | null {
  return badgeStore().get(key);
}

/** Bequemer Zugriff (`badges.set(…)`, `badges.get(…)`) – nur in Funktionen/Effekten verwenden, nicht beim Laden. */
export const badges: BadgeStore = badgeStore();

// Badges gehören zum angemeldeten Konto: bei Abmeldung, 401 und Kontowechsel leeren (U-01, lib/session.ts)
onSessionReset(() => badgeStore().clear());

/** Rendert neu, sobald sich ein Badge ändert; liefert die Versionsnummer. */
export function useBadgeVersion(store?: BadgeStore): number {
  const s = store ?? badgeStore();
  return useSyncExternalStore(s.subscribe, s.getVersion, s.getVersion);
}

/** Aktueller Wert eines Badges (mit Neuzeichnen bei Änderung). */
export function useBadge(key: string, store?: BadgeStore): number | null {
  const s = store ?? badgeStore();
  useBadgeVersion(s);
  return s.get(key);
}

/** Zahl eines Menüeintrags (Fehler im Feature-Code → keine Zahl). */
export function navBadge(item: Pick<NavItem, 'badge'>): number | null {
  if (!item.badge) return null;
  try {
    const n = item.badge();
    return typeof n === 'number' && Number.isFinite(n) && n > 0 ? Math.floor(n) : null;
  } catch {
    return null;
  }
}

/** Anzeige am Menü: „1“ … „99“, darüber „99+“. */
export function badgeText(n: number): string {
  return n > 99 ? '99+' : String(n);
}

// ------------------------------------------------------------------ Laden

const globbed = import.meta.glob('./*/module.tsx', { eager: true });

/** Alle gültigen Feature-Module (alphabetisch nach Datei). */
export const FEATURES: readonly FeatureModule[] = loadModules(globbed);

registerModules(FEATURES);

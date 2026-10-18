/**
 * Rechteprüfung, rechtebasiertes Menü und Routing-Schutz (rein, testbar).
 */
import type { Permission, Role, User } from '../api/types';

export const ROLE_LABELS: Record<Role, string> = {
  admin: 'Administration',
  schulleitung: 'Schulleitung',
  abteilungsleitung: 'Abteilungsleitung',
  planer: 'Stundenplanung',
  sekretariat: 'Sekretariat',
  lehrer: 'Lehrkraft',
  hausmeister: 'Hausmeister/in',
  schulbegleitung: 'Schulbegleitung',
  schueler: 'Schüler/in',
  eltern: 'Eltern',
  monitor: 'Monitor',
  zuschauer: 'Zuschauer/in (nur lesen)',
};

export const ALL_ROLES: Role[] = [
  'admin',
  'schulleitung',
  'abteilungsleitung',
  'planer',
  'sekretariat',
  'lehrer',
  'hausmeister',
  'schulbegleitung',
  'schueler',
  'eltern',
  'monitor',
  'zuschauer',
];

type UserLike = Pick<User, 'permissions' | 'role'> | null | undefined;

/** true, wenn der Benutzer mindestens eines der Rechte hat. */
export function can(user: UserLike, perm: Permission | readonly Permission[]): boolean {
  if (!user) return false;
  const list = Array.isArray(perm) ? perm : [perm as Permission];
  if (list.length === 0) return true;
  const have = new Set(user.permissions ?? []);
  return list.some((p) => have.has(p));
}

/** true, wenn der Benutzer alle Rechte hat. */
export function canAll(user: UserLike, perms: readonly Permission[]): boolean {
  if (!user) return false;
  const have = new Set(user.permissions ?? []);
  return perms.every((p) => have.has(p));
}

export function isFamily(user: UserLike): boolean {
  return !!user && (user.role === 'schueler' || user.role === 'eltern');
}

export type NavIcon =
  | 'home'
  | 'grid'
  | 'swap'
  | 'cog'
  | 'database'
  | 'exam'
  | 'whistle'
  | 'megaphone'
  | 'medical'
  | 'users'
  | 'transfer'
  | 'history'
  | 'user'
  | 'server'
  | 'monitor'
  | 'mail'
  | 'folder'
  | 'board';

/** Menügruppen in Anzeigereihenfolge („kommunikation“: Postfach, Kursräume). */
export type NavGroup = 'alltag' | 'kommunikation' | 'planung' | 'verwaltung' | 'konto';

export interface NavItem {
  path: string;
  label: string;
  /** Icon-Name aus components/Icon (unbekannte Namen → Info-Symbol) */
  icon: NavIcon | (string & {});
  /** mindestens eines dieser Rechte nötig (leer = alle angemeldeten) */
  anyOf?: Permission[];
  /** nur diese Rollen */
  roles?: Role[];
  /** diese Rollen ausgeschlossen */
  notRoles?: Role[];
  group: NavGroup;
  /** Zahl am Menüeintrag (z. B. ungelesene Nachrichten); `null`/0 = keine. Siehe features/registry.ts `getBadge`. */
  badge?: () => number | null;
  /** Text für Bildschirmleser, Standard „{n} neu“ */
  badgeLabel?: (n: number) => string;
  /** Sortierung innerhalb der Gruppe: Kern-Einträge 0, 10, 20 … (Listenreihenfolge), Features standardmäßig 1000 */
  order?: number;
}

export const NAV_GROUP_LABELS: Record<NavGroup, string> = {
  alltag: 'Schulalltag',
  kommunikation: 'Kommunikation',
  planung: 'Planung',
  verwaltung: 'Verwaltung',
  konto: 'Konto',
};

export const NAV_GROUP_ORDER: NavGroup[] = ['alltag', 'kommunikation', 'planung', 'verwaltung', 'konto'];

export const NAV_ITEMS: NavItem[] = [
  { path: '/', label: 'Start', icon: 'home', group: 'alltag', notRoles: ['monitor'] },
  { path: '/stundenplan', label: 'Stundenplan', icon: 'grid', group: 'alltag', notRoles: ['monitor'] },
  { path: '/vertretung', label: 'Vertretungsplan', icon: 'swap', group: 'alltag', anyOf: ['substitution.read'], notRoles: ['monitor'] },
  {
    path: '/krankmeldungen',
    label: 'Krankmeldungen',
    icon: 'medical',
    group: 'alltag',
    anyOf: ['student_absence.report', 'student_absence.read'],
  },
  { path: '/klausuren', label: 'Klausuren', icon: 'exam', group: 'alltag', notRoles: ['monitor'] },
  { path: '/aufsichten', label: 'Pausenaufsichten', icon: 'whistle', group: 'alltag', anyOf: ['plans.read_all'] },
  { path: '/planung', label: 'Planung', icon: 'cog', group: 'planung', anyOf: ['timetable.generate', 'settings.edit'] },
  { path: '/stammdaten', label: 'Stammdaten', icon: 'database', group: 'planung', anyOf: ['masterdata.edit', 'settings.edit'] },
  {
    path: '/daten',
    label: 'Import / Export',
    icon: 'transfer',
    group: 'planung',
    anyOf: ['masterdata.edit', 'settings.edit', 'timetable.generate'],
  },
  { path: '/benutzer', label: 'Benutzer', icon: 'users', group: 'verwaltung', anyOf: ['users.manage'] },
  { path: '/verlauf', label: 'Verlauf & Audit', icon: 'history', group: 'verwaltung', anyOf: ['audit.read', 'history.restore'] },
  { path: '/rechte', label: 'Rollen & Rechte', icon: 'lock', group: 'verwaltung', anyOf: ['rights.manage', 'users.manage'] },
  { path: '/system', label: 'System', icon: 'server', group: 'verwaltung', anyOf: ['system.admin'] },
  { path: '/monitor', label: 'Monitor-Ansicht', icon: 'monitor', group: 'verwaltung', anyOf: ['monitor.read'] },
  { path: '/monitore', label: 'Monitore einstellen', icon: 'monitor', group: 'verwaltung', anyOf: ['monitor.manage'] },
  { path: '/lizenz', label: 'Lizenz', icon: 'lock', group: 'verwaltung', anyOf: ['license.manage'] },
  { path: '/einrichtung', label: 'Schule einrichten', icon: 'cog', group: 'verwaltung', anyOf: ['settings.edit'] },
  { path: '/profil', label: 'Profil', icon: 'user', group: 'konto' },
];

export function navAllowed(user: UserLike, item: Pick<NavItem, 'anyOf' | 'roles' | 'notRoles'>): boolean {
  if (!user) return false;
  if (item.roles && !item.roles.includes(user.role)) return false;
  if (item.notRoles && item.notRoles.includes(user.role)) return false;
  if (item.anyOf && item.anyOf.length && !can(user, item.anyOf)) return false;
  return true;
}

let featureNav: NavItem[] = [];

/** Menüeinträge der Feature-Module (setzt features/registry.ts beim Laden; Tests rufen es direkt auf). */
export function registerFeatureNav(items: readonly NavItem[]): void {
  featureNav = items.map((i) => ({ ...i, order: i.order ?? 1000 }));
}

/** Kern- und Feature-Einträge, je Gruppe nach `order` sortiert (stabil). */
export function allNavItems(): NavItem[] {
  const core = NAV_ITEMS.map((i, n) => ({ ...i, order: i.order ?? n * 10 }));
  const items = [...core, ...featureNav];
  return NAV_GROUP_ORDER.flatMap((g) =>
    items
      .map((item, idx) => ({ item, idx }))
      .filter(({ item }) => item.group === g)
      .sort((a, b) => (a.item.order ?? 0) - (b.item.order ?? 0) || a.idx - b.idx)
      .map(({ item }) => item),
  );
}

export function visibleNav(user: UserLike): NavItem[] {
  return allNavItems().filter((i) => navAllowed(user, i));
}

/** Eintrag mit dem längsten passenden Präfix aus `items` (für die Markierung „aktuelle Seite“ im Menü). */
export function bestNavMatch<T extends Pick<NavItem, 'path'>>(items: readonly T[], path: string): T | undefined {
  let best: T | undefined;
  for (const item of items) {
    const matches = item.path === '/' ? path === '/' : path === item.path || path.startsWith(`${item.path}/`);
    if (matches && (!best || item.path.length > best.path.length)) best = item;
  }
  return best;
}

/** Findet den Menüeintrag zu einem Pfad (längstes Präfix). */
export function navItemFor(path: string): NavItem | undefined {
  return bestNavMatch(allNavItems(), path);
}

/** Zugriffsregeln einer Feature-Route (aus features/registry.ts). */
export interface RouteRule {
  path: string;
  anyOf?: Permission[];
  roles?: Role[];
  notRoles?: Role[];
  title?: string;
}

let featureRouteRules: RouteRule[] = [];

/** Routenregeln der Feature-Module (setzt features/registry.ts beim Laden; Tests rufen es direkt auf). */
export function registerFeatureRoutes(rules: readonly RouteRule[]): void {
  featureRouteRules = rules.map((r) => ({ ...r }));
}

/** Hat die Regel eigene Einschränkungen? (Sonst gelten die des Menüeintrags.) */
export function hasOwnRules(rule: Pick<RouteRule, 'anyOf' | 'roles' | 'notRoles'>): boolean {
  return !!(rule.anyOf?.length || rule.roles?.length || rule.notRoles?.length);
}

function decodeSegment(seg: string): string {
  try {
    return decodeURIComponent(seg).toLowerCase();
  } catch {
    return seg.toLowerCase();
  }
}

function scoreSegments(pattern: string[], i: number, path: string[], j: number): number {
  if (i === pattern.length) return j === path.length ? 0 : -1;
  const seg = pattern[i];
  if (seg === '*') return 1; // Rest (auch leer)
  const optional = seg.endsWith('?');
  const core = optional ? seg.slice(0, -1) : seg;
  const dynamic = core.startsWith(':');
  let best = -1;
  if (j < path.length && (dynamic || decodeSegment(path[j]) === core.toLowerCase())) {
    const rest = scoreSegments(pattern, i + 1, path, j + 1);
    if (rest >= 0) best = rest + (dynamic ? 3 : 10);
  }
  if (optional) best = Math.max(best, scoreSegments(pattern, i + 1, path, j));
  return best;
}

/**
 * Passt `path` auf ein Routenmuster im Stil von React Router (`/kursraeume/:id`, `:id?`, `*`, ohne Groß-/Kleinschreibung)?
 * Liefert eine Spezifität (statisch > Parameter > `*`) oder -1.
 */
export function matchPathPattern(pattern: string, path: string): number {
  const segments = (p: string) => p.split('/').filter(Boolean);
  return scoreSegments(segments(pattern), 0, segments(path.split(/[?#]/)[0]), 0);
}

/** Spezifischste Feature-Route zu einem Pfad. */
export function featureRouteFor(path: string): RouteRule | undefined {
  let best: RouteRule | undefined;
  let bestScore = -1;
  for (const rule of featureRouteRules) {
    const s = matchPathPattern(rule.path, path);
    if (s > bestScore) {
      best = rule;
      bestScore = s;
    }
  }
  return best;
}

/** Seitentitel für die Kopfzeile (Feature-Route mit `title`, sonst Menüeintrag). */
export function pageTitleFor(path: string): string | undefined {
  return featureRouteFor(path)?.title ?? navItemFor(path)?.label;
}

/**
 * Darf der Benutzer diesen Pfad öffnen? (Unbekannte Pfade → true, damit die 404-Seite erscheint.)
 * Feature-Routen mit eigenen Regeln entscheiden selbst; sonst gilt der Menüeintrag mit dem längsten Präfix.
 */
export function canAccessPath(user: UserLike, path: string): boolean {
  if (!user) return false;
  const route = featureRouteFor(path);
  if (route && hasOwnRules(route)) return navAllowed(user, route);
  if (path.startsWith('/druck/')) return user.role !== 'monitor';
  const item = navItemFor(path);
  if (!item) return true;
  return navAllowed(user, item);
}

/** Startseite nach der Anmeldung. */
export function homePath(user: (UserLike & { site?: string | null }) | null | undefined, firstSite?: string): string {
  if (!user) return '/login';
  if (user.role === 'monitor') {
    const site = user.site || firstSite;
    return site ? `/monitor/${encodeURIComponent(site)}` : '/monitor';
  }
  return '/';
}

export type DashboardPanel = 'family' | 'teacher' | 'planner';

/** Welche Dashboard-Bereiche bekommt ein Benutzer? */
export function dashboardPanels(user: (UserLike & { teacher_id?: string | null }) | null | undefined): DashboardPanel[] {
  if (!user) return [];
  const out: DashboardPanel[] = [];
  if (isFamily(user)) out.push('family');
  if (user.teacher_id || user.role === 'lehrer') out.push('teacher');
  if (can(user, ['timetable.generate', 'substitution.edit', 'settings.edit'])) out.push('planner');
  return out;
}

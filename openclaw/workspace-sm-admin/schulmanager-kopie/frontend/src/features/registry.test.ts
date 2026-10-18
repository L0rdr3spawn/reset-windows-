/**
 * Tests der Feature-Registry mit einem winzigen Demo-Modul, das NUR hier existiert (gemockter Glob:
 * `loadModules()` bekommt ein Objekt im Format von `import.meta.glob(..., { eager: true })`).
 */
import { createElement } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { Permission, Role } from '../api/types';
import {
  canAccessPath,
  featureRouteFor,
  matchPathPattern,
  navItemFor,
  pageTitleFor,
  visibleNav,
} from '../lib/permissions';
import {
  FEATURES,
  backgroundComponents,
  badgeStore,
  badgeText,
  createBadgeStore,
  defineFeature,
  featureRoutes,
  getBadge,
  loadModules,
  navBadge,
  registerModules,
  routeAllowed,
  setBadge,
  widgetsFor,
  type FeatureModule,
} from './registry';

const u = (role: Role, permissions: Permission[]) => ({ role, permissions });

function Demo() {
  return null;
}
const el = createElement(Demo);

const demo = defineFeature({
  id: 'demo',
  routes: [
    { path: '/demo', element: el, anyOf: ['messages.use'] },
    { path: '/demo/:id', element: el }, // ohne eigene Regeln → Regeln des Menüeintrags /demo
    { path: '/planung/demo-antraege/', element: el, anyOf: ['teacher_requests.review'], title: 'Demo-Anträge' },
    { path: '/demo-druck', element: el, layout: false, notRoles: ['monitor'] },
  ],
  nav: [
    {
      path: '/demo',
      label: 'Demo-Postfach',
      icon: 'megaphone',
      group: 'kommunikation',
      anyOf: ['messages.use'],
      badge: () => getBadge('demo.unread'),
    },
    { path: '/planung/demo-antraege', label: 'Demo-Anträge', icon: 'users', group: 'planung', anyOf: ['teacher_requests.review'] },
  ],
  widgets: [
    { id: 'b', element: el, order: 5 },
    { id: 'a', element: el, order: -1, roles: ['schueler', 'eltern'] },
    { id: 'c', element: el, order: 5, anyOf: ['messages.broadcast'] },
    { id: 'd', element: el, order: 1, notRoles: ['eltern'] },
  ],
  background: Demo,
});

/** Gemockter Glob: gültiges Demo-Modul + typische Fehler anderer Module. */
const GLOB: Record<string, unknown> = {
  './demo/module.tsx': { default: demo },
  './ohne-id/module.tsx': { default: { routes: [] } },
  './doppelt/module.tsx': { default: { ...demo, routes: [] } },
  './fehlerhaft/module.tsx': {
    default: {
      id: 'fehlerhaft',
      routes: [
        { path: 'relativ', element: el },
        { path: '/stundenplan', element: el }, // Kernpfad
        { path: '/DEMO', element: el }, // schon vergeben (Groß-/Kleinschreibung egal)
        { path: '/fehlerhaft/ok', element: el },
      ],
      nav: [
        { path: '/x', label: 'X', icon: 'home', group: 'unbekannt' },
        { path: '/y', label: 'Y', icon: 'home', group: 'alltag', badge: 3 },
      ],
      widgets: [{ id: 'ohne-order', element: el }],
    },
  },
};

function load(): FeatureModule[] {
  const warn = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
  try {
    return loadModules(GLOB);
  } finally {
    warn.mockRestore();
  }
}

afterEach(() => {
  registerModules(FEATURES); // echten Zustand wiederherstellen
  badgeStore().clear();
});

describe('Feature-Registry: Laden', () => {
  it('übernimmt gültige Module und überspringt fehlerhafte mit Warnung', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    const mods = loadModules(GLOB);
    expect(mods.map((m) => m.id)).toEqual(['demo', 'fehlerhaft']); // alphabetisch nach Datei, ohne-id + doppelt fehlen
    const bad = mods[1];
    expect(bad.routes?.map((r) => r.path)).toEqual(['/fehlerhaft/ok']);
    expect(bad.nav).toEqual([]);
    expect(bad.widgets).toEqual([]);
    const messages = warn.mock.calls.map((c) => String(c[0]));
    expect(messages.some((m) => m.includes('ohne-id'))).toBe(true);
    expect(messages.some((m) => m.includes('doppelt'))).toBe(true);
    expect(messages.some((m) => m.includes('/stundenplan') && m.includes('Kernanwendung'))).toBe(true);
    expect(messages.some((m) => m.includes('/DEMO') && m.includes('vergeben'))).toBe(true);
    warn.mockRestore();
  });

  it('normalisiert Pfade und liefert Routen in Definitionsreihenfolge', () => {
    const mods = load();
    expect(featureRoutes(mods).map((r) => r.path)).toEqual([
      '/demo',
      '/demo/:id',
      '/planung/demo-antraege',
      '/demo-druck',
      '/fehlerhaft/ok',
    ]);
    expect(featureRoutes(mods).find((r) => r.path === '/demo-druck')?.layout).toBe(false);
    expect(backgroundComponents(mods).map((b) => b.id)).toEqual(['demo']);
  });

  it('echte Module (src/features/*/module.tsx) sind gültig', () => {
    expect(Array.isArray(FEATURES)).toBe(true);
    for (const m of FEATURES) expect(m.id).toMatch(/^[a-z][a-z0-9-]*$/);
  });
});

describe('Feature-Registry: Rechte, Menü, Widgets', () => {
  it('routeAllowed prüft anyOf/roles/notRoles', () => {
    const [mod] = load();
    const [postfach, detail, antraege, druck] = mod.routes ?? [];
    expect(routeAllowed(u('lehrer', ['messages.use']), postfach)).toBe(true);
    expect(routeAllowed(u('monitor', ['monitor.read']), postfach)).toBe(false);
    expect(routeAllowed(u('monitor', ['monitor.read']), detail)).toBe(true); // keine eigenen Regeln
    expect(routeAllowed(null, detail)).toBe(false);
    expect(routeAllowed(u('schulleitung', ['teacher_requests.review']), antraege)).toBe(true);
    expect(routeAllowed(u('monitor', []), druck)).toBe(false);
  });

  it('Menü: Gruppe „Kommunikation“ nach dem Schulalltag, Badge aus dem Speicher', () => {
    registerModules(load());
    const nav = visibleNav(u('schueler', ['messages.use']));
    const paths = nav.map((i) => i.path);
    expect(paths).toContain('/demo');
    expect(paths).not.toContain('/planung/demo-antraege');
    const groups = nav.map((i) => i.group);
    expect(groups.indexOf('kommunikation')).toBeGreaterThan(groups.lastIndexOf('alltag'));
    expect(groups.indexOf('kommunikation')).toBeLessThan(groups.indexOf('konto'));
    const item = nav.find((i) => i.path === '/demo');
    expect(item && navBadge(item)).toBeNull();
    setBadge('demo.unread', 4);
    expect(item && navBadge(item)).toBe(4);
    expect(visibleNav(u('schueler', [])).map((i) => i.path)).not.toContain('/demo');
  });

  it('canAccessPath: eigene Routenregeln vor Menü-Präfix, sonst Regeln des Menüeintrags', () => {
    registerModules(load());
    const reviewer = u('schulleitung', ['teacher_requests.review', 'plans.read_all']);
    // unter „Planung“, aber eigene Regel → erreichbar ohne timetable.generate/settings.edit
    expect(canAccessPath(reviewer, '/planung/demo-antraege')).toBe(true);
    expect(canAccessPath(reviewer, '/planung/generator')).toBe(false);
    expect(canAccessPath(u('planer', ['timetable.generate']), '/planung/demo-antraege')).toBe(false);
    // /demo/:id ohne eigene Regeln erbt messages.use vom Menüeintrag /demo
    expect(canAccessPath(u('lehrer', ['messages.use']), '/demo/42')).toBe(true);
    expect(canAccessPath(u('lehrer', []), '/demo/42')).toBe(false);
    expect(canAccessPath(u('monitor', ['monitor.read']), '/demo-druck')).toBe(false);
    expect(canAccessPath(u('eltern', []), '/demo-druck')).toBe(true);
    // Kernseiten unverändert
    expect(canAccessPath(u('planer', ['timetable.generate']), '/planung/generator')).toBe(true);
    expect(navItemFor('/planung/demo-antraege')?.label).toBe('Demo-Anträge');
    expect(pageTitleFor('/planung/demo-antraege')).toBe('Demo-Anträge');
    expect(pageTitleFor('/demo/7')).toBe('Demo-Postfach');
    expect(pageTitleFor('/stundenplan/class/5a')).toBe('Stundenplan');
    expect(featureRouteFor('/demo/7')?.path).toBe('/demo/:id');
  });

  it('nach dem Zurücksetzen gelten wieder nur die echten Module', () => {
    registerModules(load());
    registerModules([]);
    expect(featureRouteFor('/demo')).toBeUndefined();
    expect(visibleNav(u('lehrer', ['messages.use'])).map((i) => i.path)).not.toContain('/demo');
  });

  it('widgetsFor filtert nach Rolle/Recht und sortiert stabil nach order', () => {
    const mods = load();
    expect(widgetsFor(u('schueler', []), mods).map((w) => w.id)).toEqual(['a', 'd', 'b']);
    expect(widgetsFor(u('eltern', []), mods).map((w) => w.id)).toEqual(['a', 'b']);
    expect(widgetsFor(u('lehrer', ['messages.broadcast']), mods).map((w) => `${w.module}:${w.id}`)).toEqual([
      'demo:d',
      'demo:b',
      'demo:c',
    ]);
    expect(widgetsFor(null, mods)).toEqual([]);
  });
});

describe('Routenmuster', () => {
  it('passt wie React Router (statisch > Parameter > *), ohne Groß-/Kleinschreibung', () => {
    expect(matchPathPattern('/demo', '/demo')).toBeGreaterThan(0);
    expect(matchPathPattern('/demo', '/demo/')).toBeGreaterThan(0);
    expect(matchPathPattern('/demo', '/Demo?x=1#y')).toBeGreaterThan(0);
    expect(matchPathPattern('/demo', '/demo/1')).toBe(-1);
    expect(matchPathPattern('/demo/:id', '/demo/1')).toBeGreaterThan(0);
    expect(matchPathPattern('/demo/:id', '/demo')).toBe(-1);
    expect(matchPathPattern('/demo/:id?', '/demo')).toBeGreaterThan(0);
    expect(matchPathPattern('/demo/:id?', '/demo/1')).toBeGreaterThan(0);
    expect(matchPathPattern('/demo/*', '/demo/a/b/c')).toBeGreaterThan(0);
    expect(matchPathPattern('/demo/neu', '/demo/neu')).toBeGreaterThan(matchPathPattern('/demo/:id', '/demo/neu'));
    expect(matchPathPattern('/demo/:id', '/demo/neu')).toBeGreaterThan(matchPathPattern('/demo/*', '/demo/neu'));
    expect(matchPathPattern('/ä/x', '/%C3%A4/x')).toBeGreaterThan(0);
  });
});

describe('Badges', () => {
  it('Speicher: setzen, abrunden, entfernen, Präfix leeren, Benachrichtigung', () => {
    const store = createBadgeStore();
    const seen: number[] = [];
    const off = store.subscribe(() => seen.push(store.getVersion()));
    store.set('a.x', 2.7);
    store.set('a.x', 2); // unverändert → kein Ereignis
    store.set('a.y', 5);
    store.set('b', 1);
    expect([store.get('a.x'), store.get('a.y'), store.get('b'), store.get('fehlt')]).toEqual([2, 5, 1, null]);
    store.set('b', 0);
    expect(store.get('b')).toBeNull();
    store.set('b', -3);
    store.set('b', Number.NaN);
    store.clear('a.');
    expect([store.get('a.x'), store.get('a.y')]).toEqual([null, null]);
    off();
    store.set('z', 9);
    expect(seen).toEqual([1, 2, 3, 4, 5]);
  });

  it('globale Funktionen und Menü-Anzeige', () => {
    setBadge('demo.unread', 120);
    expect(getBadge('demo.unread')).toBe(120);
    expect(badgeText(120)).toBe('99+');
    expect(badgeText(7)).toBe('7');
    expect(navBadge({ badge: () => getBadge('demo.unread') })).toBe(120);
    expect(
      navBadge({
        badge: () => {
          throw new Error('Feature-Fehler');
        },
      }),
    ).toBeNull();
    expect(navBadge({})).toBeNull();
    setBadge('demo.unread', null);
    expect(getBadge('demo.unread')).toBeNull();
  });
});

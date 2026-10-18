import { afterEach, describe, expect, it } from 'vitest';
import type { Permission, Role } from '../../api/types';
import {
  ALL_ROLES,
  NAV_GROUP_ORDER,
  ROLE_LABELS,
  allNavItems,
  bestNavMatch,
  can,
  canAccessPath,
  dashboardPanels,
  hasOwnRules,
  homePath,
  navItemFor,
  pageTitleFor,
  registerFeatureNav,
  registerFeatureRoutes,
  visibleNav,
} from '../permissions';

const u = (role: Role, permissions: Permission[], extra: Record<string, unknown> = {}) => ({ role, permissions, ...extra });

describe('Rechte', () => {
  it('can prüft eines von mehreren Rechten', () => {
    const p = u('planer', ['timetable.edit']);
    expect(can(p, 'timetable.edit')).toBe(true);
    expect(can(p, ['users.manage', 'timetable.edit'])).toBe(true);
    expect(can(p, 'users.manage')).toBe(false);
    expect(can(null, 'timetable.edit')).toBe(false);
  });

  it('Menü für Eltern enthält keine Verwaltung', () => {
    const paths = visibleNav(u('eltern', ['student_absence.report', 'student_absence.read'])).map((i) => i.path);
    expect(paths).toContain('/');
    expect(paths).toContain('/krankmeldungen');
    expect(paths).not.toContain('/benutzer');
    expect(paths).not.toContain('/planung');
    expect(paths).not.toContain('/aufsichten');
  });

  it('Admin sieht System und Benutzer', () => {
    const paths = visibleNav(u('admin', ['system.admin', 'users.manage', 'timetable.generate', 'masterdata.edit', 'plans.read_all'])).map((i) => i.path);
    expect(paths).toEqual(expect.arrayContaining(['/system', '/benutzer', '/planung', '/stammdaten', '/aufsichten']));
  });

  it('canAccessPath nutzt das längste Präfix', () => {
    expect(navItemFor('/planung/generator')?.path).toBe('/planung');
    expect(canAccessPath(u('lehrer', ['plans.read_all']), '/planung/generator')).toBe(false);
    expect(canAccessPath(u('planer', ['timetable.generate']), '/planung/generator')).toBe(true);
    expect(canAccessPath(u('schueler', []), '/stundenplan/student/S1')).toBe(true);
    expect(canAccessPath(u('schueler', []), '/gibt-es-nicht')).toBe(true);
  });

  it('Monitor wird auf seine Vollbildansicht geleitet', () => {
    expect(homePath({ ...u('monitor', ['monitor.read']), site: 'S1' })).toBe('/monitor/S1');
    expect(homePath(u('monitor', ['monitor.read']), 'S2')).toBe('/monitor/S2');
    expect(homePath(u('lehrer', []))).toBe('/');
    expect(canAccessPath(u('monitor', ['monitor.read']), '/')).toBe(false);
    expect(canAccessPath(u('monitor', ['monitor.read']), '/monitor/S1')).toBe(true);
  });

  it('dashboardPanels je Rolle', () => {
    expect(dashboardPanels(u('eltern', []))).toEqual(['family']);
    expect(dashboardPanels(u('lehrer', ['absence.report_self'], { teacher_id: 'MUE' }))).toEqual(['teacher']);
    expect(dashboardPanels(u('planer', ['timetable.generate'], { teacher_id: 'ABC' }))).toEqual(['teacher', 'planner']);
    expect(dashboardPanels(u('sekretariat', ['substitution.edit']))).toEqual(['planner']);
  });
});

describe('Feature-Einträge (Erweiterung 2)', () => {
  afterEach(() => {
    registerFeatureNav([]);
    registerFeatureRoutes([]);
  });

  it('Gruppe „Kommunikation“ steht zwischen Schulalltag und Planung', () => {
    expect(NAV_GROUP_ORDER).toEqual(['alltag', 'kommunikation', 'planung', 'verwaltung', 'konto']);
  });

  it('Feature-Menüeinträge werden nach order einsortiert (Kern 0, 10, 20 …, Features Standard 1000)', () => {
    registerFeatureNav([
      { path: '/postfach', label: 'Postfach', icon: 'mail', group: 'kommunikation' },
      { path: '/lehrkraft/profil', label: 'Profil als Lehrkraft', icon: 'clock', group: 'konto', order: -5 },
      { path: '/notizen', label: 'Notizen', icon: 'edit', group: 'alltag' },
    ]);
    const paths = allNavItems().map((i) => i.path);
    expect(paths.indexOf('/notizen')).toBeGreaterThan(paths.indexOf('/aufsichten')); // hinter allen Kern-Einträgen
    expect(paths.indexOf('/postfach')).toBeGreaterThan(paths.indexOf('/notizen'));
    expect(paths.indexOf('/postfach')).toBeLessThan(paths.indexOf('/planung'));
    expect(paths.indexOf('/lehrkraft/profil')).toBeLessThan(paths.indexOf('/profil'));
    expect(visibleNav(u('schueler', [])).map((i) => i.path)).toContain('/postfach');
  });

  it('genau ein aktiver Eintrag: längstes Präfix', () => {
    const items = [{ path: '/' }, { path: '/planung' }, { path: '/planung/antraege' }];
    expect(bestNavMatch(items, '/planung/antraege')?.path).toBe('/planung/antraege');
    expect(bestNavMatch(items, '/planung/generator')?.path).toBe('/planung');
    expect(bestNavMatch(items, '/planungen')).toBeUndefined();
    expect(bestNavMatch(items, '/')?.path).toBe('/');
  });

  it('Routenregeln haben Vorrang vor dem Menü-Präfix', () => {
    registerFeatureRoutes([
      { path: '/planung/antraege', anyOf: ['teacher_requests.review'], title: 'Anträge' },
      { path: '/planung/hilfe' },
    ]);
    const reviewer = u('schulleitung', ['teacher_requests.review']);
    expect(canAccessPath(reviewer, '/planung/antraege')).toBe(true);
    expect(canAccessPath(reviewer, '/planung/hilfe')).toBe(false); // ohne eigene Regeln: Menü „Planung“
    expect(canAccessPath(u('planer', ['timetable.generate']), '/planung/antraege')).toBe(false);
    expect(pageTitleFor('/planung/antraege')).toBe('Anträge');
    expect(pageTitleFor('/planung/hilfe')).toBe('Planung');
    expect(hasOwnRules({})).toBe(false);
    expect(hasOwnRules({ anyOf: [] })).toBe(false);
    expect(hasOwnRules({ notRoles: ['monitor'] })).toBe(true);
  });
});

describe('Rollen & Rechte', () => {
  it('Seite /rechte nur mit Recht, neue Rollen haben Namen', () => {
    expect(canAccessPath(u('schulleitung', ['rights.manage']), '/rechte')).toBe(true);
    expect(canAccessPath(u('lehrer', ['plans.read_all']), '/rechte')).toBe(false);
    expect(ROLE_LABELS.schulbegleitung).toBe('Schulbegleitung');
    expect(ALL_ROLES).toEqual(expect.arrayContaining(['abteilungsleitung', 'hausmeister', 'schulbegleitung']));
    expect(Object.keys(ROLE_LABELS).sort()).toEqual([...ALL_ROLES].sort());
  });
});

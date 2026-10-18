/**
 * Erreichbarkeit: Jeder Menüeintrag führt auf eine vorhandene Route und – für die Rollen, die ihn sehen – nicht auf
 * „Kein Zugriff“. „Meine Übersicht“ ist aufgelöst (Inhalte auf Start, Krankmeldungen, Noten), kein Link zeigt mehr dorthin.
 */
import { describe, expect, it } from 'vitest';
import type { Permission, Role, User } from '../../api/types';
import { featureRoutes } from '../../features/registry';
import { ALL_ROLES, allNavItems, canAccessPath, matchPathPattern, visibleNav } from '../permissions';

const SOURCES = import.meta.glob('../../**/*.{ts,tsx}', { query: '?raw', import: 'default', eager: true }) as Record<string, string>;
const APP = SOURCES['../../App.tsx'] ?? '';

/** Pfadmuster aller Routen: Kernseiten aus App.tsx + Feature-Routen. */
function routePatterns(): string[] {
  const core = [...APP.matchAll(/<Route\s+path="([^"*][^"]*)"/g)].map((m) => (m[1]!.startsWith('/') ? m[1]! : `/${m[1]}`));
  return ['/', ...core, ...featureRoutes().map((r) => r.path)];
}

function user(role: Role, permissions: Permission[]): Pick<User, 'role' | 'permissions'> {
  return { role, permissions };
}

describe('Menü und Routen', () => {
  it('jeder Menüeintrag hat eine Route', () => {
    const patterns = routePatterns();
    expect(patterns.length).toBeGreaterThan(30);
    for (const item of allNavItems()) {
      expect(
        patterns.some((p) => matchPathPattern(p, item.path) >= 0),
        `Menüeintrag ${item.path} ohne Route`,
      ).toBe(true);
    }
  });

  it('wer einen Menüeintrag sieht, darf die Seite öffnen (keine Sackgasse „Kein Zugriff“)', () => {
    const everything = [...new Set(allNavItems().flatMap((i) => i.anyOf ?? []))];
    for (const role of ALL_ROLES) {
      const u = user(role, everything);
      for (const item of visibleNav(u)) expect(canAccessPath(u, item.path), `${role}: ${item.path}`).toBe(true);
    }
  });

  it('Familien erreichen Krankmeldungen, Noten und Kursräume über das Menü', () => {
    for (const role of ['schueler', 'eltern'] as const) {
      const u = user(role, ['student_absence.read', 'student_absence.report', 'channels.use', 'channels.view_children', 'messages.use']);
      const paths = visibleNav(u).map((i) => i.path);
      for (const p of ['/', '/stundenplan', '/krankmeldungen', '/noten', '/klausuren', '/kursraeume', '/nachrichten']) expect(paths, `${role}: ${p}`).toContain(p);
      expect(paths).not.toContain('/meine-uebersicht');
    }
  });
});

describe('„Meine Übersicht“ ist aufgelöst', () => {
  it('kein Link und keine Seite verweisen mehr darauf (nur die Weiterleitung für alte Lesezeichen)', () => {
    const hits = Object.entries(SOURCES)
      .filter(([f]) => !f.includes('__tests__') && !f.endsWith('.test.ts') && !f.endsWith('.test.tsx'))
      .filter(([, text]) => text.includes('/meine-uebersicht'))
      .map(([f]) => f);
    expect(hits).toEqual(['../../features/students/module.tsx']);
    expect(Object.keys(SOURCES).some((f) => f.endsWith('OverviewPage.tsx'))).toBe(false);
  });

  it('die alte Adresse bleibt als Weiterleitung für alle Rollen offen', () => {
    expect(featureRoutes().some((r) => r.path === '/meine-uebersicht')).toBe(true);
    expect(canAccessPath(user('eltern', []), '/meine-uebersicht')).toBe(true);
    expect(canAccessPath(user('lehrer', []), '/meine-uebersicht')).toBe(true);
  });
});

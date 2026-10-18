/**
 * Feature-Modul „Plan prüfen“ (docs/PLAN-PRUEFUNG.md) für die Registry (`features/registry.ts`).
 *
 * * `/planung/vorschlaege` – Status der Dauerprüfung und offene Vorschlagspakete (Varianten vergleichen, „Diesen Plan nehmen“,
 *   verwerfen, später).
 * * `/planung/vorschlaege/:paket/:variante` – Stundenplan-Entwurf einer Variante (nichts wird gespeichert).
 * * Menü-Badge und Startseiten-Kachel mit der Zahl offener Vorschläge.
 */
import { lazy } from 'react';
import { defineFeature, getBadge } from '../registry';
import { PROPOSALS_BADGE, ProposalBadge } from './badge';

const ProposalsPage = lazy(() => import('./ProposalsPage'));
const PreviewPage = lazy(() => import('./PreviewPage'));
const ProposalsWidget = lazy(() => import('./widgets'));

export default defineFeature({
  id: 'planpruefung',
  routes: [
    { path: '/planung/vorschlaege', element: <ProposalsPage />, anyOf: ['timetable.generate', 'timetable.edit', 'settings.edit'], title: 'Planvorschläge' },
    { path: '/planung/vorschlaege/:paket/:variante', element: <PreviewPage />, anyOf: ['timetable.generate', 'timetable.edit', 'settings.edit'], title: 'Entwurf ansehen' },
  ],
  nav: [
    {
      path: '/planung/vorschlaege',
      label: 'Planvorschläge',
      icon: 'sparkles',
      group: 'planung',
      anyOf: ['timetable.generate', 'timetable.edit', 'settings.edit'],
      badge: () => getBadge(PROPOSALS_BADGE),
      badgeLabel: (n) => `${n} offen`,
    },
  ],
  widgets: [{ id: 'vorschlaege', element: <ProposalsWidget />, order: -20, anyOf: ['timetable.generate', 'timetable.edit', 'settings.edit'] }],
  background: ProposalBadge,
});

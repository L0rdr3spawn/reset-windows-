/**
 * Feature-Modul „Kompetenzraster und Lernstand“ (docs/KOMPETENZEN.md) für die Registry (`features/registry.ts`).
 *
 * * `/kompetenzen` – Lehrkräfte und Leitung: Klassenübersicht (Heatmap), Lernstand je Kind samt Lernplan und
 *   Abzeichen, Rahmen verwalten, Abzeichen definieren und vergeben.
 * * `/lernstand` – Schüler/innen (selbst einschätzen, Wochenplan, Abzeichen) und Eltern (je Kind, nur ansehen).
 */
import { lazy } from 'react';
import { defineFeature } from '../registry';

const CompetencyPage = lazy(() => import('./CompetencyPage'));
const PupilPage = lazy(() => import('./PupilPage'));

export default defineFeature({
  id: 'kompetenzen',
  routes: [
    { path: '/kompetenzen', element: <CompetencyPage />, anyOf: ['competency.read', 'competency.manage'], notRoles: ['schueler', 'eltern', 'admin'], title: 'Kompetenzen' },
    { path: '/lernstand', element: <PupilPage />, roles: ['schueler', 'eltern'], title: 'Lernstand' },
  ],
  nav: [
    { path: '/kompetenzen', label: 'Kompetenzen', icon: 'grid', group: 'alltag', anyOf: ['competency.read', 'competency.manage'], notRoles: ['schueler', 'eltern', 'admin'] },
    { path: '/lernstand', label: 'Lernstand', icon: 'check', group: 'alltag', roles: ['schueler', 'eltern'] },
  ],
});

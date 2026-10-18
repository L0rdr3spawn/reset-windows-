/**
 * Feature-Modul „Datenschutz“ (docs/DATENSCHUTZ-LOESCHKONZEPT.md): Aufbewahrungsfristen, Warteliste „ausgetreten“,
 * Vorschau „Was würde gelöscht“, Löschprotokoll sowie Auskunft und Sofort-Löschen für eine Person.
 * Backend: `/privacy/*` (Rechte `privacy.manage`, für Auskunft/Löschen `privacy.subject`).
 *
 * Importzyklus (siehe registry.ts): beim Laden nur `defineFeature`; Seiten per lazy().
 */
import { lazy } from 'react';
import { defineFeature } from '../registry';

const DatenschutzPage = lazy(() => import('./DatenschutzPage'));

export default defineFeature({
  id: 'datenschutz',
  routes: [{ path: '/datenschutz', element: <DatenschutzPage />, anyOf: ['privacy.manage'], title: 'Datenschutz und Löschkonzept' }],
  nav: [{ path: '/datenschutz', label: 'Datenschutz', icon: 'shield', group: 'verwaltung', anyOf: ['privacy.manage'], order: 1030 }],
});

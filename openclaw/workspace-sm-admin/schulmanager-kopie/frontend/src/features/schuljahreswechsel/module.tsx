/**
 * Feature-Modul „Schuljahreswechsel“ (docs/PRODUKTREIFE.md): Klassen hochstufen, Abgänger austragen, neue Klassen,
 * Kursräume archivieren, Notenbücher abschließen – mit Vorschau und Rückgängig. Das Backend verlangt
 * `settings.edit` + `masterdata.edit` + `users.manage` (Administration und Schulleitung).
 *
 * Importzyklus (siehe registry.ts): beim Laden nur `defineFeature`; Seiten per lazy().
 */
import { lazy } from 'react';
import { defineFeature } from '../registry';

const WechselPage = lazy(() => import('./WechselPage'));

export default defineFeature({
  id: 'schuljahreswechsel',
  routes: [{ path: '/schuljahreswechsel', element: <WechselPage />, roles: ['admin', 'schulleitung'], title: 'Schuljahreswechsel' }],
  nav: [{ path: '/schuljahreswechsel', label: 'Schuljahreswechsel', icon: 'calendar', group: 'verwaltung', roles: ['admin', 'schulleitung'], order: 1020 }],
});

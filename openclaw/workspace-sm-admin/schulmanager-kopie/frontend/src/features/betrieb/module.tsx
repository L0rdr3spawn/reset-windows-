/**
 * Feature-Modul „Betrieb“ (docs/PRODUKTREIFE.md): Status-Seite der Administration – Version, Datenbankstand, Speicher,
 * Mail, Sicherungen mit Test-Restore, Wartungslauf und Fehlerprotokoll. Nur Recht `system.admin`.
 *
 * Importzyklus (siehe registry.ts): beim Laden nur `defineFeature`; Seiten per lazy().
 */
import { lazy } from 'react';
import { defineFeature } from '../registry';

const BetriebPage = lazy(() => import('./BetriebPage'));

export default defineFeature({
  id: 'betrieb',
  routes: [{ path: '/betrieb', element: <BetriebPage />, anyOf: ['system.admin'], title: 'Betrieb und Status' }],
  nav: [{ path: '/betrieb', label: 'Betrieb', icon: 'server', group: 'verwaltung', anyOf: ['system.admin'], order: 1010 }],
});

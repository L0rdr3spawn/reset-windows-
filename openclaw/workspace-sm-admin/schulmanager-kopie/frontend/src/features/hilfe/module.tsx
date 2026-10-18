/**
 * Feature-Modul „Hilfe“ (docs/PRODUKTREIFE.md): Handbuch in der App – Kurzanleitungen je Rolle aus
 * `docs/hilfe/*.md` (Backend: `GET /manual`). Für alle angemeldeten Rollen außer Monitor.
 *
 * Importzyklus (siehe registry.ts): beim Laden nur `defineFeature`; Seiten per lazy().
 */
import { lazy } from 'react';
import { defineFeature } from '../registry';

const HilfePage = lazy(() => import('./HilfePage'));

export default defineFeature({
  id: 'hilfe',
  routes: [{ path: '/hilfe', element: <HilfePage />, notRoles: ['monitor'], title: 'Hilfe' }],
  nav: [{ path: '/hilfe', label: 'Hilfe', icon: 'info', group: 'konto', notRoles: ['monitor'], order: 950 }],
});

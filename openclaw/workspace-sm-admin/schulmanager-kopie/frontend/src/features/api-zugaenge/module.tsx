/**
 * Feature-Modul „API-Zugänge“ (docs/API-ZUGAENGE.md) für die Registry (`features/registry.ts`).
 *
 * * `/api-zugaenge` – Zugänge für Apps/KI-Werkzeuge ausgeben (Recht `api.own`), mit `api.manage` auch alle sehen und
 *   widerrufen. Bereichsliste und Filterwerte kommen vom Server (`GET /api-access/meta`) – nichts doppelt pflegen.
 *
 * Importzyklus (siehe registry.ts): beim Laden nur `defineFeature`; Seiten per lazy().
 */
import { lazy } from 'react';
import type { Permission } from '../../api/types';
import { defineFeature } from '../registry';

const ApiAccessPage = lazy(() => import('./ApiAccessPage'));

const ANY_OF: Permission[] = ['api.own', 'api.manage'];

export default defineFeature({
  id: 'api-zugaenge',
  routes: [{ path: '/api-zugaenge', element: <ApiAccessPage />, anyOf: ANY_OF, title: 'API-Zugänge' }],
  nav: [{ path: '/api-zugaenge', label: 'API-Zugänge', icon: 'key', group: 'verwaltung', anyOf: ANY_OF }],
});

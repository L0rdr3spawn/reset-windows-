/**
 * Feature-Modul „Anmeldedienste“ (ARCHITECTURE.md §11.4) für die Registry (`features/registry.ts`).
 *
 * * `/anmeldedienste` (nur Administration) – Microsoft, Apple, Google, Schulkonto (OIDC) einrichten.
 * * Einhängepunkte in geteilten Seiten: `slots.tsx` (Login-Knöpfe + Fehlertexte, Profil „Verbundene Konten“,
 *   Benutzerverwaltung „Verbundene Konten“).
 *
 * Importzyklus (siehe registry.ts): beim Laden nur `defineFeature`; Seiten per lazy().
 */
import { lazy } from 'react';
import { defineFeature } from '../registry';

const SetupPage = lazy(() => import('./SetupPage'));

export default defineFeature({
  id: 'anmeldedienste',
  routes: [{ path: '/anmeldedienste', element: <SetupPage />, roles: ['admin'], title: 'Anmeldedienste' }],
  nav: [{ path: '/anmeldedienste', label: 'Anmeldedienste', icon: 'key', group: 'verwaltung', roles: ['admin'] }],
});

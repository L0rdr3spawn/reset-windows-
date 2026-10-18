/**
 * Feature-Modul „Anmelde-Richtlinien“ (§11.5) für die Registry (`features/registry.ts`).
 *
 * * `/anmelde-richtlinien` – Verwaltung (Recht `login_policy.manage`: Administration, Schulleitung): wer darf sich wie
 *   anmelden, welche Anbieter-Konten müssen verbunden sein (Standard, Rollen, Jahrgänge, Klassen mit Zielgruppe, Personen),
 *   Vorschau „Was gilt für …?“, Bericht „Wer hat noch nicht verbunden?“.
 * * `/konten-verbinden` (Pflicht-Verknüpfungen herstellen) ist in `App.tsx` verdrahtet (Guard), Seite `LinkSetupPage.tsx`.
 *
 * Importzyklus (siehe registry.ts): beim Laden nur `defineFeature`; Seiten per lazy().
 */
import { lazy } from 'react';
import type { Permission } from '../../api/types';
import { defineFeature } from '../registry';

const PolicyPage = lazy(() => import('./PolicyPage'));

const ANY_OF: Permission[] = ['login_policy.manage'];

export default defineFeature({
  id: 'anmelderichtlinien',
  routes: [{ path: '/anmelde-richtlinien', element: <PolicyPage />, anyOf: ANY_OF, title: 'Anmelde-Richtlinien' }],
  nav: [{ path: '/anmelde-richtlinien', label: 'Anmelde-Richtlinien', icon: 'shield', group: 'verwaltung', anyOf: ANY_OF }],
});

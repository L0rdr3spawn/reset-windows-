/**
 * Feature-Modul „Zugangsdaten“ (§11.3): Stapel-Seite `/zugangsdaten/:id` mit Downloads (PDF/ZIP) und E-Mail-Versand.
 * Ohne Menüeintrag – erreichbar über Benutzerverwaltung, Klassen-Assistent und Klassen-Seite.
 * Importzyklus (siehe registry.ts): beim Laden nur `defineFeature`; Seiten per lazy().
 */
import { lazy } from 'react';
import { defineFeature } from '../registry';

const BatchPage = lazy(() => import('./BatchPage'));

export default defineFeature({
  id: 'zugangsdaten',
  routes: [{ path: '/zugangsdaten/:id', element: <BatchPage />, anyOf: ['users.manage', 'passwords.reset'], title: 'Zugangsdaten' }],
  nav: [],
});

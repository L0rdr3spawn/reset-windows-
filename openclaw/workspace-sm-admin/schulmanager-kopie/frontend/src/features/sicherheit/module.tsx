/**
 * Feature-Modul „Sicherheit“: `/sicherheit` (Recht `login_policy.manage`) – Zwei-Faktor-Vorgabe, Abmeldung bei
 * Inaktivität, Startpasswort-Frist, Anmelde-Drosselungen; dazu ein Startseiten-Hinweis „Zwei-Faktor empfohlen“.
 */
import { lazy } from 'react';
import type { Permission } from '../../api/types';
import { defineFeature } from '../registry';

const SecurityPage = lazy(() => import('./SecurityPage'));
const TwoFactorHint = lazy(() => import('./TwoFactorHint'));

const ANY_OF: Permission[] = ['login_policy.manage'];

export default defineFeature({
  id: 'sicherheit',
  routes: [{ path: '/sicherheit', element: <SecurityPage />, anyOf: ANY_OF, title: 'Sicherheit' }],
  nav: [{ path: '/sicherheit', label: 'Sicherheit', icon: 'shield', group: 'verwaltung', anyOf: ANY_OF }],
  widgets: [{ id: 'zwei-faktor', element: <TwoFactorHint />, order: -20, notRoles: ['schueler', 'eltern', 'monitor'] }],
});

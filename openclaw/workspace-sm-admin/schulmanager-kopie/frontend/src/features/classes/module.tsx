/**
 * Feature-Modul „Klassen“ (ARCHITECTURE.md §10.3) für die Registry (`features/registry.ts`).
 *
 * * `/klassen` – Klasse suchen (Name, Klassenleitung, Raum; Filter Standort), Liste nach Jahrgang.
 * * `/klassen/:id` – Kopf (Stufe, Standort, Klassenraum, Klassenleitung – mit `masterdata.edit` direkt änderbar),
 *   Reiter Wochenplan (konkrete Kalenderwoche inkl. Vertretungen; mit `substitution.edit` „Findet nicht statt“ und
 *   „Klasse ist nicht da“ mit Vorschau der automatischen Umstellung), Lehrkräfte, Schüler/innen.
 * * `/klassen/neu` – Klassen-Assistent (Klasse → Schülerliste einfügen → Konten → Zugangsbriefe, §11.3).
 * * Sichtbarkeit prüft das Backend (Lehrkräfte nur eigene Klassen); Schüler/innen, Eltern und Monitor nie.
 *
 * Importzyklus (siehe registry.ts): beim Laden nur `defineFeature`; Seiten per lazy().
 */
import { lazy } from 'react';
import type { Permission, Role } from '../../api/types';
import { defineFeature } from '../registry';

const ClassesPage = lazy(() => import('./ClassesPage'));
const ClassDetailPage = lazy(() => import('./ClassDetailPage'));
const NewClassPage = lazy(() => import('./NewClassPage'));
const RegisterPage = lazy(() => import('./RegisterPage'));

const ANY_OF: Permission[] = ['plans.read_all', 'masterdata.edit', 'substitution.edit'];
const NOT_ROLES: Role[] = ['schueler', 'eltern', 'monitor'];

export default defineFeature({
  id: 'klassen',
  routes: [
    { path: '/klassen', element: <ClassesPage />, anyOf: ANY_OF, notRoles: NOT_ROLES, title: 'Klassen' },
    // §11.3: Klassen-Assistent (statischer Pfad hat Vorrang vor /klassen/:id)
    { path: '/klassen/neu', element: <NewClassPage />, anyOf: ['masterdata.edit'], notRoles: NOT_ROLES, title: 'Neue Klasse' },
    { path: '/klassen/:id', element: <ClassDetailPage />, anyOf: ANY_OF, notRoles: NOT_ROLES, title: 'Klassen' },
    { path: '/klassenbuch', element: <RegisterPage />, anyOf: ['student_absence.read'], notRoles: NOT_ROLES, title: 'Klassenbuch' },
  ],
  nav: [
    { path: '/klassen', label: 'Klassen', icon: 'board', group: 'alltag', order: 15, anyOf: ANY_OF, notRoles: NOT_ROLES },
    { path: '/klassenbuch', label: 'Klassenbuch', icon: 'check', group: 'alltag', order: 16, anyOf: ['student_absence.read'], notRoles: NOT_ROLES },
  ],
});

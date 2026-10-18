/**
 * Feature-Modul „Notenbuch“ (B-52, `docs/NOTENBUCH.md`) für die Registry (`features/registry.ts`).
 *
 * * `/notenbuch` – Notenbücher des Halbjahres (eigene Kurse bzw. alle für die Schulleitung), neues Notenbuch anlegen
 * * `/notenbuch/:bookId` – Notentabelle eines Kursteils (Eintragen, Schnitte, Vorschlag, Endnote, Sperren)
 * * `/notenbuch/klasse/:classId` – Klassenübersicht, Versetzungswarnung, Notenkonferenz-Liste (Klassenleitung, Leitung)
 * * `/notenbuch/verwaltung` – Einstellungen und Export (Schulleitung, Sekretariat)
 * * Sicht für Schüler/innen und Eltern: eingebettet in „Meine Noten“ (`/noten`, `features/students/GradesPage.tsx`)
 *
 * Importzyklus (siehe registry.ts): beim Laden nur `defineFeature`; Seiten per lazy().
 */
import { lazy } from 'react';
import type { Permission, Role } from '../../api/types';
import { defineFeature } from '../registry';

const BooksPage = lazy(() => import('./BooksPage'));
const BookPage = lazy(() => import('./BookPage'));
const ClassPage = lazy(() => import('./ClassPage'));
const AdminPage = lazy(() => import('./AdminPage'));

const ANY_OF: Permission[] = ['gradebook.use', 'gradebook.read_class', 'gradebook.manage', 'gradebook.export'];
const VIEW_OF: Permission[] = ['gradebook.use', 'gradebook.read_class', 'gradebook.manage'];
const ADMIN_OF: Permission[] = ['gradebook.manage', 'gradebook.export'];
const NOT_ROLES: Role[] = ['schueler', 'eltern', 'monitor', 'admin'];

export default defineFeature({
  id: 'notenbuch',
  routes: [
    { path: '/notenbuch', element: <BooksPage />, anyOf: ANY_OF, notRoles: NOT_ROLES, title: 'Notenbuch' },
    { path: '/notenbuch/klasse/:classId', element: <ClassPage />, anyOf: ['gradebook.read_class', 'gradebook.manage'], notRoles: NOT_ROLES, title: 'Noten der Klasse' },
    { path: '/notenbuch/verwaltung', element: <AdminPage />, anyOf: ADMIN_OF, notRoles: NOT_ROLES, title: 'Notenbuch verwalten' },
    { path: '/notenbuch/:bookId', element: <BookPage />, anyOf: VIEW_OF, notRoles: NOT_ROLES, title: 'Notenbuch' },
  ],
  nav: [{ path: '/notenbuch', label: 'Notenbuch', icon: 'exam', group: 'alltag', order: 17, anyOf: ANY_OF, notRoles: NOT_ROLES }],
});

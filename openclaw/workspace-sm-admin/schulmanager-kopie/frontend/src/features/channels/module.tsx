/**
 * Feature-Modul „Kursräume“ (ARCHITECTURE.md §9.4) für die Registry (`features/registry.ts`).
 *
 * * `/kursraeume` – eigene Kursräume (Kursteile, Klassen, eigene) mit Suche; Schulleitung/Admin alle (nur lesen).
 * * `/kursraeume/:id` – Material (Ordner, Dateien, Links, Textseiten, Freigabe zur Unterrichtsstunde), Aufgaben
 *   (Abgabe, Rückmeldung), Pinnwand, Teilnehmende. Eltern (`channels.view_children`): Kursräume der Kinder nur
 *   lesend (`?child=` wählt das Kind), volljährige Kinder nur mit Einwilligung.
 * * Startseite: Schüler/innen „Neues Material & fällige Aufgaben“, Lehrkräfte „Heute: Stunden & Material
 *   freigeben“ und „Abgaben zu bewerten“; Menü-Badge „neue Inhalte“.
 *
 * Eigene Umsetzung der Moodle-Konzepte – kein Moodle-Code. Importzyklus (siehe registry.ts): beim Laden nur
 * `defineFeature`/`getBadge` benutzen, Seiten und Kacheln per `lazy()`.
 */
import { lazy } from 'react';
import { defineFeature, getBadge } from '../registry';
import { ChannelsBadge, NEW_BADGE } from './badge';

const ChannelListPage = lazy(() => import('./ChannelListPage'));
const ChannelPage = lazy(() => import('./ChannelPage'));
const StudentWidget = lazy(() => import('./widgets').then((m) => ({ default: m.StudentWidget })));
const TeacherTodayWidget = lazy(() => import('./widgets').then((m) => ({ default: m.TeacherTodayWidget })));
const TeacherGradeWidget = lazy(() => import('./widgets').then((m) => ({ default: m.TeacherGradeWidget })));

export default defineFeature({
  id: 'kursraeume',
  routes: [
    { path: '/kursraeume', element: <ChannelListPage />, anyOf: ['channels.use', 'channels.manage', 'channels.view_children'], title: 'Kursräume' },
    { path: '/kursraeume/:id', element: <ChannelPage />, anyOf: ['channels.use', 'channels.manage', 'channels.view_children'], title: 'Kursraum' },
  ],
  nav: [
    {
      path: '/kursraeume',
      label: 'Kursräume',
      icon: 'folder',
      group: 'kommunikation',
      anyOf: ['channels.use', 'channels.manage', 'channels.view_children'],
      order: 20,
      badge: () => getBadge(NEW_BADGE),
      badgeLabel: (n) => `${n} neue Inhalte`,
    },
  ],
  widgets: [
    { id: 'neu', element: <StudentWidget />, order: -5, roles: ['schueler'] },
    { id: 'heute', element: <TeacherTodayWidget />, order: -5, roles: ['lehrer'] },
    { id: 'abgaben', element: <TeacherGradeWidget />, order: -4, roles: ['lehrer'] },
  ],
  background: ChannelsBadge,
});

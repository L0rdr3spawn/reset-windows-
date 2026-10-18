/**
 * Feature-Modul „Lehrer-Selbstverwaltung“ (ARCHITECTURE.md §9.3) für die Registry (`features/registry.ts`).
 *
 * * `/lehrkraft/profil` – Lehrkräfte pflegen Fächer, Wunschklassen, Deputat, Arbeitszeitfenster und Wünsche
 *   (Antrag bzw. sofort gültig, je nach `settings.teacher_self_service`).
 * * `/planung/antraege` – Planung/Schulleitung prüft Anträge (Vergleich, Konflikte, Genehmigen/Ablehnen) und
 *   plant den Stundenplan einer Lehrkraft neu.
 *
 * Wichtig (Importzyklus, siehe registry.ts): nur gehobene Funktionen der Registry beim Laden benutzen
 * (`defineFeature`, `getBadge`), Seiten werden erst bei Bedarf geladen.
 */
import { lazy } from 'react';
import { defineFeature, getBadge } from '../registry';
import { REQUESTS_BADGE, RequestsBadge } from './badge';

const TeacherProfilePage = lazy(() => import('./TeacherProfilePage'));
const TeacherRequestsPage = lazy(() => import('./TeacherRequestsPage'));
// Kacheln erst laden, wenn die Startseite sie zeigt (DashboardPage umschließt sie mit Suspense)
const ProfileWidget = lazy(() => import('./widgets').then((m) => ({ default: m.ProfileWidget })));
const RequestsWidget = lazy(() => import('./widgets').then((m) => ({ default: m.RequestsWidget })));

export default defineFeature({
  id: 'lehrkraft',
  routes: [
    { path: '/lehrkraft/profil', element: <TeacherProfilePage />, anyOf: ['profile.teacher_self'], title: 'Mein Profil als Lehrkraft' },
    { path: '/planung/antraege', element: <TeacherRequestsPage />, anyOf: ['teacher_requests.review'], title: 'Anträge von Lehrkräften' },
  ],
  nav: [
    { path: '/lehrkraft/profil', label: 'Profil als Lehrkraft', icon: 'clock', group: 'konto', anyOf: ['profile.teacher_self'], order: 5 },
    {
      path: '/planung/antraege',
      label: 'Anträge von Lehrkräften',
      icon: 'users',
      group: 'planung',
      anyOf: ['teacher_requests.review'],
      badge: () => getBadge(REQUESTS_BADGE),
      badgeLabel: (n) => `${n} offen`,
    },
  ],
  widgets: [
    { id: 'profil', element: <ProfileWidget />, order: 10, anyOf: ['profile.teacher_self'] },
    { id: 'antraege', element: <RequestsWidget />, order: 10, anyOf: ['teacher_requests.review'] },
  ],
  background: RequestsBadge,
});

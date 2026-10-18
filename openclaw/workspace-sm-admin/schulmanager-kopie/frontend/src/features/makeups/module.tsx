/**
 * Feature-Modul „Nachschreibtermine“ für die Registry (`features/registry.ts`).
 *
 * * `/nachschreiben` – Lehrkräfte (Klausur), Klassenleitung, Sekretariat, Leitung: verpasste Klausuren/Tests, Termin
 *   festlegen, Attest-Status.
 * * Startseiten-Kachel für Lehrkräfte und Familien (nur sichtbar, wenn etwas ansteht).
 */
import { lazy } from 'react';
import { defineFeature, getBadge } from '../registry';
import { MAKEUP_BADGE, MakeupBadge } from './badge';

const MakeupsPage = lazy(() => import('./MakeupsPage'));
const MakeupWidget = lazy(() => import('./MakeupWidget'));

export default defineFeature({
  id: 'nachschreiben',
  routes: [
    { path: '/nachschreiben', element: <MakeupsPage />, anyOf: ['exam.edit', 'student_absence.read'], notRoles: ['schueler', 'eltern', 'admin'], title: 'Nachschreibtermine' },
  ],
  nav: [
    {
      path: '/nachschreiben',
      label: 'Nachschreiben',
      icon: 'exam',
      group: 'alltag',
      anyOf: ['exam.edit', 'student_absence.read'],
      notRoles: ['schueler', 'eltern', 'admin'],
      badge: () => getBadge(MAKEUP_BADGE),
      badgeLabel: (n) => `${n} offen`,
    },
  ],
  widgets: [{ id: 'nachschreiben', element: <MakeupWidget />, order: -10, anyOf: ['exam.edit', 'student_absence.read'], notRoles: ['admin'] }],
  background: MakeupBadge,
});

/**
 * Feature-Modul „Schüler-Selbstbedienung“ (ARCHITECTURE.md §9.6) für die Registry (`features/registry.ts`).
 *
 * * „Meine Übersicht“ gibt es nicht mehr als Seite: Krank melden, Krankmeldungen, Atteste/Dokumente → Seite
 *   Krankmeldungen (`FamilyAbsences.tsx`), Wochenplan/Klausuren/Aufgaben/Nachrichten → Startseite (`FamilyHome.tsx`),
 *   Noten → `/noten`. Die alte Adresse `/meine-uebersicht` leitet auf die Startseite weiter (alte Lesezeichen).
 *   Die Kinderauswahl der Eltern ist überall dieselbe (`useChild.tsx`).
 * * `/dokumente` – Sekretariat, Schulleitung, Klassenleitungen: Prüf-Eingang, „Attest fehlt“, alle Dokumente.
 *   Im Menü nur für Sekretariat/Schulleitung; Klassenleitungen erreichen die Seite über ihre Startseiten-Kachel
 *   (Fachlehrkräfte haben keinen Zugriff auf Atteste – das Backend liefert ihnen nichts).
 *
 * Importzyklus (siehe registry.ts): beim Laden nur `defineFeature`/`getBadge`; Seiten und Kacheln per lazy().
 */
import { lazy } from 'react';
import { Navigate } from 'react-router-dom';
import { defineFeature, getBadge } from '../registry';
import { DOCS_BADGE, DocumentsBadge } from './badge';

const DocumentsPage = lazy(() => import('./DocumentsPage'));
const RecordPage = lazy(() => import('./RecordPage'));
const GradesPage = lazy(() => import('./GradesPage'));
const StaffWidget = lazy(() => import('./widgets').then((m) => ({ default: m.StaffWidget })));

export default defineFeature({
  id: 'schueler',
  routes: [
    // alte Adresse der aufgelösten Seite „Meine Übersicht“ (Lesezeichen)
    { path: '/meine-uebersicht', element: <Navigate to="/" replace />, title: 'Start' },
    { path: '/dokumente', element: <DocumentsPage />, anyOf: ['student_documents.read'], notRoles: ['schueler', 'eltern'], title: 'Atteste & Dokumente' },
    { path: '/fehlzeiten/:studentId', element: <RecordPage />, anyOf: ['student_absence.read'], title: 'Fehlzeiten' },
    { path: '/noten', element: <GradesPage />, roles: ['schueler', 'eltern'], title: 'Meine Noten' },
  ],
  nav: [
    {
      path: '/noten',
      label: 'Noten',
      icon: 'exam',
      group: 'alltag',
      roles: ['schueler', 'eltern'],
      order: 6,
    },
    {
      path: '/dokumente',
      label: 'Atteste & Dokumente',
      icon: 'medical',
      group: 'verwaltung',
      anyOf: ['student_documents.read'],
      notRoles: ['schueler', 'eltern', 'lehrer'],
      badge: () => getBadge(DOCS_BADGE),
      badgeLabel: (n) => `${n} zu bearbeiten`,
    },
  ],
  widgets: [
    { id: 'dokumente', element: <StaffWidget />, order: -5, anyOf: ['student_documents.read'], notRoles: ['schueler', 'eltern'] },
  ],
  background: DocumentsBadge,
});

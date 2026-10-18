/**
 * Feature-Modul „Formulare“ (Formular-Baukasten) für die Registry (`features/registry.ts`).
 *
 * * `/formulare` – ausfüllen (Eltern, Schüler, Lehrkräfte), Eingang (Klassenleitung, Sekretariat, Schulleitung),
 *   Vorlagen und Bibliothek (Verwaltung).
 * * `/formulare/vorlage/:id` – Baukasten (nur `forms.manage`).
 * * Startseiten-Kachel, wenn etwas wartet.
 */
import { lazy } from 'react';
import { defineFeature, getBadge } from '../registry';
import { FORMS_BADGE, FormsBadge } from './badge';

const FormsPage = lazy(() => import('./FormsPage'));
const TemplateEditor = lazy(() => import('./TemplateEditor'));
const FormsWidget = lazy(() => import('./FormsWidget'));

export default defineFeature({
  id: 'formulare',
  routes: [
    { path: '/formulare', element: <FormsPage />, anyOf: ['forms.submit', 'forms.inbox', 'forms.manage'], title: 'Formulare' },
    { path: '/formulare/vorlage/:id', element: <TemplateEditor />, anyOf: ['forms.manage'], title: 'Formular bearbeiten' },
  ],
  nav: [
    {
      path: '/formulare',
      label: 'Formulare',
      icon: 'list',
      group: 'alltag',
      anyOf: ['forms.submit', 'forms.inbox', 'forms.manage'],
      badge: () => getBadge(FORMS_BADGE),
      badgeLabel: (n) => `${n} offen`,
    },
  ],
  widgets: [{ id: 'formulare', element: <FormsWidget />, order: -5, anyOf: ['forms.submit', 'forms.inbox'] }],
  background: FormsBadge,
});

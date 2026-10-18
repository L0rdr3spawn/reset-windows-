/**
 * Feature-Modul „Benachrichtigungen“ (docs/BENACHRICHTIGUNGEN.md): Seite mit Liste und Einstellungen (`/benachrichtigungen`).
 * Die Glocke selbst sitzt in der Kopfleiste (`components/Layout.tsx` → `NotificationBell`). Kein Push, keine App-Installation.
 */
import { lazy } from 'react';
import { defineFeature } from '../registry';

const NotificationsPage = lazy(() => import('./NotificationsPage'));

export default defineFeature({
  id: 'benachrichtigungen',
  routes: [{ path: '/benachrichtigungen', element: <NotificationsPage />, title: 'Benachrichtigungen' }],
  nav: [{ path: '/benachrichtigungen', label: 'Benachrichtigungen', icon: 'bell', group: 'konto', order: 4 }],
});

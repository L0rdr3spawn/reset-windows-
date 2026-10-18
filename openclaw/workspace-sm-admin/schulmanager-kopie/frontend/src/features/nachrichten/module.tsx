/**
 * Feature-Modul „Nachrichten“ (ARCHITECTURE.md §9.5): EINE Oberfläche für Einzelchats, Gruppen, Briefe/Rundschreiben,
 * E-Mails verknüpfter Konten und Mitteilungen. Die Backends bleiben getrennt (`routes/features_chats.py` Ende-zu-Ende,
 * `routes/features_messages.py` Briefe/E-Mail); die Oberfläche führt ihre Listen zusammen.
 *
 * * `/nachrichten` bzw. `/nachrichten/c/:id`, `/nachrichten/b/:id`, `/nachrichten/mitteilungen` – Liste und Geöffnetes
 * * `/nachrichten/neu` – Brief oder E-Mail verfassen; `/nachrichten/einstellungen`; `/nachrichten/moderation` (+ `/chats`)
 * * Alte Adressen `/postfach…` und `/chats…` leiten weiter (`legacy.ts`); `/mitteilungen` in `AnnouncementsPage`.
 *
 * Importzyklus (siehe registry.ts): beim Laden nur `defineFeature`/`getBadge` benutzen, Seiten per `lazy()`.
 */
import { lazy } from 'react';
import { defineFeature, getBadge } from '../registry';
import { NachrichtenBadge, REPORTS_BADGE, UNREAD_BADGE } from './badge';

const NachrichtenPage = lazy(() => import('./NachrichtenPage'));
const ComposePage = lazy(() => import('../messages/ComposePage'));
const SettingsPage = lazy(() => import('../messages/SettingsPage'));
const ModerationPage = lazy(() => import('../messages/ModerationPage'));
const ChatModerationPage = lazy(() => import('../chats/ModerationPage'));
const PrivacyPage = lazy(() => import('../chats/PrivacyPage'));
const LegacyRedirect = lazy(() => import('./LegacyRedirect'));
const InboxWidget = lazy(() => import('../messages/widgets').then((m) => ({ default: m.InboxWidget })));

const USE = ['messages.use'] as const;

export default defineFeature({
  id: 'nachrichten',
  routes: [
    { path: '/nachrichten/neu', element: <ComposePage />, anyOf: [...USE], title: 'Neuer Brief' },
    { path: '/nachrichten/einstellungen', element: <SettingsPage />, anyOf: [...USE], title: 'Nachrichten-Einstellungen' },
    { path: '/nachrichten/moderation/chats', element: <ChatModerationPage />, anyOf: ['messages.moderate'], title: 'Chat-Meldungen' },
    { path: '/nachrichten/moderation', element: <ModerationPage />, anyOf: ['messages.moderate'], title: 'Nachrichten-Moderation' },
    // eine Route für Liste und Geöffnetes – die Seite bleibt beim Wechsel erhalten
    { path: '/nachrichten/:kind?/:id?', element: <NachrichtenPage />, anyOf: [...USE], title: 'Nachrichten' },
    { path: '/datenschutz', element: <PrivacyPage />, title: 'Datenschutz' },
    // alte Adressen
    { path: '/postfach/:a?/:b?', element: <LegacyRedirect />, anyOf: [...USE], title: 'Nachrichten' },
    { path: '/chats/:a?/:b?', element: <LegacyRedirect />, anyOf: [...USE], title: 'Nachrichten' },
  ],
  nav: [
    {
      path: '/nachrichten',
      label: 'Nachrichten',
      icon: 'mail',
      group: 'kommunikation',
      anyOf: [...USE],
      order: 5,
      badge: () => getBadge(UNREAD_BADGE),
      badgeLabel: (n) => (n === 1 ? '1 ungelesene Unterhaltung' : `${n} ungelesene Unterhaltungen`),
    },
    {
      path: '/nachrichten/moderation',
      label: 'Nachrichten-Moderation',
      icon: 'shield',
      group: 'verwaltung',
      anyOf: ['messages.moderate'],
      order: 1000,
      badge: () => getBadge(REPORTS_BADGE),
      badgeLabel: (n) => (n === 1 ? '1 offene Meldung' : `${n} offene Meldungen`),
    },
    { path: '/nachrichten/moderation/chats', label: 'Chat-Meldungen', icon: 'shield', group: 'verwaltung', anyOf: ['messages.moderate'], order: 1001 },
    { path: '/datenschutz', label: 'Datenschutz', icon: 'shield', group: 'konto', order: 900 },
  ],
  widgets: [{ id: 'neu', element: <InboxWidget />, order: -10, anyOf: [...USE] }],
  background: NachrichtenBadge,
});

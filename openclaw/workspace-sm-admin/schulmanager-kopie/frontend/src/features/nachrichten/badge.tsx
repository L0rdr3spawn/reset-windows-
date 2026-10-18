/**
 * Unsichtbare Hintergrund-Komponente: EINE Zahl für alles am Menüeintrag „Nachrichten“ (Chats/Gruppen und Briefe/E-Mails
 * mit ungelesenen Nachrichten) und – für die Moderation – offene Meldungen. Aktualisiert sich live (Ereignisse ohne
 * Inhalt, Scope `chats`, `messages` bzw. `message_reports`).
 */
import { useEffect } from 'react';
import { useUser } from '../../context/AuthContext';
import { useApi } from '../../hooks/useApi';
import { can } from '../../lib/permissions';
import { chatsApi } from '../chats/api';
import { messagesApi } from '../messages/api';
import { badgeCount } from '../messages/logic';
import { setBadge } from '../registry';
import { totalUnread } from './inbox';

export const UNREAD_BADGE = 'nachrichten.unread';
export const REPORTS_BADGE = 'nachrichten.meldungen';

export function NachrichtenBadge() {
  const user = useUser();
  const enabled = can(user, 'messages.use');
  const moderator = can(user, 'messages.moderate');
  const mail = useApi((signal) => messagesApi.unread(signal), [user.id], { enabled, live: ['messages'] });
  const chats = useApi((signal) => chatsApi.unread(signal), [user.id], { enabled, live: ['chats'] });
  const reports = useApi((signal) => messagesApi.reports('offen', signal, 1), [user.id], { enabled: moderator, live: ['message_reports'] });
  useEffect(() => setBadge(UNREAD_BADGE, enabled ? totalUnread(chats.data?.unread, badgeCount(mail.data)) : 0), [enabled, mail.data, chats.data]);
  useEffect(() => setBadge(REPORTS_BADGE, moderator ? (reports.data?.counts.offen ?? 0) : 0), [moderator, reports.data]);
  useEffect(
    () => () => {
      setBadge(UNREAD_BADGE, 0);
      setBadge(REPORTS_BADGE, 0);
    },
    [],
  );
  return null;
}

/**
 * Reine Logik der gemeinsamen Liste „Nachrichten“ (ohne React, mit vitest getestet): Chats, Gruppen, Briefe,
 * E-Mails und Mitteilungen werden zu einer Liste zusammengeführt, gefiltert, gesucht und nach der letzten Aktivität
 * sortiert. Die beiden Backends (Chats Ende-zu-Ende, Briefe/E-Mail) bleiben getrennt; hier werden nur ihre Listen vereint.
 */
import type { Announcement } from '../../api/types';
import type { ChatListItem } from '../chats/api';
import { chatPath, conversationPath, listHeadline, previewLine, type InboxFilter } from '../messages/logic';
import type { GlyphName } from '../messages/components';
import type { ConversationSummary } from '../messages/types';

export type ItemType = 'chat' | 'gruppe' | 'brief' | 'email' | 'mitteilung';

export interface InboxItem {
  /** eindeutig über alle Arten, z. B. `c:12` (Chat), `b:5` (Brief/E-Mail), `a:3` (Mitteilung) */
  key: string;
  type: ItemType;
  /** Pfad ohne Filter */
  path: string;
  title: string;
  /** Betreff bzw. zweite Zeile */
  subtitle: string;
  preview: string;
  /** ISO-Zeitstempel der letzten Aktivität */
  at: string;
  unread: number;
  muted: boolean;
  archived: boolean;
  attachment: boolean;
  /** für den Profilkreis */
  avatar: { name: string; role?: string | null; glyph?: GlyphName };
  /** Beschriftung der Art ("Gruppe", "Rundschreiben", …) – leer bei Einzelchats */
  tag: string;
}

/** Zeitstempel ohne Zeitzone gelten als UTC (so liefert es das Chat-Backend). */
export function timeValue(iso: string | null | undefined): number {
  if (!iso) return 0;
  const withZone = /[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`;
  const t = new Date(withZone).getTime();
  return Number.isNaN(t) ? 0 : t;
}

export function fromChat(c: ChatListItem): InboxItem {
  const group = c.kind === 'group';
  let preview = group ? `${c.members} Mitglieder` : '';
  if (c.last) {
    if (c.last.system_text && !c.last.sender_name) preview = c.last.system_text;
    else if (c.last.deleted) preview = 'Nachricht gelöscht';
    else preview = `${c.last.mine ? 'Sie' : c.last.sender_name}: 🔒 Nachricht`;
  }
  return {
    key: `c:${c.id}`,
    type: group ? 'gruppe' : 'chat',
    path: chatPath(c.id),
    title: c.title,
    subtitle: '',
    preview,
    at: c.last?.created_at ?? c.last_activity_at,
    unread: c.unread,
    muted: c.muted,
    archived: c.archived,
    attachment: false,
    avatar: { name: c.title, glyph: group ? 'people' : undefined },
    tag: group ? 'Gruppe' : '',
  };
}

export function fromConversation(c: ConversationSummary): InboxItem {
  const other = c.kind === 'direct' ? c.participants[0] : undefined;
  const email = c.kind === 'email';
  return {
    key: `b:${c.id}`,
    type: email ? 'email' : 'brief',
    path: conversationPath(c.id),
    title: listHeadline(c),
    subtitle: c.subject,
    preview: c.match?.in === 'message' ? c.match.snippet : previewLine(c),
    at: c.last_message_at,
    unread: c.unread,
    muted: c.muted,
    archived: c.archived,
    attachment: (c.last_message?.attachments ?? 0) > 0,
    avatar: { name: other?.name ?? c.title, role: other?.role, glyph: c.kind === 'broadcast' ? 'megaphone' : email ? 'mail' : undefined },
    tag: email ? 'E-Mail' : c.kind === 'broadcast' ? 'Rundschreiben' : c.kind === 'group' ? 'Brief an mehrere' : 'Brief',
  };
}

export function fromAnnouncement(a: Announcement): InboxItem {
  return {
    key: `a:${a.id}`,
    type: 'mitteilung',
    path: '/nachrichten/mitteilungen',
    title: a.title,
    subtitle: a.priority === 'wichtig' ? 'Wichtig' : '',
    preview: (a.body ?? '').replace(/\s+/g, ' ').trim().slice(0, 140),
    at: a.created_at ?? a.valid_from ?? '',
    unread: 0,
    muted: false,
    archived: false,
    attachment: false,
    avatar: { name: a.title, glyph: 'megaphone' },
    tag: 'Mitteilung',
  };
}

/** Neueste Aktivität zuerst; bei gleicher Zeit stabil nach Schlüssel. */
export function sortItems(items: readonly InboxItem[]): InboxItem[] {
  return [...items].sort((a, b) => timeValue(b.at) - timeValue(a.at) || (a.key < b.key ? -1 : 1));
}

/** Gehört der Eintrag zum Filter? „Alle“ zeigt alles außer Archiviertem; „Archiv“ nur Archiviertes. */
export function matchesFilter(item: InboxItem, filter: InboxFilter): boolean {
  if (filter === 'archiv') return item.archived;
  if (filter === 'entwuerfe') return false;
  if (item.archived) return false;
  switch (filter) {
    case 'chats':
      return item.type === 'chat';
    case 'gruppen':
      return item.type === 'gruppe';
    case 'briefe':
      return item.type === 'brief';
    case 'email':
      return item.type === 'email';
    case 'mitteilungen':
      return item.type === 'mitteilung';
    default:
      return true;
  }
}

/** Suche in Titel, Betreff und (bei Briefen) Vorschau; Chats sind Ende-zu-Ende-verschlüsselt, dort zählt nur der Name. */
export function matchesQuery(item: InboxItem, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  const hay = [item.title, item.subtitle, item.type === 'chat' || item.type === 'gruppe' ? '' : item.preview].join(' ').toLowerCase();
  return q.split(/\s+/).every((word) => hay.includes(word));
}

/** Liste für die Anzeige: filtern, suchen, sortieren. Briefe aus der Serversuche gelten als Treffer. */
export function buildList(items: readonly InboxItem[], filter: InboxFilter, query: string): InboxItem[] {
  return sortItems(items.filter((i) => matchesFilter(i, filter) && (i.type === 'brief' || i.type === 'email' ? true : matchesQuery(i, query))));
}

/** Ungelesen-Zähler EINER für alles: Chats/Gruppen und Briefe/E-Mails mit ungelesenen Nachrichten. */
export function totalUnread(chats: number | null | undefined, mail: number | null | undefined): number {
  return Math.max(0, chats ?? 0) + Math.max(0, mail ?? 0);
}

/** Ungelesene Chats (ohne stumme und archivierte), optional nur eine Art. */
export function unreadChats(chats: readonly ChatListItem[], kind?: 'direct' | 'group'): number {
  return chats.filter((c) => !c.archived && !c.muted && c.unread > 0 && (!kind || c.kind === kind)).length;
}

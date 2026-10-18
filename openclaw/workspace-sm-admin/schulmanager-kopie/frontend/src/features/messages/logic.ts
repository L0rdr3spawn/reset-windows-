/**
 * Reine Hilfsfunktionen der Briefe und E-Mails (ohne React/DOM, mit vitest getestet): Ordner, Zeitangaben, Empfänger,
 * Art der Unterhaltung, Prüfungen beim Verfassen, Texte für Listen und Kopfzeilen.
 */
import type {
  ConversationKind,
  ConversationSummary,
  GroupOption,
  Person,
  Recipient,
  RecipientInput,
  RecipientRole,
  ReplyMode,
  UnreadCounts,
} from './types';

// ------------------------------------------------------------------ Filter und Adressen

/** Filter-Chips der Seite „Nachrichten“. `entwuerfe` erscheint nur, solange es Entwürfe gibt. */
export type InboxFilter = 'alle' | 'chats' | 'gruppen' | 'briefe' | 'email' | 'mitteilungen' | 'archiv' | 'entwuerfe';

export const INBOX_FILTERS: { key: InboxFilter; label: string; param: string }[] = [
  { key: 'alle', label: 'Alle', param: '' },
  { key: 'chats', label: 'Chats', param: 'chats' },
  { key: 'gruppen', label: 'Gruppen', param: 'gruppen' },
  { key: 'briefe', label: 'Briefe', param: 'briefe' },
  { key: 'email', label: 'E-Mail', param: 'email' },
  { key: 'mitteilungen', label: 'Mitteilungen', param: 'mitteilungen' },
  { key: 'archiv', label: 'Archiv', param: 'archiv' },
  { key: 'entwuerfe', label: 'Entwürfe', param: 'entwuerfe' },
];

/** `?f=` → Filter (unbekannt/leer → alle). */
export function filterFromParam(param: string | null | undefined): InboxFilter {
  const p = (param ?? '').trim().toLowerCase();
  return INBOX_FILTERS.find((f) => f.param && f.param === p)?.key ?? 'alle';
}

export function filterQuery(filter: InboxFilter): string {
  const p = INBOX_FILTERS.find((f) => f.key === filter)?.param ?? '';
  return p ? `?f=${p}` : '';
}

/** Adresse eines Briefs bzw. einer E-Mail (Filter bleibt erhalten). */
export function conversationPath(id: number, filter: InboxFilter = 'alle'): string {
  return `/nachrichten/b/${id}${filterQuery(filter)}`;
}

/** Adresse eines Chats bzw. einer Gruppe. */
export function chatPath(id: number, filter: InboxFilter = 'alle'): string {
  return `/nachrichten/c/${id}${filterQuery(filter)}`;
}

/** Die Liste mit einem Filter. */
export function folderPath(filter: InboxFilter = 'alle'): string {
  return `/nachrichten${filterQuery(filter)}`;
}

// ------------------------------------------------------------------ Zeitangaben

const pad = (n: number) => String(n).padStart(2, '0');
const WEEKDAYS_SHORT = ['So.', 'Mo.', 'Di.', 'Mi.', 'Do.', 'Fr.', 'Sa.'];
const WEEKDAYS_LONG = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag'];
const MONTHS = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];

function parse(ts: string | null | undefined): Date | null {
  if (!ts) return null;
  const d = new Date(ts);
  return Number.isNaN(d.getTime()) ? null : d;
}

function startOfDay(d: Date): number {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

/** Abstand in Kalendertagen (lokal): 0 = heute, 1 = gestern. */
export function daysAgo(ts: string, now: Date = new Date()): number {
  const d = parse(ts);
  if (!d) return Number.NaN;
  return Math.round((startOfDay(now) - startOfDay(d)) / 86_400_000);
}

/** Lokaler Tag „JJJJ-MM-TT“ eines Zeitstempels. */
export function dayKey(ts: string): string {
  const d = parse(ts);
  return d ? `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` : '';
}

/** Uhrzeit „14:05“. */
export function clock(ts: string): string {
  const d = parse(ts);
  return d ? `${pad(d.getHours())}:${pad(d.getMinutes())}` : '';
}

/** Zeit in Listen: heute „14:05“, gestern „Gestern“, letzte Woche „Mo.“, dieses Jahr „05.10.“, sonst „05.10.2025“. */
export function listTime(ts: string, now: Date = new Date()): string {
  const d = parse(ts);
  if (!d) return '';
  const ago = daysAgo(ts, now);
  if (ago <= 0) return clock(ts);
  if (ago === 1) return 'Gestern';
  if (ago < 7) return WEEKDAYS_SHORT[d.getDay()] ?? '';
  if (d.getFullYear() === now.getFullYear()) return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.`;
  return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()}`;
}

/** Tagesüberschrift im Verlauf: „Heute“, „Gestern“, „Montag, 5. Oktober“ (+ Jahr, wenn nicht das aktuelle). */
export function dayLabel(ts: string, now: Date = new Date()): string {
  const d = parse(ts);
  if (!d) return '';
  const ago = daysAgo(ts, now);
  if (ago === 0) return 'Heute';
  if (ago === 1) return 'Gestern';
  const base = `${WEEKDAYS_LONG[d.getDay()]}, ${d.getDate()}. ${MONTHS[d.getMonth()]}`;
  return d.getFullYear() === now.getFullYear() ? base : `${base} ${d.getFullYear()}`;
}

/** Vollständig für `title`/Bildschirmleser: „Mo., 05.10.2026, 14:05 Uhr“. */
export function fullTime(ts: string | null | undefined): string {
  const d = parse(ts);
  if (!d) return '';
  return `${WEEKDAYS_SHORT[d.getDay()]} ${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()}, ${clock(ts as string)} Uhr`;
}

/** Elemente (aufsteigend sortiert) nach lokalem Tag gruppieren. */
export function groupByDay<T extends { created_at: string }>(items: readonly T[], now: Date = new Date()): { key: string; label: string; items: T[] }[] {
  const out: { key: string; label: string; items: T[] }[] = [];
  for (const item of items) {
    const key = dayKey(item.created_at);
    const last = out[out.length - 1];
    if (last && last.key === key) last.items.push(item);
    else out.push({ key, label: dayLabel(item.created_at, now), items: [item] });
  }
  return out;
}

// ------------------------------------------------------------------ Empfänger

export function recipientKey(r: Recipient | RecipientInput): string {
  if (r.type === 'user') return `user:${r.id}`;
  if (r.type === 'email') return `email:${r.email.toLowerCase()}`;
  return `group:${r.kind}:${r.ref}`;
}

export function toInput(r: Recipient, role: RecipientRole = 'to'): RecipientInput {
  if (r.type === 'user') return { type: 'user', id: Number(r.id), role };
  if (r.type === 'email') return { type: 'email', email: r.email, name: r.name ?? '', role };
  return { type: 'group', kind: r.kind, ref: r.ref, role };
}

const EMAIL_RE = /^[^@\s<>"',;]+@[^@\s<>"',;]+\.[^@\s<>"',;]{2,}$/;

/** Sieht wie eine E-Mail-Adresse aus? */
export function isEmail(text: string): boolean {
  return EMAIL_RE.test(text.trim());
}

/** Anzeigename eines Empfängers (Chip). */
export function recipientLabel(r: Recipient): string {
  if (r.type === 'user') return r.name;
  if (r.type === 'email') return r.name ? `${r.name} <${r.email}>` : r.email;
  return r.label;
}

/** Empfänger hinzufügen (ohne Doppelte, gelöschte Konten nie). */
export function addRecipient(list: readonly Recipient[], r: Recipient): Recipient[] {
  if (r.type === 'user' && r.id === null) return [...list];
  const key = recipientKey(r);
  return list.some((x) => recipientKey(x) === key) ? [...list] : [...list, r];
}

export function removeRecipient(list: readonly Recipient[], key: string): Recipient[] {
  return list.filter((x) => recipientKey(x) !== key);
}

export function isGroup(r: Recipient | RecipientInput): r is GroupOption | Extract<RecipientInput, { type: 'group' }> {
  return r.type === 'group';
}

/** Welche Art von Unterhaltung entsteht (wie das Backend entscheidet)? `null` = noch keine Empfänger. */
export function predictKind(recipients: readonly (Recipient | RecipientInput)[], canBroadcast: boolean, allowReplies: ReplyMode): ConversationKind | null {
  const users = recipients.filter((r) => r.type === 'user').length;
  const emails = recipients.filter((r) => r.type === 'email').length;
  const groups = recipients.length - users - emails;
  if (!recipients.length) return null;
  const allow = canBroadcast ? allowReplies : 'all';
  if (groups > 0 || (allow !== 'all' && users > 1)) return 'broadcast';
  if (!users && emails) return 'email';
  return users === 1 && !emails ? 'direct' : 'group';
}

/** Obergrenze der Empfangenden (Gruppen können sich überschneiden). */
export function estimatedRecipients(recipients: readonly Recipient[]): number {
  return recipients.reduce((n, r) => n + (r.type === 'group' ? (r.count ?? 0) : 1), 0);
}

export function plural(n: number, one: string, many: string): string {
  return `${n} ${n === 1 ? one : many}`;
}

/** Erklärung unter dem Empfängerfeld. */
export function kindDescription(kind: ConversationKind | null, recipients: readonly Recipient[]): string {
  if (!kind) return '';
  if (kind === 'direct') {
    const p = recipients.find((r) => r.type === 'user');
    return p ? `Einzelnachricht an ${p.type === 'user' ? p.name : ''}.` : 'Einzelnachricht.';
  }
  if (kind === 'email') {
    return 'E-Mail an Adressen außerhalb der Schule – sie geht über Ihr verbundenes E-Mail-Konto hinaus, Antworten erscheinen hier bei den Nachrichten.';
  }
  if (kind === 'group') {
    return `Nachricht an ${plural(recipients.length, 'Person', 'Personen')} – alle sehen alle Empfänger/innen, Antworten gehen an alle. Für lockeren Austausch ohne Betreff: einen Chat oder eine Gruppe starten.`;
  }
  const n = estimatedRecipients(recipients);
  const groups = recipients.filter((r) => r.type === 'group').length;
  const parts = [groups ? plural(groups, 'Gruppe', 'Gruppen') : '', recipients.length - groups ? plural(recipients.length - groups, 'Einzelperson', 'Einzelpersonen') : '']
    .filter(Boolean)
    .join(' und ');
  return `Rundschreiben an ${parts}${n ? ` (bis zu ${plural(n, 'Person', 'Personen')})` : ''} – Empfangende sehen nur die Zielgruppe, nicht die anderen Empfänger/innen.`;
}

export const REPLY_MODE_OPTIONS: { value: ReplyMode; label: string; hint: string }[] = [
  { value: 'all', label: 'An alle', hint: 'Antworten sehen alle Empfangenden.' },
  { value: 'sender', label: 'Nur an mich', hint: 'Jede Antwort wird eine private Unterhaltung mit Ihnen.' },
  { value: 'none', label: 'Keine', hint: 'Empfangende können nicht antworten.' },
];

export interface ComposeLimits {
  subject: number;
  body: number;
  attachments: number;
  individuals: number;
  groups: number;
}

export const DEFAULT_LIMITS: ComposeLimits = { subject: 200, body: 20_000, attachments: 10, individuals: 25, groups: 30 };

/** Hinderungsgründe beim Senden (leer = alles in Ordnung). */
export function composeProblems(input: {
  recipients: readonly Recipient[];
  subject: string;
  body: string;
  attachments: number;
  kind: ConversationKind | null;
  limits?: ComposeLimits;
}): string[] {
  const limits = input.limits ?? DEFAULT_LIMITS;
  const out: string[] = [];
  const users = input.recipients.filter((r) => r.type !== 'group').length;
  const groups = input.recipients.length - users;
  if (!input.recipients.length) out.push('Bitte mindestens eine Empfängerin oder einen Empfänger auswählen.');
  if (users > limits.individuals) out.push(`Höchstens ${limits.individuals} einzelne Empfänger/innen je Nachricht.`);
  if (groups > limits.groups) out.push(`Höchstens ${limits.groups} Gruppen je Rundschreiben.`);
  if (input.kind === 'broadcast' && !input.subject.trim()) out.push('Bitte einen Betreff für das Rundschreiben angeben.');
  else if (input.kind && input.kind !== 'email' && !input.subject.trim()) out.push('Bitte einen Betreff angeben – kurze Unterhaltungen ohne Betreff gehören in einen Chat oder eine Gruppe.');
  if (input.subject.trim().length > limits.subject) out.push(`Der Betreff ist zu lang (höchstens ${limits.subject} Zeichen).`);
  if (!input.body.trim() && input.attachments === 0) out.push('Bitte einen Nachrichtentext eingeben oder eine Datei anhängen.');
  if (input.body.length > limits.body) out.push(`Die Nachricht ist zu lang (höchstens ${limits.body} Zeichen).`);
  if (input.attachments > limits.attachments) out.push(`Höchstens ${limits.attachments} Anhänge je Nachricht.`);
  return out;
}

// ------------------------------------------------------------------ Darstellung

/** „LL“ für „Lena Lindner“, „S“ für „Sekretariat“. */
export function initials(name: string): string {
  const words = name.replace(/[()]/g, ' ').split(/\s+/).filter((w) => /\p{L}/u.test(w));
  if (!words.length) return '?';
  const first = words[0]?.match(/\p{L}/u)?.[0] ?? '';
  const last = words.length > 1 ? (words[words.length - 1]?.match(/\p{L}/u)?.[0] ?? '') : '';
  return (first + last).toUpperCase();
}

/** „Rolle · Klasse 5a“ */
export function personDetail(p: Pick<Person, 'role_label' | 'info'>): string {
  return [p.role_label, p.info].filter(Boolean).join(' · ');
}

/** Wer steht in der Liste oben? Rundschreiben: absendende Person bzw. „An: Zielgruppen“; sonst die anderen. */
export function listHeadline(conv: ConversationSummary, max = 3): string {
  if (conv.kind === 'broadcast') {
    if (conv.is_creator) return `An: ${audienceText(conv) || 'Rundschreiben'}`;
    return conv.creator.name;
  }
  return participantsText([...conv.participants, ...(conv.external ?? [])], max) || 'Nur Sie';
}

export function audienceText(conv: Pick<ConversationSummary, 'audience'>): string {
  return conv.audience.map((a) => a.label).filter(Boolean).join(', ');
}

export function participantsText(people: readonly Pick<Person, 'name' | 'me'>[], max = 3): string {
  const names = people.filter((p) => !p.me).map((p) => p.name);
  if (names.length <= max) return names.join(', ');
  return `${names.slice(0, max).join(', ')} und ${names.length - max} weitere`;
}

/** Vorschauzeile: „Sie: …“ bzw. bei mehreren Personen „Name: …“. */
export function previewLine(conv: ConversationSummary): string {
  const lm = conv.last_message;
  if (!lm) return '';
  if (lm.removed || !lm.integrity_ok) return lm.preview;
  if (lm.own) return `Sie: ${lm.preview}`;
  if (conv.kind !== 'direct' && lm.sender_name) return `${lm.sender_name}: ${lm.preview}`;
  return lm.preview;
}

/** Überschrift der Unterhaltung: Betreff, sonst Gesprächspartner/Zielgruppe. */
export function threadTitle(conv: ConversationSummary): string {
  if (conv.subject) return conv.subject;
  if (conv.kind === 'broadcast') return audienceText(conv) || 'Rundschreiben';
  return participantsText(conv.participants, 4) || conv.title || '(ohne Betreff)';
}

export function unreadText(n: number): string {
  return n === 1 ? '1 ungelesene Nachricht' : `${n} ungelesene Nachrichten`;
}

/** Zahl am Menüeintrag: Unterhaltungen mit Ungelesenem (ohne stumme/archivierte). */
export function badgeCount(counts: UnreadCounts | null | undefined): number {
  return Math.max(0, counts?.unread ?? 0);
}

/** Konto gesperrt bis … (Moderation) */
export function suspendedText(until: string | null | undefined): string {
  return until ? `Das Senden von Briefen ist für Sie bis ${fullTime(until)} gesperrt. Lesen ist weiterhin möglich.` : '';
}

const ACTION_LABELS: Record<string, string> = { removed: 'Nachricht ausgeblendet', suspended: 'Senden gesperrt' };

export function actionsText(actions: readonly string[]): string {
  return actions.map((a) => ACTION_LABELS[a] ?? a).join(', ');
}

/** Text der Aufbewahrungsfrist. */
export function retentionText(days: number): string {
  if (!days) return 'Nachrichten werden nicht automatisch gelöscht.';
  if (days % 365 === 0) {
    const years = days / 365;
    return `Nachrichten werden nach ${years === 1 ? 'einem Jahr' : `${years} Jahren`} automatisch gelöscht (gemeldete erst nach der Prüfung).`;
  }
  return `Nachrichten werden nach ${days} Tagen automatisch gelöscht (gemeldete erst nach der Prüfung).`;
}

/** Wurde der Verlauf ans Ende gescrollt? (Toleranz in Pixeln) */
export function nearBottom(scrollTop: number, clientHeight: number, scrollHeight: number, tolerance = 80): boolean {
  return scrollHeight - (scrollTop + clientHeight) <= tolerance;
}

/** Zusammenführen beim Nachladen älterer Nachrichten (ohne Doppelte, aufsteigend nach ID). */
export function mergeMessages<T extends { id: number }>(older: readonly T[], current: readonly T[]): T[] {
  const byId = new Map<number, T>();
  for (const m of older) byId.set(m.id, m);
  for (const m of current) byId.set(m.id, m);
  return [...byId.values()].sort((a, b) => a.id - b.id);
}

// ------------------------------------------------------------------ Links im Nachrichtentext

export type TextSegment = { type: 'text'; value: string } | { type: 'link'; value: string; href: string };

const URL_RE = /\b(https?:\/\/[^\s<>"']+|www\.[^\s<>"']+)/giu;
const TRAILING = /[.,;:!?)\]}»“"']+$/u;

/** Zerlegt Klartext in Text und Links (nur http/https; React maskiert alles andere). */
export function linkify(text: string): TextSegment[] {
  const out: TextSegment[] = [];
  let last = 0;
  for (const match of text.matchAll(URL_RE)) {
    const start = match.index ?? 0;
    let raw = match[0];
    const trail = raw.match(TRAILING)?.[0] ?? '';
    if (trail) raw = raw.slice(0, raw.length - trail.length);
    if (!raw) continue;
    const href = raw.toLowerCase().startsWith('www.') ? `https://${raw}` : raw;
    try {
      const url = new URL(href);
      if (url.protocol !== 'http:' && url.protocol !== 'https:') continue;
    } catch {
      continue;
    }
    if (start > last) out.push({ type: 'text', value: text.slice(last, start) });
    out.push({ type: 'link', value: raw, href });
    last = start + raw.length;
  }
  if (last < text.length) out.push({ type: 'text', value: text.slice(last) });
  return out;
}

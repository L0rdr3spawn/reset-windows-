import { describe, expect, it } from 'vitest';
import {
  addRecipient,
  badgeCount,
  composeProblems,
  conversationPath,
  dayLabel,
  filterFromParam,
  chatPath,
  folderPath,
  groupByDay,
  initials,
  kindDescription,
  linkify,
  listHeadline,
  listTime,
  mergeMessages,
  nearBottom,
  participantsText,
  predictKind,
  previewLine,
  recipientKey,
  removeRecipient,
  retentionText,
  threadTitle,
  toInput,
  isEmail,
} from './logic';
import type { ConversationSummary, GroupOption, Person } from './types';

const person = (id: number, name: string, extra: Partial<Person> = {}): Person => ({
  type: 'user',
  id,
  name,
  role: 'lehrer',
  role_label: 'Lehrkraft',
  info: '',
  ...extra,
});
const group = (kind: string, ref: string, label: string, count = 20): GroupOption => ({
  type: 'group',
  kind,
  ref,
  key: `${kind}:${ref}`,
  label,
  category: 'klasse',
  category_label: 'Klasse',
  count,
});

function conv(over: Partial<ConversationSummary> = {}): ConversationSummary {
  return {
    id: 1,
    kind: 'direct',
    kind_label: 'Direkt',
    subject: '',
    integrity_ok: true,
    title: '',
    allow_replies: 'all',
    created_at: '2026-10-07T08:00:00Z',
    last_message_at: '2026-10-07T08:00:00Z',
    last_message: null,
    unread: 0,
    archived: false,
    muted: false,
    is_creator: false,
    creator: person(2, 'Lena Lindner'),
    participants: [person(2, 'Lena Lindner')],
    participant_count: 2,
    audience: [],
    recipient_count: 1,
    parent_id: null,
    ...over,
  };
}

describe('Filter und Adressen', () => {
  it('liest den Filter aus ?f= und baut Pfade', () => {
    expect(filterFromParam(null)).toBe('alle');
    expect(filterFromParam('gruppen')).toBe('gruppen');
    expect(filterFromParam('ARCHIV')).toBe('archiv');
    expect(filterFromParam('entwuerfe')).toBe('entwuerfe');
    expect(filterFromParam('unsinn')).toBe('alle');
    expect(folderPath('alle')).toBe('/nachrichten');
    expect(folderPath('briefe')).toBe('/nachrichten?f=briefe');
    expect(conversationPath(7)).toBe('/nachrichten/b/7');
    expect(conversationPath(7, 'archiv')).toBe('/nachrichten/b/7?f=archiv');
    expect(chatPath(3, 'chats')).toBe('/nachrichten/c/3?f=chats');
  });
});

describe('Zeitangaben', () => {
  const now = new Date(2026, 9, 7, 15, 0); // Mittwoch, 7. Oktober 2026
  const at = (y: number, m: number, d: number, h = 9, min = 5) => new Date(y, m, d, h, min).toISOString();

  it('kurz in Listen', () => {
    expect(listTime(at(2026, 9, 7, 9, 5), now)).toBe('09:05');
    expect(listTime(at(2026, 9, 6), now)).toBe('Gestern');
    expect(listTime(at(2026, 9, 5), now)).toBe('Mo.');
    expect(listTime(at(2026, 8, 1), now)).toBe('01.09.');
    expect(listTime(at(2025, 11, 24), now)).toBe('24.12.2025');
    expect(listTime('kaputt', now)).toBe('');
  });

  it('Tagesüberschriften und Gruppierung im Verlauf', () => {
    expect(dayLabel(at(2026, 9, 7), now)).toBe('Heute');
    expect(dayLabel(at(2026, 9, 6), now)).toBe('Gestern');
    expect(dayLabel(at(2026, 9, 5), now)).toBe('Montag, 5. Oktober');
    expect(dayLabel(at(2025, 9, 5), now)).toBe('Sonntag, 5. Oktober 2025');
    const groups = groupByDay(
      [
        { id: 1, created_at: at(2026, 9, 6, 8) },
        { id: 2, created_at: at(2026, 9, 6, 18) },
        { id: 3, created_at: at(2026, 9, 7, 7) },
      ],
      now,
    );
    expect(groups.map((g) => [g.label, g.items.map((i) => i.id)])).toEqual([
      ['Gestern', [1, 2]],
      ['Heute', [3]],
    ]);
  });
});

describe('Empfänger und Art der Unterhaltung', () => {
  const lena = person(2, 'Lena Lindner');
  const ben = person(3, 'Ben Winter', { role: 'schueler', role_label: 'Schüler/in', info: 'Klasse 5a' });
  const klasse = group('class_parents', '5a', 'Klasse 5a – Eltern', 24);

  it('fügt ohne Doppelte hinzu und entfernt per Schlüssel', () => {
    let list = addRecipient([], lena);
    list = addRecipient(list, lena);
    list = addRecipient(list, klasse);
    expect(list.map(recipientKey)).toEqual(['user:2', 'group:class_parents:5a']);
    expect(addRecipient(list, person(0, 'Gelöscht', { id: null }))).toHaveLength(2);
    expect(removeRecipient(list, 'user:2').map(recipientKey)).toEqual(['group:class_parents:5a']);
    expect(toInput(klasse)).toEqual({ type: 'group', kind: 'class_parents', ref: '5a', role: 'to' });
    expect(toInput(lena, 'cc')).toEqual({ type: 'user', id: 2, role: 'cc' });
    expect(toInput({ type: 'email', email: 'a@b.de' }, 'bcc')).toEqual({ type: 'email', email: 'a@b.de', name: '', role: 'bcc' });
    expect(isEmail('mama@web.de')).toBe(true);
    expect(isEmail('Lena')).toBe(false);
  });

  it('sagt die Art wie das Backend voraus', () => {
    expect(predictKind([], true, 'all')).toBeNull();
    expect(predictKind([lena], true, 'none')).toBe('direct');
    expect(predictKind([lena, ben], false, 'none')).toBe('group');
    expect(predictKind([lena, ben], true, 'all')).toBe('group');
    expect(predictKind([lena, ben], true, 'sender')).toBe('broadcast');
    expect(predictKind([klasse], true, 'all')).toBe('broadcast');
  });

  it('erklärt die Art verständlich', () => {
    expect(kindDescription('direct', [lena])).toBe('Einzelnachricht an Lena Lindner.');
    expect(kindDescription('group', [lena, ben])).toContain('Nachricht an 2 Personen');
    const text = kindDescription('broadcast', [klasse, lena]);
    expect(text).toContain('1 Gruppe und 1 Einzelperson');
    expect(text).toContain('bis zu 25 Personen');
    expect(text).toContain('nicht die anderen Empfänger/innen');
  });

  it('prüft vor dem Senden', () => {
    expect(composeProblems({ recipients: [], subject: '', body: '', attachments: 0, kind: null })).toEqual([
      'Bitte mindestens eine Empfängerin oder einen Empfänger auswählen.',
      'Bitte einen Nachrichtentext eingeben oder eine Datei anhängen.',
    ]);
    expect(composeProblems({ recipients: [lena], subject: 'Betreff', body: '', attachments: 1, kind: 'direct' })).toEqual([]);
    expect(composeProblems({ recipients: [lena], subject: ' ', body: 'x', attachments: 0, kind: 'direct' })[0]).toContain('Betreff');
    expect(composeProblems({ recipients: [lena], subject: '', body: 'x', attachments: 0, kind: 'email' })).toEqual([]);
    expect(composeProblems({ recipients: [klasse], subject: '  ', body: 'Hallo', attachments: 0, kind: 'broadcast' })).toEqual([
      'Bitte einen Betreff für das Rundschreiben angeben.',
    ]);
    const many = Array.from({ length: 26 }, (_, i) => person(i + 10, `P${i}`));
    expect(composeProblems({ recipients: many, subject: 'x', body: 'x', attachments: 0, kind: 'group' })[0]).toContain('Höchstens 25');
  });
});

describe('Darstellung', () => {
  it('Initialen', () => {
    expect(initials('Lena Lindner')).toBe('LL');
    expect(initials('Sekretariat')).toBe('S');
    expect(initials('Özge  von Ärger')).toBe('ÖÄ');
    expect(initials('')).toBe('?');
  });

  it('Kopfzeilen und Vorschau', () => {
    const direct = conv({ last_message: { id: 5, sender_id: 1, own: true, preview: 'Bis morgen', integrity_ok: true, created_at: '', attachments: 0, removed: false } });
    expect(listHeadline(direct)).toBe('Lena Lindner');
    expect(previewLine(direct)).toBe('Sie: Bis morgen');
    expect(threadTitle(direct)).toBe('Lena Lindner');
    const broadcast = conv({
      kind: 'broadcast',
      subject: 'Wandertag',
      participants: [],
      audience: [{ kind: 'class', ref: '5a', label: 'Klasse 5a – Schüler/innen' }],
      creator: person(9, 'Sabine Sekretariat'),
      last_message: { id: 6, sender_id: 9, own: false, preview: 'Wir treffen uns', integrity_ok: true, created_at: '', attachments: 0, removed: false, sender_name: 'Sabine Sekretariat' },
    });
    expect(listHeadline(broadcast)).toBe('Sabine Sekretariat');
    expect(listHeadline({ ...broadcast, is_creator: true })).toBe('An: Klasse 5a – Schüler/innen');
    expect(previewLine(broadcast)).toBe('Sabine Sekretariat: Wir treffen uns');
    expect(threadTitle(broadcast)).toBe('Wandertag');
    expect(threadTitle({ ...broadcast, subject: '' })).toBe('Klasse 5a – Schüler/innen');
    expect(participantsText([person(1, 'A', { me: true }), person(2, 'B'), person(3, 'C'), person(4, 'D'), person(5, 'E')], 2)).toBe('B, C und 2 weitere');
  });

  it('Badge, Aufbewahrung', () => {
    expect(badgeCount(undefined)).toBe(0);
    expect(badgeCount({ unread: 3, messages: 7, muted: 1, archived: 0 })).toBe(3);
    expect(retentionText(0)).toBe('Nachrichten werden nicht automatisch gelöscht.');
    expect(retentionText(365)).toContain('nach einem Jahr');
    expect(retentionText(730)).toContain('nach 2 Jahren');
    expect(retentionText(90)).toContain('nach 90 Tagen');
  });
});

describe('Links im Text', () => {
  it('erkennt nur http(s) und schneidet Satzzeichen ab', () => {
    expect(linkify('Siehe https://schule.example/plan.pdf, danke.')).toEqual([
      { type: 'text', value: 'Siehe ' },
      { type: 'link', value: 'https://schule.example/plan.pdf', href: 'https://schule.example/plan.pdf' },
      { type: 'text', value: ', danke.' },
    ]);
    expect(linkify('www.example.org!')).toEqual([
      { type: 'link', value: 'www.example.org', href: 'https://www.example.org' },
      { type: 'text', value: '!' },
    ]);
    expect(linkify('javascript:alert(1) und ftp://x')).toEqual([{ type: 'text', value: 'javascript:alert(1) und ftp://x' }]);
    expect(linkify('')).toEqual([]);
  });
});

describe('Verlauf', () => {
  it('führt ältere Nachrichten ohne Doppelte zusammen', () => {
    expect(mergeMessages([{ id: 1 }, { id: 2 }], [{ id: 2 }, { id: 3 }]).map((m) => m.id)).toEqual([1, 2, 3]);
  });
  it('erkennt „unten angekommen“', () => {
    expect(nearBottom(900, 100, 1000)).toBe(true);
    expect(nearBottom(500, 100, 1000)).toBe(false);
  });
});

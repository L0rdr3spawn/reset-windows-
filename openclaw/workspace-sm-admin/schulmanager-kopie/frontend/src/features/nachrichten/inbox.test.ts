import { describe, expect, it } from 'vitest';
import { buildList, matchesFilter, sortItems, timeValue, totalUnread, type InboxItem } from './inbox';

const item = (over: Partial<InboxItem>): InboxItem => ({
  key: 'c:1',
  type: 'chat',
  path: '/nachrichten/c/1',
  title: 'Anna',
  subtitle: '',
  preview: '',
  at: '2026-10-13T10:00:00Z',
  unread: 0,
  muted: false,
  archived: false,
  attachment: false,
  avatar: { name: 'Anna' },
  tag: '',
  ...over,
});

describe('gemeinsame Liste', () => {
  const list = [
    item({ key: 'c:1', at: '2026-10-13T10:00:00' }),
    item({ key: 'c:2', type: 'gruppe', title: 'Klasse 5a', at: '2026-10-13T12:00:00Z' }),
    item({ key: 'b:1', type: 'brief', title: 'Sekretariat', subtitle: 'Elternabend', at: '2026-10-12T09:00:00Z' }),
    item({ key: 'b:2', type: 'email', at: '2026-10-11T09:00:00Z', archived: true }),
    item({ key: 'a:1', type: 'mitteilung', title: 'Ferien', at: '2026-10-10T09:00:00Z' }),
  ];
  it('Zeitstempel ohne Zone gelten als UTC', () => {
    expect(timeValue('2026-10-13T10:00:00')).toBe(timeValue('2026-10-13T10:00:00Z'));
    expect(timeValue(null)).toBe(0);
  });
  it('sortiert nach letzter Aktivität', () => {
    expect(sortItems(list).map((i) => i.key)).toEqual(['c:2', 'c:1', 'b:1', 'b:2', 'a:1']);
  });
  it('Filter: Alle ohne Archiv, Archiv nur Archiviertes, Arten getrennt', () => {
    expect(buildList(list, 'alle', '').map((i) => i.key)).toEqual(['c:2', 'c:1', 'b:1', 'a:1']);
    expect(buildList(list, 'archiv', '').map((i) => i.key)).toEqual(['b:2']);
    expect(buildList(list, 'chats', '').map((i) => i.key)).toEqual(['c:1']);
    expect(buildList(list, 'gruppen', '').map((i) => i.key)).toEqual(['c:2']);
    expect(buildList(list, 'mitteilungen', '').map((i) => i.key)).toEqual(['a:1']);
    expect(matchesFilter(list[3], 'email')).toBe(false);
  });
  it('Suche: Chats und Mitteilungen nach Name, Briefe bereits vom Server gefiltert', () => {
    expect(buildList(list, 'chats', 'anna').map((i) => i.key)).toEqual(['c:1']);
    expect(buildList(list, 'gruppen', 'klasse').map((i) => i.key)).toEqual(['c:2']);
    expect(buildList(list, 'gruppen', 'xyz')).toEqual([]);
    expect(buildList(list, 'mitteilungen', 'ferien').map((i) => i.key)).toEqual(['a:1']);
  });
  it('EIN Ungelesen-Zähler', () => {
    expect(totalUnread(2, 3)).toBe(5);
    expect(totalUnread(undefined, -1)).toBe(0);
  });
});

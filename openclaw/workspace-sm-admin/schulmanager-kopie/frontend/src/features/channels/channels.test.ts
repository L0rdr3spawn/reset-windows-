import { describe, expect, it } from 'vitest';
import {
  badgeCount,
  buildFolderTree,
  countInFolder,
  descendantIds,
  draftToInput,
  dueText,
  flattenTree,
  folderPath,
  fromLocalInput,
  groupByDate,
  isOpenForStudent,
  lessonLine,
  matchChannel,
  remainingText,
  safeHref,
  toLocalInput,
  visibilityText,
} from './logic';
import { parseInline, parseMarkdown, plainText } from './markdown';
import type { Folder, Item } from './types';

const F = (id: number, parent_id: number | null, name: string, position = 0, hidden = false): Folder => ({ id, parent_id, name, position, hidden });

describe('Ordnerbaum', () => {
  const folders = [F(1, null, 'Woche 2', 1), F(2, null, 'Woche 1', 0), F(3, 2, 'Arbeitsblätter'), F(4, 3, 'Lösungen', 0, true), F(5, 99, 'Waise', 5)];

  it('baut den Baum nach Position, Waisen landen oben', () => {
    const tree = buildFolderTree(folders);
    expect(tree.map((n) => n.name)).toEqual(['Woche 1', 'Woche 2', 'Waise']);
    expect(tree[0]!.children[0]!.children[0]!.name).toBe('Lösungen');
    expect(flattenTree(tree).map((n) => [n.name, n.depth])).toEqual([
      ['Woche 1', 0],
      ['Arbeitsblätter', 1],
      ['Lösungen', 2],
      ['Woche 2', 0],
      ['Waise', 0],
    ]);
  });

  it('Pfad, Unterordner und Zählung', () => {
    expect(folderPath(folders, 4).map((f) => f.name)).toEqual(['Woche 1', 'Arbeitsblätter', 'Lösungen']);
    expect(folderPath(folders, null)).toEqual([]);
    expect([...descendantIds(folders, 2)].sort()).toEqual([3, 4]);
    const items = [{ folder_id: 3 }, { folder_id: 4 }, { folder_id: null }, { folder_id: 1 }] as Item[];
    expect(countInFolder(folders, items, 2)).toBe(2);
  });

  it('Zyklen führen nicht zu Endlosschleifen', () => {
    const cyc = [F(1, 2, 'a'), F(2, 1, 'b')];
    expect(folderPath(cyc, 1).length).toBeLessThanOrEqual(2);
    expect(buildFolderTree(cyc)).toEqual([]);
  });
});

describe('Sichtbarkeit und Fristen', () => {
  it('Texte für Lehrende', () => {
    expect(visibilityText({ visibility: 'hidden', state: 'hidden', lesson: null })).toBe('verborgen');
    expect(visibilityText({ visibility: 'visible', state: 'folder_hidden', lesson: null })).toMatch(/Ordner nicht freigegeben/);
    const lesson = { date: '2026-10-13', lesson_id: 'L2', period: 0, label: 'Di, 13.10. · 1. Std. · 07:55', key: 'k' };
    expect(visibilityText({ visibility: 'lesson', state: 'lesson', lesson, release_at: '2026-10-13T05:55:00Z' })).toBe('zur Stunde Di, 13.10. · 1. Std. · 07:55');
    expect(visibilityText({ visibility: 'lesson', state: 'visible', lesson })).toMatch(/^sichtbar seit Stundenbeginn/);
    expect(visibilityText({ visibility: 'scheduled', state: 'scheduled', lesson: null, release_at: '2026-10-13T05:55:00Z' })).toMatch(/^geplant ab /);
  });

  it('datetime-local ↔ ISO (UTC) ist verlustfrei', () => {
    const iso = fromLocalInput('2026-10-13T08:15');
    expect(iso).toMatch(/Z$/);
    expect(toLocalInput(iso)).toBe('2026-10-13T08:15');
    expect(fromLocalInput('')).toBeNull();
    expect(fromLocalInput('kein Datum')).toBeNull();
  });

  it('Frist und Restzeit', () => {
    const now = new Date('2026-10-12T10:00:00Z');
    expect(dueText(null, now)).toBe('ohne Frist');
    expect(dueText('2026-10-12T09:00:00Z', now)).toMatch(/^Frist abgelaufen/);
    expect(dueText('2026-10-14T09:00:00Z', now)).toMatch(/^bis /);
    expect(remainingText('2026-10-15T10:00:00Z', now)).toBe('noch 3 Tage');
    expect(remainingText('2026-10-12T15:00:00Z', now)).toBe('noch 5 Std.');
    expect(remainingText('2026-10-12T09:00:00Z', now)).toBe('');
    expect(isOpenForStudent('zurueckgegeben')).toBe(true);
    expect(isOpenForStudent('abgegeben')).toBe(false);
  });

  it('Formular-Entwurf → Backend-Eingabe', () => {
    expect(draftToInput({ mode: 'visible', from: '', lesson: null })).toEqual({ visibility: 'visible' });
    expect(draftToInput({ mode: 'scheduled', from: '', lesson: null })).toMatch(/Zeitpunkt|Datum/);
    expect(draftToInput({ mode: 'lesson', from: '', lesson: null })).toMatch(/stunde/i);
    const lesson = { key: 'k', date: '2026-10-13', lesson_id: 'L2', period: 0, label: 'x' };
    expect(draftToInput({ mode: 'lesson', from: '', lesson })).toEqual({ visibility: 'lesson', lesson: { date: '2026-10-13', lesson_id: 'L2', period: 0 } });
  });
});

describe('Kanäle und Stunden', () => {
  const ch = { title: 'Kath. Religion · Religion/PP 5a+5b', subtitle: 'kath · Frau Becker · 5a, 5b', ref: 'REL-5a-5b#1', classes: ['5a', '5b'], subject_name: 'Kath. Religion', teachers: ['Frau Becker'] };

  it('Suche über alle Wörter (Kurs, Klasse, Lehrkraft)', () => {
    expect(matchChannel(ch, '')).toBe(true);
    expect(matchChannel(ch, '5b becker')).toBe(true);
    expect(matchChannel(ch, 'religion 6a')).toBe(false);
  });

  it('Badge zählt neues Material und Beiträge, archivierte nicht', () => {
    expect(
      badgeCount([
        { new_items: 2, new_posts: 1, archived: false },
        { new_items: 5, new_posts: 0, archived: true },
        { archived: false },
      ]),
    ).toBe(3);
  });

  it('Stunden nach Tagen gruppieren und beschreiben', () => {
    const g = groupByDate([{ date: '2026-10-12' }, { date: '2026-10-12' }, { date: '2026-10-13' }]);
    expect(g.map((x) => [x.date, x.lessons.length])).toEqual([
      ['2026-10-12', 2],
      ['2026-10-13', 1],
    ]);
    expect(lessonLine({ period_label: '1.', time: '07:55', end_time: '08:40', rooms: ['R101'] })).toBe('1. Std. · 07:55–08:40 · Raum R101');
  });

  it('nur sichere Links', () => {
    expect(safeHref('https://example.org/a b')).toBe('https://example.org/a%20b');
    expect(safeHref('javascript:alert(1)')).toBeNull();
    expect(safeHref('data:text/html,x')).toBeNull();
    expect(safeHref('mailto:a@b.de')).toBe('mailto:a@b.de');
  });
});

describe('Markdown (sicher, ohne HTML)', () => {
  it('Blöcke: Überschrift, Liste, Zitat, Code, Absatz', () => {
    const b = parseMarkdown('# Titel\n\nText mit **fett** und *kursiv*.\n\n- eins\n- zwei\n\n1. a\n2. b\n\n> Zitat\n\n```\ncode <b>\n```');
    expect(b.map((x) => x.t)).toEqual(['h', 'p', 'ul', 'ol', 'quote', 'pre']);
    expect(b[5]).toEqual({ t: 'pre', v: 'code <b>' });
  });

  it('Inline: fett, kursiv, Code, Links nur http/https/mailto', () => {
    expect(parseInline('**a** _b_ `c`').map((n) => n.t)).toEqual(['strong', 'text', 'em', 'text', 'code']);
    const links = parseInline('[gut](https://example.org) [böse](javascript:alert(1)) https://schule.example/x.');
    const hrefs = links.filter((n) => n.t === 'link').map((n) => (n.t === 'link' ? n.href : ''));
    expect(hrefs).toEqual(['https://example.org/', 'https://schule.example/x']);
    expect(links.some((n) => n.t === 'text' && n.v.includes('javascript:'))).toBe(true);
  });

  it('HTML bleibt Text, snake_case bleibt unverändert', () => {
    const nodes = parseInline('<script>alert(1)</script> datei_name_neu');
    expect(nodes).toEqual([{ t: 'text', v: '<script>alert(1)</script> datei_name_neu' }]);
  });

  it('Vorschautext ohne Auszeichnung', () => {
    expect(plainText('# Hallo\n\n**Welt** und [Link](https://a.de)')).toBe('Hallo Welt und Link');
    expect(plainText('x'.repeat(300), 20)).toHaveLength(20);
  });
});

import { describe, expect, it } from 'vitest';
import { eventWhen, infoCards, messageLink, moveCard, splitContacts, withoutInfoCards } from './classInfo';
import type { ClassContact, Item } from './types';

const I = (id: number, position: number, info_card?: boolean): Item => ({ id, position, info_card, title: `T${id}` }) as unknown as Item;

describe('Klassenraum: Bereich „Klasse“', () => {
  it('Infokarten stehen in Reihenfolge und fehlen im Material', () => {
    const items = [I(1, 0), I(2, 5, true), I(3, 1, true)];
    expect(infoCards(items).map((c) => c.id)).toEqual([3, 2]);
    const detail = { items, x: 1 };
    expect(withoutInfoCards(detail).items.map((i) => i.id)).toEqual([1]);
    const plain = { items: [I(1, 0)] };
    expect(withoutInfoCards(plain)).toBe(plain);
  });

  it('Karte verschieben tauscht die Plätze und nummeriert neu', () => {
    const cards = [I(3, 1, true), I(2, 5, true), I(4, 9, true)];
    // neue Reihenfolge 2, 3, 4 → Positionen 0, 1, 2; Karte 3 steht schon auf 1
    expect(moveCard(cards, 2, -1)).toEqual([
      { id: 2, position: 0 },
      { id: 4, position: 2 },
    ]);
    expect(moveCard(cards, 3, -1)).toEqual([]);
    expect(moveCard(cards, 4, 1)).toEqual([]);
    expect(moveCard(cards, 99, 1)).toEqual([]);
  });

  it('Termin: Datum und Uhrzeit', () => {
    expect(eventWhen({ date_from: '2027-02-02', date_to: '2027-02-02', time_from: '19:00', time_to: '20:30' })).toBe('02.02.2027, 19:00–20:30 Uhr');
    expect(eventWhen({ date_from: '2027-02-02', date_to: '2027-02-02', time_from: '19:00', time_to: '' })).toBe('02.02.2027, ab 19:00 Uhr');
    expect(eventWhen({ date_from: '2027-02-02', date_to: '2027-02-04', time_from: '', time_to: '' })).toBe('02.02.2027 – 04.02.2027');
  });

  it('Ansprechpersonen: Klassenleitung getrennt, Nachricht ans Postfach', () => {
    const c = (id: string, lead: boolean): ClassContact => ({ teacher_id: id, name: id, class_teacher: lead, subjects: [] });
    const { lead, others } = splitContacts([c('MÜL', true), c('SCH', false)]);
    expect(lead.map((x) => x.teacher_id)).toEqual(['MÜL']);
    expect(others.map((x) => x.teacher_id)).toEqual(['SCH']);
    expect(messageLink('A&B')).toBe('/nachrichten/neu?lehrkraft=A%26B');
  });
});

/** Reine Hilfen für den Bereich „Klasse“ des Klassenraums (siehe ClassTab.tsx). */
import { dateRangeLabel } from '../../lib/dates';
import { byPosition } from './logic';
import type { ClassContact, ClassEvent, Item } from './types';

/** Infokarten in der angezeigten Reihenfolge (Material und Aufgaben gehören nicht dazu). */
export function infoCards(items: readonly Item[]): Item[] {
  return items.filter((i) => i.info_card).sort(byPosition);
}

/** Material ohne die angehefteten Infokarten (die stehen im Bereich „Klasse“). */
export function withoutInfoCards<T extends { items: readonly Item[] }>(detail: T): T {
  return detail.items.some((i) => i.info_card) ? { ...detail, items: detail.items.filter((i) => !i.info_card) } : detail;
}

/** Neue Positionen nach Verschieben einer Karte um `dir` (-1 hoch, +1 runter); nur geänderte Karten. */
export function moveCard(cards: readonly Item[], id: number, dir: -1 | 1): { id: number; position: number }[] {
  const order = cards.map((c) => c.id);
  const at = order.indexOf(id);
  const to = at + dir;
  if (at < 0 || to < 0 || to >= order.length) return [];
  [order[at], order[to]] = [order[to], order[at]];
  return order.map((cid, position) => ({ id: cid, position })).filter((p) => cards.find((c) => c.id === p.id)?.position !== p.position);
}

/** „Di., 02.02.2027“ bzw. Zeitraum, dazu „19:00–20:30 Uhr“. */
export function eventWhen(ev: Pick<ClassEvent, 'date_from' | 'date_to' | 'time_from' | 'time_to'>): string {
  const day = dateRangeLabel(ev.date_from, ev.date_to || ev.date_from);
  const time = ev.time_from ? (ev.time_to ? `${ev.time_from}–${ev.time_to} Uhr` : `ab ${ev.time_from} Uhr`) : '';
  return time ? `${day}, ${time}` : day;
}

/** Klassenleitung zuerst, dann Fachlehrkräfte (alphabetisch, wie vom Server geliefert). */
export function splitContacts(contacts: readonly ClassContact[]): { lead: ClassContact[]; others: ClassContact[] } {
  return { lead: contacts.filter((c) => c.class_teacher), others: contacts.filter((c) => !c.class_teacher) };
}

/** Adresse „Nachricht schreiben“ an eine Lehrkraft (Postfach). */
export function messageLink(teacherId: string): string {
  return `/nachrichten/neu?lehrkraft=${encodeURIComponent(teacherId)}`;
}

/**
 * Klausuren und Tests führen direkt in den Kursraum des Kurses/Kursteils (der Server liefert `channel_id` nur, wenn das
 * Konto den Kursraum öffnen darf). Die Adresse trägt `klausur`, `datum` und `art`, damit der Kursraum einen Hinweis
 * „Klausur am …“ mit Link zu den Details zeigen kann. Ohne Zugang bleibt der Link zum Klausur-Detail.
 */
export type ExamKind = 'klausur' | 'test' | 'nachschreiben';

export const examDetailLink = (id: string, date?: string): string => `/klausuren?klausur=${encodeURIComponent(id)}${date ? `&datum=${date}` : ''}`;

export function examRoomLink(channelId: number, x: { id: string; kind?: ExamKind; date?: string }, child?: string): string {
  const p = new URLSearchParams({ klausur: x.id });
  if (x.date) p.set('datum', x.date);
  if (x.kind) p.set('art', x.kind);
  if (child) p.set('child', child);
  return `/kursraeume/${channelId}?${p.toString()}`;
}

/** Ziel beim Klick auf eine Klausur/einen Test: Kursraum, sonst Klausur-Detail (Nachschreibtermine ohne Zugang: kein Ziel). */
export function examTarget(x: { id: string; kind?: ExamKind; channel_id?: number | null; exam_id?: string }, date: string, child?: string): string | undefined {
  if (x.channel_id) return examRoomLink(x.channel_id, { id: x.exam_id ?? x.id, kind: x.kind, date }, child);
  return x.kind === 'nachschreiben' ? undefined : examDetailLink(x.id, date);
}

/** Hilfen für Emoji in Texten (Unicode, mit Zeichenfolgen wie 👨‍👩‍👧 oder 🇩🇪 als *ein* Zeichen). */

const segmenter: { segment(text: string): Iterable<{ segment: string }> } | null =
  typeof Intl !== 'undefined' && 'Segmenter' in Intl ? new Intl.Segmenter('de', { granularity: 'grapheme' }) : null;

/** Zerlegt in sichtbare Zeichen (Graphem-Cluster); ohne `Intl.Segmenter` nach Codepunkten. */
export function graphemes(text: string): string[] {
  return segmenter ? Array.from(segmenter.segment(text), (s) => s.segment) : Array.from(text);
}

/** Kürzt ohne ein Emoji (Surrogatpaar, Hautton, Flagge …) zu zerreißen. */
export function truncateText(text: string, max: number): string {
  const parts = graphemes(text);
  return parts.length <= max ? text : `${parts.slice(0, max).join('')}…`;
}

const EMOJI_ONLY = /^(?:\p{Extended_Pictographic}|\p{Regional_Indicator}|\p{Emoji_Modifier}|[‍️⃣\s])+$/u;

/** Besteht der Text nur aus 1–`max` Emoji (und Leerraum)? Dann wird er größer dargestellt. */
export function isEmojiOnly(text: string, max = 6): boolean {
  const t = text.trim();
  if (!t || !EMOJI_ONLY.test(t)) return false;
  return graphemes(t).filter((g) => g.trim()).length <= max;
}

/** Fügt `insert` an der Cursorposition (bzw. Auswahl) ein; liefert neuen Text und neue Cursorposition. */
export function insertAt(
  value: string,
  start: number | null | undefined,
  end: number | null | undefined,
  insert: string,
  maxLength?: number,
): { value: string; caret: number } {
  const s = Math.min(start ?? value.length, value.length);
  const e = Math.min(Math.max(end ?? s, s), value.length);
  const next = value.slice(0, s) + insert + value.slice(e);
  if (maxLength && next.length > maxLength) return { value, caret: s };
  return { value: next, caret: s + insert.length };
}

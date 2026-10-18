const FOLD: Record<string, string> = { ä: 'ae', ö: 'oe', ü: 'ue', ß: 'ss', Ä: 'AE', Ö: 'OE', Ü: 'UE' };

/** Kürzel-Vorschlag aus dem Fachnamen: „Informatik“ → „INF“; ist es vergeben, wird eine Ziffer angehängt. */
export function suggestSubjectCode(name: string, taken: Iterable<string>): string {
  const letters = name
    .replace(/[äöüßÄÖÜ]/g, (c) => FOLD[c] ?? c)
    .replace(/[^A-Za-z0-9 ]/g, '')
    .trim();
  if (!letters) return '';
  const words = letters.split(/\s+/);
  const base = (words.length > 1 ? words.map((w) => w.slice(0, 1)).join('') : (words[0] ?? '').slice(0, 3)).toUpperCase();
  const used = new Set([...taken].map((x) => x.toLowerCase()));
  if (!used.has(base.toLowerCase())) return base;
  for (let i = 2; i < 100; i++) if (!used.has(`${base}${i}`.toLowerCase())) return `${base}${i}`;
  return base;
}

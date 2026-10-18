/** Kleine Formatierungs- und Listenhelfer. */

export function joinList(list: readonly (string | null | undefined)[] | null | undefined, sep = ', '): string {
  return (list ?? []).filter((x): x is string => !!x).join(sep);
}

export function parseList(text: string): string[] {
  return text
    .split(/[,;\n]/)
    .map((x) => x.trim())
    .filter(Boolean);
}

export function parseNumList(text: string): number[] {
  return parseList(text)
    .map((x) => parseInt(x, 10))
    .filter((n) => !Number.isNaN(n));
}

export function formatBytes(n: number | null | undefined): string {
  if (n === null || n === undefined) return '–';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

export function plural(n: number, one: string, many: string): string {
  return `${n} ${n === 1 ? one : many}`;
}

/** Erzeugt eine kurze, zufällige ID mit Präfix (für neue Datensätze). */
export function newId(prefix: string): string {
  const rnd = Math.random().toString(36).slice(2, 8).toUpperCase();
  return `${prefix}${Date.now().toString(36).slice(-4).toUpperCase()}${rnd}`;
}

/** Deutsche, natürliche Sortierung (5a < 10a). */
export const collator = new Intl.Collator('de', { numeric: true, sensitivity: 'base' });

export function sortBy<T>(list: readonly T[], key: (x: T) => string | number): T[] {
  return list.slice().sort((a, b) => {
    const ka = key(a);
    const kb = key(b);
    if (typeof ka === 'number' && typeof kb === 'number') return ka - kb;
    return collator.compare(String(ka), String(kb));
  });
}

/** Volltextsuche: alle Wörter müssen vorkommen. */
export function matchesQuery(haystack: string, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  const h = haystack.toLowerCase();
  return q.split(/\s+/).every((w) => h.includes(w));
}

/** Sichtbarer Zeilenbereich für virtualisierte Listen [start, end). */
export function visibleRange(scrollTop: number, viewport: number, rowHeight: number, total: number, overscan = 8): [number, number] {
  const start = Math.max(0, Math.floor(scrollTop / rowHeight) - overscan);
  const end = Math.min(total, Math.ceil((scrollTop + viewport) / rowHeight) + overscan);
  return [start, Math.max(start, end)];
}

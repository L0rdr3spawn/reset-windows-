/**
 * App-Rahmen (A-61): Auswahl der Einträge für die untere Leiste am Handy (< 600 px).
 * Breakpoints und Navigationsmuster: docs/DESIGN.md, Abschnitt „Breakpoints“.
 */

/** Wichtigste Ziele in dieser Reihenfolge – was die Rolle nicht sehen darf, entfällt. */
export const BOTTOM_NAV_PREFERRED = ['/', '/stundenplan', '/vertretung', '/nachrichten'] as const;

/** Kurze Beschriftungen für die untere Leiste (sonst die Menübeschriftung). */
export const BOTTOM_NAV_SHORT: Record<string, string> = {
  '/vertretung': 'Vertretung',
  '/krankmeldungen': 'Krank',
};

/**
 * Bis zu `max` Einträge für die untere Leiste: zuerst die bevorzugten Ziele, dann die übrigen sichtbaren Einträge
 * in Menüreihenfolge. Alles andere bleibt im Menü („Menü“-Knopf öffnet die Seitenleiste).
 */
export function bottomNavItems<T extends { path: string }>(items: readonly T[], max = 4): T[] {
  const out: T[] = [];
  for (const p of BOTTOM_NAV_PREFERRED) {
    const hit = items.find((i) => i.path === p);
    if (hit && out.length < max) out.push(hit);
  }
  for (const i of items) {
    if (out.length >= max) break;
    if (!out.includes(i) && i.path !== '/profil') out.push(i);
  }
  return out;
}

export function bottomNavLabel(item: { path: string; label: string }): string {
  return BOTTOM_NAV_SHORT[item.path] ?? item.label;
}

/**
 * Nach dem Schließen des ausgeklappten Menüs (Escape, Schließen, Hintergrund): Fokus zurück zum Auslöser, wenn er in
 * der Seitenleiste lag (am Handy danach unsichtbar) oder verloren ging. Nach einem Seitenwechsel liegt er schon im
 * Inhalt und bleibt dort.
 */
export function shouldRestoreMenuFocus<N>(
  active: N | null | undefined,
  sidebar: { contains: (n: N) => boolean } | null | undefined,
  body: N | null | undefined,
): boolean {
  if (!active || active === body) return true;
  return !!sidebar && sidebar.contains(active);
}

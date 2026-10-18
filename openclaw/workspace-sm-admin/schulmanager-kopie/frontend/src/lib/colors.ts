/**
 * Fächerfarben: Server-Farbe verwenden, sonst stabile Farbe aus dem Kürzel ableiten.
 * Textfarbe wird nach Kontrast (WCAG) gewählt.
 */

const PALETTE = [
  '#4f86c6', '#e07a5f', '#81b29a', '#f2cc8f', '#9c6ade', '#3d9970', '#ff851b', '#7fdbff',
  '#b10dc9', '#2ecc40', '#e6a23c', '#5dade2', '#c0392b', '#16a085', '#d35400', '#8e44ad',
  '#27ae60', '#f39c12', '#2980b9', '#e84393',
];

export function hashString(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

export function fallbackColor(key: string): string {
  return PALETTE[hashString(key || '?') % PALETTE.length] ?? '#888888';
}

function parseHex(color: string): [number, number, number] | null {
  let c = color.trim();
  if (!c.startsWith('#')) return null;
  c = c.slice(1);
  if (c.length === 3) c = c.split('').map((x) => x + x).join('');
  if (c.length !== 6 || !/^[0-9a-f]{6}$/i.test(c)) return null;
  return [parseInt(c.slice(0, 2), 16), parseInt(c.slice(2, 4), 16), parseInt(c.slice(4, 6), 16)];
}

export function isHexColor(color: string | null | undefined): boolean {
  return !!color && parseHex(color) !== null;
}

/** Relative Leuchtdichte nach WCAG 2.x */
export function luminance(color: string): number {
  const rgb = parseHex(color);
  if (!rgb) return 0.5;
  const [r, g, b] = rgb.map((v) => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  }) as [number, number, number];
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contrastRatio(a: string, b: string): number {
  const la = luminance(a);
  const lb = luminance(b);
  const [hi, lo] = la > lb ? [la, lb] : [lb, la];
  return (hi + 0.05) / (lo + 0.05);
}

/** Schwarz oder Weiß – je nachdem, was auf der Hintergrundfarbe besser lesbar ist. */
export function textOn(bg: string): string {
  return contrastRatio(bg, '#111111') >= contrastRatio(bg, '#ffffff') ? '#111111' : '#ffffff';
}

export function subjectColor(subject: string, color?: string | null): string {
  return isHexColor(color) ? (color as string) : fallbackColor(subject);
}

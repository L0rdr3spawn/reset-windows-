/** Abzeichen-Symbol aus den eingebauten Zeichnungen (kein Bild-Upload nötig). */
import './kompetenzen.css';

const PATHS: Record<string, string> = {
  star: 'M12 3l2.8 5.7 6.2.9-4.5 4.4 1 6.2L12 17.2 6.5 20.2l1-6.2L3 9.6l6.2-.9z',
  medal: 'M12 15a6 6 0 1 0 0-12 6 6 0 0 0 0 12zM8.5 14L7 21l5-3 5 3-1.5-7',
  trophy: 'M8 4h8v5a4 4 0 0 1-8 0zM8 6H4v1a3 3 0 0 0 4 2.8M16 6h4v1a3 3 0 0 1-4 2.8M12 13v4M8 21h8M10 17h4',
  flag: 'M5 21V4M5 4h12l-2 4 2 4H5',
  book: 'M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2zM4 19a2 2 0 0 1 2-2h13',
  calculator: 'M6 3h12v18H6zM9 7h6M9 12h.01M12 12h.01M15 12h.01M9 16h.01M12 16h.01M15 16h.01',
  pencil: 'M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z',
  puzzle: 'M10 4a2 2 0 1 1 4 0v2h4v4h-2a2 2 0 1 0 0 4h2v4h-4v-2a2 2 0 1 0-4 0v2H6v-4h2a2 2 0 1 0 0-4H6V6h4z',
  bulb: 'M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z',
  heart: 'M12 21s-8-5-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 10c0 6-8 11-8 11z',
  leaf: 'M5 19C5 10 10 5 20 4c0 10-5 15-14 15zM5 19c2-4 5-7 9-9',
  rocket: 'M5 15c-1 2-1 4-1 5 1 0 3 0 5-1M9 15l-3-3c1-5 5-9 14-9 0 9-4 13-9 14zM15 9h.01',
};

export function BadgeIcon({ icon, color, size = 'md', label }: { icon: string; color: string; size?: 'sm' | 'md' | 'lg'; label?: string }) {
  const d = PATHS[icon] ?? PATHS.star;
  return (
    <span className={`cp-badge cp-badge-${size} cp-color-${color}`} role={label ? 'img' : undefined} aria-label={label} aria-hidden={label ? undefined : true}>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" focusable="false">
        <path d={d} />
      </svg>
    </span>
  );
}

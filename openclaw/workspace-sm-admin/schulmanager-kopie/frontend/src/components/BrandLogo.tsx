import { APP_NAME } from '../brand';

/**
 * Bildmarke als Inline-SVG in `currentColor` (Pulslinie + Punkt, ohne Kachel). Die Kachel liefert die umgebende
 * Fläche (`.brand-logo`: Primärfarbe + `--on-primary`), so folgt das Logo automatisch den Design-Tokens und dem
 * Farbschema. Geometrie identisch mit `assets/logo-mono.svg`.
 */
export function BrandLogo({ size = 20, title }: { size?: number; title?: string }) {
  return (
    <svg viewBox="0 0 64 64" width={size} height={size} role={title ? 'img' : undefined} aria-hidden={title ? undefined : true} focusable="false">
      {title ? <title>{title ?? APP_NAME}</title> : null}
      <path d="M8 37h13l6-18 8 28 6-10h9" fill="none" stroke="currentColor" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="56" cy="37" r="5" fill="currentColor" />
    </svg>
  );
}

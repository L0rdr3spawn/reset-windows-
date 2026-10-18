/** Kleine Bausteine des Postfachs: Symbole, Profilkreis, Personenzeile, Zeitangabe. */
import type { ReactNode } from 'react';
import { fullTime, initials, listTime, personDetail } from './logic';
import type { Person } from './types';

const GLYPHS = {
  mail: 'M3 5h18v14H3zM3 7l9 6 9-6',
  send: 'M21 3L10 14M21 3l-7 18-4-7-7-4z',
  reply: 'M9 14L4 9l5-5M4 9h11a5 5 0 0 1 5 5v6',
  clip: 'M21 11.5l-8.6 8.6a5.5 5.5 0 0 1-7.8-7.8l8.6-8.6a3.7 3.7 0 0 1 5.2 5.2l-8.6 8.6a1.8 1.8 0 0 1-2.6-2.6l7.9-7.9',
  archive: 'M3 4h18v4H3zM5 8v12h14V8M10 12h4',
  unarchive: 'M3 4h18v4H3zM5 8v12h14V8M12 18v-6M9 15l3-3 3 3',
  bellOff: 'M13.7 21a2 2 0 0 1-3.4 0M18.6 13A17 17 0 0 1 18 8M6.3 6.3A6 6 0 0 0 6 8c0 7-3 9-3 9h14M18 8a6 6 0 0 0-9.3-5M3 3l18 18',
  bell: 'M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0',
  flag: 'M4 22V4M4 4h13l-2 4 2 4H4',
  ban: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM5.6 5.6l12.8 12.8',
  trash: 'M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v6M14 11v6',
  unread: 'M3 5h18v14H3zM3 7l9 6 9-6M19 3.5a2 2 0 1 0 .01 0',
  people: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8',
  megaphone: 'M3 11v3a1 1 0 0 0 1 1h2l5 4V6L6 10H4a1 1 0 0 0-1 1zM15 9a3 3 0 0 1 0 6M18 6a7 7 0 0 1 0 12',
  lock: 'M5 11h14v10H5zM8 11V7a4 4 0 0 1 8 0v4',
  shield: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z',
  back: 'M15 18l-6-6 6-6',
  pen: 'M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z',
  check: 'M20 6L9 17l-5-5',
  plus: 'M12 5v14M5 12h14',
  arrowUp: 'M12 19V5M5 12l7-7 7 7',
  cog: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z',
} as const;

export type GlyphName = keyof typeof GLYPHS;

/** Symbol (dekorativ – die Bedeutung steht immer auch als Text oder `aria-label` daneben). */
export function Glyph({ name, size = 18, className }: { name: GlyphName; size?: number; className?: string }) {
  return (
    <svg
      className={`pf-glyph${className ? ` ${className}` : ''}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.9"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d={GLYPHS[name]} />
    </svg>
  );
}

function tone(role: string | null | undefined): string {
  if (role === 'schueler') return 'pf-tone-student';
  if (role === 'eltern') return 'pf-tone-parent';
  if (!role) return 'pf-tone-none';
  return 'pf-tone-staff';
}

/** Profilkreis mit Initialen bzw. Symbol (Rundschreiben, Gruppe) – dekorativ. */
export function Avatar({ name, role, size = 36, group, glyph }: { name: string; role?: string | null; size?: number; group?: boolean; glyph?: GlyphName }) {
  const symbol = glyph ?? (group ? 'megaphone' : null);
  return (
    <span className={`pf-avatar ${symbol ? 'pf-tone-group' : tone(role)}`} style={{ width: size, height: size, fontSize: Math.round(size * 0.38) }} aria-hidden="true">
      {symbol ? <Glyph name={symbol} size={Math.round(size * 0.5)} /> : initials(name)}
    </span>
  );
}

/** Name mit Rolle/Klasse (datensparsam aus dem Backend). */
export function PersonLine({ person, extra }: { person: Person; extra?: ReactNode }) {
  const detail = personDetail(person);
  return (
    <span className="pf-person">
      <span className="pf-person-name">{person.name}</span>
      {detail && <span className="pf-person-detail">{detail}</span>}
      {person.active === false && person.id !== null && <span className="badge badge-warning">nicht erreichbar</span>}
      {extra}
    </span>
  );
}

/** Zeitangabe mit vollständigem Datum für Maus und Bildschirmleser. */
export function When({ ts, now }: { ts: string; now?: Date }) {
  return (
    <time dateTime={ts} title={fullTime(ts)} className="pf-when">
      <span aria-hidden="true">{listTime(ts, now)}</span>
      <span className="sr-only">{fullTime(ts)}</span>
    </time>
  );
}

export function KindTag({ kind, label }: { kind: string; label: string }) {
  if (kind === 'direct') return null;
  return <span className={`badge ${kind === 'broadcast' ? 'badge-info' : ''}`}>{label}</span>;
}

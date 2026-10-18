/**
 * Alte Adressen (`/postfach…`, `/chats…`, `/mitteilungen`) → neue Adressen unter `/nachrichten`. Rein und getestet;
 * die Seite `LegacyRedirect` leitet damit alte Lesezeichen, Mails und Links weiter. Abfrageparameter bleiben erhalten
 * (z. B. `?lehrkraft=`, `?link=`), `?ordner=` des Postfachs wird zum Filter `?f=`.
 */

const FOLDERS: Record<string, string> = {
  archiv: 'archiv',
  archive: 'archiv',
  entwuerfe: 'entwuerfe',
  entwürfe: 'entwuerfe',
  drafts: 'entwuerfe',
  mitteilungen: 'mitteilungen',
  email: 'email',
  briefe: 'briefe',
  chats: 'chats',
  gruppen: 'gruppen',
};

/** Neue Adresse für eine alte; `null`, wenn die Adresse nicht zu den alten gehört. */
export function legacyTarget(pathname: string, search = ''): string | null {
  const path = pathname.replace(/\/+$/, '') || '/';
  const params = new URLSearchParams(search);
  const rest = (drop: string[] = []) => {
    const p = new URLSearchParams(params);
    for (const k of drop) p.delete(k);
    const s = p.toString();
    return s ? `?${s}` : '';
  };
  if (path === '/mitteilungen') return '/nachrichten?f=mitteilungen';
  const m = /^\/(postfach|chats)(?:\/([^/]+))?(?:\/([^/]+))?$/.exec(path);
  if (!m) return null;
  const [, area, a, b] = m;
  if (!a) {
    const folder = area === 'chats' ? 'chats' : FOLDERS[(params.get('ordner') ?? params.get('f') ?? '').toLowerCase()];
    const p = new URLSearchParams(params);
    p.delete('ordner');
    p.delete('f');
    if (folder) p.set('f', folder);
    const s = p.toString();
    return `/nachrichten${s ? `?${s}` : ''}`;
  }
  if (a === 'neu' && !b) return `/nachrichten/neu${rest()}`;
  if (a === 'einstellungen' && !b) return `/nachrichten/einstellungen${rest()}`;
  if (a === 'moderation' && !b) return area === 'chats' ? `/nachrichten/moderation/chats${rest()}` : `/nachrichten/moderation${rest()}`;
  if (/^\d+$/.test(a) && !b) return `/nachrichten/${area === 'chats' ? 'c' : 'b'}/${a}${rest()}`;
  return '/nachrichten';
}

/**
 * Kleiner, sicherer Markdown-Parser für die Handbuch-Seiten (`docs/hilfe/*.md`). Unterstützt Überschriften (#–###),
 * Absätze, Listen (- und 1.), **fett**, `Code` und Links [Text](Adresse). Liefert eine Baumstruktur statt HTML –
 * die Seite rendert daraus React-Elemente, es wird nie HTML eingesetzt. Links sind nur http(s), mailto oder
 * Pfade der App erlaubt.
 */
export type Inline = { t: 'text'; v: string } | { t: 'strong'; v: Inline[] } | { t: 'code'; v: string } | { t: 'link'; href: string; v: Inline[] };

export type Block =
  | { t: 'h'; level: 1 | 2 | 3; id: string; v: Inline[] }
  | { t: 'p'; v: Inline[] }
  | { t: 'ul'; items: Inline[][] }
  | { t: 'ol'; items: Inline[][] };

export function safeHref(href: string): string | null {
  const h = href.trim();
  if (/^(https?:\/\/|mailto:)/i.test(h)) return h;
  if (h.startsWith('/') && !h.startsWith('//')) return h;
  return null;
}

export function slug(text: string): string {
  return text
    .toLowerCase()
    .replace(/ä/g, 'ae')
    .replace(/ö/g, 'oe')
    .replace(/ü/g, 'ue')
    .replace(/ß/g, 'ss')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export function parseInline(text: string): Inline[] {
  const out: Inline[] = [];
  const re = /(\*\*([^*]+)\*\*)|(`([^`]+)`)|(\[([^\]]+)\]\(([^)\s]+)\))/g;
  let last = 0;
  let m: RegExpExecArray | null;
  const push = (v: string) => {
    if (v) out.push({ t: 'text', v });
  };
  while ((m = re.exec(text))) {
    push(text.slice(last, m.index));
    if (m[1]) out.push({ t: 'strong', v: parseInline(m[2]) });
    else if (m[3]) out.push({ t: 'code', v: m[4] });
    else {
      const href = safeHref(m[7]);
      if (href) out.push({ t: 'link', href, v: parseInline(m[6]) });
      else push(m[6]);
    }
    last = m.index + m[0].length;
  }
  push(text.slice(last));
  return out;
}

export function parseMarkdown(src: string): Block[] {
  const blocks: Block[] = [];
  const lines = src.replace(/\r\n/g, '\n').split('\n');
  let para: string[] = [];
  let list: { kind: 'ul' | 'ol'; items: string[] } | null = null;
  const flushPara = () => {
    if (para.length) blocks.push({ t: 'p', v: parseInline(para.join(' ')) });
    para = [];
  };
  const flushList = () => {
    if (list) blocks.push({ t: list.kind, items: list.items.map(parseInline) });
    list = null;
  };
  for (const raw of lines) {
    const line = raw.trimEnd();
    const h = /^(#{1,3})\s+(.+)$/.exec(line);
    const ul = /^\s*[-*]\s+(.+)$/.exec(line);
    const ol = /^\s*\d+\.\s+(.+)$/.exec(line);
    if (!line.trim()) {
      flushPara();
      flushList();
    } else if (h) {
      flushPara();
      flushList();
      blocks.push({ t: 'h', level: h[1].length as 1 | 2 | 3, id: slug(h[2]), v: parseInline(h[2]) });
    } else if (ul || ol) {
      flushPara();
      const kind = ul ? 'ul' : 'ol';
      if (list && list.kind !== kind) flushList();
      list = list ?? { kind, items: [] };
      list.items.push((ul ?? ol)![1]);
    } else if (list && /^\s{2,}\S/.test(raw)) {
      list.items[list.items.length - 1] += ` ${line.trim()}`;
    } else {
      flushList();
      para.push(line.trim());
    }
  }
  flushPara();
  flushList();
  return blocks;
}

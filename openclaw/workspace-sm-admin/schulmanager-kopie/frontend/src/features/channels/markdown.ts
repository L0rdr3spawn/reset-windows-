/**
 * Kleiner, sicherer Markdown-Leser für Textseiten, Aufgaben und Rückmeldungen (ohne HTML, ohne Bibliothek):
 * Überschriften (#–###), Absätze, Listen (-, *, 1.), Zitate (>), Codeblöcke (```), **fett**, *kursiv* bzw. _kursiv_,
 * `Code`, Links [Text](https://…), nackte Adressen und Formeln (`$x^2$` im Text, `$$…$$` als eigener Block; gesetzt
 * wird mit KaTeX in `MathView.tsx`, hier wird nur erkannt). Ergebnis ist ein Baum – gerendert wird er in
 * `Markdown.tsx` ausschließlich über React-Elemente (kein `dangerouslySetInnerHTML`).
 */
import { safeHref } from './logic';

export type Inline =
  | { t: 'text'; v: string }
  | { t: 'strong'; c: Inline[] }
  | { t: 'em'; c: Inline[] }
  | { t: 'code'; v: string }
  | { t: 'link'; href: string; c: Inline[] }
  | { t: 'math'; v: string; display?: boolean }
  | { t: 'br' };

export type Block =
  | { t: 'h'; level: 1 | 2 | 3; c: Inline[] }
  | { t: 'p'; c: Inline[] }
  | { t: 'ul' | 'ol'; items: Inline[][] }
  | { t: 'quote'; c: Inline[] }
  | { t: 'pre'; v: string }
  | { t: 'math'; v: string };

/** Längste Formel (Zeichen) – Schutz gegen übergroße Eingaben. */
export const MAX_MATH = 1000;

/**
 * Formel ab `$` bei Position `i`: `$$…$$` oder `$…$`. Wie bei Pandoc beginnt `$…$` nicht mit Leerzeichen, endet nicht
 * mit Leerzeichen und darf nicht von einer Ziffer gefolgt werden – „5 $ und 6 $“ bleibt deshalb Text.
 */
export function matchMath(text: string, i: number): { v: string; end: number; display: boolean } | null {
  if (text[i] !== '$') return null;
  if (text.startsWith('$$', i)) {
    const end = text.indexOf('$$', i + 2);
    const v = end > i + 2 ? text.slice(i + 2, end).trim() : '';
    if (v && v.length <= MAX_MATH) return { v, end: end + 2, display: true };
  }
  if (/\s/.test(text[i + 1] ?? ' ') || text[i + 1] === '$') return null;
  for (let j = i + 1; j < text.length && j - i <= MAX_MATH + 1; j++) {
    const c = text[j]!;
    if (c === '\n') return null;
    if (c === '\\') {
      j += 1;
      continue;
    }
    if (c === '$') {
      if (/\s/.test(text[j - 1]!) || /\d/.test(text[j + 1] ?? '')) return null;
      return { v: text.slice(i + 1, j), end: j + 1, display: false };
    }
  }
  return null;
}

const URL_RE = /https?:\/\/[^\s<>()]+[^\s<>().,;:!?'"]/y;

/** Inline-Auszeichnungen (rekursiv für fett/kursiv/Linktext, Tiefe begrenzt). */
export function parseInline(text: string, depth = 0): Inline[] {
  const out: Inline[] = [];
  let buf = '';
  const flush = () => {
    if (buf) out.push({ t: 'text', v: buf });
    buf = '';
  };
  let i = 0;
  while (i < text.length) {
    const ch = text[i]!;
    const rest = text.slice(i);
    if (ch === '\n') {
      flush();
      out.push({ t: 'br' });
      i += 1;
      continue;
    }
    if (ch === '\\' && i + 1 < text.length && '\\`*_[]()#>-$'.includes(text[i + 1]!)) {
      buf += text[i + 1];
      i += 2;
      continue;
    }
    if (ch === '`') {
      const end = text.indexOf('`', i + 1);
      if (end > i + 1) {
        flush();
        out.push({ t: 'code', v: text.slice(i + 1, end) });
        i = end + 1;
        continue;
      }
    }
    if (ch === '$') {
      const m = matchMath(text, i);
      if (m) {
        flush();
        out.push({ t: 'math', v: m.v, display: m.display });
        i = m.end;
        continue;
      }
    }
    if (depth < 4 && (rest.startsWith('**') || rest.startsWith('__'))) {
      const mark = rest.slice(0, 2);
      const end = text.indexOf(mark, i + 2);
      if (end > i + 2) {
        flush();
        out.push({ t: 'strong', c: parseInline(text.slice(i + 2, end), depth + 1) });
        i = end + 2;
        continue;
      }
    }
    if (depth < 4 && (ch === '*' || ch === '_') && text[i + 1] !== ' ' && text[i + 1] !== ch) {
      // _ nur am Wortanfang (snake_case bleibt Text)
      const before = i > 0 ? text[i - 1]! : ' ';
      if (ch === '*' || !/[\p{L}\p{N}]/u.test(before)) {
        const end = text.indexOf(ch, i + 1);
        if (end > i + 1 && text[end - 1] !== ' ') {
          flush();
          out.push({ t: 'em', c: parseInline(text.slice(i + 1, end), depth + 1) });
          i = end + 1;
          continue;
        }
      }
    }
    if (ch === '[') {
      const close = text.indexOf('](', i + 1);
      const end = close > 0 ? text.indexOf(')', close + 2) : -1;
      if (close > i && end > close) {
        const href = safeHref(text.slice(close + 2, end).trim());
        if (href) {
          flush();
          out.push({ t: 'link', href, c: parseInline(text.slice(i + 1, close), depth + 1) });
          i = end + 1;
          continue;
        }
      }
    }
    if (ch === 'h' && (rest.startsWith('http://') || rest.startsWith('https://'))) {
      const before = i > 0 ? text[i - 1]! : ' ';
      if (!/[\p{L}\p{N}]/u.test(before)) {
        URL_RE.lastIndex = i;
        const m = URL_RE.exec(text);
        const href = m ? safeHref(m[0]) : null;
        if (m && href) {
          flush();
          out.push({ t: 'link', href, c: [{ t: 'text', v: m[0] }] });
          i += m[0].length;
          continue;
        }
      }
    }
    buf += ch;
    i += 1;
  }
  flush();
  return out;
}

const UL_RE = /^\s{0,3}[-*+]\s+(.*)$/;
const OL_RE = /^\s{0,3}\d{1,3}[.)]\s+(.*)$/;
const H_RE = /^(#{1,3})\s+(.*?)\s*#*\s*$/;

/** Text → Blöcke. */
export function parseMarkdown(src: string): Block[] {
  const lines = (src || '').replace(/\r\n?/g, '\n').split('\n');
  const blocks: Block[] = [];
  let para: string[] = [];
  const flushPara = () => {
    if (para.length) blocks.push({ t: 'p', c: parseInline(para.join('\n').trim()) });
    para = [];
  };
  let i = 0;
  while (i < lines.length) {
    const line = lines[i]!;
    if (/^\s*```/.test(line)) {
      flushPara();
      const code: string[] = [];
      i += 1;
      while (i < lines.length && !/^\s*```/.test(lines[i]!)) {
        code.push(lines[i]!);
        i += 1;
      }
      blocks.push({ t: 'pre', v: code.join('\n') });
      i += 1;
      continue;
    }
    if (!line.trim()) {
      flushPara();
      i += 1;
      continue;
    }
    if (/^\s*\$\$/.test(line)) {
      // Formelblock: `$$ … $$` in einer Zeile oder über mehrere Zeilen bis zum schließenden `$$`
      const first = line.trim().slice(2);
      const closeAt = first.indexOf('$$');
      let tex: string | null = null;
      let next = i + 1;
      if (closeAt >= 0 && !first.slice(closeAt + 2).trim()) {
        tex = first.slice(0, closeAt);
      } else if (closeAt < 0) {
        const body = [first];
        let j = i + 1;
        while (j < lines.length && j - i <= 40) {
          const l = lines[j]!;
          const end = l.indexOf('$$');
          if (end >= 0) {
            if (!l.slice(end + 2).trim()) {
              body.push(l.slice(0, end));
              tex = body.join('\n');
              next = j + 1;
            }
            break;
          }
          if (!l.trim()) break;
          body.push(l);
          j += 1;
        }
      }
      if (tex !== null && tex.trim() && tex.length <= MAX_MATH) {
        flushPara();
        blocks.push({ t: 'math', v: tex.trim() });
        i = next;
        continue;
      }
    }
    const h = H_RE.exec(line);
    if (h) {
      flushPara();
      blocks.push({ t: 'h', level: h[1]!.length as 1 | 2 | 3, c: parseInline(h[2]!) });
      i += 1;
      continue;
    }
    if (UL_RE.test(line) || OL_RE.test(line)) {
      flushPara();
      const ordered = !UL_RE.test(line);
      const re = ordered ? OL_RE : UL_RE;
      const items: Inline[][] = [];
      while (i < lines.length && re.test(lines[i]!)) {
        let text = re.exec(lines[i]!)![1]!;
        i += 1;
        // eingerückte Folgezeilen gehören zum Listenpunkt
        while (i < lines.length && /^\s{2,}\S/.test(lines[i]!) && !UL_RE.test(lines[i]!) && !OL_RE.test(lines[i]!)) {
          text += `\n${lines[i]!.trim()}`;
          i += 1;
        }
        items.push(parseInline(text));
      }
      blocks.push({ t: ordered ? 'ol' : 'ul', items });
      continue;
    }
    if (/^\s{0,3}>\s?/.test(line)) {
      flushPara();
      const quote: string[] = [];
      while (i < lines.length && /^\s{0,3}>\s?/.test(lines[i]!)) {
        quote.push(lines[i]!.replace(/^\s{0,3}>\s?/, ''));
        i += 1;
      }
      blocks.push({ t: 'quote', c: parseInline(quote.join('\n')) });
      continue;
    }
    para.push(line);
    i += 1;
  }
  flushPara();
  return blocks;
}

/** Reiner Text (z. B. für Vorschauen): Auszeichnungen entfernt. */
export function plainText(src: string, max = 160): string {
  const walk = (nodes: Inline[]): string =>
    nodes.map((n) => (n.t === 'text' || n.t === 'code' || n.t === 'math' ? n.v : n.t === 'br' ? ' ' : 'c' in n ? walk(n.c) : '')).join('');
  const text = parseMarkdown(src)
    .map((b) => (b.t === 'pre' || b.t === 'math' ? b.v : 'items' in b ? b.items.map(walk).join(' · ') : walk(b.c)))
    .join(' ')
    .replace(/\s+/g, ' ')
    .trim();
  return text.length > max ? `${text.slice(0, max - 1).trimEnd()}…` : text;
}

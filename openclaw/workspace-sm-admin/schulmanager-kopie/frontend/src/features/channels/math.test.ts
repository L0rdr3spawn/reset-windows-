import { describe, expect, it } from 'vitest';
import { matchMath, parseInline, parseMarkdown, plainText } from './markdown';

describe('Formeln im Markdown', () => {
  it('erkennt Formeln im Text', () => {
    expect(parseInline('Es gilt $a^2+b^2=c^2$ im Dreieck.')).toEqual([
      { t: 'text', v: 'Es gilt ' },
      { t: 'math', v: 'a^2+b^2=c^2', display: false },
      { t: 'text', v: ' im Dreieck.' },
    ]);
  });

  it('Geldbeträge bleiben Text (Leerzeichen, Ziffer danach, einzelnes Zeichen)', () => {
    for (const s of ['Das kostet 5 $ und 6 $ zusammen', 'Preis $5 und $10', 'nur ein $ hier', 'a $ b$ c']) {
      expect(parseInline(s).some((n) => n.t === 'math')).toBe(false);
    }
  });

  it('maskiertes Dollarzeichen und Code bleiben Text', () => {
    expect(parseInline('\\$x\\$')).toEqual([{ t: 'text', v: '$x$' }]);
    expect(parseInline('`$x$`')).toEqual([{ t: 'code', v: '$x$' }]);
  });

  it('Formelblock in einer Zeile und über mehrere Zeilen', () => {
    expect(parseMarkdown('$$\\frac{1}{2}$$')).toEqual([{ t: 'math', v: '\\frac{1}{2}' }]);
    const multi = parseMarkdown('Vorher\n\n$$\nx = 1\ny = 2\n$$\n\nNachher');
    expect(multi.map((b) => b.t)).toEqual(['p', 'math', 'p']);
    expect(multi[1]).toEqual({ t: 'math', v: 'x = 1\ny = 2' });
  });

  it('nicht geschlossener Block bleibt Text', () => {
    expect(parseMarkdown('$$ offen\nweiter').some((b) => b.t === 'math')).toBe(false);
  });

  it('HTML in der Formel wird nie zu Auszeichnung (nur Quelltext für KaTeX)', () => {
    const n = parseInline('$<img src=x onerror=alert(1)>$')[0]!;
    expect(n).toEqual({ t: 'math', v: '<img src=x onerror=alert(1)>', display: false });
  });

  it('übergroße Formeln werden nicht gesetzt', () => {
    expect(matchMath(`$${'x'.repeat(1200)}$`, 0)).toBeNull();
  });

  it('Klartext-Vorschau zeigt den Formeltext', () => {
    expect(plainText('Wert $x^2$ ok')).toBe('Wert x^2 ok');
  });
});

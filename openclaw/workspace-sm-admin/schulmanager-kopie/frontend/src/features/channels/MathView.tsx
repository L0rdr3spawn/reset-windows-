/**
 * Formelsatz mit KaTeX (lokal gebündelt, kein CDN). Die Bibliothek und ihr Stylesheet werden erst geladen, wenn
 * ein Text wirklich eine Formel enthält. Gesetzt wird mit `katex.render` direkt ins Element – ohne HTML-Zeichenkette,
 * ohne `trust` (keine Links, kein `\href`, keine Bilder), mit Grenzen für Größe und Makro-Erweiterung.
 */
import { useEffect, useRef, useState } from 'react';
import './lernen-math.css';

type Katex = typeof import('katex');
let loader: Promise<Katex> | null = null;

function loadKatex(): Promise<Katex> {
  loader ??= Promise.all([import('katex'), import('katex/dist/katex.min.css')]).then(([m]) => m);
  return loader;
}

export const KATEX_OPTIONS = { throwOnError: false, trust: false, strict: 'ignore', maxSize: 20, maxExpand: 300, output: 'htmlAndMathml' } as const;

export function MathView({ tex, display = false }: { tex: string; display?: boolean }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    let alive = true;
    const el = ref.current;
    loadKatex()
      .then((k) => {
        if (!alive || !el) return;
        try {
          k.render(tex, el, { ...KATEX_OPTIONS, displayMode: display });
          setReady(true);
        } catch {
          setReady(false);
        }
      })
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, [tex, display]);
  // Solange KaTeX lädt (oder falls es nicht lädt) bleibt der Quelltext der Formel lesbar stehen.
  return (
    <span className={`kr-math${display ? ' kr-math-display' : ''}`} data-ready={ready ? 'true' : undefined}>
      {!ready && <code className="kr-math-src">{display ? `$$${tex}$$` : `$${tex}$`}</code>}
      <span ref={ref} hidden={!ready} />
    </span>
  );
}

export default MathView;

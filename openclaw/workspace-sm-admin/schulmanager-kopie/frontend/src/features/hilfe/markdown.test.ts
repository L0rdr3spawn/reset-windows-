import { describe, expect, it } from 'vitest';
import { parseInline, parseMarkdown, safeHref, slug } from './markdown';

describe('Markdown für das Handbuch', () => {
  it('erkennt Überschriften, Absätze und Listen', () => {
    const b = parseMarkdown('# Titel\n\nEin Satz\nüber zwei Zeilen.\n\n1. eins\n2. zwei\n\n- a\n- b');
    expect(b.map((x) => x.t)).toEqual(['h', 'p', 'ol', 'ul']);
    expect(b[1]).toEqual({ t: 'p', v: [{ t: 'text', v: 'Ein Satz über zwei Zeilen.' }] });
    expect((b[2] as { items: unknown[] }).items).toHaveLength(2);
  });

  it('wandelt Auszeichnungen um', () => {
    expect(parseInline('**fett** und `code`')).toEqual([
      { t: 'strong', v: [{ t: 'text', v: 'fett' }] },
      { t: 'text', v: ' und ' },
      { t: 'code', v: 'code' },
    ]);
  });

  it('lässt nur sichere Links zu', () => {
    expect(safeHref('https://schule.de')).toBe('https://schule.de');
    expect(safeHref('/betrieb')).toBe('/betrieb');
    expect(safeHref('javascript:alert(1)')).toBeNull();
    expect(safeHref('//evil.example')).toBeNull();
    const inl = parseInline('[x](javascript:alert(1)) [ok](/daten)');
    expect(inl[0]).toEqual({ t: 'text', v: 'x' });
    expect(inl[2]).toMatchObject({ t: 'link', href: '/daten' });
  });

  it('setzt kein HTML ein', () => {
    const b = parseMarkdown('<script>alert(1)</script>');
    expect(b[0]).toEqual({ t: 'p', v: [{ t: 'text', v: '<script>alert(1)</script>' }] });
  });

  it('bildet Anker', () => {
    expect(slug('Für Lehrkräfte & mehr')).toBe('fuer-lehrkraefte-mehr');
  });

  it('hängt eingerückte Folgezeilen an den Listenpunkt', () => {
    const b = parseMarkdown('- erster\n  weiter\n- zweiter');
    expect(b[0]).toMatchObject({ t: 'ul' });
    expect((b[0] as { items: unknown[][] }).items[0]).toEqual([{ t: 'text', v: 'erster weiter' }]);
  });
});

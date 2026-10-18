/**
 * Regression „Attest einreichen: kann nicht draufklicken“: Der Einreichen-Dialog (Attest, Entschuldigung, Antrag,
 * Unterlagen nachreichen) darf von Meldungen (Toasts), der Rückgängig-Leiste und doppelten IDs nicht blockiert werden.
 * Läuft in Node ohne DOM: prüft Quelltext und Stylesheets.
 */
import { describe, expect, it } from 'vitest';

/** Datei roh lesen (vitest läuft in Node; CSS-Importe liefert vitest ohne Verarbeitung leer). */
async function read(rel: string): Promise<string> {
  const fs = (await import(/* @vite-ignore */ `node:${'fs'}`)) as { readFileSync: (p: URL, enc: 'utf8') => string };
  return fs.readFileSync(new URL(rel, import.meta.url), 'utf8');
}

describe('Einreichen-Dialog', () => {
  it('SubmitDocumentForm vergibt eigene IDs (kein doppeltes st-cat/st-abs/st-title/st-note im Dialog und im Dokumente-Bereich)', async () => {
    const components = await read('./components.tsx');
    expect(components).toContain('useId()');
    for (const id of ['st-cat', 'st-abs', 'st-title', 'st-note']) expect(components).not.toMatch(new RegExp(`(id|htmlFor)="${id}"`));
  });

  it('Einreichen-Leiste klebt unten im Dialog und ein Hinweis nennt den nächsten Schritt', async () => {
    const components = await read('./components.tsx');
    const studentsCss = await read('./students.css');
    expect(components).toContain('st-submit-bar');
    expect(components).toContain('Erst die Datei hochladen');
    expect(studentsCss).toMatch(/\.modal-body \.st-submit-bar\s*\{[^}]*position:\s*sticky;[^}]*bottom:\s*0/);
  });

  it('Meldungen (Toasts, liegen über dem Dialog) wandern bei offenem Dialog nach oben statt auf den Knopf', async () => {
    const appCss = await read('../../styles/app.css');
    expect(appCss).toMatch(/body:has\(\.modal-backdrop\) \.toasts\s*\{[^}]*top:[^}]*bottom:\s*auto/);
  });

  it('Rückgängig-Leiste: Seite bekommt Platz darunter', async () => {
    const studentsCss = await read('./students.css');
    expect(studentsCss).toMatch(/body:has\(\.st-undo\) \.app-main\s*\{\s*padding-bottom/);
  });
});

/**
 * R2-D: Kernpfade (U-76), Bewegungs-Token und gültige CSS-Schatten (U-77), „Kein Zugriff“ im App-Rahmen (U-38).
 * CSS und App.tsx werden als Text gelesen (vitest liefert CSS-Importe leer, App braucht ein DOM).
 */
import { describe, expect, it, vi } from 'vitest';
import { CORE_PATHS, loadModules } from '../../features/registry';

const APP = (import.meta.glob('../../App.tsx', { query: '?raw', import: 'default', eager: true }) as Record<string, string>)['../../App.tsx'] ?? '';
/** alle CSS-Dateien unter src/ (nur die Namen; Inhalt per node:fs, weil vitest CSS-Importe leer liefert) */
const CSS_FILES = Object.keys(import.meta.glob('../../**/*.css'));

async function readCss(rel: string): Promise<string> {
  const fs = (await import(/* @vite-ignore */ `node:${'fs'}`)) as { readFileSync: (p: URL, enc: 'utf8') => string };
  return fs.readFileSync(new URL(rel, import.meta.url), 'utf8');
}

describe('Kernpfade (U-76)', () => {
  const PUBLIC = ['/passwort-vergessen', '/passwort-zuruecksetzen', '/test-postausgang', '/konten-verbinden'];

  it('öffentliche bzw. direkt verdrahtete Seiten sind Kernpfade', () => {
    for (const p of PUBLIC) expect(CORE_PATHS.has(p), p).toBe(true);
  });

  it('ein Feature kann sie nicht belegen', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    const el = null;
    const mods = loadModules({
      './dieb/module.tsx': { default: { id: 'dieb', routes: PUBLIC.map((path) => ({ path, element: el })).concat([{ path: '/dieb', element: el }]) } },
    });
    warn.mockRestore();
    expect(mods[0]?.routes?.map((r) => r.path)).toEqual(['/dieb']);
  });

  it('jede öffentliche Route in App.tsx steht in CORE_PATHS', () => {
    const app = APP;
    const top = [...app.matchAll(/<Route\s+path="(\/[a-z-]+)/g)].map((m) => m[1] as string);
    expect(top.length).toBeGreaterThan(5);
    for (const p of top) expect(CORE_PATHS.has(`/${p.split('/')[1]}`), p).toBe(true);
  });
});

describe('CSS (U-77)', () => {
  it('--motion hat einen Standardwert mit Zeiteinheit und 0s bei „Bewegung reduzieren“', async () => {
    const tokens = await readCss('../../styles/tokens.css');
    const root = tokens.slice(tokens.indexOf(':root {'), tokens.indexOf('}', tokens.indexOf(':root {')));
    expect(root).toMatch(/--motion:\s*\d+m?s;/);
    const reduced = tokens.slice(tokens.indexOf('prefers-reduced-motion'));
    expect(reduced).toMatch(/--motion:\s*0s;/);
    expect(tokens).not.toMatch(/--motion:\s*0;/);
  });

  it('kein box-shadow mit „dashed“ (ungültig, Deklaration wird verworfen)', async () => {
    expect(CSS_FILES.length).toBeGreaterThan(4);
    for (const f of CSS_FILES) {
      const bad = (await readCss(f)).match(/box-shadow:[^;]*\bdashed\b/);
      expect(bad, f).toBeNull();
    }
  });
});

describe('„Kein Zugriff“ im App-Rahmen (U-38)', () => {
  it('die Rechte der Layout-Seiten prüft AccessGate innerhalb von AppLayout', () => {
    const app = APP;
    const layout = app.indexOf('<Guard inFrame>');
    const gate = app.indexOf('<Route element={<AccessGate />}>');
    expect(layout).toBeGreaterThan(0);
    expect(gate).toBeGreaterThan(layout);
    expect(app.slice(layout, gate)).toContain('<AppLayout />');
    // Rückweg ohne Neuladen der Seite (Zwischenspeicher bleiben konsistent, kein Blitzen)
    expect(app).not.toMatch(/<a className="btn[^"]*" href="\/"/);
  });
});

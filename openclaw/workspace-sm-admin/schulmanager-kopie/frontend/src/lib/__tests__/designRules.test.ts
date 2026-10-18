/**
 * Gestaltungsregel (docs/DESIGN.md §7): keine neuen erklärenden Absätze (`className="explain"`) auf Seiten – Hilfe
 * gehört an die Beschriftung (`Field help=`, `HelpText`, `PageHelp`). Der Bestand ist als Obergrenze je Datei
 * erfasst und soll mit jeder Design-Runde schrumpfen; neue Dateien dürfen keine Erklärabsätze enthalten.
 */
import { describe, expect, it } from 'vitest';

/** Quelltexte aller .tsx-Dateien (Vite/vitest liest sie zur Testzeit ein; Schlüssel relativ zu src/). */
const SOURCES: Record<string, string> = Object.fromEntries(
  Object.entries(import.meta.glob('../../**/*.tsx', { query: '?raw', import: 'default', eager: true }) as Record<string, string>).map(
    ([path, text]) => [path.replace(/^\.\.\/\.\.\//, ''), text],
  ),
);

/** Stylesheet roh lesen (vitest läuft in Node; CSS-Importe liefert vitest ohne Verarbeitung leer). */
async function readStyle(name: string): Promise<string> {
  const fs = (await import(/* @vite-ignore */ `node:${'fs'}`)) as { readFileSync: (p: URL, enc: 'utf8') => string };
  return fs.readFileSync(new URL(`../../styles/${name}`, import.meta.url), 'utf8');
}

/** Inhalte aller `@media …`-Blöcke mit genau dieser Bedingung (Klammern gezählt). */
function mediaBlocks(css: string, query: string): string[] {
  const out: string[] = [];
  let at = css.indexOf(query);
  while (at >= 0) {
    const open = css.indexOf('{', at);
    let depth = 0;
    let end = open;
    for (; end < css.length; end++) {
      if (css[end] === '{') depth++;
      else if (css[end] === '}' && --depth === 0) break;
    }
    out.push(css.slice(open + 1, end));
    at = css.indexOf(query, end);
  }
  return out;
}

/** Bestand Stand R1-D1 (10.10.2026) – Werte nur senken, nie erhöhen. */
const EXPLAIN_BASELINE: Record<string, number> = {
  // keine Datei mit Bestand (Planung: 0 seit 16.10.2026)
};

/**
 * Lange Erklärsätze gehören ins (i): `<p className="muted|hint|small|xsmall|explain">` mit mehr als 12 Wörtern festen
 * Texts (ohne `{…}`-Ausdrücke und ohne HelpTip/PageHelp darin) sind verboten. Ausnahmen mit Begründung:
 * Pflichthinweise (Datenschutz, Einwilligung), Fehler- und Leerzustände sowie Texte in Dateien, die gerade andere überarbeiten.
 */
const LONG_TEXT_WORDS = 12;
const LONG_TEXT_EXCEPTIONS: Record<string, string> = {
  'features/chats/PrivacyPage.tsx': 'Datenschutzerklärung (rechtlich erforderlicher Text)',
  'pages/AccessLettersPage.tsx': 'gedruckter Zugangsbrief, kein Bedienelement',
  'features/chats/ChatsPage.tsx': 'Hinweis zur Weitergabe beim Melden (Einwilligung)',
  'features/chats/DevicesPanel.tsx': 'Sicherheitshinweis zum Wiederherstellungs-Backup',
  'features/schuljahreswechsel/WechselPage.tsx': 'Warnung vor einer folgenreichen Aktion',
  'components/FileUpload.tsx': 'Fehlerzustand',
  'features/channels/widgets.tsx': 'Leerzustand mit Handlungshinweis',
  'features/konto/ContactSection.tsx': 'Einwilligung zur Bestätigung von Kontaktdaten',
  'features/students/ReportCard.tsx': 'Status mit Pflichthinweis (Attest nötig)',
  'features/students/DocumentsPage.tsx': 'Datenschutzhinweis zu Gesundheitsdaten',
  'features/channels/VisibilityPicker.tsx': 'Statuszeile',
  'pages/planning/CurriculaEditor.tsx': 'Stundentafeln werden gerade von einem anderen Agenten überarbeitet',
  'pages/SetupPage.tsx': 'Status des Einrichtungsassistenten',
  'features/anmeldedienste/SetupPage.tsx': 'Warnung zu Skripten Dritter (innerhalb der Hilfe)',
};

export function longExplainParagraphs(rel: string, text: string): string[] {
  if (Object.keys(LONG_TEXT_EXCEPTIONS).some((k) => rel.startsWith(k))) return [];
  const out: string[] = [];
  const re = /<p\s+className="([^"]*)"[^>]*>([\s\S]*?)<\/p>/g;
  for (const m of text.matchAll(re)) {
    if (!/\b(muted|hint|small|xsmall|explain)\b/.test(m[1])) continue;
    if (m[2].includes('`')) continue; // dynamische Texte (Template-Strings) sind keine festen Erklärsätze
    const inner = m[2]
      .replace(/<HelpTip[\s\S]*?<\/HelpTip>/g, ' ')
      .replace(/<PageHelp[\s\S]*?<\/PageHelp>/g, ' ')
      .replace(/\{[^}]*\}/g, ' ')
      .replace(/<[^>]+>/g, ' ');
    const words = inner.split(/\s+/).filter(Boolean).length;
    if (words > LONG_TEXT_WORDS) out.push(`${rel}: ${words} Wörter – „${inner.trim().slice(0, 50)} …“`);
  }
  return out;
}

describe('Gestaltungsregeln', () => {
  it('keine neuen Erklärabsätze (className="explain")', () => {
    const over: string[] = [];
    expect(Object.keys(SOURCES).length).toBeGreaterThan(50);
    for (const [rel, text] of Object.entries(SOURCES)) {
      const count = (text.match(/className="explain"/g) ?? []).length;
      const allowed = EXPLAIN_BASELINE[rel] ?? 0;
      if (count > allowed) over.push(`${rel}: ${count} (erlaubt ${allowed}) – Hilfe an die Beschriftung, siehe docs/DESIGN.md`);
    }
    expect(over).toEqual([]);
  });

  it('Referenzseiten (Anmeldung, Start, Profil) ohne Erklärabsätze', () => {
    for (const rel of ['pages/LoginPage.tsx', 'pages/DashboardPage.tsx', 'pages/ProfilePage.tsx']) {
      const text = SOURCES[rel];
      expect(text, rel).toBeTypeOf('string');
      expect(text, rel).not.toMatch(/className="explain"/);
    }
  });
});

describe('Gestaltungsregeln: Beschreibungen im (i)', () => {
  it('keine langen Erklär-Absätze (muted/hint/small) außerhalb der Hilfe-Bausteine', () => {
    const found = Object.entries(SOURCES).flatMap(([rel, text]) => longExplainParagraphs(rel, text));
    expect(found).toEqual([]);
  });

  it('die Prüfung erkennt einen langen Absatz und lässt die Hilfe zu', () => {
    const long = '<p className="small muted">eins zwei drei vier fünf sechs sieben acht neun zehn elf zwölf dreizehn</p>';
    expect(longExplainParagraphs('x/Neu.tsx', long)).toHaveLength(1);
    const ok = '<p className="small muted">Kurz<HelpTip>eins zwei drei vier fünf sechs sieben acht neun zehn elf zwölf dreizehn</HelpTip></p>';
    expect(longExplainParagraphs('x/Neu.tsx', ok)).toEqual([]);
  });
});

describe('Gestaltungsregeln: App-Rahmen (Prüfung R1-D1)', () => {
  it('Druck: untere Leiste und offene Hilfe werden nicht gedruckt', async () => {
    const print = mediaBlocks(await readStyle('print.css'), '@media print').join('\n');
    const hidden = print.slice(0, print.indexOf('display: none'));
    expect(hidden).toContain('.bottom-nav');
    expect(hidden).toContain('.help-pop');
  });

  it('Handy: Meldungen (Toasts) liegen über der unteren Leiste', async () => {
    const phone = mediaBlocks(await readStyle('app.css'), '@media (max-width: 599.98px)').join('\n');
    expect(phone).toMatch(/\.toasts\s*\{[^}]*bottom:\s*calc\(var\(--bottom-nav-h\)/);
  });

  it('Touch: Name mit Hilfe hat eine vergrößerte Trefferfläche', async () => {
    const coarse = mediaBlocks(await readStyle('app.css'), '@media (pointer: coarse)').join('\n');
    expect(coarse).toMatch(/\.help-trigger\s*\{[^}]*padding-block/);
  });
});

/** Alle Stylesheets unter src/ roh (vitest liefert CSS-Importe leer, daher per fs; Schlüssel relativ zu src/). */
async function readAllStyles(): Promise<Record<string, string>> {
  const fs = (await import(/* @vite-ignore */ `node:${'fs'}`)) as {
    readdirSync: (p: URL, o: { withFileTypes: true }) => { name: string; isDirectory: () => boolean }[];
    readFileSync: (p: URL, enc: 'utf8') => string;
  };
  const out: Record<string, string> = {};
  const walk = (rel: string) => {
    for (const e of fs.readdirSync(new URL(`../../${rel}`, import.meta.url), { withFileTypes: true })) {
      const sub = `${rel}${e.name}`;
      if (e.isDirectory()) walk(`${sub}/`);
      else if (e.name.endsWith('.css')) out[sub] = fs.readFileSync(new URL(`../../${sub}`, import.meta.url), 'utf8');
    }
  };
  walk('');
  return out;
}

/**
 * Gestaltungsregel (docs/DESIGN.md §10a): Ansichten „Tage × Stunden“ gibt es nur über `components/grid/DayPeriodGrid`
 * (das Stundenplan-Raster). Eigene Raster – CSS-Grid mit Tagesspalten, Tabelle mit Wochentagen im Kopf, Klassen `tt-*`
 * von Hand – sind verboten. Ausnahmen nur hier eintragen (mit Begründung) und nur in Ausnahmefällen.
 */
const GRID_BUILDING_BLOCK = 'components/grid/DayPeriodGrid.tsx';
const GRID_EXCEPTIONS: Record<string, string> = {};
const GRID_STYLE_OWNER = 'styles/timetable.css';
/** Weitere Stylesheets, die das Raster nur ergänzen (Wochen-/Ferientage, Druck). */
const GRID_STYLE_EXTENSIONS = ['components/weeks.css', 'styles/print.css'];

describe('Gestaltungsregeln: Tage×Stunden-Raster nur über DayPeriodGrid', () => {
  it('keine handgebauten Raster in .tsx (Tagesspalten per grid-template-columns, Wochentage im Tabellenkopf, tt-*-Klassen)', () => {
    const bad: string[] = [];
    for (const [rel, text] of Object.entries(SOURCES)) {
      if (rel === GRID_BUILDING_BLOCK || rel in GRID_EXCEPTIONS || rel.includes('__tests__') || /\.test\.tsx$/.test(rel)) continue;
      if (/gridTemplateColumns:\s*`[^`]*\$\{[^}]*\b(days|weekdays|dayCount)\b[^}]*\}/i.test(text)) bad.push(`${rel}: grid-template-columns mit Tagesspalten`);
      if (/role="columnheader"/.test(text)) bad.push(`${rel}: eigenes Raster mit role="columnheader"`);
      if (/<th\b[^>]*>\s*(?:<[^>]+>\s*)*\{WEEKDAYS(?:_SHORT)?\[/.test(text)) bad.push(`${rel}: Tabelle mit Wochentagen im Kopf`);
      if (/className=["'{`][^"'}`]*\btt-(grid|slot|time|head|scroll)\b/.test(text)) bad.push(`${rel}: tt-*-Klassen von Hand`);
    }
    expect(bad, 'Tage×Stunden-Ansichten gehören in DayPeriodGrid (docs/DESIGN.md §10a)').toEqual([]);
  });

  it('keine eigenen Raster-Stylesheets (alte Klassen kl-week, wg-table, duty-week, tp-avail, rule-preview)', async () => {
    const styles = await readAllStyles();
    expect(Object.keys(styles).length).toBeGreaterThan(5);
    const bad: string[] = [];
    for (const [rel, text] of Object.entries(styles)) {
      if (/(^|[\s,}])\.(kl-week|wg-table|wg-cell|duty-week|duty-grid|tp-avail|rule-preview)\b(?!-)/m.test(text.replace(/\.kl-week-(tools|label|wrap|nav)/g, ''))) bad.push(`${rel}: altes Eigenbau-Raster`);
      if (rel !== GRID_STYLE_OWNER && !GRID_STYLE_EXTENSIONS.includes(rel) && /\.tt-(grid|slot)\b/.test(text)) bad.push(`${rel}: .tt-grid/.tt-slot gehören nur nach ${GRID_STYLE_OWNER}`);
      if (rel !== GRID_STYLE_OWNER && /grid-template-columns:[^;]*var\(--days/.test(text)) bad.push(`${rel}: Tagesspalten per CSS-Variable`);
    }
    expect(bad).toEqual([]);
  });

  it('umgestellte Ansichten nutzen den Baustein', () => {
    for (const rel of [
      'components/TimetableGrid.tsx',
      'components/RuleEditor.tsx',
      'features/students/AbsenceStats.tsx',
      'features/teacher/AvailabilityEditor.tsx',
      'features/duties/DutyOverviewView.tsx',
      'features/classes/WeekTab.tsx',
    ]) {
      expect(SOURCES[rel], rel).toMatch(/grid\/DayPeriodGrid|\.\/grid\/DayPeriodGrid/);
    }
  });
});

/**
 * Keine nativen Browser-Popups: `window.confirm`/`alert`/`prompt` sind nicht gestaltbar und werden in eingebetteten
 * Browsern abgebrochen. Bestätigungen laufen über `AsyncButton confirm=`, `confirmAsk()`/`useConfirm()`
 * (`lib/confirm.ts`) oder `ConfirmDialog`; Texteingaben über `promptAsk()`. `beforeunload` (Browser-Dialog beim
 * Schließen/Neuladen) nur in den unten begründeten Dateien.
 */
const NATIVE_DIALOG_EXCEPTIONS: Record<string, string> = {
};
const BEFOREUNLOAD_ALLOWED: Record<string, string> = {
  'features/channels/MaterialUpload.tsx': 'laufende Datei-Uploads gehen beim Schließen/Neuladen verloren',
};

describe('Gestaltungsregeln: keine nativen Browser-Popups', () => {
  const ALL: Record<string, string> = Object.fromEntries(
    Object.entries(import.meta.glob('../../**/*.{ts,tsx}', { query: '?raw', import: 'default', eager: true }) as Record<string, string>)
      .map(([path, text]) => [path.replace(/^\.\.\/\.\.\//, ''), text])
      .filter(([path]) => !/\.test\.tsx?$/.test(path as string) && !(path as string).startsWith('lib/__tests__/')),
  );
  const strip = (t: string) => t.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/.*$/gm, '$1');

  it('kein window.confirm/alert/prompt außerhalb begründeter Ausnahmen', () => {
    const hits = Object.entries(ALL)
      .filter(([path, text]) => !(path in NATIVE_DIALOG_EXCEPTIONS) && /(?:window\.|(?<![.\w$]))(?:confirm|alert|prompt)\s*\(\s*[^)\s]/.test(strip(text)))
      .map(([path]) => path);
    expect(hits).toEqual([]);
  });

  it('beforeunload nur in begründeten Dateien', () => {
    const hits = Object.entries(ALL)
      .filter(([path, text]) => !(path in BEFOREUNLOAD_ALLOWED) && !(path in NATIVE_DIALOG_EXCEPTIONS) && strip(text).includes('beforeunload'))
      .map(([path]) => path);
    expect(hits).toEqual([]);
  });
});

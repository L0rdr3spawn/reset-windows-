/**
 * Schülerliste einfügen (Klassen-Assistent, §11.3) – reine Logik, ohne React.
 *
 * Erkannte Formate (je Zeile eine Person, Leerzeilen werden übersprungen):
 * * Tabelle aus Excel/Word (Tabulator) oder CSV mit `;` – optional mit Kopfzeile. Spalten über die Kopfzeile:
 *   Nachname, Vorname, Name (ganzer Name), E-Mail, Geburtsdatum, volljährig, Eltern/Elternteil 1|2 (Name),
 *   E-Mail Eltern/Elternteil 1|2; unbekannte Spalten (Klasse, Nr. …) werden ignoriert.
 *   Ohne Kopfzeile: Text-Spalten = „Nachname, Vorname“, Zellen mit `@` = E-Mail, Datumsangaben = Geburtsdatum,
 *   „ja/x/volljährig“ = volljährig, reine Zahlen (laufende Nummer) werden ignoriert.
 * * „Nachname, Vorname“ je Zeile (Komma).
 * * „Vorname Nachname“ je Zeile (Namenszusätze wie „von der“ gehören zum Nachnamen), optional mit E-Mail und Datum.
 * Namen IN GROSSBUCHSTABEN werden in normale Schreibweise gebracht („MÜLLER-LÜDENSCHEIDT“ → „Müller-Lüdenscheidt“).
 */

export interface ParentDraft {
  name: string;
  email: string;
}

export interface StudentDraft {
  /** stabiler Schlüssel für Listen */
  key: string;
  /** Zeile im eingefügten Text (1-basiert), 0 = von Hand ergänzt */
  line: number;
  first_name: string;
  last_name: string;
  email: string;
  /** ISO-Datum oder leer */
  birth_date: string;
  /** nur maßgeblich ohne Geburtsdatum */
  adult: boolean;
  /** höchstens zwei */
  parents: ParentDraft[];
}

export interface ParseResult {
  rows: StudentDraft[];
  header: boolean;
  format: 'tabelle' | 'komma' | 'text' | 'leer';
  /** erkannte Spalten (Kopfzeile) bzw. Hinweis */
  columns: string[];
}

export interface RowCheck {
  errors: string[];
  warnings: string[];
}

export const MAX_STUDENTS = 60;
export const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const PARTICLES = new Set([
  'von',
  'vom',
  'van',
  'de',
  'der',
  'den',
  'del',
  'della',
  'di',
  'da',
  'du',
  'dos',
  'das',
  'zu',
  'zur',
  'zum',
  'ten',
  'ter',
  'la',
  'le',
  'el',
  'al',
  'bin',
  'ben',
  'ibn',
  'y',
  'op',
]);
const YES = new Set(['ja', 'j', 'x', 'yes', 'y', 'true', 'wahr', 'volljährig', 'volljaehrig', '18+', '✓', '✔']);
const NO = new Set(['nein', 'n', 'no', 'false', 'falsch', '-', 'minderjährig', 'minderjaehrig']);

type Col = 'last' | 'first' | 'full' | 'email' | 'birth' | 'adult' | 'p1name' | 'p1mail' | 'p2name' | 'p2mail' | 'skip';

let keyCounter = 0;
export function newKey(): string {
  keyCounter += 1;
  return `st${keyCounter}`;
}

export function emptyDraft(line = 0): StudentDraft {
  return { key: newKey(), line, first_name: '', last_name: '', email: '', birth_date: '', adult: false, parents: [] };
}

// ---------------------------------------------------------------------------------------------- Hilfen

function norm(s: string): string {
  return s
    .toLowerCase()
    .replace(/ä/g, 'ae')
    .replace(/ö/g, 'oe')
    .replace(/ü/g, 'ue')
    .replace(/ß/g, 'ss')
    .replace(/[^a-z0-9+]/g, '');
}

function unquote(s: string): string {
  const t = s.trim();
  if (t.length >= 2 && ((t.startsWith('"') && t.endsWith('"')) || (t.startsWith("'") && t.endsWith("'")))) return t.slice(1, -1).replace(/""/g, '"').trim();
  return t;
}

/** „MÜLLER-LÜDENSCHEIDT“ → „Müller-Lüdenscheidt“; gemischte Schreibweise bleibt unverändert. */
export function fixCase(name: string): string {
  return name
    .split(' ')
    .map((word) => {
      const letters = word.replace(/[^\p{L}]/gu, '');
      if (letters.length < 2 || letters !== letters.toUpperCase() || letters === letters.toLowerCase()) return word;
      if (PARTICLES.has(word.toLowerCase())) return word.toLowerCase();
      return word.toLowerCase().replace(/(^|[-'’])(\p{L})/gu, (_m, sep: string, ch: string) => sep + ch.toUpperCase());
    })
    .join(' ');
}

function clean(s: string): string {
  return fixCase(s.replace(/\s+/g, ' ').trim());
}

/** „Vorname Nachname“ → [Vorname, Nachname]; „Nachname, Vorname“ → [Vorname, Nachname]. */
export function splitName(full: string): [string, string] {
  const s = full.replace(/\s+/g, ' ').trim();
  if (!s) return ['', ''];
  if (s.includes(',')) {
    const [last = '', ...rest] = s.split(',');
    return [clean(rest.join(',')), clean(last)];
  }
  const parts = s.split(' ');
  if (parts.length < 2) return ['', clean(s)];
  let i = parts.length - 1;
  while (i > 1 && PARTICLES.has((parts[i - 1] ?? '').toLowerCase())) i -= 1;
  return [clean(parts.slice(0, i).join(' ')), clean(parts.slice(i).join(' '))];
}

/** Datum (TT.MM.JJJJ, T.M.JJ, JJJJ-MM-TT) → ISO; ungültig → ''. */
export function parseDate(value: string, today: Date = new Date()): string {
  const s = value.trim();
  let y: number;
  let m: number;
  let d: number;
  let match = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(s);
  if (match) {
    y = Number(match[1]);
    m = Number(match[2]);
    d = Number(match[3]);
  } else {
    match = /^(\d{1,2})[./](\d{1,2})[./](\d{2}|\d{4})$/.exec(s);
    if (!match) return '';
    d = Number(match[1]);
    m = Number(match[2]);
    y = Number(match[3]);
    if ((match[3] ?? '').length === 2) {
      const yy = today.getFullYear() % 100;
      y += y <= yy ? 2000 : 1900;
    }
  }
  const dt = new Date(Date.UTC(y, m - 1, d));
  if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== m - 1 || dt.getUTCDate() !== d) return '';
  return `${String(y).padStart(4, '0')}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
}

/** Alter in Jahren am Stichtag (ISO-Datum). */
export function ageOn(birthISO: string, today: Date = new Date()): number | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(birthISO);
  if (!m) return null;
  const y = Number(m[1]);
  const mo = Number(m[2]);
  const d = Number(m[3]);
  let age = today.getFullYear() - y;
  if (today.getMonth() + 1 < mo || (today.getMonth() + 1 === mo && today.getDate() < d)) age -= 1;
  return age;
}

/** Volljährig: aus dem Geburtsdatum (Stichtag heute), sonst die manuelle Angabe. */
export function isAdult(row: Pick<StudentDraft, 'birth_date' | 'adult'>, today: Date = new Date()): boolean {
  const age = row.birth_date ? ageOn(row.birth_date, today) : null;
  return age !== null ? age >= 18 : row.adult;
}

function headerCol(cell: string): Col | null {
  const h = norm(cell);
  if (!h) return null;
  const parent = /eltern|mutter|vater|erzieh|sorge|parent|guardian/.test(h);
  const second = /2|vater|zweit/.test(h);
  if (/mail/.test(h)) return parent ? (second ? 'p2mail' : 'p1mail') : 'email';
  if (parent) return second ? 'p2name' : 'p1name';
  if (/geburt|^geb|birth|dob/.test(h)) return 'birth';
  if (/volljaehrig|^18|adult|mündig|muendig/.test(h)) return 'adult';
  if (/vorname|rufname|firstname|givenname/.test(h)) return 'first';
  if (/nachname|familienname|lastname|surname/.test(h)) return 'last';
  if (/^(name|schueler|schuelerin|schuelerinnen|schuelerin(nen)?|kind|person|vollername)$/.test(h)) return 'full';
  if (/klasse|^nr|nummer|^id$|kurs|geschlecht|^m\/?w|telefon|handy|adresse|strasse|ort|plz/.test(h)) return 'skip';
  return null;
}

function looksLikeDate(s: string): boolean {
  return parseDate(s) !== '';
}

function splitLine(line: string, sep: string): string[] {
  if (sep === '\t') return line.split('\t').map(unquote);
  // CSV mit Anführungszeichen (einfach)
  const out: string[] = [];
  let cur = '';
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i] as string;
    if (ch === '"') {
      if (quoted && line[i + 1] === '"') {
        cur += '"';
        i += 1;
      } else quoted = !quoted;
    } else if (ch === sep && !quoted) {
      out.push(cur.trim());
      cur = '';
    } else cur += ch;
  }
  out.push(cur.trim());
  return out;
}

// ---------------------------------------------------------------------------------------------- Zeilen

function fromCells(cells: string[], cols: Col[] | null, line: number): StudentDraft | null {
  const row = emptyDraft(line);
  if (cols) {
    let full = '';
    cells.forEach((raw, i) => {
      const v = raw.trim();
      if (!v) return;
      const c = cols[i];
      if (c === 'last') row.last_name = clean(v);
      else if (c === 'first') row.first_name = clean(v);
      else if (c === 'full') full = v;
      else if (c === 'email') row.email = v;
      else if (c === 'birth') row.birth_date = parseDate(v) || v;
      else if (c === 'adult') row.adult = YES.has(v.toLowerCase());
      else if (c === 'p1name' || c === 'p2name' || c === 'p1mail' || c === 'p2mail') {
        const idx = c.startsWith('p2') ? 1 : 0;
        while (row.parents.length <= idx) row.parents.push({ name: '', email: '' });
        const p = row.parents[idx] as ParentDraft;
        if (c.endsWith('mail')) p.email = v;
        else p.name = clean(v);
      }
    });
    if (full && !(row.first_name && row.last_name)) {
      const [f, l] = splitName(full);
      row.first_name = row.first_name || f;
      row.last_name = row.last_name || l;
    }
    row.parents = row.parents.filter((p) => p.name || p.email);
  } else {
    const texts: string[] = [];
    let emails = 0;
    for (const raw of cells) {
      const v = raw.trim();
      if (!v) continue;
      if (v.includes('@')) {
        if (emails === 0) row.email = v;
        else if (row.parents.length < 2) row.parents.push({ name: '', email: v });
        emails += 1;
      } else if (looksLikeDate(v)) row.birth_date = parseDate(v);
      else if (YES.has(v.toLowerCase())) row.adult = true;
      else if (NO.has(v.toLowerCase())) row.adult = false;
      else if (/^\d+[.)]?$/.test(v)) continue;
      else texts.push(v);
    }
    if (texts.length >= 2) {
      row.last_name = clean(texts[0] as string);
      row.first_name = clean(texts[1] as string);
    } else if (texts.length === 1) {
      const [f, l] = splitName(texts[0] as string);
      row.first_name = f;
      row.last_name = l;
    }
  }
  if (!row.first_name && !row.last_name && !row.email) return null;
  return row;
}

function fromText(text: string, line: number): StudentDraft | null {
  let s = text.replace(/^\s*(?:\d+\s*[.)]\s+|[-•*–]\s+)/, '').trim();
  const row = emptyDraft(line);
  const tokens = s.split(/\s+/);
  const rest: string[] = [];
  for (const t of tokens) {
    const v = t.replace(/^[<(]|[>),;]$/g, '');
    if (v.includes('@')) {
      if (!row.email) row.email = v;
      else if (row.parents.length < 2) row.parents.push({ name: '', email: v });
    } else if (looksLikeDate(v)) row.birth_date = parseDate(v);
    else if (YES.has(v.toLowerCase()) && /volljährig|volljaehrig|18\+/i.test(v)) row.adult = true;
    else rest.push(t);
  }
  s = rest.join(' ').replace(/[,;]\s*$/, '');
  const [f, l] = splitName(s);
  row.first_name = f;
  row.last_name = l;
  if (!row.first_name && !row.last_name && !row.email) return null;
  return row;
}

/** Eingefügten Text in Zeilen zerlegen (siehe Modul-Doku). */
export function parseStudentList(input: string): ParseResult {
  const lines = input.replace(/^﻿/, '').replace(/\r\n?/g, '\n').split('\n');
  const filled = lines.map((l, i) => ({ text: l, line: i + 1 })).filter((l) => l.text.trim() !== '');
  if (!filled.length) return { rows: [], header: false, format: 'leer', columns: [] };
  const sep = filled.some((l) => l.text.includes('\t')) ? '\t' : filled.some((l) => l.text.includes(';')) ? ';' : null;
  const commaTable = !sep && filled.filter((l) => (l.text.match(/,/g) ?? []).length >= 2).length > filled.length / 2;
  if (sep || commaTable) {
    const s = sep ?? ',';
    const first = splitLine((filled[0] as { text: string }).text, s);
    const mapped = first.map(headerCol);
    const isHeader = mapped.some((c) => c !== null && c !== 'skip') && !first.some((c) => c.includes('@') || looksLikeDate(c));
    const cols = isHeader ? mapped.map((c) => c ?? 'skip') : null;
    if (cols && !cols.some((c) => c === 'last' || c === 'first' || c === 'full')) {
      // Kopfzeile ohne Namensspalte: erste unbekannte Spalten als Nachname/Vorname
      const free = cols.map((c, i) => (c === 'skip' && headerCol(first[i] ?? '') === null ? i : -1)).filter((i) => i >= 0);
      if (free[0] !== undefined) cols[free[0]] = 'last';
      if (free[1] !== undefined) cols[free[1]] = 'first';
    }
    const body = isHeader ? filled.slice(1) : filled;
    const rows = body.map((l) => fromCells(splitLine(l.text, s), cols, l.line)).filter((r): r is StudentDraft => r !== null);
    const labels: Record<Col, string> = {
      last: 'Nachname',
      first: 'Vorname',
      full: 'Name',
      email: 'E-Mail',
      birth: 'Geburtsdatum',
      adult: 'volljährig',
      p1name: 'Eltern 1',
      p1mail: 'E-Mail Eltern 1',
      p2name: 'Eltern 2',
      p2mail: 'E-Mail Eltern 2',
      skip: '',
    };
    return { rows, header: isHeader, format: 'tabelle', columns: cols ? cols.map((c) => labels[c]).filter(Boolean) : [] };
  }
  if (filled.every((l) => l.text.includes(','))) {
    const rows = filled
      .map((l) => {
        const cells = splitLine(l.text, ',');
        const name = cells.slice(0, 2).join(', ');
        const r = fromText(name, l.line);
        if (r) {
          for (const extra of cells.slice(2)) {
            if (extra.includes('@') && !r.email) r.email = extra.trim();
            else if (looksLikeDate(extra)) r.birth_date = parseDate(extra);
          }
        }
        return r;
      })
      .filter((r): r is StudentDraft => r !== null);
    return { rows, header: false, format: 'komma', columns: [] };
  }
  const rows = filled.map((l) => fromText(l.text, l.line)).filter((r): r is StudentDraft => r !== null);
  return { rows, header: false, format: 'text', columns: [] };
}

// ---------------------------------------------------------------------------------------------- Prüfen

export function fullName(r: Pick<StudentDraft, 'first_name' | 'last_name'>): string {
  return `${r.first_name.trim()} ${r.last_name.trim()}`.trim();
}

/** Fehler (verhindern das Anlegen) und Warnungen je Zeile; `existing` = Namen, die es schon gibt. */
export function checkRows(rows: readonly StudentDraft[], existing: readonly string[] = [], today: Date = new Date()): RowCheck[] {
  const counts = new Map<string, number>();
  for (const r of rows) {
    const k = fullName(r).toLowerCase();
    if (k) counts.set(k, (counts.get(k) ?? 0) + 1);
  }
  const known = new Set(existing.map((n) => n.trim().toLowerCase()));
  return rows.map((r) => {
    const errors: string[] = [];
    const warnings: string[] = [];
    if (!r.first_name.trim()) errors.push('Vorname fehlt');
    if (!r.last_name.trim()) errors.push('Nachname fehlt');
    if (r.email.trim() && !EMAIL_RE.test(r.email.trim())) errors.push('E-Mail-Adresse ungültig');
    if (r.birth_date) {
      const age = ageOn(r.birth_date, today);
      if (age === null) errors.push('Geburtsdatum nicht erkannt (TT.MM.JJJJ)');
      else if (age < 0 || age > 120) errors.push('Geburtsdatum nicht plausibel');
      else if (age < 4 || age > 30) warnings.push(`Alter ${age} Jahre – bitte prüfen`);
    }
    r.parents.forEach((p, i) => {
      if (p.email.trim() && !EMAIL_RE.test(p.email.trim())) errors.push(`E-Mail der Eltern ${i + 1} ungültig`);
    });
    const k = fullName(r).toLowerCase();
    if (k && (counts.get(k) ?? 0) > 1) warnings.push('Name doppelt in der Liste');
    if (k && known.has(k)) warnings.push('Name gibt es schon');
    return { errors, warnings };
  });
}

/** Zeilen → Format für `POST /classes` bzw. `/classes/{id}/students`. */
export function toApiStudents(rows: readonly StudentDraft[]) {
  return rows.map((r) => ({
    first_name: r.first_name.trim(),
    last_name: r.last_name.trim(),
    email: r.email.trim() || null,
    birth_date: r.birth_date || null,
    adult: r.birth_date ? false : r.adult,
    parents: r.parents.filter((p) => p.name.trim() || p.email.trim()).map((p) => ({ name: p.name.trim(), email: p.email.trim() || null })),
  }));
}

/** Gibt es irgendwo E-Mail-Adressen (Schüler/in oder Eltern)? */
export function hasEmails(rows: readonly StudentDraft[]): { students: number; parents: number } {
  return {
    students: rows.filter((r) => r.email.trim()).length,
    parents: rows.filter((r) => r.parents.some((p) => p.email.trim())).length,
  };
}

/** Jahrgang aus der Klassenbezeichnung („7b“ → 7, „Q1“ → 11, „EF“ → 10). */
export function gradeFromName(id: string): number | null {
  const s = id.trim().toUpperCase();
  let m = /^(\d{1,2})/.exec(s);
  if (m) return Number(m[1]);
  m = /^Q\s*([12])/.exec(s);
  if (m) return 10 + Number(m[1]);
  if (s.startsWith('EF')) return 10;
  return null;
}

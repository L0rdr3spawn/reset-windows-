/**
 * Minimaler CSV-Kopfzeilen-Parser für das Spalten-Mapping beim Import (rein, testbar).
 * Erkennt Trennzeichen ; , oder Tab, berücksichtigt Anführungszeichen und UTF-8-BOM.
 */

export function detectDelimiter(line: string): string {
  const counts: [string, number][] = [';', ',', '\t', '|'].map((d) => [d, line.split(d).length - 1]);
  counts.sort((a, b) => b[1] - a[1]);
  const best = counts[0];
  return best && best[1] > 0 ? best[0] : ';';
}

export function parseCsvLine(line: string, delimiter: string): string[] {
  const out: string[] = [];
  let cur = '';
  let quoted = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (quoted) {
      if (ch === '"') {
        if (line[i + 1] === '"') {
          cur += '"';
          i++;
        } else quoted = false;
      } else cur += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === delimiter) {
      out.push(cur.trim());
      cur = '';
    } else cur += ch;
  }
  out.push(cur.trim());
  return out;
}

export interface CsvPreview {
  delimiter: string;
  headers: string[];
  rows: string[][];
}

export function previewCsv(text: string, maxRows = 5): CsvPreview {
  const clean = text.replace(/^﻿/, '');
  const lines = clean.split(/\r?\n/).filter((l) => l.trim() !== '');
  const first = lines[0] ?? '';
  const delimiter = detectDelimiter(first);
  return {
    delimiter,
    headers: parseCsvLine(first, delimiter),
    rows: lines.slice(1, 1 + maxRows).map((l) => parseCsvLine(l, delimiter)),
  };
}

function simplify(s: string): string {
  return s
    .toLowerCase()
    .replace(/ä/g, 'ae')
    .replace(/ö/g, 'oe')
    .replace(/ü/g, 'ue')
    .replace(/ß/g, 'ss')
    .replace(/[^a-z0-9]/g, '');
}

/**
 * Schlägt für jedes Zielfeld eine Quellspalte vor (gleicher Name oder bekannter Alias).
 * Ergebnis: Zielfeld → Spaltenname der Datei.
 */
export function suggestMapping(headers: readonly string[], fields: readonly { key: string; aliases?: string[] }[]): Record<string, string> {
  const out: Record<string, string> = {};
  const simple = headers.map(simplify);
  for (const f of fields) {
    const cands = [f.key, ...(f.aliases ?? [])].map(simplify);
    const idx = simple.findIndex((h) => cands.includes(h));
    if (idx >= 0) out[f.key] = headers[idx] as string;
  }
  return out;
}

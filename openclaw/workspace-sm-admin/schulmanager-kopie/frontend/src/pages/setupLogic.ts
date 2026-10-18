/** Logik des Einrichtungs-Assistenten (`SetupPage.tsx`), ohne Oberfläche – damit testbar. */

export interface SetupStep {
  key: string;
  done: boolean;
  skipped: boolean;
  optional: boolean;
  auto: boolean;
  marked: 'done' | 'skipped' | null;
}

export const STEP_TITLES: Record<string, string> = {
  admin: 'Administration sichern',
  lizenz: 'Lizenz',
  schule: 'Schuldaten',
  schuljahr: 'Schuljahr und Ferien',
  zeitraster: 'Zeitraster',
  stammdaten: 'Lehrkräfte, Klassen, Fächer und Räume',
  schueler: 'Schüler/innen',
  unterricht: 'Stundentafeln und Kurse',
  stundenplan: 'Stundenplan',
  konten: 'Konten und Zugangsbriefe',
  rechte: 'Rollen und Rechte',
  mail: 'E-Mail-Versand',
  sso: 'Anmeldung über Schulkonto (optional)',
};

/** Anzahl erledigter und übersprungener Schritte (für die Fortschrittsanzeige) */
export function progress(steps: readonly SetupStep[]): { done: number; skipped: number; total: number; percent: number } {
  const done = steps.filter((s) => s.done).length;
  const skipped = steps.filter((s) => s.skipped).length;
  const total = steps.length;
  return { done, skipped, total, percent: total ? Math.round(((done + skipped) / total) * 100) : 0 };
}

/** Nächster Schritt, der weder erledigt noch übersprungen ist – ab `after` (Schlüssel), sonst von vorn */
export function nextOpen(steps: readonly SetupStep[], after?: string): string | null {
  const start = after ? steps.findIndex((s) => s.key === after) + 1 : 0;
  const order = [...steps.slice(start), ...steps.slice(0, start)];
  return order.find((s) => !s.done && !s.skipped)?.key ?? null;
}

export const LOGO_MAX_BYTES = 300_000;
export const LOGO_TYPES = ['image/png', 'image/jpeg'];

/** Prüft eine Logo-Datei vor dem Hochladen; liefert eine Fehlermeldung oder `null` */
export function logoProblem(file: { type: string; size: number }): string | null {
  if (!LOGO_TYPES.includes(file.type)) return 'Das Logo muss eine PNG- oder JPEG-Datei sein.';
  if (file.size > LOGO_MAX_BYTES) return 'Das Logo darf höchstens 300 kB groß sein.';
  return null;
}

/** Zeilen für „Daten übernehmen“: Anzahl je Art in empfohlener Importreihenfolge */
export const IMPORT_ORDER: { key: string; label: string }[] = [
  { key: 'subjects', label: 'Fächer' },
  { key: 'rooms', label: 'Räume' },
  { key: 'classes', label: 'Klassen' },
  { key: 'teachers', label: 'Lehrkräfte' },
  { key: 'students', label: 'Schüler/innen' },
];

export function importSummary(counts: Record<string, number>): string {
  return IMPORT_ORDER.map((i) => `${i.label}: ${counts[i.key] ?? 0}`).join(' · ');
}

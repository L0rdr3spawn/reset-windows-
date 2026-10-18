/** Ferien & Feiertage aus öffentlicher API (`/holiday-import`, Recht `masterdata.edit`) – Endpunkte und reine Hilfen. */
import { http } from '../../api/client';

export interface HolidayImportState {
  enabled: boolean;
  country: string;
  region: string;
  language: string;
  /** false = Server hat den Import abgeschaltet (`SM_HOLIDAY_IMPORT=0`) */
  available: boolean;
  status: { last_run: string | null; last_error: string | null; next_run: string | null };
  school_years: number[];
}

export interface HolidayCountry {
  code: string;
  name: string;
  source: 'openholidays' | 'nager';
}

export interface HolidayRegion {
  code: string;
  name: string;
  category: string;
  parent: string;
}

export type ChangeAction = 'add' | 'update' | 'unchanged' | 'exists' | 'edited' | 'removed';

export interface HolidayChange {
  action: ChangeAction;
  name: string;
  date_from: string;
  date_to: string;
  kind: string;
  old?: { name: string; date_from: string; date_to: string; kind: string };
}

export interface HolidayImportResult {
  changes: HolidayChange[];
  counts: Record<ChangeAction, number>;
}

export const holidayImportApi = {
  get: () => http.get<HolidayImportState>('/holiday-import'),
  put: (b: { enabled: boolean; country: string; region: string; language: string }) => http.put<HolidayImportState>('/holiday-import', b),
  countries: () => http.get<HolidayCountry[]>('/holiday-import/countries'),
  regions: (country: string) => http.get<HolidayRegion[]>('/holiday-import/regions', { country }),
  preview: () => http.post<HolidayImportResult>('/holiday-import/preview', {}),
  apply: () => http.post<HolidayImportResult>('/holiday-import/apply', {}),
};

export const ACTION_LABELS: Record<ChangeAction, string> = {
  add: 'neu',
  update: 'geändert',
  unchanged: 'unverändert',
  exists: 'schon vorhanden',
  edited: 'von Hand geändert – bleibt',
  removed: 'von Hand gelöscht – bleibt weg',
};

/** Nur das, was den Nutzer interessiert: zuerst Neues und Änderungen, dann Hinweise; „unverändert“ entfällt. */
export function visibleChanges(changes: HolidayChange[]): HolidayChange[] {
  const order: Record<ChangeAction, number> = { add: 0, update: 1, edited: 2, removed: 3, exists: 4, unchanged: 5 };
  return changes.filter((c) => c.action !== 'unchanged').sort((a, b) => order[a.action] - order[b.action] || a.date_from.localeCompare(b.date_from));
}

/** Kurzfassung für Meldungen, z. B. „3 neu, 1 geändert“. */
export function summaryText(counts: Record<ChangeAction, number>): string {
  const parts: string[] = [];
  if (counts.add) parts.push(`${counts.add} neu`);
  if (counts.update) parts.push(`${counts.update} geändert`);
  return parts.length ? parts.join(', ') : 'Keine Änderungen';
}

/** Regionen in Auswahlreihenfolge: Oberebene zuerst, Unterregionen eingerückt dahinter. */
export function regionOptions(regions: HolidayRegion[]): { code: string; label: string }[] {
  const top = regions.filter((r) => !r.parent);
  const out: { code: string; label: string }[] = [];
  for (const r of [...top].sort((a, b) => a.name.localeCompare(b.name, 'de'))) {
    out.push({ code: r.code, label: r.name });
    for (const c of regions.filter((x) => x.parent === r.code)) out.push({ code: c.code, label: ` ${c.name}` });
  }
  return out.length ? out : regions.map((r) => ({ code: r.code, label: r.name }));
}

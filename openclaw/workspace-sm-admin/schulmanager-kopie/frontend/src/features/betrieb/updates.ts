/** Updates unter `/betrieb`: Typen der Antwort von `GET /admin/updates` und kleine Anzeige-Hilfen. */

export interface UpdateOffer {
  version: string;
  notes?: string;
  urgent?: boolean;
  migration?: { present: boolean; backward_compatible: boolean } | null;
  channel?: string;
}

export interface UpdateWindow {
  label?: string;
  start?: string;
  end?: string;
  inside?: boolean;
}

export interface UpdateStatus {
  node: string;
  version: string;
  state: string;
  detail?: string;
  offered: UpdateOffer | null;
  window: UpdateWindow | null;
  announce?: string;
  urgent?: boolean;
  prepared?: string | null;
  mode: 'auto' | 'manual';
  postponed_until?: string | null;
  can_postpone?: boolean;
  may_choose_strategy?: boolean;
  contract_manual?: boolean;
  strategy?: string | null;
  nodes?: number;
  failed?: Record<string, string>;
  log: { ts: string; text: string }[];
  last_poll_at?: string;
  last_ok_at?: string;
  last_error?: string;
  updated_at?: string;
}

export interface UpdatesOverview {
  version: string;
  node: string;
  agent: boolean;
  agent_stale: boolean | null;
  status: UpdateStatus | null;
  plan: { mode?: string; strategy?: string };
  max_postpone_days: number;
}

export const UPDATE_STATE_LABELS: Record<string, string> = {
  idle: 'aktuell',
  waiting: 'wartet',
  downloading: 'lädt',
  ready: 'bereit, wartet auf den Termin',
  draining: 'nimmt den Server aus dem Betrieb',
  backing_up: 'sichert',
  updating: 'aktualisiert',
  verifying: 'prüft',
  held: 'angehalten (Wartungsfenster)',
  healthy: 'aktualisiert und gesund',
  rolled_back: 'zurückgerollt',
  error: 'Fehler',
  postponed: 'verschoben',
  manual: 'wartet auf Ihre Freigabe',
};

export const UPDATE_STATE_BADGE: Record<string, string> = {
  idle: 'badge-success',
  healthy: 'badge-success',
  rolled_back: 'badge-danger',
  error: 'badge-danger',
  downloading: 'badge-warning',
  draining: 'badge-warning',
  backing_up: 'badge-warning',
  updating: 'badge-warning',
  verifying: 'badge-warning',
  held: 'badge-warning',
};

/** Zeitfenster als lesbarer Text in Ortszeit, z. B. „Sa, 21.05.2026, 00:00 bis 06:00 Uhr“. */
export function windowText(w: UpdateWindow | null | undefined, locale = 'de-DE', tz = 'Europe/Berlin'): string {
  if (!w?.start || !w.end) return w?.label ?? '–';
  const start = new Date(w.start);
  const end = new Date(w.end);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return w.label ?? '–';
  const day = new Intl.DateTimeFormat(locale, { timeZone: tz, weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' }).format(start);
  const hm = new Intl.DateTimeFormat(locale, { timeZone: tz, hour: '2-digit', minute: '2-digit' });
  return `${day}, ${hm.format(start)} bis ${hm.format(end)} Uhr`;
}

/** Hinweistext zur Migration des angebotenen Updates. */
export function migrationText(m: UpdateOffer['migration']): string {
  if (!m || !m.present) return 'Keine Datenbank-Änderung.';
  return m.backward_compatible
    ? 'Enthält eine Datenbank-Änderung (abwärtskompatibel).'
    : 'Enthält eine Datenbank-Änderung. Bei mehreren Servern werden alle gemeinsam in einem Wartungsfenster aktualisiert (kurze Ausfallzeit).';
}

/** Hilfsfunktionen der Betriebs-Statusseite (`BetriebPage.tsx`). */

export type CheckLevel = 'ok' | 'warn' | 'error';

export interface Check {
  key: string;
  label: string;
  level: CheckLevel;
  detail: string;
}

export interface BackupItem {
  name: string;
  size: number;
  created_at: string;
  kind: string;
}

export interface VerifyResult {
  name: string;
  ok: boolean;
  integrity: string;
  users: number | null;
  plan_versions: number | null;
  revision: string | null;
  seconds: number;
}

export interface Status {
  version: string;
  mode: 'production' | 'demo' | 'development';
  env: string;
  school_name: string;
  uptime_seconds: number;
  generated_at: string;
  database: { kind: string; revision: string | null; head: string | null; up_to_date: boolean; file_bytes: number | null };
  storage: {
    disk: { total: number | null; used: number | null; free: number | null; free_percent: number | null };
    files_bytes: number;
    backups_bytes: number;
    data_dir: string;
  };
  mail: { smtp: boolean; dev_outbox: boolean; pending: number; failed: number; last_sent: string | null };
  backup: { count: number; last: BackupItem | null; auto_hours: number; keep: number };
  maintenance: { last: string | null; interval_seconds: number };
  encryption: { source: string; active: string; keys: { id: string; fingerprint: string }[] };
  license: { state?: string; enforced?: boolean; message?: string; read_only?: boolean };
  errors: { last_24h: number; total: number };
  checks: Check[];
  ok: boolean;
}

export interface ErrorEntry {
  id: number;
  created_at: string;
  level: string;
  logger: string;
  message: string;
  request_id: string | null;
  trace: string | null;
}

export const MODE_LABELS: Record<Status['mode'], string> = {
  production: 'Echtbetrieb',
  demo: 'Vorführung (Demo)',
  development: 'Entwicklung',
};

export const LEVEL_BADGE: Record<CheckLevel, string> = {
  ok: 'badge-success',
  warn: 'badge-warning',
  error: 'badge-danger',
};

export const LEVEL_TEXT: Record<CheckLevel, string> = { ok: 'in Ordnung', warn: 'Hinweis', error: 'Fehler' };

/** Gesamturteil für die Kopfzeile */
export function summary(checks: readonly Check[]): { level: CheckLevel; text: string } {
  const errors = checks.filter((c) => c.level === 'error').length;
  const warns = checks.filter((c) => c.level === 'warn').length;
  if (errors) return { level: 'error', text: `${errors} ${errors === 1 ? 'Fehler' : 'Fehler'}, ${warns} Hinweise` };
  if (warns) return { level: 'warn', text: `${warns} ${warns === 1 ? 'Hinweis' : 'Hinweise'}` };
  return { level: 'ok', text: 'Alles in Ordnung' };
}

/** „3 Tage 4 Std.“ aus Sekunden */
export function uptimeText(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (d) return `${d} ${d === 1 ? 'Tag' : 'Tage'} ${h} Std.`;
  if (h) return `${h} Std. ${m} Min.`;
  return `${m} Min.`;
}

/** Wie lange die letzte Sicherung her ist, als Text */
export function ageText(iso: string | null | undefined, now: number = Date.now()): string {
  if (!iso) return 'noch nie';
  const diff = (now - new Date(iso).getTime()) / 1000;
  if (diff < 90) return 'gerade eben';
  if (diff < 3600) return `vor ${Math.round(diff / 60)} Min.`;
  if (diff < 86400) return `vor ${Math.round(diff / 3600)} Std.`;
  const days = Math.round(diff / 86400);
  return `vor ${days} ${days === 1 ? 'Tag' : 'Tagen'}`;
}

export function verifyText(v: VerifyResult): string {
  if (!v.ok) return `Prüfung fehlgeschlagen: ${v.integrity}`;
  return `Lesbar und vollständig – ${v.users ?? 0} Konten, ${v.plan_versions ?? 0} Planversionen (${v.seconds.toFixed(1)} s)`;
}

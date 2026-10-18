/**
 * Typisierte Endpunkte gemäß docs/ARCHITECTURE.md §6.
 */
import { API_BASE, asList, buildQuery, http, type QueryValue } from './client';
import type {
  AutoPlanStatus,
  Absence,
  AbsencePreview,
  Announcement,
  AuditEntry,
  BackupInfo,
  ApiTokenInfo,
  BulkCreated,
  Candidate,
  CollectionName,
  CollectionTypes,
  DayPlan,
  Exam,
  HistoryEntry,
  ImportReport,
  Job,
  LoginResponse,
  ManagedUser,
  MeResponse,
  MonitorConfig,
  MonitorData,
  MoveOption,
  MyDay,
  MyWeek,
  Override,
  PlanningReport,
  ReportDetailsResponse,
  Role,
  RolesInfo,
  SessionInfo,
  Settings,
  StudentAbsence,
  ReportPreview,
  StudentAbsenceAccess,
  StudentAbsenceKind,
  StudentAbsenceSource,
  StudentAbsenceStatus,
  AttendanceRecord,
  TeacherStat,
  TimetableKind,
  TimetableView,
  User,
  WarningsResponse,
  DutyOverview,
  CurriculaOverview,
  RebuildResult,
  CalendarPreview,
  SchoolYear,
  PlanPeriodInput,
  PlanPeriodsResponse,
} from './types';

const enc = encodeURIComponent;

// ------------------------------------------------------------------ Auth

export const auth = {
  me: () => http.get<MeResponse>('/auth/me', undefined, { skipAuthRedirect: true }),
  /** ``add``: weiteres Konto anmelden, das bisherige bleibt angemeldet (Kontowechsel) */
  login: (username: string, password: string, totp?: string, add = false) =>
    http.post<LoginResponse>(`/auth/login${add ? '?add=true' : ''}`, { username, password, ...(totp ? { totp } : {}) }, { skipAuthRedirect: true }),
  /** ``accounts``: Zahl der in diesem Browser noch angemeldeten weiteren Konten (kein automatischer Wechsel) */
  logout: () => http.post<{ ok: boolean; accounts?: number } | undefined>('/auth/logout', {}, { skipAuthRedirect: true }),
  /** ohne aktive Sitzung (nach dem Abmelden) nur die weiteren, noch gültigen Konten; Fehler 401 gibt es nicht */
  accounts: (signal?: AbortSignal) =>
    http.get<{ accounts: { id: number; username: string; display_name: string; role: Role; active: boolean }[]; max: number; signed_in?: boolean }>(
      '/auth/accounts',
      undefined,
      { signal, skipAuthRedirect: true },
    ),
  switchAccount: (userId: number) => http.post<MeResponse>('/auth/accounts/switch', { user_id: userId }, { skipAuthRedirect: true }),
  logoutOther: (userId: number) => http.post<{ ok: boolean; accounts?: number }>(`/auth/accounts/${userId}/logout`, {}, { skipAuthRedirect: true }),
  changePassword: (old_password: string, new_password: string) =>
    http.post<void>('/auth/password', { old_password, new_password }),
  setup2fa: (renew = false) => http.post<{ secret: string; otpauth_url: string }>(`/auth/2fa/setup${renew ? '?neu=true' : ''}`, {}),
  enable2fa: (code: string) => http.post<void>('/auth/2fa/enable', { code }),
  disable2fa: (password: string) => http.post<void>('/auth/2fa/disable', { password }),
  icalUrl: () => http.get<{ url: string | null; active: boolean }>('/me/ical-url'),
  icalReset: () => http.post<{ url: string; active: boolean }>('/me/ical-url', {}),
  icalDelete: () => http.del<void>('/me/ical-url'),
  /** DSGVO-Datenauskunft als Datei */
  exportUrl: () => `${API_BASE}/me/export`,
  config: () =>
    http.get<{
      app_name?: string;
      env?: string;
      oidc?: { enabled: boolean; label?: string; login_url?: string | null };
      password_min_length?: Record<string, number>;
    }>(
      '/auth/config',
      undefined,
      { skipAuthRedirect: true },
    ),
};

// ------------------------------------------------------------------ Benutzer

export const users = {
  list: async (query?: Record<string, QueryValue>) => asList<ManagedUser>(await http.get<unknown>('/users', query)),
  get: (id: string | number) => http.get<ManagedUser>(`/users/${enc(String(id))}`),
  create: (u: Partial<ManagedUser> & { password?: string }) => http.post<ManagedUser & { temp_password?: string }>('/users', u),
  update: (id: string | number, u: Partial<ManagedUser> & { password?: string }) =>
    http.patch<ManagedUser>(`/users/${enc(String(id))}`, u),
  remove: (id: string | number) => http.del<void>(`/users/${enc(String(id))}`),
  resetPassword: (id: string | number, disable_2fa = false) =>
    http.post<{ temp_password: string; username?: string }>(`/users/${enc(String(id))}/reset-password`, { disable_2fa }),
  /** Vorführ-Instanz: ausgegebene Demo-Zugänge und mögliche Arten (nur Inhaber) */
  demoAccessInfo: (signal?: AbortSignal) =>
    http.get<{ kinds: { kind: string; label: string }[]; issued: { id: number; username: string; display_name: string; role: Role; active: boolean; last_login: string | null }[] }>(
      '/demo-access',
      undefined,
      { signal },
    ),
  demoAccess: (name: string, kinds: string[]) =>
    http.post<{ letters: { username: string; display_name: string; temp_password: string; role: Role }[] }>('/demo-access', { name, kinds }),
  bulk: (role: Extract<Role, 'schueler' | 'lehrer' | 'eltern'>, class_ids?: string[]) =>
    http.post<{ created: BulkCreated[]; skipped?: unknown[] }>('/users/bulk', { role, ...(class_ids?.length ? { class_ids } : {}) }),
  apiToken: (id: string | number, name?: string) =>
    http.post<{ token: string; name?: string }>(`/users/${enc(String(id))}/api-token`, name ? { name } : {}),
  sessions: async (id: string | number) => asList<SessionInfo>(await http.get<unknown>(`/users/${enc(String(id))}/sessions`)),
  deleteSession: (id: string | number) => http.del<void>(`/sessions/${enc(String(id))}`),
  revokeAllSessions: (id: string | number) => http.del<{ revoked: number }>(`/users/${enc(String(id))}/sessions`),
  children: (id: string | number) =>
    http.get<{ student_ids: string[]; students: { id: string; name: string | null; class: string | null }[] }>(`/users/${enc(String(id))}/children`),
  setChildren: (id: string | number, student_ids: string[]) => http.put<{ student_ids: string[] }>(`/users/${enc(String(id))}/children`, { student_ids }),
  apiTokens: async (id: string | number) => asList<ApiTokenInfo>(await http.get<unknown>(`/users/${enc(String(id))}/api-tokens`)),
  deleteApiToken: (tokenId: string | number) => http.del<void>(`/api-tokens/${enc(String(tokenId))}`),
  roles: () => http.get<RolesInfo>('/roles'),
};

// ------------------------------------------------------------------ Verlauf / Audit / System

export const history = {
  list: async (limit = 100) => asList<HistoryEntry>(await http.get<unknown>('/history', { limit })),
  restore: (version: number) => http.post<unknown>(`/history/${version}/restore`, {}),
  undo: () => http.post<unknown>('/history/undo', {}),
  audit: async (q: { limit?: number; user?: string; action?: string }) =>
    asList<AuditEntry>(await http.get<unknown>('/audit', q)),
};

export const admin = {
  system: () => http.get<Record<string, unknown>>('/admin/system'),
  backups: async () => asList<BackupInfo>(await http.get<unknown>('/admin/backups')),
  createBackup: () => http.post<BackupInfo>('/admin/backups', {}),
  backupUrl: (name: string) => `${API_BASE}/admin/backups/${enc(name)}`,
  deleteBackup: (name: string) => http.del<void>(`/admin/backups/${enc(name)}`),
  /** Lädt die Demo-Schule (synchron, Dauer ≈ time_limit) */
  loadDemo: (body: { time_limit?: number; accounts?: boolean; classes_per_grade?: number } = {}) =>
    http.post<{ version?: number; accounts?: { username: string; password?: string; role?: string; display_name?: string }[]; [k: string]: unknown }>('/admin/demo', body),
  maintenance: () => http.post<{ deleted?: Record<string, number> | number }>('/admin/maintenance', {}),
  version: () => http.get<Record<string, unknown>>('/version'),
};

// ------------------------------------------------------------------ Stammdaten (generisch)

export const data = {
  list: async <K extends CollectionName>(c: K, query?: Record<string, QueryValue>) =>
    asList<CollectionTypes[K]>(await http.get<unknown>(`/data/${c}`, query)),
  /** ohne `id` erzeugt der Server eine (außer Lehrkräfte/Klassen/Fächer) */
  /** `force`: Stundentafeln trotz Überschneidung speichern (sonst 409 mit Klassenliste) */
  create: <K extends CollectionName>(c: K, item: Partial<CollectionTypes[K]>, force = false) =>
    http.post<CollectionTypes[K]>(`/data/${c}`, item, force ? { query: { force: 1 } } : {}),
  update: <K extends CollectionName>(c: K, id: string, item: Partial<CollectionTypes[K]>, force = false) =>
    http.put<CollectionTypes[K]>(`/data/${c}/${enc(id)}`, item, force ? { query: { force: 1 } } : {}),
  /** 409 bei bestehenden Verweisen; `force` entfernt die Verweise mit */
  remove: (c: CollectionName, id: string, force = false) => http.del<void>(`/data/${c}/${enc(id)}`, force ? { query: { force: 1 } } : {}),
};

export const settings = {
  get: () => http.get<Settings>('/settings'),
  /** `force` übernimmt eine 409-Bestätigung (`plan_change`, `grid_change`) */
  put: (s: Settings, opts: { force?: boolean } = {}) => http.put<Settings>('/settings', s, { query: { force: opts.force ? 1 : undefined } }),
  /** Wirkung einer Kalenderänderung (Schuljahresbeginn, Zählung, Unterrichtstage) vorab (Recht `settings.edit`) */
  calendarPreview: (body: Partial<Settings>) => http.post<CalendarPreview>('/settings/calendar-preview', body),
};

// ------------------------------------------------------------------ Kalender (R3)

export const calendar = {
  /** Wochen des Schuljahres; `class_id` nur mit Sichtrecht (sonst 404) */
  schoolYear: (q: { date?: string; class_id?: string } = {}, signal?: AbortSignal) =>
    http.get<SchoolYear>('/calendar/school-year', { date: q.date || undefined, class_id: q.class_id || undefined }, { signal }),
  /** Nächster/vorheriger Schultag ohne Ferien, Feiertage und freie Tage */
  schoolDay: (q: { date: string; dir: 1 | -1; class_id?: string }) =>
    http.get<{ date: string; found: boolean }>('/calendar/school-day', { date: q.date, dir: q.dir, class_id: q.class_id || undefined }),
  /** Planzeiträume (Halbjahre …) mit `has_plan`; `suggested` = Vorschlag zum Einrichten, `target` = Voreinstellung im Generator */
  planPeriods: (signal?: AbortSignal) => http.get<PlanPeriodsResponse>('/calendar/plan-periods', undefined, { signal }),
  savePlanPeriods: (body: { periods: PlanPeriodInput[]; adopt?: string; confirm_delete?: boolean }) =>
    http.put<PlanPeriodsResponse>('/calendar/plan-periods', body),
  copyPlanPeriod: (to: string, from: string, replace = false) =>
    http.post<PlanPeriodsResponse & { copied: number; skipped: number }>(`/calendar/plan-periods/${enc(to)}/copy/${enc(from)}`, {}, { query: { replace: replace ? 1 : undefined } }),
  clearPlanPeriod: (id: string) => http.del<PlanPeriodsResponse & { removed: number }>(`/calendar/plan-periods/${enc(id)}/plan`),
};

// ------------------------------------------------------------------ Planung

export const planning = {
  coursesFromCurricula: (opts: { dry_run?: boolean; reset_manual?: boolean } = {}) =>
    http.post<RebuildResult>('/planning/courses-from-curricula', opts),
  curriculaOverview: () => http.get<CurriculaOverview>('/planning/curricula/overview'),
  assignTeachers: () => http.post<WarningsResponse>('/planning/assign-teachers', {}),
  report: () => http.get<PlanningReport>('/planning/report'),
  reportDetails: (signal?: AbortSignal) => http.get<ReportDetailsResponse>('/planning/report/details', undefined, { signal }),
  generate: (opts: { time_limit?: number; keep_locked?: boolean; seed?: number; workers?: number; period?: string; copy_from?: string }) =>
    http.post<{ job_id: string; job?: Job }>('/planning/generate', opts),
  job: (id: string) => http.get<Job>(`/planning/jobs/${enc(id)}`),
  jobs: async () => asList<Job>(await http.get<unknown>('/planning/jobs')),
  cancel: (id: string) => http.post<Job>(`/planning/jobs/${enc(id)}/cancel`, {}),
  apply: (id: string) => http.post<unknown>(`/planning/jobs/${enc(id)}/apply`, {}),
  dutiesOverview: (date: string, signal?: AbortSignal) => http.get<DutyOverview>('/duties/overview', { date }, { signal }),
  generateDuties: () => http.post<WarningsResponse>('/duties/generate', {}),
  autoplan: () => http.get<AutoPlanStatus>('/planning/autoplan'),
  autoplanRun: () => http.post<AutoPlanStatus>('/planning/autoplan/run', {}),
};

// ------------------------------------------------------------------ Stundenplan

/** Woche per Datum (kanonisch) bzw. laufender Woche des Schuljahres (`week_no`) */
export interface TimetableQuery {
  date?: string;
  week_no?: number;
  all_days?: boolean;
}

export const timetable = {
  view: (kind: TimetableKind, ref: string, week: number | TimetableQuery = 0) =>
    http.get<TimetableView>(
      `/timetable/${kind}/${enc(ref)}`,
      typeof week === 'number'
        ? { week }
        : { date: week.date || undefined, week_no: week.week_no ?? undefined, all_days: week.all_days === undefined ? undefined : week.all_days ? 1 : 0 },
    ),
  options: async (lessonId: string) =>
    asList<MoveOption>(await http.get<unknown>(`/timetable/lessons/${enc(lessonId)}/options`)),
  move: (lessonId: string, day: number, start: number) =>
    http.post<unknown>(`/timetable/lessons/${enc(lessonId)}/move`, { day, start }),
  lock: (lessonId: string, locked: boolean) => http.post<unknown>(`/timetable/lessons/${enc(lessonId)}/lock`, { locked }),
};

// ------------------------------------------------------------------ Vertretung

export interface SubstitutionQuery {
  date: string;
  site?: string;
  class_id?: string;
  teacher?: string;
  /** öffentliche Sicht (Druck/Aushang) im Datenumfang der Rolle (B-04) */
  public?: boolean;
}

export const substitutions = {
  day: (q: SubstitutionQuery) => http.get<DayPlan>('/substitutions', { ...q }),
  range: async (from: string, to: string) => asList<DayPlan>(await http.get<unknown>('/substitutions/range', { from, to })),
  candidates: async (q: { date: string; lesson_id: string; period: number; part?: number }) =>
    asList<Candidate>(await http.get<unknown>('/substitutions/candidates', q)),
  /** Bestätigungsmodus: Vorschläge eines Tages freigeben (ohne `entryIds` alle) */
  release: (date: string, entryIds?: string[]) => http.post<{ released: number; date: string }>('/substitutions/release', { date, entry_ids: entryIds }),
  stats: async (from: string, to: string): Promise<TeacherStat[]> => {
    const r = await http.get<unknown>('/substitutions/stats', { from, to });
    if (r && typeof r === 'object' && !Array.isArray(r) && Array.isArray((r as { teachers?: unknown }).teachers)) return (r as { teachers: TeacherStat[] }).teachers;
    return asList<TeacherStat>(r);
  },
};

export const absences = {
  list: async (query?: Record<string, QueryValue>) => asList<Absence>(await http.get<unknown>('/absences', query)),
  create: (a: Omit<Absence, 'id'> & { id?: string }) => http.post<Absence>('/absences', a),
  update: (id: string, a: Omit<Absence, 'id'>) => http.put<Absence>(`/absences/${enc(id)}`, a),
  remove: (id: string) => http.del<void>(`/absences/${enc(id)}`),
  /** Vorschau vor dem Speichern: Schultage, Ferien und betroffene Einträge (`absence_id` = bisherige beim Bearbeiten) */
  preview: (a: Omit<Absence, 'id'>, absenceId?: string) =>
    http.post<AbsencePreview>('/absences/preview', a, { query: { absence_id: absenceId } }),
  reportSelf: (r: { date_from: string; date_to: string; periods?: number[]; reason: string }) =>
    http.post<Absence>('/absences/report-self', r),
};

export const overrides = {
  list: async (query?: Record<string, QueryValue>) => asList<Override>(await http.get<unknown>('/overrides', query)),
  create: (o: Omit<Override, 'id'> & { id?: string; all_periods?: boolean }) => http.post<Override>('/overrides', o),
  remove: (id: string) => http.del<void>(`/overrides/${enc(id)}`),
};

export const me = {
  today: (date?: string, student_id?: string) => http.get<MyDay>('/me/today', { date, student_id }),
  week: async (date?: string, student_id?: string): Promise<MyWeek> => {
    const raw = await http.get<unknown>('/me/week', { date, student_id });
    if (Array.isArray(raw)) return { days: raw as MyDay[] };
    const r = raw as Partial<MyWeek>;
    return { days: Array.isArray(r?.days) ? r.days : [], ...(r?.week_info ? { week_info: r.week_info } : {}) };
  },
};

/** Normalisiert verschiedene mögliche Antwortformen von GET /monitor. */
export function normalizeMonitor(raw: unknown): MonitorData {
  const empty: MonitorData = { days: [], announcements: [] };
  if (!raw || typeof raw !== 'object') return empty;
  if (Array.isArray(raw)) return { ...empty, days: raw as DayPlan[] };
  const r = raw as Record<string, unknown>;
  const announcements = Array.isArray(r.announcements) ? (r.announcements as Announcement[]) : [];
  let days: DayPlan[] = [];
  if (Array.isArray(r.days)) days = r.days as DayPlan[];
  else if (Array.isArray(r.plans)) days = r.plans as DayPlan[];
  else if (Array.isArray(r.entries)) days = [r as unknown as DayPlan];
  else {
    for (const key of ['today', 'tomorrow']) {
      const v = r[key];
      if (v && typeof v === 'object' && Array.isArray((v as DayPlan).entries)) days.push(v as DayPlan);
    }
  }
  return {
    site: typeof r.site === 'string' ? r.site : null,
    site_name: typeof r.site_name === 'string' ? r.site_name : null,
    school_name: typeof r.school_name === 'string' ? r.school_name : null,
    days,
    announcements,
    config: r.config && typeof r.config === 'object' ? (r.config as MonitorConfig) : null,
  };
}

export const monitor = {
  get: async (site?: string, date?: string) => normalizeMonitor(await http.get<unknown>('/monitor', { site, date })),
  configs: (signal?: AbortSignal) =>
    http.get<{ monitors: { site: string; site_name: string; config: MonitorConfig }[]; defaults: MonitorConfig }>('/monitor/config', undefined, { signal }),
  saveConfig: (site: string, config: MonitorConfig) => http.put<MonitorConfig>(`/monitor/config/${encodeURIComponent(site || 'alle')}`, config),
};

// ------------------------------------------------------------------ Klausuren / Mitteilungen / Krankmeldungen

export const exams = {
  list: async (query?: Record<string, QueryValue>) => asList<Exam>(await http.get<unknown>('/exams', query)),
  /** `force` speichert trotz Warnungen (nicht für Lehrkräfte) */
  create: (e: Partial<Exam> & { force?: boolean }) => http.post<Exam & { warnings?: string[] }>('/exams', e),
  update: (id: string, e: Partial<Exam> & { force?: boolean }) => http.put<Exam & { warnings?: string[] }>(`/exams/${enc(id)}`, e),
  remove: (id: string) => http.del<void>(`/exams/${enc(id)}`),
  check: async (e: Partial<Exam>): Promise<string[]> => {
    const r = await http.post<unknown>('/exams/check', e);
    if (Array.isArray(r)) return r.map(String);
    if (r && typeof r === 'object') {
      const o = r as Record<string, unknown>;
      for (const key of ['warnings', 'conflicts', 'problems']) {
        if (Array.isArray(o[key])) return (o[key] as unknown[]).map(String);
      }
    }
    return [];
  },
};

export const announcements = {
  list: async (query?: Record<string, QueryValue>) => asList<Announcement>(await http.get<unknown>('/announcements', query)),
  create: (a: Partial<Announcement>) => http.post<Announcement>('/announcements', a),
  update: (id: string | number, a: Partial<Announcement>) => http.put<Announcement>(`/announcements/${enc(String(id))}`, a),
  remove: (id: string | number) => http.del<void>(`/announcements/${enc(String(id))}`),
};

export const studentAbsences = {
  list: async (query?: Record<string, QueryValue>) =>
    asList<StudentAbsence>(await http.get<unknown>('/student-absences', query)),
  create: (a: {
    student_id?: string;
    date_from: string;
    date_to: string;
    reason: string;
    periods?: number[];
    note?: string;
    kind?: StudentAbsenceKind;
    minutes?: number | null;
    source?: StudentAbsenceSource;
    status?: StudentAbsenceStatus;
  }) => http.post<StudentAbsence>('/student-absences', a),
  setStatus: (id: string | number, status: StudentAbsenceStatus, note?: string) =>
    http.patch<StudentAbsence>(`/student-absences/${enc(String(id))}`, { status, ...(note !== undefined ? { note } : {}) }),
  patch: (id: string | number, body: Partial<{ status: StudentAbsenceStatus; note: string; kind: StudentAbsenceKind; minutes: number; source: StudentAbsenceSource }>) =>
    http.patch<StudentAbsence>(`/student-absences/${enc(String(id))}`, body),
  /** Fehlzeiten-Übersicht eines Kindes (Standard: aktuelles Schuljahr) */
  record: (studentId: string, signal?: AbortSignal) => http.get<AttendanceRecord>('/student-absences/record', { student_id: studentId }, { signal }),
  /** Formular „Schriftliche Entschuldigung“ (PDF), optional vorausgefüllt */
  formUrl: (q: { student_id?: string; absence_id?: string | number } = {}) =>
    `${API_BASE}/student-absences/form.pdf${buildQuery({ student_id: q.student_id, absence_id: q.absence_id !== undefined ? String(q.absence_id) : undefined })}`,
  /** Formular „Antrag auf Beurlaubung“ (PDF), optional vorausgefüllt */
  leaveFormUrl: (q: { student_id?: string; absence_id?: string | number } = {}) =>
    `${API_BASE}/student-absences/leave-form.pdf${buildQuery({ student_id: q.student_id, absence_id: q.absence_id !== undefined ? String(q.absence_id) : undefined })}`,
  /** Vorschau beim Melden: Schultage und Attestpflicht für den Zeitraum */
  preview: (q: { student_id?: string; from: string; to: string }, signal?: AbortSignal) =>
    http.get<ReportPreview>('/student-absences/preview', { student_id: q.student_id, from: q.from, to: q.to }, { signal }),
  remove: (id: string | number) => http.del<void>(`/student-absences/${enc(String(id))}`),
  access: () => http.get<StudentAbsenceAccess>('/student-absences/access'),
};

// ------------------------------------------------------------------ Import / Export

export type CsvWhat = 'teachers' | 'classes' | 'rooms' | 'subjects' | 'students' | 'lessons' | 'curricula';

export const exportUrls = {
  untis: (q?: Record<string, QueryValue>) => `${API_BASE}/export/untis.zip${buildQuery(q)}`,
  schulmanagerOnline: (q?: Record<string, QueryValue>) => `${API_BASE}/export/schulmanager-online.zip${buildQuery(q)}`,
  csv: (what: CsvWhat) => `${API_BASE}/export/csv/${what}`,
  json: () => `${API_BASE}/export/json`,
  ical: (kind: string, ref: string, q?: Record<string, QueryValue>) =>
    `${API_BASE}/export/ical/${kind}/${enc(ref)}${buildQuery(q)}`,
};

export const imports = {
  /** Untis-GPU-Dateien oder ZIP; mode=merge ergänzt, replace ersetzt; dryRun = Probelauf */
  untis: (files: File[], mode: 'merge' | 'replace' = 'merge', dryRun = false) => {
    const fd = new FormData();
    for (const f of files) fd.append('files', f, f.name);
    fd.append('mode', mode);
    return http.upload<ImportReport>('/import/untis', fd, dryRun ? { dry_run: 1 } : undefined);
  },
  /** mapping: {"Spalte in Datei": "feld"} */
  csv: (what: CsvWhat, file: File, mapping: Record<string, string>, dryRun = false) => {
    const fd = new FormData();
    fd.append('file', file, file.name);
    if (Object.keys(mapping).length) fd.append('mapping', JSON.stringify(mapping));
    return http.upload<ImportReport>(`/import/csv/${what}`, fd, dryRun ? { dry_run: 1 } : undefined);
  },
  /** Komplettimport (ersetzt alles) – als Datei-Upload */
  json: (file: File, dryRun = false) => {
    const fd = new FormData();
    fd.append('file', file, file.name);
    return http.upload<ImportReport>('/import/json', fd, dryRun ? { dry_run: 1 } : undefined);
  },
};

export type { User };

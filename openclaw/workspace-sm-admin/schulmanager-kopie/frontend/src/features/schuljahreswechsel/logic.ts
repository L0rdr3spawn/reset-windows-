/** Logik des Schuljahreswechsel-Assistenten (`WechselPage.tsx`), ohne Oberfläche. */

export type ClassAction = 'promote' | 'graduate' | 'keep';

export interface PlanForm {
  new_year_start: string;
  final_grade: number | null;
  class_rules: Record<string, { action: ClassAction }>;
  extra_leavers: string[];
  rename_classes: boolean;
  new_classes: { name: string; grade: number; site: string; count: number }[];
  archive_rooms: 'none' | 'removed' | 'all';
  lock_gradebooks: boolean;
  deactivate_accounts: boolean;
  clear_lessons: boolean;
}

export interface PreviewClass {
  id: string;
  name: string;
  grade: number;
  action: ClassAction;
  new_name: string;
  new_grade: number;
  students: number;
}

export interface Preview {
  old_year: string;
  new_year: string;
  old_start: string;
  new_start: string;
  final_grade: number;
  classes: PreviewClass[];
  leavers: { count: number; by_class: Record<string, number>; sample: { id: string; name: string; class_id: string }[] };
  courses_removed: number;
  lessons_removed: number;
  new_classes: { name: string; grade: number; count: number }[];
  accounts: { students: number; parents: number };
  rooms: number;
  gradebooks: number;
  warnings: string[];
  conflicts: string[];
  token: string;
  can_execute: boolean;
}

export interface Run {
  id: string;
  at: string;
  by: string;
  old_year: string;
  new_year: string;
  summary: Record<string, number>;
  undone_at: string | null;
  notes: string[];
}

export const ACTION_LABELS: Record<ClassAction, string> = {
  promote: 'Hochstufen',
  graduate: 'Abgang',
  keep: 'Unverändert',
};

function pad(n: number): string {
  return String(n).padStart(2, '0');
}

/** Vorschlag für den Beginn des nächsten Schuljahres: Montag auf oder vor dem 31.8. (bis August: dieses Jahr, danach nächstes) */
export function suggestYearStart(today: Date = new Date()): string {
  const year = today.getMonth() <= 7 ? today.getFullYear() : today.getFullYear() + 1;
  const d = new Date(Date.UTC(year, 7, 31));
  const back = (d.getUTCDay() + 6) % 7; // Tage seit Montag
  d.setUTCDate(d.getUTCDate() - back);
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`;
}

export function defaultPlan(today: Date = new Date()): PlanForm {
  return {
    new_year_start: suggestYearStart(today),
    final_grade: null,
    class_rules: {},
    extra_leavers: [],
    rename_classes: true,
    new_classes: [],
    archive_rooms: 'removed',
    lock_gradebooks: true,
    deactivate_accounts: true,
    clear_lessons: false,
  };
}

/** Plan für die API: leere/ungültige neue Klassen weglassen */
export function toRequest(p: PlanForm): PlanForm {
  return {
    ...p,
    new_classes: p.new_classes
      .map((c) => ({ ...c, name: c.name.trim() }))
      .filter((c) => c.name && c.grade >= 1 && c.grade <= 13),
  };
}

/** Eine Klassenregel setzen; entspricht sie der automatischen Vorgabe, wird sie entfernt */
export function setRule(p: PlanForm, id: string, action: ClassAction, auto: ClassAction): PlanForm {
  const rules = { ...p.class_rules };
  if (action === auto) delete rules[id];
  else rules[id] = { action };
  return { ...p, class_rules: rules };
}

/** Kurzfassung eines Laufs für die Anzeige */
export function runText(r: Run): string {
  const s = r.summary;
  const parts = [`${s.promoted ?? 0} Klassen hochgestuft`];
  if (s.graduated) parts.push(`${s.graduated} Abgangsklassen`);
  if (s.leavers) parts.push(`${s.leavers} Abgänger/innen`);
  if (s.new_classes) parts.push(`${s.new_classes} neue Klassen`);
  if (s.accounts) parts.push(`${s.accounts} Konten gesperrt`);
  if (s.rooms) parts.push(`${s.rooms} Kursräume archiviert`);
  if (s.gradebooks) parts.push(`${s.gradebooks} Notenbücher abgeschlossen`);
  return parts.join(', ');
}

/** Typen des Notenbuchs (Server: `routes/features_gradebook.py`, `docs/NOTENBUCH.md`). */

export type ScaleKind = 'note6' | 'punkte15' | 'prozent' | 'verbal' | 'bestanden' | 'custom';
export type EntryStatus = '' | 'entschuldigt' | 'ausgelassen' | 'nachschreiben' | 'unentschuldigt';
export type Visibility = 'aus' | 'sofort' | 'freigabe' | 'endnote';
export type Rounding = 'ganz' | 'tendenz';

export interface Scale {
  id: string;
  name: string;
  kind: ScaleKind;
  builtin: boolean;
  numeric: boolean;
  higher_better: boolean;
  labels: { label: string; value: number }[];
}

export interface GradeKey {
  id: string;
  name: string;
  scale_id: string;
  builtin: boolean;
  steps: { min_percent: number; label: string }[];
}

export interface RiskSettings {
  enabled: boolean;
  min_grade: number;
  max_points: number;
  core_count: number;
  any_count: number;
}

export interface TemplateNode {
  name: string;
  weight: number;
  children?: TemplateNode[];
}

export interface GradebookSettings {
  default_scale?: string;
  scale_by_grade?: Record<string, string>;
  scale_by_course?: Record<string, string>;
  keys_default?: Record<string, string>;
  visibility: Visibility;
  show_averages: boolean;
  rounding: Rounding;
  decimals: number;
  custom_scales?: { id: string; name: string; higher_better: boolean; labels: { label: string; value: number }[] }[];
  custom_keys?: { id: string; name: string; scale_id: string; steps: { min_percent: number; label: string }[] }[];
  risk: RiskSettings;
  halfyear_split?: string;
  templates?: Record<string, TemplateNode[]>;
}

export interface TermOption {
  id: string;
  label: string;
}

export interface Meta {
  scales: Scale[];
  keys: GradeKey[];
  term: string;
  terms: TermOption[];
  settings: GradebookSettings;
  visibility_options: { id: Visibility; label: string }[];
  statuses: { id: EntryStatus; label: string }[];
  can: { use: boolean; read_class: boolean; manage: boolean; export: boolean };
  classes: { id: string; name: string; grade: number }[];
  default_template: TemplateNode[];
  export_formats: { id: string; label: string }[];
  grades: number[];
  subjects: { id: string; name: string; core: boolean }[];
}

export interface BookInfo {
  id: number;
  course_id: string;
  part: number;
  term: string;
  term_label: string;
  title: string;
  subject: string;
  subject_name: string;
  classes: string[];
  teacher_name: string;
  scale: Scale | null;
  scale_id: string;
  key_id: string;
  key: GradeKey | null;
  rounding: Rounding;
  decimals: number;
  locked: boolean;
  locked_at: string | null;
  locked_by: string;
  can_edit: boolean;
  can_unlock: boolean;
  can_lock: boolean;
  access: 'edit' | 'read' | null;
}

export interface BookListItem extends BookInfo {
  students: number;
}

export interface CourseOption {
  course_id: string;
  part: number;
  title: string;
  subject: string;
  subject_name: string;
  classes: string[];
  teacher_name: string;
  access: 'edit' | 'read';
  book_id: number | null;
  locked: boolean;
  scale_id: string;
}

export interface Category {
  id: number;
  parent_id: number | null;
  name: string;
  weight: number;
  position: number;
  depth: number;
}

export interface Item {
  id: number;
  category_id: number | null;
  title: string;
  date: string;
  weight: number;
  max_points: number | null;
  key_id: string;
  position: number;
  released: boolean;
  makeup_date: string;
  source_type: string;
  source_id: string;
  source_label: string;
}

export interface Entry {
  value: string;
  label: string;
  status: EntryStatus;
  note: string;
  makeup_date: string;
  invalid: boolean;
  from_source?: boolean;
}

export interface StudentRow {
  student_id: string;
  name: string;
  class_id: string | null;
  support: boolean;
  entries: Record<string, Entry>;
  categories: Record<string, number | null>;
  average: number | null;
  proposal: string;
  counted: number;
  final: string;
  final_note: string;
  final_by: string;
  final_at: string | null;
  overridden: boolean;
}

export interface Table {
  book: BookInfo;
  categories: Category[];
  items: Item[];
  students: StudentRow[];
  pending_sources: number;
  visibility: Visibility;
}

export interface EntryPatch {
  student_id: string;
  value?: string;
  status?: EntryStatus;
  note?: string;
  makeup_date?: string;
}

export interface SourceCandidate {
  source_type: string;
  source_label: string;
  source_id: string;
  title: string;
  date: string;
  max_points: number | null;
  count: number;
  kind: 'punkte' | 'note';
  state: 'open' | 'adopted' | 'dismissed';
  item_id: number | null;
}

export interface LogRow {
  id: number;
  at: string;
  actor: string;
  action: string;
  item_id: number | null;
  item: string;
  student_id: string;
  student: string;
  detail: Record<string, unknown>;
}

export interface ClassCell {
  value: string;
  final: boolean;
  locked: boolean;
  overridden: boolean;
  deficit: boolean;
  core: boolean;
  average: number | null;
  book_id: number;
  scale: ScaleKind;
}

export interface ClassOverview {
  class_id: string;
  term: string;
  term_label: string;
  subjects: { id: string; name: string; core: boolean }[];
  students: { student_id: string; name: string; cells: Record<string, ClassCell>; warnings: string[]; deficits: number }[];
  books: { book_id: number; subject: string; locked: boolean; title: string }[];
  risk: RiskSettings;
  locked_all: boolean;
  warning_count: number;
}

export interface MyItem {
  item_id: number;
  title: string;
  date: string;
  category_id: number | null;
  max_points: number | null;
  makeup_date: string;
  value: string;
  label: string;
  status: EntryStatus;
  note: string;
}

export interface MySubject {
  book_id: number;
  subject: string;
  subject_name: string;
  teacher_name: string;
  scale: Scale;
  final: string;
  final_note: string;
  locked: boolean;
  average: number | null;
  categories: { id: number; name: string; parent_id: number | null; average: number }[];
  items: MyItem[];
}

export interface MyGradebook {
  student: { id: string; name: string; class_id: string };
  term: string;
  term_label: string;
  terms?: TermOption[];
  visibility: Visibility;
  show_averages?: boolean;
  subjects: MySubject[];
}

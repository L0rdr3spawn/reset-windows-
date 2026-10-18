/** Typen der Anmelde-Richtlinien (§11.5, Backend `routes/features_login_policy.py`). */

export type Scope = 'default' | 'role' | 'grade' | 'class' | 'user';
export type Audience = 'alle' | 'schueler' | 'eltern';
export type PolicyField = 'methods' | 'required_links' | 'self_link' | 'reset_channels' | 'sso_create';
export type ListField = 'methods' | 'required_links' | 'reset_channels';
export type BoolField = 'self_link' | 'sso_create';

/** Felder einer Regel – `null` = erben. */
export interface RuleValues {
  methods: string[] | null;
  required_links: string[] | null;
  self_link: boolean | null;
  reset_channels: string[] | null;
  sso_create: boolean | null;
}

export interface RuleBody extends RuleValues {
  note: string;
}

export interface TargetKey {
  scope: Scope;
  ref: string;
  audience: Audience;
}

export interface PersonRef {
  id: number;
  username: string;
  display_name: string;
  role: string;
  active?: boolean;
}

export interface PolicyRule extends RuleValues, TargetKey {
  id: number;
  label: string;
  note: string;
  updated_at: string | null;
  updated_by: { id: number; name: string } | null;
  /** Klasse/Jahrgang/Person gibt es nicht mehr */
  orphan: boolean;
  target: (PersonRef | { id: string; name: string; grade: string | null }) | null;
}

/** Wirksame Werte mit Herkunft je Feld. */
export interface PolicyValues {
  methods: string[];
  required_links: string[];
  self_link: boolean;
  reset_channels: string[];
  sso_create: boolean;
  sources: Partial<Record<PolicyField, string>>;
}

export interface Option {
  id: string;
  label: string;
}

export interface ProviderOption extends Option {
  available: boolean;
  mock: boolean;
}

export interface ClassOption {
  id: string;
  name: string;
  grade: string;
}

export interface PolicyOptions {
  roles: (Option & { manageable: boolean })[];
  grades: (Option & { classes: number })[];
  classes: ClassOption[];
  providers: ProviderOption[];
  methods: Option[];
  reset_channels: (Option & { available: boolean })[];
  audiences: Option[];
  fields: Record<PolicyField, string>;
}

export interface PoliciesResponse {
  rules: PolicyRule[];
  options: PolicyOptions;
  defaults: PolicyValues;
  can_manage_admins: boolean;
}

export interface EffectiveMember {
  student_id: string;
  name: string;
  class: ClassOption | null;
}

export interface EffectiveResponse {
  target:
    | { kind: 'user'; user: PersonRef; students: EffectiveMember[] }
    | { kind: 'class'; class: ClassOption; audience: Audience }
    | { kind: 'grade'; grade: string; audience: Audience }
    | { kind: 'role'; role: string };
  policy: PolicyValues;
  /** nur Person: Werte ohne die Personen-Regel */
  inherited?: PolicyValues;
  linked?: string[];
  missing_links?: string[];
  password_login?: 'ok' | 'setup' | 'denied';
}

export interface ReportCounts {
  accounts: number;
  required: number;
  complete: number;
  missing: number;
}

export interface ReportItem {
  user: PersonRef;
  group: 'schueler' | 'eltern';
  students: { id: string; name: string }[];
  required: string[];
  linked: string[];
  missing: string[];
  last_login: string | null;
}

export interface ReportResponse {
  class: ClassOption;
  audience: Audience;
  counts: Record<'schueler' | 'eltern', ReportCounts>;
  students_total: number;
  students_without_account: number | null;
  items: ReportItem[];
}

/** Öffentliche Anbieterliste (`GET /auth/sso/providers`, Agent Anbieter). */
export interface SsoProvider {
  id: string;
  label: string;
  mock?: boolean;
}

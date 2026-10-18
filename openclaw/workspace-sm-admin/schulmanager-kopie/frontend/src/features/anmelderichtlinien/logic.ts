/**
 * Reine Logik der Anmelde-Richtlinien (§11.5): Vererbung für die Anzeige „erbt …“ (gleicher Vorrang wie das
 * Backend `server/login_policy.py`), Formular ↔ Regel, Kurzfassungen, Beispiel-Voreinstellung, Verknüpfungsliste.
 *
 * Vorrang je Feld: Person > Klasse (Zielgruppe vor „alle“) > Jahrgang (Zielgruppe vor „alle“) > Rolle > Standard >
 * Voreinstellung. Personen-Regeln löst das Backend auf (`GET /login-policies/effective?user_id=` → `inherited`).
 */
import type {
  Audience,
  BoolField,
  ListField,
  PolicyField,
  PolicyRule,
  PolicyValues,
  RuleBody,
  RuleValues,
  Scope,
  TargetKey,
} from './types';

export const FIELDS: readonly PolicyField[] = ['methods', 'required_links', 'self_link', 'reset_channels', 'sso_create'];
export const LIST_FIELDS: readonly ListField[] = ['methods', 'required_links', 'reset_channels'];
export const BOOL_FIELDS: readonly BoolField[] = ['self_link', 'sso_create'];

export const FIELD_LABELS: Record<PolicyField, string> = {
  methods: 'Anmeldewege',
  required_links: 'Pflicht-Verknüpfungen',
  self_link: 'Konten selbst verbinden/trennen',
  reset_channels: '„Passwort vergessen“ per',
  sso_create: 'Beim ersten Anbieter-Login per E-Mail zuordnen',
};

export const FIELD_HINTS: Record<PolicyField, string> = {
  methods: 'Womit darf man sich anmelden? Ohne „Passwort“ geht es nur noch über die gewählten Anbieter.',
  required_links: 'Diese Konten müssen verbunden sein – sonst führt jede Anmeldung zuerst auf „Konten verbinden“.',
  self_link: 'Darf die Person im Profil eigene Anbieter-Konten verbinden und wieder trennen?',
  reset_channels:
    'Über welche bestätigten Kontaktwege darf man ein neues Passwort selbst anfordern? Keine Auswahl = nicht selbst zurücksetzbar; dann setzen Klassenleitung bzw. Verwaltung zurück.',
  sso_create:
    'Meldet sich jemand zum ersten Mal mit einem Anbieter an, wird das Konto über die bestätigte E-Mail-Adresse zugeordnet.',
};

export const AUDIENCE_LABELS: Record<Audience, string> = { alle: 'Alle', schueler: 'Schüler/innen', eltern: 'Eltern' };

export const METHOD_LABELS: Record<string, string> = {
  password: 'Passwort',
  microsoft: 'Microsoft',
  apple: 'Apple',
  google: 'Google',
  oidc: 'Schulkonto',
};
export const CHANNEL_LABELS: Record<string, string> = { email: 'E-Mail', sms: 'SMS' };

export const BUILTIN_SOURCE = 'Voreinstellung';

/** Eindeutiger Schlüssel einer Regel. */
export function ruleKey(t: TargetKey): string {
  return `${t.scope}|${t.scope === 'default' ? '' : t.ref}|${t.audience}`;
}

export function indexRules(rules: readonly PolicyRule[]): Map<string, PolicyRule> {
  return new Map(rules.map((r) => [ruleKey(r), r]));
}

export function hasAudience(scope: Scope): boolean {
  return scope === 'grade' || scope === 'class';
}

/** Rolle hinter einer Zielgruppe (für die Vererbung). */
function audienceRole(aud: Exclude<Audience, 'alle'>): string {
  return aud;
}

export interface InheritChain {
  /** Zielgruppe, für die diese Kette gilt (`null` = für alle gleich) */
  audience: Exclude<Audience, 'alle'> | null;
  chain: TargetKey[];
}

/** Stufen unterhalb von `target`, aus denen es erbt (ohne Person). `grade` = Jahrgang der Klasse. */
export function inheritChains(target: TargetKey, grade?: string | null): InheritChain[] {
  const def: TargetKey = { scope: 'default', ref: '', audience: 'alle' };
  const role = (r: string): TargetKey => ({ scope: 'role', ref: r, audience: 'alle' });
  const gradeKeys = (g: string | null | undefined, aud: Audience): TargetKey[] =>
    g == null
      ? []
      : aud === 'alle'
        ? [{ scope: 'grade', ref: g, audience: 'alle' }]
        : [
            { scope: 'grade', ref: g, audience: aud },
            { scope: 'grade', ref: g, audience: 'alle' },
          ];
  switch (target.scope) {
    case 'default':
      return [{ audience: null, chain: [] }];
    case 'role':
      return [{ audience: null, chain: [def] }];
    case 'user':
      // Person: Klasse/Rolle kennt nur das Backend → `GET /login-policies/effective?user_id=` (`inherited`)
      return [{ audience: null, chain: [def] }];
    case 'grade':
    case 'class': {
      const auds: Exclude<Audience, 'alle'>[] = target.audience === 'alle' ? ['schueler', 'eltern'] : [target.audience];
      const g = target.scope === 'grade' ? target.ref : grade;
      return auds.map((aud) => {
        const chain: TargetKey[] = [];
        if (target.audience !== 'alle') chain.push({ ...target, audience: 'alle' });
        if (target.scope === 'class') chain.push(...gradeKeys(g, aud));
        chain.push(role(audienceRole(aud)), def);
        return { audience: target.audience === 'alle' ? aud : null, chain };
      });
    }
  }
}

/** Wert eines Feldes über eine Kette auflösen (erster gesetzter Wert, sonst Voreinstellung). */
export function resolveChain(
  rules: Map<string, PolicyRule>,
  chain: readonly TargetKey[],
  defaults: PolicyValues,
): PolicyValues {
  const out: PolicyValues = {
    methods: defaults.methods,
    required_links: defaults.required_links,
    self_link: defaults.self_link,
    reset_channels: defaults.reset_channels,
    sso_create: defaults.sso_create,
    sources: {},
  };
  for (const f of FIELDS) {
    let found = false;
    for (const key of chain) {
      const rule = rules.get(ruleKey(key));
      const value = rule?.[f];
      if (rule && value !== null && value !== undefined && !(f === 'methods' && Array.isArray(value) && value.length === 0)) {
        (out as unknown as Record<string, unknown>)[f] = value;
        out.sources[f] = rule.label;
        found = true;
        break;
      }
    }
    if (!found) out.sources[f] = BUILTIN_SOURCE;
  }
  return out;
}

export function sameValues(a: PolicyValues, b: PolicyValues): boolean {
  return FIELDS.every((f) => JSON.stringify(normalize(a[f])) === JSON.stringify(normalize(b[f])) && a.sources[f] === b.sources[f]);
}

function normalize(v: unknown): unknown {
  return Array.isArray(v) ? [...v].sort() : v;
}

export interface Inherited {
  audience: Exclude<Audience, 'alle'> | null;
  values: PolicyValues;
}

/** Was erbt `target`? Bei „alle“ in Jahrgang/Klasse ggf. getrennt für Schüler/innen und Eltern. */
export function inheritedFor(
  rules: readonly PolicyRule[],
  target: TargetKey,
  defaults: PolicyValues,
  grade?: string | null,
): Inherited[] {
  const index = indexRules(rules);
  const list = inheritChains(target, grade).map((c) => ({ audience: c.audience, values: resolveChain(index, c.chain, defaults) }));
  if (list.length === 2 && list[0] && list[1] && sameValues(list[0].values, list[1].values)) return [{ audience: null, values: list[0].values }];
  return list;
}

// ------------------------------------------------------------------ Formular ↔ Regel
export interface FieldState<T> {
  inherit: boolean;
  value: T;
}

export interface RuleForm {
  methods: FieldState<string[]>;
  required_links: FieldState<string[]>;
  self_link: FieldState<boolean>;
  reset_channels: FieldState<string[]>;
  sso_create: FieldState<boolean>;
  note: string;
}

/** Regel (oder keine) → Formular; geerbte Felder übernehmen den geerbten Wert als Startwert fürs Festlegen. */
export function ruleToForm(rule: Partial<RuleValues> & { note?: string } | null, inherited?: PolicyValues): RuleForm {
  const list = (f: ListField): FieldState<string[]> => {
    const v = rule?.[f];
    return v == null ? { inherit: true, value: [...(inherited?.[f] ?? [])] } : { inherit: false, value: [...v] };
  };
  const bool = (f: BoolField, fallback: boolean): FieldState<boolean> => {
    const v = rule?.[f];
    return v == null ? { inherit: true, value: inherited?.[f] ?? fallback } : { inherit: false, value: v };
  };
  return {
    methods: list('methods'),
    required_links: list('required_links'),
    self_link: bool('self_link', true),
    reset_channels: list('reset_channels'),
    sso_create: bool('sso_create', false),
    note: rule?.note ?? '',
  };
}

/** Reihenfolge der Auswahl beibehalten (wie im Backend). */
export function ordered(values: readonly string[], order: readonly string[]): string[] {
  const set = new Set(values);
  return [...order.filter((o) => set.has(o)), ...[...set].filter((v) => !order.includes(v)).sort()];
}

export function formToBody(form: RuleForm, orders: Partial<Record<ListField, readonly string[]>> = {}): RuleBody {
  const fallback = (f: ListField) => Object.keys(f === 'reset_channels' ? CHANNEL_LABELS : METHOD_LABELS);
  const list = (f: ListField) => (form[f].inherit ? null : ordered(form[f].value, orders[f] ?? fallback(f)));
  return {
    methods: list('methods'),
    required_links: list('required_links'),
    self_link: form.self_link.inherit ? null : form.self_link.value,
    reset_channels: list('reset_channels'),
    sso_create: form.sso_create.inherit ? null : form.sso_create.value,
    note: form.note.trim(),
  };
}

export function isEmptyBody(body: RuleValues): boolean {
  return FIELDS.every((f) => body[f] === null);
}

/** Prüfungen vor dem Speichern (das Backend prüft dasselbe noch einmal). */
export function validateForm(form: RuleForm): Partial<Record<PolicyField, string>> {
  const errors: Partial<Record<PolicyField, string>> = {};
  if (!form.methods.inherit && form.methods.value.length === 0) {
    errors.methods = 'Mindestens einen Anmeldeweg auswählen – sonst kann sich niemand mehr anmelden.';
  }
  return errors;
}

/** Hinweise zur Kombination (kein Fehler): Pflicht-Anbieter, die nicht zum Anmelden erlaubt sind, u. ä. */
export function formWarnings(form: RuleForm, inherited?: PolicyValues): string[] {
  const methods = form.methods.inherit ? inherited?.methods ?? [] : form.methods.value;
  const required = form.required_links.inherit ? inherited?.required_links ?? [] : form.required_links.value;
  const out: string[] = [];
  const notLogin = required.filter((p) => !methods.includes(p));
  if (notLogin.length) {
    out.push(`${listText(notLogin, METHOD_LABELS)} muss verbunden werden, ist aber kein erlaubter Anmeldeweg – das Konto wird nur verknüpft.`);
  }
  if (methods.length > 0 && !methods.includes('password')) {
    out.push('Ohne Passwort: Mit dem Startpasswort ist nur noch die Ersteinrichtung möglich (Konten verbinden).');
  }
  return out;
}

/** Beispiel: „Schüler/innen: nur Microsoft + Apple, beide Pflicht“ (übrige Felder bleiben, wie sie sind). */
export function applyMicrosoftApplePreset(form: RuleForm): RuleForm {
  return {
    ...form,
    methods: { inherit: false, value: ['microsoft', 'apple'] },
    required_links: { inherit: false, value: ['microsoft', 'apple'] },
  };
}

// ------------------------------------------------------------------ Anzeige
export function listText(ids: readonly string[], labels: Record<string, string>): string {
  if (!ids.length) return 'keine';
  return ids.map((id) => labels[id] ?? id).join(', ');
}

export function valueText(field: PolicyField, value: unknown): string {
  if (field === 'self_link' || field === 'sso_create') return value ? 'Ja' : 'Nein';
  const ids = Array.isArray(value) ? (value as string[]) : [];
  return listText(ids, field === 'reset_channels' ? CHANNEL_LABELS : METHOD_LABELS);
}

/** Kurzfassung einer Regel für Listen, z. B. „Anmeldewege: Microsoft, Apple“. */
export function summarizeRule(rule: RuleValues | null | undefined): string[] {
  if (!rule) return [];
  return FIELDS.filter((f) => rule[f] !== null && rule[f] !== undefined).map((f) => `${FIELD_LABELS[f]}: ${valueText(f, rule[f])}`);
}

export interface EffectiveRow {
  field: PolicyField;
  label: string;
  value: string;
  source: string;
}

export function effectiveRows(p: PolicyValues): EffectiveRow[] {
  return FIELDS.map((f) => ({ field: f, label: FIELD_LABELS[f], value: valueText(f, p[f]), source: p.sources[f] ?? BUILTIN_SOURCE }));
}

/** Klassen nach Name/Jahrgang filtern (Suche „5“, „5a“, „Q1“). */
export function filterClasses<T extends { id: string; name: string; grade: string }>(classes: readonly T[], q: string): T[] {
  const s = q.trim().toLowerCase();
  if (!s) return [...classes];
  return classes.filter((c) => c.name.toLowerCase().includes(s) || c.id.toLowerCase().includes(s) || c.grade === s);
}

// ------------------------------------------------------------------ Konten verbinden (/konten-verbinden)
export interface LinkItem {
  id: string;
  label: string;
  available: boolean;
}

/** Fehlende Pflicht-Anbieter mit Verfügbarkeit (öffentliche Anbieterliste). */
export function linkItems(missing: readonly string[], available: readonly { id: string; label?: string }[] | null): LinkItem[] {
  const byId = new Map((available ?? []).map((p) => [p.id, p]));
  return missing.map((id) => ({ id, label: byId.get(id)?.label?.replace(/\s*\(Test\)$/, '') ?? METHOD_LABELS[id] ?? id, available: byId.has(id) }));
}

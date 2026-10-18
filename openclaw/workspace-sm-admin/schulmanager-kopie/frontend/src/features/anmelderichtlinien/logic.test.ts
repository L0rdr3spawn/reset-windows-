import { describe, expect, it } from 'vitest';
import {
  applyMicrosoftApplePreset,
  effectiveRows,
  filterClasses,
  formToBody,
  formWarnings,
  inheritChains,
  inheritedFor,
  isEmptyBody,
  linkItems,
  ruleToForm,
  summarizeRule,
  validateForm,
} from './logic';
import type { PolicyRule, PolicyValues } from './types';

const DEFAULTS: PolicyValues = {
  methods: ['password', 'microsoft', 'apple', 'google', 'oidc'],
  required_links: [],
  self_link: true,
  reset_channels: ['email', 'sms'],
  sso_create: false,
  sources: {},
};

function rule(scope: PolicyRule['scope'], ref: string, audience: PolicyRule['audience'], values: Partial<PolicyRule>, label: string): PolicyRule {
  return {
    id: 1,
    scope,
    ref,
    audience,
    label,
    note: '',
    updated_at: null,
    updated_by: null,
    orphan: false,
    target: null,
    methods: null,
    required_links: null,
    self_link: null,
    reset_channels: null,
    sso_create: null,
    ...values,
  };
}

const RULES: PolicyRule[] = [
  rule('default', '', 'alle', { reset_channels: ['email'] }, 'Standard'),
  rule('role', 'schueler', 'alle', { methods: ['password', 'microsoft'] }, 'Rolle Schüler/in'),
  rule('grade', '5', 'schueler', { methods: ['microsoft', 'apple'] }, 'Jahrgang 5 · Schüler/innen'),
  rule('grade', '5', 'alle', { self_link: false }, 'Jahrgang 5'),
  rule('class', '5a', 'alle', { sso_create: true }, 'Klasse 5a'),
];

describe('Vererbung (Anzeige „erbt …“)', () => {
  it('Klasse + Zielgruppe erbt von Klasse „alle“, Jahrgang (Zielgruppe vor alle), Rolle, Standard', () => {
    const chains = inheritChains({ scope: 'class', ref: '5a', audience: 'schueler' }, '5');
    expect(chains).toHaveLength(1);
    expect(chains[0]?.chain.map((k) => `${k.scope}:${k.ref}:${k.audience}`)).toEqual([
      'class:5a:alle',
      'grade:5:schueler',
      'grade:5:alle',
      'role:schueler:alle',
      'default::alle',
    ]);
    const [inh] = inheritedFor(RULES, { scope: 'class', ref: '5a', audience: 'schueler' }, DEFAULTS, '5');
    expect(inh?.values.methods).toEqual(['microsoft', 'apple']);
    expect(inh?.values.sources.methods).toBe('Jahrgang 5 · Schüler/innen');
    expect(inh?.values.sso_create).toBe(true);
    expect(inh?.values.self_link).toBe(false);
    expect(inh?.values.reset_channels).toEqual(['email']);
    expect(inh?.values.sources.required_links).toBe('Voreinstellung');
  });

  it('„alle“ in einer Klasse zeigt getrennte Werte für Schüler/innen und Eltern', () => {
    const list = inheritedFor(RULES, { scope: 'class', ref: '5a', audience: 'alle' }, DEFAULTS, '5');
    expect(list.map((x) => x.audience)).toEqual(['schueler', 'eltern']);
    expect(list[1]?.values.methods).toEqual(DEFAULTS.methods);
    // ohne Unterschiede: eine Zeile
    const same = inheritedFor([RULES[0] as PolicyRule], { scope: 'grade', ref: '7', audience: 'alle' }, DEFAULTS);
    expect(same).toHaveLength(1);
    expect(same[0]?.audience).toBeNull();
  });

  it('Rolle erbt nur vom Standard, Standard von der Voreinstellung', () => {
    expect(inheritedFor(RULES, { scope: 'role', ref: 'lehrer', audience: 'alle' }, DEFAULTS)[0]?.values.reset_channels).toEqual(['email']);
    expect(inheritedFor(RULES, { scope: 'default', ref: '', audience: 'alle' }, DEFAULTS)[0]?.values.sources.reset_channels).toBe('Voreinstellung');
  });
});

describe('Formular ↔ Regel', () => {
  it('erben = null, festlegen = Werte in fester Reihenfolge', () => {
    const form = ruleToForm(null, DEFAULTS);
    expect(form.methods.inherit).toBe(true);
    expect(form.methods.value).toEqual(DEFAULTS.methods);
    expect(isEmptyBody(formToBody(form))).toBe(true);
    const set = { ...form, methods: { inherit: false, value: ['apple', 'password'] }, self_link: { inherit: false, value: false } };
    const body = formToBody(set, { methods: ['password', 'microsoft', 'apple'] });
    expect(body.methods).toEqual(['password', 'apple']);
    expect(body.self_link).toBe(false);
    expect(body.required_links).toBeNull();
    expect(ruleToForm(body).methods).toEqual({ inherit: false, value: ['password', 'apple'] });
  });

  it('leere Anmeldewege sind ungültig, Pflicht ohne Anmeldeweg gibt einen Hinweis', () => {
    const form = { ...ruleToForm(null, DEFAULTS), methods: { inherit: false, value: [] as string[] } };
    expect(validateForm(form).methods).toMatch(/Mindestens/);
    const preset = applyMicrosoftApplePreset(ruleToForm(null, DEFAULTS));
    expect(validateForm(preset)).toEqual({});
    expect(formToBody(preset)).toMatchObject({ methods: ['microsoft', 'apple'], required_links: ['microsoft', 'apple'], self_link: null });
    expect(formWarnings(preset, DEFAULTS).join(' ')).toMatch(/Ohne Passwort/);
    const odd = { ...ruleToForm(null, DEFAULTS), methods: { inherit: false, value: ['password'] }, required_links: { inherit: false, value: ['google'] } };
    expect(formWarnings(odd, DEFAULTS)[0]).toMatch(/Google muss verbunden werden/);
  });

  it('Kurzfassung und Wirksam-Tabelle', () => {
    expect(summarizeRule(RULES[1])).toEqual(['Anmeldewege: Passwort, Microsoft']);
    expect(summarizeRule(rule('default', '', 'alle', { required_links: [] }, 'Standard'))).toEqual(['Pflicht-Verknüpfungen: keine']);
    const rows = effectiveRows({ ...DEFAULTS, sources: { methods: 'Klasse 5a' } });
    expect(rows[0]).toEqual({ field: 'methods', label: 'Anmeldewege', value: 'Passwort, Microsoft, Apple, Google, Schulkonto', source: 'Klasse 5a' });
    expect(rows.find((r) => r.field === 'sso_create')?.value).toBe('Nein');
  });
});

describe('Hilfen', () => {
  it('Klassensuche', () => {
    const classes = [
      { id: '5a', name: '5a', grade: '5' },
      { id: '10a', name: '10a', grade: '10' },
      { id: 'Q1-1', name: 'Jg. 11 Tutorium 1', grade: '11' },
    ];
    expect(filterClasses(classes, '5').map((c) => c.id)).toEqual(['5a']);
    expect(filterClasses(classes, 'q1').map((c) => c.id)).toEqual(['Q1-1']);
    expect(filterClasses(classes, '11').map((c) => c.id)).toEqual(['Q1-1']);
    expect(filterClasses(classes, '')).toHaveLength(3);
  });

  it('Konten verbinden: Verfügbarkeit und Beschriftung', () => {
    const items = linkItems(['microsoft', 'apple'], [{ id: 'microsoft', label: 'Microsoft (Test)' }]);
    expect(items).toEqual([
      { id: 'microsoft', label: 'Microsoft', available: true },
      { id: 'apple', label: 'Apple', available: false },
    ]);
    expect(linkItems(['oidc'], null)[0]).toEqual({ id: 'oidc', label: 'Schulkonto', available: false });
  });
});

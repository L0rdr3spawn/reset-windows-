/**
 * Regel-Editor (Dialog): je Feld „erben“ oder festlegen, Anzeige des geerbten Werts mit Herkunft,
 * Beispiel-Voreinstellung „nur Microsoft + Apple, beide Pflicht“, Notiz, Entfernen.
 */
import { useId, useMemo, useState, type ReactNode } from 'react';
import { errorMessage } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { policyApi } from './api';
import {
  AUDIENCE_LABELS,
  FIELD_HINTS,
  FIELD_LABELS,
  applyMicrosoftApplePreset,
  formToBody,
  formWarnings,
  inheritedFor,
  isEmptyBody,
  ruleToForm,
  validateForm,
  valueText,
  type Inherited,
  type RuleForm,
} from './logic';
import type { BoolField, ListField, PoliciesResponse, PolicyField, PolicyRule, PolicyValues, TargetKey } from './types';

export interface EditTarget extends TargetKey {
  label: string;
  /** Jahrgang einer Klasse (Vererbung) */
  grade?: string | null;
  /** Person/Rolle der Administration */
  admin?: boolean;
  /** Beispiel beim Öffnen übernehmen */
  preset?: boolean;
}

function InheritedText({ field, inherited }: { field: PolicyField; inherited: Inherited[] }) {
  return (
    <span className="small muted">
      {inherited.map((x, i) => (
        <span key={i} className="ar-inherit">
          {x.audience ? `${AUDIENCE_LABELS[x.audience]}: ` : ''}
          <strong>{valueText(field, x.values[field])}</strong> <span>({x.values.sources[field] ?? 'Voreinstellung'})</span>
        </span>
      ))}
    </span>
  );
}

function FieldBlock({
  field,
  inherit,
  onInherit,
  inherited,
  children,
  error,
}: {
  field: PolicyField;
  inherit: boolean;
  onInherit: (v: boolean) => void;
  inherited: Inherited[];
  children: ReactNode;
  error?: string;
}) {
  const id = useId();
  return (
    <fieldset className="ar-field" aria-describedby={`${id}-hint`}>
      <legend>{FIELD_LABELS[field]}</legend>
      <p className="small muted ar-hint" id={`${id}-hint`}>
        {FIELD_HINTS[field]}
      </p>
      <div className="ar-mode" role="radiogroup" aria-label={`${FIELD_LABELS[field]}: erben oder festlegen`}>
        <label className="check">
          <input type="radio" name={`${id}-mode`} checked={inherit} onChange={() => onInherit(true)} />
          <span>
            Erben – <InheritedText field={field} inherited={inherited} />
          </span>
        </label>
        <label className="check">
          <input type="radio" name={`${id}-mode`} checked={!inherit} onChange={() => onInherit(false)} />
          <span>Für diesen Bereich festlegen</span>
        </label>
      </div>
      {!inherit && <div className="ar-values">{children}</div>}
      {error && (
        <p className="error-text" role="alert">
          {error}
        </p>
      )}
    </fieldset>
  );
}

function Checks({
  options,
  value,
  onChange,
  label,
}: {
  options: { id: string; label: string; note?: string }[];
  value: string[];
  onChange: (v: string[]) => void;
  label: string;
}) {
  return (
    <div className="check-grid" role="group" aria-label={label}>
      {options.map((o) => (
        <label key={o.id} className="check">
          <input
            type="checkbox"
            checked={value.includes(o.id)}
            onChange={(e) => onChange(e.target.checked ? [...value, o.id] : value.filter((v) => v !== o.id))}
          />
          <span>
            {o.label}
            {o.note && <span className="small muted"> ({o.note})</span>}
          </span>
        </label>
      ))}
    </div>
  );
}

function YesNo({ value, onChange, label }: { value: boolean; onChange: (v: boolean) => void; label: string }) {
  const name = useId();
  return (
    <div className="check-grid" role="radiogroup" aria-label={label}>
      <label className="check">
        <input type="radio" name={name} checked={value} onChange={() => onChange(true)} /> Ja
      </label>
      <label className="check">
        <input type="radio" name={name} checked={!value} onChange={() => onChange(false)} /> Nein
      </label>
    </div>
  );
}

export function RuleEditor({
  target,
  rule,
  data,
  onClose,
  onSaved,
}: {
  target: EditTarget;
  rule: PolicyRule | undefined;
  data: PoliciesResponse;
  onClose: () => void;
  onSaved: () => void;
}) {
  const toast = useToast();
  const isUser = target.scope === 'user';
  // Person: Vererbung ohne Personen-Regel kommt vom Backend (Klasse/Kinder/Rolle der Person)
  const personal = useApi((signal) => policyApi.effectiveUser(Number(target.ref), signal), [target.ref], { enabled: isUser });
  const inherited = useMemo<Inherited[] | null>(() => {
    if (isUser) return personal.data?.inherited ? [{ audience: null, values: personal.data.inherited }] : null;
    return inheritedFor(data.rules, target, data.defaults, target.grade);
  }, [isUser, personal.data, data, target]);
  const firstInherited: PolicyValues | undefined = inherited?.[0]?.values;

  const [form, setForm] = useState<RuleForm | null>(null);
  const current = form ?? (inherited ? ruleToForm(rule ?? null, firstInherited) : null);
  const effectiveForm = current && target.preset && !form ? applyMicrosoftApplePreset(current) : current;
  const [error, setError] = useState<string | null>(null);

  if (!effectiveForm || !inherited) {
    return (
      <Modal title={`Regel: ${target.label}`} onClose={onClose} size="lg">
        {personal.error ? <Alert kind="error">{errorMessage(personal.error)}</Alert> : <Loading />}
      </Modal>
    );
  }
  const f = effectiveForm;
  const update = (patch: Partial<RuleForm>) => setForm({ ...f, ...patch });
  const setList = (field: ListField, patch: Partial<RuleForm[ListField]>) => update({ [field]: { ...f[field], ...patch } } as Partial<RuleForm>);
  const setBool = (field: BoolField, patch: Partial<RuleForm[BoolField]>) => update({ [field]: { ...f[field], ...patch } } as Partial<RuleForm>);
  const errors = validateForm(f);
  const warnings = formWarnings(f, firstInherited);
  const orders = {
    methods: data.options.methods.map((m) => m.id),
    required_links: data.options.providers.map((p) => p.id),
    reset_channels: data.options.reset_channels.map((c) => c.id),
  };
  const providerNote = (id: string) => {
    const p = data.options.providers.find((x) => x.id === id);
    if (!p) return undefined;
    if (!p.available) return 'noch nicht eingerichtet';
    return p.mock ? 'Test-Anbieter' : undefined;
  };
  const methodOptions = data.options.methods.map((m) => ({ id: m.id, label: m.label, note: m.id === 'password' ? undefined : providerNote(m.id) }));
  const providerOptions = data.options.providers.map((p) => ({ id: p.id, label: p.label, note: providerNote(p.id) }));
  const channelOptions = data.options.reset_channels.map((c) => ({ id: c.id, label: c.label, note: c.available ? undefined : 'derzeit nicht zustellbar' }));

  const save = async () => {
    setError(null);
    if (Object.keys(errors).length) return;
    const body = formToBody(f, orders);
    try {
      await policyApi.save(target.scope, target.ref, target.audience, body);
      toast.show('success', isEmptyBody(body) ? `Regel „${target.label}“ entfernt – alles wird geerbt.` : `Regel „${target.label}“ gespeichert.`);
      onSaved();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  const remove = async () => {
    setError(null);
    try {
      await policyApi.remove(target.scope, target.ref, target.audience);
      toast.show('success', `Regel „${target.label}“ entfernt.`);
      onSaved();
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  return (
    <Modal
      title={`Regel: ${target.label}`}
      onClose={onClose}
      size="lg"
      footer={
        <div className="ar-footer">
          {rule && (
            <AsyncButton className="btn btn-ghost ar-danger" onClick={remove} confirm={`Regel „${target.label}“ wirklich entfernen?`}>
              <Icon name="trash" /> Regel entfernen
            </AsyncButton>
          )}
          <span className="ar-grow" />
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={save} disabled={Object.keys(errors).length > 0}>
            <Icon name="check" /> Speichern
          </AsyncButton>
        </div>
      }
    >
      <div className="stack ar-editor">
        <p className="small muted">
          Regel für <strong>{target.label}</strong>
          <HelpTip>„Erben“ übernimmt den Wert des allgemeineren Bereichs (Person › Klasse › Jahrgang › Rolle › Standard). Nur festgelegte Felder gelten für {target.label}.</HelpTip>
        </p>
        {target.admin && (
          <Alert kind="info" title="Administration">
            Passwort-Anmeldung immer erlaubt, keine Pflicht-Verknüpfungen.
            <HelpTip>Das schützt vor dem Aussperren.</HelpTip>
          </Alert>
        )}
        {personal.data?.target.kind === 'user' && personal.data.target.students.length > 0 && (
          <p className="small">
            <span className="muted">Gehört zu: </span>
            {personal.data.target.students.map((s) => `${s.name}${s.class ? ` (Klasse ${s.class.name})` : ''}`).join(', ')}
          </p>
        )}
        <div className="row ar-preset">
          <button type="button" className="btn btn-sm" onClick={() => setForm(applyMicrosoftApplePreset(f))}>
            <Icon name="sparkles" /> Beispiel: nur Microsoft + Apple, beide Pflicht
          </button>
        </div>

        <FieldBlock field="methods" inherit={f.methods.inherit} onInherit={(v) => setList('methods', { inherit: v })} inherited={inherited} error={errors.methods}>
          <Checks label={FIELD_LABELS.methods} options={methodOptions} value={f.methods.value} onChange={(v) => setList('methods', { value: v })} />
        </FieldBlock>
        <FieldBlock
          field="required_links"
          inherit={f.required_links.inherit}
          onInherit={(v) => setList('required_links', { inherit: v })}
          inherited={inherited}
        >
          <Checks
            label={FIELD_LABELS.required_links}
            options={providerOptions}
            value={f.required_links.value}
            onChange={(v) => setList('required_links', { value: v })}
          />
          {f.required_links.value.length === 0 && <p className="small muted">Keine Auswahl = ausdrücklich keine Pflicht-Verknüpfung.</p>}
        </FieldBlock>
        <FieldBlock field="self_link" inherit={f.self_link.inherit} onInherit={(v) => setBool('self_link', { inherit: v })} inherited={inherited}>
          <YesNo label={FIELD_LABELS.self_link} value={f.self_link.value} onChange={(v) => setBool('self_link', { value: v })} />
        </FieldBlock>
        <FieldBlock
          field="reset_channels"
          inherit={f.reset_channels.inherit}
          onInherit={(v) => setList('reset_channels', { inherit: v })}
          inherited={inherited}
        >
          <Checks
            label={FIELD_LABELS.reset_channels}
            options={channelOptions}
            value={f.reset_channels.value}
            onChange={(v) => setList('reset_channels', { value: v })}
          />
          {f.reset_channels.value.length === 0 && <p className="small muted">Keine Auswahl = „Passwort vergessen“ abgeschaltet.</p>}
        </FieldBlock>
        <FieldBlock field="sso_create" inherit={f.sso_create.inherit} onInherit={(v) => setBool('sso_create', { inherit: v })} inherited={inherited}>
          <YesNo label={FIELD_LABELS.sso_create} value={f.sso_create.value} onChange={(v) => setBool('sso_create', { value: v })} />
        </FieldBlock>

        <div className="field">
          <label htmlFor="ar-note">Notiz (intern, optional)</label>
          <input id="ar-note" type="text" maxLength={500} value={f.note} onChange={(e) => update({ note: e.target.value })} />
        </div>
        {warnings.length > 0 && (
          <Alert kind="warning" title="Bitte beachten">
            <ul className="ar-list">
              {warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          </Alert>
        )}
        <div aria-live="polite">{error && <Alert kind="error" title="Nicht gespeichert">{error}</Alert>}</div>
      </div>
    </Modal>
  );
}

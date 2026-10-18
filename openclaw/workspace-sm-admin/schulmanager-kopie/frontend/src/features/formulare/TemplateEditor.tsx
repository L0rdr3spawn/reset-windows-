/**
 * Formular-Baukasten (`/formulare/vorlage/:id`): Felder, Zielgruppe, Ablauf, Fristen, Aktionen, Vorschau.
 * Änderungen an Felder/Ablauf erzeugen – sobald es Einreichungen gibt – automatisch eine neue Version.
 */
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { AsyncButton, ErrorBox, Field, FormErrors, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useTitle } from '../../hooks/misc';
import {
  formsApi,
  type AbsenceKind,
  type ActionType,
  type Answers,
  type AudienceRole,
  type FormAction,
  type FormDefinition,
  type FormField,
  type FormStep,
  type FormsMeta,
  type TemplateStatus,
} from './api';
import { FormFields } from './FormFields';
import { TEMPLATE_LABEL, TEMPLATE_TONE, dropFieldRefs, emptyDefinition, fieldsOfType, hasOptions, initialAnswers, moveItem, newField, publishBlocker, FIELD_ORDER, TYPE_HINT } from './logic';
import './formulare.css';

const csvToNumbers = (s: string): number[] =>
  s
    .split(/[,;\s]+/)
    .map((x) => Number.parseInt(x, 10))
    .filter((n) => Number.isFinite(n));

export function FieldEditor({ f, index, count, meta, onChange, onMove, onRemove }: {
  f: FormField;
  index: number;
  count: number;
  meta: { field_types: Partial<Record<FormField['type'], string>> };
  onChange: (next: FormField) => void;
  onMove: (dir: -1 | 1) => void;
  onRemove: () => void;
}) {
  const set = (patch: Partial<FormField>) => onChange({ ...f, ...patch });
  return (
    <li className="fm-field-card">
      <div className="fm-field-head">
        <span className="badge badge-info" title={TYPE_HINT[f.type]}>
          {meta.field_types[f.type]}
        </span>
        <span className="fm-field-tools">
          <button type="button" className="btn btn-sm btn-ghost" aria-label="Nach oben" disabled={index === 0} onClick={() => onMove(-1)}>
            ↑
          </button>
          <button type="button" className="btn btn-sm btn-ghost" aria-label="Nach unten" disabled={index === count - 1} onClick={() => onMove(1)}>
            ↓
          </button>
          <button type="button" className="btn btn-sm btn-ghost" aria-label={`Feld „${f.label || f.id}“ entfernen`} onClick={onRemove}>
            <Icon name="trash" />
          </button>
        </span>
      </div>
      <Field label="Beschriftung" htmlFor={`fe-l-${f.id}`}>
        <input id={`fe-l-${f.id}`} type="text" value={f.label} maxLength={200} onChange={(e) => set({ label: e.target.value })} />
      </Field>
      <Field label="Hilfetext (optional)" htmlFor={`fe-h-${f.id}`} help="Erscheint als kleines Hilfe-Symbol neben der Beschriftung.">
        <input id={`fe-h-${f.id}`} type="text" value={f.help ?? ''} maxLength={500} onChange={(e) => set({ help: e.target.value })} />
      </Field>
      {hasOptions(f.type) && (
        <Field label="Auswahlmöglichkeiten (eine pro Zeile)" htmlFor={`fe-o-${f.id}`}>
          <textarea id={`fe-o-${f.id}`} rows={4} value={(f.options ?? []).join('\n')} onChange={(e) => set({ options: e.target.value.split('\n') })} />
        </Field>
      )}
      {f.type === 'scale' && (
        <div className="fm-two">
          <Field label="Beschriftung bei 1" htmlFor={`fe-lo-${f.id}`}>
            <input id={`fe-lo-${f.id}`} type="text" value={f.low ?? ''} maxLength={40} placeholder="z. B. trifft nicht zu" onChange={(e) => set({ low: e.target.value })} />
          </Field>
          <Field label="Beschriftung bei 5" htmlFor={`fe-hi-${f.id}`}>
            <input id={`fe-hi-${f.id}`} type="text" value={f.high ?? ''} maxLength={40} placeholder="z. B. trifft voll zu" onChange={(e) => set({ high: e.target.value })} />
          </Field>
        </div>
      )}
      {f.type === 'number' && (
        <div className="fm-two">
          <Field label="Kleinster Wert" htmlFor={`fe-min-${f.id}`}>
            <input id={`fe-min-${f.id}`} type="number" value={f.min ?? ''} onChange={(e) => set({ min: e.target.value === '' ? undefined : Number(e.target.value) })} />
          </Field>
          <Field label="Größter Wert" htmlFor={`fe-max-${f.id}`}>
            <input id={`fe-max-${f.id}`} type="number" value={f.max ?? ''} onChange={(e) => set({ max: e.target.value === '' ? undefined : Number(e.target.value) })} />
          </Field>
        </div>
      )}
      {f.type === 'confirm' && (
        <Field label="Text neben dem Häkchen" htmlFor={`fe-t-${f.id}`}>
          <textarea id={`fe-t-${f.id}`} rows={2} value={f.text ?? ''} maxLength={500} onChange={(e) => set({ text: e.target.value })} />
        </Field>
      )}
      {f.type !== 'student' && (
        <label className="fm-choice">
          <input type="checkbox" checked={!!f.required} onChange={(e) => set({ required: e.target.checked })} />
          <span>Pflichtfeld</span>
        </label>
      )}
    </li>
  );
}

function ActionEditor({ a, fields, onChange, onRemove }: { a: FormAction; fields: FormField[]; onChange: (a: FormAction) => void; onRemove: () => void }) {
  const set = (patch: Partial<FormAction>) => onChange({ ...a, ...patch });
  const pick = (value: string | null | undefined, types: FormField['type'][], label: string, key: keyof FormAction, optional = false) => (
    <Field label={label} htmlFor={`ac-${key}`}>
      <select id={`ac-${key}`} value={value ?? ''} onChange={(e) => set({ [key]: e.target.value || null } as Partial<FormAction>)}>
        <option value="">{optional ? '– nicht verwenden –' : 'Bitte wählen …'}</option>
        {fieldsOfType(fields, ...types).map((f) => (
          <option key={f.id} value={f.id}>
            {f.label || f.id}
          </option>
        ))}
      </select>
    </Field>
  );
  return (
    <li className="fm-field-card">
      <div className="fm-field-head">
        <strong>{a.type === 'create_absence' ? 'Beurlaubung / Krankmeldung anlegen' : a.type === 'inform_teachers' ? 'Lehrkräfte informieren' : 'Termin eintragen'}</strong>
        <button type="button" className="btn btn-sm btn-ghost" aria-label="Aktion entfernen" onClick={onRemove}>
          <Icon name="trash" />
        </button>
      </div>
      {a.type === 'create_absence' && (
        <>
          <div className="fm-two">
            <Field label="Art" htmlFor="ac-kind">
              <select id="ac-kind" value={a.kind ?? 'beurlaubung'} onChange={(e) => set({ kind: e.target.value as AbsenceKind })}>
                <option value="beurlaubung">Beurlaubung</option>
                <option value="krank">Krankmeldung</option>
                <option value="fehlt">Gefehlt</option>
              </select>
            </Field>
            <Field label="Status" htmlFor="ac-status">
              <select id="ac-status" value={a.status ?? 'entschuldigt'} onChange={(e) => set({ status: e.target.value as 'gemeldet' | 'entschuldigt' })}>
                <option value="entschuldigt">genehmigt / entschuldigt</option>
                <option value="gemeldet">nur gemeldet</option>
              </select>
            </Field>
          </div>
          {pick(a.student, ['student'], 'Feld „Schüler/in“', 'student', true)}
          {pick(a.range, ['daterange', 'date'], 'Feld „Zeitraum“', 'range')}
          {pick(a.periods, ['periods'], 'Feld „Stunden“', 'periods', true)}
          {pick(a.reason, ['text', 'textarea', 'select'], 'Feld „Anlass / Grund“', 'reason', true)}
          <p className="small muted" style={{ margin: 0 }}>
            Nutzt die Funktion „Krankmeldungen“.
            <HelpTip>Läuft bei der Genehmigung, mit allen Prüfungen (Schultage, Überschneidungen).</HelpTip>
          </p>
        </>
      )}
      {a.type === 'calendar_entry' && (
        <>
          <Field label="Titel des Termins" htmlFor="ac-title" help="Erscheint im Kalender der Klasse – bitte keine persönlichen Angaben.">
            <input id="ac-title" type="text" value={a.title ?? ''} maxLength={120} onChange={(e) => set({ title: e.target.value })} />
          </Field>
          {pick(a.date, ['date', 'daterange'], 'Feld „Datum“', 'date')}
        </>
      )}
      {a.type === 'inform_teachers' && (
        <p className="small muted" style={{ margin: 0 }}>
          Lehrkräfte der Klasse werden informiert.
          <HelpTip>Sie sehen sofort, dass sich etwas geändert hat, ohne Inhalt.</HelpTip>
        </p>
      )}
    </li>
  );
}

function Editor({ id, meta }: { id: number | null; meta: FormsMeta }) {
  const nav = useNavigate();
  const toast = useToast();
  const q = useApi((signal) => (id ? formsApi.template(id, signal) : Promise.resolve(null)), [id]);
  const approvers = useApi((signal) => formsApi.approvers(signal), []);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('sonstiges');
  const [sensitive, setSensitive] = useState(false);
  const [defn, setDefn] = useState<FormDefinition>(emptyDefinition());
  const [loaded, setLoaded] = useState(!id);
  const [error, setError] = useState<unknown>(null);
  const [preview, setPreview] = useState(false);
  const [previewAnswers, setPreviewAnswers] = useState<Answers>({});
  const [addType, setAddType] = useState<string>('text');
  const [status, setStatus] = useState<TemplateStatus>('entwurf');
  const tmpl = q.data;

  useEffect(() => {
    if (tmpl) {
      setTitle(tmpl.title);
      setDescription(tmpl.description);
      setCategory(tmpl.category);
      setSensitive(tmpl.sensitive);
      setDefn(tmpl.definition);
      setStatus(tmpl.status);
      setLoaded(true);
    }
  }, [tmpl]);
  useTitle(id ? 'Formular bearbeiten' : 'Neues Formular');
  const blocker = useMemo(() => publishBlocker(defn, title), [defn, title]);
  const update = (patch: Partial<FormDefinition>) => setDefn((d) => ({ ...d, ...patch }));

  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!loaded) return <Loading />;

  const body = (st?: TemplateStatus) => ({ title, description, category, sensitive, definition: defn, status: st ?? status });
  const save = async (st?: TemplateStatus) => {
    setError(null);
    try {
      const saved = id ? await formsApi.update(id, body(st)) : await formsApi.create(body(st));
      setStatus(saved.status);
      toast.success(st === 'aktiv' ? 'Veröffentlicht' : saved.version > (tmpl?.version ?? 1) ? `Gespeichert – neue Version ${saved.version}` : 'Gespeichert');
      if (!id) nav(`/formulare/vorlage/${saved.id}`, { replace: true });
      else q.reload();
    } catch (e) {
      setError(e);
    }
  };
  const showPdf = async () => {
    try {
      const blob = await formsApi.previewPdf(title || 'Formular', description, defn);
      window.open(URL.createObjectURL(blob), '_blank', 'noopener');
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  const setField = (i: number, next: FormField) => update({ fields: defn.fields.map((f, j) => (j === i ? next : f)) });
  const removeField = (i: number) => {
    const gone = defn.fields[i];
    update({ fields: defn.fields.filter((_, j) => j !== i), actions: gone ? dropFieldRefs(defn.actions, gone.id) : defn.actions });
  };
  const setStep = (i: number, next: FormStep) => update({ workflow: { ...defn.workflow, steps: defn.workflow.steps.map((s, j) => (j === i ? next : s)) } });
  const setAction = (i: number, next: FormAction) => update({ actions: defn.actions.map((a, j) => (j === i ? next : a)) });
  const toggleRole = (r: AudienceRole) => update({ audience: { ...defn.audience, roles: defn.audience.roles.includes(r) ? defn.audience.roles.filter((x) => x !== r) : [...defn.audience.roles, r] } });
  const hasAction = (t: ActionType) => defn.actions.some((a) => a.type === t);
  const hasStudent = defn.fields.some((f) => f.type === 'student');

  return (
    <FormErrors error={error}>
      <div className="stack fm-editor">
        <div className="row row-between" style={{ flexWrap: 'wrap', gap: 8 }}>
          <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
            <Link to="/formulare?tab=vorlagen" className="btn btn-sm btn-ghost">
              ← Alle Formulare
            </Link>
            {id && <span className={`badge badge-${TEMPLATE_TONE[status]}`}>{TEMPLATE_LABEL[status]}</span>}
            {tmpl && <span className="small muted">Version {tmpl.version}</span>}
          </div>
          <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
            <button type="button" className="btn btn-sm" onClick={() => setPreview((p) => !p)} aria-pressed={preview}>
              <Icon name="eye" /> Vorschau
            </button>
            <button type="button" className="btn btn-sm" onClick={showPdf}>
              <Icon name="print" /> PDF
            </button>
            <AsyncButton className="btn btn-sm" onClick={() => save()}>
              <Icon name="check" /> Speichern
            </AsyncButton>
            {status !== 'aktiv' && (
              <AsyncButton className="btn btn-sm btn-primary" disabled={!!blocker} title={blocker ?? undefined} onClick={() => save('aktiv')}>
                Veröffentlichen
              </AsyncButton>
            )}
            {status === 'aktiv' && (
              <AsyncButton className="btn btn-sm" onClick={() => save('archiviert')} confirm="Das Formular wird archiviert und kann nicht mehr ausgefüllt werden. Bestehende Einreichungen bleiben erhalten.">
                Archivieren
              </AsyncButton>
            )}
          </div>
        </div>
        {tmpl && (tmpl.counts?.total ?? 0) > 0 && (
          <div className="alert alert-info">
            Es gibt {tmpl.counts?.total} Einreichung(en).
            <HelpTip>Änderungen an Feldern, Zielgruppe oder Ablauf gelten für neue Einreichungen als neue Version, bisherige bleiben unverändert.</HelpTip>
          </div>
        )}
        {blocker && status !== 'aktiv' && <p className="small muted" style={{ margin: 0 }}>Zum Veröffentlichen fehlt noch: {blocker}</p>}

        {preview && (
          <section className="card" aria-label="Vorschau">
            <div className="card-head">
              <h2>Vorschau: {title || 'Formular'}</h2>
            </div>
            <FormFields definition={defn} answers={{ ...initialAnswers(defn), ...previewAnswers }} onChange={(k, v) => setPreviewAnswers((a) => ({ ...a, [k]: v }))} students={[{ id: 's', name: 'Beispiel Kind', class_id: '5a', submission_id: null }]} studentId="s" periods={meta.periods} preview />
          </section>
        )}

        <section className="card">
          <div className="card-head">
            <h2>Grunddaten</h2>
          </div>
          <div className="stack">
            <Field label="Titel" htmlFor="fe-title" name="title">
              <input id="fe-title" type="text" value={title} maxLength={200} onChange={(e) => setTitle(e.target.value)} />
            </Field>
            <div className="fm-two">
              <Field label="Kategorie" htmlFor="fe-cat">
                <select id="fe-cat" value={category} onChange={(e) => setCategory(e.target.value)}>
                  {Object.entries(meta.categories).map(([k, v]) => (
                    <option key={k} value={k}>
                      {v}
                    </option>
                  ))}
                </select>
              </Field>
              <label className="fm-choice fm-align-end">
                <input type="checkbox" checked={sensitive} onChange={(e) => setSensitive(e.target.checked)} />
                <span>
                  Enthält besonders geschützte Angaben{' '}
                  <HelpTip>Gesundheits- oder Förderangaben: Ansehen und Export werden protokolliert; nur Schulleitung, Sekretariat und die Klassenleitung der Klasse sehen die Inhalte. Die technische Administration sieht Inhalte nie.</HelpTip>
                </span>
              </label>
            </div>
            <Field label="Beschreibung (für Familien sichtbar)" htmlFor="fe-desc">
              <textarea id="fe-desc" rows={2} value={description} maxLength={2000} onChange={(e) => setDescription(e.target.value)} />
            </Field>
            <Field label="Einleitung über dem Formular (optional)" htmlFor="fe-intro">
              <textarea id="fe-intro" rows={2} value={defn.intro ?? ''} maxLength={1500} onChange={(e) => update({ intro: e.target.value })} />
            </Field>
          </div>
        </section>

        <section className="card">
          <div className="card-head">
            <h2>
              Felder <HelpTip>Reihenfolge wie im Formular. Mit „Pflichtfeld“ muss das Feld ausgefüllt werden. Ein Feld „Schüler/in“ lässt Familien das Kind wählen.</HelpTip>
            </h2>
          </div>
          {defn.fields.length === 0 && <p className="muted small">Noch keine Felder – unten das erste hinzufügen.</p>}
          <ol className="fm-field-list">
            {defn.fields.map((f, i) => (
              <FieldEditor key={f.id} f={f} index={i} count={defn.fields.length} meta={meta} onChange={(n) => setField(i, n)} onMove={(d) => update({ fields: moveItem(defn.fields, i, d) })} onRemove={() => removeField(i)} />
            ))}
          </ol>
          <div className="row" style={{ gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
            <label className="sr-only" htmlFor="fe-add">
              Feldart
            </label>
            <select id="fe-add" value={addType} onChange={(e) => setAddType(e.target.value)}>
              {FIELD_ORDER.filter((t) => t !== 'student' || !hasStudent).map((t) => (
                <option key={t} value={t}>
                  {meta.field_types[t]}
                </option>
              ))}
            </select>
            <button type="button" className="btn" onClick={() => update({ fields: [...defn.fields, newField(addType as FormField['type'], defn.fields)] })}>
              <Icon name="plus" /> Feld hinzufügen
            </button>
          </div>
        </section>

        <section className="card">
          <div className="card-head">
            <h2>Wer füllt aus?</h2>
          </div>
          <div className="stack">
            <div className="fm-choices" role="group" aria-label="Rollen">
              {(Object.entries(meta.audience_roles) as [AudienceRole, string][]).map(([r, label]) => (
                <label key={r} className="fm-choice">
                  <input type="checkbox" checked={defn.audience.roles.includes(r)} onChange={() => toggleRole(r)} />
                  <span>{label}</span>
                </label>
              ))}
            </div>
            <Field label="Für welche Klassen?" htmlFor="fe-scope" help="Gilt für die Klasse des Kindes. Bei Lehrkräften ohne Kind-Bezug spielt es keine Rolle.">
              <select id="fe-scope" value={defn.audience.scope} onChange={(e) => update({ audience: { ...defn.audience, scope: e.target.value as 'all' | 'classes' | 'grades' } })}>
                <option value="all">Alle Klassen</option>
                <option value="classes">Bestimmte Klassen</option>
                <option value="grades">Bestimmte Jahrgänge</option>
              </select>
            </Field>
            {defn.audience.scope === 'classes' && (
              <div className="fm-choices" role="group" aria-label="Klassen">
                {meta.classes.map((c) => (
                  <label key={c.id} className="fm-choice">
                    <input
                      type="checkbox"
                      checked={defn.audience.classes.includes(c.id)}
                      onChange={(e) => update({ audience: { ...defn.audience, classes: e.target.checked ? [...defn.audience.classes, c.id] : defn.audience.classes.filter((x) => x !== c.id) } })}
                    />
                    <span>{c.name}</span>
                  </label>
                ))}
              </div>
            )}
            {defn.audience.scope === 'grades' && (
              <Field label="Jahrgänge (Zahlen, durch Komma getrennt)" htmlFor="fe-grades">
                <input id="fe-grades" type="text" inputMode="numeric" value={defn.audience.grades.join(', ')} onChange={(e) => update({ audience: { ...defn.audience, grades: csvToNumbers(e.target.value) } })} />
              </Field>
            )}
            <label className="fm-choice">
              <input type="checkbox" checked={!!defn.once} onChange={(e) => update({ once: e.target.checked })} />
              <span>
                Nur einmal je Kind <HelpTip>Sinnvoll für Einwilligungen und Rückmeldungen. Abgelehnte oder zurückgezogene zählen nicht.</HelpTip>
              </span>
            </label>
          </div>
        </section>

        <section className="card">
          <div className="card-head">
            <h2>
              Wer prüft? <HelpTip>Mehrere Schritte laufen nacheinander. Die Schulleitung kann jeden Schritt übernehmen. Ohne Schritt landet die Einreichung im Eingang und wird dort abgeschlossen.</HelpTip>
            </h2>
          </div>
          <ol className="fm-field-list">
            {defn.workflow.steps.map((s, i) => (
              <li key={i} className="fm-field-card">
                <div className="fm-field-head">
                  <strong>Schritt {i + 1}</strong>
                  <span className="fm-field-tools">
                    <button type="button" className="btn btn-sm btn-ghost" aria-label="Nach oben" disabled={i === 0} onClick={() => update({ workflow: { ...defn.workflow, steps: moveItem(defn.workflow.steps, i, -1) } })}>
                      ↑
                    </button>
                    <button type="button" className="btn btn-sm btn-ghost" aria-label="Nach unten" disabled={i === defn.workflow.steps.length - 1} onClick={() => update({ workflow: { ...defn.workflow, steps: moveItem(defn.workflow.steps, i, 1) } })}>
                      ↓
                    </button>
                    <button type="button" className="btn btn-sm btn-ghost" aria-label={`Schritt ${i + 1} entfernen`} onClick={() => update({ workflow: { ...defn.workflow, steps: defn.workflow.steps.filter((_, j) => j !== i) } })}>
                      <Icon name="trash" />
                    </button>
                  </span>
                </div>
                <div className="fm-two">
                  <Field label="Wer prüft?" htmlFor={`st-a-${i}`}>
                    <select id={`st-a-${i}`} value={s.approver} onChange={(e) => setStep(i, { approver: e.target.value as FormStep['approver'], label: undefined, user_id: e.target.value === 'user' ? s.user_id : undefined })}>
                      {Object.entries(meta.approvers).map(([k, v]) => (
                        <option key={k} value={k}>
                          {v}
                        </option>
                      ))}
                    </select>
                  </Field>
                  {s.approver === 'user' && (
                    <Field label="Person" htmlFor={`st-u-${i}`}>
                      <select id={`st-u-${i}`} value={s.user_id ?? ''} onChange={(e) => setStep(i, { ...s, user_id: Number(e.target.value) || null })}>
                        <option value="">Bitte wählen …</option>
                        {(approvers.data ?? []).map((u) => (
                          <option key={u.id} value={u.id}>
                            {u.name} ({u.role_label})
                          </option>
                        ))}
                      </select>
                    </Field>
                  )}
                </div>
              </li>
            ))}
          </ol>
          <div className="row" style={{ gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
            <button type="button" className="btn" disabled={defn.workflow.steps.length >= 4} onClick={() => update({ workflow: { steps: [...defn.workflow.steps, { approver: 'class_teacher' }], auto_complete: false } })}>
              <Icon name="plus" /> Prüfschritt hinzufügen
            </button>
            {defn.workflow.steps.length === 0 && (
              <label className="fm-choice">
                <input type="checkbox" checked={defn.workflow.auto_complete} onChange={(e) => update({ workflow: { ...defn.workflow, auto_complete: e.target.checked } })} />
                <span>
                  Sofort erledigt <HelpTip>Die Einreichung gilt direkt als erledigt (z. B. Rückmeldungen). Sie bleibt im Eingang einsehbar.</HelpTip>
                </span>
              </label>
            )}
          </div>
        </section>

        <section className="card">
          <div className="card-head">
            <h2>Fristen & Erinnerung</h2>
          </div>
          <div className="fm-two">
            <Field label="Ausfüllbar ab" htmlFor="dl-from">
              <input id="dl-from" type="date" value={defn.deadline.open_from ?? ''} onChange={(e) => update({ deadline: { ...defn.deadline, open_from: e.target.value || null } })} />
            </Field>
            <Field label="Ausfüllbar bis" htmlFor="dl-until">
              <input id="dl-until" type="date" value={defn.deadline.open_until ?? ''} onChange={(e) => update({ deadline: { ...defn.deadline, open_until: e.target.value || null } })} />
            </Field>
            <Field label="Bearbeitung innerhalb (Tage)" htmlFor="dl-dec" help="Danach gilt die Einreichung als überfällig.">
              <input id="dl-dec" type="number" min={1} max={90} value={defn.deadline.decide_days ?? ''} onChange={(e) => update({ deadline: { ...defn.deadline, decide_days: e.target.value ? Number(e.target.value) : null } })} />
            </Field>
            <Field label="Erinnerung nach (Tagen)" htmlFor="dl-rem" help="Die Prüfenden erhalten einen Hinweis, wenn eine Einreichung so lange offen ist.">
              <input id="dl-rem" type="number" min={1} max={60} value={defn.deadline.remind_days ?? ''} onChange={(e) => update({ deadline: { ...defn.deadline, remind_days: e.target.value ? Number(e.target.value) : null } })} />
            </Field>
          </div>
        </section>

        <section className="card">
          <div className="card-head">
            <h2>
              Bei Genehmigung <HelpTip>Aktionen laufen automatisch, sobald der letzte Schritt genehmigt (oder bei „Sofort erledigt“ eingereicht) wird. Schlägt eine Aktion fehl, bleibt die Genehmigung bestehen und der Eingang kann sie erneut ausführen.</HelpTip>
            </h2>
          </div>
          <ol className="fm-field-list">
            {defn.actions.map((a, i) => (
              <ActionEditor key={i} a={a} fields={defn.fields} onChange={(n) => setAction(i, n)} onRemove={() => update({ actions: defn.actions.filter((_, j) => j !== i) })} />
            ))}
          </ol>
          <div className="row" style={{ gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
            <button type="button" className="btn" disabled={!hasStudent} title={hasStudent ? undefined : 'Dafür braucht das Formular ein Feld „Schüler/in“'} onClick={() => update({ actions: [...defn.actions, { type: 'create_absence', kind: 'beurlaubung', status: 'entschuldigt', student: defn.fields.find((f) => f.type === 'student')?.id ?? null, range: defn.fields.find((f) => f.type === 'daterange')?.id ?? null, periods: defn.fields.find((f) => f.type === 'periods')?.id ?? null, reason: null }] })}>
              <Icon name="plus" /> Beurlaubung/Krankmeldung anlegen
            </button>
            <button type="button" className="btn" disabled={hasAction('inform_teachers') || !hasStudent} onClick={() => update({ actions: [...defn.actions, { type: 'inform_teachers' }] })}>
              <Icon name="plus" /> Lehrkräfte informieren
            </button>
            <button type="button" className="btn" onClick={() => update({ actions: [...defn.actions, { type: 'calendar_entry', title: '', date: defn.fields.find((f) => f.type === 'date')?.id ?? null }] })}>
              <Icon name="plus" /> Termin eintragen
            </button>
          </div>
        </section>
      </div>
    </FormErrors>
  );
}

/** `/formulare/vorlage/:id` – `id` = Zahl oder `neu`. */
export default function TemplateEditor() {
  const { id } = useParams();
  const meta = useApi((signal) => formsApi.meta(signal), []);
  if (meta.error) return <ErrorBox error={meta.error} onRetry={meta.reload} />;
  if (!meta.data) return <Loading />;
  const num = id && id !== 'neu' ? Number(id) : null;
  return (
    <div className="page">
      <div className="page-head">
        <h1>{num ? 'Formular bearbeiten' : 'Neues Formular'}</h1>
      </div>
      <Editor key={num ?? 'neu'} id={num} meta={meta.data} />
    </div>
  );
}

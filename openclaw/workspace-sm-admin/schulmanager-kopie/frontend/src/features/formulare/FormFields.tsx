/**
 * Eingabefelder eines Formulars (Ausfüllen und Vorschau im Baukasten) – eine Spalte, große Berührflächen, Handy-tauglich.
 */
import type { ReactNode } from 'react';
import { FileUpload } from '../../components/FileUpload';
import { Field } from '../../components/ui';
import type { Answers, AvailableStudent, FormDefinition, FormField } from './api';
import './formulare.css';
import { APP_NAME } from '../../brand';

export interface FormFieldsProps {
  definition: FormDefinition;
  answers: Answers;
  onChange: (id: string, value: unknown) => void;
  errors?: Record<string, string>;
  /** Kinder zur Auswahl (Feld „Schüler/in“ bzw. Kind-Auswahl) */
  students?: AvailableStudent[];
  studentId?: string | null;
  onStudent?: (id: string) => void;
  periods?: number;
  signer?: string;
  disabled?: boolean;
  /** Vorschau: Dateiupload zeigt nur die Beschriftung */
  preview?: boolean;
}

function Control({ f, id, value, onChange, disabled, periods, students, studentId, onStudent, signer, preview }: {
  f: FormField;
  id: string;
  value: unknown;
  onChange: (v: unknown) => void;
  disabled?: boolean;
  periods: number;
  students: AvailableStudent[];
  studentId?: string | null;
  onStudent?: (id: string) => void;
  signer?: string;
  preview?: boolean;
}): ReactNode {
  switch (f.type) {
    case 'text':
      return <input id={id} type="text" value={String(value ?? '')} maxLength={f.max ?? 200} disabled={disabled} onChange={(e) => onChange(e.target.value)} />;
    case 'textarea':
      return <textarea id={id} rows={4} value={String(value ?? '')} maxLength={f.max ?? 4000} disabled={disabled} onChange={(e) => onChange(e.target.value)} />;
    case 'number':
      return <input id={id} type="text" inputMode="decimal" value={String(value ?? '')} disabled={disabled} onChange={(e) => onChange(e.target.value)} />;
    case 'date':
      return <input id={id} type="date" value={String(value ?? '')} disabled={disabled} onChange={(e) => onChange(e.target.value)} />;
    case 'daterange': {
      const r = (value as { from?: string; to?: string } | null) ?? {};
      return (
        <div className="fm-range">
          <label className="fm-sub">
            <span className="small muted">von</span>
            <input id={id} type="date" value={r.from ?? ''} disabled={disabled} onChange={(e) => onChange({ from: e.target.value, to: r.to && r.to >= e.target.value ? r.to : e.target.value })} />
          </label>
          <label className="fm-sub">
            <span className="small muted">bis einschließlich</span>
            <input type="date" value={r.to ?? ''} min={r.from || undefined} disabled={disabled} onChange={(e) => onChange({ from: r.from || e.target.value, to: e.target.value })} />
          </label>
        </div>
      );
    }
    case 'select':
      return (
        <select id={id} value={String(value ?? '')} disabled={disabled} onChange={(e) => onChange(e.target.value)}>
          <option value="">Bitte wählen …</option>
          {(f.options ?? []).map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
      );
    case 'multiselect': {
      const chosen = new Set((value as string[] | null) ?? []);
      return (
        <div className="fm-choices" role="group" aria-labelledby={`${id}-l`}>
          {(f.options ?? []).map((o) => (
            <label key={o} className="fm-choice">
              <input
                type="checkbox"
                checked={chosen.has(o)}
                disabled={disabled}
                onChange={(e) => {
                  const next = new Set(chosen);
                  if (e.target.checked) next.add(o);
                  else next.delete(o);
                  onChange((f.options ?? []).filter((x) => next.has(x)));
                }}
              />
              <span>{o}</span>
            </label>
          ))}
        </div>
      );
    }
    case 'yesno':
      return (
        <div className="fm-choices fm-yesno" role="radiogroup" aria-labelledby={`${id}-l`}>
          {[
            ['Ja', true],
            ['Nein', false],
          ].map(([label, v]) => (
            <label key={String(label)} className="fm-choice">
              <input type="radio" name={id} checked={value === v} disabled={disabled} onChange={() => onChange(v)} />
              <span>{label as string}</span>
            </label>
          ))}
        </div>
      );
    case 'confirm':
      return (
        <label className="fm-choice fm-confirm">
          <input id={id} type="checkbox" checked={value === true} disabled={disabled} onChange={(e) => onChange(e.target.checked)} />
          <span>{f.text || 'Ich bestätige.'}</span>
        </label>
      );
    case 'signature': {
      const sig = (value as { name?: string } | null) ?? {};
      return (
        <div className="fm-sig">
          <input id={id} type="text" autoComplete="name" placeholder={signer ? `Vollständiger Name, z. B. ${signer}` : 'Vollständiger Name'} value={sig.name ?? ''} maxLength={120} disabled={disabled} onChange={(e) => onChange({ name: e.target.value })} />
          <span className="small muted">Das Datum setzt {APP_NAME} automatisch.</span>
        </div>
      );
    }
    case 'file':
      return preview ? (
        <p className="small muted">Hier können Foto oder PDF angehängt werden.</p>
      ) : (
        <FileUpload purpose="form_file" maxFiles={5} accept=".pdf,.jpg,.jpeg,.png,.heic" label="Foto oder PDF anhängen" disabled={disabled} onChange={(files) => onChange(files.map((x) => x.id))} />
      );
    case 'scale': {
      const current = value === '' || value === null || value === undefined ? null : Number(value);
      return (
        <div className="fm-scale" role="radiogroup" aria-labelledby={`${id}-l`}>
          {f.low ? <span className="fm-scale-end small muted">{f.low}</span> : null}
          <div className="fm-scale-steps">
            {[1, 2, 3, 4, 5].map((n) => (
              <label key={n} className={`fm-scale-step${current === n ? ' is-on' : ''}`}>
                <input type="radio" name={id} checked={current === n} disabled={disabled} onChange={() => onChange(n)} />
                <span>{n}</span>
              </label>
            ))}
          </div>
          {f.high ? <span className="fm-scale-end small muted">{f.high}</span> : null}
        </div>
      );
    }
    case 'student':
      return (
        <select id={id} value={studentId ?? ''} disabled={disabled || students.length === 1} onChange={(e) => onStudent?.(e.target.value)}>
          {students.length !== 1 && <option value="">Bitte wählen …</option>}
          {students.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
              {s.class_id ? ` (${s.class_id})` : ''}
            </option>
          ))}
        </select>
      );
    case 'periods': {
      const chosen = new Set((value as number[] | null) ?? []);
      return (
        <div className="fm-periods" role="group" aria-labelledby={`${id}-l`}>
          {Array.from({ length: periods }, (_, i) => (
            <label key={i} className={`fm-period${chosen.has(i) ? ' is-on' : ''}`}>
              <input
                type="checkbox"
                checked={chosen.has(i)}
                disabled={disabled}
                onChange={(e) => {
                  const next = new Set(chosen);
                  if (e.target.checked) next.add(i);
                  else next.delete(i);
                  onChange([...next].sort((a, b) => a - b));
                }}
              />
              <span>{i + 1}.</span>
            </label>
          ))}
        </div>
      );
    }
    default:
      return null;
  }
}

export function FormFields({ definition, answers, onChange, errors = {}, students = [], studentId, onStudent, periods = 8, signer, disabled, preview }: FormFieldsProps) {
  return (
    <div className="fm-fields">
      {definition.intro ? <p className="fm-intro">{definition.intro}</p> : null}
      {definition.fields.map((f) => {
        const id = `fm-${f.id}`;
        const group = f.type === 'multiselect' || f.type === 'yesno' || f.type === 'periods' || f.type === 'scale';
        return (
          <Field key={f.id} label={<span id={`${id}-l`}>{f.label}{f.required ? ' *' : ''}</span>} htmlFor={group ? undefined : id} help={f.help || undefined} error={errors[f.id]}>
            <Control
              f={f}
              id={id}
              value={answers[f.id]}
              onChange={(v) => onChange(f.id, v)}
              disabled={disabled}
              periods={periods}
              students={students}
              studentId={studentId}
              onStudent={onStudent}
              signer={signer}
              preview={preview}
            />
          </Field>
        );
      })}
    </div>
  );
}

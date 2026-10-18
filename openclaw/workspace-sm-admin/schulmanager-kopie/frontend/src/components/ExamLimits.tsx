/**
 * Höchstzahlen für Klassenarbeiten/Klausuren je Woche und Tag mit Vererbung Schule → Jahrgang → Klasse.
 *
 * - `ClassExamLimitsFields`: Felder im Klassen-Editor („Wie Vorgabe (Jahrgang 7: 2/Woche, 1/Tag)“ oder eigene Werte).
 * - `ExamLimitsDefaultsCard`: Vorgabe der Schule und je Jahrgang (Seite „Klausuren“, Recht `settings.edit`).
 * - `examLimitsFor`/`examLimitsText`: wirksame Werte und Text (Spiegel von `rules.exam_limits_for_class`).
 */
import { useEffect, useId, useState } from 'react';
import { settings as settingsApi } from '../api/endpoints';
import type { Settings } from '../api/types';
import { useToast } from '../context/ToastContext';
import { invalidate, useCollection, useSettings } from '../hooks/useCollection';
import { HelpTip } from './HelpTip';
import { AsyncButton, Field } from './ui';

export interface ExamLimitValues {
  max_exams_per_week?: number | null;
  max_exams_per_day?: number | null;
}

type Source = 'school' | 'grade' | 'class';
const SOURCE: Record<Source, string> = { school: 'Schule', grade: 'Jahrgang', class: 'Klasse' };

/** Wirksame Werte einer Klasse (eigene → Jahrgang → Schule). */
export function examLimitsFor(
  cls: (ExamLimitValues & { grade?: number }) | null | undefined,
  st: Pick<Settings, 'max_exams_per_week' | 'max_exams_per_day' | 'exam_limits_by_grade'> | null | undefined,
): { per_week: number; per_day: number; source_week: Source; source_day: Source } {
  const out = { per_week: st?.max_exams_per_week ?? 3, per_day: st?.max_exams_per_day ?? 1, source_week: 'school' as Source, source_day: 'school' as Source };
  const g = cls?.grade !== undefined ? st?.exam_limits_by_grade?.[String(cls.grade)] : undefined;
  if (g?.per_week !== undefined && g.per_week !== null) Object.assign(out, { per_week: g.per_week, source_week: 'grade' });
  if (g?.per_day !== undefined && g.per_day !== null) Object.assign(out, { per_day: g.per_day, source_day: 'grade' });
  if (cls?.max_exams_per_week !== undefined && cls.max_exams_per_week !== null) Object.assign(out, { per_week: cls.max_exams_per_week, source_week: 'class' });
  if (cls?.max_exams_per_day !== undefined && cls.max_exams_per_day !== null) Object.assign(out, { per_day: cls.max_exams_per_day, source_day: 'class' });
  return out;
}

export function examLimitsText(l: { per_week: number; per_day: number; source_week: Source; source_day: Source }): string {
  const src = l.source_week === l.source_day ? SOURCE[l.source_week] : `Woche: ${SOURCE[l.source_week]}, Tag: ${SOURCE[l.source_day]}`;
  return `max. ${l.per_week} je Woche, ${l.per_day} je Tag (${src})`;
}

export function sameExamLimits(a: ExamLimitValues, b: ExamLimitValues): boolean {
  return (a.max_exams_per_week ?? null) === (b.max_exams_per_week ?? null) && (a.max_exams_per_day ?? null) === (b.max_exams_per_day ?? null);
}

/** Felder einer Klasse: „Wie Vorgabe“ oder eigene Höchstzahlen. */
export function ClassExamLimitsFields({ value, grade, onChange, disabled }: { value: ExamLimitValues; grade: number | undefined; onChange: (v: ExamLimitValues) => void; disabled?: boolean }) {
  const id = useId();
  const { data: st } = useSettings();
  const own = value.max_exams_per_week !== null && value.max_exams_per_week !== undefined || value.max_exams_per_day !== null && value.max_exams_per_day !== undefined;
  const inherited = examLimitsFor({ grade }, st);
  return (
    <div className="stack-sm">
      <span className="field-label">
        Klassenarbeiten / Klausuren{' '}
        <HelpTip>
          Höchstzahl angesetzter Klassenarbeiten und Klausuren je Woche und je Tag für diese Klasse. Angekündigte Tests zählen nicht mit. Ohne eigene Werte gilt
          die Vorgabe des Jahrgangs, sonst die der Schule (Seite „Klausuren“). Die Klausurplanung warnt beim Eintragen, wenn eine Grenze erreicht ist.
        </HelpTip>
      </span>
      <label className="check">
        <input type="checkbox" checked={!own} disabled={disabled} onChange={(e) => onChange(e.target.checked ? { max_exams_per_week: null, max_exams_per_day: null } : { max_exams_per_week: inherited.per_week, max_exams_per_day: inherited.per_day })} />{' '}
        Wie Vorgabe ({examLimitsText(inherited)})
      </label>
      {own && (
        <div className="form-grid">
          <Field label="Höchstens je Woche" htmlFor={`${id}-w`}>
            <input id={`${id}-w`} type="number" min={0} max={20} value={value.max_exams_per_week ?? inherited.per_week} disabled={disabled} onChange={(e) => onChange({ ...value, max_exams_per_week: Math.min(20, Math.max(0, parseInt(e.target.value || '0', 10))) })} />
          </Field>
          <Field label="Höchstens je Tag" htmlFor={`${id}-d`}>
            <input id={`${id}-d`} type="number" min={0} max={5} value={value.max_exams_per_day ?? inherited.per_day} disabled={disabled} onChange={(e) => onChange({ ...value, max_exams_per_day: Math.min(5, Math.max(0, parseInt(e.target.value || '0', 10))) })} />
          </Field>
        </div>
      )}
    </div>
  );
}

type GradeRow = { per_week?: number | null; per_day?: number | null };

/** Vorgaben der Schule und je Jahrgang (Seite „Klausuren“). */
export function ExamLimitsDefaultsCard({ canEdit }: { canEdit: boolean }) {
  const toast = useToast();
  const { data: st } = useSettings();
  const classes = useCollection('classes').data ?? [];
  const [week, setWeek] = useState(3);
  const [day, setDay] = useState(1);
  const [byGrade, setByGrade] = useState<Record<string, GradeRow>>({});
  const [dirty, setDirty] = useState(false);
  const id = useId();
  useEffect(() => {
    if (!st || dirty) return;
    setWeek(st.max_exams_per_week);
    setDay(st.max_exams_per_day);
    setByGrade(structuredClone(st.exam_limits_by_grade ?? {}));
  }, [st, dirty]);
  const grades = [...new Set(classes.map((c) => c.grade))].sort((a, b) => a - b);
  const setGrade = (g: number, patch: GradeRow) => {
    setByGrade((cur) => ({ ...cur, [String(g)]: { ...cur[String(g)], ...patch } }));
    setDirty(true);
  };
  const gradeCount = Object.keys(st?.exam_limits_by_grade ?? {}).length;
  const ownClasses = classes.filter((c) => (c.max_exams_per_week ?? null) !== null || (c.max_exams_per_day ?? null) !== null);
  return (
    <details className="disclosure card" style={{ padding: 12 }}>
      <summary>
        Höchstzahlen je Woche und Tag{' '}
        <span className="small muted">
          – Schule: {st?.max_exams_per_week ?? '–'} / {st?.max_exams_per_day ?? '–'}
          {gradeCount ? ` · ${gradeCount} Jahr${gradeCount === 1 ? 'gang' : 'gänge'} mit eigenen Werten` : ''}
          {ownClasses.length ? ` · ${ownClasses.length} Klasse${ownClasses.length !== 1 ? 'n' : ''} mit eigenen Werten` : ''}
        </span>
      </summary>
      <div className="stack-sm" style={{ marginTop: 8 }}>
        <p className="small muted" style={{ margin: 0 }}>
          Vorgabe der Schule
          <HelpTip>
            Wie viele Klassenarbeiten und Klausuren darf eine Klasse höchstens je Woche und je Tag schreiben? Je Jahrgang kann die Vorgabe anders sein; einzelne Klassen können im Klassen-Editor eigene Werte setzen. Angekündigte Tests zählen nicht.
          </HelpTip>
        </p>
        <div className="form-grid">
          <Field label="Schule: höchstens je Woche" htmlFor={`${id}-w`}>
            <input id={`${id}-w`} type="number" min={0} max={20} value={week} disabled={!canEdit} onChange={(e) => { setWeek(Math.min(20, Math.max(0, parseInt(e.target.value || '0', 10)))); setDirty(true); }} />
          </Field>
          <Field label="Schule: höchstens je Tag" htmlFor={`${id}-d`}>
            <input id={`${id}-d`} type="number" min={0} max={5} value={day} disabled={!canEdit} onChange={(e) => { setDay(Math.min(5, Math.max(0, parseInt(e.target.value || '0', 10)))); setDirty(true); }} />
          </Field>
        </div>
        {grades.length > 0 && (
          <div className="table-wrap">
            <table className="table table-compact">
              <caption className="sr-only">Vorgaben je Jahrgang</caption>
              <thead>
                <tr>
                  <th scope="col">Jahrgang</th>
                  <th scope="col">je Woche</th>
                  <th scope="col">je Tag</th>
                  <th scope="col">Klassen mit eigenen Werten</th>
                </tr>
              </thead>
              <tbody>
                {grades.map((g) => {
                  const row = byGrade[String(g)] ?? {};
                  const own = ownClasses.filter((c) => c.grade === g);
                  return (
                    <tr key={g}>
                      <th scope="row">{g}</th>
                      <td>
                        <input type="number" min={0} max={20} aria-label={`Jahrgang ${g}: je Woche`} placeholder={`wie Schule (${week})`} value={row.per_week ?? ''} disabled={!canEdit} style={{ width: '8rem' }} onChange={(e) => setGrade(g, { per_week: e.target.value === '' ? null : Math.min(20, Math.max(0, parseInt(e.target.value, 10) || 0)) })} />
                      </td>
                      <td>
                        <input type="number" min={0} max={5} aria-label={`Jahrgang ${g}: je Tag`} placeholder={`wie Schule (${day})`} value={row.per_day ?? ''} disabled={!canEdit} style={{ width: '8rem' }} onChange={(e) => setGrade(g, { per_day: e.target.value === '' ? null : Math.min(5, Math.max(0, parseInt(e.target.value, 10) || 0)) })} />
                      </td>
                      <td className="small muted">{own.length ? own.map((c) => `${c.name} (${c.max_exams_per_week ?? '–'}/${c.max_exams_per_day ?? '–'})`).join(', ') : '–'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {canEdit && (
          <div className="row-end">
            {dirty && <span className="small muted">Ungespeicherte Änderungen</span>}
            <button type="button" className="btn btn-sm" disabled={!dirty} onClick={() => setDirty(false)}>
              Verwerfen
            </button>
            <AsyncButton
              className="btn btn-primary btn-sm"
              disabled={!dirty}
              onClick={async () => {
                try {
                  const clean: Record<string, GradeRow> = {};
                  for (const [g, r] of Object.entries(byGrade)) {
                    const row: GradeRow = {};
                    if (r.per_week !== null && r.per_week !== undefined) row.per_week = r.per_week;
                    if (r.per_day !== null && r.per_day !== undefined) row.per_day = r.per_day;
                    if (Object.keys(row).length) clean[g] = row;
                  }
                  await settingsApi.put({ max_exams_per_week: week, max_exams_per_day: day, exam_limits_by_grade: clean } as Settings);
                  toast.success('Höchstzahlen gespeichert');
                  setDirty(false);
                  invalidate('settings');
                } catch (e) {
                  toast.error(e, 'Speichern');
                }
              }}
            >
              Speichern
            </AsyncButton>
          </div>
        )}
      </div>
    </details>
  );
}

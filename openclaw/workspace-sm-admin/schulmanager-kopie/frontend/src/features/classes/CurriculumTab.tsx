/**
 * Stundentafel einer Klasse: welches Fach wie viele Wochenstunden hat. Ändern dürfen Stammdaten/Planung und die
 * Klassenleitung. Beim Speichern entstehen die Kurse der Klasse sofort (Lehrkräfte werden zugewiesen); die
 * automatische Neuplanung legt neue oder fehlende Stunden in den Stundenplan.
 */
import { AbbrList, SubjectAbbr } from '../../components/Abbr';
import { HelpTip } from '../../components/HelpTip';
import { useEffect, useMemo, useState } from 'react';
import { Icon } from '../../components/Icon';
import { SubjectAdder } from '../../components/SubjectAdder';
import { useUser } from '../../context/AuthContext';
import { can } from '../../lib/permissions';
import { Alert, AsyncButton, ErrorBox, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { classesApi } from './api';
import type { ClassCurriculum, CurriculumRow, CurriculumSubject } from './types';

/** Bearbeitbare Tabelle Fach → Wochenstunden (+ Doppelstunde). Ohne eigenes Laden/Speichern. */
export function CurriculumEditor({
  rows,
  subjects,
  onChange,
  disabled,
}: {
  rows: CurriculumRow[];
  subjects: CurriculumSubject[];
  onChange: (rows: CurriculumRow[]) => void;
  disabled?: boolean;
}) {
  const used = new Set(rows.map((r) => r.subject));
  const free = subjects.filter((s) => !used.has(s.id));
  const user = useUser();
  const total = rows.reduce((n, r) => n + (Number(r.hours) || 0), 0);
  const name = (id: string) => subjects.find((s) => s.id === id)?.name ?? id;
  const update = (i: number, patch: Partial<CurriculumRow>) => onChange(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)));

  return (
    <div className="stack-sm">
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Fach</th>
              <th className="num" style={{ width: 150 }}>
                Wochenstunden
              </th>
              <th style={{ width: 130 }}>Doppelstunde</th>
              <th style={{ width: 60 }}>
                <span className="sr-only">Entfernen</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.subject}>
                <td>
                  <strong>{name(r.subject)}</strong>{' '}
                  <span className="xsmall muted">
                    <SubjectAbbr id={r.subject} fallback={name(r.subject)} />
                  </span>
                  {r.teachers && r.teachers.length > 0 && (
                    <div className="xsmall muted">
                      Lehrkraft: <AbbrList kind="teacher" ids={r.teachers} />
                    </div>
                  )}
                </td>
                <td className="num">
                  <input
                    type="number"
                    min={0}
                    max={20}
                    value={r.hours}
                    disabled={disabled}
                    aria-label={`Wochenstunden ${name(r.subject)}`}
                    style={{ width: 80, textAlign: 'right' }}
                    onChange={(e) => update(i, { hours: Math.max(0, Math.min(20, parseInt(e.target.value || '0', 10))) })}
                  />
                </td>
                <td>
                  <label className="check">
                    <input type="checkbox" checked={r.double} disabled={disabled} onChange={(e) => update(i, { double: e.target.checked })} /> als Block
                  </label>
                </td>
                <td>
                  {!disabled && (
                    <button type="button" className="btn btn-sm btn-ghost" title={`${name(r.subject)} entfernen`} onClick={() => onChange(rows.filter((_, j) => j !== i))}>
                      <Icon name="trash" />
                      <span className="sr-only">{name(r.subject)} entfernen</span>
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {!rows.length && (
              <tr>
                <td colSpan={4} className="muted small">
                  Noch keine Fächer.
                </td>
              </tr>
            )}
          </tbody>
          <tfoot>
            <tr>
              <th>Summe</th>
              <th className="num">{total} Std./Woche</th>
              <th colSpan={2} />
            </tr>
          </tfoot>
        </table>
      </div>
      {!disabled && (
        <div className="row">
          <SubjectAdder options={free} onPick={(id) => onChange([...rows, { subject: id, hours: 2, double: false }])} canCreate={can(user, 'masterdata.edit')} />
        </div>
      )}
    </div>
  );
}

const toRows = (c: ClassCurriculum): CurriculumRow[] => c.entries.map((e) => ({ subject: e.subject, hours: e.hours, double: e.double, teachers: e.teachers }));

export function CurriculumTab({ classId }: { classId: string }) {
  const toast = useToast();
  const q = useApi((signal) => classesApi.curriculum(classId, signal), [classId], { live: ['curricula', 'courses', 'subjects'] });
  const [rows, setRows] = useState<CurriculumRow[] | null>(null);
  const [result, setResult] = useState<string[] | null>(null);
  const data = q.data;
  useEffect(() => {
    if (data) setRows(toRows(data));
  }, [data]);
  const dirty = useMemo(() => !!data && !!rows && JSON.stringify(toRows(data).map(({ teachers, ...r }) => r)) !== JSON.stringify(rows.map(({ teachers, ...r }) => r)), [data, rows]); // eslint-disable-line @typescript-eslint/no-unused-vars

  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!data || !rows) return <Loading />;

  const save = async (entries: CurriculumRow[]) => {
    try {
      const r = await classesApi.putCurriculum(classId, entries);
      const msgs: string[] = [];
      if (r.added.length) msgs.push(`${r.added.length} Fach/Fächer neu`);
      if (r.changed.length) msgs.push(`${r.changed.length} geändert`);
      if (r.removed.length) msgs.push(`${r.removed.length} entfernt`);
      setResult([...(r.warnings ?? []), ...(r.open_parts.length ? [`Ohne Lehrkraft: ${r.open_parts.join(', ')} – bitte unter Planung → Generator → „Lehrkräfte zuweisen“ oder direkt im Kurs zuweisen`] : [])]);
      toast.success(`Stundentafel gespeichert${msgs.length ? ` (${msgs.join(', ')})` : ''} – der Stundenplan wird automatisch angepasst`);
      q.reload();
    } catch (e) {
      toast.error(e, 'Stundentafel');
    }
  };

  return (
    <div className="stack">
      <section className="card stack-sm">
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <h2 style={{ margin: 0 }}>
            Stundentafel {data.class_name}{' '}
            <HelpTip label="Hilfe zur Stundentafel">
              Welches Fach hat die Klasse wie viele Stunden pro Woche? Nach dem Speichern entstehen die Kurse der Klasse sofort, passende Lehrkräfte werden
              zugewiesen und die automatische Neuplanung legt neue oder fehlende Stunden in den Stundenplan.
              {(data.source === 'grade' || data.source === 'profile') && ' Beim Speichern bekommt die Klasse eine eigene Stundentafel – die des Jahrgangs bleibt für die anderen Klassen.'}
            </HelpTip>
          </h2>
          <span className="badge">
            {data.source === 'class'
              ? 'eigene Stundentafel der Klasse'
              : data.source === 'profile'
                ? `${data.profile?.name ?? 'Jahrgang'}: ${data.curriculum_name}`
                : data.source === 'grade'
                  ? `Klassenstufe ${data.grade}: ${data.curriculum_name}`
                  : 'keine Stundentafel'}
          </span>
        </div>
        <CurriculumEditor rows={rows} subjects={data.subjects} onChange={setRows} disabled={!data.can_edit} />
        {data.can_edit && (
          <div className="row">
            <AsyncButton className="btn btn-primary" disabled={!dirty} onClick={() => save(rows)}>
              <Icon name="check" /> Speichern
            </AsyncButton>
            {dirty && (
              <button type="button" className="btn" onClick={() => setRows(toRows(data))}>
                Verwerfen
              </button>
            )}
            {data.source === 'class' && (
              <AsyncButton className="btn btn-ghost" confirm="Eigene Stundentafel entfernen? Danach gilt wieder die der Klassenstufe." onClick={() => save([])}>
                <Icon name="undo" /> Stundentafel der Klassenstufe verwenden
              </AsyncButton>
            )}
          </div>
        )}
        {result && result.length > 0 && (
          <Alert kind="warning" title="Hinweise">
            <ul className="small">
              {result.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </Alert>
        )}
      </section>
    </div>
  );
}

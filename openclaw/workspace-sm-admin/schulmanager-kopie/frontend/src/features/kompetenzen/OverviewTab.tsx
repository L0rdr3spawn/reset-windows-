/** Klasse × Kompetenzen als Heatmap (Tabelle), Filter nach Bereich und „braucht Unterstützung“. */
import { useMemo, useState } from 'react';
import { ErrorBox, Field, Loading, SegmentedControl } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { useStoredState } from '../../hooks/misc';
import { compApi, type AssessmentEntry, type CompetencyState, type Overview, type OverviewStudent } from './api';
import { AssessDialog } from './AssessDialog';
import { filterStudents, levelBucket, levelLabel, percent, type StudentFilter } from './logic';

function stub(c: { id: number; code: string; title: string; descriptors: string[] }, level: number | null): CompetencyState {
  const entry = (lv: number): AssessmentEntry => ({ id: 0, kind: 'teacher', level: lv, date: '', by: '', evidence_type: '', evidence_ref: '', evidence: '', comment: '', confirmed: false, confirmed_by: '' });
  return { ...c, teacher: level ? entry(level) : null, self: null, pending: false, history: [], links: [] };
}

export function OverviewTab({ canAssess, onOpenStudent }: { canAssess: boolean; onOpenStudent: (id: string, classId: string, frameworkId: number) => void }) {
  const [frameworkId, setFrameworkId] = useStoredState<number | null>('sm-comp-fw', null);
  const [classId, setClassId] = useStoredState<string | null>('sm-comp-class', null);
  const [areaId, setAreaId] = useState<number | null>(null);
  const [filter, setFilter] = useState<StudentFilter>('alle');
  const [editing, setEditing] = useState<{ student: OverviewStudent; comp: CompetencyState } | null>(null);
  const q = useApi<Overview>((signal) => compApi.overview({ framework_id: frameworkId ?? undefined, class_id: classId ?? undefined, area_id: areaId ?? undefined }, signal), [frameworkId, classId, areaId], { live: ['competency'] });
  const data = q.data;
  const fw = data?.framework ?? null;
  const students = useMemo(() => (data ? filterStudents(data.students, filter) : []), [data, filter]);
  const comps = useMemo(() => (fw ? fw.areas.flatMap((a) => a.competencies.map((c) => ({ ...c, area: a.id }))) : []), [fw]);

  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!data) return <Loading />;
  if (!data.frameworks.length) return <p className="muted">Noch kein Kompetenzrahmen. Anlegen unter „Rahmen“.</p>;
  if (!data.classes.length || !fw || !data.class) return <p className="muted">Für Sie sind keine Klassen mit Schüler/innen sichtbar.</p>;
  const n = fw.levels.length;

  return (
    <div className="stack">
      <div className="cp-filters">
        <Field label="Rahmen" htmlFor="cp-ov-fw">
          <select id="cp-ov-fw" value={fw.id} onChange={(e) => { setFrameworkId(Number(e.target.value)); setAreaId(null); }}>
            {data.frameworks.map((f) => (
              <option key={f.id} value={f.id}>
                {f.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Klasse" htmlFor="cp-ov-class">
          <select id="cp-ov-class" value={data.class.id} onChange={(e) => setClassId(e.target.value)}>
            {data.classes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Bereich" htmlFor="cp-ov-area">
          <select id="cp-ov-area" value={areaId ?? ''} onChange={(e) => setAreaId(e.target.value ? Number(e.target.value) : null)}>
            <option value="">Alle Bereiche</option>
            {fw.all_areas.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </Field>
        <div className="field">
          <span className="cp-filter-label">Anzeigen</span>
          <SegmentedControl<StudentFilter>
            label="Schüler/innen filtern"
            value={filter}
            onChange={setFilter}
            options={[
              { value: 'alle', label: 'Alle' },
              { value: 'unterstuetzung', label: `Unterstützung (${data.summary.support_students ?? 0})`, title: 'Wer braucht Unterstützung' },
              { value: 'offen', label: `Offen (${data.summary.pending ?? 0})`, title: 'Selbsteinschätzung wartet auf Bestätigung' },
            ]}
          />
        </div>
      </div>

      <Legend levels={fw.levels} />

      {!students.length ? (
        <p className="muted">Keine Schüler/innen für diesen Filter.</p>
      ) : (
        <>
          <div className="cp-scroll cp-heat-wrap">
            <table className="cp-heat">
              <thead>
                <tr>
                  <th rowSpan={2} className="cp-name-col" scope="col">
                    Schüler/in
                  </th>
                  {fw.areas.map((a) => (
                    <th key={a.id} colSpan={a.competencies.length} scope="colgroup" className="cp-area-head">
                      {a.name}
                    </th>
                  ))}
                  <th rowSpan={2} scope="col" className="cp-sum-col">
                    Stand
                  </th>
                </tr>
                <tr>
                  {comps.map((c, i) => (
                    <th key={c.id} scope="col" className="cp-comp-head" title={c.title}>
                      {c.code || i + 1}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {students.map((s) => (
                  <tr key={s.id}>
                    <th scope="row" className="cp-name-col">
                      <button type="button" className="cp-link" onClick={() => onOpenStudent(s.id, data.class!.id, fw.id)}>
                        {s.name}
                      </button>
                    </th>
                    {comps.map((c) => {
                      const cell = s.cells[String(c.id)];
                      const t = cell?.t ?? null;
                      const label = `${s.name}, ${c.title}: ${t ? levelLabel(fw.levels, t) : 'nicht eingeschätzt'}${cell?.s ? `, Selbsteinschätzung ${levelLabel(fw.levels, cell.s)}` : ''}`;
                      return (
                        <td key={c.id} className="cp-cell-td">
                          <button
                            type="button"
                            className={`cp-cell cp-b${levelBucket(t, n)}${cell?.p ? ' cp-pending' : ''}`}
                            aria-label={label}
                            title={label}
                            disabled={!canAssess}
                            onClick={() => setEditing({ student: s, comp: stub(c, t) })}
                          >
                            {t ?? '–'}
                            {cell?.s ? <span className="cp-cell-self">{cell.s}</span> : null}
                          </button>
                        </td>
                      );
                    })}
                    <td className="cp-sum">
                      <span className="mono">{percent(s.progress)}</span>
                      {s.support > 0 && <span className="badge badge-warning">{s.support}</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <ul className="cp-cards">
            {students.map((s) => (
              <li key={s.id} className="card cp-student-card">
                <button type="button" className="cp-link" onClick={() => onOpenStudent(s.id, data.class!.id, fw.id)}>
                  {s.name}
                </button>
                <progress className="cp-progress" max={100} value={Math.round(s.progress * 100)} aria-label={`Fortschritt ${s.name}`} />
                <span className="small mono">{percent(s.progress)}</span>
                {s.support > 0 && <span className="badge badge-warning">{s.support} Unterstützung</span>}
                {s.pending > 0 && <span className="badge badge-info">{s.pending} offen</span>}
              </li>
            ))}
          </ul>
        </>
      )}

      {editing && (
        <AssessDialog
          fw={fw}
          comp={editing.comp}
          studentId={editing.student.id}
          studentName={editing.student.name}
          onClose={() => setEditing(null)}
          onSaved={q.reload}
        />
      )}
    </div>
  );
}

function Legend({ levels }: { levels: readonly string[] }) {
  return (
    <ul className="cp-legend" aria-label="Legende der Niveaustufen">
      {levels.map((l, i) => (
        <li key={l + i}>
          <span className={`cp-cell-sample cp-b${levelBucket(i + 1, levels.length)}`}>{i + 1}</span> {l}
        </li>
      ))}
      <li>
        <span className="cp-cell-sample cp-b0">–</span> nicht eingeschätzt
      </li>
    </ul>
  );
}

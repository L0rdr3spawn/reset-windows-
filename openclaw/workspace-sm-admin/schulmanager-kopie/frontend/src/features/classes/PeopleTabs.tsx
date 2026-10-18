/**
 * Reiter „Lehrkräfte“ (Fach → Kurs/Kursteil → Lehrkraft, Klassenleitung markiert) und „Schüler/innen“ (mit Kurswahl).
 */
import { useId, useMemo, useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { AbbrList, SubjectAbbr } from '../../components/Abbr';
import { Empty } from '../../components/ui';
import { BirthDateEditor } from '../students/BirthDateEditor';
import { filterStudents, groupSubjects, partnerClasses, sortTeachers, type NameLookup } from './logic';
import type { ClassDetail, ClassStudent } from './types';

/** Erweiterungen des Reiters „Schüler/innen“ (Konten & Zugangsdaten, §11.3) */
export interface StudentsTabExtra {
  toolbar?: ReactNode;
  /** Auswahl je Zeile (Checkbox) */
  selected?: ReadonlySet<string>;
  onToggle?: (studentId: string) => void;
  /** zusätzlicher Inhalt rechts in der Zeile (Konto, Passwort) */
  rowSide?: (s: ClassStudent) => ReactNode;
}

function ClassTeacherBadge() {
  return <span className="badge badge-primary">Klassenleitung</span>;
}

export function TeachersTab({ detail, names }: { detail: ClassDetail; names: NameLookup }) {
  const cls = detail.class;
  const leadId = cls.class_teacher?.id ?? null;
  const groups = useMemo(() => groupSubjects(detail.subjects), [detail.subjects]);
  const teachers = useMemo(() => sortTeachers(detail.teachers), [detail.teachers]);
  return (
    <div className="grid grid-2 kl-grid">
      <section className="card" aria-labelledby="kl-subjects-h">
        <div className="card-head">
          <h2 id="kl-subjects-h">Fächer und Lehrkräfte</h2>
          <span className="badge">{groups.length === 1 ? '1 Fach' : `${groups.length} Fächer`}</span>
        </div>
        {groups.length === 0 ? (
          <Empty icon="info">Für diese Klasse sind keine Kurse angelegt.</Empty>
        ) : (
          <ul className="kl-subjects">
            {groups.map((g) => (
              <li key={g.subject}>
                <h3 className="kl-subject-name">
                  {g.name}
                  {g.name !== g.subject && (
                    <span className="muted small">
                      {' '}
                      (<SubjectAbbr id={g.subject} fallback={g.name} />)
                    </span>
                  )}
                </h3>
                <ul className="kl-rows">
                  {g.rows.map((r) => {
                    const partners = partnerClasses(r, cls.id);
                    return (
                      <li key={`${r.course_id}#${r.part ?? ''}`} className="kl-row">
                        <span className="kl-row-main">
                          <span>{r.label || g.name}</span>
                          <span className="small muted">
                            {r.hours} {r.hours === 1 ? 'Wochenstunde' : 'Wochenstunden'}
                            {r.coupled &&
                              (partners.length ? (
                                <>
                                  {' · gekoppelt mit '}
                                  <AbbrList kind="class" ids={partners} />
                                </>
                              ) : (
                                ' · Kursteil einer Kopplung'
                              ))}
                          </span>
                        </span>
                        <span className="kl-row-side">
                          {r.teacher ? <strong>{r.teacher.name}</strong> : <em className="muted">keine Lehrkraft</em>}
                          {r.teacher && r.teacher.id === leadId && <ClassTeacherBadge />}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section className="card" aria-labelledby="kl-teachers-h">
        <div className="card-head">
          <h2 id="kl-teachers-h">Lehrkräfte der Klasse</h2>
          <span className="badge">{teachers.length}</span>
        </div>
        {teachers.length === 0 ? (
          <Empty icon="user">Noch keine Lehrkräfte zugeordnet.</Empty>
        ) : (
          <ul className="kl-rows">
            {teachers.map((t) => (
              <li key={t.id} className="kl-row">
                <span className="kl-row-main">
                  <strong>{t.name}</strong>
                  <span className="small muted">{t.subjects.map((s) => names.subject(s)).join(', ') || '–'}</span>
                </span>
                <span className="kl-row-side">
                  {(t.is_class_teacher || t.id === leadId) && <ClassTeacherBadge />}
                  <span className="small">{t.hours > 0 ? `${t.hours} Std.` : 'unterrichtet die Klasse nicht'}</span>
                  <Link className="btn btn-ghost btn-sm" to={`/stundenplan/teacher/${encodeURIComponent(t.id)}`} aria-label={`Stundenplan von ${t.name}`}>
                    Plan
                  </Link>
                </span>
              </li>
            ))}
          </ul>
        )}
        {leadId && !teachers.some((t) => t.id === leadId) && cls.class_teacher && (
          <p className="small muted" style={{ marginTop: 8 }}>
            Klassenleitung: {cls.class_teacher.name} (unterrichtet die Klasse derzeit nicht)
          </p>
        )}
      </section>
    </div>
  );
}

export function StudentsTab({ detail, extra }: { detail: ClassDetail; extra?: StudentsTabExtra }) {
  const [q, setQ] = useState('');
  const id = useId();
  const all = detail.students ?? [];
  const shown = useMemo(() => filterStudents(all, q), [all, q]);
  if (detail.students === null) {
    return <Empty icon="lock">Die Schülerliste ist für Ihr Konto nicht freigegeben.</Empty>;
  }
  return (
    <section className="card" aria-labelledby="kl-students-h">
      <div className="card-head">
        <h2 id="kl-students-h">Schüler/innen</h2>
        <span className="badge">{all.length}</span>
      </div>
      {extra?.toolbar}
      {all.length > 8 && (
        <div className="field" style={{ maxWidth: 360 }}>
          <label htmlFor={id}>Name oder Kurs suchen</label>
          <input id={id} type="search" value={q} onChange={(e) => setQ(e.target.value)} autoComplete="off" />
        </div>
      )}
      {q && (
        <p className="small muted" aria-live="polite">
          {shown.length === 1 ? '1 Treffer' : `${shown.length} Treffer`}
        </p>
      )}
      {all.length === 0 ? (
        <Empty icon="users">Der Klasse sind keine Schüler/innen zugeordnet.</Empty>
      ) : (
        <ol className="kl-rows kl-students">
          {shown.map((s) => (
            <li key={s.id} className="kl-row">
              <span className="kl-row-main">
                {extra?.onToggle ? (
                  <label className="check">
                    <input type="checkbox" checked={!!extra.selected?.has(s.id)} onChange={() => extra.onToggle?.(s.id)} />
                    <strong>{s.name}</strong>
                  </label>
                ) : (
                  <strong>{s.name}</strong>
                )}{' '}
                <Link className="small" to={`/fehlzeiten/${encodeURIComponent(s.id)}`} aria-label={`Fehlzeiten und Förderung von ${s.name}`}>
                  Fehlzeiten &amp; Förderung
                </Link>
              </span>
              {s.can_set_birth_date && <BirthDateEditor studentId={s.id} name={s.name} value={s.birth_date ?? null} />}
              {s.courses.length > 0 && (
                <span className="kl-chips" aria-label={`Kurswahl von ${s.name}`}>
                  {s.courses.map((c) => (
                    <span key={`${c.course_id}#${c.part ?? ''}`} className="badge">
                      {c.label}
                    </span>
                  ))}
                </span>
              )}
              {extra?.rowSide && <span className="kl-row-side">{extra.rowSide(s)}</span>}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

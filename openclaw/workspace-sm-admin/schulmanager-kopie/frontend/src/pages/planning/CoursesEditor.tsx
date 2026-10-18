import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ApiError } from '../../api/client';
import { data as dataApi } from '../../api/endpoints';
import type { Course, CoursePart } from '../../api/types';
import { Icon } from '../../components/Icon';
import { HelpTip } from '../../components/HelpTip';
import { Modal } from '../../components/Modal';
import { MultiSelect, SearchSelect, type SelectOption } from '../../components/SearchSelect';
import { VirtualTable, type Column } from '../../components/VirtualTable';
import { Alert, AsyncButton, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { AbbrList, SubjectAbbr, TeacherAbbr } from '../../components/Abbr';
import { invalidate, useCollection } from '../../hooks/useCollection';
import { useSchoolYear } from '../../components/WeekNav';
import { todayISO } from '../../lib/dates';
import { useDebounced } from '../../hooks/misc';
import { matchesQuery, sortBy } from '../../lib/format';
import { WeekPatternInput } from '../../components/WeekPatternInput';
import { describeSelection, weeksSortValue } from '../../lib/weeks';
import { confirmAsk } from '../../lib/confirm';

const PIN_LABELS: Record<string, string> = { hours: 'Wochenstunden', double: 'Doppelstunde', weeks: 'Wochen', label: 'Bezeichnung', parts: 'Kursteile/Räume' };

function blankPart(): CoursePart {
  return { subject: '', teacher: null, room: null, room_type: null, label: '', students: null };
}

function CourseModal({ course, onClose, canEdit }: { course: Course; onClose: () => void; canEdit: boolean }) {
  const toast = useToast();
  const { year } = useSchoolYear(todayISO());
  const subjects = useCollection('subjects');
  const teachers = useCollection('teachers');
  const rooms = useCollection('rooms');
  const classes = useCollection('classes');
  const [c, setC] = useState<Course>(() => structuredClone(course));

  const teacherOptions: SelectOption[] = useMemo(
    () => sortBy(teachers.data ?? [], (t) => t.name).map((t) => ({ value: t.id, label: t.name, sub: `${t.id} · ${t.subjects.join(', ')}` })),
    [teachers.data],
  );
  const classOptions: SelectOption[] = useMemo(() => sortBy(classes.data ?? [], (x) => x.name).map((x) => ({ value: x.id, label: x.name })), [classes.data]);
  const roomOptions = useMemo(() => sortBy(rooms.data ?? [], (r) => r.id), [rooms.data]);
  const roomTypes = useMemo(() => [...new Set((rooms.data ?? []).map((r) => r.type))].sort(), [rooms.data]);

  const setPart = (i: number, p: Partial<CoursePart>) => setC((x) => ({ ...x, parts: x.parts.map((y, j) => (j === i ? { ...y, ...p } : y)) }));

  const save = async () => {
    try {
      if (!c.parts.length || c.parts.some((p) => !p.subject)) {
        toast.warning('Jeder Kursteil braucht ein Fach.');
        return;
      }
      if (c.id) await dataApi.update('courses', c.id, c);
      else {
        const { id: _omit, ...rest } = c;
        void _omit;
        await dataApi.create('courses', rest);
      }
      toast.success('Kurs gespeichert');
      invalidate('courses');
      onClose();
    } catch (e) {
      toast.error(e, 'Speichern');
    }
  };

  const remove = async () => {
    const fromTafel = course.origin === 'curriculum'
      ? '\n\nDieser Kurs stammt aus der Stundentafel und wird beim nächsten „Kurse erzeugen“ neu angelegt. Soll er dauerhaft entfallen, setzen Sie die Wochenstunden des Fachs in der Stundentafel auf 0.'
      : '';
    if (!(await confirmAsk({ title: 'Kurs löschen', message: `Möchten Sie den Kurs ${c.label || c.id} wirklich löschen? Zugehörige Stunden werden aus dem Plan entfernt.${fromTafel}`, confirmLabel: 'Löschen', danger: true }))) return;
    try {
      await dataApi.remove('courses', c.id);
    } catch (e) {
      if (e instanceof ApiError && e.isConflict && (await confirmAsk({ title: 'Verweise vorhanden', confirmLabel: 'Trotzdem löschen', danger: true, message: `${e.message}\n${e.conflicts.slice(0, 12).join('\n')}\n\nTrotzdem löschen und Verweise entfernen?` }))) {
        await dataApi.remove('courses', c.id, true);
      } else {
        toast.error(e, 'Löschen');
        return;
      }
    }
    toast.success('Kurs gelöscht');
    invalidate('courses');
    onClose();
  };

  return (
    <Modal
      size="lg"
      title={c.id ? `Kurs ${c.label || c.id}` : 'Neuer Kurs / Kopplung'}
      onClose={onClose}
      footer={
        canEdit ? (
          <>
            {c.id && (
              <button type="button" className="btn btn-ghost" onClick={remove}>
                <Icon name="trash" /> Löschen
              </button>
            )}
            <button type="button" className="btn" onClick={onClose}>
              Abbrechen
            </button>
            <AsyncButton className="btn btn-primary" onClick={save}>
              Speichern
            </AsyncButton>
          </>
        ) : undefined
      }
    >
      <div className="stack">
        {course.origin === 'curriculum' && (course.pinned?.length ?? 0) > 0 && (
          <Alert
            kind="info"
            title={
              <>
                {`Eigene Anpassungen: ${(course.pinned ?? []).map((f) => PIN_LABELS[f] ?? f).join(', ')}`}{' '}
                <HelpTip label="Erklärung: Eigene Anpassungen">Diese Anpassungen bleiben beim Erzeugen der Kurse erhalten.</HelpTip>
              </>
            }
            action={
              canEdit ? (
                <AsyncButton
                  className="btn btn-sm"
                  confirm="Anpassungen verwerfen? Beim nächsten „Kurse erzeugen“ gilt wieder die Stundentafel."
                  onClick={async () => {
                    try {
                      await dataApi.update('courses', course.id, { pinned: [] });
                      toast.success('Anpassungen verworfen');
                      invalidate('courses');
                      onClose();
                    } catch (e) {
                      toast.error(e);
                    }
                  }}
                >
                  Wie Stundentafel
                </AsyncButton>
              ) : undefined
            }
          />
        )}
        <div className="form-grid">
          <Field label="Bezeichnung" htmlFor="co-label" hint="z. B. „Religion/Ethik 7“ oder „Q1 Schiene 2“">
            <input id="co-label" type="text" value={c.label} disabled={!canEdit} onChange={(e) => setC({ ...c, label: e.target.value })} />
          </Field>
          <Field label="Wochenstunden" htmlFor="co-hours">
            <input id="co-hours" type="number" min={0} max={20} value={c.hours} disabled={!canEdit} onChange={(e) => setC({ ...c, hours: Math.max(0, parseInt(e.target.value || '0', 10)) })} />
          </Field>
          <div className="field">
            <span className="field-label">Doppelstunde</span>
            <label className="check">
              <input type="checkbox" checked={c.double} disabled={!canEdit} onChange={(e) => setC({ ...c, double: e.target.checked })} /> bevorzugt als Block
            </label>
          </div>
          <div className="span-all">
            <WeekPatternInput
              value={{ weeks: c.weeks, rhythm: c.rhythm ?? null }}
              onChange={(v) => setC({ ...c, weeks: v.weeks, rhythm: v.rhythm ?? null })}
              yearWeeks={year?.weeks_in_year ?? 52}
              label="Wochen, in denen der Kurs stattfindet"
              disabled={!canEdit}
            />
          </div>
          <div className="span-all">
            <Field label="Klassen" help="Mehrere Klassen ergeben einen klassenübergreifenden Kurs, z. B. Religion/Ethik oder in der Oberstufe.">
              <MultiSelect label="Klasse hinzufügen" options={classOptions} values={c.classes} onChange={(v) => setC({ ...c, classes: v })} placeholder="Klasse hinzufügen …" />
            </Field>
          </div>
        </div>

        <fieldset>
          <legend>
            Parallele Kursteile {c.parts.length > 1 ? `(Kopplung mit ${c.parts.length} Teilen)` : ''}{' '}
            <HelpTip label="Erklärung: Parallele Kursteile">Alle Teile liegen immer gleichzeitig, z. B. ev. Religion, kath. Religion und Ethik parallel.</HelpTip>
          </legend>
          {c.parts.map((p, i) => (
            <div className="rule-row" key={i}>
              <div className="row-between">
                <strong className="small">Teil {i + 1}</strong>
                {canEdit && c.parts.length > 1 && (
                  <button type="button" className="btn btn-ghost btn-sm" onClick={() => setC({ ...c, parts: c.parts.filter((_, j) => j !== i) })}>
                    <Icon name="trash" /> Entfernen
                  </button>
                )}
              </div>
              <div className="form-grid">
                <Field label="Fach" htmlFor={`cp-s-${i}`}>
                  <select id={`cp-s-${i}`} value={p.subject} disabled={!canEdit} onChange={(e) => setPart(i, { subject: e.target.value })}>
                    <option value="">– Fach –</option>
                    {sortBy(subjects.data ?? [], (s) => s.id).map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.id} – {s.name}
                      </option>
                    ))}
                  </select>
                </Field>
                <SearchSelect
                  label="Lehrkraft (leer = automatisch)"
                  options={teacherOptions}
                  value={p.teacher}
                  onChange={(v) => setPart(i, { teacher: v })}
                  allowClear
                  disabled={!canEdit}
                />
                <Field label="Fester Raum" htmlFor={`cp-r-${i}`}>
                  <select id={`cp-r-${i}`} value={p.room ?? ''} disabled={!canEdit} onChange={(e) => setPart(i, { room: e.target.value || null })}>
                    <option value="">automatisch</option>
                    {roomOptions.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.id} ({r.type})
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Raumtyp" htmlFor={`cp-t-${i}`}>
                  <select id={`cp-t-${i}`} value={p.room_type ?? ''} disabled={!canEdit} onChange={(e) => setPart(i, { room_type: e.target.value || null })}>
                    <option value="">wie Fach</option>
                    {roomTypes.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Bezeichnung" htmlFor={`cp-l-${i}`}>
                  <input id={`cp-l-${i}`} type="text" value={p.label} disabled={!canEdit} onChange={(e) => setPart(i, { label: e.target.value })} placeholder="z. B. ev. Religion" />
                </Field>
              </div>
              {p.students && <p className="xsmall muted">{p.students.length} zugeordnete Schüler/innen</p>}
            </div>
          ))}
          {canEdit && (
            <button type="button" className="btn btn-sm" style={{ marginTop: 8 }} onClick={() => setC({ ...c, parts: [...c.parts, blankPart()] })}>
              <Icon name="plus" /> Parallelen Kursteil hinzufügen
            </button>
          )}
        </fieldset>
      </div>
    </Modal>
  );
}

/** Kurse & Kopplungen: Liste (virtualisiert) mit Filter und Editor. */
export function CoursesEditor({ canEdit }: { canEdit: boolean }) {
  const courses = useCollection('courses');
  const classes = useCollection('classes');
  const [classId, setClassId] = useState<string | null>(null);
  const [q, setQ] = useState('');
  const query = useDebounced(q, 150);
  const [onlyCoupled, setOnlyCoupled] = useState(false);
  const [onlyOpen, setOnlyOpen] = useState(false);
  const [edit, setEdit] = useState<Course | null>(null);
  // Sprung aus dem Qualitätsbericht: /planung/kurse?kurs=<id> öffnet den Kurs
  const [search, setSearch] = useSearchParams();
  const deepLink = search.get('kurs');
  useEffect(() => {
    if (!deepLink || !courses.data) return;
    const hit = courses.data.find((c) => c.id === deepLink);
    if (hit) setEdit(hit);
    else setQ(deepLink);
    const sp = new URLSearchParams(search);
    sp.delete('kurs');
    setSearch(sp, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deepLink, courses.data]);

  const rows = useMemo(() => {
    return (courses.data ?? []).filter((c) => {
      if (classId && !c.classes.includes(classId)) return false;
      if (onlyCoupled && c.parts.length < 2 && c.classes.length < 2) return false;
      if (onlyOpen && !c.parts.some((p) => !p.teacher)) return false;
      if (query && !matchesQuery(`${c.id} ${c.label} ${c.classes.join(' ')} ${c.parts.map((p) => `${p.subject} ${p.teacher ?? ''} ${p.label}`).join(' ')}`, query)) return false;
      return true;
    });
  }, [courses.data, classId, query, onlyCoupled, onlyOpen]);

  const columns: Column<Course>[] = [
    { key: 'label', header: 'Kurs', render: (c) => c.label || c.id, sortValue: (c) => c.label || c.id },
    { key: 'classes', header: 'Klassen', render: (c) => <AbbrList kind="class" ids={c.classes} />, sortValue: (c) => c.classes.join(','), width: '140px' },
    { key: 'subjects', header: 'Fach/Teile', render: (c) =>
        c.parts.length ? (
          c.parts.map((p, i) => (
            <span key={i}>
              {i > 0 ? ' | ' : null}
              <SubjectAbbr id={p.subject} />
            </span>
          ))
        ) : (
          '–'
        ),
    },
    {
      key: 'teachers',
      header: 'Lehrkraft',
      render: (c) =>
        c.parts.map((p, i) => (
          <span key={i} className={p.teacher ? undefined : 'badge badge-danger'} style={{ marginRight: 4 }}>
            {p.teacher ? <TeacherAbbr id={p.teacher} /> : 'offen'}
          </span>
        )),
    },
    { key: 'hours', header: 'Std.', className: 'num', render: (c) => `${c.hours}${c.double ? ' (D)' : ''}`, sortValue: (c) => c.hours, width: '80px' },
    {
      key: 'weeks',
      header: 'Wochen',
      render: (c) => (c.weeks.length || c.rhythm ? describeSelection(c) : 'alle'),
      sortValue: (c) => weeksSortValue(c),
      width: '120px',
    },
    {
      key: 'origin',
      header: 'Herkunft',
      render: (c) => (c.origin === 'curriculum' ? (c.pinned?.length ? 'Stundentafel, angepasst' : 'Stundentafel') : 'manuell'),
      width: '120px',
    },
  ];

  const classOptions: SelectOption[] = useMemo(() => sortBy(classes.data ?? [], (c) => c.name).map((c) => ({ value: c.id, label: c.name })), [classes.data]);

  if (courses.error) return <ErrorBox error={courses.error} onRetry={courses.reload} />;
  if (!courses.data) return <Loading />;

  return (
    <div>
      <div className="toolbar">
        <div className="field">
          <SearchSelect label="Klasse" options={classOptions} value={classId} onChange={setClassId} allowClear placeholder="alle Klassen" />
        </div>
        <div className="field wide">
          <label htmlFor="co-q">Suche</label>
          <input id="co-q" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Fach, Kürzel, Bezeichnung …" />
        </div>
        <label className="check">
          <input type="checkbox" checked={onlyCoupled} onChange={(e) => setOnlyCoupled(e.target.checked)} /> nur Kopplungen
        </label>
        <label className="check">
          <input type="checkbox" checked={onlyOpen} onChange={(e) => setOnlyOpen(e.target.checked)} /> ohne Lehrkraft
        </label>
        {canEdit && (
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setEdit({ id: '', classes: classId ? [classId] : [], parts: [blankPart()], hours: 2, double: false, label: '', weeks: [], origin: 'manual' })}
          >
            <Icon name="plus" /> Kurs / Kopplung
          </button>
        )}
      </div>
      <VirtualTable rows={rows} columns={columns} rowKey={(c) => c.id} onRowClick={setEdit} caption="Kurse" height="60vh" />
      {edit && <CourseModal course={edit} onClose={() => setEdit(null)} canEdit={canEdit} />}
    </div>
  );
}

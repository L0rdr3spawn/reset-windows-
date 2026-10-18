/**
 * Klassen-Assistent `/klassen/neu` (§11.3): (1) Klasse → (2) Schülerliste einfügen → (3) Konten (Probelauf) →
 * (4) Ergebnis mit Zugangsbriefen (PDF/ZIP/E-Mail). Rechte prüft das Backend (masterdata.edit, Konten users.manage).
 */
import { useId, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import { Icon } from '../../components/Icon';
import { SearchSelect, type SelectOption } from '../../components/SearchSelect';
import { Alert, AsyncButton, Field } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { invalidate, useCollection } from '../../hooks/useCollection';
import { useTitle } from '../../hooks/misc';
import { collator } from '../../lib/format';
import { can } from '../../lib/permissions';
import { accountBody, AccountOptionsForm, CreateResultView, defaultAccountOpts, PreviewTable, type AccountOpts } from './accountsUi';
import { GRADE_MAX, GRADE_MIN } from '../../pages/planning/curricula';
import { classesApi } from './api';
import { StudentListEditor, studentListErrors } from './StudentListEditor';
import { gradeFromName, toApiStudents, type StudentDraft } from './studentList';
import type { ClassCreateBody, CreateStudentsResult } from './types';
import './classes.css';

const STEPS = ['Klasse', 'Schülerliste', 'Konten', 'Ergebnis'] as const;
const ID_BAD = /[/#?\\]/;

export default function NewClassPage() {
  useTitle('Neue Klasse');
  const me = useUser();
  const canManage = can(me, 'users.manage');
  const [step, setStep] = useState(0);
  const [cls, setCls] = useState({ id: '', name: '', grade: '', gradeTouched: false, site: '', room: null as string | null, teacher: null as string | null });
  const [rows, setRows] = useState<StudentDraft[]>([]);
  const [opts, setOpts] = useState<AccountOpts | null>(null);
  const [preview, setPreview] = useState<{ key: string; result: CreateStudentsResult } | null>(null);
  const [result, setResult] = useState<CreateStudentsResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ids = { id: useId(), name: useId(), grade: useId(), site: useId() };
  const classes = useCollection('classes');
  const sites = useCollection('sites');
  const rooms = useCollection('rooms');
  const teachers = useCollection('teachers');
  const students = useCollection('students');

  const grade = cls.gradeTouched ? Number(cls.grade) : (gradeFromName(cls.id) ?? Number(cls.grade));
  const idTaken = !!cls.id.trim() && (classes.data ?? []).some((c) => c.id.toLowerCase() === cls.id.trim().toLowerCase());
  const idError = !cls.id.trim()
    ? 'Bitte ein Kürzel angeben (z. B. 5a)'
    : ID_BAD.test(cls.id)
      ? 'Keine Zeichen / # ? \\ verwenden'
      : idTaken
        ? 'Diese Klasse gibt es schon'
        : null;
  const gradeError = !Number.isInteger(grade) || grade < GRADE_MIN || grade > GRADE_MAX ? `Klassenstufe ${GRADE_MIN} bis ${GRADE_MAX}` : null;

  const homeOf = useMemo(() => {
    const m = new Map<string, string[]>();
    for (const c of classes.data ?? []) if (c.home_room) m.set(c.home_room, [...(m.get(c.home_room) ?? []), c.id]);
    return m;
  }, [classes.data]);
  const roomOptions: SelectOption[] = useMemo(
    () =>
      [...(rooms.data ?? [])]
        .sort(
          (a, b) => Number(!!cls.site && a.site !== cls.site) - Number(!!cls.site && b.site !== cls.site) || collator.compare(a.name || a.id, b.name || b.id),
        )
        .map((r) => ({
          value: r.id,
          label: r.name || r.id,
          sub: [r.type, homeOf.get(r.id)?.length ? `Klassenraum von ${homeOf.get(r.id)?.join(', ')}` : ''].filter(Boolean).join(' · '),
          keywords: r.id,
        })),
    [rooms.data, homeOf, cls.site],
  );
  const teacherOptions: SelectOption[] = useMemo(
    () => [...(teachers.data ?? [])].sort((a, b) => collator.compare(a.name, b.name)).map((t) => ({ value: t.id, label: t.name, sub: t.id, keywords: t.id })),
    [teachers.data],
  );
  const existingNames = useMemo(() => (students.data ?? []).map((s) => s.name), [students.data]);
  const listErrors = studentListErrors(rows, existingNames);
  const options = opts ?? defaultAccountOpts(rows, canManage);

  const body = (dryRun: boolean): ClassCreateBody => ({
    id: cls.id.trim(),
    name: cls.name.trim() || undefined,
    grade,
    site: cls.site || null,
    home_room: cls.room,
    class_teacher: cls.teacher,
    students: toApiStudents(rows),
    ...accountBody(options, dryRun),
  });
  const inputsKey = JSON.stringify(body(true));

  const run = async (dryRun: boolean) => {
    setError(null);
    try {
      const r = await classesApi.create(body(dryRun));
      if (dryRun) setPreview({ key: inputsKey, result: r });
      else {
        setResult(r);
        setStep(3);
        invalidate('classes');
        invalidate('students');
      }
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  const roomHint = cls.room && homeOf.get(cls.room)?.length ? `schon Klassenraum von ${homeOf.get(cls.room)?.join(', ')}` : null;

  return (
    <div className="page stack kl-page">
      <div className="page-head">
        <div style={{ minWidth: 0 }}>
          <nav aria-label="Pfad" className="small">
            <Link to="/klassen">Klassen</Link> <span aria-hidden="true">›</span> <span className="muted">Neue Klasse</span>
          </nav>
          <h1>Neue Klasse anlegen</h1>
        </div>
      </div>

      <ol className="kl-steps" aria-label="Schritte">
        {STEPS.map((s, i) => (
          <li key={s} aria-current={i === step ? 'step' : undefined} className={i < step ? 'done' : undefined}>
            <span className="kl-step-num" aria-hidden="true">
              {i < step ? <Icon name="check" /> : i + 1}
            </span>
            {s}
          </li>
        ))}
      </ol>

      {error && (
        <Alert kind="error" title="Nicht möglich">
          {error}
        </Alert>
      )}

      {step === 0 && (
        <section className="card stack" aria-labelledby="kl-w1">
          <h2 id="kl-w1">1. Klasse</h2>
          <div className="form-grid">
            <Field label="Kürzel *" htmlFor={ids.id} hint="wie im Stundenplan, z. B. 5a; später nicht änderbar" error={cls.id ? idError : null}>
              <input
                id={ids.id}
                type="text"
                value={cls.id}
                maxLength={64}
                autoCapitalize="none"
                onChange={(e) => setCls({ ...cls, id: e.target.value })}
                aria-invalid={!!cls.id && !!idError}
              />
            </Field>
            <Field label="Anzeigename" htmlFor={ids.name} hint="optional, sonst wie das Kürzel">
              <input id={ids.name} type="text" value={cls.name} maxLength={100} onChange={(e) => setCls({ ...cls, name: e.target.value })} />
            </Field>
            <Field
              label="Klassenstufe *"
              htmlFor={ids.grade}
              error={cls.id || cls.gradeTouched ? gradeError : null}
              hint={!cls.gradeTouched && gradeFromName(cls.id) ? 'aus dem Kürzel erkannt' : undefined}
            >
              <input
                id={ids.grade}
                type="number"
                min={GRADE_MIN}
                max={GRADE_MAX}
                value={Number.isFinite(grade) && (cls.gradeTouched || gradeFromName(cls.id)) ? grade : cls.grade}
                onChange={(e) => setCls({ ...cls, grade: e.target.value, gradeTouched: true })}
              />
            </Field>
            {(sites.data?.length ?? 0) > 1 && (
              <Field label="Standort" htmlFor={ids.site}>
                <select id={ids.site} value={cls.site} onChange={(e) => setCls({ ...cls, site: e.target.value })}>
                  <option value="">– (aus dem Klassenraum)</option>
                  {(sites.data ?? []).map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </Field>
            )}
            <div>
              <SearchSelect
                label="Klassenraum"
                options={roomOptions}
                value={cls.room}
                onChange={(v) => setCls({ ...cls, room: v })}
                allowClear
                placeholder="Raum suchen …"
              />
              {roomHint && (
                <span className="small kl-sl-warn">
                  <Icon name="alert" /> {roomHint}
                </span>
              )}
            </div>
            <SearchSelect
              label="Klassenleitung"
              options={teacherOptions}
              value={cls.teacher}
              onChange={(v) => setCls({ ...cls, teacher: v })}
              allowClear
              placeholder="Lehrkraft suchen …"
            />
          </div>
          <div className="row">
            <button type="button" className="btn btn-primary" disabled={!!idError || !!gradeError} onClick={() => setStep(1)}>
              Weiter <Icon name="chevronRight" />
            </button>
            <Link className="btn" to="/klassen">
              Abbrechen
            </Link>
          </div>
        </section>
      )}

      {step === 1 && (
        <section className="card stack" aria-labelledby="kl-w2">
          <h2 id="kl-w2">2. Schülerliste – Klasse {cls.id}</h2>
          <StudentListEditor rows={rows} onChange={setRows} existing={existingNames} />
          <div className="row">
            <button type="button" className="btn" onClick={() => setStep(0)}>
              <Icon name="chevronLeft" /> Zurück
            </button>
            <button type="button" className="btn btn-primary" disabled={listErrors > 0} onClick={() => setStep(2)}>
              Weiter <Icon name="chevronRight" />
            </button>
            {rows.length === 0 && <span className="small muted">Ohne Schüler/innen wird nur die Klasse angelegt.</span>}
            {listErrors > 0 && <span className="small error-text">Bitte zuerst die markierten Zeilen korrigieren.</span>}
          </div>
        </section>
      )}

      {step === 2 && (
        <section className="card stack" aria-labelledby="kl-w3">
          <h2 id="kl-w3">3. Konten</h2>
          <AccountOptionsForm value={options} onChange={setOpts} canManage={canManage} rows={rows} />
          {preview && preview.key !== inputsKey && (
            <Alert kind="warning" title="Eingaben geändert">
              Die Vorschau passt nicht mehr – bitte „Probelauf“ erneut ausführen.
            </Alert>
          )}
          {preview && <PreviewTable result={preview.result} />}
          <div className="row">
            <button type="button" className="btn" onClick={() => setStep(1)}>
              <Icon name="chevronLeft" /> Zurück
            </button>
            <AsyncButton className={`btn${preview?.key === inputsKey ? '' : ' btn-primary'}`} onClick={() => run(true)}>
              <Icon name="eye" /> Probelauf (Vorschau)
            </AsyncButton>
            <AsyncButton className="btn btn-primary" disabled={preview?.key !== inputsKey} onClick={() => run(false)}>
              <Icon name="check" /> Klasse anlegen
            </AsyncButton>
          </div>
          {!preview && <p className="small muted">Der Probelauf zeigt Benutzernamen und Hinweise, ohne etwas zu speichern.</p>}
        </section>
      )}

      {step === 3 && result && (
        <section className="stack" aria-labelledby="kl-w4">
          <h2 id="kl-w4">4. Ergebnis</h2>
          <CreateResultView result={result} title={`Klasse ${result.class.name || result.class.id} angelegt`} />
          <div className="row">
            <Link className="btn btn-primary" to={`/klassen/${encodeURIComponent(result.class.id)}?tab=schueler`}>
              Zur Klasse {result.class.name || result.class.id} <Icon name="chevronRight" />
            </Link>
            <button
              type="button"
              className="btn"
              onClick={() => {
                setCls({ id: '', name: '', grade: '', gradeTouched: false, site: cls.site, room: null, teacher: null });
                setRows([]);
                setOpts(null);
                setPreview(null);
                setResult(null);
                setStep(0);
              }}
            >
              <Icon name="plus" /> Weitere Klasse anlegen
            </button>
          </div>
        </section>
      )}
    </div>
  );
}

/**
 * Stammdaten → Jahrgänge: frei definierbare Jahrgänge/Profile („5“, „5 Informatik“, „Montessori“, „GIF 26“) als
 * Karten mit Farbe, Klassen, Schülerzahl und Stundentafel. Hier werden Jahrgänge angelegt, Klassen zugeordnet (auch
 * nachträglich), Klassen hinzugefügt oder gelöscht (mit Folgen) und Jahrgänge gelöscht (Folgen-Vorschau, Umzug der
 * Klassen). Ältere Dokumente mit Stundentafeln je Klassenstufen-Nummer werden mit Vorschau umgestellt.
 * Keine Browser-Popups: alle Rückfragen laufen über Modal, ConfirmDialog und AsyncButton confirm=.
 */
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { data as dataApi } from '../../api/endpoints';
import type { GradeProfile } from '../../api/types';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { MultiSelect, type SelectOption } from '../../components/SearchSelect';
import { Alert, AsyncButton, Empty, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { invalidate, useCollection } from '../../hooks/useCollection';
import { textOn } from '../../lib/colors';
import { plural } from '../../lib/format';
import { RebuildCourses } from '../../pages/planning/RebuildCourses';
import { gradeLevelsApi } from './api';
import './gradeLevels.css';
import { GRADE_MAX, GRADE_MIN, gradeValid, impactLines, needsTypedConfirm, profileColor, profileImpactLines, profileShort, suggestClassNames } from './logic';
import type { CurriculumChoice, GradeClassRow, MigrationPreview, ProfileImpact, ProfileInput, ProfileRow, ProfilesResponse } from './types';

type ColorVars = React.CSSProperties & { '--jg-color'?: string; '--jg-on'?: string };

function colorVars(p: Pick<GradeProfile, 'id' | 'color'>): ColorVars {
  const c = profileColor(p);
  return { '--jg-color': c, '--jg-on': textOn(c) };
}

/* ------------------------------------------------------------------ Jahrgang anlegen / ändern */
type TafelMode = 'keep' | 'existing' | 'new' | 'derive' | 'none';

function ProfileDialog({
  data,
  profile,
  preset,
  onClose,
  onDone,
}: {
  data: ProfilesResponse;
  /** vorhandener Jahrgang (ändern) oder null (anlegen) */
  profile: ProfileRow | null;
  /** Vorbelegung beim Anlegen aus einer Klassenstufe ohne Jahrgang */
  preset?: { grade: number | null; classIds: string[] } | null;
  onClose: () => void;
  onDone: () => void;
}) {
  const toast = useToast();
  const editing = !!profile;
  const [name, setName] = useState(profile?.name ?? (preset?.grade !== null && preset?.grade !== undefined ? `Jahrgang ${preset.grade}` : ''));
  const [short, setShort] = useState(profile?.short ?? (preset?.grade !== null && preset?.grade !== undefined ? String(preset.grade) : ''));
  const [grade, setGrade] = useState<string>(profile?.grade !== null && profile?.grade !== undefined ? String(profile.grade) : preset?.grade !== null && preset?.grade !== undefined ? String(preset.grade) : '');
  const [color, setColor] = useState(profile?.color ?? '');
  const [department, setDepartment] = useState(profile?.department ?? '');
  const [description, setDescription] = useState(profile?.description ?? '');
  const [mode, setMode] = useState<TafelMode>(editing ? 'keep' : data.curricula.length ? 'derive' : 'new');
  const [curId, setCurId] = useState(profile?.curriculum ?? '');
  const [baseId, setBaseId] = useState(profile?.curriculum ?? '');
  const [tafelName, setTafelName] = useState('');
  const [classIds, setClassIds] = useState<string[]>(preset?.classIds ?? []);
  const classes = useCollection('classes');

  const g = grade.trim() === '' ? null : Number(grade);
  const gradeOk = g === null || gradeValid(g);
  const options = data.curricula.filter((c) => !c.for_classes);
  const classOptions: SelectOption[] = useMemo(
    () =>
      (classes.data ?? [])
        .slice()
        .sort((a, b) => a.grade - b.grade || a.name.localeCompare(b.name, 'de', { numeric: true }))
        .map((c) => {
          const p = c.profile ? data.profiles.find((x) => x.id === c.profile) : null;
          return { value: c.id, label: c.name, sub: p ? `zurzeit ${p.name}` : `Stufe ${c.grade} · ohne Jahrgang`, keywords: p?.name };
        }),
    [classes.data, data.profiles],
  );
  const ok = !!name.trim() && gradeOk && (mode !== 'existing' || !!curId) && (mode !== 'derive' || !!baseId);

  const choice = (): CurriculumChoice | null | undefined => {
    switch (mode) {
      case 'keep':
        return undefined;
      case 'none':
        return null;
      case 'existing':
        return { id: curId };
      case 'new':
        return { new: true, name: tafelName.trim() || `Stundentafel ${name.trim()}` };
      case 'derive':
        return { base: baseId, name: tafelName.trim() || `Stundentafel ${name.trim()}` };
    }
  };

  const save = async () => {
    const body: ProfileInput = { name: name.trim(), short: short.trim(), grade: g, color, department: department.trim(), description: description.trim() };
    const c = choice();
    if (c !== undefined) body.curriculum = c;
    try {
      if (profile) {
        await gradeLevelsApi.updateProfile(profile.id, body);
        toast.success('Jahrgang gespeichert');
      } else {
        body.class_ids = classIds;
        const r = await gradeLevelsApi.createProfile(body);
        toast.success(`Jahrgang „${r.name}“ angelegt`);
      }
    } catch (e) {
      toast.error(e, 'Jahrgang');
      return;
    }
    invalidate('grade_profiles', 'classes', 'curricula');
    onDone();
    onClose();
  };

  const tafelLabel = (m: TafelMode) =>
    ({ keep: `Beibehalten (${profile?.curriculum_info?.name ?? 'keine'})`, existing: 'Vorhandene Stundentafel', new: 'Neue, leere Stundentafel', derive: 'Von einer Stundentafel ableiten', none: 'Keine Stundentafel' })[m];
  const modes: TafelMode[] = editing ? ['keep', 'existing', 'derive', 'new', 'none'] : ['derive', 'existing', 'new', 'none'];

  return (
    <Modal
      title={editing ? `Jahrgang „${profile.name}“ bearbeiten` : 'Jahrgang anlegen'}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" disabled={!ok} onClick={save}>
            {editing ? 'Speichern' : 'Anlegen'}
          </AsyncButton>
        </>
      }
    >
      <form
        className="form-grid"
        onSubmit={(e) => {
          e.preventDefault();
          if (ok) void save();
        }}
      >
        <Field label="Name" htmlFor="jg-name" help="Frei wählbar, z. B. „5“, „5 Informatik“, „Montessori“ oder „GIF 26“. Der Name erscheint an den Klassen und in der Stundentafel.">
          <input id="jg-name" type="text" maxLength={120} value={name} onChange={(e) => setName(e.target.value)} autoFocus required />
        </Field>
        <Field label="Kurzname" htmlFor="jg-short" help="Kürzel für Karten und Spaltenköpfe, z. B. „5 IF“. Leer = Klassenstufe.">
          <input id="jg-short" type="text" maxLength={20} value={short} onChange={(e) => setShort(e.target.value)} />
        </Field>
        <Field label="Klassenstufe" htmlFor="jg-grade" help="Zahl für Sortierung, Klassenarbeits-Grenzen und Vorlagen; optional, z. B. leer für jahrgangsgemischte Gruppen." error={gradeOk ? null : `Nur ${GRADE_MIN} bis ${GRADE_MAX} oder leer`}>
          <input id="jg-grade" type="number" min={GRADE_MIN} max={GRADE_MAX} value={grade} onChange={(e) => setGrade(e.target.value)} />
        </Field>
        <Field label="Farbe" htmlFor="jg-color">
          <div className="jg-color-row">
            <input id="jg-color" type="color" value={color || profileColor({ id: profile?.id ?? (name || 'neu'), color: '' })} onChange={(e) => setColor(e.target.value)} />
            <button type="button" className="btn btn-sm btn-ghost" onClick={() => setColor('')} disabled={!color}>
              Automatisch
            </button>
          </div>
        </Field>
        <Field label="Schulform / Abteilung" htmlFor="jg-dep" help="Optional, z. B. „Gymnasium“, „Berufsschule Holz“ oder „Abendschule“.">
          <input id="jg-dep" type="text" maxLength={80} value={department} onChange={(e) => setDepartment(e.target.value)} />
        </Field>
        <Field label="Beschreibung" htmlFor="jg-desc" className="span-all">
          <textarea id="jg-desc" rows={2} maxLength={500} value={description} onChange={(e) => setDescription(e.target.value)} />
        </Field>

        <fieldset className="span-all stack-sm" style={{ border: 0, padding: 0, margin: 0 }}>
          <legend className="field-label">
            Stundentafel{' '}
            <HelpTip label="Hilfe zur Stundentafel des Jahrgangs">
              Der Jahrgang bestimmt die Stundentafel seiner Klassen. Ableiten heißt: wie die Basis, plus eigene Abweichungen („plus 2 Std. Informatik, minus 1 Std. Kunst“); Änderungen an
              der Basis wirken weiter. Die Kurse ändern sich erst mit „Kurse erzeugen“.
            </HelpTip>
          </legend>
          <div className="stack-sm">
            {modes.map((m) => (
              <div key={m}>
                <label className="check">
                  <input type="radio" name="jg-tafel" checked={mode === m} onChange={() => setMode(m)} /> {tafelLabel(m)}
                </label>
              </div>
            ))}
          </div>
          {mode === 'existing' && (
            <Field label="Stundentafel" htmlFor="jg-cur">
              <select id="jg-cur" value={curId} onChange={(e) => setCurId(e.target.value)}>
                <option value="">– wählen –</option>
                {options.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.hours} Std.{c.base ? ', abgeleitet' : ''})
                  </option>
                ))}
              </select>
            </Field>
          )}
          {mode === 'derive' && (
            <Field label="Basis" htmlFor="jg-base">
              <select id="jg-base" value={baseId} onChange={(e) => setBaseId(e.target.value)}>
                <option value="">– wählen –</option>
                {options.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.hours} Std.)
                  </option>
                ))}
              </select>
            </Field>
          )}
          {(mode === 'new' || mode === 'derive') && (
            <Field label="Name der Stundentafel" htmlFor="jg-tname" hint={`Leer = „Stundentafel ${name.trim() || '…'}“`} hintInline>
              <input id="jg-tname" type="text" maxLength={120} value={tafelName} onChange={(e) => setTafelName(e.target.value)} />
            </Field>
          )}
        </fieldset>

        {!editing && (
          <div className="span-all">
            <MultiSelect label="Klassen zuordnen" options={classOptions} values={classIds} onChange={setClassIds} placeholder="Klasse suchen …" />
          </div>
        )}
      </form>
    </Modal>
  );
}

/* ------------------------------------------------------------------ Klassen zuordnen */
function AssignClassesDialog({ data, profile, onClose, onDone }: { data: ProfilesResponse; profile: ProfileRow; onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const classes = useCollection('classes');
  const initial = useMemo(() => profile.classes.map((c) => c.id), [profile.classes]);
  const [values, setValues] = useState<string[]>(initial);
  const options: SelectOption[] = useMemo(
    () =>
      (classes.data ?? [])
        .slice()
        .sort((a, b) => a.grade - b.grade || a.name.localeCompare(b.name, 'de', { numeric: true }))
        .map((c) => {
          const p = c.profile ? data.profiles.find((x) => x.id === c.profile) : null;
          return { value: c.id, label: c.name, sub: p && p.id !== profile.id ? `zurzeit ${p.name}` : p ? profile.name : `Stufe ${c.grade} · ohne Jahrgang`, keywords: p?.name };
        }),
    [classes.data, data.profiles, profile],
  );
  const added = values.filter((v) => !initial.includes(v));
  const removed = initial.filter((v) => !values.includes(v));
  const moving = added.filter((id) => classes.data?.find((c) => c.id === id)?.profile);

  const save = async () => {
    try {
      if (added.length) await gradeLevelsApi.assign(added, profile.id);
      if (removed.length) await gradeLevelsApi.assign(removed, null);
    } catch (e) {
      toast.error(e, 'Zuordnung');
      return;
    }
    invalidate('classes', 'grade_profiles');
    toast.success(`Zuordnung zu „${profile.name}“ gespeichert`);
    onDone();
    onClose();
  };

  return (
    <Modal
      title={`Klassen in „${profile.name}“`}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" disabled={!added.length && !removed.length} onClick={save}>
            Zuordnung speichern
          </AsyncButton>
        </>
      }
    >
      <div className="stack">
        <MultiSelect label="Klassen dieses Jahrgangs" options={options} values={values} onChange={setValues} placeholder="Klasse suchen …" />
        {moving.length > 0 && (
          <Alert kind="info">
            {plural(moving.length, 'Klasse wechselt', 'Klassen wechseln')} aus einem anderen Jahrgang. Die Kurse ändern sich erst mit „Kurse erzeugen“.
          </Alert>
        )}
        {removed.length > 0 && <Alert kind="warning">{plural(removed.length, 'Klasse bleibt', 'Klassen bleiben')} danach ohne Jahrgang.</Alert>}
      </div>
    </Modal>
  );
}

/* ------------------------------------------------------------------ Jahrgang löschen */
function DeleteProfileDialog({ profile, onClose, onDone }: { profile: ProfileRow; onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const impact = useApi<ProfileImpact>((signal) => gradeLevelsApi.profileImpact(profile.id, signal), [profile.id]);
  const [moveTo, setMoveTo] = useState('');
  const [delCur, setDelCur] = useState(false);
  const imp = impact.data;
  const lines = imp ? profileImpactLines(imp, moveTo || null, delCur) : [];

  const run = async () => {
    const r = await gradeLevelsApi.deleteProfile(profile.id, { moveTo: moveTo || null, deleteCurriculum: delCur });
    invalidate('grade_profiles', 'classes', 'curricula');
    toast.success(`Jahrgang „${profile.name}“ gelöscht${r.moved_classes.length ? `, ${plural(r.moved_classes.length, 'Klasse', 'Klassen')} umgezogen` : ''}`);
    onDone();
    onClose();
  };

  return (
    <Modal
      title="Jahrgang löschen?"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-danger" disabled={!imp} onClick={run}>
            <Icon name="trash" /> Jahrgang löschen
          </AsyncButton>
        </>
      }
    >
      <div className="stack">
        <p style={{ margin: 0 }}>
          <strong>{profile.name}</strong> wird gelöscht. Rückgängig über den Planverlauf.
        </p>
        {impact.error ? <ErrorBox error={impact.error} onRetry={impact.reload} /> : !imp ? <Loading /> : null}
        {imp && (
          <>
            {imp.classes.length > 0 && (
              <Field label="Klassen" htmlFor="jg-move" help="Die Klassen bleiben bestehen. Mit einem Ziel-Jahrgang behalten sie eine Stundentafel; ohne Ziel sind sie bis zur nächsten Zuordnung ohne Stundentafel.">
                <select id="jg-move" value={moveTo} onChange={(e) => setMoveTo(e.target.value)}>
                  <option value="">ohne Jahrgang lassen</option>
                  {imp.alternatives.map((a) => (
                    <option key={a.id} value={a.id}>
                      in „{a.name}“ verschieben{a.grade !== null ? ` (Stufe ${a.grade})` : ''}
                    </option>
                  ))}
                </select>
              </Field>
            )}
            {imp.curriculum && !imp.curriculum.shared && (
              <label className="check">
                <input type="checkbox" checked={delCur} onChange={(e) => setDelCur(e.target.checked)} /> Stundentafel „{imp.curriculum.name}“ mitlöschen (wird nur hier verwendet)
              </label>
            )}
            {lines.length === 0 ? (
              <p className="small muted" style={{ margin: 0 }}>
                Keine Klassen und keine Kurse betroffen.
              </p>
            ) : (
              <ul className="small" aria-label="Folgen des Löschens" style={{ margin: 0 }}>
                {lines.map((l) => (
                  <li key={l.text} className={l.danger ? 'error-text' : undefined}>
                    {l.danger ? <strong>{l.text}</strong> : l.text}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>
    </Modal>
  );
}

/* ------------------------------------------------------------------ Umstellung alter Dokumente */
function MigrationDialog({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const q = useApi<MigrationPreview>((signal) => gradeLevelsApi.migrationPreview(signal), []);
  const rows = q.data?.profiles ?? [];
  const run = async () => {
    const r = await gradeLevelsApi.migrate();
    invalidate('grade_profiles', 'classes', 'curricula');
    toast.success(`${plural(r.profiles.filter((p) => !p.exists).length, 'Jahrgang', 'Jahrgänge')} angelegt, ${plural(r.classes, 'Klasse', 'Klassen')} zugeordnet`);
    onDone();
    onClose();
  };
  return (
    <Modal
      title="Klassenstufen in Jahrgänge übernehmen"
      size="lg"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" disabled={!q.data?.pending} onClick={run}>
            Übernehmen
          </AsyncButton>
        </>
      }
    >
      <div className="stack">
        <p style={{ margin: 0 }}>
          Vorschau: je Klassenstufe ein Jahrgang mit der bisherigen Stundentafel; die Klassen der Stufe werden zugeordnet.{' '}
          <HelpTip label="Hilfe zur Umstellung">
            Bisher galt eine Stundentafel über die Klassenstufen-Nummer. Danach gilt sie über den Jahrgang; Namen, Farben und weitere Jahrgänge („5 Informatik“) lassen sich frei
            ändern und anlegen. Bei mehreren Tafeln je Stufe bleibt die Zuordnung offen. Rückgängig über den Planverlauf.
          </HelpTip>
        </p>
        {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : !q.data ? <Loading /> : null}
        {q.data && rows.length === 0 && <Empty>Nichts zu übernehmen.</Empty>}
        {rows.length > 0 && (
          <div className="table-wrap">
            <table className="table table-compact jg-preview-table">
              <caption className="sr-only">Vorschau der Umstellung</caption>
              <thead>
                <tr>
                  <th scope="col">Jahrgang</th>
                  <th scope="col">Stufe</th>
                  <th scope="col">Stundentafel</th>
                  <th scope="col">Klassen</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <td>
                      {r.name} {r.exists && <span className="badge">vorhanden</span>}
                    </td>
                    <td className="num">{r.grade}</td>
                    <td>
                      {r.conflict ? (
                        <span className="badge badge-danger" title={(r.candidates ?? []).join(', ')}>
                          mehrere Tafeln – bleibt offen
                        </span>
                      ) : (
                        r.curriculum_name ?? <span className="muted">keine</span>
                      )}
                    </td>
                    <td>{r.classes.length ? r.classes.join(', ') : <span className="muted">–</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Modal>
  );
}

/* ------------------------------------------------------------------ Klassen anlegen */
function AddClassesDialog({ data, profile, onClose, onDone }: { data: ProfilesResponse; profile: ProfileRow | null; onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const [grade, setGrade] = useState(String(profile?.grade ?? ''));
  const [count, setCount] = useState(1);
  const g = Number(grade);
  const existing = useMemo(() => [...data.profiles.flatMap((p) => p.classes.map((c) => c.id)), ...data.unassigned.flatMap((u) => u.classes.map((c) => c.id))], [data]);
  const suggested = useMemo(() => (grade.trim() && gradeValid(g) ? suggestClassNames(g, existing, count) : []), [g, grade, existing, count]);
  const [edited, setEdited] = useState<Record<number, string>>({});
  const names = suggested.map((n, i) => edited[i] ?? n);
  const [copyFrom, setCopyFrom] = useState('');
  const [courses, setCourses] = useState(true);
  const dup =
    names.some((n, i) => names.findIndex((m) => m.trim().toLowerCase() === n.trim().toLowerCase()) !== i) ||
    names.some((n) => existing.some((e) => e.toLowerCase() === n.trim().toLowerCase()));
  const ok = grade.trim() !== '' && gradeValid(g) && count >= 1 && names.length === count && names.every((n) => n.trim()) && !dup;
  const hasTafel = !!profile?.curriculum_info;

  const save = async () => {
    const r = await gradeLevelsApi.createClasses(g, { names: names.map((n) => n.trim()), copy_from: copyFrom || null, create_courses: courses, profile: profile?.id ?? null });
    invalidate('classes', 'courses', 'grade_profiles');
    toast.success(`${plural(r.created.length, 'Klasse', 'Klassen')} angelegt`);
    if (r.warnings.length) toast.warning('Hinweise zu den neuen Klassen', r.warnings.slice(0, 5));
    onDone();
    onClose();
  };

  return (
    <Modal
      title={profile ? `Klassen zu „${profile.name}“ hinzufügen` : 'Klassen anlegen'}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" disabled={!ok} onClick={save}>
            {plural(count, 'Klasse', 'Klassen')} anlegen
          </AsyncButton>
        </>
      }
    >
      <div className="form-grid">
        <Field label="Klassenstufe" htmlFor="gl-grade" help="Zahl in der Klassenbezeichnung und für Vorschläge wie „5a, 5b“." error={grade.trim() === '' || gradeValid(g) ? null : `Nur ${GRADE_MIN} bis ${GRADE_MAX}`}>
          <input
            id="gl-grade"
            type="number"
            min={GRADE_MIN}
            max={GRADE_MAX}
            value={grade}
            onChange={(e) => {
              setGrade(e.target.value);
              setEdited({});
            }}
          />
        </Field>
        <Field label="Anzahl" htmlFor="gl-count">
          <input
            id="gl-count"
            type="number"
            min={1}
            max={12}
            value={count}
            onChange={(e) => {
              setCount(Math.max(1, Math.min(12, Number(e.target.value) || 1)));
              setEdited({});
            }}
          />
        </Field>
        <div className="span-all stack-sm">
          <span className="field-label">Kürzel der neuen Klassen</span>
          <div className="row" style={{ flexWrap: 'wrap', gap: 6 }}>
            {names.map((n, i) => (
              <input key={i} type="text" aria-label={`Kürzel der ${i + 1}. neuen Klasse`} style={{ width: 90 }} maxLength={20} value={n} onChange={(e) => setEdited((x) => ({ ...x, [i]: e.target.value }))} />
            ))}
            {names.length === 0 && <span className="small muted">Klassenstufe eingeben.</span>}
          </div>
          {dup && <span className="error-text">Ein Kürzel gibt es schon oder steht doppelt da.</span>}
        </div>
        {profile && profile.classes.length > 0 && (
          <Field label="Einstellungen übernehmen von" htmlFor="gl-copy" help="Standort, Stunden pro Tag und Unterrichtstage der gewählten Klasse.">
            <select id="gl-copy" value={copyFrom} onChange={(e) => setCopyFrom(e.target.value)}>
              <option value="">erste Klasse des Jahrgangs</option>
              {profile.classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </Field>
        )}
        <label className="check span-all">
          <input type="checkbox" checked={courses} onChange={(e) => setCourses(e.target.checked)} /> Kurse aus der Stundentafel gleich erzeugen
        </label>
        {!hasTafel && courses && (
          <div className="span-all">
            <Alert kind="info">{profile ? 'Der Jahrgang hat noch keine Stundentafel – die Kurse entstehen, sobald eine zugeordnet ist.' : 'Ohne Jahrgang entstehen keine Kurse.'}</Alert>
          </div>
        )}
      </div>
    </Modal>
  );
}

/* ------------------------------------------------------------------ Klassen löschen */
/** „Möchten Sie das wirklich löschen?“ mit Folgen (Schüler/innen, Kurse, Stunden) – auch aus den Stammdaten nutzbar. */
export function DeleteClassesDialog({ title, ids, data: given, onClose, onDone }: { title: string; ids: string[]; data?: ProfilesResponse; onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const own = useApi<ProfilesResponse>((signal) => gradeLevelsApi.profiles(signal), [], { enabled: !given });
  const data = given ?? own.data;
  const impact = useApi((signal) => gradeLevelsApi.impact(ids, signal), [ids.join(',')]);
  const [move, setMove] = useState('');
  const [typed, setTyped] = useState('');
  const t = impact.data?.totals;
  const targets = useMemo(() => {
    if (!data) return [];
    const all = [...data.profiles.flatMap((p) => p.classes.map((c) => ({ ...c, where: p.name }))), ...data.unassigned.flatMap((u) => u.classes.map((c) => ({ ...c, where: `Stufe ${u.grade}` })))];
    return all.filter((c) => !ids.includes(c.id));
  }, [data, ids]);
  const moved = !!move;
  const lines = t ? impactLines(t, moved) : [];
  const typedNeeded = t ? needsTypedConfirm(t, moved) : true;
  const word = 'löschen';
  const ready = !!t && (!typedNeeded || typed.trim().toLowerCase() === word);

  const run = async () => {
    const r = await gradeLevelsApi.deleteClasses(ids, move || null);
    invalidate('classes', 'students', 'courses', 'curricula', 'grade_profiles');
    toast.success(`${plural(r.deleted.length, 'Klasse', 'Klassen')} gelöscht${r.moved_students ? `, ${plural(r.moved_students, 'Schüler/in', 'Schüler/innen')} verschoben` : ''}`);
    onDone();
    onClose();
  };

  return (
    <Modal
      title="Möchten Sie das wirklich löschen?"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-danger" disabled={!ready} onClick={run}>
            <Icon name="trash" /> Endgültig löschen
          </AsyncButton>
        </>
      }
    >
      <div className="stack">
        <p style={{ margin: 0 }}>
          <strong>{title}</strong> wird endgültig gelöscht.
        </p>
        {impact.error ? <ErrorBox error={impact.error} onRetry={impact.reload} /> : !t ? <Loading /> : null}
        {t && (
          <>
            {lines.length === 0 ? (
              <p className="small muted" style={{ margin: 0 }}>
                Daran hängen keine Schüler/innen, Kurse oder Stunden.
              </p>
            ) : (
              <ul className="small" aria-label="Folgen des Löschens">
                {lines.map((l) => (
                  <li key={l.text} className={l.danger ? 'error-text' : undefined}>
                    {l.danger ? <strong>{l.text}</strong> : l.text}
                  </li>
                ))}
              </ul>
            )}
            {t.students > 0 && (
              <Field label="Schüler/innen" htmlFor="gl-move" help="Verschieben behält die Personen; Kurswahlen, die die Zielklasse nicht hat, entfallen.">
                <select id="gl-move" value={move} onChange={(e) => setMove(e.target.value)}>
                  <option value="">mit der Klasse löschen</option>
                  {targets.map((c) => (
                    <option key={c.id} value={c.id}>
                      verschieben nach {c.name} ({c.where})
                    </option>
                  ))}
                </select>
              </Field>
            )}
            {typedNeeded && (
              <Field label={`Zur Sicherheit „${word}“ eintippen`} htmlFor="gl-typed">
                <input id="gl-typed" type="text" autoComplete="off" value={typed} onChange={(e) => setTyped(e.target.value)} placeholder={word} />
              </Field>
            )}
          </>
        )}
      </div>
    </Modal>
  );
}

/* ------------------------------------------------------------------ Klassenzeile (Tabelle im Jahrgang) */
function ClassRow({ c, canEdit, onDelete, onUnassign }: { c: GradeClassRow; canEdit: boolean; onDelete: () => void; onUnassign?: () => Promise<void> }) {
  const toast = useToast();
  const classes = useCollection('classes');
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(c.name);

  const rename = async () => {
    const full = (classes.data ?? []).find((x) => x.id === c.id);
    if (!full || !name.trim()) return;
    await dataApi.update('classes', c.id, { ...full, name: name.trim() });
    invalidate('classes');
    toast.success('Klasse umbenannt');
    setEditing(false);
  };

  return (
    <tr>
      <td>
        {editing ? (
          <span className="row" style={{ gap: 4, flexWrap: 'nowrap' }}>
            <input
              type="text"
              className="input-sm"
              aria-label={`Neue Bezeichnung für ${c.id}`}
              value={name}
              maxLength={100}
              autoFocus
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') void rename();
                if (e.key === 'Escape') setEditing(false);
              }}
            />
            <AsyncButton className="btn btn-sm btn-primary" onClick={rename} disabled={!name.trim()}>
              OK
            </AsyncButton>
          </span>
        ) : (
          <>
            <Link to={`/klassen/${encodeURIComponent(c.id)}`}>
              <strong>{c.name}</strong>
            </Link>
            {c.name !== c.id && <span className="xsmall muted"> ({c.id})</span>}
          </>
        )}
      </td>
      <td className="num">{c.students}</td>
      <td>{c.class_teacher?.name ?? <span className="muted">–</span>}</td>
      <td>
        {c.curriculum_conflict ? (
          <span className="badge badge-danger">Überschneidung</span>
        ) : c.curriculum_name ? (
          <>
            <span className="small">{c.curriculum_name}</span> {c.curriculum_source === 'class' && <span className="badge">eigene</span>}
            {c.curriculum_source === 'grade' && <span className="badge">über Stufe</span>}
          </>
        ) : (
          <span className="badge badge-warning">keine</span>
        )}
      </td>
      <td className="num">
        {c.courses}
        {c.open_courses > 0 && (
          <span className="badge badge-warning" style={{ marginLeft: 4 }} title="Kurse ohne Lehrkraft">
            {c.open_courses} offen
          </span>
        )}
      </td>
      <td className="actions">
        {canEdit && !editing && (
          <span className="row" style={{ gap: 2, justifyContent: 'flex-end', flexWrap: 'nowrap' }}>
            <button type="button" className="btn btn-ghost btn-sm btn-icon" onClick={() => setEditing(true)} aria-label={`${c.name} umbenennen`} title="Umbenennen">
              <Icon name="edit" />
            </button>
            {onUnassign && (
              <AsyncButton className="btn btn-ghost btn-sm btn-icon" onClick={onUnassign} title="Aus dem Jahrgang lösen">
                <Icon name="x" />
                <span className="sr-only">{c.name} aus dem Jahrgang lösen</span>
              </AsyncButton>
            )}
            <button type="button" className="btn btn-ghost btn-sm btn-icon" onClick={onDelete} aria-label={`${c.name} löschen`} title="Löschen">
              <Icon name="trash" />
            </button>
          </span>
        )}
      </td>
    </tr>
  );
}

function ClassTable({ rows, caption, canEdit, onDelete, onUnassign }: { rows: GradeClassRow[]; caption: string; canEdit: boolean; onDelete: (ids: string[], title: string) => void; onUnassign?: (id: string) => Promise<void> }) {
  return (
    <div className="table-wrap">
      <table className="table table-compact">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr>
            <th scope="col">Klasse</th>
            <th scope="col" className="num">
              SuS
            </th>
            <th scope="col">Klassenleitung</th>
            <th scope="col">Stundentafel</th>
            <th scope="col" className="num">
              Kurse
            </th>
            <th scope="col">
              <span className="sr-only">Aktionen</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <ClassRow key={c.id} c={c} canEdit={canEdit} onDelete={() => onDelete([c.id], `Klasse ${c.name}`)} onUnassign={onUnassign ? () => onUnassign(c.id) : undefined} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ------------------------------------------------------------------ Karte eines Jahrgangs */
function ProfileCard({
  p,
  data,
  onEdit,
  onAssign,
  onAddClasses,
  onDelete,
  onDeleteClasses,
  onChanged,
}: {
  p: ProfileRow;
  data: ProfilesResponse;
  onEdit: () => void;
  onAssign: () => void;
  onAddClasses: () => void;
  onDelete: () => void;
  onDeleteClasses: (ids: string[], title: string) => void;
  onChanged: () => void;
}) {
  const toast = useToast();
  const baseName = p.curriculum_info?.base ? data.curricula.find((c) => c.id === p.curriculum_info?.base)?.name : null;
  const withoutTafel = p.classes.filter((c) => !c.curriculum_id && !c.curriculum_conflict);
  const unassign = async (id: string) => {
    await gradeLevelsApi.assign([id], null);
    invalidate('classes', 'grade_profiles');
    toast.success('Klasse aus dem Jahrgang gelöst');
    onChanged();
  };
  const meta = [p.grade !== null && p.grade !== undefined ? `Klassenstufe ${p.grade}` : null, p.department || null].filter(Boolean).join(' · ');
  return (
    <article className="jg-card" style={colorVars(p)} aria-label={`Jahrgang ${p.name}`}>
      <div className="jg-card-head">
        <div className="jg-title">
          <span className="jg-short" aria-hidden="true">
            {profileShort(p)}
          </span>
          <h3>{p.name}</h3>
          {meta && <span className="jg-meta">{meta}</span>}
        </div>
        {data.can_write && (
          <div className="jg-actions">
            <button type="button" className="btn btn-ghost btn-sm btn-icon" onClick={onEdit} aria-label={`${p.name} bearbeiten`} title="Bearbeiten">
              <Icon name="edit" />
            </button>
            <button type="button" className="btn btn-ghost btn-sm btn-icon" onClick={onDelete} aria-label={`${p.name} löschen`} title="Löschen">
              <Icon name="trash" />
            </button>
          </div>
        )}
      </div>
      {p.description && <p className="small muted" style={{ margin: 0 }}>{p.description}</p>}
      <div className="jg-facts">
        <div className="jg-fact">
          <span className="jg-fact-value">{p.classes.length}</span>
          <span className="jg-fact-label">{p.classes.length === 1 ? 'Klasse' : 'Klassen'}</span>
        </div>
        <div className="jg-fact">
          <span className="jg-fact-value">{p.students}</span>
          <span className="jg-fact-label">Schüler/innen</span>
        </div>
        <div className="jg-fact">
          <span className="jg-fact-value">{p.curriculum_info ? p.curriculum_info.hours : '–'}</span>
          <span className="jg-fact-label">Wochenstunden</span>
        </div>
      </div>
      <div className="jg-tafel">
        {p.curriculum_info ? (
          <>
            <span className="jg-tafel-name">{p.curriculum_info.name}</span>
            <span className="muted">{plural(p.curriculum_info.subjects, 'Fach', 'Fächer')}</span>
            {baseName && <span className="badge badge-info">abgeleitet von {baseName}</span>}
            <Link to={`/planung/stundentafeln?tafel=${encodeURIComponent(p.curriculum_info.id)}`} className="small">
              Stundentafel öffnen
            </Link>
          </>
        ) : (
          <>
            <span className="badge badge-warning">{p.curriculum_missing ? 'Stundentafel fehlt' : 'keine Stundentafel'}</span>
            {data.can_write && (
              <button type="button" className="btn btn-sm btn-ghost" onClick={onEdit}>
                Stundentafel wählen
              </button>
            )}
          </>
        )}
        {p.open_courses > 0 && <span className="badge badge-warning">{p.open_courses} Kurse ohne Lehrkraft</span>}
      </div>
      <div className="jg-classes" aria-label={`Klassen in ${p.name}`}>
        {p.classes.map((c) => (
          <Link key={c.id} to={`/klassen/${encodeURIComponent(c.id)}`} className={`jg-class${withoutTafel.includes(c) || c.curriculum_conflict ? ' warn' : ''}`}>
            {c.name}
            {c.curriculum_source === 'class' && <span className="xsmall muted">eigene Tafel</span>}
            {c.curriculum_conflict && <span className="xsmall error-text">Konflikt</span>}
          </Link>
        ))}
        {data.can_write && (
          <button type="button" className="jg-class jg-class-add" onClick={onAssign}>
            <Icon name="plus" /> Klasse zuordnen
          </button>
        )}
        {data.can_edit && (
          <button type="button" className="jg-class jg-class-add" onClick={onAddClasses}>
            <Icon name="plus" /> Neue Klassen
          </button>
        )}
      </div>
      {p.classes.length > 0 && (
        <details>
          <summary>Klassen verwalten</summary>
          <div style={{ marginTop: 8 }}>
            <ClassTable rows={p.classes} caption={`Klassen in ${p.name}`} canEdit={data.can_edit} onDelete={onDeleteClasses} onUnassign={data.can_write ? unassign : undefined} />
          </div>
        </details>
      )}
    </article>
  );
}

/* ------------------------------------------------------------------ Seite */
export function GradeLevelsView() {
  const q = useApi<ProfilesResponse>((signal) => gradeLevelsApi.profiles(signal), [], { live: ['grade_profiles', 'classes', 'students', 'courses', 'curricula'], keepPrevious: true });
  const toast = useToast();
  const [editing, setEditing] = useState<{ profile: ProfileRow | null; preset?: { grade: number | null; classIds: string[] } | null } | null>(null);
  const [assigning, setAssigning] = useState<ProfileRow | null>(null);
  const [adding, setAdding] = useState<{ profile: ProfileRow | null } | null>(null);
  const [deleting, setDeleting] = useState<ProfileRow | null>(null);
  const [deletingClasses, setDeletingClasses] = useState<{ ids: string[]; title: string } | null>(null);
  const [migrating, setMigrating] = useState(false);
  const [rebuild, setRebuild] = useState(false);
  const [assignTo, setAssignTo] = useState<{ classIds: string[]; profileId: string } | null>(null);

  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  const data = q.data;
  if (!data) return <Loading />;
  const done = () => {
    q.reload();
    setRebuild(true);
  };

  return (
    <div className="stack">
      <div className="jg-head">
        <h2>
          Jahrgänge{' '}
          <HelpTip label="Hilfe zu Jahrgängen">
            Ein Jahrgang ist frei definierbar – eine Klassenstufe wie „5“, ein Profil wie „5 Informatik“, ein Montessori-Zweig oder ein Bildungsgang wie „GIF 26“. Klassen gehören zu
            einem Jahrgang; der Jahrgang bestimmt ihre Stundentafel. Löschen und Umzüge sind über den Planverlauf rückgängig.
          </HelpTip>
        </h2>
        {data.can_write && (
          <button type="button" className="btn btn-primary" onClick={() => setEditing({ profile: null })}>
            <Icon name="plus" /> Jahrgang anlegen
          </button>
        )}
      </div>

      {data.migration.pending && data.can_write && (
        <Alert
          kind="info"
          title="Stundentafeln gelten noch über Klassenstufen-Nummern"
          action={
            <button type="button" className="btn btn-sm" onClick={() => setMigrating(true)}>
              Vorschau und Übernahme
            </button>
          }
        >
          {plural(data.migration.profiles, 'neuer Jahrgang', 'neue Jahrgänge')}, {plural(data.migration.classes, 'Klasse', 'Klassen')} zuzuordnen.
        </Alert>
      )}

      {rebuild && data.can_plan && (
        <Alert kind="info" title="Die Kurse ändern sich erst mit „Kurse erzeugen“">
          <div style={{ marginTop: 6 }}>
            <RebuildCourses className="btn btn-sm btn-primary" onDone={() => setRebuild(false)} />
          </div>
        </Alert>
      )}

      {data.profiles.length === 0 && !data.migration.pending && (
        <Empty title="Noch keine Jahrgänge" action={data.can_write ? <button type="button" className="btn btn-primary" onClick={() => setEditing({ profile: null })}>Jahrgang anlegen</button> : undefined}>
          Legen Sie den ersten Jahrgang an und ordnen Sie ihm Klassen zu.
        </Empty>
      )}

      <div className="jg-grid">
        {data.profiles.map((p) => (
          <ProfileCard
            key={p.id}
            p={p}
            data={data}
            onEdit={() => setEditing({ profile: p })}
            onAssign={() => setAssigning(p)}
            onAddClasses={() => setAdding({ profile: p })}
            onDelete={() => setDeleting(p)}
            onDeleteClasses={(ids, title) => setDeletingClasses({ ids, title })}
            onChanged={done}
          />
        ))}
      </div>

      {data.unassigned.length > 0 && (
        <section aria-label="Klassen ohne Jahrgang" className="stack-sm">
          <h2 className="jg-head" style={{ fontSize: 'var(--fs-md)' }}>
            Ohne Jahrgang
          </h2>
          {data.unassigned.map((u) => (
            <div key={u.grade} className="jg-unassigned">
              <div className="stack-sm" style={{ minWidth: 0 }}>
                <strong>Klassenstufe {u.grade}</strong>
                <div className="jg-classes">
                  {u.classes.map((c) => (
                    <Link key={c.id} to={`/klassen/${encodeURIComponent(c.id)}`} className={`jg-class${c.curriculum_id ? '' : ' warn'}`}>
                      {c.name}
                    </Link>
                  ))}
                </div>
              </div>
              {data.can_write && (
                <div className="row" style={{ gap: 6, flexWrap: 'wrap' }}>
                  {data.profiles.length > 0 && (
                    <>
                      <label htmlFor={`jg-to-${u.grade}`} className="sr-only">
                        Klassenstufe {u.grade} einem Jahrgang zuordnen
                      </label>
                      <select
                        id={`jg-to-${u.grade}`}
                        className="input-sm"
                        style={{ width: 'auto' }}
                        value={assignTo?.profileId && assignTo.classIds[0] === u.classes[0]?.id ? assignTo.profileId : ''}
                        onChange={(e) => setAssignTo(e.target.value ? { classIds: u.classes.map((c) => c.id), profileId: e.target.value } : null)}
                      >
                        <option value="">Jahrgang wählen …</option>
                        {data.profiles.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.name}
                          </option>
                        ))}
                      </select>
                    </>
                  )}
                  <button type="button" className="btn btn-sm" onClick={() => setEditing({ profile: null, preset: { grade: u.grade, classIds: u.classes.map((c) => c.id) } })}>
                    <Icon name="plus" /> Jahrgang daraus anlegen
                  </button>
                </div>
              )}
            </div>
          ))}
        </section>
      )}

      {editing && <ProfileDialog data={data} profile={editing.profile} preset={editing.preset} onClose={() => setEditing(null)} onDone={done} />}
      {assigning && <AssignClassesDialog data={data} profile={assigning} onClose={() => setAssigning(null)} onDone={done} />}
      {adding && <AddClassesDialog data={data} profile={adding.profile} onClose={() => setAdding(null)} onDone={q.reload} />}
      {deleting && <DeleteProfileDialog profile={deleting} onClose={() => setDeleting(null)} onDone={done} />}
      {deletingClasses && <DeleteClassesDialog title={deletingClasses.title} ids={deletingClasses.ids} data={data} onClose={() => setDeletingClasses(null)} onDone={q.reload} />}
      {migrating && <MigrationDialog onClose={() => setMigrating(false)} onDone={done} />}
      {assignTo && (
        <ConfirmDialog
          title="Klassen zuordnen"
          confirmLabel="Zuordnen"
          onCancel={() => setAssignTo(null)}
          onConfirm={async () => {
            await gradeLevelsApi.assign(assignTo.classIds, assignTo.profileId);
            invalidate('classes', 'grade_profiles');
            toast.success(`${plural(assignTo.classIds.length, 'Klasse', 'Klassen')} zugeordnet`);
            done();
          }}
        >
          <p style={{ margin: 0 }}>
            {plural(assignTo.classIds.length, 'Klasse', 'Klassen')} ({assignTo.classIds.join(', ')}) kommen in den Jahrgang „{data.profiles.find((p) => p.id === assignTo.profileId)?.name ?? assignTo.profileId}“. Die Kurse ändern sich erst mit „Kurse
            erzeugen“.
          </p>
        </ConfirmDialog>
      )}
    </div>
  );
}

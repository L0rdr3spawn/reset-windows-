/**
 * Planung → Stundentafeln: eine Matrix Fächer × Stundentafeln (Jahrgänge). Werte werden direkt in der Tabelle
 * bearbeitet, Summen je Zeile und Spalte, Soll (Tafel) gegen Ist (Kurse), Abweichungen abgeleiteter Tafeln zur Basis
 * farbig mit Vorzeichen. Am Handy eine Tafel als Liste. Entwürfe bleiben ohne Popup erhalten (sessionStorage) und
 * werden über die Leiste „Ungespeicherte Änderungen“ gespeichert oder verworfen; alle Rückfragen laufen über App-Dialoge.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { ApiError } from '../../api/client';
import { data as dataApi } from '../../api/endpoints';
import type { Curriculum, GradeProfile, RebuildResult } from '../../api/types';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { MultiSelect, type SelectOption } from '../../components/SearchSelect';
import { SubjectAdder } from '../../components/SubjectAdder';
import { Alert, Empty, ErrorBox, Field, Loading } from '../../components/ui';
import { UnsavedBar } from '../../components/UnsavedChanges';
import { useUser } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { gradeLevelsApi } from '../../features/gradeLevels/api';
import { profileColor } from '../../features/gradeLevels/logic';
import type { CurriculumImpact, MatrixResponse, SubjectImpact } from '../../features/gradeLevels/types';
import { useApi } from '../../hooks/useApi';
import { useMediaQuery } from '../../hooks/misc';
import { invalidate, useCollection, useSettings } from '../../hooks/useCollection';
import { confirmAsk } from '../../lib/confirm';
import { plural } from '../../lib/format';
import { can } from '../../lib/permissions';
import { schoolDaysOf } from '../../lib/weeks';
import { curriculumOrder, deviation, effectiveEntries, matrixSubjects, resolveCurricula, setEffectiveHours, weeklyCapacity } from './curricula';
import './curricula.css';
import { RebuildCourses, RebuildResultView } from './RebuildCourses';

const DRAFT_KEY = 'sm-stundentafeln-entwurf';
const NEW_PREFIX = '__neu_';

type Drafts = Record<string, Curriculum>;

function loadDrafts(): Drafts {
  try {
    const raw = window.sessionStorage.getItem(DRAFT_KEY);
    return raw ? (JSON.parse(raw) as Drafts) : {};
  } catch {
    return {};
  }
}
function storeDrafts(d: Drafts): void {
  try {
    if (Object.keys(d).length) window.sessionStorage.setItem(DRAFT_KEY, JSON.stringify(d));
    else window.sessionStorage.removeItem(DRAFT_KEY);
  } catch {
    /* ohne Speicher weiterarbeiten */
  }
}

/* ------------------------------------------------------------------ Stundentafel (Spalte) anlegen/bearbeiten */
function ColumnDialog({
  cur,
  all,
  profiles,
  canEdit,
  onClose,
  onSave,
  onDelete,
}: {
  /** null = neue Stundentafel */
  cur: Curriculum | null;
  all: readonly Curriculum[];
  profiles: readonly GradeProfile[];
  canEdit: boolean;
  onClose: () => void;
  onSave: (next: Curriculum, profileIds: string[] | null) => void;
  onDelete: () => void;
}) {
  const classes = useCollection('classes');
  const [name, setName] = useState(cur?.name ?? '');
  const [base, setBase] = useState(cur?.base ?? '');
  const [copyFrom, setCopyFrom] = useState('');
  const [classIds, setClassIds] = useState<string[]>(cur?.classes ?? []);
  const [profileIds, setProfileIds] = useState<string[]>(profiles.filter((p) => p.curriculum === cur?.id).map((p) => p.id));
  const isNew = !cur;
  const others = all.filter((c) => c.id !== cur?.id && !c.id.startsWith(NEW_PREFIX));
  const classOptions: SelectOption[] = useMemo(
    () => (classes.data ?? []).slice().sort((a, b) => a.grade - b.grade || a.name.localeCompare(b.name, 'de', { numeric: true })).map((c) => ({ value: c.id, label: c.name, sub: `Stufe ${c.grade}` })),
    [classes.data],
  );
  const profileOptions: SelectOption[] = profiles.map((p) => ({ value: p.id, label: p.name, sub: p.curriculum && p.curriculum !== cur?.id ? `zurzeit ${all.find((c) => c.id === p.curriculum)?.name ?? p.curriculum}` : undefined }));
  const ok = !!name.trim();

  const save = () => {
    const src = copyFrom ? all.find((c) => c.id === copyFrom) : null;
    const next: Curriculum = cur
      ? { ...cur, name: name.trim(), base: base || null, classes: classIds, deltas: base ? (cur.base === base ? cur.deltas ?? [] : []) : [] }
      : { id: `${NEW_PREFIX}${Date.now()}`, name: name.trim(), grades: [], classes: classIds, entries: src ? effectiveEntries(all, src).map((e) => ({ ...e })) : [], base: base || null, deltas: [] };
    if (!cur && base) next.entries = [];
    if (cur && !cur.base && base) next.entries = [];
    if (cur && cur.base && !base) next.entries = effectiveEntries(all, cur);
    onSave(next, cur ? profileIds : null);
    onClose();
  };

  return (
    <Modal
      title={isNew ? 'Neue Stundentafel' : `Stundentafel „${cur.name}“`}
      onClose={onClose}
      footer={
        <>
          {!isNew && canEdit && !cur.id.startsWith(NEW_PREFIX) && (
            <button type="button" className="btn btn-ghost" onClick={onDelete} style={{ marginRight: 'auto' }}>
              <Icon name="trash" /> Löschen
            </button>
          )}
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          {canEdit && (
            <button type="button" className="btn btn-primary" disabled={!ok} onClick={save}>
              {isNew ? 'Anlegen' : 'Übernehmen'}
            </button>
          )}
        </>
      }
    >
      <form
        className="form-grid"
        onSubmit={(e) => {
          e.preventDefault();
          if (ok && canEdit) save();
        }}
      >
        <Field label="Name" htmlFor="ce-name" className="span-all">
          <input id="ce-name" type="text" maxLength={120} value={name} disabled={!canEdit} onChange={(e) => setName(e.target.value)} autoFocus required />
        </Field>
        <Field
          label="Abgeleitet von"
          htmlFor="ce-base"
          help="Wie die Basis, plus eigene Abweichungen je Fach („plus 2 Std. Informatik, minus 1 Std. Kunst“). Änderungen an der Basis wirken weiter. Ohne Basis ist die Tafel eigenständig; beim Lösen der Basis werden die aktuellen Werte übernommen."
        >
          <select id="ce-base" value={base} disabled={!canEdit} onChange={(e) => setBase(e.target.value)}>
            <option value="">– eigenständig –</option>
            {others.map((c) => (
              <option key={c.id} value={c.id} disabled={c.base === cur?.id}>
                {c.name}
              </option>
            ))}
          </select>
        </Field>
        {isNew && !base && others.length > 0 && (
          <Field label="Start mit Kopie von" htmlFor="ce-copy" help="Die Fächer und Stunden einer vorhandenen Tafel als Ausgangspunkt übernehmen – danach unabhängig.">
            <select id="ce-copy" value={copyFrom} onChange={(e) => setCopyFrom(e.target.value)}>
              <option value="">leer</option>
              {others.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </Field>
        )}
        <div className="span-all stack-sm">
          <span className="field-label">
            Gilt für{' '}
            <HelpTip label="Hilfe zur Gültigkeit">
              Die Tafel gilt für die Klassen ihrer Jahrgänge. Einzelne Klassen (Sonderfall) haben Vorrang vor dem Jahrgang, z. B. eine Praxisklasse. Jahrgänge verwalten Sie unter
              Stammdaten → Jahrgänge.
            </HelpTip>
          </span>
          {isNew ? (
            <span className="small muted">Jahrgänge nach dem Speichern zuordnen.</span>
          ) : canEdit ? (
            <MultiSelect label="Jahrgänge" options={profileOptions} values={profileIds} onChange={setProfileIds} placeholder="Jahrgang suchen …" />
          ) : (
            <span className="small">{profileIds.map((id) => profiles.find((p) => p.id === id)?.name ?? id).join(', ') || '–'}</span>
          )}
          <Link to="/stammdaten/klassenstufen" className="small">
            Jahrgänge verwalten
          </Link>
          {canEdit ? (
            <MultiSelect label="Einzelne Klassen (Sonderfall)" options={classOptions} values={classIds} onChange={setClassIds} placeholder="Klasse suchen …" />
          ) : (
            classIds.length > 0 && <span className="small">Einzelne Klassen: {classIds.join(', ')}</span>
          )}
        </div>
      </form>
    </Modal>
  );
}

/* ------------------------------------------------------------------ Stundentafel löschen (mit Folgen) */
function DeleteCurriculumDialog({ cur, onClose, onDone }: { cur: Curriculum; onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const impact = useApi<CurriculumImpact>((signal) => gradeLevelsApi.curriculumImpact(cur.id, signal), [cur.id]);
  const imp = impact.data;
  return (
    <ConfirmDialog
      title="Stundentafel löschen?"
      confirmLabel="Stundentafel löschen"
      danger
      onCancel={onClose}
      onConfirm={async () => {
        await dataApi.remove('curricula', cur.id, true);
        invalidate('curricula', 'grade_profiles');
        toast.success(`Stundentafel „${cur.name}“ gelöscht`);
        onDone();
      }}
    >
      <p style={{ margin: 0 }}>
        <strong>{cur.name}</strong> wird gelöscht. Rückgängig über den Planverlauf.
      </p>
      {impact.error ? <ErrorBox error={impact.error} onRetry={impact.reload} /> : !imp ? <Loading /> : null}
      {imp && (
        <ul className="small" aria-label="Folgen des Löschens" style={{ margin: 0 }}>
          {imp.profiles.length > 0 && (
            <li>
              {plural(imp.profiles.length, 'Jahrgang', 'Jahrgänge')} ohne Stundentafel: {imp.profiles.map((p) => p.name).join(', ')}
            </li>
          )}
          {imp.classes.length > 0 && (
            <li className="error-text">
              <strong>
                {plural(imp.classes.length, 'Klasse', 'Klassen')} ohne Stundentafel ({imp.classes.map((c) => c.name).join(', ')})
                {imp.courses ? `; ${plural(imp.courses, 'Kurs', 'Kurse')}${imp.lessons ? ` mit ${plural(imp.lessons, 'Stunde', 'Stunden')} im Plan` : ''} entfallen beim nächsten „Kurse erzeugen“` : ''}
              </strong>
            </li>
          )}
          {imp.derived.length > 0 && (
            <li>
              {plural(imp.derived.length, 'abgeleitete Tafel wird', 'abgeleitete Tafeln werden')} eigenständig: {imp.derived.map((d) => d.name).join(', ')}
            </li>
          )}
          {imp.profiles.length === 0 && imp.classes.length === 0 && imp.derived.length === 0 && <li>Keine Jahrgänge, Klassen oder Kurse betroffen.</li>}
        </ul>
      )}
    </ConfirmDialog>
  );
}

/* ------------------------------------------------------------------ Fach löschen (mit Folgen) */
function DeleteSubjectDialog({ id, name, onClose, onDone }: { id: string; name: string; onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const impact = useApi<SubjectImpact>((signal) => gradeLevelsApi.subjectImpact(id, signal), [id]);
  const imp = impact.data;
  return (
    <ConfirmDialog
      title="Fach löschen?"
      confirmLabel="Fach löschen"
      danger
      onCancel={onClose}
      onConfirm={async () => {
        await dataApi.remove('subjects', id, true);
        invalidate('subjects', 'curricula', 'courses');
        toast.success(`Fach „${name}“ gelöscht`);
        onDone();
      }}
    >
      <p style={{ margin: 0 }}>
        <strong>
          {name} ({id})
        </strong>{' '}
        wird aus allen Stammdaten entfernt. Rückgängig über den Planverlauf.
      </p>
      {impact.error ? <ErrorBox error={impact.error} onRetry={impact.reload} /> : !imp ? <Loading /> : null}
      {imp && (
        <ul className="small" aria-label="Folgen des Löschens" style={{ margin: 0 }}>
          {imp.curricula.length > 0 && <li>Aus {plural(imp.curricula.length, 'Stundentafel', 'Stundentafeln')} gestrichen: {imp.curricula.map((c) => c.name).join(', ')}</li>}
          {imp.courses > 0 && (
            <li className="error-text">
              <strong>
                {plural(imp.courses, 'Kurs', 'Kurse')}
                {imp.lessons ? ` mit ${plural(imp.lessons, 'Stunde', 'Stunden')} im Plan` : ''} werden gelöscht
              </strong>
            </li>
          )}
          {imp.exams > 0 && <li className="error-text">{plural(imp.exams, 'Klausur', 'Klausuren')} werden gelöscht</li>}
          {imp.teachers > 0 && <li>{plural(imp.teachers, 'Lehrkraft verliert', 'Lehrkräfte verlieren')} das Fach</li>}
          {imp.courses === 0 && imp.curricula.length === 0 && imp.teachers === 0 && <li>Keine Kurse, Stundentafeln oder Lehrkräfte betroffen.</li>}
        </ul>
      )}
    </ConfirmDialog>
  );
}

/* ------------------------------------------------------------------ Zelle */
function Cell({
  id,
  value,
  double,
  dev,
  canEdit,
  onChange,
  onToggleDouble,
  label,
}: {
  id: string;
  value: number;
  double: boolean;
  dev: { base: number; delta: number } | null;
  canEdit: boolean;
  onChange: (hours: number) => void;
  onToggleDouble: () => void;
  label: string;
}) {
  const mark = dev ? (dev.delta > 0 ? `+${dev.delta}` : `−${-dev.delta}`) : '';
  const title = dev ? `Basis: ${dev.base} Std.` : undefined;
  if (!canEdit) {
    return (
      <span className="ce-cell" title={title}>
        <span className="ce-static">{value || '–'}</span>
        {dev && <span className="ce-dev-mark">{mark}</span>}
      </span>
    );
  }
  return (
    <span className="ce-cell" title={title}>
      <input
        id={id}
        type="number"
        inputMode="numeric"
        min={0}
        max={40}
        className="input-sm"
        aria-label={label}
        placeholder="–"
        value={value || ''}
        onChange={(e) => onChange(Math.min(40, Math.max(0, parseInt(e.target.value || '0', 10) || 0)))}
      />
      {value > 0 ? (
        <button type="button" className="ce-dbl" aria-pressed={double} aria-label={`${label}: Doppelstunde`} title={double ? 'Doppelstunde bevorzugt' : 'Einzelstunden'} onClick={onToggleDouble}>
          2er
        </button>
      ) : (
        <span className="ce-dbl" aria-hidden="true" />
      )}
      {dev && <span className="ce-dev-mark">{mark}</span>}
    </span>
  );
}

/* ------------------------------------------------------------------ Editor */
export function CurriculaEditor({ canEdit }: { canEdit: boolean }) {
  const toast = useToast();
  const navigate = useNavigate();
  const user = useUser();
  const canSubjects = can(user, 'masterdata.edit');
  const curricula = useCollection('curricula');
  const subjects = useCollection('subjects');
  const classes = useCollection('classes');
  const profilesCol = useCollection('grade_profiles');
  const matrix = useApi<MatrixResponse>((signal) => gradeLevelsApi.matrix(signal), [], { live: ['courses', 'curricula', 'classes', 'grade_profiles'], keepPrevious: true });
  const { data: settings } = useSettings();
  const capacity = weeklyCapacity(settings?.periods ?? 0, schoolDaysOf(settings).length);
  const mobile = useMediaQuery('(max-width: 699.98px)');
  const [params, setParams] = useSearchParams();

  const [drafts, setDrafts] = useState<Drafts>(loadDrafts);
  const [filter, setFilter] = useState('');
  const [extraRows, setExtraRows] = useState<string[]>([]);
  const [column, setColumn] = useState<{ cur: Curriculum | null } | null>(null);
  const [deleting, setDeleting] = useState<Curriculum | null>(null);
  const [deletingSubject, setDeletingSubject] = useState<{ id: string; name: string } | null>(null);
  const [saved, setSaved] = useState(false);
  const [rebuilt, setRebuilt] = useState<RebuildResult | null>(null);
  const [focusCell, setFocusCell] = useState<string | null>(null);
  const tableRef = useRef<HTMLDivElement>(null);

  useEffect(() => storeDrafts(drafts), [drafts]);
  // Spalte aus der Adresse (?tafel=…) einmal ins Bild holen
  const scrolledTo = useRef<string | null>(null);
  useEffect(() => {
    const id = params.get('tafel');
    if (!id || !curricula.data || scrolledTo.current === id) return;
    const th = tableRef.current?.querySelector<HTMLElement>('th.ce-focus');
    if (!th) return;
    scrolledTo.current = id;
    th.scrollIntoView({ block: 'nearest', inline: 'center' });
  }, [params, curricula.data]);
  useEffect(() => {
    if (!focusCell) return;
    tableRef.current?.querySelector<HTMLInputElement>(`#${focusCell}`)?.focus();
    setFocusCell(null);
  }, [focusCell]);

  const profiles = useMemo(() => profilesCol.data ?? [], [profilesCol.data]);
  const classList = useMemo(() => classes.data ?? [], [classes.data]);
  const subjectList = useMemo(() => (subjects.data ?? []).slice().sort((a, b) => a.name.localeCompare(b.name, 'de')), [subjects.data]);

  // Server-Stand + Entwürfe (Entwürfe zu gelöschten Tafeln fallen weg)
  const all = useMemo<Curriculum[]>(() => {
    const server = curricula.data ?? [];
    const merged = server.map((c) => drafts[c.id] ?? c);
    const fresh = Object.values(drafts).filter((d) => d.id.startsWith(NEW_PREFIX));
    return curriculumOrder([...merged, ...fresh], profiles);
  }, [curricula.data, drafts, profiles]);
  const dirtyIds = useMemo(() => Object.keys(drafts).filter((id) => id.startsWith(NEW_PREFIX) || (curricula.data ?? []).some((c) => c.id === id)), [drafts, curricula.data]);
  const dirty = dirtyIds.length > 0;

  const res = useMemo(() => resolveCurricula(all, classList, profiles), [all, classList, profiles]);
  const appliesTo = (id: string) => classList.filter((c) => res[c.id]?.curriculum === id);
  const conflictsOf = (id: string) => classList.filter((c) => res[c.id]?.conflict && res[c.id]?.candidates.includes(id));
  const withoutTafel = classList.filter((c) => res[c.id]?.source === null);
  const ist = useMemo(() => new Map((matrix.data?.curricula ?? []).map((c) => [c.id, c])), [matrix.data]);

  const rows = useMemo(() => {
    const base = matrixSubjects(all, subjectList);
    const withExtra = [...base, ...extraRows.filter((s) => !base.includes(s))];
    const name = (id: string) => subjectList.find((s) => s.id === id)?.name ?? id;
    const q = filter.trim().toLowerCase();
    return withExtra.filter((id) => !q || id.toLowerCase().includes(q) || name(id).toLowerCase().includes(q));
  }, [all, subjectList, extraRows, filter]);

  const focusId = params.get('tafel');
  const [mobileCol, setMobileCol] = useState<string>(focusId ?? '');
  useEffect(() => {
    if (focusId) setMobileCol(focusId);
  }, [focusId]);
  const mobileCur = all.find((c) => c.id === mobileCol) ?? all[0];

  const subjName = (id: string) => subjectList.find((s) => s.id === id)?.name ?? '';
  const known = (id: string) => subjectList.some((s) => s.id === id);
  const hoursOf = (cur: Curriculum, subject: string) => effectiveEntries(all, cur).find((e) => e.subject === subject);
  const colSum = (cur: Curriculum) => effectiveEntries(all, cur).reduce((a, e) => a + e.hours, 0);
  const rowSum = (subject: string) => all.reduce((a, c) => a + (hoursOf(c, subject)?.hours ?? 0), 0);
  const profilesOf = (id: string) => profiles.filter((p) => p.curriculum === id);
  const baseName = (cur: Curriculum) => (cur.base ? all.find((c) => c.id === cur.base)?.name ?? cur.base : null);

  const setDraft = (next: Curriculum) => {
    setDrafts((d) => ({ ...d, [next.id]: next }));
    setSaved(false);
  };
  const setCell = (cur: Curriculum, subject: string, hours: number) => setDraft(setEffectiveHours(all, cur, subject, hours));
  const toggleDouble = (cur: Curriculum, subject: string) => {
    const e = hoursOf(cur, subject);
    if (!e) return;
    setDraft(setEffectiveHours(all, cur, subject, e.hours, !e.double));
  };
  const addRow = (subject: string) => {
    setExtraRows((r) => (r.includes(subject) ? r : [...r, subject]));
    setFilter('');
    const first = mobile ? mobileCur : all[0];
    if (first) setFocusCell(cellId(first.id, subject));
  };
  const clearRow = (subject: string) => {
    setDrafts((d) => {
      const next = { ...d };
      for (const c of all) if (hoursOf(c, subject)) next[c.id] = setEffectiveHours(all, d[c.id] ?? c, subject, 0);
      return next;
    });
    setExtraRows((r) => r.filter((s) => s !== subject));
  };
  const discard = () => {
    setDrafts({});
    setExtraRows([]);
  };

  const save = async () => {
    const list = dirtyIds.map((id) => drafts[id]).filter((c): c is Curriculum => !!c);
    const sendOne = async (c: Curriculum, force: boolean): Promise<Curriculum> => {
      const body: Partial<Curriculum> = { name: c.name.trim() || 'Stundentafel', grades: c.grades, classes: c.classes, entries: c.entries.filter((e) => e.subject), base: c.base ?? null, deltas: (c.deltas ?? []).filter((e) => e.subject) };
      if (c.id.startsWith(NEW_PREFIX)) return dataApi.create('curricula', body, force);
      return dataApi.update('curricula', c.id, body, force);
    };
    let n = 0;
    try {
      for (const c of list) {
        try {
          await sendOne(c, false);
        } catch (e) {
          if (!(e instanceof ApiError && e.isConflict)) throw e;
          const ok = await confirmAsk({
            title: `„${c.name}“: Überschneidung`,
            message: `${e.message}:\n${e.conflicts.slice(0, 12).join('\n')}\n\nTrotzdem speichern? Für diese Klassen werden keine Kurse erzeugt, bis die Überschneidung behoben ist.`,
            confirmLabel: 'Trotzdem speichern',
          });
          if (!ok) continue;
          await sendOne(c, true);
        }
        n += 1;
        setDrafts((d) => {
          const next = { ...d };
          delete next[c.id];
          return next;
        });
      }
    } catch (e) {
      toast.error(e, 'Speichern');
    } finally {
      invalidate('curricula');
      matrix.reload();
    }
    if (n) {
      toast.success(`${plural(n, 'Stundentafel', 'Stundentafeln')} gespeichert`);
      setSaved(true);
      setExtraRows([]);
    }
  };

  const saveColumn = async (next: Curriculum, profileIds: string[] | null) => {
    setDraft(next);
    if (profileIds && !next.id.startsWith(NEW_PREFIX)) {
      const before = profiles.filter((p) => p.curriculum === next.id).map((p) => p.id);
      const added = profileIds.filter((id) => !before.includes(id));
      const removed = before.filter((id) => !profileIds.includes(id));
      try {
        for (const id of added) await dataApi.update('grade_profiles', id, { curriculum: next.id });
        for (const id of removed) await dataApi.update('grade_profiles', id, { curriculum: null });
        if (added.length || removed.length) {
          invalidate('grade_profiles');
          toast.success('Jahrgänge zugeordnet');
        }
      } catch (e) {
        toast.error(e, 'Jahrgänge');
      }
    }
    if (!mobile) setParams({ tafel: next.id }, { replace: true });
    else setMobileCol(next.id);
  };

  if (curricula.error) return <ErrorBox error={curricula.error} onRetry={curricula.reload} />;
  if (!curricula.data || !subjects.data) return <Loading />;

  const header = (
    <div className="ce-toolbar">
      <div className="row" style={{ gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <h2 style={{ margin: 0, fontSize: 'var(--fs-lg)' }}>
          Stundentafeln{' '}
          <HelpTip label="Hilfe zu Stundentafeln">
            Zeilen sind Fächer, Spalten Stundentafeln mit ihren Jahrgängen; die Zahl ist die Wochenstundenzahl. Abgeleitete Tafeln zeigen Abweichungen zur Basis farbig mit Vorzeichen.
            Unten steht das Soll der Tafel neben dem Ist aus den vorhandenen Kursen je Klasse. Kurse ändern sich erst mit „Kurse erzeugen“.
          </HelpTip>
        </h2>
        <div className="field">
          <label htmlFor="ce-filter" className="sr-only">
            Fächer filtern
          </label>
          <input id="ce-filter" type="search" className="input-sm" placeholder="Fach filtern …" value={filter} onChange={(e) => setFilter(e.target.value)} />
        </div>
      </div>
      <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
        {withoutTafel.length > 0 && (
          <Link to="/stammdaten/klassenstufen" className="badge badge-warning" title={withoutTafel.map((c) => c.name).join(', ')}>
            {plural(withoutTafel.length, 'Klasse', 'Klassen')} ohne Stundentafel
          </Link>
        )}
        {canEdit && (
          <button type="button" className="btn btn-sm" onClick={() => setColumn({ cur: null })}>
            <Icon name="plus" /> Stundentafel
          </button>
        )}
      </div>
    </div>
  );

  const colHead = (cur: Curriculum, focused: boolean) => {
    const ps = profilesOf(cur.id);
    const n = appliesTo(cur.id).length;
    const k = conflictsOf(cur.id).length;
    const bn = baseName(cur);
    return (
      <div className="ce-col-head">
        <button type="button" className="ce-col-name" onClick={() => setColumn({ cur })} aria-label={`Stundentafel ${cur.name} bearbeiten`} aria-current={focused || undefined}>
          {cur.name}
          {cur.id.startsWith(NEW_PREFIX) && <span className="xsmall muted"> · neu</span>}
        </button>
        <div className="ce-col-tags">
          {ps.map((p) => (
            <span key={p.id} className="ce-tag" style={{ '--ce-dot': profileColor(p) } as React.CSSProperties} title={p.name}>
              <span className="ce-dot" aria-hidden="true" />
              {p.short || p.name}
            </span>
          ))}
          {cur.classes.length > 0 && <span className="ce-tag">{cur.classes.length <= 3 ? cur.classes.join(', ') : plural(cur.classes.length, 'Klasse', 'Klassen')}</span>}
          {cur.grades.length > 0 && <span className="ce-tag">Stufe {cur.grades.join(', ')}</span>}
          {k > 0 ? <span className="badge badge-danger">{k} Konflikt{k === 1 ? '' : 'e'}</span> : n === 0 ? <span className="badge badge-warning">keine Klasse</span> : <span>{n} Kl.</span>}
          {bn && (
            <span className="ce-tag" title={`abgeleitet von ${bn}`}>
              <Icon name="link" /> {bn}
            </span>
          )}
        </div>
      </div>
    );
  };

  const istCell = (cur: Curriculum) => {
    const m = ist.get(cur.id);
    const soll = colSum(cur);
    if (!m || !m.applies.length) return <span className="muted">–</span>;
    const diff = Math.round((m.actual_hours - soll) * 10) / 10;
    return (
      <span className={`ce-ist ${diff === 0 ? 'good' : Math.abs(diff) >= 1 ? 'bad' : ''}`} title={`Ist aus den Stundentafel-Kursen je Klasse (Mittel), Soll ${soll}`}>
        {m.actual_hours}
        {diff !== 0 && <span className="xsmall"> ({diff > 0 ? '+' : ''}{diff})</span>}
      </span>
    );
  };

  const dialogs = (
    <>
      {column && (
        <ColumnDialog
          cur={column.cur}
          all={all}
          profiles={profiles}
          canEdit={canEdit}
          onClose={() => setColumn(null)}
          onSave={(next, pids) => void saveColumn(next, pids)}
          onDelete={() => {
            if (column.cur) setDeleting(column.cur);
            setColumn(null);
          }}
        />
      )}
      {deleting && (
        <DeleteCurriculumDialog
          cur={deleting}
          onClose={() => setDeleting(null)}
          onDone={() => {
            setDrafts((d) => {
              const next = { ...d };
              delete next[deleting.id];
              return next;
            });
            setDeleting(null);
          }}
        />
      )}
      {deletingSubject && <DeleteSubjectDialog id={deletingSubject.id} name={deletingSubject.name} onClose={() => setDeletingSubject(null)} onDone={() => setDeletingSubject(null)} />}
    </>
  );

  const after = (
    <>
      {canEdit && saved && !dirty && (
        <Alert kind="info" title="Gespeichert – Kurse ändern sich erst mit „Kurse erzeugen“">
          <div className="row" style={{ flexWrap: 'wrap', gap: 8, marginTop: 6 }}>
            <RebuildCourses
              className="btn btn-sm btn-primary"
              onDone={(r) => {
                setRebuilt(r);
                if (r) setSaved(false);
              }}
            />
          </div>
        </Alert>
      )}
      {canEdit && rebuilt && <RebuildResultView result={rebuilt} onReplan={() => navigate('/planung/generator')} replanLabel="Zum Generator" />}
    </>
  );

  if (all.length === 0) {
    return (
      <div className="stack">
        {header}
        <Empty title="Noch keine Stundentafel">{canEdit ? 'Legen Sie die erste Stundentafel an und ordnen Sie ihr unter Stammdaten → Jahrgänge einen Jahrgang zu.' : 'Es gibt noch keine Stundentafeln.'}</Empty>
        {dialogs}
      </div>
    );
  }

  // ---------------------------------------------------------------- Handy: eine Tafel als Liste
  if (mobile) {
    const cur = mobileCur as Curriculum;
    const sum = colSum(cur);
    return (
      <div className="stack">
        {dirty && canEdit && (
          <div className="ce-save">
            <UnsavedBar onSave={save} onDiscard={discard}>
              {plural(dirtyIds.length, 'Stundentafel', 'Stundentafeln')} geändert
            </UnsavedBar>
          </div>
        )}
        {header}
        <div className="row" style={{ gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <label htmlFor="ce-mobile-col" className="sr-only">
            Stundentafel wählen
          </label>
          <select id="ce-mobile-col" value={cur.id} onChange={(e) => setMobileCol(e.target.value)} style={{ flex: 1 }}>
            {all.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
                {drafts[c.id] ? ' *' : ''}
              </option>
            ))}
          </select>
          <button type="button" className="btn btn-sm btn-icon" onClick={() => setColumn({ cur })} aria-label={`Stundentafel ${cur.name} bearbeiten`}>
            <Icon name="edit" />
          </button>
        </div>
        <div className="ce-col-tags" style={{ justifyContent: 'flex-start', maxWidth: 'none' }}>
          {profilesOf(cur.id).map((p) => (
            <span key={p.id} className="ce-tag" style={{ '--ce-dot': profileColor(p) } as React.CSSProperties}>
              <span className="ce-dot" aria-hidden="true" />
              {p.name}
            </span>
          ))}
          {baseName(cur) && (
            <span className="ce-tag">
              <Icon name="link" /> abgeleitet von {baseName(cur)}
            </span>
          )}
          <span>{plural(appliesTo(cur.id).length, 'Klasse', 'Klassen')}</span>
        </div>
        <ul className="ce-list" aria-label={`Fächer der Stundentafel ${cur.name}`}>
          {rows.map((subject) => {
            const e = hoursOf(cur, subject);
            const dev = deviation(all, cur, subject);
            if (!e && !canEdit && !dev) return null;
            return (
              <li key={subject} className={dev ? 'ce-dev' : undefined}>
                <span>
                  <strong>{subject}</strong>
                  {subjName(subject) && <span className="muted"> {subjName(subject)}</span>}
                  {!known(subject) && <span className="ce-unknown xsmall"> fehlt in den Fächern</span>}
                </span>
                <Cell
                  id={cellId(cur.id, subject)}
                  value={e?.hours ?? 0}
                  double={!!e?.double}
                  dev={dev}
                  canEdit={canEdit}
                  onChange={(h) => setCell(cur, subject, h)}
                  onToggleDouble={() => toggleDouble(cur, subject)}
                  label={`${subjName(subject) || subject}, ${cur.name}`}
                />
              </li>
            );
          })}
        </ul>
        <div className="ce-list-sum">
          <span>Summe</span>
          <span>
            {sum} Std.
            {capacity > 0 && sum > capacity && <span className="error-text"> (Raster: {capacity})</span>}
          </span>
        </div>
        {canEdit && <SubjectAdder options={subjectList.filter((s) => !hoursOf(cur, s.id))} onPick={addRow} canCreate={canSubjects} />}
        {after}
        {dialogs}
      </div>
    );
  }

  // ---------------------------------------------------------------- Matrix
  return (
    <div className="stack">
      {dirty && canEdit && (
        <div className="ce-save">
          <UnsavedBar onSave={save} onDiscard={discard}>
            {plural(dirtyIds.length, 'Stundentafel', 'Stundentafeln')} geändert
          </UnsavedBar>
        </div>
      )}
      {header}
      <div className="ce-wrap" ref={tableRef}>
        <table className="ce-matrix">
          <caption className="sr-only">Stundentafeln: Wochenstunden je Fach und Stundentafel</caption>
          <thead>
            <tr>
              <th scope="col" className="ce-subject">
                Fach
              </th>
              {all.map((c) => (
                <th key={c.id} scope="col" className={`ce-col${c.id === focusId ? ' ce-focus' : ''}`}>
                  {colHead(c, c.id === focusId)}
                </th>
              ))}
              <th scope="col" className="ce-sum">
                Σ
              </th>
              {canEdit && (
                <th scope="col" className="ce-row-actions">
                  <span className="sr-only">Aktionen</span>
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {rows.map((subject) => (
              <tr key={subject}>
                <th scope="row" className="ce-subject">
                  <span>
                    <strong>{subject}</strong>
                    {subjName(subject) && <span className="muted small"> {subjName(subject)}</span>}
                    {!known(subject) && <span className="ce-unknown xsmall"> fehlt in den Fächern</span>}
                  </span>
                </th>
                {all.map((c) => {
                  const e = hoursOf(c, subject);
                  const dev = deviation(all, c, subject);
                  return (
                    <td key={c.id} className={`ce-col${dev ? ' ce-dev' : ''}${c.id === focusId ? ' ce-focus' : ''}`}>
                      <Cell
                        id={cellId(c.id, subject)}
                        value={e?.hours ?? 0}
                        double={!!e?.double}
                        dev={dev}
                        canEdit={canEdit}
                        onChange={(h) => setCell(c, subject, h)}
                        onToggleDouble={() => toggleDouble(c, subject)}
                        label={`${subjName(subject) || subject}, ${c.name}`}
                      />
                    </td>
                  );
                })}
                <td className="ce-sum">{rowSum(subject) || ''}</td>
                {canEdit && (
                  <td className="ce-row-actions">
                    <span className="row" style={{ gap: 2, flexWrap: 'nowrap', justifyContent: 'flex-end' }}>
                      <button type="button" className="btn btn-ghost btn-sm btn-icon" onClick={() => clearRow(subject)} aria-label={`${subjName(subject) || subject} aus allen Stundentafeln entfernen`} title="Aus allen Tafeln entfernen">
                        <Icon name="x" />
                      </button>
                      {canSubjects && known(subject) && (
                        <button type="button" className="btn btn-ghost btn-sm btn-icon" onClick={() => setDeletingSubject({ id: subject, name: subjName(subject) })} aria-label={`Fach ${subjName(subject) || subject} löschen`} title="Fach löschen">
                          <Icon name="trash" />
                        </button>
                      )}
                    </span>
                  </td>
                )}
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={all.length + 2 + (canEdit ? 1 : 0)} className="muted">
                  {filter ? 'Kein Fach passt zum Filter.' : 'Noch keine Fächer – unten „Fach hinzufügen“.'}
                </td>
              </tr>
            )}
          </tbody>
          <tfoot>
            <tr>
              <td className="ce-subject">Soll (Wochenstunden)</td>
              {all.map((c) => {
                const sum = colSum(c);
                return (
                  <td key={c.id} className={`ce-col${c.id === focusId ? ' ce-focus' : ''}`}>
                    <span className={capacity > 0 && sum > capacity ? 'error-text' : undefined} title={capacity > 0 && sum > capacity ? `mehr als die ${capacity} Wochenstunden des Rasters` : undefined}>
                      {sum}
                    </span>
                  </td>
                );
              })}
              <td className="ce-sum">{all.reduce((a, c) => a + colSum(c), 0)}</td>
              {canEdit && <td className="ce-row-actions" />}
            </tr>
            <tr>
              <td className="ce-subject">
                Ist (Kurse je Klasse){' '}
                <HelpTip label="Hilfe zu Soll und Ist">
                  Ist zählt die Wochenstunden der aus der Tafel erzeugten Kurse je Klasse, im Mittel über die Klassen der Tafel. Abweichungen vom Soll verschwinden mit „Kurse
                  erzeugen“ oder deuten auf eigene Anpassungen an Kursen hin.
                </HelpTip>
              </td>
              {all.map((c) => (
                <td key={c.id} className="ce-col">
                  {istCell(c)}
                </td>
              ))}
              <td className="ce-sum" />
              {canEdit && <td className="ce-row-actions" />}
            </tr>
            <tr>
              <td className="ce-subject">Klassen</td>
              {all.map((c) => {
                const cls = appliesTo(c.id);
                return (
                  <td key={c.id} className="ce-col" title={cls.map((x) => x.name).join(', ')}>
                    {cls.length ? cls.length <= 4 ? cls.map((x) => x.name).join(', ') : cls.length : '–'}
                  </td>
                );
              })}
              <td className="ce-sum" />
              {canEdit && <td className="ce-row-actions" />}
            </tr>
          </tfoot>
        </table>
      </div>
      {canEdit && (
        <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
          <SubjectAdder options={subjectList.filter((s) => !rows.includes(s.id))} onPick={addRow} canCreate={canSubjects} />
        </div>
      )}
      {after}
      {dialogs}
    </div>
  );
}

function cellId(curId: string, subject: string): string {
  return `ce-${curId}-${subject}`.replace(/[^A-Za-z0-9_-]/g, '_');
}

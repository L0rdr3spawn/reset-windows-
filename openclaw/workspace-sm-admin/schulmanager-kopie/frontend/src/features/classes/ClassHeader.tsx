/**
 * Kopf der Klassen-Seite: Jahrgang, Standort, Schülerzahl, Klassenraum und Klassenleitung.
 * Mit `can_edit` (masterdata.edit) direkt änderbar – Klassenraum optional „auch im Stundenplan übernehmen“.
 * Hinweise vor dem Speichern stammen aus den Auswahllisten; verbindlich sind die Warnungen der Antwort.
 * R3 (V12): Zeile „Planung“ (Zeitraster · Unterrichtstage) nur mit `can_plan`, änderbar mit
 * „Stundenplan bearbeiten“ (`timetable.edit`); eine 409 `plan_change` erscheint als Liste mit „Trotzdem übernehmen“.
 */
import { useEffect, useId, useRef, useState } from 'react';
import { ApiError, errorMessage } from '../../api/client';
import { ClassPlanningFields, classPlanningOf, PLANNING_FORBIDDEN, samePlanning, type ClassPlanning } from '../../components/ClassPlanningFields';
import { useConfirmChanges } from '../../components/ConfirmChanges';
import { ClassExamLimitsFields, sameExamLimits, type ExamLimitValues } from '../../components/ExamLimits';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { SearchSelect, type SelectOption } from '../../components/SearchSelect';
import { Alert, AsyncButton } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { invalidate, useSettings } from '../../hooks/useCollection';
import { can } from '../../lib/permissions';
import { classPlanningText } from '../../lib/weeks';
import { classesApi } from './api';
import { roomHints, teacherHint } from './logic';
import type { ClassDetail, ClassPatchResult } from './types';

type EditKey = 'room' | 'teacher';

interface SavedInfo {
  what: EditKey;
  result: ClassPatchResult;
}

/** Bearbeitungsfeld: fokussiert die Auswahl beim Öffnen, Escape bricht ab (außer die Liste ist offen). */
function Editor({
  label,
  options,
  initial,
  hintsFor,
  extra,
  onSave,
  onCancel,
}: {
  label: string;
  options: SelectOption[];
  initial: string | null;
  hintsFor: (value: string | null) => string[];
  extra?: React.ReactNode;
  onSave: (value: string | null) => Promise<void>;
  onCancel: () => void;
}) {
  const id = useId();
  const [value, setValue] = useState<string | null>(initial);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    document.getElementById(id)?.focus();
  }, [id]);
  const hints = hintsFor(value);
  return (
    <div
      className="kl-editor stack-sm"
      onKeyDown={(e) => {
        if (e.key === 'Escape' && !e.defaultPrevented) {
          e.preventDefault();
          onCancel();
        }
      }}
    >
      <SearchSelect id={id} label={label} options={options} value={value} onChange={setValue} allowClear placeholder="Suchen …" />
      {hints.length > 0 && (
        <ul className="kl-hints" aria-live="polite">
          {hints.map((h) => (
            <li key={h}>
              <Icon name="alert" /> {h}
            </li>
          ))}
        </ul>
      )}
      {extra}
      {error && (
        <Alert kind="error" title="Nicht gespeichert">
          {error}
        </Alert>
      )}
      <div className="row">
        <AsyncButton
          className="btn btn-primary btn-sm"
          disabled={value === initial}
          onClick={async () => {
            setError(null);
            try {
              await onSave(value);
            } catch (e) {
              setError(errorMessage(e));
            }
          }}
        >
          <Icon name="check" /> Speichern
        </AsyncButton>
        <button type="button" className="btn btn-sm" onClick={onCancel}>
          Abbrechen
        </button>
      </div>
    </div>
  );
}

/** Höchstzahlen für Klassenarbeiten je Woche/Tag: Vorgabe (Jahrgang/Schule) oder eigene Werte der Klasse. */
function ExamLimitsEditor({ classId, initial, grade, onDone, onCancel }: { classId: string; initial: ExamLimitValues; grade: number; onDone: () => void; onCancel: () => void }) {
  const [value, setValue] = useState<ExamLimitValues>(initial);
  const [error, setError] = useState<string | null>(null);
  const inherit = (value.max_exams_per_week ?? null) === null && (value.max_exams_per_day ?? null) === null;
  return (
    <div
      className="kl-editor stack-sm"
      onKeyDown={(e) => {
        if (e.key === 'Escape' && !e.defaultPrevented) {
          e.preventDefault();
          onCancel();
        }
      }}
    >
      <ClassExamLimitsFields value={value} grade={grade} onChange={setValue} />
      {error && (
        <Alert kind="error" title="Nicht gespeichert">
          {error}
        </Alert>
      )}
      <div className="row">
        <AsyncButton
          className="btn btn-primary btn-sm"
          disabled={sameExamLimits(value, initial)}
          onClick={async () => {
            setError(null);
            try {
              await classesApi.patch(classId, inherit ? { exam_limits_inherit: true } : { max_exams_per_week: value.max_exams_per_week ?? null, max_exams_per_day: value.max_exams_per_day ?? null });
              onDone();
            } catch (e) {
              setError(errorMessage(e));
            }
          }}
        >
          <Icon name="check" /> Speichern
        </AsyncButton>
        <button type="button" className="btn btn-sm" onClick={onCancel}>
          Abbrechen
        </button>
      </div>
    </div>
  );
}

/** Bearbeiten des Planungsfelds (Unterrichtstage) mit 409-Bestätigung. */
function PlanningEditor({ classId, initial, onDone, onCancel }: { classId: string; initial: ClassPlanning; onDone: () => void; onCancel: () => void }) {
  const { data: settings } = useSettings();
  const [value, setValue] = useState<ClassPlanning>(initial);
  const [error, setError] = useState<string | null>(null);
  const confirm = useConfirmChanges();
  return (
    <div
      className="kl-editor stack-sm"
      onKeyDown={(e) => {
        if (e.key === 'Escape' && !e.defaultPrevented) {
          e.preventDefault();
          onCancel();
        }
      }}
    >
      <ClassPlanningFields value={value} onChange={setValue} settings={settings} />
      {error && (
        <Alert kind="error" title="Nicht gespeichert">
          {error}
        </Alert>
      )}
      <div className="row">
        <AsyncButton
          className="btn btn-primary btn-sm"
          disabled={samePlanning(value, initial)}
          onClick={async () => {
            setError(null);
            try {
              const r = await confirm.run((force) => classesApi.patch(classId, value, { force }));
              if (r) onDone();
            } catch (e) {
              setError(e instanceof ApiError && e.status === 403 ? PLANNING_FORBIDDEN : errorMessage(e));
            }
          }}
        >
          <Icon name="check" /> Speichern
        </AsyncButton>
        <button type="button" className="btn btn-sm" onClick={onCancel}>
          Abbrechen
        </button>
      </div>
      {confirm.dialog}
    </div>
  );
}

function SavedAlert({ info, onClose }: { info: SavedInfo; onClose: () => void }) {
  const { result, what } = info;
  const warn = result.warnings.length > 0 || result.skipped.length > 0;
  return (
    <Alert
      kind={warn ? 'warning' : 'success'}
      title={`${what === 'room' ? 'Klassenraum' : 'Klassenleitung'} gespeichert${result.warnings.length ? ' – bitte prüfen' : ''}`}
      action={
        <button type="button" className="btn btn-ghost btn-sm" onClick={onClose} aria-label="Hinweis schließen">
          <Icon name="close" />
        </button>
      }
    >
      {result.warnings.length > 0 && (
        <ul>
          {result.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}
      {what === 'room' && result.moved_lessons > 0 && (
        <p style={{ margin: '4px 0 0' }}>
          {result.moved_lessons === 1 ? '1 Stunde' : `${result.moved_lessons} Stunden`} im Stundenplan auf den neuen Raum umgestellt.
        </p>
      )}
      {result.skipped.length > 0 && (
        <>
          <p style={{ margin: '4px 0 0' }}>Nicht umgestellt (Raum zur selben Zeit belegt):</p>
          <ul>
            {result.skipped.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </>
      )}
    </Alert>
  );
}

export function ClassHeader({ detail, onSaved }: { detail: ClassDetail; onSaved: () => void }) {
  const cls = detail.class;
  const toast = useToast();
  const user = useUser();
  const { data: settings } = useSettings();
  const canPlanFields = detail.can_edit_plan ?? can(user, 'timetable.edit');
  const [planning, setPlanning] = useState(false);
  const planBtn = useRef<HTMLButtonElement>(null);
  const [exams, setExams] = useState(false);
  const examBtn = useRef<HTMLButtonElement>(null);
  const [editing, setEditing] = useState<EditKey | null>(null);
  const [saved, setSaved] = useState<SavedInfo | null>(null);
  const [apply, setApply] = useState(true);
  const roomBtn = useRef<HTMLButtonElement>(null);
  const teacherBtn = useRef<HTMLButtonElement>(null);
  const applyId = useId();

  const close = (what: EditKey) => {
    setEditing(null);
    // Fokus zurück auf „Ändern“ (nach dem Neuzeichnen)
    window.setTimeout(() => (what === 'room' ? roomBtn : teacherBtn).current?.focus(), 0);
  };

  const save = async (what: EditKey, value: string | null) => {
    const result = await classesApi.patch(cls.id, what === 'room' ? { home_room: value, apply_to_timetable: apply } : { class_teacher: value });
    setSaved({ what, result });
    if (!result.warnings.length && !result.skipped.length) toast.success(`${what === 'room' ? 'Klassenraum' : 'Klassenleitung'} gespeichert`);
    invalidate('classes');
    onSaved();
    close(what);
  };

  const rooms = detail.room_choices ?? [];
  const roomOptions: SelectOption[] = rooms.map((r) => {
    const others = r.home_of.filter((c) => c !== cls.id);
    return {
      value: r.id,
      label: r.name || r.id,
      sub: [r.type, r.capacity ? `${r.capacity} Plätze` : '', others.length ? `Klassenraum von ${others.join(', ')}` : ''].filter(Boolean).join(' · '),
      keywords: `${r.id} ${r.site}`,
    };
  });
  // die Klassenleitung steht auch ohne eigene Stunden in `teachers` – „unterrichtet“ nur mit Stunden
  const teachingRows = detail.teachers.filter((t) => t.hours > 0);
  const teaching = new Set(teachingRows.map((t) => t.id));
  const teacherOptions: SelectOption[] = (detail.teacher_choices ?? [])
    .map((t) => ({ value: t.id, label: t.name, sub: teaching.has(t.id) ? 'unterrichtet die Klasse' : undefined, keywords: t.id }))
    .sort((a, b) => Number(!!b.sub) - Number(!!a.sub) || a.label.localeCompare(b.label, 'de'));

  const room = cls.home_room;
  return (
    <section className="card kl-head" aria-label={`Angaben zur Klasse ${cls.name}`}>
      <dl className="kl-facts">
        <div>
          <dt>Klassenstufe</dt>
          <dd>{cls.grade || '–'}</dd>
        </div>
        <div>
          <dt>Standort</dt>
          <dd>{cls.site_name || cls.site || '–'}</dd>
        </div>
        <div>
          <dt>Schüler/innen</dt>
          <dd>{detail.student_count}</dd>
        </div>
        <div className="kl-fact-wide">
          <dt>Klassenraum</dt>
          <dd>
            {editing === 'room' ? (
              <Editor
                label="Neuer Klassenraum"
                options={roomOptions}
                initial={room?.id ?? null}
                hintsFor={(v) => {
                  const r = rooms.find((x) => x.id === v);
                  return roomHints(r, cls, detail.student_count).map((h) => `${r?.name ?? v} ${h}`);
                }}
                extra={
                  <div className="row">
                    <label className="check" htmlFor={applyId}>
                      <input id={applyId} type="checkbox" checked={apply} onChange={(e) => setApply(e.target.checked)} /> auch im Stundenplan übernehmen
                    </label>
                    <HelpTip>Ersetzt in Stunden von Kursen nur dieser Klasse den bisherigen Klassenraum, dort, wo der neue Raum zur selben Zeit frei ist.</HelpTip>
                  </div>
                }
                onSave={(v) => save('room', v)}
                onCancel={() => close('room')}
              />
            ) : (
              <span className="kl-fact-value">
                <span>
                  {room ? (
                    <>
                      <strong>{room.name}</strong>
                      <span className="muted small">
                        {' '}
                        {[room.type, room.capacity ? `${room.capacity} Plätze` : ''].filter(Boolean).join(' · ')}
                      </span>
                    </>
                  ) : (
                    <em className="muted">kein Klassenraum</em>
                  )}
                </span>
                {detail.can_edit && (
                  <button ref={roomBtn} type="button" className="btn btn-ghost btn-sm" aria-label="Klassenraum ändern" onClick={() => setEditing('room')}>
                    <Icon name="edit" /> Ändern
                  </button>
                )}
              </span>
            )}
          </dd>
        </div>
        <div className="kl-fact-wide">
          <dt>Klassenleitung</dt>
          <dd>
            {editing === 'teacher' ? (
              <Editor
                label="Neue Klassenleitung"
                options={teacherOptions}
                initial={cls.class_teacher?.id ?? null}
                hintsFor={(v) => {
                  const h = teacherHint(v, teachingRows);
                  return h ? [`${teacherOptions.find((o) => o.value === v)?.label ?? v} ${h}`] : [];
                }}
                onSave={(v) => save('teacher', v)}
                onCancel={() => close('teacher')}
              />
            ) : (
              <span className="kl-fact-value">
                <span>{cls.class_teacher ? <strong>{cls.class_teacher.name}</strong> : <em className="muted">nicht gesetzt</em>}</span>
                {detail.can_edit && (
                  <button ref={teacherBtn} type="button" className="btn btn-ghost btn-sm" aria-label="Klassenleitung ändern" onClick={() => setEditing('teacher')}>
                    <Icon name="edit" /> Ändern
                  </button>
                )}
              </span>
            )}
          </dd>
        </div>
        {(detail.can_plan || detail.can_edit) && cls.exam_limits && (
          <div className="kl-fact-wide">
            <dt>Klassenarbeiten</dt>
            <dd>
              {exams ? (
                <ExamLimitsEditor
                  classId={cls.id}
                  initial={{ max_exams_per_week: cls.max_exams_per_week ?? null, max_exams_per_day: cls.max_exams_per_day ?? null }}
                  grade={cls.grade}
                  onCancel={() => {
                    setExams(false);
                    window.setTimeout(() => examBtn.current?.focus(), 0);
                  }}
                  onDone={() => {
                    setExams(false);
                    toast.success('Höchstzahlen der Klasse gespeichert');
                    invalidate('classes');
                    onSaved();
                    window.setTimeout(() => examBtn.current?.focus(), 0);
                  }}
                />
              ) : (
                <span className="kl-fact-value">
                  <span>{cls.exam_limits.text}</span>
                  {detail.can_edit && (
                    <button ref={examBtn} type="button" className="btn btn-ghost btn-sm" aria-label="Höchstzahlen für Klassenarbeiten ändern" onClick={() => setExams(true)}>
                      <Icon name="edit" /> Ändern
                    </button>
                  )}
                </span>
              )}
            </dd>
          </div>
        )}
        {detail.can_plan && (
          <div className="kl-fact-wide">
            <dt>Planung</dt>
            <dd>
              {planning ? (
                <PlanningEditor
                  classId={cls.id}
                  initial={classPlanningOf(cls)}
                  onCancel={() => {
                    setPlanning(false);
                    window.setTimeout(() => planBtn.current?.focus(), 0);
                  }}
                  onDone={() => {
                    setPlanning(false);
                    toast.success('Planung der Klasse gespeichert');
                    invalidate('classes');
                    onSaved();
                    window.setTimeout(() => planBtn.current?.focus(), 0);
                  }}
                />
              ) : (
                <span className="kl-fact-value">
                  <span>{cls.plan?.text || classPlanningText(cls, settings)}</span>
                  {canPlanFields && (
                    <button ref={planBtn} type="button" className="btn btn-ghost btn-sm" aria-label="Planung ändern" onClick={() => setPlanning(true)}>
                      <Icon name="edit" /> Ändern
                    </button>
                  )}
                </span>
              )}
            </dd>
          </div>
        )}
      </dl>
      {/* dauerhafte Live-Region, damit Bildschirmleser das Ergebnis samt Warnungen ansagen */}
      <div aria-live="polite">{saved && <SavedAlert info={saved} onClose={() => setSaved(null)} />}</div>
    </section>
  );
}

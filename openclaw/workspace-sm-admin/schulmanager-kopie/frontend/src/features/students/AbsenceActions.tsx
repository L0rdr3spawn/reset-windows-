/**
 * Aktionen an einer Meldung (Familie, volljährige Schüler/innen): zurücknehmen, „Ich komme früher zurück“ (verkürzen),
 * verlängern, Rücknahme anfragen (wenn die Meldung schon bearbeitet ist), Beurlaubung zurückziehen/zurückgeben,
 * Unterlagen nachreichen. Welche Knöpfe erscheinen, bestimmt der Server pro Meldung (`actions`).
 */
import { useState } from 'react';
import { errorMessage } from '../../api/client';
import { studentAbsences as saApi } from '../../api/endpoints';
import type { StudentAbsence } from '../../api/types';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { AsyncButton, Field } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { addDays, formatDate } from '../../lib/dates';
import { studentSelfApi } from './api';
import { AttestPreview } from './ReportCard';
import type { StudentOverview } from './types';

type Panel = 'shorten' | 'extend' | null;

/** Frühester Tag, an dem man „wieder da“ sein kann, ohne die Meldung ganz aufzugeben (nach dem ersten Fehltag, nicht gestern). */
export function earliestBack(a: Pick<StudentAbsence, 'date_from'>, today: string): string {
  const next = addDays(a.date_from, 1);
  return next > today ? next : today;
}

function ShortenPanel({ a, ov, onDone, onCancel }: { a: StudentAbsence; ov: StudentOverview; onDone: () => void; onCancel: () => void }) {
  const toast = useToast();
  const minDay = earliestBack(a, ov.today);
  const canDay = a.date_to >= minDay;
  const lessonMin = a.date_from > ov.today ? a.date_from : ov.today;
  const canLesson = !a.periods?.length && a.date_to >= lessonMin;
  const [mode, setMode] = useState<'day' | 'lesson'>(canDay ? 'day' : 'lesson');
  const tomorrow = ov.next_school_day && ov.next_school_day > ov.today ? ov.next_school_day : addDays(ov.today, 1);
  const [day, setDay] = useState(tomorrow >= minDay && tomorrow <= a.date_to ? tomorrow : minDay);
  const [lessonDay, setLessonDay] = useState(lessonMin);
  const [lesson, setLesson] = useState(3);
  const back = mode === 'day' ? day : lessonDay;
  const valid = mode === 'day' ? canDay && day >= minDay && day <= a.date_to : canLesson && lessonDay >= lessonMin && lessonDay <= a.date_to && lesson >= 2 && lesson <= ov.periods;

  const save = async () => {
    try {
      await studentSelfApi.shorten(a.id, { back_date: back, ...(mode === 'lesson' ? { back_lesson: lesson } : {}) });
      toast.success(mode === 'lesson' ? `Gespeichert – ab der ${lesson}. Stunde am ${formatDate(back)} wieder da.` : `Gespeichert – ab ${formatDate(back)} wieder da.`);
      onDone();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  return (
    <div className="stack-sm st-panel">
      <div className="row">
        <strong>Ich komme früher zurück</strong>
        <HelpTip label="Hilfe zu „Früher zurück“">Die Meldung wird verkürzt. Lehrkräfte und Klassenleitung sehen die Änderung; Attestpflicht und Nachschreibtermine passen sich an.</HelpTip>
      </div>
      <div className="row" role="radiogroup" aria-label="Wann wieder da?">
        <label className="check">
          <input type="radio" name={`sh-${a.id}`} checked={mode === 'day'} disabled={!canDay} onChange={() => setMode('day')} /> Ab einem Tag wieder da
        </label>
        <label className="check">
          <input type="radio" name={`sh-${a.id}`} checked={mode === 'lesson'} disabled={!canLesson} onChange={() => setMode('lesson')} /> Ab einer Stunde wieder da
        </label>
      </div>
      <div className="form-grid">
        {mode === 'day' ? (
          <Field label="Wieder da ab (Tag)" htmlFor={`sh-day-${a.id}`}>
            <input id={`sh-day-${a.id}`} type="date" value={day} min={minDay} max={a.date_to} onChange={(e) => setDay(e.target.value)} />
          </Field>
        ) : (
          <>
            <Field label="Tag" htmlFor={`sh-ld-${a.id}`}>
              <input id={`sh-ld-${a.id}`} type="date" value={lessonDay} min={lessonMin} max={a.date_to} onChange={(e) => setLessonDay(e.target.value)} />
            </Field>
            <Field label="Wieder da ab Stunde" htmlFor={`sh-l-${a.id}`}>
              <select id={`sh-l-${a.id}`} value={lesson} onChange={(e) => setLesson(Number(e.target.value))}>
                {Array.from({ length: Math.max(0, ov.periods - 1) }, (_, i) => i + 2).map((n) => (
                  <option key={n} value={n}>
                    {n}. Stunde
                  </option>
                ))}
              </select>
            </Field>
          </>
        )}
      </div>
      <div className="row-end">
        <button type="button" className="btn btn-ghost" onClick={onCancel}>
          Abbrechen
        </button>
        <AsyncButton className="btn btn-primary" onClick={save} disabled={!valid}>
          <Icon name="check" /> Meldung verkürzen
        </AsyncButton>
      </div>
    </div>
  );
}

function ExtendPanel({ a, ov, onDone, onCancel }: { a: StudentAbsence; ov: StudentOverview; onDone: () => void; onCancel: () => void }) {
  const toast = useToast();
  const parent = ov.role === 'eltern';
  const leave = a.kind === 'beurlaubung';
  const asNewRequest = leave && a.status !== 'gemeldet';
  const [to, setTo] = useState(addDays(a.date_to, 1));
  const [reason, setReason] = useState('');
  const valid = to > a.date_to;
  const save = async () => {
    try {
      await studentSelfApi.extend(a.id, { date_to: to, ...(asNewRequest && reason.trim() ? { reason: reason.trim() } : {}) });
      toast.success(asNewRequest ? 'Verlängerung beantragt – die Klassenleitung entscheidet.' : `Verlängert bis ${formatDate(to)}.`);
      onDone();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  return (
    <div className="stack-sm st-panel">
      <div className="row">
        <strong>{leave ? 'Verlängerung beantragen' : 'Krankmeldung verlängern'}</strong>
        <HelpTip label="Hilfe zum Verlängern">
          {leave
            ? 'Für die zusätzlichen Tage entsteht ein neuer Antrag; die Klassenleitung entscheidet darüber.'
            : 'Die Meldung gilt dann bis zum neuen Ende. Ob ein Attest nötig wird, sehen Sie sofort darunter.'}
        </HelpTip>
      </div>
      <Field label={leave ? 'Neues Ende' : 'Neues Ende (voraussichtlich)'} htmlFor={`ex-to-${a.id}`}>
        <input id={`ex-to-${a.id}`} type="date" value={to} min={addDays(a.date_to, 1)} onChange={(e) => setTo(e.target.value)} />
      </Field>
      {asNewRequest && (
        <Field label="Anlass (optional)" htmlFor={`ex-r-${a.id}`} help="Ohne Eingabe gilt der Anlass des ursprünglichen Antrags.">
          <input id={`ex-r-${a.id}`} value={reason} maxLength={500} onChange={(e) => setReason(e.target.value)} />
        </Field>
      )}
      {!leave && <AttestPreview studentId={parent ? ov.student.id : undefined} from={a.date_from} to={to} valid={valid} parent={parent} />}
      <div className="row-end">
        <button type="button" className="btn btn-ghost" onClick={onCancel}>
          Abbrechen
        </button>
        <AsyncButton className="btn btn-primary" onClick={save} disabled={!valid}>
          <Icon name="check" /> {leave ? 'Verlängerung beantragen' : 'Verlängern'}
        </AsyncButton>
      </div>
    </div>
  );
}

export function AbsenceRowActions({ a, ov, onChanged, onUpload }: { a: StudentAbsence; ov: StudentOverview; onChanged: () => void; onUpload?: () => void }) {
  const toast = useToast();
  const [panel, setPanel] = useState<Panel>(null);
  const actions = a.actions ?? [];
  const leave = a.kind === 'beurlaubung';
  const done = () => {
    setPanel(null);
    onChanged();
  };
  const run = async (fn: () => Promise<unknown>, ok: string) => {
    try {
      await fn();
      toast.success(ok);
      onChanged();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  const has = (x: (typeof actions)[number]) => actions.includes(x);
  if (!actions.length && !onUpload) return null;

  return (
    <div className="st-row-actions">
      {has('withdraw') && (
        <AsyncButton
          className="btn btn-sm btn-ghost"
          confirm={leave ? 'Antrag zurückziehen?' : 'Meldung zurücknehmen? Lehrkräfte und Klassenbuch sehen sie dann nicht mehr.'}
          onClick={() => run(() => saApi.remove(a.id), leave ? 'Antrag zurückgezogen' : 'Meldung zurückgenommen')}
        >
          <Icon name="undo" /> {leave ? 'Antrag zurückziehen' : 'Zurücknehmen'}
        </AsyncButton>
      )}
      {has('request_withdrawal') &&
        (a.withdrawal_requested ? (
          <span className="small muted">
            <Icon name="check" /> Rücknahme angefragt – die Klassenleitung meldet sich.
          </span>
        ) : (
          <AsyncButton
            className="btn btn-sm btn-ghost"
            confirm="Die Klassenleitung bitten, diese Meldung zurückzunehmen?"
            onClick={() => run(() => studentSelfApi.requestWithdrawal(a.id), 'Rücknahme angefragt – die Klassenleitung wurde informiert.')}
          >
            <Icon name="undo" /> Rücknahme anfragen
          </AsyncButton>
        ))}
      {has('shorten') && (
        <button type="button" className="btn btn-sm" aria-expanded={panel === 'shorten'} onClick={() => setPanel(panel === 'shorten' ? null : 'shorten')}>
          Ich komme früher zurück
        </button>
      )}
      {has('extend') && (
        <button type="button" className="btn btn-sm" aria-expanded={panel === 'extend'} onClick={() => setPanel(panel === 'extend' ? null : 'extend')}>
          {leave ? 'Verlängerung beantragen' : 'Verlängern'}
        </button>
      )}
      {has('return_leave') && (
        <AsyncButton
          className="btn btn-sm btn-ghost"
          confirm="Beurlaubung zurückgeben? Sie ist dann nicht mehr nötig; die Klassenleitung wird informiert."
          onClick={() => run(() => studentSelfApi.returnLeave(a.id), 'Beurlaubung zurückgegeben – die Klassenleitung wurde informiert.')}
        >
          <Icon name="undo" /> Beurlaubung zurückgeben
        </AsyncButton>
      )}
      {onUpload && (
        <button type="button" className="btn btn-sm btn-ghost" onClick={onUpload}>
          <Icon name="upload" /> Unterlagen nachreichen
        </button>
      )}
      {panel === 'shorten' && <ShortenPanel a={a} ov={ov} onDone={done} onCancel={() => setPanel(null)} />}
      {panel === 'extend' && <ExtendPanel a={a} ov={ov} onDone={done} onCancel={() => setPanel(null)} />}
    </div>
  );
}

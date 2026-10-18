/**
 * Karte „Krank melden“ für volljährige Schüler/innen und Eltern (je Kind): ein großer Knopf „Für heute krank melden“
 * (ein Klick + Bestätigen), daneben „Mehrere Tage / später“ (von–bis, auch in der Zukunft, optional einzelne Stunden,
 * mit sofortiger Anzeige, ob ein Attest nötig ist) und „Beurlaubung beantragen“. Vordrucke zum Ausdrucken liegen
 * darunter. Nach jeder Meldung erscheint kurz eine Leiste mit „Rückgängig“ (Versehen!); danach gibt es weiter
 * „Zurücknehmen“ an der Meldung (siehe AbsenceActions). Minderjährige Schüler/innen sehen diese Karte nie (das
 * erledigen die Eltern). Gemeldet wird nur hier – die Kopfzeile hat keinen Melde-Knopf mehr.
 */
import { useEffect, useRef, useState } from 'react';
import { errorMessage } from '../../api/client';
import { studentAbsences as saApi } from '../../api/endpoints';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { AsyncButton, Field } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { addDays, formatDate, formatLong } from '../../lib/dates';
import { SickPhone } from '../../pages/StudentAbsencesPage';
import { studentSelfApi } from './api';
import { reportStart } from './logic';
import type { StudentOverview } from './types';

type Mode = 'closed' | 'range' | 'leave';

/** So lange (Sekunden) bleibt „Rückgängig“ nach einer Meldung sichtbar. */
const UNDO_SECONDS = 20;
type Undo = { id: string | number; text: string; key: number };

/** Leiste am unteren Rand: „Gemeldet – Rückgängig“ mit Ablauf (Versehen sofort zurücknehmen). */
function UndoBar({ undo, onUndo, onClose }: { undo: Undo; onUndo: () => Promise<unknown>; onClose: () => void }) {
  const [left, setLeft] = useState(UNDO_SECONDS);
  useEffect(() => {
    setLeft(UNDO_SECONDS);
    const t = window.setInterval(() => setLeft((n) => n - 1), 1000);
    return () => window.clearInterval(t);
  }, [undo.key]);
  useEffect(() => {
    if (left <= 0) onClose();
  }, [left, onClose]);
  return (
    <div className="st-undo" role="status">
      <span className="st-undo-text">{undo.text}</span>
      <AsyncButton className="btn btn-sm btn-primary" onClick={onUndo}>
        <Icon name="undo" /> Rückgängig ({Math.max(left, 0)})
      </AsyncButton>
      <button type="button" className="btn btn-sm btn-ghost btn-icon" onClick={onClose} aria-label="Leiste schließen">
        <Icon name="close" />
      </button>
    </div>
  );
}

/** Stundenwahl (1., 2., …) – gemeinsam für „Mehrere Tage“ und „Beurlaubung“ */
function PeriodPicker({ count, value, onChange, label }: { count: number; value: number[]; onChange: (v: number[]) => void; label: string }) {
  return (
    <div className="toggle-grid" role="group" aria-label={label}>
      {Array.from({ length: count }, (_, p) => (
        <button key={p} type="button" className="toggle" aria-pressed={value.includes(p)} onClick={() => onChange(value.includes(p) ? value.filter((x) => x !== p) : [...value, p].sort((a, b) => a - b))}>
          {p + 1}.
        </button>
      ))}
    </div>
  );
}

/** Zeile unter dem Zeitraum: „3 Schultage – Attest nötig“ bzw. „Unterschriebene Entschuldigung reicht“. */
export function AttestPreview({ studentId, from, to, valid }: { studentId?: string; from: string; to: string; valid: boolean; parent?: boolean }) {
  const q = useApi((signal) => saApi.preview({ student_id: studentId, from, to }, signal), [studentId, from, to], { enabled: valid });
  const p = q.data;
  if (!valid || !p) return null;
  const days = `${p.school_days} ${p.school_days === 1 ? 'Schultag' : 'Schultage'}`;
  if (!p.school_days) return <p className="small muted">Im gewählten Zeitraum ist kein Schultag.</p>;
  if (!p.attest_needed) {
    return (
      <p className="small" role="status">
        <Icon name="check" /> {days} – <strong>unterschriebene Entschuldigung reicht</strong>.
      </p>
    );
  }
  const why = [
    p.attest_by_days ? `ab ${p.attest_after_days} Schultagen` : '',
    ...p.exams.map((e) => `Klausur ${formatDate(e.date)}${e.title ? ` (${e.title})` : ''}`),
  ].filter(Boolean);
  return (
    <p className="small" role="status">
      <Icon name="alert" /> {days} – <strong>ärztliches Attest nötig</strong> ({why.join(', ')}). Sie können es nach der Meldung hochladen.
    </p>
  );
}

export function ReportCard({ ov, onDone }: { ov: StudentOverview; onDone: () => void }) {
  const toast = useToast();
  const [undo, setUndo] = useState<Undo | null>(null);
  const undoKey = useRef(0);
  const [mode, setMode] = useState<Mode>('closed');
  const [confirming, setConfirming] = useState(false);
  const parent = ov.role === 'eltern';
  const sid = parent ? ov.student.id : undefined;
  const start = reportStart(ov.today, ov.today_is_school_day, ov.next_school_day);
  const [from, setFrom] = useState(start);
  const [to, setTo] = useState(start);
  const [whole, setWhole] = useState(true);
  const [periods, setPeriods] = useState<number[]>([]);
  const [reason, setReason] = useState('');
  const [lvFrom, setLvFrom] = useState(start);
  const [lvTo, setLvTo] = useState(start);
  const [lvWhole, setLvWhole] = useState(true);
  const [lvPeriods, setLvPeriods] = useState<number[]>([]);
  const [lvReason, setLvReason] = useState('');
  const first = parent ? ov.student.name.split(' ')[0] : 'Sie';
  const already = ov.absences.some((a) => (a.kind ?? 'krank') === 'krank' && a.date_from <= start && a.date_to >= start && !a.periods?.length);

  /** Rückgängig-Leiste anbieten (nicht bei zusammengeführten Meldungen: sie gehören schon zu einer älteren Meldung). */
  const offerUndo = (r: { id: string | number; merged?: boolean } | undefined, text: string) => {
    if (r && !r.merged) setUndo({ id: r.id, text, key: ++undoKey.current });
  };
  const undoNow = async () => {
    if (!undo) return;
    try {
      await saApi.remove(undo.id);
      toast.success('Rückgängig gemacht – die Meldung ist zurückgenommen.');
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setUndo(null);
      onDone();
    }
  };

  const reset = () => {
    setMode('closed');
    setConfirming(false);
    setReason('');
    setPeriods([]);
    setLvReason('');
    setLvPeriods([]);
  };

  const sendToday = async () => {
    try {
      const r = await studentSelfApi.report({ student_id: sid, date_from: start, date_to: start, periods: [], reason: '' });
      toast.success(`${parent ? first : 'Sie'} ${parent ? 'ist' : 'sind'} krank gemeldet – gute Besserung!`);
      offerUndo(r, `${parent ? first : 'Sie'} ${parent ? 'ist' : 'sind'} für ${ov.today_is_school_day ? 'heute' : formatDate(start)} krank gemeldet.`);
      reset();
      onDone();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  const sendRange = async () => {
    try {
      const r = await studentSelfApi.report({ student_id: sid, date_from: from, date_to: to < from ? from : to, periods: whole ? [] : periods, reason: reason.trim() });
      toast.success(`Krankmeldung für ${parent ? ov.student.name : 'Sie'} übermittelt – gute Besserung!`);
      offerUndo(r, 'Krankmeldung übermittelt.');
      reset();
      onDone();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  const sendLeave = async () => {
    try {
      const r = await studentSelfApi.report({
        student_id: sid,
        date_from: lvFrom,
        date_to: lvTo < lvFrom ? lvFrom : lvTo,
        periods: lvWhole ? [] : lvPeriods,
        reason: lvReason.trim(),
        kind: 'beurlaubung',
      });
      toast.success('Beurlaubung beantragt – die Klassenleitung entscheidet, das Ergebnis steht unter „Meldungen“.');
      offerUndo(r, 'Beurlaubung beantragt.');
      reset();
      onDone();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  const rangeValid = !!from && !!to && to >= from;

  return (
    <section className="card st-report" aria-labelledby="st-report-h" id="krank-melden">
      <div className="card-head">
        <h2 id="st-report-h" className="with-help">
          {parent ? `${first} melden` : 'Krank melden'}
          <HelpTip label="Hilfe zum Krankmelden">
            {ov.today_is_school_day ? 'Heute' : `Nächster Schultag: ${formatLong(start)}`} – ein Klick genügt. Lehrkräfte und Klassenbuch sehen die Meldung sofort. Entschuldigt ist sie erst, wenn die schriftliche Entschuldigung (bei langer Krankheit das Attest)
            eingereicht und von der Klassenleitung bestätigt wurde. Den Grund sehen Fachlehrkräfte nicht.
          </HelpTip>
        </h2>
      </div>
      <SickPhone />
      <div className="row st-report-actions">
        {confirming ? (
          <>
            <span>{ov.today_is_school_day ? 'Heute' : formatDate(start)} krank melden?</span>
            <AsyncButton className="btn btn-primary" onClick={sendToday}>
              <Icon name="check" /> Ja, krank melden
            </AsyncButton>
            <button type="button" className="btn btn-ghost" onClick={() => setConfirming(false)}>
              Abbrechen
            </button>
          </>
        ) : (
          <>
            <button type="button" className="btn btn-primary btn-lg" onClick={() => setConfirming(true)} disabled={already}>
              <Icon name="medical" /> {already ? 'Schon krank gemeldet' : ov.today_is_school_day ? `${parent ? first : 'Mich'} für heute krank melden` : `Für ${formatDate(start)} krank melden`}
            </button>
            <button type="button" className="btn" aria-expanded={mode === 'range'} aria-controls="st-report-more" onClick={() => setMode(mode === 'range' ? 'closed' : 'range')}>
              Mehrere Tage / später
            </button>
            <button type="button" className="btn" aria-expanded={mode === 'leave'} aria-controls="st-report-leave" onClick={() => setMode(mode === 'leave' ? 'closed' : 'leave')}>
              Beurlaubung beantragen
            </button>
          </>
        )}
      </div>
      {mode === 'range' && (
        <div id="st-report-more" className="stack st-report-more">
          <div className="form-grid">
            <Field label="Erster Fehltag" htmlFor="st-from">
              <input
                id="st-from"
                type="date"
                value={from}
                min={addDays(ov.today, -30)}
                onChange={(e) => {
                  setFrom(e.target.value);
                  if (to < e.target.value) setTo(e.target.value);
                }}
              />
            </Field>
            <Field label="Letzter Fehltag (voraussichtlich)" htmlFor="st-to" help="Auch für die Zukunft möglich – z. B. für einen Operationstermin.">
              <input id="st-to" type="date" value={to} min={from} onChange={(e) => setTo(e.target.value)} />
            </Field>
          </div>
          <label className="check">
            <input type="checkbox" checked={whole} onChange={(e) => setWhole(e.target.checked)} /> ganztägig
          </label>
          {!whole && <PeriodPicker count={ov.periods} value={periods} onChange={setPeriods} label="Fehlstunden" />}
          <Field label="Grund (optional)" htmlFor="st-reason" help="Keine Diagnose nötig – z. B. „krank“ oder „Arzttermin“. Wird verschlüsselt gespeichert; Fachlehrkräfte sehen ihn nicht.">
            <input id="st-reason" type="text" value={reason} maxLength={500} onChange={(e) => setReason(e.target.value)} />
          </Field>
          <AttestPreview studentId={sid} from={from} to={to} valid={rangeValid} parent={parent} />
          <div className="row-end">
            <AsyncButton className="btn btn-primary" onClick={sendRange} disabled={!rangeValid || (!whole && !periods.length)}>
              <Icon name="medical" /> Krankmeldung senden
            </AsyncButton>
          </div>
        </div>
      )}
      {mode === 'leave' && (
        <div id="st-report-leave" className="stack st-report-more">
          <div className="form-grid">
            <Field label="Von" htmlFor="lv-from">
              <input
                id="lv-from"
                type="date"
                value={lvFrom}
                min={ov.today}
                onChange={(e) => {
                  setLvFrom(e.target.value);
                  if (lvTo < e.target.value) setLvTo(e.target.value);
                }}
              />
            </Field>
            <Field label="Bis" htmlFor="lv-to">
              <input id="lv-to" type="date" value={lvTo} min={lvFrom} onChange={(e) => setLvTo(e.target.value)} />
            </Field>
          </div>
          <label className="check">
            <input type="checkbox" checked={lvWhole} onChange={(e) => setLvWhole(e.target.checked)} /> ganze Tage
          </label>
          {!lvWhole && <PeriodPicker count={ov.periods} value={lvPeriods} onChange={setLvPeriods} label="Stunden der Beurlaubung" />}
          <Field label="Anlass" htmlFor="lv-reason" help="z. B. Arzttermin, Behördentermin, Fahrprüfung. Wird verschlüsselt gespeichert; die Klassenleitung entscheidet, die betroffenen Fachlehrkräfte erfahren nur Datum und Stunden – nicht den Anlass.">
            <input id="lv-reason" value={lvReason} maxLength={500} onChange={(e) => setLvReason(e.target.value)} />
          </Field>
          <div className="row-end">
            <AsyncButton className="btn btn-primary" onClick={sendLeave} disabled={!lvReason.trim() || !lvFrom || lvTo < lvFrom || (!lvWhole && !lvPeriods.length)}>
              Beurlaubung beantragen
            </AsyncButton>
          </div>
        </div>
      )}
      <div className="row st-report-forms">
        <span className="small muted">Zum Ausdrucken:</span>
        <a className="btn btn-sm btn-ghost" href={saApi.formUrl({ student_id: ov.student.id })} target="_blank" rel="noopener">
          <Icon name="download" /> Schriftliche Entschuldigung
        </a>
        <a className="btn btn-sm btn-ghost" href={saApi.leaveFormUrl({ student_id: ov.student.id })} target="_blank" rel="noopener">
          <Icon name="download" /> Antrag auf Beurlaubung
        </a>
      </div>
      {undo && <UndoBar undo={undo} onUndo={undoNow} onClose={() => setUndo(null)} />}
    </section>
  );
}

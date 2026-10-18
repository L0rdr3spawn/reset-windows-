/**
 * „Einmalige Ausnahme beantragen“: Datum (optional bis), ab/bis Stunde oder ganztägig, Anlass. Der Antrag geht an die
 * Prüfenden (Recht `teacher_requests.review`); bei Genehmigung entsteht eine Abwesenheit, die als Vertretungsfall in
 * die Vertretungsplanung läuft. Dauerhafte Änderungen (z. B. „nicht mehr mittwochs“) gehören dagegen in die
 * Verfügbarkeit mit „gilt ab“.
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { AsyncButton, Field } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { formatDateTime } from '../../lib/dates';
import { teacherProfileApi } from './api';
import { StatusBadge } from './components';
import { todayISO } from './availability';
import type { ChangeRequest } from './types';

/** Stunden aus „von/bis“ (1-basiert, leer = ganztägig, `bis` leer = bis Schulschluss) → 0-basierte Liste. */
export function periodsFromRange(from: number | null, to: number | null, total: number): number[] {
  if (!from) return [];
  const last = Math.min(total, to && to >= from ? to : total);
  return Array.from({ length: last - from + 1 }, (_, i) => from - 1 + i);
}

export function ExceptionCard({ periods, periodTimes, items, onChanged }: { periods: number; periodTimes: string[]; items: ChangeRequest[]; onChanged: () => void }) {
  const toast = useToast();
  const [date, setDate] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [mode, setMode] = useState<'all' | 'from' | 'range'>('from');
  const [from, setFrom] = useState(5);
  const [to, setTo] = useState(0);
  const [reason, setReason] = useState('');
  const [note, setNote] = useState('');
  const label = (p: number) => `${p}. Stunde${periodTimes[p - 1] ? ` (${periodTimes[p - 1]})` : ''}`;
  const send = async () => {
    try {
      const ps = mode === 'all' ? [] : periodsFromRange(from, mode === 'range' ? to : null, periods);
      const r = await teacherProfileApi.requestException({ date_from: date, date_to: dateTo || undefined, periods: ps, reason, note });
      toast.success(`Antrag gesendet – die Stundenplanung entscheidet. ${r.impact.text}`);
      setDate('');
      setDateTo('');
      setReason('');
      setNote('');
      onChanged();
    } catch (e) {
      toast.error(e, 'Antrag senden');
    }
  };
  return (
    <section className="card stack" aria-labelledby="tp-exc-h">
      <h2 id="tp-exc-h">
        Einmalige Ausnahme beantragen{' '}
        <HelpTip>
          Für einen einzelnen Termin, z. B. „Do 15.10. ab der 5. Stunde nicht da“. Bei Genehmigung wird der Unterricht als Abwesenheit vertreten. Dauerhafte Änderungen tragen Sie oben in der
          Verfügbarkeit mit „Gilt ab“ ein. Schüler/innen und Eltern stellen Anträge über die <Link to="/formulare">Formulare</Link>.
        </HelpTip>
      </h2>
      <div className="form-grid">
        <Field label="Datum" htmlFor="exc-date">
          <input id="exc-date" type="date" min={todayISO()} value={date} onChange={(e) => setDate(e.target.value)} />
        </Field>
        <Field label="bis Datum (optional)" htmlFor="exc-date-to">
          <input id="exc-date-to" type="date" min={date || todayISO()} value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </Field>
        <Field label="Welche Stunden?" htmlFor="exc-mode">
          <select id="exc-mode" value={mode} onChange={(e) => setMode(e.target.value as typeof mode)}>
            <option value="all">ganztägig</option>
            <option value="from">ab einer Stunde bis Schulschluss</option>
            <option value="range">von … bis …</option>
          </select>
        </Field>
        {mode !== 'all' && (
          <Field label={mode === 'range' ? 'von Stunde' : 'ab Stunde'} htmlFor="exc-from">
            <select id="exc-from" value={from} onChange={(e) => setFrom(Number(e.target.value))}>
              {Array.from({ length: periods }, (_, i) => (
                <option key={i} value={i + 1}>
                  {label(i + 1)}
                </option>
              ))}
            </select>
          </Field>
        )}
        {mode === 'range' && (
          <Field label="bis Stunde" htmlFor="exc-to">
            <select id="exc-to" value={to || from} onChange={(e) => setTo(Number(e.target.value))}>
              {Array.from({ length: periods - from + 1 }, (_, i) => (
                <option key={i} value={from + i}>
                  {label(from + i)}
                </option>
              ))}
            </select>
          </Field>
        )}
        <Field label="Anlass (kurz)" htmlFor="exc-reason" hint="z. B. Arzttermin, Fortbildung">
          <input id="exc-reason" type="text" maxLength={200} value={reason} onChange={(e) => setReason(e.target.value)} />
        </Field>
      </div>
      <Field label="Hinweis an die Prüfenden (optional)" htmlFor="exc-note" hint="Wird verschlüsselt gespeichert.">
        <textarea id="exc-note" className="tp-text" maxLength={2000} value={note} onChange={(e) => setNote(e.target.value)} />
      </Field>
      <div className="row">
        <AsyncButton className="btn btn-primary" onClick={send} disabled={!date}>
          <Icon name="check" /> Ausnahme beantragen
        </AsyncButton>
      </div>
      {items.length > 0 && (
        <ul className="list-plain tp-history" aria-label="Meine Ausnahme-Anträge">
          {items.slice(0, 8).map((r) => (
            <li key={r.id} className="card" style={{ padding: 12 }}>
              <div className="row-between">
                <span className="row" style={{ gap: 8 }}>
                  <StatusBadge status={r.status} label={r.status_label} />
                  <strong className="small">{r.exception_text}</strong>
                </span>
                <span className="small muted">{formatDateTime(r.decided_at ?? r.created_at)}</span>
              </div>
              {r.exception?.reason && <p className="small" style={{ margin: '6px 0 0' }}>{r.exception.reason}</p>}
              {r.review_comment && <p className="tp-note small">{r.review_comment}</p>}
              {r.status === 'offen' && (
                <AsyncButton
                  className="btn btn-sm"
                  confirm="Antrag zurückziehen?"
                  onClick={async () => {
                    try {
                      await teacherProfileApi.withdrawException(r.id);
                      onChanged();
                    } catch (e) {
                      toast.error(e);
                    }
                  }}
                >
                  <Icon name="undo" /> Zurückziehen
                </AsyncButton>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

import { useId, useState } from 'react';
import { calendar } from '../api/endpoints';
import { currentSchoolDay, formatLong, isValidISO, relativeDayLabel, shiftSchoolDay, todayISO, type SchoolDays } from '../lib/dates';
import { Icon } from './Icon';

/**
 * Datumsnavigation: vorheriger/nächster Schultag, Heute, Datumsfeld. `schoolDays` = Zahl (erste n Tage) oder Liste der
 * Unterrichtstage (R3, z. B. `open_days`); `weekText` = `week_info.week_text` („Woche 6 · KW 41“). Die Pfeile
 * überspringen auch Ferien, Feiertage und unterrichtsfreie Tage (Server, `classId` = Unterrichtstage der Klasse);
 * ohne Antwort gilt die Wochentagsregel.
 */
export function DateNav({
  value,
  onChange,
  schoolDays = 5,
  weekText,
  classId,
}: {
  value: string;
  onChange: (iso: string) => void;
  schoolDays?: SchoolDays;
  weekText?: string;
  classId?: string;
}) {
  const id = useId();
  const [busy, setBusy] = useState(false);
  const step = async (dir: 1 | -1) => {
    setBusy(true);
    try {
      const r = await calendar.schoolDay({ date: value, dir, class_id: classId });
      onChange(r.found ? r.date : shiftSchoolDay(value, dir, schoolDays));
    } catch {
      onChange(shiftSchoolDay(value, dir, schoolDays));
    } finally {
      setBusy(false);
    }
  };
  const rel = relativeDayLabel(value);
  return (
    <div className="date-nav" role="group" aria-label="Datum wählen">
      <button type="button" className="btn btn-icon" onClick={() => void step(-1)} disabled={busy} aria-label="Vorheriger Schultag">
        <Icon name="chevronLeft" />
      </button>
      <button type="button" className="btn" onClick={() => onChange(currentSchoolDay(new Date(), schoolDays))} disabled={value === todayISO()}>
        Heute
      </button>
      <button type="button" className="btn btn-icon" onClick={() => void step(1)} disabled={busy} aria-label="Nächster Schultag">
        <Icon name="chevronRight" />
      </button>
      <label htmlFor={id} className="sr-only">
        Datum
      </label>
      <input
        id={id}
        type="date"
        value={value}
        onChange={(e) => {
          if (isValidISO(e.target.value)) onChange(e.target.value);
        }}
      />
      <span className="date-label" aria-live="polite">
        {formatLong(value)}
        {(rel === 'Heute' || rel === 'Morgen' || rel === 'Gestern') && <span className="badge badge-primary ml-2">{rel}</span>}
        {weekText && (
          <span className="badge ml-1">
            {weekText}
          </span>
        )}
      </span>
    </div>
  );
}

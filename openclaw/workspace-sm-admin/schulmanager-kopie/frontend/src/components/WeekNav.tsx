/**
 * Wochenwahl (R3, Entwurf §8, §15.5): „‹ [Woche 12 · KW 45 · 02.11.–08.11.] › Heute“ und `week_text` des Servers.
 * Ersetzt die Wochenbuchstaben-Umschalter (DESIGN.md: Segmente nur für 2–5 Optionen). Die Auswahlliste nennt alle
 * Wochen 1 … Y des Schuljahres mit Ferien; ohne Schuljahresdaten (älterer Server) bleiben Blättern und „Heute“.
 * Blättern: Pfeiltasten links/rechts auf den Knöpfen, wochenweise immer Mo–So.
 */
import { useEffect, useId, useState, type KeyboardEvent } from 'react';
import { calendar } from '../api/endpoints';
import type { SchoolYear, WeekInfo } from '../api/types';
import { useApi } from '../hooks/useApi';
import { addDays, mondayOf, todayISO } from '../lib/dates';
import { dateInYear, holidayBadge, isCurrentWeek, plainWeekText, weekOfDate, weekOptionLabel, weekText } from '../lib/weeks';
import { groupLabel, groupWeeks, planOfWeek } from '../lib/planPeriods';
import { Icon } from './Icon';
import { PlanBadges } from './PlanNotice';
import './weeks.css';

/**
 * Schuljahr zum Datum (`GET /calendar/school-year`), neu geladen erst, wenn das Datum das Schuljahr verlässt, oder bei
 * Änderungen an Einstellungen/Ferien. `classId` liefert die Unterrichtstage der Klasse (`open_days`).
 */
export function useSchoolYear(date: string, opts: { classId?: string; enabled?: boolean } = {}): { year: SchoolYear | undefined; error: unknown } {
  const [anchor, setAnchor] = useState(date);
  const q = useApi<SchoolYear>((signal) => calendar.schoolYear({ date: anchor, class_id: opts.classId }, signal), [anchor, opts.classId], {
    enabled: opts.enabled !== false,
    live: ['settings', 'holidays', 'classes'],
  });
  useEffect(() => {
    if (q.data && !dateInYear(q.data, date) && date !== anchor) setAnchor(date);
  }, [date, q.data, anchor]);
  return { year: q.error ? undefined : q.data, error: q.error };
}

export function WeekNav({
  value,
  onChange,
  year,
  info,
  today = todayISO(),
  label = 'Woche wählen',
  showText = true,
}: {
  /** ein Tag der angezeigten Woche (wird auf Montag gerundet) */
  value: string;
  /** Montag der neuen Woche */
  onChange: (monday: string) => void;
  year?: SchoolYear | null;
  /** Woche der Antwort (Text, Ferien) */
  info?: WeekInfo | null;
  today?: string;
  label?: string;
  /** Text der Woche anzeigen (aus, wenn die Seite einen eigenen Titel mit Zeitraum zeigt) */
  showText?: boolean;
}) {
  const id = useId();
  const monday = mondayOf(value);
  const current = weekOfDate(year, monday);
  const numbering = year?.numbering ?? 'school_year';
  const go = (n: number) => onChange(addDays(monday, 7 * n));
  const onKey = (e: KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      go(-1);
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      go(1);
    }
  };
  const badge = holidayBadge(info ?? (current ? { holiday_week: current.holiday_week, holiday_name: current.holidays[0] ?? null } : null));
  const plan = info?.plan ?? planOfWeek(year, current);
  const groups = year?.plan_periods?.length ? groupWeeks(year) : null;
  const text = info && mondayOf(info.week_start) === monday ? weekText(info, monday) : current ? weekOptionLabel(current, numbering).replace(/ · Ferien$/, '') : plainWeekText(monday);
  return (
    <div className="week-nav" role="group" aria-label={label}>
      <span className="week-nav-main">
        <button type="button" className="btn btn-icon" onClick={() => go(-1)} onKeyDown={onKey} aria-label="Vorherige Woche">
          <Icon name="chevronLeft" />
        </button>
        {year && year.weeks.length > 0 && (
          <>
            <label htmlFor={id} className="sr-only">
              Woche
            </label>
            <select id={id} value={current ? current.week_start : ''} onChange={(e) => e.target.value && onChange(e.target.value)}>
              {!current && <option value="">{plainWeekText(monday)}</option>}
              {groups
                ? groups.map((g) => (
                    <optgroup key={g.period?.id ?? 'ohne'} label={groupLabel(g)}>
                      {g.weeks.map((w) => (
                        <option key={w.week_start} value={w.week_start}>
                          {weekOptionLabel(w, numbering)}
                        </option>
                      ))}
                    </optgroup>
                  ))
                : year.weeks.map((w) => (
                    <option key={w.week_start} value={w.week_start}>
                      {weekOptionLabel(w, numbering)}
                    </option>
                  ))}
            </select>
          </>
        )}
        <button type="button" className="btn btn-icon" onClick={() => go(1)} onKeyDown={onKey} aria-label="Nächste Woche">
          <Icon name="chevronRight" />
        </button>
      </span>
      <button type="button" className="btn" onClick={() => onChange(mondayOf(today))} disabled={isCurrentWeek(monday, today)}>
        Heute
      </button>
      {showText ? (
        <span className="week-text" aria-live="polite">
          {text}
        </span>
      ) : (
        <span className="sr-only" aria-live="polite">
          {text}
        </span>
      )}
      {(badge || isCurrentWeek(monday, today) || plan?.active) && (
        <span className="week-badges">
          {isCurrentWeek(monday, today) && <span className="badge badge-primary">Diese Woche</span>}
          {badge && <span className="badge badge-warning">{badge}</span>}
          <PlanBadges plan={plan} weekStart={monday} />
        </span>
      )}
    </div>
  );
}

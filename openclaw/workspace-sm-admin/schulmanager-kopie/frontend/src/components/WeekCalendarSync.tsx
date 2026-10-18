/**
 * Hält den Schuljahreskalender für die Wochenanzeige aktuell (`lib/weeks.ts` › `setWeekCalendar`): Alle Wochenangaben
 * (Kurse, Sperrzeiten, Aufsichten …) werden gespeichert als laufende Woche und als Kalenderwoche (KW) angezeigt und
 * eingegeben. Ändert sich der Kalender (Einstellungen, Schuljahreswechsel), baut `WeekCalendarOutlet` die Seite neu auf,
 * damit alle Wochentexte neu berechnet werden.
 */
import { Fragment, useEffect, useSyncExternalStore } from 'react';
import { Outlet } from 'react-router-dom';
import { todayISO } from '../lib/dates';
import { setWeekCalendar, subscribeWeekCalendar, weekCalendarVersion } from '../lib/weeks';
import { useSchoolYear } from './WeekNav';

export function WeekCalendarSync() {
  const { year } = useSchoolYear(todayISO());
  useEffect(() => {
    const first = year?.first_monday ?? year?.weeks[0]?.week_start;
    setWeekCalendar(year && first ? { iso: year.numbering === 'iso', firstMonday: first, weeks: year.weeks_in_year } : null);
  }, [year]);
  return null;
}

/** `<Outlet />` mit neuem Aufbau bei geändertem Kalender. */
export function WeekCalendarOutlet() {
  const version = useSyncExternalStore(subscribeWeekCalendar, weekCalendarVersion);
  return (
    <>
      <WeekCalendarSync />
      <Fragment key={version}>
        <Outlet />
      </Fragment>
    </>
  );
}

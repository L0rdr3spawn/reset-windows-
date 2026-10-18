import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { data as dataApi, planning } from '../api/endpoints';
import type { Duty } from '../api/types';
import { Icon } from '../components/Icon';
import { Modal } from '../components/Modal';
import { SearchSelect, type SelectOption } from '../components/SearchSelect';
import { AsyncButton, Empty, ErrorBox, Loading } from '../components/ui';
import { useSchoolYear, WeekNav } from '../components/WeekNav';
import { WeekPatternInput } from '../components/WeekPatternInput';
import { useUser } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { invalidate, useCollection, useSettings } from '../hooks/useCollection';
import { useMediaQuery, useTitle } from '../hooks/misc';
import { useApi } from '../hooks/useApi';
import { DutyOverviewView, overviewCounts, type DutyPick } from '../features/duties/DutyOverviewView';
import { mondayOf, todayISO, WEEKDAYS, WEEKDAYS_SHORT } from '../lib/dates';
import { sortBy } from '../lib/format';
import { can } from '../lib/permissions';
import { describeSelection, specActive, weekOfDate, weekQueryFromSearch } from '../lib/weeks';
import { isScopedTeacher } from '../features/teacher/windows';
import type { BreakDef, SupervisionArea } from '../api/types';
import { SiteAbbr } from '../components/Abbr';

/** Woche der Ansicht: laufende Woche; unbekannt (ohne Schuljahresdaten) = alle Aufsichten. */
export interface DutyWeek {
  weekNo?: number;
}

/** Findet die Aufsicht in dieser Woche statt? (jede Woche, ausgewählte Wochen oder Rhythmus) */
export function dutyActive(d: Pick<Duty, 'weeks' | 'rhythm'>, w: DutyWeek): boolean {
  return specActive(d, w.weekNo);
}

/** Wochenangabe einer Aufsicht („Woche 1“, „jede 2. Woche ab Woche 10“) oder leer bei jeder Woche. */
export function dutyWeeksText(d: Pick<Duty, 'weeks' | 'rhythm'>): string {
  const t = describeSelection(d);
  return t === 'jede Woche' ? '' : t;
}

/** Lehrkräfte (§9.3) bekommen vom Server nur ihre eigenen Aufsichten – als kompakte Liste statt Gesamtplan. */
function MyDutiesList({ duties, areas, breaks, week }: { duties: Duty[]; areas: SupervisionArea[]; breaks: BreakDef[]; week: DutyWeek }) {
  const byArea = new Map(areas.map((a) => [a.id, a]));
  const rows = sortBy(
    duties.filter((d) => dutyActive(d, week)),
    (d) => `${d.day}-${String(d.break_index).padStart(2, '0')}`,
  );
  if (!rows.length) return <Empty icon="whistle">Sie haben in dieser Woche keine Pausenaufsichten.</Empty>;
  return (
    <ul className="list-plain stack-sm" aria-label="Meine Pausenaufsichten">
      {rows.map((d) => {
        const b = breaks[d.break_index];
        const a = byArea.get(d.area);
        return (
          <li key={d.id} className="card" style={{ padding: 12 }}>
            <strong>{WEEKDAYS[d.day] ?? `Tag ${d.day + 1}`}</strong> · {b ? `Pause ${d.break_index + 1} (nach der ${b.after + 1}. Stunde)` : `Pause ${d.break_index + 1}`}
            <div className="small muted">
              {a ? a.name : d.area}
              {a?.site ? (
                <>
                  {' · '}
                  <SiteAbbr id={a.site} />
                </>
              ) : null}
              {dutyWeeksText(d) ? ` · ${dutyWeeksText(d)}` : ''}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function DutyModal({ duty, label, yearWeeks, onClose }: { duty: Partial<Duty>; label: string; yearWeeks: number; onClose: () => void }) {
  const toast = useToast();
  const teachers = useCollection('teachers');
  const [teacher, setTeacher] = useState<string | null>(duty.teacher ?? null);
  const [weeks, setWeeks] = useState<{ weeks: number[]; rhythm?: Duty['rhythm'] }>({ weeks: duty.weeks ?? [], rhythm: duty.rhythm ?? null });
  const options: SelectOption[] = useMemo(() => sortBy(teachers.data ?? [], (t) => t.name).map((t) => ({ value: t.id, label: t.name, sub: t.id })), [teachers.data]);
  const save = async () => {
    const body = { teacher, weeks: weeks.weeks, rhythm: weeks.rhythm ?? null };
    try {
      if (duty.id) await dataApi.update('duties', duty.id, { ...(duty as Duty), ...body });
      else await dataApi.create('duties', { ...duty, ...body });
      invalidate('duties');
      toast.success('Aufsicht gespeichert');
      onClose();
    } catch (e) {
      toast.error(e, 'Speichern');
    }
  };
  const remove = async () => {
    if (!duty.id) return;
    try {
      await dataApi.remove('duties', duty.id);
      invalidate('duties');
      toast.success('Aufsicht entfernt');
      onClose();
    } catch (e) {
      toast.error(e, 'Löschen');
    }
  };
  return (
    <Modal
      title={duty.id ? 'Aufsicht ändern' : 'Aufsicht hinzufügen'}
      onClose={onClose}
      footer={
        <>
          {duty.id && (
            <button type="button" className="btn btn-ghost" onClick={remove}>
              <Icon name="trash" /> Entfernen
            </button>
          )}
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={save}>
            Speichern
          </AsyncButton>
        </>
      }
    >
      <p className="muted">{label}</p>
      <div className="stack">
        <SearchSelect label="Lehrkraft" options={options} value={teacher} onChange={setTeacher} allowClear />
        <WeekPatternInput value={weeks} onChange={setWeeks} yearWeeks={yearWeeks} />
      </div>
    </Modal>
  );
}

export default function DutiesPage() {
  useTitle('Pausenaufsichten');
  const user = useUser();
  const toast = useToast();
  const { data: settings } = useSettings();
  const duties = useCollection('duties');
  const areas = useCollection('areas');
  const sites = useCollection('sites');
  const canEdit = can(user, 'timetable.edit');
  const canSee = canEdit || can(user, 'substitution.edit');
  const ownOnly = isScopedTeacher(user) && !canSee;
  // Woche (R3): ?datum= (Montag) bzw. ?woche=L wie im Stundenplan; ohne Schuljahresdaten werden alle Aufsichten gezeigt
  const [search, setSearch] = useSearchParams();
  const wq = weekQueryFromSearch(search);
  const today = todayISO();
  const { year } = useSchoolYear(wq.date ?? mondayOf(today));
  const fromNo = wq.week_no && !wq.date ? year?.weeks.find((w) => w.week_no === wq.week_no) : undefined;
  const monday = wq.date ?? fromNo?.week_start ?? mondayOf(today);
  const yw = weekOfDate(year, monday);
  const week: DutyWeek = yw ? { weekNo: yw.week_no } : {};
  const setMonday = (m: string) => {
    const sp = new URLSearchParams(search);
    sp.set('datum', m);
    sp.delete('woche');
    setSearch(sp, { replace: true });
  };
  const [site, setSite] = useState('');
  const [onlyMine, setOnlyMine] = useState(false);
  const [edit, setEdit] = useState<{ duty: Partial<Duty>; label: string } | null>(null);
  const wide = useMediaQuery('(min-width: 900px)');
  const [modePref, setModePref] = useState<'week' | 'day' | null>(null);
  const mode: 'week' | 'day' = modePref ?? (wide ? 'week' : 'day');
  const [dayPref, setDayPref] = useState<number | null>(null);

  const overview = useApi((signal) => planning.dutiesOverview(monday, signal), [monday], {
    enabled: canSee,
    live: ['duties', 'absences', 'substitutions', 'events', 'timetable'],
  });
  const ov = overview.data;
  const openDaysOv = (ov?.days ?? []).filter((d) => d.open);
  const day = dayPref ?? openDaysOv.find((d) => d.date === today)?.weekday ?? openDaysOv[0]?.weekday ?? 0;
  const counts = overviewCounts(ov, site);

  const mineCount = useMemo(
    () => (duties.data ?? []).filter((d) => d.teacher && d.teacher === user.teacher_id && dutyActive(d, week)).length,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [duties.data, user.teacher_id, week.weekNo],
  );

  const pick = (p: DutyPick) => {
    const found = p.dutyId ? (duties.data ?? []).find((x) => x.id === p.dutyId) : undefined;
    setEdit({ duty: found ?? { area: p.area, day: p.day, break_index: p.breakIndex, teacher: null, weeks: [] }, label: p.label });
  };

  if (duties.error) return <ErrorBox error={duties.error} onRetry={duties.reload} />;
  if (!duties.data || !areas.data) return <Loading />;

  return (
    <div className="page">
      <div className="page-head">
        <h1>Pausenaufsichten</h1>
        <div className="actions">
          {canEdit && (
            <AsyncButton
              className="btn btn-primary"
              confirm="Alle Pausenaufsichten neu und fair verteilen? Bestehende Einteilung wird ersetzt."
              onClick={async () => {
                try {
                  const r = await planning.generateDuties();
                  invalidate('duties');
                  overview.reload();
                  const open = Number((r as Record<string, unknown>).open ?? 0);
                  if (open) toast.warning(`Aufsichten erzeugt – ${open} offen`);
                  else toast.success('Aufsichten automatisch erzeugt');
                } catch (e) {
                  toast.error(e, 'Erzeugen');
                }
              }}
            >
              <Icon name="sparkles" /> Automatisch erzeugen
            </AsyncButton>
          )}
          <button type="button" className="btn" onClick={() => window.print()}>
            <Icon name="print" /> Drucken
          </button>
        </div>
      </div>
      <div className="toolbar card" style={{ padding: 12 }}>
        {(sites.data?.length ?? 0) > 1 && !ownOnly && (
          <div className="field">
            <label htmlFor="d-site">Standort</label>
            <select id="d-site" value={site} onChange={(e) => setSite(e.target.value)}>
              <option value="">alle</option>
              {(sites.data ?? []).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="field" style={{ minWidth: 0 }}>
          <span className="field-label">Woche</span>
          <WeekNav value={monday} onChange={setMonday} year={year} today={today} />
        </div>
        {user.teacher_id && !ownOnly && (
          <label className="check">
            <input type="checkbox" checked={onlyMine} onChange={(e) => setOnlyMine(e.target.checked)} /> nur meine ({mineCount})
          </label>
        )}
        {ownOnly ? (
          <span className="small muted">Sie sehen Ihre eigenen Aufsichten ({mineCount} in dieser Woche).</span>
        ) : (
          <>
            {counts.open > 0 ? <span className="badge badge-danger">{counts.open} offene Plätze</span> : <span className="badge badge-success">alle Aufsichten besetzt</span>}
            {counts.replaced > 0 && <span className="badge badge-warning">{counts.replaced} mit automatischem Ersatz</span>}
            {counts.conflict > 0 && <span className="badge badge-danger">{counts.conflict} Konflikte ohne Ersatz</span>}
          </>
        )}
      </div>
      {!ownOnly && (
        <div className="duty-modebar" role="group" aria-label="Ansicht">
          <button type="button" className={`btn btn-sm${mode === 'week' ? ' btn-primary' : ''}`} aria-pressed={mode === 'week'} onClick={() => setModePref('week')}>
            Woche
          </button>
          <button type="button" className={`btn btn-sm${mode === 'day' ? ' btn-primary' : ''}`} aria-pressed={mode === 'day'} onClick={() => setModePref('day')}>
            Tag
          </button>
          {mode === 'day' &&
            openDaysOv.map((d) => (
              <button key={d.date} type="button" className={`btn btn-sm${d.weekday === day ? ' btn-primary' : ''}`} aria-pressed={d.weekday === day} onClick={() => setDayPref(d.weekday)}>
                {WEEKDAYS_SHORT[d.weekday]}
              </button>
            ))}
        </div>
      )}
      {ownOnly ? (
        <MyDutiesList duties={duties.data} areas={areas.data} breaks={settings?.breaks ?? []} week={week} />
      ) : overview.error ? (
        <ErrorBox error={overview.error} onRetry={overview.reload} />
      ) : !ov ? (
        <Loading />
      ) : ov.days.every((d) => d.breaks.length === 0) && areas.data.length === 0 ? (
        <Empty icon="whistle">Keine Aufsichtsbereiche oder Pausen angelegt (Stammdaten → Aufsichtsbereiche, Planung → Zeitraster).</Empty>
      ) : (
        <DutyOverviewView ov={ov} mode={mode} day={day} myId={user.teacher_id} onlyMine={onlyMine} canEdit={canEdit} site={site} onPick={pick} />
      )}
      {edit && (
        <DutyModal
          duty={edit.duty}
          label={edit.label}
          yearWeeks={year?.weeks_in_year ?? 52}
          onClose={() => {
            setEdit(null);
            overview.reload();
          }}
        />
      )}
    </div>
  );
}

/**
 * Planungsfeld einer Klasse (Entwurf §3, §15.2 V12, Texte §15.5): Jahrgang (bestimmt die Stundentafel) und
 * Unterrichtstage („Wie Schule (Mo–Fr)“ oder Chips). Unterrichtstage ändern nur Konten mit „Stundenplan bearbeiten“
 * (`timetable.edit`); das Backend prüft es (403) und bestätigt Umrechnungen per 409. Den Jahrgang ändern Stammdaten
 * oder Stundenplanung.
 */
import { useId } from 'react';
import type { Settings } from '../api/types';
import { useCollection } from '../hooks/useCollection';
import { daysText, schoolDaysOf } from '../lib/weeks';
import { DayChips } from './WeekPatternInput';
import { Field } from './ui';

export interface ClassPlanning {
  school_days: number[];
  /** Jahrgang (`GradeProfile.id`), null = keine Zuordnung */
  profile: string | null;
}

/** Werte der Klasse mit Standards (leer = Schulvorgabe). `profile` darf als ID oder als `{id}` kommen. */
export function classPlanningOf(cls: { school_days?: number[] | null; profile?: string | { id: string } | null } | null | undefined): ClassPlanning {
  const p = cls?.profile;
  return { school_days: [...(cls?.school_days ?? [])], profile: typeof p === 'string' ? p || null : p?.id ?? null };
}

export function samePlanning(a: ClassPlanning, b: ClassPlanning): boolean {
  return a.school_days.join(',') === b.school_days.join(',') && (a.profile ?? null) === (b.profile ?? null);
}

export const PLANNING_FORBIDDEN = 'Für Zeitraster und Unterrichtstage brauchen Sie das Recht „Stundenplan bearbeiten“.';

export function ClassPlanningFields({
  value,
  onChange,
  settings,
  disabled,
  profileDisabled,
}: {
  value: ClassPlanning;
  onChange: (v: ClassPlanning) => void;
  settings: Pick<Settings, 'days' | 'school_days'> | null | undefined;
  disabled?: boolean;
  /** Jahrgang nicht änderbar (sonst wie `disabled`) */
  profileDisabled?: boolean;
}) {
  const id = useId();
  const profiles = useCollection('grade_profiles');
  const schoolDays = schoolDaysOf(settings);
  const ownDays = value.school_days.length > 0;
  const list = (profiles.data ?? []).slice().sort((a, b) => (a.grade ?? 999) - (b.grade ?? 999) || a.name.localeCompare(b.name, 'de', { numeric: true }));
  const unknown = value.profile && !list.some((p) => p.id === value.profile);
  return (
    <div className="stack-sm">
      <Field label="Jahrgang" htmlFor={`${id}-profile`} help="Der Jahrgang bestimmt die Stundentafel der Klasse (sofern sie keine eigene hat). Jahrgänge anlegen und ändern Sie unter Stammdaten → Jahrgänge.">
        <select id={`${id}-profile`} value={value.profile ?? ''} disabled={profileDisabled ?? disabled} onChange={(e) => onChange({ ...value, profile: e.target.value || null })}>
          <option value="">– kein Jahrgang –</option>
          {unknown && <option value={value.profile as string}>{value.profile} (unbekannt)</option>}
          {list.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
              {p.grade !== null && p.grade !== undefined && !p.name.includes(String(p.grade)) ? ` (Stufe ${p.grade})` : ''}
            </option>
          ))}
        </select>
      </Field>
      <div className="field">
        <span className="field-label" id={`${id}-days`}>
          Unterrichtstage
        </span>
        <label className="check">
          <input type="checkbox" checked={!ownDays} disabled={disabled} onChange={(e) => onChange({ ...value, school_days: e.target.checked ? [] : [...schoolDays] })} /> Wie Schule ({daysText(schoolDays)})
        </label>
        {ownDays && <DayChips value={value.school_days} onChange={(d) => onChange({ ...value, school_days: d })} label="Unterrichtstage der Klasse" disabled={disabled} />}
      </div>
    </div>
  );
}

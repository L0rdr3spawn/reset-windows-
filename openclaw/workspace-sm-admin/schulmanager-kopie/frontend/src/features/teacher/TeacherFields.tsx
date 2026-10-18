/**
 * Felder für den Lehrer-Editor in den Stammdaten (Planung/Sekretariat): Verfügbarkeit (Sperrzeiten und Wünsche in einem
 * Editor) mit Konfliktprüfung und Lösungsvorschlägen.
 */
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import type { TimeRule } from '../../api/types';
import { Icon } from '../../components/Icon';
import { useUser } from '../../context/AuthContext';
import { useDebounced } from '../../hooks/misc';
import { can } from '../../lib/permissions';
import { teacherProfileApi } from './api';
import { ConflictList } from './components';
import { AvailabilityEditor } from './AvailabilityEditor';
import { detachRules, todayISO } from './availability';
import type { PreviewResponse, TimeWindow } from './types';

export interface GridRefs {
  days: number;
  periods: number;
  periodTimes: string[];
  periodMinutes: number;
}

export function asWindows(v: unknown): TimeWindow[] {
  if (!Array.isArray(v)) return [];
  return v
    .filter((w): w is TimeWindow => !!w && typeof w === 'object' && Array.isArray((w as TimeWindow).days))
    .map((w) => ({
      days: [...w.days],
      start: String(w.start ?? ''),
      end: String(w.end ?? ''),
      weeks: Array.isArray(w.weeks) ? [...w.weeks] : [],
      ...(w.rhythm ? { rhythm: { ...w.rhythm } } : {}),
    }));
}

/** „Verfügbarkeit“ in den Stammdaten: Sperrzeiten und Wünsche in EINEM Editor (Raster antippen + Rhythmus + „gilt ab“).
 * Alte Zeitfenster/Raster-Sperren erscheinen als normale Blöcke und werden beim ersten Ändern ersetzt (verlustfrei).
 * Bei bestehenden Lehrkräften Konflikte mit Lösungsvorschlägen laut Server. */
export function TeacherAvailabilityField({
  teacherId,
  isNew,
  unavailable,
  wishes,
  onChange,
  disabled,
  refs,
  profile,
}: {
  teacherId: string;
  isNew: boolean;
  unavailable: TimeRule[];
  wishes: TimeRule[];
  /** neue Regeln; Zeitfenster und Raster werden dabei geleert */
  onChange: (v: { unavailable: TimeRule[]; wishes: TimeRule[] }) => void;
  disabled?: boolean;
  refs: GridRefs & { yearWeeks?: number };
  profile: { subjects: string[]; preferred_classes: string[]; max_hours: number };
}) {
  const user = useUser();
  const hard = useMemo(() => detachRules(unavailable), [unavailable]);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const input = useDebounced(JSON.stringify({ hard, wishes, profile }), 400);
  useEffect(() => {
    if (isNew || !teacherId) {
      setPreview(null);
      return undefined;
    }
    let alive = true;
    const parsed = JSON.parse(input) as { hard: TimeRule[]; wishes: TimeRule[]; profile: { subjects: string[]; preferred_classes: string[]; max_hours: number } };
    teacherProfileApi
      .preview(teacherId, { unavailable: parsed.hard, wishes: parsed.wishes, ...parsed.profile })
      .then((r) => alive && setPreview(r))
      .catch(() => alive && setPreview(null));
    return () => {
      alive = false;
    };
  }, [input, teacherId, isNew]);
  const outside = preview?.conflicts.outside_windows.length ?? 0;
  return (
    <div className="span-all stack">
      <AvailabilityEditor
        unavailable={hard}
        wishes={wishes}
        onChange={onChange}
        days={refs.days}
        periods={refs.periods}
        periodTimes={refs.periodTimes}
        periodMinutes={refs.periodMinutes}
        yearWeeks={refs.yearWeeks}
        hours={profile.max_hours}
        conflicts={preview?.conflicts.outside_windows ?? []}
        disabled={disabled}
        who="die Lehrkraft"
        defaultValidFrom={isNew ? '' : todayISO()}
      />
      {preview && <ConflictList conflicts={preview.conflicts} title="Auswirkungen beim Speichern" />}
      {outside > 0 && can(user, 'timetable.generate') && (
        <p className="small" style={{ margin: 0 }}>
          Nach dem Speichern:{' '}
          <Link to={`/planung/antraege?lehrkraft=${encodeURIComponent(teacherId)}`}>
            <Icon name="sparkles" /> Stundenplan dieser Lehrkraft neu planen
          </Link>
        </p>
      )}
    </div>
  );
}

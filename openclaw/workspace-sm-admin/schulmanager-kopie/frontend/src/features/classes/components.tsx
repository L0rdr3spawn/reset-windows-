/**
 * Kleine Bausteine der Klassen-Seite: Status-Badge (Text + Kurzzeichen, nie nur Farbe), Namensauflösung,
 * Stundenauswahl.
 */
import { useMemo } from 'react';
import { useIndex } from '../../hooks/useCollection';
import { makeNames, STATUS_INFO, type NameLookup, type StatusKey } from './logic';
import type { ClassDetail } from './types';

export function StatusBadge({ status, compact }: { status: StatusKey; compact?: boolean }) {
  const info = STATUS_INFO[status];
  return (
    <span className={`kind kl-status ${info.cls}`} title={info.description}>
      <span className="kind-short" aria-hidden="true">
        {info.short}
      </span>
      {compact ? <span className="sr-only">{info.label}</span> : info.label}
    </span>
  );
}

/**
 * Namen für Fächer, Lehrkräfte und Räume: Stammdaten (für alle Schulkonten lesbar) und, falls diese noch laden
 * oder fehlen, die Namen aus der Klassenantwort.
 */
export function useClassNames(detail: ClassDetail | undefined): NameLookup {
  const subjects = useIndex('subjects');
  const teachers = useIndex('teachers');
  const rooms = useIndex('rooms');
  return useMemo(() => {
    const s = new Map<string, string>();
    const t = new Map<string, string>();
    const r = new Map<string, string>();
    for (const x of detail?.subjects ?? []) {
      if (x.subject_name) s.set(x.subject, x.subject_name);
      if (x.teacher) t.set(x.teacher.id, x.teacher.name);
    }
    for (const x of detail?.teachers ?? []) t.set(x.id, x.name);
    for (const x of detail?.teacher_choices ?? []) t.set(x.id, x.name);
    for (const x of detail?.room_choices ?? []) r.set(x.id, x.name);
    if (detail?.class.home_room) r.set(detail.class.home_room.id, detail.class.home_room.name);
    for (const [id, x] of subjects) if (x.name) s.set(id, x.name);
    for (const [id, x] of teachers) if (x.name) t.set(id, x.name);
    for (const [id, x] of rooms) if (x.name) r.set(id, x.name);
    return makeNames({ subjects: s, teachers: t, rooms: r });
  }, [detail, subjects, teachers, rooms]);
}

/** Stunden auswählen (Umschaltknöpfe); `only` beschränkt auf bestimmte Stunden. */
export function PeriodToggles({
  count,
  value,
  onChange,
  times,
  labelId,
  only,
}: {
  count: number;
  value: readonly number[];
  onChange: (v: number[]) => void;
  times?: readonly string[];
  labelId: string;
  only?: readonly number[];
}) {
  const list = only ?? Array.from({ length: count }, (_, p) => p);
  return (
    <div className="toggle-grid" role="group" aria-labelledby={labelId}>
      {list.map((p) => {
        const on = value.includes(p);
        return (
          <button
            key={p}
            type="button"
            className="toggle"
            aria-pressed={on}
            title={times?.[p] || undefined}
            onClick={() => onChange(on ? value.filter((x) => x !== p) : [...value, p].sort((a, b) => a - b))}
          >
            {p + 1}.<span className="sr-only"> Stunde{times?.[p] ? `, ${times[p]}` : ''}</span>
          </button>
        );
      })}
    </div>
  );
}

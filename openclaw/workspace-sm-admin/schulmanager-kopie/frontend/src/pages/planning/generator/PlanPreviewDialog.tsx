import { useEffect, useMemo, useState } from 'react';
import { timetable as ttApi } from '../../../api/endpoints';
import type { TimetableView } from '../../../api/types';
import { Modal } from '../../../components/Modal';
import { SearchSelect, type SelectOption } from '../../../components/SearchSelect';
import { TimetableGrid } from '../../../components/TimetableGrid';
import { useSchoolYear, WeekNav } from '../../../components/WeekNav';
import { ErrorBox, Loading, SegmentedControl } from '../../../components/ui';
import { useApi } from '../../../hooks/useApi';
import { useCollection } from '../../../hooks/useCollection';
import { mondayOf, todayISO } from '../../../lib/dates';
import type { ViewKind } from './api';

type Mode = 'draft' | 'current';

/**
 * Stundenplan-Vorschau eines Entwurfs, einer Variante oder eines Plan-Stands als Klassen- bzw. Lehrkraftplan
 * (gemeinsames Raster `TimetableGrid`), wahlweise im Vergleich zum aktuellen Plan. Nichts wird gespeichert.
 */
export function PlanPreviewDialog({
  title,
  draftLabel,
  load,
  onClose,
}: {
  title: string;
  /** Beschriftung des Entwurfs im Umschalter, z. B. „Entwurf“ oder „Stand“ */
  draftLabel: string;
  load: (kind: ViewKind, ref: string, date: string) => Promise<TimetableView>;
  onClose: () => void;
}) {
  const classes = useCollection('classes').data ?? [];
  const teachers = useCollection('teachers').data ?? [];
  const [kind, setKind] = useState<ViewKind>('class');
  const [ref, setRef] = useState('');
  const [mode, setMode] = useState<Mode>('draft');
  const today = todayISO();
  const [monday, setMonday] = useState(mondayOf(today));
  const { year } = useSchoolYear(monday);
  const options: SelectOption[] = useMemo(
    () =>
      kind === 'class'
        ? classes.map((c) => ({ value: c.id, label: c.name || c.id }))
        : teachers.map((t) => ({ value: t.id, label: t.name || t.id, sub: t.id })),
    [kind, classes, teachers],
  );
  useEffect(() => {
    if (!options.some((o) => o.value === ref)) setRef(options[0]?.value ?? '');
  }, [options, ref]);
  const view = useApi(
    () => {
      if (!ref) return Promise.resolve(null);
      return mode === 'draft' ? load(kind, ref, monday) : ttApi.view(kind, ref, { date: monday });
    },
    [kind, ref, mode, monday],
    { live: mode === 'current' ? ['timetable'] : undefined },
  );
  return (
    <Modal title={title} onClose={onClose} size="lg">
      <div className="stack">
        <div className="row" style={{ flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div className="field" style={{ minWidth: 0 }}>
            <span className="field-label">Ansicht</span>
            <SegmentedControl
              label="Klasse oder Lehrkraft"
              value={kind}
              onChange={setKind}
              options={[
                { value: 'class', label: 'Klasse' },
                { value: 'teacher', label: 'Lehrkraft' },
              ]}
            />
          </div>
          <div className="field" style={{ minWidth: '12rem' }}>
            <SearchSelect options={options} value={ref} onChange={(v) => setRef(v ?? '')} label={kind === 'class' ? 'Klasse' : 'Lehrkraft'} />
          </div>
          <div className="field" style={{ minWidth: 0 }}>
            <span className="field-label">Plan</span>
            <SegmentedControl
              label="Entwurf oder aktueller Plan"
              value={mode}
              onChange={setMode}
              options={[
                { value: 'draft', label: draftLabel },
                { value: 'current', label: 'Aktuell' },
              ]}
            />
          </div>
          <div className="field" style={{ minWidth: 0 }}>
            <span className="field-label">Woche</span>
            <WeekNav value={monday} onChange={setMonday} year={year} info={view.data?.week_info} today={today} />
          </div>
        </div>
        {view.error ? <ErrorBox error={view.error} onRetry={view.reload} /> : null}
        {view.initialLoading && <Loading />}
        {view.data && <TimetableGrid view={view.data} />}
      </div>
    </Modal>
  );
}

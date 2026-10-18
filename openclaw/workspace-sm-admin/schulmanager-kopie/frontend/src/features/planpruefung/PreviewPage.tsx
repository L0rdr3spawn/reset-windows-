import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { timetable as ttApi } from '../../api/endpoints';
import type { TimetableKind } from '../../api/types';
import { AbbrList } from '../../components/Abbr';
import { Icon } from '../../components/Icon';
import { TimetableGrid } from '../../components/TimetableGrid';
import { SearchSelect, type SelectOption } from '../../components/SearchSelect';
import { useSchoolYear, WeekNav } from '../../components/WeekNav';
import { Alert, ErrorBox, Loading, SegmentedControl } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { useCollection } from '../../hooks/useCollection';
import { useTitle } from '../../hooks/misc';
import { mondayOf, todayISO } from '../../lib/dates';
import { proposalsApi } from './api';
import { impactText } from './logic';
import './planpruefung.css';

type Mode = 'draft' | 'current';

/** Stundenplan-Entwurf einer Variante: Klassen- bzw. Lehrkraftplan mit der Variante, im Vergleich zum aktuellen Plan. */
export default function PreviewPage() {
  const { paket, variante } = useParams<{ paket: string; variante: string }>();
  const pid = Number(paket);
  const vid = Number(variante);
  useTitle('Entwurf ansehen');
  const pkg = useApi((signal) => proposalsApi.get(pid, signal), [pid], { live: ['proposals'] });
  const variant = pkg.data?.variants?.find((v) => v.id === vid);
  const classes = useCollection('classes').data ?? [];
  const teachers = useCollection('teachers').data ?? [];
  const [kind, setKind] = useState<'class' | 'teacher'>('class');
  const [ref, setRef] = useState<string>('');
  const [mode, setMode] = useState<Mode>('draft');
  const today = todayISO();
  const [monday, setMonday] = useState(mondayOf(today));
  const { year } = useSchoolYear(monday);

  const options: SelectOption[] = useMemo(() => {
    const ids = kind === 'class' ? (variant?.affected_classes ?? []) : (variant?.affected_teachers ?? []);
    if (kind === 'class') return ids.map((id) => ({ value: id, label: classes.find((c) => c.id === id)?.name ?? id }));
    return ids.map((id) => ({ value: id, label: teachers.find((t) => t.id === id)?.name ?? id, sub: id }));
  }, [kind, variant, classes, teachers]);
  useEffect(() => {
    if (!options.some((o) => o.value === ref)) setRef(options[0]?.value ?? '');
  }, [options, ref]);
  useEffect(() => {
    if (variant && variant.affected_classes.length === 0 && variant.affected_teachers.length > 0) setKind('teacher');
  }, [variant]);

  const view = useApi(
    (signal) => {
      void signal;
      if (!ref) return Promise.resolve(null);
      return mode === 'draft' ? proposalsApi.draftView(pid, vid, kind, ref, monday) : ttApi.view(kind as TimetableKind, ref, { date: monday });
    },
    [pid, vid, kind, ref, mode, monday],
    { live: ['timetable'], enabled: !!variant },
  );

  if (pkg.error) return <ErrorBox error={pkg.error} onRetry={pkg.reload} />;
  if (!pkg.data) return <Loading />;
  if (!variant) return <Alert kind="warning" title="Variante nicht gefunden">Dieser Vorschlag ist nicht mehr verfügbar.</Alert>;
  const changesOfRef = variant.changes.filter((c) => (kind === 'class' ? c.classes.includes(ref) : c.teachers.includes(ref)));
  const open = pkg.data.status === 'offen';

  return (
    <div className="page">
      <div className="page-head">
        <h1>Entwurf: {variant.title}</h1>
        <Link to="/planung/vorschlaege" className="btn btn-sm">
          <Icon name="chevronLeft" /> Zurück zu den Vorschlägen
        </Link>
      </div>
      {!open && (
        <Alert kind="info" title="Dieser Vorschlag ist nicht mehr offen">
          Er wurde entschieden oder ersetzt.
        </Alert>
      )}
      <p className="small muted">{impactText(variant)} – es wird nichts gespeichert, solange Sie den Vorschlag nicht annehmen.</p>
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
          <SearchSelect options={options} value={ref} onChange={(v) => setRef(v ?? '')} label={kind === 'class' ? 'Betroffene Klasse' : 'Betroffene Lehrkraft'} />
        </div>
        <div className="field" style={{ minWidth: 0 }}>
          <span className="field-label">Plan</span>
          <SegmentedControl
            label="Entwurf oder aktueller Plan"
            value={mode}
            onChange={setMode}
            options={[
              { value: 'draft', label: 'Entwurf' },
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
      {view.data && (
        <div className="pp-preview-grid">
          <TimetableGrid view={view.data} />
          {changesOfRef.length > 0 && (
            <div className="card">
              <h3>Änderungen für {view.data.title}</h3>
              <ul className="pp-changes">
                {changesOfRef.map((c) => (
                  <li key={c.course_id}>
                    <strong>{c.label}</strong>
                    {c.classes.length > 0 && (
                      <>
                        {' '}
                        (<AbbrList kind="class" ids={c.classes} />)
                      </>
                    )}
                    {c.cover ? `: ${c.cover}` : `: ${c.from.join(', ') || '–'} → ${c.to.join(', ') || '–'}`}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

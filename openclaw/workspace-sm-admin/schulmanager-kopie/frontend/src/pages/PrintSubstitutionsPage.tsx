import { useSearchParams } from 'react-router-dom';
import { substitutions } from '../api/endpoints';
import { EntryTable } from '../components/EntryTable';
import { Icon } from '../components/Icon';
import { ErrorBox, Loading } from '../components/ui';
import { useApi } from '../hooks/useApi';
import { useSettings } from '../hooks/useCollection';
import { useTitle } from '../hooks/misc';
import { currentSchoolDay, formatDateTime, formatLong, isValidISO } from '../lib/dates';
import { NO_PLAN_SHORT, planMissing } from '../lib/planPeriods';
import { schoolDaysOf } from '../lib/weeks';
import { classAbsenceRows, withoutClassAbsences } from '../lib/substitution';

/**
 * Druckansicht Vertretungsplan (Aushang): öffentliche Sicht wie der Monitor (`public=1` – ohne Gründe, Aufsichten,
 * Warnungen; abwesende Lehrkräfte laut Einstellung nur Kürzel bzw. mit Name). Klassen nur mit gemeldeter
 * Abwesenheit, eine Zeile je Klasse (A-56).
 */
export default function PrintSubstitutionsPage() {
  const [params] = useSearchParams();
  const { data: settings } = useSettings();
  const date = isValidISO(params.get('datum')) ? (params.get('datum') as string) : currentSchoolDay(new Date(), schoolDaysOf(settings));
  const site = params.get('standort') ?? undefined;
  const classId = params.get('klasse') ?? undefined;
  const q = useApi(() => substitutions.day({ date, site, class_id: classId, public: true }), [date, site, classId], {
    live: ['substitutions', 'absences', 'overrides', 'settings'],
    liveDates: [date],
  });
  useTitle(`Vertretungsplan ${date}`);
  const p = q.data;
  const teachers = (p?.absent_teacher_details ?? []).map((d) => (d.name ? `${d.teacher} (${d.name})` : d.teacher));
  const entries = withoutClassAbsences(p?.entries ?? []);
  const classRows = classAbsenceRows(p?.absent_class_details);
  return (
    <div className="print-page">
      <div className="print-toolbar">
        <button type="button" className="btn btn-primary" onClick={() => window.print()}>
          <Icon name="print" /> Drucken
        </button>
        <button type="button" className="btn" onClick={() => window.close()}>
          Schließen
        </button>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!p && !q.error && <Loading />}
      {p && (
        <>
          <div className="print-header">
            <h1>
              Vertretungsplan {formatLong(date)}
              {p.week_no ? ` (Woche ${p.week_no})` : ''}
            </h1>
            <span>
              {settings?.school_name}
              {site ? ` · ${site}` : ''} · Stand {formatDateTime(new Date().toISOString())}
            </span>
          </div>
          {p.holiday && <p>{p.holiday}</p>}
          {!p.holiday && planMissing(p.week_info?.plan) && <p>{NO_PLAN_SHORT}</p>}
          {teachers.length > 0 && (
            <p className="small">
              <strong>Abwesende Lehrkräfte:</strong> {teachers.join(', ')}
            </p>
          )}
          {entries.length || classRows.length ? (
            <EntryTable entries={entries} classAbsences={classRows} caption={`Vertretungsplan ${date}`} />
          ) : (
            <p>Keine Vertretungen.</p>
          )}
        </>
      )}
    </div>
  );
}

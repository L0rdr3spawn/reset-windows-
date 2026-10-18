/**
 * `/fehlzeiten/:studentId` – Fehlzeiten eines Kindes im Schuljahr: Summen (Tage/Stunden entschuldigt, unentschuldigt,
 * offen; Verspätungen; früher gegangen), alle Einträge mit Status und die eingereichten Entschuldigungen/Atteste.
 * Personal (Klassenleitung, Lehrkräfte der Klasse, Sekretariat, Schulleitung) setzt den Status und prüft
 * Entschuldigungen; die Familie lädt schriftliche Entschuldigungen hoch und lädt das Formular herunter.
 */
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { studentAbsences as saApi } from '../../api/endpoints';
import { fileUrl } from '../../api/files';
import type { StudentAbsence, StudentAbsenceStatus } from '../../api/types';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton, ErrorBox, Loading } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useTitle } from '../../hooks/misc';
import { dateRangeLabel, formatDateTime } from '../../lib/dates';
import { isFamily } from '../../lib/permissions';
import { kindText, SickPhone, STATUS_LABEL, StatusBadge } from '../../pages/StudentAbsencesPage';
import { AbsenceHistory, AbsenceTimeline, reportLine } from './AbsenceHistory';
import { AbsenceStats } from './AbsenceStats';
import { documentsApi } from './api';
import { SubmitDocumentForm } from './components';
import { SupportSection } from './SupportSection';
import './students.css';

function Tile({ value, label, tone }: { value: number | string; label: string; tone?: 'ok' | 'bad' | 'open' }) {
  return (
    <div className={`card kpi${tone ? ` st-kpi-${tone}` : ''}`}>
      <span className="kpi-value">{value}</span>
      <span className="kpi-label">{label}</span>
    </div>
  );
}

export default function RecordPage() {
  const { studentId = '' } = useParams();
  const user = useUser();
  const toast = useToast();
  const family = isFamily(user);
  const q = useApi((signal) => saApi.record(studentId, signal), [studentId], { live: ['student_absences', 'student_documents'] });
  const [excuseFor, setExcuseFor] = useState<StudentAbsence | null>(null);
  const data = q.data;
  useTitle(data ? `Fehlzeiten ${data.student.name}` : 'Fehlzeiten');

  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!data) return <Loading />;
  const s = data.summary;
  // Minderjährige Schüler/innen sehen keine Melde- und Upload-Elemente (das erledigen die Eltern)
  const showForms = !family || !!data.can_report;

  const setStatus = async (a: StudentAbsence, st: StudentAbsenceStatus) => {
    try {
      await saApi.setStatus(a.id, st);
      toast.success(`${dateRangeLabel(a.date_from, a.date_to)}: ${STATUS_LABEL[st]}`);
      q.reload();
    } catch (e) {
      toast.error(e);
    }
  };
  const docsFor = (a: StudentAbsence) => data.documents.filter((d) => String(d.absence_id) === String(a.id));

  return (
    <div className="page stack">
      <div className="page-head">
        <div>
          <nav aria-label="Pfad" className="small">
            <Link to="/krankmeldungen">Krankmeldungen</Link> <span aria-hidden="true">›</span>{' '}
            <span className="muted">Fehlzeiten</span>
          </nav>
          <h1>
            Fehlzeiten {data.student.name} <span className="muted small">({data.student.class_id})</span>
          </h1>
          <p className="small muted" style={{ margin: 0 }}>
            Schuljahr seit {new Date(data.from).toLocaleDateString('de-DE')}
          </p>
        </div>
        {showForms && (
          <a className="btn" href={saApi.formUrl({ student_id: data.student.id })} target="_blank" rel="noopener">
            <Icon name="download" /> Formular „Schriftliche Entschuldigung“
          </a>
        )}
      </div>
      {showForms && <SickPhone />}
      <AbsenceStats studentId={data.student.id} />
      <SupportSection studentId={data.student.id} />
      <div className="grid grid-4">
        <Tile value={s.days} label="Fehltage gesamt" />
        <Tile value={s.days_excused} label="davon entschuldigt" tone="ok" />
        <Tile value={s.days_unexcused} label="davon unentschuldigt" tone={s.days_unexcused ? 'bad' : undefined} />
        <Tile value={s.days_open} label="noch offen" tone={s.days_open ? 'open' : undefined} />
        <Tile value={s.lessons} label="einzelne Fehlstunden" />
        <Tile value={s.late_count} label={`mal zu spät${s.late_minutes ? ` (${s.late_minutes} Min.)` : ''}`} tone={s.late_count ? 'open' : undefined} />
        <Tile value={s.early_count} label="mal früher gegangen" />
        <Tile value={s.open_count} label="Einträge ohne Entscheidung" tone={s.open_count ? 'open' : undefined} />
      </div>
      <section className="card" aria-labelledby="rec-h">
        <h2 id="rec-h">Alle Einträge</h2>
        {!data.entries.length ? (
          <p className="muted small">Keine Fehlzeiten in diesem Schuljahr.</p>
        ) : (
          <ul className="st-list">
            {data.entries.map((a) => {
              const docs = docsFor(a);
              return (
                <li key={a.id} className={`st-row${a.status === 'unentschuldigt' ? ' st-row-alert' : ''}`}>
                  <div className="st-row-main">
                    <strong>
                      {dateRangeLabel(a.date_from, a.date_to)} · {kindText(a)}
                    </strong>
                    <span className="small muted">
                      {a.periods?.length ? `${a.periods.map((p) => p + 1).join(', ')}. Std. · ` : a.school_days && a.kind !== 'verspaetung' && a.kind !== 'frueh' ? `${a.school_days} Schultag${a.school_days === 1 ? '' : 'e'} · ` : ''}
                      {a.reason ? `${a.reason} · ` : a.reason_hidden ? 'Grund vertraulich · ' : ''}
                      {a.source_label} von {a.reported_by_name || '–'}
                      {a.excused_by_name ? ` · bearbeitet von ${a.excused_by_name}${a.excused_at ? ` (${formatDateTime(a.excused_at)})` : ''}` : ''}
                    </span>
                    {a.history && a.reported_at && <span className="small">{reportLine(a, 'gemeldet')}</span>}
                    <AbsenceHistory events={a.history} label="Verlauf der Meldung" />
                    {docs.length > 0 && (
                      <span className="small">
                        <Icon name="upload" />{' '}
                        {docs.map((d) => `${d.category_label} (${d.status_label ?? d.status})`).join(', ')}
                      </span>
                    )}
                  </div>
                  <div className="st-row-side">
                    <StatusBadge a={a} />
                    {data.can_manage && (
                      <>
                        <AsyncButton className="btn btn-sm" disabled={a.status === 'entschuldigt'} onClick={() => setStatus(a, 'entschuldigt')}>
                          <Icon name="check" /> {a.kind === 'beurlaubung' ? 'genehmigen' : 'entschuldigt'}
                        </AsyncButton>
                        {a.kind !== 'beurlaubung' && (
                          <AsyncButton className="btn btn-sm btn-ghost" disabled={a.status === 'teilweise'} onClick={() => setStatus(a, 'teilweise')} title="angerufen, schriftliche Entschuldigung fehlt">
                            teilweise
                          </AsyncButton>
                        )}
                        <AsyncButton className="btn btn-sm btn-ghost" disabled={a.status === 'unentschuldigt'} onClick={() => setStatus(a, 'unentschuldigt')}>
                          <Icon name="x" /> {a.kind === 'beurlaubung' ? 'ablehnen' : 'unentschuldigt'}
                        </AsyncButton>
                      </>
                    )}
                    {family && showForms && a.status !== 'entschuldigt' && (
                      <button type="button" className="btn btn-sm" onClick={() => setExcuseFor(a)}>
                        <Icon name="upload" /> Entschuldigung hochladen
                      </button>
                    )}
                    {showForms && (
                      <a className="btn btn-sm btn-ghost" href={a.kind === 'beurlaubung' ? saApi.leaveFormUrl({ absence_id: a.id }) : saApi.formUrl({ absence_id: a.id })} target="_blank" rel="noopener" title="Formular für diesen Eintrag">
                        <Icon name="print" />
                        <span className="sr-only">Formular für {dateRangeLabel(a.date_from, a.date_to)}</span>
                      </a>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>
      {!!data.withdrawn?.length && (
        <section className="card" aria-labelledby="rec-withdrawn">
          <h2 id="rec-withdrawn">
            Zurückgenommene Meldungen
            <HelpTip>Das Protokoll bleibt erhalten, auch wenn eine Meldung zurückgenommen oder gelöscht wird.</HelpTip>
          </h2>
          {data.withdrawn.map((w) => (
            <AbsenceTimeline key={w.absence_id} events={w.history} />
          ))}
        </section>
      )}
      {data.documents.length > 0 && (
        <section className="card" aria-labelledby="rec-docs">
          <h2 id="rec-docs">
            Entschuldigungen &amp; Atteste
            {!family && <HelpTip>Wird eine Entschuldigung oder ein Attest zu einem Eintrag als „geprüft“ markiert, gilt der Eintrag automatisch als entschuldigt.</HelpTip>}
          </h2>
          <ul className="st-list">
            {data.documents.map((d) => (
              <li key={d.id} className="st-row">
                <div className="st-row-main">
                  <strong>{d.title || d.category_label}</strong>
                  <span className="small muted">
                    {d.category_label} · {formatDateTime(d.created_at)}
                  </span>
                </div>
                <div className="st-row-side">
                  <span className={`badge ${d.status === 'geprueft' ? 'badge-success' : d.status === 'abgelehnt' ? 'badge-danger' : 'badge-warning'}`}>{d.status_label ?? d.status}</span>
                  {d.file && (
                    <a className="btn btn-sm btn-ghost" href={fileUrl(d.file.id, { inline: true })} target="_blank" rel="noopener noreferrer">
                      <Icon name="eye" /> Ansehen
                    </a>
                  )}
                  {!family && d.can_handle !== false && d.status !== 'geprueft' && (
                    <AsyncButton
                      className="btn btn-sm"
                      onClick={async () => {
                        try {
                          await documentsApi.handle(d.id, { status: 'geprueft' });
                          toast.success(d.absence_id ? 'Geprüft – die Fehlzeit ist jetzt entschuldigt' : 'Geprüft');
                          q.reload();
                        } catch (e) {
                          toast.error(e);
                        }
                      }}
                    >
                      <Icon name="check" /> Geprüft
                    </AsyncButton>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
      {family && showForms && (
        <Alert kind="info">
          Schriftliche Entschuldigung: Formular herunterladen, unterschreiben und als Foto oder PDF hochladen oder in der Schule abgeben.
        </Alert>
      )}
      {excuseFor && (
        <Modal title={`Entschuldigung für ${dateRangeLabel(excuseFor.date_from, excuseFor.date_to)}`} onClose={() => setExcuseFor(null)}>
          <SubmitDocumentForm
            studentId={user.role === 'eltern' ? data.student.id : undefined}
            absences={data.entries}
            absenceId={Number(excuseFor.id)}
            defaultCategory="entschuldigung"
            onDone={() => {
              setExcuseFor(null);
              q.reload();
            }}
          />
        </Modal>
      )}
    </div>
  );
}

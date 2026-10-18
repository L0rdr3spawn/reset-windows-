/**
 * Krankmeldungen für Schüler/innen und Eltern (je Kind) – Teil der Seite `/krankmeldungen`. Karten sauber
 * untereinander, jedes Element nur einmal: 1. Melden (`ReportCard`: nur Eltern und volljährige Schüler/innen),
 * 2. Meldungen – eine Liste; Offenes (fehlendes Attest, fehlende Entschuldigung, beantragte Beurlaubung) steht oben
 * direkt an der Meldung, mit Upload und den Aktionen (zurücknehmen, früher zurück, verlängern, …) –, dazu die
 * Dokumente, 3. Statistik. Minderjährige Schüler/innen sehen nur 2 und 3 (ohne Melde- und Upload-Elemente):
 * Krankmeldung, Beurlaubung und Dokumente übernehmen die Eltern. (Früher „Meine Übersicht“.)
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { studentAbsences as saApi } from '../../api/endpoints';
import type { StudentAbsence } from '../../api/types';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { ErrorBox, Loading } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { dateRangeLabel } from '../../lib/dates';
import { studentSelfApi } from './api';
import { AbsenceRowActions } from './AbsenceActions';
import { AbsenceList, DocumentList, SubmitDocumentForm } from './components';
import { attestUploadWanted, sortAbsences } from './logic';
import { ReportCard } from './ReportCard';
import './students.css';
import type { DocCategory, StudentDocument, StudentOverview } from './types';
import { AbsenceStats } from './AbsenceStats';
import { ChildSelect, useFamilyChild } from './useChild';

/** Daten der Familien-Übersicht eines Kindes (`/me/student-overview`), live aktualisiert. */
export function useStudentOverview() {
  const { parent, child, setChild, kids } = useFamilyChild();
  const q = useApi<StudentOverview>((signal) => studentSelfApi.overview(child, signal), [child], {
    live: ['student_absences', 'student_documents', 'exams'],
    keepPrevious: true,
  });
  return { q, parent, child, setChild, kids };
}

type OpenKind = 'attest' | 'excuse' | 'leave';
type AbsenceRow = StudentOverview['absences'][number];

/** Eingereichte, noch nicht geprüfte Unterlagen zu einer Meldung (Attest, Entschuldigung, Antrag). */
function pendingDocs(a: AbsenceRow, docs: StudentDocument[]): StudentDocument[] {
  return docs.filter((d) => d.absence_id === Number(a.id) && d.status === 'eingegangen' && ['attest', 'entschuldigung', 'beurlaubung'].includes(d.category));
}

/** Offener Punkt einer Meldung: Attest fehlt/nötig, Entschuldigung fehlt, Beurlaubung wartet auf Entscheidung. */
function openKind(a: AbsenceRow, docs: StudentDocument[]): OpenKind | null {
  if (a.kind === 'beurlaubung') return (a.status === 'gemeldet' || a.status === 'teilweise') && !pendingDocs(a, docs).length ? 'leave' : null;
  if ((a.kind ?? 'krank') !== 'krank') return null;
  if (attestUploadWanted(a)) return 'attest';
  if (a.status === 'entschuldigt' || a.status === 'unentschuldigt') return null;
  if (a.attest?.state === 'eingereicht' || a.attest?.state === 'geprueft' || pendingDocs(a, docs).length) return null;
  return 'excuse';
}

const OPEN_TITLE: Record<OpenKind, string> = { attest: 'Attest', excuse: 'Entschuldigung', leave: 'Beurlaubung' };
const OPEN_BUTTON: Record<OpenKind, string> = { attest: 'Attest hochladen', excuse: 'Entschuldigung hochladen', leave: 'Antrag hochladen' };
const OPEN_CATEGORY: Record<OpenKind, DocCategory> = { attest: 'attest', excuse: 'entschuldigung', leave: 'beurlaubung' };

export function FamilyAbsencesSection() {
  const { q, parent, child, setChild, kids } = useStudentOverview();
  const [upload, setUpload] = useState<{ absence: StudentAbsence; kind: OpenKind } | null>(null);
  const ov = q.data;
  const docs = ov?.documents ?? [];
  const kindOf = (a: AbsenceRow): OpenKind | null => (ov?.can_submit_documents ? openKind(a, docs) : null);
  // Offenes zuerst, dann wie bisher (fehlendes Attest, neueste zuerst)
  const absences = ov ? sortAbsences(ov.absences).sort((x, y) => Number(!!kindOf(y)) - Number(!!kindOf(x))) : [];

  return (
    <div className="stack st-page">
      {parent && <ChildSelect kids={ov?.children ?? kids} value={ov?.student.id ?? child} onChange={setChild} />}
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {ov && (
        <>
          <p className="small muted" style={{ margin: 0 }} hidden={parent && (ov.children.length ?? 0) > 1}>
            {ov.student.name} · Klasse {ov.student.class_id}
            {ov.student.class_name && ov.student.class_name !== ov.student.class_id ? ` (${ov.student.class_name})` : ''}
            {ov.student.adult ? ' · volljährig' : ''}
          </p>
          {/* 1. Melden – nur Eltern und volljährige Schüler/innen; Minderjährige sehen keine Melde-Elemente */}
          {ov.can_report && <ReportCard key={`report-${ov.student.id}`} ov={ov} onDone={q.reload} />}
          {/* 2. Meldungen (Offenes oben, direkt an der Meldung) mit Dokumenten */}
          <section className="card" aria-labelledby="st-abs-h">
            <div className="card-head">
              <h2 id="st-abs-h" className="with-help">
                {ov.can_report ? 'Meldungen' : 'Meine Fehlzeiten'}
                {!ov.can_report && !parent && (
                  <HelpTip label="Hilfe zu Krankmeldungen">Krankmeldung, Beurlaubung und Dokumente übernehmen Ihre Eltern. Werden Sie volljährig, schaltet das Sekretariat Ihr Konto dafür frei.</HelpTip>
                )}
              </h2>
              {!ov.absences_hidden && (
                <Link className="btn btn-sm" to={`/fehlzeiten/${encodeURIComponent(ov.student.id)}`}>
                  Fehlzeiten-Übersicht
                </Link>
              )}
            </div>
            {ov.absences_hidden ? (
              <p className="small muted">{parent ? 'Ihr Kind ist volljährig; Krankmeldungen sehen Sie nur mit seiner Freigabe.' : 'Keine Krankmeldungen sichtbar.'}</p>
            ) : (
              <AbsenceList
                rows={absences}
                hint={(a) => {
                  const kind = kindOf(a as AbsenceRow);
                  if (!kind) return null;
                  return kind === 'attest'
                    ? `Attest – ab ${ov.sick_note_after_days} Schultagen braucht die Schule ein ärztliches Attest.`
                    : kind === 'excuse'
                      ? 'Entschuldigung – bitte die unterschriebene Entschuldigung einreichen.'
                      : 'Beurlaubung – beantragt, die Klassenleitung entscheidet. Den unterschriebenen Antrag bitte einreichen.';
                }}
                note={(a) => (pendingDocs(a as AbsenceRow, docs).length ? 'Unterlagen eingereicht – wird geprüft' : null)}
                primary={(a) => {
                  const kind = kindOf(a as AbsenceRow);
                  if (!kind) return null;
                  return (
                    <>
                      <button type="button" className="btn btn-sm btn-primary" onClick={() => setUpload({ absence: a, kind })}>
                        <Icon name="upload" /> {OPEN_BUTTON[kind]}
                      </button>
                      {kind !== 'attest' && (
                        <a className="btn btn-sm btn-ghost" href={kind === 'excuse' ? saApi.formUrl({ absence_id: a.id }) : saApi.leaveFormUrl({ absence_id: a.id })} target="_blank" rel="noopener">
                          <Icon name="download" /> Vordruck
                        </a>
                      )}
                    </>
                  );
                }}
                actions={(a) => {
                  const row = a as AbsenceRow;
                  const later = ov.can_submit_documents && !kindOf(row) && (a.status === 'gemeldet' || a.status === 'teilweise') && ['krank', 'beurlaubung'].includes(a.kind ?? 'krank');
                  return (
                    <AbsenceRowActions
                      a={a}
                      ov={ov}
                      onChanged={q.reload}
                      onUpload={later ? () => setUpload({ absence: a, kind: a.kind === 'beurlaubung' ? 'leave' : row.attest?.state === 'eingereicht' ? 'attest' : 'excuse' }) : undefined}
                    />
                  );
                }}
              />
            )}
            {(ov.documents.length > 0 || ov.can_submit_documents) && (
              <details className="st-details">
                <summary>
                  Dokumente ({ov.documents.length}){ov.can_submit_documents ? ' und einreichen' : ''}
                </summary>
                <DocumentList docs={ov.documents} onChanged={q.reload} />
                {ov.can_submit_documents && <SubmitDocumentForm studentId={parent ? ov.student.id : undefined} absences={ov.absences} onDone={q.reload} />}
              </details>
            )}
            {ov.documents_hidden && <p className="small muted">Ihr Kind ist volljährig und reicht Atteste und Dokumente selbst ein.</p>}
          </section>
          {/* 3. Statistik */}
          {!ov.absences_hidden && <AbsenceStats key={`stats-${ov.student.id}`} studentId={ov.student.id} />}
        </>
      )}
      {upload && ov && (
        <Modal title={`${upload.kind === 'leave' ? 'Beurlaubungsantrag' : OPEN_TITLE[upload.kind]} für ${dateRangeLabel(upload.absence.date_from, upload.absence.date_to)}`} onClose={() => setUpload(null)}>
          <SubmitDocumentForm
            studentId={parent ? ov.student.id : undefined}
            absences={ov.absences}
            absenceId={Number(upload.absence.id)}
            defaultCategory={OPEN_CATEGORY[upload.kind]}
            onDone={() => {
              setUpload(null);
              q.reload();
            }}
          />
        </Modal>
      )}
    </div>
  );
}

/**
 * „Atteste & Dokumente“ (`/dokumente`) für Sekretariat, Schulleitung und Klassenleitungen: Prüf-Eingang
 * (geprüft/abgelehnt mit Vermerk), Krankmeldungen mit fehlendem Attest (Papier-Attest vermerken, Eltern
 * anschreiben) und alle Dokumente. Fachlehrkräfte sehen hier nichts (Backend-Scope `class_teacher`).
 */
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import type { StudentAbsence } from '../../api/types';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { AsyncButton, Empty, ErrorBox, Field, Loading, Tabs } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useTitle } from '../../hooks/misc';
import { addDays, dateRangeLabel, formatDate, todayISO } from '../../lib/dates';
import { documentsApi } from './api';
import { AttestBadge, DocumentList, SubmitDocumentForm } from './components';
import { sortInbox } from './logic';
import './students.css';
import type { DocStatus, StudentDocument } from './types';

type Tab = 'eingang' | 'fehlt' | 'alle';

function matches(q: string, ...values: (string | null | undefined)[]): boolean {
  const s = q.trim().toLowerCase();
  return !s || values.some((v) => (v ?? '').toLowerCase().includes(s));
}

function RejectDialog({ doc, onClose, onDone }: { doc: StudentDocument; onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const [note, setNote] = useState(doc.note);
  return (
    <Modal
      title={`„${doc.title}“ ablehnen`}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton
            className="btn btn-danger"
            disabled={!note.trim()}
            onClick={async () => {
              try {
                await documentsApi.handle(doc.id, { status: 'abgelehnt', note: note.trim() });
                toast.success('Abgelehnt – die Einreichenden sehen die Begründung.');
                onDone();
              } catch (e) {
                toast.error(errorMessage(e));
              }
            }}
          >
            Ablehnen
          </AsyncButton>
        </>
      }
    >
      <Field label="Begründung (für die Familie sichtbar)" htmlFor="st-reject" hint="z. B. „Stempel/Unterschrift fehlt“, „Zeitraum passt nicht“.">
        <textarea id="st-reject" rows={3} value={note} maxLength={1000} onChange={(e) => setNote(e.target.value)} autoFocus />
      </Field>
    </Modal>
  );
}

export default function DocumentsPage() {
  useTitle('Atteste & Dokumente');
  const toast = useToast();
  const [tab, setTab] = useState<Tab>('eingang');
  const [search, setSearch] = useState('');
  const [rejecting, setRejecting] = useState<StudentDocument | null>(null);
  const [paperFor, setPaperFor] = useState<StudentAbsence | null>(null);
  const status: DocStatus | '' = tab === 'eingang' ? 'eingegangen' : '';
  const docs = useApi((signal) => documentsApi.list({ status }, signal), [status], { enabled: tab !== 'fehlt', live: ['student_documents'], keepPrevious: true });
  const missing = useApi((signal) => documentsApi.missingAttests(addDays(todayISO(), -60), signal), [], { live: ['student_absences', 'student_documents'] });
  const summary = useApi((signal) => documentsApi.summary(signal), [], { live: ['student_documents', 'student_absences'] });

  const list = useMemo(() => sortInbox((docs.data ?? []).filter((d) => matches(search, d.student_name, d.class_id, d.title, d.category_label))), [docs.data, search]);
  const missingRows = useMemo(() => (missing.data ?? []).filter((a) => matches(search, a.student_name, a.class_id)), [missing.data, search]);

  const approve = async (d: StudentDocument) => {
    try {
      await documentsApi.handle(d.id, { status: 'geprueft' });
      toast.success(`${d.student_name}: ${d.category_label} geprüft`);
      docs.reload();
      summary.reload();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  const actions = (d: StudentDocument) =>
    d.can_handle ? (
      <>
        {d.status !== 'geprueft' && (
          <AsyncButton className="btn btn-sm" onClick={() => approve(d)}>
            <Icon name="check" /> Geprüft
          </AsyncButton>
        )}
        {d.status !== 'abgelehnt' && (
          <button type="button" className="btn btn-sm btn-ghost" onClick={() => setRejecting(d)}>
            <Icon name="x" /> Ablehnen
          </button>
        )}
      </>
    ) : null;

  const open = summary.data?.open ?? 0;
  const miss = summary.data?.attest_missing ?? 0;
  return (
    <div className="page st-page">
      <div className="page-head">
        <h1>Atteste &amp; Dokumente</h1>
      </div>
      <p className="small muted">
        Atteste sehen nur Sekretariat, Schulleitung und Klassenleitung; jeder Zugriff wird protokolliert.
      </p>
      <Tabs
        label="Ansicht"
        active={tab}
        onChange={setTab}
        tabs={[
          { key: 'eingang', label: `Eingang${open ? ` (${open})` : ''}` },
          { key: 'fehlt', label: `Attest fehlt${miss ? ` (${miss})` : ''}` },
          { key: 'alle', label: 'Alle Dokumente' },
        ]}
      />
      <div className="toolbar">
        <Field label="Suche" htmlFor="st-search">
          <input id="st-search" type="search" value={search} placeholder="Name, Klasse oder Titel" style={{ minWidth: 'min(320px, 100%)' }} onChange={(e) => setSearch(e.target.value)} />
        </Field>
      </div>
      {tab !== 'fehlt' ? (
        <section className="card" aria-label={tab === 'eingang' ? 'Eingang' : 'Alle Dokumente'}>
          {docs.error ? <ErrorBox error={docs.error} onRetry={docs.reload} /> : null}
          {docs.initialLoading && <Loading />}
          {docs.data && !list.length ? (
            <Empty icon="checkCircle">{tab === 'eingang' ? 'Keine neuen Dokumente – alles bearbeitet.' : 'Keine Dokumente gefunden.'}</Empty>
          ) : (
            <DocumentList docs={list} showStudent onChanged={docs.reload} actions={actions} />
          )}
        </section>
      ) : (
        <section className="card" aria-label="Attest fehlt">
          {missing.error ? <ErrorBox error={missing.error} onRetry={missing.reload} /> : null}
          {missing.initialLoading && <Loading />}
          {missing.data && !missingRows.length ? (
            <Empty icon="checkCircle">Keine fehlenden Atteste.</Empty>
          ) : (
            <ul className="st-list" aria-label="Krankmeldungen ohne Attest">
              {missingRows.map((a) => (
                <li key={a.id} className="st-row st-row-alert">
                  <div className="st-row-main">
                    <strong>
                      {a.student_name} ({a.class_id ?? '–'})
                    </strong>
                    <span className="small muted">
                      {dateRangeLabel(a.date_from, a.date_to)} · {a.attest?.school_days} Schultage
                      {a.attest?.due ? ` · fällig seit ${formatDate(a.attest.due)}` : ''} · gemeldet von {a.reported_by_name || '–'}
                    </span>
                  </div>
                  <div className="st-row-side">
                    <AttestBadge attest={a.attest} />
                    <button type="button" className="btn btn-sm" onClick={() => setPaperFor(a)}>
                      <Icon name="check" /> Papier-Attest vermerken
                    </button>
                    <Link
                      className="btn btn-sm btn-ghost"
                      to={a.student_adult ? `/nachrichten/neu?schueler=${encodeURIComponent(a.student_id)}` : `/nachrichten/neu?eltern=${encodeURIComponent(a.student_id)}`}
                    >
                      <Icon name="mail" /> {a.student_adult ? 'Schüler/in schreiben' : 'Eltern schreiben'}
                    </Link>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
      {rejecting && (
        <RejectDialog
          doc={rejecting}
          onClose={() => setRejecting(null)}
          onDone={() => {
            setRejecting(null);
            docs.reload();
            summary.reload();
          }}
        />
      )}
      {paperFor && (
        <Modal title={`Attest für ${paperFor.student_name ?? paperFor.student_id} (${dateRangeLabel(paperFor.date_from, paperFor.date_to)})`} onClose={() => setPaperFor(null)}>
          <SubmitDocumentForm
            studentId={paperFor.student_id}
            absences={[paperFor]}
            absenceId={Number(paperFor.id)}
            allowPaper
            onDone={() => {
              setPaperFor(null);
              missing.reload();
              summary.reload();
            }}
          />
        </Modal>
      )}
    </div>
  );
}

/**
 * Bausteine der Schüler-Selbstbedienung: Attest-Badge, Liste der Meldungen, Dokumentliste und Einreichen-Formular
 * (Krankmelden selbst: ReportCard.tsx).
 */
import { useId, useState, type ReactNode } from 'react';
import { errorMessage } from '../../api/client';
import { fileUrl, type StoredFileInfo } from '../../api/files';
import type { AttestInfo, StudentAbsence } from '../../api/types';
import { FileUpload } from '../../components/FileUpload';
import { Icon } from '../../components/Icon';
import { AsyncButton, Field } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { dateRangeLabel, formatDate, formatDateTime } from '../../lib/dates';
import { documentsApi } from './api';
import { attestBadgeClass, CATEGORY_LABELS, docStatusBadgeClass, periodsLabel, showAttest } from './logic';
import type { DocCategory, StudentDocument } from './types';

export function AttestBadge({ attest }: { attest?: AttestInfo | null }) {
  if (!attest || attest.state === 'nicht_noetig') return null;
  const due = attest.state === 'erforderlich' && attest.due ? ` bis ${formatDate(attest.due)}` : '';
  return (
    <span className={`badge ${attestBadgeClass(attest.state)}`} title={`Attestpflicht ab ${attest.school_days} Schultagen`}>
      {attest.state === 'fehlt' && <Icon name="alert" />} {attest.label}
      {due}
    </span>
  );
}

// ---------------------------------------------------------------------------------------------- Krankmeldungen
/** Kurzer Status einer Meldung (Beurlaubungen: beantragt/genehmigt/abgelehnt). */
export function absenceStatusText(a: Pick<StudentAbsence, 'kind' | 'status' | 'status_label'>): string {
  if (a.kind === 'beurlaubung' && a.status_label) return a.status_label;
  return a.status === 'teilweise' ? 'teilweise entschuldigt' : a.status ?? '';
}

export function absenceStatusBadge(a: Pick<StudentAbsence, 'kind' | 'status'>): string {
  if (a.kind === 'beurlaubung') return a.status === 'entschuldigt' ? 'badge-success' : a.status === 'unentschuldigt' ? 'badge-danger' : 'badge-info';
  return a.status === 'entschuldigt' ? 'badge-success' : a.status === 'unentschuldigt' ? 'badge-danger' : a.status === 'teilweise' ? 'badge-info' : 'badge-warning';
}

/**
 * Meldungen eines Kindes in einer Liste: Zeitraum, Art, Status, Attest-Zustand. Offene Punkte (`hint`) stehen direkt an
 * der Meldung, mit Hauptknopf (`primary`) und weiteren Aktionen (`actions`, unter der Zeile).
 */
export function AbsenceList({
  rows,
  hint,
  primary,
  actions,
  note,
}: {
  rows: (StudentAbsence & { attest?: AttestInfo })[];
  /** Offener Punkt dieser Meldung (z. B. „Attest fehlt noch“) – hebt die Zeile hervor */
  hint?: (a: StudentAbsence) => string | null;
  primary?: (a: StudentAbsence) => ReactNode;
  actions?: (a: StudentAbsence) => ReactNode;
  /** zusätzlicher Statustext (z. B. „Unterlagen eingereicht – wird geprüft“) */
  note?: (a: StudentAbsence) => string | null;
}) {
  if (!rows.length) return <p className="muted small">Keine Meldungen in den letzten 60 Tagen.</p>;
  return (
    <ul className="st-list" aria-label="Meldungen">
      {rows.map((a) => {
        const open = hint?.(a) ?? null;
        const status = note?.(a) ?? null;
        return (
          <li key={a.id} className={`st-row${a.attest?.state === 'fehlt' ? ' st-row-alert' : open ? ' st-row-open' : ''}`}>
            <div className="st-row-main">
              <strong>{dateRangeLabel(a.date_from, a.date_to)}</strong>
              <span className="small muted">
                {periodsLabel(a.periods)}
                {a.reason ? ` · ${a.reason}` : ''} · gemeldet von {a.reported_by_name || '–'}
              </span>
              {open && (
                <span className="small">
                  <Icon name="alert" /> <strong>Offen:</strong> {open}
                </span>
              )}
              {status && (
                <span className="small muted">
                  <Icon name="info" /> {status}
                </span>
              )}
            </div>
            <div className="st-row-side">
              {a.kind && a.kind !== 'krank' && <span className="badge">{a.kind_label}</span>}
              <span className={`badge ${absenceStatusBadge(a)}`} title={a.status_label}>
                {absenceStatusText(a)}
              </span>
              {showAttest(a) && <AttestBadge attest={a.attest} />}
              {primary?.(a)}
            </div>
            {actions?.(a)}
          </li>
        );
      })}
    </ul>
  );
}

// ---------------------------------------------------------------------------------------------- Dokumente
export function DocumentList({
  docs,
  onChanged,
  showStudent = false,
  actions,
}: {
  docs: StudentDocument[];
  onChanged: () => void;
  showStudent?: boolean;
  actions?: (d: StudentDocument) => ReactNode;
}) {
  const toast = useToast();
  if (!docs.length) return <p className="muted small">Noch keine Dokumente eingereicht.</p>;
  return (
    <ul className="st-list" aria-label="Dokumente">
      {docs.map((d) => (
        <li key={d.id} className="st-row">
          <div className="st-row-main">
            <strong className="st-title">{d.title}</strong>
            <span className="small muted">
              {showStudent ? `${d.student_name} (${d.class_id ?? '–'}) · ` : ''}
              {d.category_label} · {formatDateTime(d.created_at)} · von {d.uploaded_by_name || '–'}
            </span>
            {d.note && (
              <span className="small">
                <strong>Vermerk:</strong> {d.note}
              </span>
            )}
            {d.handled_by_name && d.status !== 'eingegangen' && (
              <span className="small muted">
                {d.status_label} von {d.handled_by_name}
                {d.handled_at ? `, ${formatDateTime(d.handled_at)}` : ''}
              </span>
            )}
          </div>
          <div className="st-row-side">
            <span className={`badge ${docStatusBadgeClass(d.status)}`}>{d.status_label}</span>
            {d.file ? (
              <>
                <a className="btn btn-sm" href={fileUrl(d.file.id, { inline: d.file.inline })} target="_blank" rel="noopener noreferrer">
                  <Icon name="eye" /> <span className="sr-only">{d.title}: </span>Ansehen
                </a>
                <a className="btn btn-sm btn-ghost" href={fileUrl(d.file.id)} download>
                  <Icon name="download" /> <span className="sr-only">{d.title}: </span>Herunterladen
                </a>
              </>
            ) : (
              <span className="badge">Papier</span>
            )}
            {actions?.(d)}
            {d.can_delete && (
              <AsyncButton
                className="btn btn-sm btn-ghost"
                title="Dokument löschen"
                confirm={`„${d.title}“ wirklich löschen?`}
                onClick={async () => {
                  try {
                    await documentsApi.remove(d.id);
                    toast.success('Dokument gelöscht');
                    onChanged();
                  } catch (e) {
                    toast.error(errorMessage(e));
                  }
                }}
              >
                <Icon name="trash" />
                <span className="sr-only">„{d.title}“ löschen</span>
              </AsyncButton>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}

export function SubmitDocumentForm({
  studentId,
  absences,
  absenceId,
  allowPaper = false,
  defaultCategory = 'attest',
  onDone,
}: {
  studentId?: string;
  absences: StudentAbsence[];
  absenceId?: number | null;
  /** vorausgewählte Art (z. B. „entschuldigung“ beim Knopf „Entschuldigung hochladen“) */
  defaultCategory?: DocCategory;
  /** Personal: ohne Datei „Papier-Attest liegt vor“ vermerken */
  allowPaper?: boolean;
  onDone: () => void;
}) {
  const toast = useToast();
  // eigene IDs je Formular: dasselbe Formular steckt auch im (zugeklappten) „Dokumente“-Bereich – doppelte IDs ließen Beschriftungen ins Leere fokussieren
  const uid = useId();
  const [category, setCategory] = useState<DocCategory>(defaultCategory);
  const [title, setTitle] = useState('');
  const [absence, setAbsence] = useState<string>(absenceId ? String(absenceId) : '');
  const [file, setFile] = useState<StoredFileInfo | null>(null);
  const [note, setNote] = useState('');
  const [resetKey, setResetKey] = useState(0);
  const paper = allowPaper && !file;

  const submit = async () => {
    if (!file && !allowPaper) {
      toast.warning('Bitte zuerst eine Datei (PDF oder Foto) hochladen.');
      return;
    }
    try {
      await documentsApi.submit({
        student_id: studentId,
        category,
        title: title.trim() || (paper ? 'Papier-Attest liegt vor' : ''),
        absence_id: absence ? Number(absence) : null,
        file_id: file?.id ?? null,
        note: note.trim(),
      });
      toast.success(paper ? 'Vermerk gespeichert' : 'Dokument eingereicht – die Schule prüft es.');
      setTitle('');
      setNote('');
      setFile(null);
      setResetKey((k) => k + 1);
      onDone();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  return (
    <div className="stack st-submit">
      <div className="form-grid">
        <Field label="Art" htmlFor={`${uid}-cat`}>
          <select id={`${uid}-cat`} value={category} onChange={(e) => setCategory(e.target.value as DocCategory)}>
            {Object.entries(CATEGORY_LABELS).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Zu Krankmeldung (optional)" htmlFor={`${uid}-abs`}>
          <select id={`${uid}-abs`} value={absence} onChange={(e) => setAbsence(e.target.value)}>
            <option value="">– keine –</option>
            {absences.map((a) => (
              <option key={a.id} value={String(a.id)}>
                {dateRangeLabel(a.date_from, a.date_to)}
                {a.attest?.missing ? ' (Attest fehlt)' : ''}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <Field label="Titel (optional)" htmlFor={`${uid}-title`} hint="Wird verschlüsselt gespeichert.">
        <input id={`${uid}-title`} type="text" value={title} maxLength={200} placeholder={CATEGORY_LABELS[category]} onChange={(e) => setTitle(e.target.value)} />
      </Field>
      <FileUpload
        key={resetKey}
        purpose="student_document"
        multiple={false}
        accept=".pdf,.jpg,.jpeg,.png,.heic,.webp"
        label="Datei (PDF oder Foto)"
        hint={allowPaper ? 'Ohne Datei wird nur vermerkt, dass das Original im Sekretariat vorliegt.' : 'Fotos vom Handy gehen auch – bitte gut lesbar.'}
        onChange={(files) => setFile(files[0] ?? null)}
      />
      <Field label="Bemerkung (optional)" htmlFor={`${uid}-note`}>
        <input id={`${uid}-note`} type="text" value={note} maxLength={1000} onChange={(e) => setNote(e.target.value)} />
      </Field>
      <div className="row-end st-submit-bar">
        {!file && !allowPaper && <span className="small muted st-submit-hint">Erst die Datei hochladen, dann einreichen.</span>}
        <AsyncButton className="btn btn-primary" onClick={submit}>
          <Icon name="upload" /> {paper ? 'Papier-Attest vermerken' : 'Einreichen'}
        </AsyncButton>
      </div>
    </div>
  );
}

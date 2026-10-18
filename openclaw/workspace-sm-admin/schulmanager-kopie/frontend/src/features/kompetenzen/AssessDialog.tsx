/** Dialog: Stufe einer Kompetenz setzen (Datum, Nachweis, Kommentar) bzw. eine Selbsteinschätzung bestätigen. */
import { useState } from 'react';
import { Modal } from '../../components/Modal';
import { AsyncButton, Field } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { todayISO } from '../../lib/dates';
import { compApi, type CompetencyState, type EvidenceType, type FrameworkState } from './api';
import { EVIDENCE_LABEL, levelLabel } from './logic';

export function AssessDialog({
  fw,
  comp,
  studentId,
  studentName,
  confirmSelf,
  onClose,
  onSaved,
}: {
  fw: Pick<FrameworkState, 'levels' | 'name'>;
  comp: CompetencyState;
  studentId: string;
  studentName: string;
  /** Selbsteinschätzung bestätigen (statt neuer Einschätzung) */
  confirmSelf?: boolean;
  onClose: () => void;
  onSaved: () => void;
}) {
  const toast = useToast();
  const self = comp.self;
  const [level, setLevel] = useState<number>(confirmSelf && self ? self.level : (comp.teacher?.level ?? 0));
  const [date, setDate] = useState(todayISO());
  const [comment, setComment] = useState('');
  const [evType, setEvType] = useState<EvidenceType>('');
  const [evText, setEvText] = useState('');
  const n = fw.levels.length;
  const descriptor = level ? comp.descriptors[level - 1] : '';

  const save = async () => {
    if (!level) {
      toast.warning('Bitte eine Stufe wählen.');
      return;
    }
    if (confirmSelf && self) {
      await compApi.confirm(self.id, level, comment);
      toast.success(level === self.level ? 'Selbsteinschätzung bestätigt' : 'Selbsteinschätzung mit anderer Stufe bestätigt');
    } else {
      const r = await compApi.assess([
        { student_id: studentId, competency_id: comp.id, level, date, comment, evidence_type: evType, evidence_text: evType ? evText : undefined },
      ]);
      toast.success(r.created ? 'Einschätzung gespeichert' : 'Keine Änderung – die Stufe ist schon eingetragen');
      if (r.badges.length) toast.success(`Neues Abzeichen: ${r.badges.map((b) => b.name).join(', ')}`);
    }
    onSaved();
    onClose();
  };

  return (
    <Modal
      title={confirmSelf ? 'Selbsteinschätzung bestätigen' : 'Kompetenz einschätzen'}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={save}>
            {confirmSelf ? 'Bestätigen' : 'Speichern'}
          </AsyncButton>
        </>
      }
    >
      <div className="stack">
        <div>
          <strong>{studentName}</strong>
          <div>{comp.title}</div>
          {confirmSelf && self && <div className="small muted">Selbsteinschätzung: {levelLabel(fw.levels, self.level)}{self.comment ? ` – „${self.comment}“` : ''}</div>}
        </div>
        <fieldset className="cp-levels">
          <legend>Stufe</legend>
          {fw.levels.map((l, i) => (
            <label key={l + i} className="cp-level-opt">
              <input type="radio" name="cp-level" checked={level === i + 1} onChange={() => setLevel(i + 1)} />
              <span>
                <strong>{i + 1}</strong> {l}
                {comp.descriptors[i] ? <span className="small muted"> – {comp.descriptors[i]}</span> : null}
              </span>
            </label>
          ))}
        </fieldset>
        {descriptor && level ? <div className="small muted">Stufe {level} von {n}: {descriptor}</div> : null}
        {!confirmSelf && (
          <Field label="Datum" htmlFor="cp-date" help="Stand der Einschätzung. Frühere Einträge bleiben im Verlauf erhalten.">
            <input id="cp-date" type="date" value={date} max={todayISO()} onChange={(e) => setDate(e.target.value)} />
          </Field>
        )}
        <Field label="Kommentar" htmlFor="cp-comment" help="Sieht auch die Schülerin bzw. der Schüler und die Familie.">
          <textarea id="cp-comment" rows={2} maxLength={1000} value={comment} onChange={(e) => setComment(e.target.value)} />
        </Field>
        {!confirmSelf && (
          <>
            <Field label="Nachweis" htmlFor="cp-ev" help="Beobachtungsnotizen sehen nur Lehrkräfte. Ein Link kann auf Material oder eine Abgabe zeigen (https://… oder /kursraeume/…).">
              <select id="cp-ev" value={evType} onChange={(e) => setEvType(e.target.value as EvidenceType)}>
                {(['', 'note', 'link'] as EvidenceType[]).map((t) => (
                  <option key={t} value={t}>
                    {EVIDENCE_LABEL[t]}
                  </option>
                ))}
              </select>
            </Field>
            {evType && (
              <Field label={evType === 'note' ? 'Beobachtung' : 'Link'} htmlFor="cp-ev-text">
                {evType === 'note' ? (
                  <textarea id="cp-ev-text" rows={3} maxLength={1000} value={evText} onChange={(e) => setEvText(e.target.value)} />
                ) : (
                  <input id="cp-ev-text" type="text" maxLength={1000} placeholder="https://…" value={evText} onChange={(e) => setEvText(e.target.value)} />
                )}
              </Field>
            )}
          </>
        )}
      </div>
    </Modal>
  );
}

/**
 * Dialoge im Wochenplan (nur `can_plan` = substitution.edit):
 * * „Findet nicht statt“ – eine Stunde (bzw. Block) eines Kurses an einem Tag, ganzer Block oder ein Kursteil.
 * * „Klasse ist nicht da“ – Zeitraum (höchstens 14 Tage), Stunden, Begleitlehrkräfte.
 * Ablauf jeweils: Eingaben → „Vorschau anzeigen“ (`dry_run: true`, speichert nichts) → „Übernehmen“.
 * Ändern sich die Eingaben nach der Vorschau, muss sie erneuert werden – übernommen wird nur, was angezeigt wurde.
 */
import { useEffect, useId, useMemo, useRef, useState, type ReactNode } from 'react';
import { errorMessage } from '../../api/client';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { MultiSelect, type SelectOption } from '../../components/SearchSelect';
import { Alert, Field, KindBadge } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useCollection } from '../../hooks/useCollection';
import { formatLong } from '../../lib/dates';
import { collator } from '../../lib/format';
import { classesApi } from './api';
import { PeriodToggles } from './components';
import {
  blockPeriods,
  classBody,
  coursePeriods,
  describeChanges,
  MAX_RANGE_DAYS,
  lessonBody,
  periodText,
  periodsText,
  previewStats,
  previewStatsText,
  rangeError,
  type NameLookup,
  type SlotItem,
} from './logic';
import type { ClassDetail, NotTakingPlaceBody, NotTakingPlaceResult, WeekCell } from './types';

// ---------------------------------------------------------------------------------------------- Vorschau

export function PreviewView({ result, names, ownClass, headingRef }: { result: NotTakingPlaceResult; names: NameLookup; ownClass: string; headingRef?: React.Ref<HTMLHeadingElement> }) {
  const hid = useId();
  const stats = previewStats(result.preview, ownClass);
  return (
    <section className="kl-preview" aria-labelledby={hid}>
      <h3 id={hid} ref={headingRef} tabIndex={-1}>
        Vorschau der automatischen Umstellung
      </h3>
      {result.summary && (
        <p style={{ margin: '0 0 4px' }}>
          <strong>{result.summary}</strong>
        </p>
      )}
      {/* die Zusammenfassung des Servers nennt Anzahl und betroffene Klassen schon – sonst selbst zählen */}
      {!result.summary && (
        <p className="small muted" style={{ margin: 0 }}>
          {previewStatsText(stats)}
        </p>
      )}
      {stats.changes === 0 && (
        <p className="small" style={{ margin: '4px 0 0' }}>
          Der Vertretungsplan ändert sich dadurch nicht.
        </p>
      )}
      {result.preview
        .filter((d) => d.changes.length > 0 || (d.warnings?.length ?? 0) > 0)
        .map((d) => (
          <div key={d.date} className="kl-preview-day">
            <h4>{formatLong(d.date)}</h4>
            <ul className="kl-changes">
              {describeChanges(d.changes, names, ownClass).map((l) => (
                <li key={l.key} className={l.warning ? 'kl-change-warn' : undefined}>
                  <KindBadge kind={l.kind} compact />
                  <span>
                    {l.text}
                    {l.warning && (
                      <>
                        {' '}
                        <Icon name="alert" title="Achtung: bitte prüfen" />
                      </>
                    )}
                  </span>
                </li>
              ))}
            </ul>
            {(d.warnings?.length ?? 0) > 0 && (
              <Alert kind="warning" title="Bitte prüfen">
                <ul>
                  {d.warnings?.map((w) => (
                    <li key={w}>{w}</li>
                  ))}
                </ul>
              </Alert>
            )}
          </div>
        ))}
      <p className="small muted" style={{ margin: '8px 0 0' }}>
        <Icon name="info" /> Erst „Übernehmen“ trägt den Ausfall ein.
      </p>
    </section>
  );
}

/**
 * Rahmen für beide Dialoge: Vorschau anfordern, anzeigen, übernehmen. `inputsKey` fasst die Eingaben zusammen;
 * weicht er vom Stand der Vorschau ab, ist „Übernehmen“ gesperrt.
 */
function PlanDialog({
  title,
  classId,
  names,
  buildBody,
  inputsKey,
  onClose,
  onApplied,
  children,
}: {
  title: string;
  classId: string;
  names: NameLookup;
  /** `null` = Eingaben unvollständig */
  buildBody: (dryRun: boolean) => NotTakingPlaceBody | null;
  inputsKey: string;
  onClose: () => void;
  onApplied: (r: NotTakingPlaceResult) => void;
  children: ReactNode;
}) {
  const [preview, setPreview] = useState<{ key: string; result: NotTakingPlaceResult } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<'preview' | 'apply' | null>(null);
  const headRef = useRef<HTMLHeadingElement>(null);
  const current = !!preview && preview.key === inputsKey;
  const ready = buildBody(true) !== null;

  useEffect(() => setError(null), [inputsKey]);

  const run = async (dryRun: boolean) => {
    const body = buildBody(dryRun);
    if (!body) return;
    setBusy(dryRun ? 'preview' : 'apply');
    setError(null);
    try {
      const result = await classesApi.notTakingPlace(classId, body);
      if (dryRun) {
        setPreview({ key: inputsKey, result });
        // Vorschau vorlesen lassen: Fokus auf die Überschrift
        window.setTimeout(() => headRef.current?.focus(), 0);
      } else {
        onApplied(result);
      }
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(null);
    }
  };

  return (
    <Modal
      title={title}
      size="lg"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <button type="button" className={`btn${current ? '' : ' btn-primary'}`} disabled={!ready || busy !== null} aria-busy={busy === 'preview'} onClick={() => run(true)}>
            <Icon name="eye" /> {busy === 'preview' ? 'Vorschau wird berechnet …' : preview ? 'Vorschau aktualisieren' : 'Vorschau anzeigen'}
          </button>
          <button type="button" className="btn btn-primary" disabled={!current || busy !== null} aria-busy={busy === 'apply'} onClick={() => run(false)}>
            <Icon name="check" /> {busy === 'apply' ? 'Wird übernommen …' : 'Übernehmen'}
          </button>
        </>
      }
    >
      <div className="stack">
        {children}
        {error && (
          <Alert kind="error" title="Nicht möglich">
            {error}
          </Alert>
        )}
        <div aria-live="polite">
          {preview && !current && (
            <Alert kind="warning" title="Eingaben geändert">
              Die Vorschau passt nicht mehr zu den Eingaben – bitte „Vorschau aktualisieren“.
            </Alert>
          )}
        </div>
        {preview && <PreviewView result={preview.result} names={names} ownClass={classId} headingRef={headRef} />}
        {!preview && <p className="small muted">Die Vorschau zeigt die Umstellung des Plans.</p>}
      </div>
    </Modal>
  );
}

// ---------------------------------------------------------------------------------------------- „Findet nicht statt“

export function LessonDialog({
  detail,
  date,
  dayCells,
  item,
  periodTimes,
  names,
  onClose,
  onApplied,
}: {
  detail: ClassDetail;
  date: string;
  dayCells: readonly WeekCell[];
  item: SlotItem;
  periodTimes: readonly string[];
  names: NameLookup;
  onClose: () => void;
  onApplied: (r: NotTakingPlaceResult) => void;
}) {
  const toast = useToast();
  const courseId = item.courseId ?? '';
  const available = useMemo(() => coursePeriods(dayCells, courseId), [dayCells, courseId]);
  const [periods, setPeriods] = useState<number[]>(() => blockPeriods(dayCells, item.lessonId, item.period));
  const [scope, setScope] = useState<'all' | number>('all');
  const [reason, setReason] = useState('');
  const reasonId = useId();
  const periodsLabelId = useId();
  const scopeName = useId();

  const partLabel = (part: number | null) =>
    detail.subjects.find((s) => s.course_id === courseId && (s.part ?? 0) === (part ?? 0))?.label ?? '';
  const parts = item.cells.map((c) => ({
    part: c.part ?? 0,
    text: `${partLabel(c.part) || names.subject(c.subject)}${c.teacher ? ` (${names.teacher(c.teacher)})` : ''}`,
  }));
  const subjects = [...new Set(item.cells.map((c) => names.subject(c.subject)))].join(' / ');
  const teachers = [...new Set(item.cells.map((c) => c.teacher).filter(Boolean))].map((t) => names.teacher(t)).join(', ');

  const inputsKey = JSON.stringify([periods, scope, reason.trim()]);
  const buildBody = (dryRun: boolean) =>
    courseId && periods.length ? lessonBody({ date, periods, courseId, part: scope === 'all' ? null : scope, reason }, dryRun) : null;

  return (
    <PlanDialog
      title="Findet nicht statt"
      classId={detail.class.id}
      names={names}
      buildBody={buildBody}
      inputsKey={inputsKey}
      onClose={onClose}
      onApplied={(r) => {
        toast.success(r.summary || 'Ausfall eingetragen – der Plan wurde automatisch umgestellt.');
        onApplied(r);
      }}
    >
      <div className="kl-dialog-what">
        <strong>{subjects || 'Unterricht'}</strong>
        {teachers && <span> · {teachers}</span>}
        <div className="small muted">
          {formatLong(date)} · {periodText(item.period)}
          {periodTimes[item.period] ? ` (${periodTimes[item.period]})` : ''} · Klasse {detail.class.name}
        </div>
      </div>

      {available.length > 1 ? (
        <div>
          <div className="field-label" id={periodsLabelId}>
            Welche Stunden fallen aus?
          </div>
          <PeriodToggles count={available.length} only={available} value={periods} onChange={setPeriods} times={periodTimes} labelId={periodsLabelId} />
          {periods.length === 0 && <span className="error-text small">Bitte mindestens eine Stunde wählen.</span>}
        </div>
      ) : (
        <p className="small" style={{ margin: 0 }}>
          Betrifft die {periodText(item.period)} dieses Kurses.
        </p>
      )}

      {parts.length > 1 && (
        <fieldset className="kl-fieldset">
          <legend>Umfang</legend>
          <label className="check">
            <input type="radio" name={scopeName} checked={scope === 'all'} onChange={() => setScope('all')} /> Ganzer Block ({parts.length} Kursteile)
          </label>
          {parts.map((p) => (
            <label key={p.part} className="check">
              <input type="radio" name={scopeName} checked={scope === p.part} onChange={() => setScope(p.part)} /> nur Kursteil {p.text}
            </label>
          ))}
        </fieldset>
      )}

      <Field
        label="Grund"
        htmlFor={reasonId}
        hint="z. B. Exkursion des Kurses, Fortbildung, Projekttag. Schüler/innen und Eltern sehen nur „Unterricht entfällt“."
      >
        <input id={reasonId} type="text" value={reason} maxLength={200} onChange={(e) => setReason(e.target.value)} />
      </Field>
    </PlanDialog>
  );
}

// ---------------------------------------------------------------------------------------------- „Klasse ist nicht da“

export function ClassAbsentDialog({
  detail,
  defaultDate,
  periodsCount,
  periodTimes,
  names,
  onClose,
  onApplied,
}: {
  detail: ClassDetail;
  defaultDate: string;
  periodsCount: number;
  periodTimes: readonly string[];
  names: NameLookup;
  onClose: () => void;
  onApplied: (r: NotTakingPlaceResult) => void;
}) {
  const toast = useToast();
  const [from, setFrom] = useState(defaultDate);
  const [to, setTo] = useState(defaultDate);
  const [whole, setWhole] = useState(true);
  const [periods, setPeriods] = useState<number[]>([]);
  const [reason, setReason] = useState('');
  const [escorts, setEscorts] = useState<string[]>([]);
  const fromId = useId();
  const toId = useId();
  const reasonId = useId();
  const periodsLabelId = useId();
  const allTeachers = useCollection('teachers');

  // Begleitlehrkräfte: Lehrkräfte der Klasse zuerst
  const options: SelectOption[] = useMemo(() => {
    const own = new Map(detail.teachers.map((t) => [t.id, t.name]));
    const all = new Map<string, string>(own);
    for (const t of detail.teacher_choices ?? []) all.set(t.id, t.name);
    for (const t of allTeachers.data ?? []) all.set(t.id, t.name);
    return [...all.entries()]
      .map(([value, label]) => ({ value, label, sub: own.has(value) ? `unterrichtet ${detail.class.name}` : undefined, keywords: value }))
      .sort((a, b) => Number(!!b.sub) - Number(!!a.sub) || collator.compare(a.label, b.label));
  }, [detail, allTeachers.data]);

  const rangeErr = rangeError(from, to);
  const periodErr = !whole && periods.length === 0 ? 'Bitte mindestens eine Stunde wählen – oder „ganztägig“.' : null;
  const inputsKey = JSON.stringify([from, to, whole ? [] : periods, reason.trim(), escorts]);
  const buildBody = (dryRun: boolean) =>
    rangeErr || periodErr ? null : classBody({ from, to, periods: whole ? [] : periods, reason, escorts }, dryRun);

  return (
    <PlanDialog
      title={`Klasse ${detail.class.name} ist nicht da`}
      classId={detail.class.id}
      names={names}
      buildBody={buildBody}
      inputsKey={inputsKey}
      onClose={onClose}
      onApplied={(r) => {
        toast.success(r.summary || `Abwesenheit der Klasse ${detail.class.name} eingetragen – der Plan wurde automatisch umgestellt.`);
        onApplied(r);
      }}
    >
      <div className="form-grid">
        <Field label="Von" htmlFor={fromId}>
          <input
            id={fromId}
            type="date"
            value={from}
            onChange={(e) => {
              setFrom(e.target.value);
              if (to < e.target.value) setTo(e.target.value);
            }}
          />
        </Field>
        <Field label="Bis" htmlFor={toId} hint={`höchstens ${MAX_RANGE_DAYS} Tage`} error={rangeErr}>
          <input id={toId} type="date" value={to} min={from} onChange={(e) => setTo(e.target.value)} aria-invalid={!!rangeErr} />
        </Field>
      </div>
      <div>
        <label className="check">
          <input type="checkbox" checked={whole} onChange={(e) => setWhole(e.target.checked)} /> ganztägig
        </label>
        {!whole && (
          <div style={{ marginTop: 6 }}>
            <div className="field-label" id={periodsLabelId}>
              Stunden <span className="muted small">({periodsText(periods, 'noch keine gewählt')})</span>
            </div>
            <PeriodToggles count={periodsCount} value={periods} onChange={setPeriods} times={periodTimes} labelId={periodsLabelId} />
            {periodErr && <span className="error-text small">{periodErr}</span>}
          </div>
        )}
      </div>
      <Field
        label="Grund"
        htmlFor={reasonId}
        help="Für Exkursion, Klassenfahrt, Wandertag oder Praktikum: Der Unterricht der Klasse entfällt, die Lehrkräfte werden frei und können vertreten. Begleitlehrkräfte fehlen in ihren anderen Klassen, dort plant das System Vertretung. Der Grund ist intern, nicht für Schüler/innen und Eltern sichtbar."
      >
        <input id={reasonId} type="text" value={reason} maxLength={200} onChange={(e) => setReason(e.target.value)} />
      </Field>
      <MultiSelect label="Begleitlehrkräfte" options={options} values={escorts} onChange={setEscorts} placeholder="Lehrkraft hinzufügen …" />
    </PlanDialog>
  );
}

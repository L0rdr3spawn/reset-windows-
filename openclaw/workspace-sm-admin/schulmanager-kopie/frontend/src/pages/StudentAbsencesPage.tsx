import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { studentAbsences as saApi } from '../api/endpoints';
import type { StudentAbsence, StudentAbsenceAccess, StudentAbsenceKind, StudentAbsenceSource, StudentAbsenceStatus } from '../api/types';
import { ClassAbbr } from '../components/Abbr';
import { HelpText } from '../components/Help';
import { Icon } from '../components/Icon';
import { SearchSelect, type SelectOption } from '../components/SearchSelect';
import { VirtualTable, type Column } from '../components/VirtualTable';
import { Alert, AsyncButton, ErrorBox, Field, Loading } from '../components/ui';
import { useUser } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useApi } from '../hooks/useApi';
import { useCollection, useSettings } from '../hooks/useCollection';
import { useTitle } from '../hooks/misc';
import { addDays, currentSchoolDay, dateRangeLabel, formatDateTime, todayISO } from '../lib/dates';
import { schoolDaysOf } from '../lib/weeks';
import { sortBy } from '../lib/format';
import { ClassAbsenceStats } from '../features/students/AbsenceStats';
import { can, isFamily } from '../lib/permissions';
import { FamilyAbsencesSection } from '../features/students/FamilyAbsences';
import { ACCESS_LIVE_SCOPES, actionsWidth, canSeeStatus, COLUMN_WIDTHS, defaultListFrom, isPresence, listHelp, mayReport, minReportDate, needsAttestColumn, REASON_AUDIENCE, reportMode, shortRange } from '../lib/studentAbsences';

export const STATUS_LABEL: Record<StudentAbsenceStatus, string> = {
  gemeldet: 'gemeldet – noch nicht entschuldigt',
  teilweise: 'teilweise entschuldigt',
  entschuldigt: 'entschuldigt',
  unentschuldigt: 'unentschuldigt',
};
export const STATUS_HINT: Record<StudentAbsenceStatus, string> = {
  gemeldet: 'krank gemeldet – zählt als nicht entschuldigt, bis die schriftliche Entschuldigung vorliegt und bestätigt ist',
  teilweise: 'telefonisch gemeldet – die schriftliche Entschuldigung fehlt noch',
  entschuldigt: 'entschuldigt',
  unentschuldigt: 'nicht entschuldigt',
};
export const STATUS_BADGE: Record<StudentAbsenceStatus, string> = {
  gemeldet: 'badge-warning',
  teilweise: 'badge-info',
  entschuldigt: 'badge-success',
  unentschuldigt: 'badge-danger',
};
export const KIND_LABEL: Record<StudentAbsenceKind, string> = { krank: 'krank', verspaetung: 'zu spät', frueh: 'früher gegangen', fehlt: 'gefehlt', beurlaubung: 'Beurlaubung' };
const SOURCE_LABEL: Record<StudentAbsenceSource, string> = { online: 'online', telefon: 'Telefon', schriftlich: 'schriftlich', lehrkraft: 'Lehrkraft' };
const ATTEST_BADGE: Record<string, string> = { erforderlich: 'badge-warning', fehlt: 'badge-danger', eingereicht: 'badge-info', geprueft: 'badge-success', abgelehnt: 'badge-danger' };

/** Attestpflicht (§9.6): nur anzeigen, wenn ein Attest nötig ist */
function AttestCell({ a }: { a: StudentAbsence }) {
  if (!a.attest || a.attest.state === 'nicht_noetig') return <span className="muted small">–</span>;
  return <span className={`badge ${ATTEST_BADGE[a.attest.state] ?? ''}`}>{a.attest.label}</span>;
}

/** Touch-Gerät? (Knöpfe dort 44 px, A-61) */
function coarsePointer(): boolean {
  return typeof window !== 'undefined' && !!window.matchMedia?.('(pointer: coarse)').matches;
}

function periodsText(periods?: number[]): string {
  return periods?.length ? `${periods.map((p) => p + 1).join(', ')}. Std.` : '';
}

export function StatusBadge({ a }: { a: Pick<StudentAbsence, 'status' | 'kind' | 'status_label'> }) {
  if (!a.status) return <span className="muted small">–</span>;
  // Beurlaubungen heißen beantragt/genehmigt/abgelehnt (Backend: LEAVE_STATUS_LABELS)
  if (a.kind === 'beurlaubung' && a.status_label) {
    return <span className={`badge ${a.status === 'entschuldigt' ? 'badge-success' : a.status === 'unentschuldigt' ? 'badge-danger' : 'badge-info'}`}>{a.status_label}</span>;
  }
  return (
    <span className={`badge ${STATUS_BADGE[a.status] ?? ''}`} title={STATUS_HINT[a.status]}>
      {STATUS_LABEL[a.status] ?? a.status}
    </span>
  );
}

export function kindText(a: Pick<StudentAbsence, 'kind' | 'minutes'>): string {
  const k = a.kind ?? 'krank';
  return KIND_LABEL[k] + (k === 'verspaetung' && a.minutes ? ` (${a.minutes} Min.)` : '');
}

/** Telefonnummer für Krankmeldungen (Schul-Einstellung) */
export function SickPhone({ className }: { className?: string }) {
  const { data: settings } = useSettings();
  if (!settings?.sick_phone) return null;
  return (
    <p className={className ?? 'small'} style={{ margin: 0 }}>
      <Icon name="info" /> Telefonisch krank melden: <a href={`tel:${settings.sick_phone.replace(/[^\d+]/g, '')}`}>{settings.sick_phone}</a>
      {settings.sick_phone_hours ? ` (${settings.sick_phone_hours})` : ''}
    </p>
  );
}

function ReportForm({ access, onDone }: { access: StudentAbsenceAccess | null; onDone: () => void }) {
  const user = useUser();
  const toast = useToast();
  const { data: settings } = useSettings();
  const students = useCollection('students');
  const today = todayISO();
  const [studentId, setStudentId] = useState<string | null>(null);
  const [from, setFrom] = useState(() => currentSchoolDay(new Date(), schoolDaysOf(settings)));
  const [to, setTo] = useState(from);
  const [whole, setWhole] = useState(true);
  const [periods, setPeriods] = useState<number[]>([]);
  const [reason, setReason] = useState('');
  const [kind, setKind] = useState<StudentAbsenceKind>('krank');
  const [minutes, setMinutes] = useState(10);
  const [source, setSource] = useState<StudentAbsenceSource>(user.role === 'sekretariat' ? 'telefon' : 'lehrkraft');
  const [status, setStatus] = useState<StudentAbsenceStatus>(user.role === 'sekretariat' ? 'teilweise' : 'gemeldet');
  const [busy, setBusy] = useState(false);
  const nPeriods = settings?.periods ?? 10;
  const oneDay = kind === 'verspaetung' || kind === 'frueh';

  const options: SelectOption[] = useMemo(() => sortBy(students.data ?? [], (s) => s.name).map((s) => ({ value: s.id, label: s.name, sub: s.class_id })), [students.data]);
  const effectiveStudent = studentId ?? (options.length === 1 ? options[0]?.value ?? null : null);
  const chosenClass = options.find((o) => o.value === effectiveStudent)?.sub ?? null;
  // Fachlehrkraft: nur die eigene Stunde (ein Tag, nicht in der Zukunft; ohne Auswahl = alle eigenen Stunden)
  const lesson = reportMode(access, chosenClass) === 'lesson';
  const day = lesson && from > today ? today : from;

  const submit = async () => {
    if (!effectiveStudent) {
      toast.warning('Bitte Schüler/in auswählen.');
      return;
    }
    setBusy(true);
    try {
      const r = await saApi.create({
        student_id: effectiveStudent ?? undefined,
        date_from: day,
        date_to: lesson || oneDay ? day : to < day ? day : to,
        periods: whole && !lesson && kind !== 'frueh' ? [] : periods,
        reason,
        ...(lesson ? {} : { kind, minutes: kind === 'verspaetung' ? minutes : null, source, status }),
      });
      toast.success(r?.merged ? 'Mit der vorhandenen Meldung zusammengeführt.' : lesson ? 'Abwesenheit gemeldet.' : 'Eintrag gespeichert');
      setReason('');
      setPeriods([]);
      onDone();
    } catch (e) {
      toast.error(e, 'Krankmeldung');
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card" aria-labelledby="report-h">
      <h2 id="report-h">{lesson ? 'Abwesenheit in meiner Stunde melden' : 'Fehlzeit erfassen'}</h2>
      <div className="stack">
        <SearchSelect label="Schüler/in" options={options} value={effectiveStudent} onChange={setStudentId} placeholder="Name oder Klasse …" />
        {!lesson && (
          <div className="form-grid">
            <Field label="Art" htmlFor="sa-kind">
              <select id="sa-kind" value={kind} onChange={(e) => setKind(e.target.value as StudentAbsenceKind)}>
                <option value="krank">krank / abwesend gemeldet</option>
                <option value="verspaetung">zu spät gekommen</option>
                <option value="frueh">früher gegangen</option>
                <option value="fehlt">ohne Meldung gefehlt</option>
              </select>
            </Field>
            <Field label="Gemeldet per" htmlFor="sa-source">
              <select id="sa-source" value={source} onChange={(e) => setSource(e.target.value as StudentAbsenceSource)}>
                {Object.entries(SOURCE_LABEL).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Status" htmlFor="sa-initial" hint={STATUS_HINT[status]}>
              <select id="sa-initial" value={status} onChange={(e) => setStatus(e.target.value as StudentAbsenceStatus)}>
                {Object.entries(STATUS_LABEL).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </Field>
            {kind === 'verspaetung' && (
              <Field label="Minuten zu spät" htmlFor="sa-min">
                <input id="sa-min" type="number" min={1} max={600} value={minutes} onChange={(e) => setMinutes(Math.max(1, Number(e.target.value) || 1))} />
              </Field>
            )}
          </div>
        )}
        <div className="form-grid">
          <Field label={lesson || oneDay ? 'Tag' : 'Erster Fehltag'} htmlFor="sa-from" help={lesson ? 'Fachlehrkräfte melden nur für die eigene Stunde – am selben Tag oder danach.' : undefined}>
            <input id="sa-from" type="date" value={day} min={minReportDate(today, access)} max={lesson ? today : undefined} onChange={(e) => setFrom(e.target.value)} />
          </Field>
          {!lesson && !oneDay && (
            <Field label="Letzter Fehltag (voraussichtlich)" htmlFor="sa-to">
              <input id="sa-to" type="date" value={to < from ? from : to} min={from} onChange={(e) => setTo(e.target.value)} />
            </Field>
          )}
        </div>
        {!lesson && kind !== 'verspaetung' && (
          <label className="check">
            <input type="checkbox" checked={whole && kind !== 'frueh'} disabled={kind === 'frueh'} onChange={(e) => setWhole(e.target.checked)} />{' '}
            {kind === 'frueh' ? 'versäumte Stunden auswählen' : 'ganztägig'}
          </label>
        )}
        {(lesson || (kind !== 'verspaetung' && (!whole || kind === 'frueh'))) && (
          <div className="stack-sm">
            {lesson && (
              <span className="small">
                <HelpText help="Ohne Auswahl werden alle Ihre Stunden mit der Schülerin bzw. dem Schüler an diesem Tag gemeldet.">Stunden</HelpText>
              </span>
            )}
            <div className="toggle-grid" role="group" aria-label="Fehlstunden">
              {Array.from({ length: nPeriods }, (_, p) => (
                <button key={p} type="button" className="toggle" aria-pressed={periods.includes(p)} onClick={() => setPeriods((s) => (s.includes(p) ? s.filter((x) => x !== p) : [...s, p].sort((a, b) => a - b)))}>
                  {p + 1}.
                </button>
              ))}
            </div>
          </div>
        )}
        <Field label="Grund (optional)" htmlFor="sa-reason" hint="Keine Diagnosen nötig – z. B. „krank“ oder „Arzttermin“.">
          <input id="sa-reason" type="text" value={reason} onChange={(e) => setReason(e.target.value)} maxLength={500} />
        </Field>
        <div className="row-end">
          <a className="btn btn-ghost" href={saApi.formUrl({ student_id: effectiveStudent ?? undefined })} target="_blank" rel="noopener">
            <Icon name="download" /> Formular „Schriftliche Entschuldigung“
          </a>
          <button type="button" className="btn btn-primary" onClick={submit} disabled={busy}>
            <Icon name="medical" /> {busy ? 'Senden …' : lesson ? 'Abwesenheit melden' : 'Speichern'}
          </button>
        </div>
      </div>
    </section>
  );
}

export default function StudentAbsencesPage() {
  useTitle('Krankmeldungen');
  const user = useUser();
  const toast = useToast();
  const family = isFamily(user);
  const canRead = can(user, 'student_absence.read');
  const accessQ = useApi(() => saApi.access(), [], { enabled: canRead || can(user, 'student_absence.report'), live: [...ACCESS_LIVE_SCOPES] });
  const access = accessQ.data ?? null;
  const canReport = mayReport(can(user, 'student_absence.report'), access);
  const showStatus = canSeeStatus(access);
  const classes = useCollection('classes', !family);
  const [from, setFrom] = useState(() => defaultListFrom(todayISO(), family));
  const [classId, setClassId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('');
  const [kind, setKind] = useState<string>('');
  const q = useApi(() => saApi.list({ from, class_id: classId ?? undefined, status: (showStatus && status) || undefined, kind: kind || undefined }), [from, classId, status, kind, showStatus], {
    enabled: canRead && !family,
    live: ['student_absences', 'parent_access'],
  });

  const setSt = async (a: StudentAbsence, s: StudentAbsenceStatus) => {
    try {
      const updated = await saApi.setStatus(a.id, s);
      q.setData((list) => (list ?? []).map((x) => (x.id === a.id ? { ...x, ...updated } : x)));
      toast.success(`${a.student_name ?? a.student_id}: ${a.kind === 'beurlaubung' ? (s === 'entschuldigt' ? 'Beurlaubung genehmigt' : s === 'unentschuldigt' ? 'Beurlaubung abgelehnt' : 'beantragt') : STATUS_LABEL[s]}`);
    } catch (e) {
      toast.error(e);
    }
  };
  const remove = async (a: StudentAbsence) => {
    try {
      await saApi.remove(a.id);
      q.setData((list) => (list ?? []).filter((x) => x.id !== a.id));
      toast.success('Meldung gelöscht');
    } catch (e) {
      toast.error(e);
    }
  };

  const rows = q.data ?? [];
  const actionsPx = actionsWidth(rows, coarsePointer());
  const columns: Column<StudentAbsence>[] = [
    {
      key: 'name',
      header: 'Schüler/in',
      width: `${COLUMN_WIDTHS.name}px`,
      render: (a) => {
        const inner = (
          <span title={[a.student_name ?? a.student_id, a.class_id].filter(Boolean).join(', ')}>
            <strong>{a.student_name ?? a.student_id}</strong>
            {a.class_id ? (
              <span className="muted small">
                {' '}
                <ClassAbbr id={a.class_id} passive />
              </span>
            ) : null}
          </span>
        );
        return family ? inner : <Link to={`/fehlzeiten/${encodeURIComponent(a.student_id)}`}>{inner}</Link>;
      },
      sortValue: (a) => a.student_name ?? a.student_id,
    },
    {
      key: 'range',
      header: 'Zeitraum',
      width: `${COLUMN_WIDTHS.range}px`,
      render: (a) => {
        if (isPresence(a)) return `heute (${periodsText(a.periods)})`;
        const hours = a.periods?.length ? ` (${periodsText(a.periods)})` : '';
        return <span title={`${dateRangeLabel(a.date_from, a.date_to)}${hours}`}>{`${shortRange(a.date_from, a.date_to, todayISO())}${hours}`}</span>;
      },
      sortValue: (a) => a.date_from,
    },
    { key: 'kind', header: 'Art', render: (a) => kindText(a), sortValue: (a) => a.kind ?? '', width: '120px' },
    {
      key: 'reason',
      header: 'Grund',
      width: `${COLUMN_WIDTHS.reason}px`,
      render: (a) =>
        a.reason_hidden || isPresence(a) || a.view === 'leave' ? (
          <span className="muted small">
            <HelpText help={REASON_AUDIENCE}>vertraulich</HelpText>
          </span>
        ) : (
          <span title={a.reason}>{a.reason}</span>
        ),
    },
    {
      key: 'by',
      header: 'Gemeldet von',
      width: `${COLUMN_WIDTHS.by}px`,
      render: (a) => {
        const text = [a.source_label, a.reported_by_name, a.created_at ? formatDateTime(a.created_at) : ''].filter(Boolean).join(' · ');
        return text ? <span className="small" title={text}>{text}</span> : <span className="muted small">–</span>;
      },
    },
    ...(showStatus
      ? ([
          {
            key: 'status',
            header: 'Status',
            render: (a) => (a.status ? <StatusBadge a={a} /> : <span className="muted small">–</span>),
            sortValue: (a) => a.status ?? '',
            width: `${COLUMN_WIDTHS.status}px`,
          },
        ] satisfies Column<StudentAbsence>[])
      : []),
    ...(showStatus && needsAttestColumn(rows)
      ? ([{ key: 'attest', header: 'Attest', render: (a) => <AttestCell a={a} />, sortValue: (a) => (a.attest?.missing ? 0 : 1), width: `${COLUMN_WIDTHS.attest}px` }] satisfies Column<StudentAbsence>[])
      : []),
    ...(actionsPx
      ? ([
          {
            key: 'actions',
            header: <span className="sr-only">Aktionen</span>,
            className: 'actions',
            width: `${actionsPx}px`,
            render: (a) => (
              <span className="row-end nowrap">
                {a.can_manage && (
                  <>
                    <AsyncButton className="btn btn-sm btn-icon" disabled={a.status === 'entschuldigt'} onClick={() => setSt(a, 'entschuldigt')} title={a.kind === 'beurlaubung' ? 'genehmigen' : 'entschuldigen'}>
                      <Icon name="check" />
                      <span className="sr-only">{a.kind === 'beurlaubung' ? 'genehmigt' : 'entschuldigt'}</span>
                    </AsyncButton>
                    <AsyncButton className="btn btn-sm btn-icon btn-ghost" disabled={a.status === 'unentschuldigt'} onClick={() => setSt(a, 'unentschuldigt')} title={a.kind === 'beurlaubung' ? 'ablehnen' : 'unentschuldigt'}>
                      <Icon name="x" />
                      <span className="sr-only">{a.kind === 'beurlaubung' ? 'abgelehnt' : 'unentschuldigt'}</span>
                    </AsyncButton>
                  </>
                )}
                {a.can_delete && (
                  <AsyncButton className="btn btn-sm btn-icon btn-ghost" confirm="Meldung löschen?" onClick={() => remove(a)} title="löschen">
                    <Icon name="trash" />
                    <span className="sr-only">löschen</span>
                  </AsyncButton>
                )}
              </span>
            ),
          },
        ] satisfies Column<StudentAbsence>[])
      : []),
  ];

  return (
    <div className="page">
      <div className="page-head">
        <h1>Krankmeldungen &amp; Fehlzeiten</h1>
        {!family && can(user, 'student_documents.read') && (access?.all || !!access?.class_ids.length) && (
          <Link className="btn" to="/dokumente">
            <Icon name="medical" /> Atteste &amp; Dokumente
          </Link>
        )}
      </div>
      <div className="stack">
        {/* Schüler/innen und Eltern (je Kind): krank melden, Meldungen, Atteste und Dokumente an einer Stelle */}
        {family && <FamilyAbsencesSection />}
        {!family && canReport && <ReportForm access={access} onDone={q.reload} />}
        {canRead && !family && (
          <section className="card" aria-labelledby="list-h">
            <div className="card-head">
              <h2 id="list-h">
                <HelpText help={listHelp(access, user.role === 'schueler')}>{family ? 'Bisherige Meldungen' : 'Gemeldete Abwesenheiten'}</HelpText>
              </h2>
              {family && user.students?.[0] && (
                <Link className="btn btn-sm" to={`/fehlzeiten/${encodeURIComponent(user.students[0].id)}`}>
                  Fehlzeiten-Übersicht
                </Link>
              )}
            </div>
            <div className="toolbar">
              <Field label="ab" htmlFor="sa-lfrom">
                <input id="sa-lfrom" type="date" value={from} max={addDays(todayISO(), 366)} onChange={(e) => setFrom(e.target.value || defaultListFrom(todayISO(), family))} />
              </Field>
              {!family && (
                <div className="field">
                  <SearchSelect
                    label="Klasse"
                    options={sortBy(classes.data ?? [], (c) => c.name).map((c) => ({ value: c.id, label: c.name }))}
                    value={classId}
                    onChange={setClassId}
                    allowClear
                    placeholder="alle (eigene) Klassen"
                  />
                </div>
              )}
              {showStatus && (
                <Field label="Status" htmlFor="sa-status">
                  <select id="sa-status" value={status} onChange={(e) => setStatus(e.target.value)}>
                    <option value="">alle</option>
                    {Object.entries(STATUS_LABEL).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                </Field>
              )}
              {!family && (
                <Field label="Art" htmlFor="sa-kindf">
                  <select id="sa-kindf" value={kind} onChange={(e) => setKind(e.target.value)}>
                    <option value="">alle</option>
                    {Object.entries(KIND_LABEL).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                </Field>
              )}
            </div>
            {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
            {q.initialLoading && <Loading />}
            {q.data && <VirtualTable rows={rows} columns={columns} rowKey={(a) => `${a.view ?? ''}-${a.id}-${a.date_from}`} caption="Krankmeldungen" height="60vh" emptyText="Keine Einträge im Zeitraum." />}
          </section>
        )}
        {canRead && !family && classId && <ClassAbsenceStats classId={classId} />}
        {!family && !canReport && !canRead && <Alert kind="info">Für Krankmeldungen fehlt die Berechtigung.</Alert>}
      </div>
    </div>
  );
}

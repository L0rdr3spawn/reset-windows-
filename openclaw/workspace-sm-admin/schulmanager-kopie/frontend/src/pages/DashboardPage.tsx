import { Suspense, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { absences as absencesApi, me as meApi, planning, substitutions } from '../api/endpoints';
import type { Announcement, Exam, MyDay } from '../api/types';
import { EntryTable } from '../components/EntryTable';
import { Icon } from '../components/Icon';
import { FeatureBoundary } from '../components/Layout';
import { widgetsFor, type FeatureWidget } from '../features/registry';
import { Modal } from '../components/Modal';
import { HelpText } from '../components/Help';
import { AbbrList, RoomAbbr, SubjectAbbr } from '../components/Abbr';
import { CalendarWeekCard } from '../features/classes/CalendarWeek';
import FamilyHome from '../features/students/FamilyHome';
import { ExamHint, useExamHints } from '../features/students/ExamHints';
import { CurrentLessonAttendance } from '../features/classes/RegisterPage';
import { Alert, AsyncButton, Empty, ErrorBox, Field, KindBadge, Loading } from '../components/ui';
import { useUser } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useApi } from '../hooks/useApi';
import { useSettings } from '../hooks/useCollection';
import { useTitle } from '../hooks/misc';
import { currentSchoolDay, formatDate, formatLong, relativeDayLabel, shiftSchoolDay, todayISO } from '../lib/dates';
import { NoPlanNotice } from '../components/PlanNotice';
import { can, dashboardPanels } from '../lib/permissions';
import { KIND_ORDER, kindInfo } from '../lib/substitution';
import { examDetailLink, examTarget } from '../features/channels/examRoom';
import { ReportTiles } from './planning/ReportTiles';

function greeting(d = new Date()): string {
  const h = d.getHours();
  if (h < 11) return 'Guten Morgen';
  if (h < 18) return 'Guten Tag';
  return 'Guten Abend';
}

export function AnnouncementList({ items, empty = 'Keine aktuellen Mitteilungen.' }: { items: Announcement[]; empty?: string }) {
  if (!items.length) return <p className="muted small">{empty}</p>;
  return (
    <div className="stack-sm">
      {items.map((a) => (
        <article key={a.id} className={`announcement${a.priority === 'wichtig' ? ' important' : ''}`}>
          <h3>
            {a.priority === 'wichtig' && <span className="badge badge-danger mr-1">Wichtig</span>}
            {a.title}
          </h3>
          {a.body && <div className="body small">{a.body}</div>}
          <div className="xsmall faint">
            {[a.author_name, a.valid_from ? `ab ${formatDate(a.valid_from)}` : null, a.valid_to ? `bis ${formatDate(a.valid_to)}` : null].filter(Boolean).join(' · ')}
          </div>
        </article>
      ))}
    </div>
  );
}

function ExamList({ exams }: { exams: (Exam & { course_label?: string })[] }) {
  const dates = exams.map((e) => e.date).sort();
  const hints = useExamHints(dates[0] ?? todayISO(), dates[dates.length - 1] ?? todayISO(), exams.length > 0);
  if (!exams.length) return null;
  return (
    <div className="stack-sm mt-3">
      {exams.map((e) => (
        <div key={e.id} className="row">
          <KindBadge kind="klausur" />
          <span>
            <Link to={examTarget(e, e.date) ?? examDetailLink(e.id, e.date)} title={e.channel_id ? 'Zum Kursraum' : undefined}>
              <strong>{e.title || 'Klassenarbeit'}</strong>
            </Link>{' '}
            · {e.start + 1}.{e.length > 1 ? `–${e.start + e.length}.` : ''} Std.
            {e.subject ? <> · <SubjectAbbr id={e.subject} /></> : null}
            {e.room ? <> · Raum <RoomAbbr id={e.room} /></> : null}
            <ExamHint students={hints[e.id]} />
            {e.channel_id ? (
              <>
                {' '}
                <Link to={examDetailLink(e.id, e.date)} className="small">
                  Details
                </Link>
              </>
            ) : null}
          </span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------- Schüler/Eltern

function FamilyPanel() {
  const { data } = useApi<MyDay>(() => meApi.today(todayISO()), [], { live: ['announcements'] });
  return (
    <div className="stack">
      <Suspense fallback={<Loading />}>
        <FamilyHome />
      </Suspense>
      <section className="card" aria-labelledby="ann-h">
        <div className="card-head">
          <h2 id="ann-h">Mitteilungen</h2>
          <Link to="/nachrichten?f=mitteilungen" className="small">
            Alle anzeigen
          </Link>
        </div>
        <AnnouncementList items={data?.announcements ?? []} />
      </section>
    </div>
  );
}

// ---------------------------------------------------------------- Lehrkräfte

export function SelfReportModal({ onClose }: { onClose: () => void }) {
  const toast = useToast();
  const { data: settings } = useSettings();
  const periods = settings?.periods ?? 10;
  // Vorbelegung: heute bzw. am Wochenende der nächste Schultag (wie „Meine Tage“)
  const [from, setFrom] = useState(() => currentSchoolDay(new Date(), settings?.days ?? 5));
  const [to, setTo] = useState(() => currentSchoolDay(new Date(), settings?.days ?? 5));
  const [whole, setWhole] = useState(true);
  const [sel, setSel] = useState<number[]>([]);
  const [reason, setReason] = useState('krank');
  const [busy, setBusy] = useState(false);
  const submit = async () => {
    setBusy(true);
    try {
      await absencesApi.reportSelf({ date_from: from, date_to: to < from ? from : to, periods: whole ? [] : sel, reason });
      toast.success('Abwesenheit gespeichert – der Vertretungsplan passt sich automatisch an.');
      onClose();
    } catch (e) {
      toast.error(e, 'Krankmeldung');
    } finally {
      setBusy(false);
    }
  };
  return (
    <Modal
      title="Krankmeldung (Lehrkraft)"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <button type="button" className="btn btn-primary" onClick={submit} disabled={busy || (!whole && !sel.length)}>
            {busy ? 'Senden …' : 'Krank melden'}
          </button>
        </>
      }
    >
      <div className="form-grid">
        <Field label="Von" htmlFor="sr-from">
          <input id="sr-from" type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
        </Field>
        <Field label="Bis" htmlFor="sr-to">
          <input id="sr-to" type="date" value={to} min={from} onChange={(e) => setTo(e.target.value)} />
        </Field>
        <div className="span-all">
          <label className="check">
            <input type="checkbox" checked={whole} onChange={(e) => setWhole(e.target.checked)} /> ganztägig
          </label>
          {!whole && (
            <div className="toggle-grid" role="group" aria-label="Stunden" style={{ marginTop: 8 }}>
              {Array.from({ length: periods }, (_, p) => (
                <button key={p} type="button" className="toggle" aria-pressed={sel.includes(p)} onClick={() => setSel((s) => (s.includes(p) ? s.filter((x) => x !== p) : [...s, p].sort((a, b) => a - b)))}>
                  {p + 1}.
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="span-all row" role="group" aria-label="Schnellauswahl Grund">
          {['krank', 'Kind krank', 'Beurlaubung'].map((r) => (
            <button key={r} type="button" className="btn btn-sm" aria-pressed={reason === r} onClick={() => setReason(r)}>
              {r === 'krank' ? 'Ich bin krank' : r === 'Kind krank' ? 'Mein Kind ist krank' : r}
            </button>
          ))}
        </div>
        <Field label="Grund (nur für die Schulleitung sichtbar)" htmlFor="sr-reason" className="span-all">
          <input id="sr-reason" type="text" value={reason} onChange={(e) => setReason(e.target.value)} />
        </Field>
      </div>
    </Modal>
  );
}

function TeacherDay({ date, label }: { date: string; label: string }) {
  const user = useUser();
  const { data, error, initialLoading, reload } = useApi<MyDay>(() => meApi.today(date), [date], {
    live: ['substitutions', 'timetable', 'absences', 'overrides', 'duties', 'exams'],
  });
  const mine = (data?.plan_entries ?? []).filter((e) => e.substitute === user.teacher_id);
  const duties = (data?.cells ?? []).filter((c) => c.kind === 'aufsicht');
  return (
    <section className="card" aria-label={`${label}: ${formatLong(date)}`}>
      <div className="card-head">
        <h2>
          {label} <span className="muted small">{formatLong(date)}</span>
        </h2>
        {data?.week_no ? <span className="badge">Woche {data.week_no}</span> : null}
      </div>
      {error ? <ErrorBox error={error} onRetry={reload} /> : null}
      {initialLoading && <Loading />}
      {data?.holiday && <Alert kind="info" title="Kein Unterricht">{data.holiday}</Alert>}
      {data && !data.holiday && <NoPlanNotice plan={data.week_info?.plan} />}
      {data && !data.holiday && (
        <>
          {mine.length > 0 ? (
            <Alert kind="warning" title={`${mine.length} Vertretung${mine.length === 1 ? '' : 'en'} für Sie`}>
              <ul>
                {mine.map((e) => (
                  <li key={e.id}>
                    {e.period_label || `${e.period + 1}.`} Std. · <AbbrList kind="class" ids={e.classes} /> · <SubjectAbbr id={e.subject} /> · {kindInfo(e.kind).label}
                    {e.new_room || e.room ? (
                      <>
                        {' · Raum '}
                        <RoomAbbr id={e.new_room ?? e.room} />
                      </>
                    ) : null}
                  </li>
                ))}
              </ul>
            </Alert>
          ) : (
            <p className="small muted">Keine Vertretungen für Sie.</p>
          )}
          {duties.length > 0 && (
            <p className="small">
              <strong>Aufsichten:</strong> {duties.map((d) => `${d.subject || 'Aufsicht'} (${d.note || `nach ${d.period + 1}. Std.`})`).join(', ')}
            </p>
          )}
          <ExamList exams={data.exams} />
        </>
      )}
    </section>
  );
}

function TeacherPanel() {
  const user = useUser();
  const { data: settings } = useSettings();
  const days = settings?.days ?? 5;
  const [report, setReport] = useState(false);
  const d1 = currentSchoolDay(new Date(), days);
  const d2 = shiftSchoolDay(d1, 1, days);
  return (
    <div className="stack">
      <div className="row-between">
        <h2 style={{ margin: 0 }}>Meine Tage</h2>
        <div className="row">
          {can(user, 'absence.report_self') && (
            <button type="button" className="btn btn-danger" onClick={() => setReport(true)}>
              <Icon name="medical" /> Krankmeldung
            </button>
          )}
          <Link to="/vertretung" className="btn">
            <Icon name="swap" /> Vertretungsplan
          </Link>
        </div>
      </div>
      <CurrentLessonAttendance />
      <div className="grid grid-2">
        <TeacherDay date={d1} label={relativeDayLabel(d1)} />
        <TeacherDay date={d2} label={relativeDayLabel(d2)} />
      </div>
      {user.teacher_id && <CalendarWeekCard kind="teacher" refId={user.teacher_id} title={user.display_name} heading="Meine Woche" />}
      {report && <SelfReportModal onClose={() => setReport(false)} />}
    </div>
  );
}

// ---------------------------------------------------------------- Planung/Leitung

/** Kennzahl in einer `.stats`-Leiste (eine Fläche statt vieler Karten); `help` erscheint an der Beschriftung. */
function Kpi({ value, label, tone, help }: { value: number | string; label: string; tone?: 'warn' | 'bad' | 'good'; help?: string }) {
  return (
    <div className={`kpi${tone ? ` ${tone}` : ''}`}>
      <span className="kpi-value">{value}</span>
      <span className="kpi-label">{help ? <HelpText help={help}>{label}</HelpText> : label}</span>
    </div>
  );
}

function PlannerPanel() {
  const user = useUser();
  const { data: settings } = useSettings();
  const days = settings?.days ?? 5;
  const date = currentSchoolDay(new Date(), days);
  const plan = useApi(() => substitutions.day({ date }), [date], {
    live: ['substitutions', 'absences', 'overrides', 'timetable', 'holidays'],
  });
  const showReport = can(user, ['timetable.generate', 'timetable.edit', 'plans.read_all']);
  const report = useApi(() => planning.report(), [], { enabled: showReport, live: ['timetable', 'courses', 'classes', 'teachers'] });

  const p = plan.data;
  const open = useMemo(() => (p?.entries ?? []).filter((e) => e.warning), [p]);
  
  return (
    <div className="stack">
      <div className="row-between">
        <h2 style={{ margin: 0 }}>
          Lage {relativeDayLabel(date) === 'Heute' ? 'heute' : `am ${formatDate(date)}`}
        </h2>
        <div className="row">
          {can(user, 'substitution.edit') && (
            <Link to="/vertretung" className="btn btn-primary">
              <Icon name="swap" /> Vertretungsplan bearbeiten
            </Link>
          )}
          {can(user, 'timetable.generate') && (
            <Link to="/planung/pruefung" className="btn">
              <Icon name="sparkles" /> Plan prüfen
            </Link>
          )}
        </div>
      </div>
      {plan.error ? <ErrorBox error={plan.error} onRetry={plan.reload} /> : null}
      {plan.initialLoading && <Loading />}
      {p && (
        <>
          {p.holiday && <Alert kind="info" title="Unterrichtsfrei">{p.holiday}</Alert>}
          {!p.holiday && <NoPlanNotice plan={p.week_info?.plan} />}
          <div className="stats">
            <Kpi value={p.absent_teachers?.length ?? 0} label="Lehrkräfte abwesend" tone={(p.absent_teachers?.length ?? 0) > 0 ? 'warn' : undefined} />
            <Kpi value={p.entries.length} label="Änderungen im Plan" />
            <Kpi
              value={open.length}
              label="offene Lücken / zu prüfen"
              tone={open.length ? 'bad' : 'good'}
              help="Änderungen mit Warnung, z. B. ohne gefundene Vertretung – bitte im Vertretungsplan prüfen."
            />
            <Kpi value={p.absent_classes?.length ?? 0} label="Klassen abwesend" />
          </div>
          <div className="card">
            <h3>Verteilung</h3>
            <div className="row">
              {KIND_ORDER.filter((k) => (p.stats?.[k] ?? 0) > 0).map((k) => (
                <span key={k} className="row" style={{ gap: 4 }}>
                  <KindBadge kind={k} /> <strong>{p.stats[k]}</strong>
                </span>
              ))}
              {Object.values(p.stats ?? {}).every((v) => !v) && <span className="muted small">Keine Änderungen.</span>}
            </div>
          </div>
          {(p.warnings.length > 0 || open.length > 0) && (
            <div className="card">
              <h3>Warnungen & offene Lücken</h3>
              {p.warnings.length > 0 && (
                <ul className="warning-list">
                  {p.warnings.slice(0, 12).map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              )}
              {open.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <EntryTable entries={open} caption="Offene Lücken" grouped={false} />
                </div>
              )}
            </div>
          )}
        </>
      )}
      {showReport && (
        <div className="card">
          <div className="card-head">
            <h3>Stundenplan-Qualität</h3>
            <Link to="/planung/bericht" className="small">
              Bericht öffnen
            </Link>
          </div>
          {report.error ? <ErrorBox error={report.error} onRetry={report.reload} /> : null}
          {report.data && <ReportTiles keys={['lessons', 'unplaced_hours', 'class_gaps', 'conflicts']} stats={report.data.stats} ranges={report.data.ranges} compact />}
          {report.data && report.data.warnings.length > 0 && (
            <details className="disclosure">
              <summary>{report.data.warnings.length} Hinweise</summary>
              <ul className="warning-list small">
                {report.data.warnings.slice(0, 30).map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}
    </div>
  );
}

/** Startseiten-Kacheln der Feature-Module (Rolle/Recht gefiltert, nach `order` sortiert). */
function FeatureWidgets({ items, label }: { items: (FeatureWidget & { module: string })[]; label: string }) {
  if (!items.length) return null;
  return (
    <div
      className="grid grid-2"
      role="region"
      aria-label={label}
      // min(320px, 100%): auch auf sehr schmalen Handys kein horizontales Scrollen
      style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(min(320px, 100%), 1fr))' }}
    >
      {items.map((w) => (
        <div key={`${w.module}:${w.id}`} style={{ minWidth: 0, ...(w.wide ? { gridColumn: '1 / -1' } : {}) }}>
          <FeatureBoundary label={w.id}>
            <Suspense fallback={<Loading />}>{w.element}</Suspense>
          </FeatureBoundary>
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  useTitle('Start');
  const user = useUser();
  const panels = dashboardPanels(user);
  // Schüler/Eltern: Übersicht und Nachrichten stehen schon auf der Startseite – keine doppelten Kacheln
  const widgets = widgetsFor(user).filter((w) => !(panels.includes('family') && (w.module === 'schueler' || w.module === 'nachrichten')));
  const widgetsTop = widgets.filter((w) => w.order < 0);
  const widgetsBottom = widgets.filter((w) => w.order >= 0);
  const full = user.display_name || user.username;
  const first = full.split(' ')[0] ?? full;
  // „Frau Ludwig“/„Herr …“/„Familie …“ vollständig, sonst Vorname
  const name = /^(frau|herr|familie|dr\.?)$/i.test(first) || /\(/.test(full) ? full.replace(/\s*\(.*\)\s*/, '') : first;
  return (
    <div className="page stack">
      <div className="page-head">
        <div>
          <h1>
            {greeting()}, {name}
          </h1>
          <p className="muted" style={{ margin: 0 }}>
            {formatLong(todayISO())}
          </p>
        </div>
        <AsyncButton className="btn btn-ghost btn-sm" onClick={() => window.location.reload()}>
          <Icon name="refresh" /> Aktualisieren
        </AsyncButton>
      </div>
      <FeatureWidgets items={widgetsTop} label="Wichtig für Sie" />
      {panels.includes('family') && <FamilyPanel />}
      {panels.includes('teacher') && <TeacherPanel />}
      {panels.includes('planner') && <PlannerPanel />}
      <FeatureWidgets items={widgetsBottom} label="Weitere Bereiche" />
      {panels.length === 0 && widgets.length === 0 && (
        <div className="card">
          <Empty
            icon="home"
            title="Keine Startseiten-Inhalte für Ihre Rolle"
            action={
              can(user, 'substitution.read') ? (
                <Link to="/vertretung" className="btn">
                  Vertretungsplan
                </Link>
              ) : undefined
            }
          />
        </div>
      )}
      {!panels.includes('family') && <StaffAnnouncements />}
    </div>
  );
}

function StaffAnnouncements() {
  const { data } = useApi(() => meApi.today(todayISO()), [], { live: ['announcements'] });
  const items = data?.announcements ?? [];
  if (!items.length) return null;
  return (
    <section className="card">
      <div className="card-head">
        <h2>Mitteilungen</h2>
        <Link to="/nachrichten?f=mitteilungen" className="small">
          Alle anzeigen
        </Link>
      </div>
      <AnnouncementList items={items.slice(0, 5)} />
    </section>
  );
}


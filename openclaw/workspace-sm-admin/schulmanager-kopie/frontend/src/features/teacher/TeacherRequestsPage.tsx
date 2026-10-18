/**
 * „Anträge von Lehrkräften“ (/planung/antraege, Recht `teacher_requests.review`): Profiländerungen (Fächer,
 * Wunschklassen, Deputat, Arbeitszeitfenster, Wünsche) prüfen – Vergleich alt/neu, Konflikte mit dem aktuellen
 * Stundenplan, Genehmigen/Ablehnen mit Kommentar und Neuplanung des Stundenplans dieser Lehrkraft.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { TeacherAbbr } from '../../components/Abbr';
import { Icon } from '../../components/Icon';
import { SearchSelect, type SelectOption } from '../../components/SearchSelect';
import { HelpTip } from '../../components/HelpTip';
import { AsyncButton, Empty, ErrorBox, Field, Loading, SegmentedControl } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useCollection, useSettings } from '../../hooks/useCollection';
import { useMediaQuery, useTitle } from '../../hooks/misc';
import { formatDateTime } from '../../lib/dates';
import { sortBy } from '../../lib/format';
import { can } from '../../lib/permissions';
import { teacherRequestsApi } from './api';
import { ConflictList, DiffTable, StatusBadge } from './components';
import { ReplanPanel } from './ReplanPanel';
import type { ChangeRequest, RequestStatus } from './types';

type Filter = RequestStatus | 'alle';
const FILTERS: { value: Filter; label: string }[] = [
  { value: 'offen', label: 'Offen' },
  { value: 'genehmigt', label: 'Genehmigt' },
  { value: 'abgelehnt', label: 'Abgelehnt' },
  { value: 'zurueckgezogen', label: 'Zurückgezogen' },
  { value: 'alle', label: 'Alle' },
];

function isFilter(v: string | null): v is Filter {
  return !!v && FILTERS.some((f) => f.value === v);
}

function RequestDetail({ id, onDecided }: { id: number; onDecided: (status: RequestStatus) => void }) {
  const toast = useToast();
  const user = useUser();
  const q = useApi<ChangeRequest>(() => teacherRequestsApi.get(id), [id], { live: ['teacher_requests', 'teachers', 'timetable', 'courses', 'settings'] });
  const [comment, setComment] = useState('');
  const [after, setAfter] = useState<ChangeRequest['conflicts'] | null>(null);
  useEffect(() => {
    setComment('');
    setAfter(null);
  }, [id]);
  const r = q.data;
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!r) return <Loading label="Antrag wird geladen …" />;
  const open = r.status === 'offen';
  const isException = r.kind === 'ausnahme';
  const outside = (after ?? r.conflicts)?.outside_windows.length ?? 0;

  const decide = async (approve: boolean) => {
    try {
      if (approve) {
        const res = await teacherRequestsApi.approve(r.id, comment);
        toast.success(`Antrag von ${r.teacher_name} genehmigt – die Änderung gilt jetzt.`);
        if (isException) toast.info('Die Abwesenheit wurde angelegt – sie erscheint im Vertretungsplan.');
        if (res.conflicts && res.conflicts.count > 0) {
          setAfter(res.conflicts);
          toast.warning('Der aktuelle Stundenplan passt noch nicht zum neuen Profil', res.conflicts.messages);
        }
      } else {
        await teacherRequestsApi.reject(r.id, comment);
        toast.info(`Antrag von ${r.teacher_name} abgelehnt.`);
      }
      setComment('');
      q.reload();
      onDecided(approve ? 'genehmigt' : 'abgelehnt');
    } catch (e) {
      toast.error(e, approve ? 'Genehmigen' : 'Ablehnen');
    }
  };

  return (
    <div className="stack">
      <section className="card stack" aria-labelledby="tr-detail-h">
        <div className="card-head" style={{ marginBottom: 0 }}>
          <h2 id="tr-detail-h" style={{ margin: 0 }}>
            {r.teacher_name}{' '}
            <span className="muted small mono">
              <TeacherAbbr id={r.teacher_id} fallback={r.teacher_name} />
            </span>
          </h2>
          <StatusBadge status={r.status} label={r.auto ? 'direkt übernommen' : r.status_label} />
        </div>
        <p className="small muted" style={{ margin: 0 }}>
          gestellt {formatDateTime(r.created_at)}
          {r.user_name ? ` von ${r.user_name}` : ''}
          {r.updated_at ? ` · geändert ${formatDateTime(r.updated_at)}` : ''}
          {r.decided_at ? ` · entschieden ${formatDateTime(r.decided_at)}${r.reviewer_name ? ` von ${r.reviewer_name}` : ''}` : ''}
        </p>
        {r.note && (
          <div>
            <div className="small muted">Begründung der Lehrkraft</div>
            <p className="tp-note small">{r.note}</p>
          </div>
        )}
        {isException ? (
          <>
            <h3 style={{ margin: 0 }}>Einmalige Ausnahme</h3>
            <p style={{ margin: 0 }}>
              <strong>{r.exception_text}</strong>
              {r.exception?.reason ? ` – ${r.exception.reason}` : ''}
            </p>
            {r.impact && (
              <div>
                <p className="small" style={{ margin: 0 }}>
                  {r.impact.text}
                </p>
                {r.impact.lessons.length > 0 && (
                  <ul className="small">
                    {r.impact.lessons.map((l, i) => (
                      <li key={i}>
                        {formatDateTime(`${l.date}T12:00:00`).split(',')[0]} · {l.period + 1}. Stunde · {l.label} ({l.classes.join(', ')})
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </>
        ) : (
          <>
            <h3 style={{ margin: 0 }}>Vergleich bisher / neu</h3>
            <DiffTable diff={r.diff} />
            {r.load && (
              <p className="small" style={{ margin: 0 }}>
                Aktuell {r.load.hours} Wochenstunden in {r.load.courses.length} Kursen
              </p>
            )}
            {(open || after) && <ConflictList conflicts={after ?? r.conflicts} title={open ? 'Auswirkungen bei Genehmigung' : 'Auswirkungen'} />}
          </>
        )}
        {!open && r.review_comment && (
          <div>
            <div className="small muted">Kommentar der Prüfung</div>
            <p className="tp-note small">{r.review_comment}</p>
          </div>
        )}
        {open && (
          <div className="stack-sm">
            <Field label="Kommentar an die Lehrkraft (optional)" htmlFor="tr-comment" hint="Wird verschlüsselt gespeichert; die Lehrkraft sieht ihn in ihrem Profil.">
              <textarea id="tr-comment" className="tp-text" value={comment} maxLength={2000} onChange={(e) => setComment(e.target.value)} />
            </Field>
            <div className="row">
              <AsyncButton className="btn btn-primary" onClick={() => decide(true)}>
                <Icon name="check" /> Genehmigen
              </AsyncButton>
              <AsyncButton className="btn btn-danger" confirm={`Antrag von ${r.teacher_name} ablehnen?`} onClick={() => decide(false)}>
                <Icon name="x" /> Ablehnen
              </AsyncButton>
            </div>
          </div>
        )}
        <div className="row">
          <Link className="btn btn-sm" to={`/stundenplan/teacher/${encodeURIComponent(r.teacher_id)}`}>
            <Icon name="grid" /> Stundenplan der Lehrkraft
          </Link>
          {can(user, 'masterdata.edit') && (
            <Link className="btn btn-sm" to={`/stammdaten/teachers?lehrkraft=${encodeURIComponent(r.teacher_id)}`}>
              <Icon name="database" /> Stammdaten
            </Link>
          )}
        </div>
      </section>
      {/* Neuplanung erst, wenn die Änderung gilt – vorher rechnete der Generator mit den alten Zeiten */}
      {can(user, 'timetable.generate') && r.status === 'genehmigt' && !isException && (
        <ReplanPanel teacherId={r.teacher_id} teacherName={r.teacher_name} outsideCount={outside} />
      )}
    </div>
  );
}

function ReplanAnyTeacher({ initial }: { initial?: string }) {
  const teachers = useCollection('teachers');
  const [tid, setTid] = useState<string | null>(initial ?? null);
  const options: SelectOption[] = useMemo(() => sortBy(teachers.data ?? [], (t) => t.name).map((t) => ({ value: t.id, label: t.name, sub: t.id })), [teachers.data]);
  const name = teachers.data?.find((t) => t.id === tid)?.name ?? tid ?? '';
  return (
    <details className="card disclosure" open={!!initial}>
      <summary>Stundenplan einer beliebigen Lehrkraft neu planen</summary>
      <div className="row" style={{ alignItems: 'flex-end' }}>
        <div className="grow">
          <SearchSelect label="Lehrkraft" options={options} value={tid} onChange={setTid} allowClear />
        </div>
        <HelpTip>Zum Beispiel nach einer direkt übernommenen Änderung (Einstellung „sofort gültig“) oder nach Änderungen in den Stammdaten.</HelpTip>
      </div>
      {tid && (
        <div style={{ marginTop: 12 }}>
          <ReplanPanel key={tid} teacherId={tid} teacherName={name} />
        </div>
      )}
    </details>
  );
}

export default function TeacherRequestsPage() {
  useTitle('Anträge von Lehrkräften');
  const user = useUser();
  const { data: settings } = useSettings();
  const [params, setParams] = useSearchParams();
  const status: Filter = isFilter(params.get('status')) ? (params.get('status') as Filter) : 'offen';
  const teacherFilter = params.get('lehrkraft') || undefined;
  const selected = Number(params.get('antrag')) || null;
  const list = useApi<ChangeRequest[]>(() => teacherRequestsApi.list(status, teacherFilter), [status, teacherFilter], { live: ['teacher_requests'] });
  const teachers = useCollection('teachers');
  const teacherOptions: SelectOption[] = useMemo(() => sortBy(teachers.data ?? [], (t) => t.name).map((t) => ({ value: t.id, label: t.name, sub: t.id })), [teachers.data]);
  const mode = (settings as { teacher_self_service?: string } | undefined)?.teacher_self_service ?? 'approval';

  const setParam = (key: string, value: string | null) => {
    const sp = new URLSearchParams(params);
    if (value) sp.set(key, value);
    else sp.delete(key);
    if (key !== 'antrag') sp.delete('antrag');
    setParams(sp, { replace: key !== 'antrag' });
  };

  const rows = list.data ?? [];
  const current = selected && rows.some((r) => r.id === selected) ? selected : null;
  const wide = useMediaQuery('(min-width: 1100px)');
  const narrow = useMediaQuery('(max-width: 700px)');
  const detailRef = useRef<HTMLDivElement | null>(null);

  // breite Ansicht: ersten Antrag vorwählen (auf dem Handy erst nach Antippen)
  useEffect(() => {
    if (!wide || current || !rows.length) return;
    const sp = new URLSearchParams(params);
    sp.set('antrag', String(rows[0]?.id));
    setParams(sp, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wide, current, rows.length]);

  const choose = (id: number) => {
    setParam('antrag', String(id));
    if (!wide) {
      const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
      window.setTimeout(() => detailRef.current?.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' }), 50);
    }
  };

  return (
    <div className="page stack">
      <div className="page-head">
        <div>
          <h1>
            Anträge von Lehrkräften
            <HelpTip>
              Lehrkräfte pflegen Fächer, Wunschklassen, Deputat und Sperrzeiten (auch „ab Datum“) selbst und beantragen einmalige Ausnahmen. Anträge von Schüler/innen und Eltern (z. B. Beurlaubung) laufen über die{' '}
              <Link to="/formulare">Formulare</Link>.
            </HelpTip>
          </h1>
          <p className="muted" style={{ margin: 0 }}>
            {mode === 'direct' ? 'Einstellung: Änderungen gelten sofort (hier nur zur Kontrolle).' : 'Einstellung: Änderungen brauchen eine Genehmigung.'}
          </p>
        </div>
        {can(user, 'settings.edit') && (
          <div className="actions">
            <Link className="btn btn-sm" to="/planung/regeln">
              <Icon name="cog" /> Einstellung ändern
            </Link>
          </div>
        )}
      </div>

      <div className="toolbar card" style={{ padding: 12 }}>
        {narrow ? (
          <Field label="Status" htmlFor="tr-status">
            <select id="tr-status" value={status} onChange={(e) => setParam('status', e.target.value === 'offen' ? null : e.target.value)}>
              {FILTERS.map((f) => (
                <option key={f.value} value={f.value}>
                  {f.label}
                </option>
              ))}
            </select>
          </Field>
        ) : (
          <div className="field" style={{ minWidth: 0 }}>
            <span className="field-label">Status</span>
            <SegmentedControl label="Status" value={status} options={FILTERS} onChange={(v) => setParam('status', v === 'offen' ? null : v)} />
          </div>
        )}
        <div className="field">
          <SearchSelect label="Lehrkraft" options={teacherOptions} value={teacherFilter ?? null} onChange={(v) => setParam('lehrkraft', v)} allowClear placeholder="alle Lehrkräfte" />
        </div>
      </div>

      {list.error ? <ErrorBox error={list.error} onRetry={list.reload} /> : null}
      {list.initialLoading && <Loading />}
      {list.data && rows.length === 0 && (
        <Empty icon="checkCircle">{status === 'offen' ? 'Keine offenen Anträge.' : 'Keine Anträge für diesen Filter.'}</Empty>
      )}
      {rows.length > 0 && (
        <div className="tp-layout">
          <ul className="tp-req-list" aria-label="Anträge">
            {rows.map((r) => {
              const n = r.conflicts?.count ?? 0;
              return (
                <li key={r.id}>
                  <button type="button" className="tp-req" aria-current={current === r.id ? 'true' : undefined} onClick={() => choose(r.id)}>
                    <span>
                      <strong>{r.teacher_name}</strong>{' '}
                      <span className="mono small muted">
                        <TeacherAbbr id={r.teacher_id} fallback={r.teacher_name} />
                      </span>
                      <span className="meta" style={{ display: 'block' }}>
                        {r.kind === 'ausnahme' ? `Ausnahme: ${r.exception_text}` : r.diff.map((d) => d.label).join(', ') || 'keine inhaltliche Änderung'}
                      </span>
                      <span className="meta" style={{ display: 'block' }}>
                        {formatDateTime(r.updated_at ?? r.created_at)}
                      </span>
                    </span>
                    <span className="stack-sm" style={{ justifyItems: 'end' }}>
                      <StatusBadge status={r.status} label={r.auto ? 'direkt' : r.status_label} />
                      {r.status === 'offen' && n > 0 && <span className="badge badge-warning">{n} Konflikt{n === 1 ? '' : 'e'}</span>}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
          <div ref={detailRef} style={{ scrollMarginTop: 72 }}>
            {current ? (
              <RequestDetail
                id={current}
                onDecided={(st) => {
                  // entschiedenen Antrag sichtbar lassen (u. a. für „neu planen“)
                  const sp = new URLSearchParams(params);
                  sp.set('status', st);
                  sp.set('antrag', String(current));
                  setParams(sp, { replace: true });
                  list.reload();
                }}
              />
            ) : (
              <p className="muted small card">{wide ? 'Bitte links einen Antrag auswählen.' : 'Bitte oben einen Antrag antippen.'}</p>
            )}
          </div>
        </div>
      )}
      {can(user, 'timetable.generate') && <ReplanAnyTeacher key={!current ? (teacherFilter ?? '') : ''} initial={!current ? teacherFilter : undefined} />}
    </div>
  );
}

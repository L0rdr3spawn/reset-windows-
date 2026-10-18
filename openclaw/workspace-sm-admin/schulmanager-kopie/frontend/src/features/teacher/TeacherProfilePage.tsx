/**
 * „Mein Profil als Lehrkraft“ (/lehrkraft/profil): Fächer, Wunschklassen, Deputat, Arbeitszeitfenster und Wünsche
 * selbst pflegen – je nach Schuleinstellung als Antrag (Genehmigung durch die Planung) oder sofort gültig.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ApiError } from '../../api/client';
import { TeacherAbbr } from '../../components/Abbr';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { MultiSelect, type SelectOption } from '../../components/SearchSelect';
import { Alert, AsyncButton, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useLive } from '../../hooks/useLive';
import { useDebounced, useTitle } from '../../hooks/misc';
import { formatDateTime } from '../../lib/dates';
import { teacherProfileApi } from './api';
import { ConflictList, DiffTable, StatusBadge } from './components';
import { AvailabilityEditor } from './AvailabilityEditor';
import { detachRules, todayISO } from './availability';
import { ExceptionCard } from './ExceptionCard';
import type { ChangeRequest, MyProfileResponse, NewSubject, PreviewResponse, TeacherProfile } from './types';
import { profileDays, profileEqual } from './windows';

/** Profil für die Oberfläche: Sperrzeiten immer als normale Regeln (alte Anträge ohne `unavailable` übernehmen die
 * aktuellen), Zeitfenster/Raster gibt es dort nicht mehr. */
function normProfile(p: TeacherProfile, current: TeacherProfile): TeacherProfile {
  return { ...p, unavailable: detachRules(p.unavailable ?? current.unavailable ?? []), wishes: p.wishes ?? [], time_windows: [], work_grid: {} };
}

/** Das, was an den Server geht: ohne die leeren Altformate. */
function profilePayload(p: TeacherProfile): Omit<TeacherProfile, 'time_windows' | 'work_grid'> {
  const { time_windows: _tw, work_grid: _wg, ...rest } = p;
  void _tw;
  void _wg;
  return rest;
}

const STATUS_TEXT: Record<string, string> = {
  genehmigt: 'Ihr Antrag wurde genehmigt – die Änderung gilt jetzt.',
  abgelehnt: 'Ihr Antrag wurde abgelehnt.',
};

const SUBJECT_ID_BAD = /[/#?\\,;|]/;

/** „Fach fehlt?“ – Vorschlag für ein neues Fach (Kürzel, Name, Fachraum-Typ); wird erst nach Genehmigung angelegt. */
function ProposeSubject({ existing, proposed, onAdd }: { existing: { id: string; name: string }[]; proposed: NewSubject[]; onAdd: (s: NewSubject) => void }) {
  const [open, setOpen] = useState(false);
  const [id, setId] = useState('');
  const [name, setName] = useState('');
  const [roomType, setRoomType] = useState('');
  const code = id.trim();
  const clash = existing.find((s) => s.id.toLowerCase() === code.toLowerCase() || (name.trim() && s.name.toLowerCase() === name.trim().toLowerCase()));
  const error = !code ? null : SUBJECT_ID_BAD.test(code) ? 'Keine Zeichen / # ? \\ , ; |' : proposed.some((p) => p.id === code) ? 'Schon vorgeschlagen' : null;
  if (!open) {
    return (
      <button type="button" className="btn btn-ghost btn-sm" onClick={() => setOpen(true)} disabled={proposed.length >= 5}>
        <Icon name="plus" /> Fach fehlt? Vorschlagen
      </button>
    );
  }
  return (
    <fieldset className="stack-sm">
      <legend className="small">Neues Fach vorschlagen</legend>
      <div className="form-grid">
        <Field label="Kürzel" htmlFor="tp-ns-id" error={error}>
          <input id="tp-ns-id" type="text" maxLength={20} value={id} onChange={(e) => setId(e.target.value)} />
        </Field>
        <Field label="Name" htmlFor="tp-ns-name">
          <input id="tp-ns-name" type="text" maxLength={80} value={name} onChange={(e) => setName(e.target.value)} />
        </Field>
        <Field label="Fachraum-Typ" htmlFor="tp-ns-room" hint="Leer = Klassenraum, sonst z. B. „Werkraum“ oder „Informatik“">
          <input id="tp-ns-room" type="text" maxLength={40} value={roomType} onChange={(e) => setRoomType(e.target.value)} placeholder="Klassenraum" />
        </Field>
      </div>
      {clash && (
        <p className="small" role="status" style={{ margin: 0 }}>
          Vorhanden: {clash.id} – {clash.name}. Bitte oben auswählen.
        </p>
      )}
      <div className="row">
        <button
          type="button"
          className="btn btn-sm btn-primary"
          disabled={!code || !name.trim() || !!error || !!clash}
          onClick={() => {
            onAdd({ id: code, name: name.trim(), room_type: roomType.trim() || null });
            setId('');
            setName('');
            setRoomType('');
            setOpen(false);
          }}
        >
          Übernehmen
        </button>
        <button type="button" className="btn btn-sm" onClick={() => setOpen(false)}>
          Abbrechen
        </button>
      </div>
    </fieldset>
  );
}

function RequestHistory({ requests }: { requests: ChangeRequest[] }) {
  const done = requests.filter((r) => r.status !== 'offen');
  if (!done.length) return <p className="small muted">Noch keine Änderungen.</p>;
  return (
    <ul className="list-plain tp-history">
      {done.slice(0, 10).map((r) => (
        <li key={r.id} className="card" style={{ padding: 12 }}>
          <div className="row-between">
            <span className="row" style={{ gap: 8 }}>
              <StatusBadge status={r.status} label={r.auto ? 'direkt übernommen' : r.status_label} />
              <span className="small muted">{formatDateTime(r.decided_at ?? r.created_at)}</span>
            </span>
            {r.reviewer_name && <span className="small muted">geprüft von {r.reviewer_name}</span>}
          </div>
          <p className="small" style={{ margin: '6px 0 0' }}>
            {r.diff.map((d) => d.label).join(', ') || 'keine inhaltliche Änderung'}
          </p>
          {r.review_comment && <p className="tp-note small">{r.review_comment}</p>}
        </li>
      ))}
    </ul>
  );
}

export default function TeacherProfilePage() {
  useTitle('Mein Profil als Lehrkraft');
  const toast = useToast();
  const q = useApi<MyProfileResponse>(() => teacherProfileApi.mine(), [], {
    live: ['teacher_requests', 'teacher_profile', 'teachers', 'settings', 'timetable', 'courses'],
  });
  const data = q.data;
  const [draft, setDraft] = useState<TeacherProfile | null>(null);
  const [note, setNote] = useState('');
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const lastStatus = useRef<Map<number, string>>(new Map());

  // Entwurf aus dem Server-Stand (offener Antrag hat Vorrang) initialisieren – nur wenn nichts bearbeitet wurde
  const rawBase: TeacherProfile | null = data ? (data.pending?.payload ?? data.profile) : null;
  const base: TeacherProfile | null = data && rawBase ? normProfile(rawBase, data.profile) : null;
  const dirty = !!(draft && base && !profileEqual(draft, base));
  useEffect(() => {
    if (base && !dirty) setDraft(structuredClone(base));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  // Entscheidung über eigenen Antrag live melden
  useLive(['teacher_requests'], (ev) => {
    const e = ev as (typeof ev & { request_id?: number; status?: string }) | null;
    if (e?.request_id && e.status && STATUS_TEXT[e.status] && lastStatus.current.get(e.request_id) === 'offen') {
      if (e.status === 'genehmigt') toast.success(STATUS_TEXT[e.status]);
      else toast.warning(STATUS_TEXT[e.status] ?? '');
    }
  });
  useEffect(() => {
    for (const r of data?.requests ?? []) lastStatus.current.set(r.id, r.status);
  }, [data]);

  // Vorschau (Konflikte, Verfügbarkeit) entprellt vom Server
  const debounced = useDebounced(draft, 350);
  useEffect(() => {
    if (!debounced || !data) return undefined;
    let alive = true;
    teacherProfileApi
      .previewMine(profilePayload(debounced))
      .then((r) => {
        if (!alive) return;
        setPreview(r);
        setPreviewError(null);
      })
      .catch((e: unknown) => alive && setPreviewError(e instanceof ApiError ? e.message : String(e)));
    return () => {
      alive = false;
    };
  }, [debounced, data]);

  const subjectOptions: SelectOption[] = useMemo(() => (data?.options.subjects ?? []).map((s) => ({ value: s.id, label: `${s.id} – ${s.name}` })), [data]);
  const classOptions: SelectOption[] = useMemo(
    () => (data?.options.classes ?? []).map((c) => ({ value: c.id, label: c.name === c.id ? c.id : `${c.id} – ${c.name}`, sub: `Jg. ${c.grade}` })),
    [data],
  );

  if (q.error) {
    const conflict = q.error instanceof ApiError && q.error.status === 409;
    return (
      <div className="page-narrow">
        <h1>Mein Profil als Lehrkraft</h1>
        {conflict ? (
          <Alert kind="warning" title="Kein Lehrkraft-Profil verknüpft">
            {(q.error as ApiError).message}
          </Alert>
        ) : (
          <ErrorBox error={q.error} onRetry={q.reload} />
        )}
      </div>
    );
  }
  if (!data || !draft) return <Loading label="Profil wird geladen …" />;

  const o = data.options;
  const approval = data.mode === 'approval';
  const set = <K extends keyof TeacherProfile>(k: K, v: TeacherProfile[K]) => setDraft((d) => (d ? { ...d, [k]: v } : d));
  const changedVsCurrent = !profileEqual(draft, normProfile(data.profile, data.profile));
  const timesEditable = data.can_edit_times !== false;
  const lastDecided = data.requests.find((r) => r.status === 'genehmigt' || r.status === 'abgelehnt');
  const proposed = draft.new_subjects ?? [];
  const proposedIds = new Set(proposed.map((n) => n.id));

  const save = async () => {
    try {
      const r = await teacherProfileApi.saveMine({ ...profilePayload(draft), note });
      if (r.status === 'applied') toast.success('Ihre Änderungen gelten ab sofort.');
      else if (!approval && draft.new_subjects?.length) toast.success('Antrag gesendet – neue Fächer legt die Stundenplanung nach Prüfung an.');
      else toast.success('Antrag gesendet – die Stundenplanung prüft Ihre Änderung.');
      if (r.conflicts.count) toast.warning('Hinweis: Ihre Änderung betrifft den aktuellen Stundenplan', r.conflicts.messages);
      setNote('');
      q.reload();
    } catch (e) {
      toast.error(e, 'Speichern');
    }
  };

  return (
    <div className="page stack">
      <div className="page-head">
        <div>
          <h1>Mein Profil als Lehrkraft</h1>
          <p className="muted" style={{ margin: 0 }}>
            {data.name} (<TeacherAbbr id={data.teacher_id} fallback={data.name} />) · Verfügbarkeit: {data.description}
          </p>
        </div>
        <div className="actions">
          <Link className="btn" to={`/stundenplan/teacher/${encodeURIComponent(data.teacher_id)}`}>
            <Icon name="grid" /> Mein Stundenplan
          </Link>
        </div>
      </div>

      <Alert kind="info" title={approval ? 'Änderungen werden geprüft' : 'Änderungen gelten sofort'}>
        {approval
          ? 'Ihre Angaben gehen als Antrag an die Stundenplanung bzw. Schulleitung. Bis zur Entscheidung gilt Ihr bisheriges Profil.'
          : 'Ihre Angaben werden sofort übernommen. Liegen danach Stunden außerhalb Ihrer Zeitfenster, plant die Stundenplanung Ihren Stundenplan neu.'}
      </Alert>

      {data.pending && (
        <section className="card" aria-labelledby="tp-pending-h">
          <div className="card-head">
            <h2 id="tp-pending-h">Offener Antrag</h2>
            <StatusBadge status="offen" label="wird geprüft" />
          </div>
          <p className="small muted" style={{ marginTop: 0 }}>
            gestellt {formatDateTime(data.pending.created_at)}
            {data.pending.updated_at ? ` · zuletzt geändert ${formatDateTime(data.pending.updated_at)}` : ''}
          </p>
          <DiffTable diff={data.pending.diff} />
          {data.pending.note && <p className="tp-note small">{data.pending.note}</p>}
          <div className="row" style={{ marginTop: 12 }}>
            <AsyncButton
              className="btn btn-sm"
              confirm="Offenen Antrag zurückziehen?"
              onClick={async () => {
                try {
                  await teacherProfileApi.withdraw();
                  toast.success('Antrag zurückgezogen');
                  setDraft(null);
                  q.reload();
                } catch (e) {
                  toast.error(e);
                }
              }}
            >
              <Icon name="undo" /> Antrag zurückziehen
            </AsyncButton>
            <span className="small muted">Erneutes Absenden aktualisiert den offenen Antrag.</span>
          </div>
        </section>
      )}

      {!data.pending && lastDecided && lastDecided.status === 'abgelehnt' && (
        <Alert kind="warning" title={`Letzter Antrag abgelehnt (${formatDateTime(lastDecided.decided_at)})`}>
          {lastDecided.review_comment || 'Ohne Begründung.'}
        </Alert>
      )}

      {data.conflicts.outside_windows.length > 0 && (
        <Alert kind="warning" title="Ihr aktueller Stundenplan passt noch nicht zu Ihren Zeitfenstern">
          {data.conflicts.outside_windows.length} Unterrichtsblöcke liegen außerhalb Ihrer Zeitfenster.
          <HelpTip>Die Stundenplanung plant Ihren Stundenplan neu; bis dahin gilt der bisherige Plan.</HelpTip>
        </Alert>
      )}

      <form
        className="stack"
        onSubmit={(e) => {
          e.preventDefault();
          void save();
        }}
      >
        <div className="grid grid-2">
          <section className="card stack" aria-labelledby="tp-subj-h">
            <h2 id="tp-subj-h">
              Fächer & Klassen
              <HelpTip>Wunschklassen werden bei der nächsten Zuweisung der Lehrkräfte bevorzugt, ohne Garantie.</HelpTip>
            </h2>
            <MultiSelect
              label="Fächer, die ich unterrichten kann (Lehrbefähigung)"
              options={subjectOptions}
              values={draft.subjects.filter((x) => !proposedIds.has(x))}
              onChange={(v) => set('subjects', v)}
            />
            {proposed.length > 0 && (
              <div className="chips" aria-label="Vorgeschlagene neue Fächer">
                {proposed.map((n) => (
                  <span className="chip" key={n.id}>
                    {n.id} – {n.name} <span className="badge badge-info">Vorschlag</span>
                    <button
                      type="button"
                      aria-label={`Vorschlag ${n.id} entfernen`}
                      onClick={() =>
                        setDraft((d) => (d ? { ...d, subjects: d.subjects.filter((x) => x !== n.id), new_subjects: (d.new_subjects ?? []).filter((x) => x.id !== n.id) } : d))
                      }
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
            <ProposeSubject
              existing={o.subjects}
              proposed={proposed}
              onAdd={(n) => setDraft((d) => (d ? { ...d, new_subjects: [...(d.new_subjects ?? []), n] } : d))}
            />
            <MultiSelect
              label="Klassen, die ich hauptsächlich unterrichte"
              options={classOptions}
              values={draft.preferred_classes}
              onChange={(v) => set('preferred_classes', v)}
              placeholder="Klasse hinzufügen …"
            />
          </section>
          <section className="card stack" aria-labelledby="tp-hours-h">
            <h2 id="tp-hours-h">Deputat</h2>
            <Field label="Wochenstunden (Deputat)" htmlFor="tp-hours" hint={`Zurzeit unterrichten Sie ${data.load.hours} Stunden pro Woche.`}>
              <input
                id="tp-hours"
                type="number"
                min={0}
                max={40}
                value={draft.max_hours}
                onChange={(e) => set('max_hours', Math.max(0, Math.min(40, parseInt(e.target.value || '0', 10))))}
              />
            </Field>
            <details className="disclosure">
              <summary>Mein Unterricht ({data.load.courses.length} Kurse)</summary>
              <ul className="small">
                {data.load.courses.map((c) => (
                  <li key={c.id}>
                    {c.classes.join(', ')} · {c.subjects.join('/')} · {c.hours} Std. <span className="muted">({c.label})</span>
                  </li>
                ))}
              </ul>
            </details>
          </section>
        </div>

        <section className="card stack" aria-labelledby="tp-win-h">
          <h2 id="tp-win-h">
            Verfügbarkeit: Sperrzeiten und Wünsche
            <HelpTip>
              Sperrzeit = nie Unterricht, Wunsch = möglichst keiner. Jeder Block hat sein eigenes Raster, einen Rhythmus (z. B. alle 2 Wochen) und optional ein Datum „gilt ab“.
              {!timesEditable || approval
                ? ' Änderungen an Sperrzeiten gehen als Antrag an die Stundenplanung bzw. Schulleitung; Wünsche gelten ' + (approval ? 'nach Prüfung.' : 'sofort.')
                : ''}{' '}
              Nur für einen einzelnen Termin: unten „Einmalige Ausnahme“.
            </HelpTip>
          </h2>
          <AvailabilityEditor
            unavailable={draft.unavailable ?? []}
            wishes={draft.wishes}
            onChange={(v) => setDraft((d) => (d ? { ...d, unavailable: v.unavailable, wishes: v.wishes, time_windows: [], work_grid: {} } : d))}
            days={profileDays(o)}
            periods={o.periods}
            periodTimes={o.period_times}
            periodMinutes={o.period_minutes}
            hours={draft.max_hours}
            conflicts={preview?.conflicts.outside_windows ?? []}
            defaultValidFrom={todayISO()}
          />
        </section>

        <section className="card stack" aria-labelledby="tp-send-h">
          <h2 id="tp-send-h">{approval ? 'Antrag stellen' : 'Speichern'}</h2>
          {previewError && <Alert kind="error" title="Prüfung fehlgeschlagen">{previewError}</Alert>}
          {preview && changedVsCurrent && <DiffTable diff={preview.diff} />}
          {preview && <ConflictList conflicts={preview.conflicts} />}
          <Field label="Begründung / Hinweis (optional)" htmlFor="tp-note" hint="Wird verschlüsselt gespeichert und ist nur für die Stundenplanung/Schulleitung sichtbar.">
            <textarea id="tp-note" className="tp-text" value={note} maxLength={2000} onChange={(e) => setNote(e.target.value)} />
          </Field>
          <div className="row">
            <AsyncButton type="submit" className="btn btn-primary" onClick={save} disabled={!changedVsCurrent}>
              <Icon name="check" /> {approval ? (data.pending ? 'Antrag aktualisieren' : 'Änderung beantragen') : 'Änderungen speichern'}
            </AsyncButton>
            <button type="button" className="btn" disabled={!dirty} onClick={() => setDraft(structuredClone(base as TeacherProfile))}>
              Zurücksetzen
            </button>
            {!changedVsCurrent && <span className="small muted">Keine Änderungen gegenüber Ihrem aktuellen Profil.</span>}
          </div>
        </section>
      </form>

      <ExceptionCard periods={o.periods} periodTimes={o.period_times} items={data.exceptions ?? []} onChanged={q.reload} />

      <section className="card" aria-labelledby="tp-hist-h">
        <h2 id="tp-hist-h">Verlauf</h2>
        <RequestHistory requests={data.requests} />
      </section>
    </div>
  );
}

/**
 * Selbsttests eines Kursraums: Liste, Anlegen/Bearbeiten (Fragen aus der Sammlung, Versuche, Zeitlimit, Mischen,
 * Rückmeldung), Durchführen und Auswertung je Schüler/in und Frage. Kein volles Quiz-System.
 */
import { useMemo, useState } from 'react';
import { errorMessage } from '../../api/client';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton, Empty, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { formatDateTime } from '../../lib/dates';
import { fromLocalInput, toLocalInput } from '../channels/logic';
import { learnApi, type BankQuestion, type ReviewMode, type Selftest, type TestResults, type TestStatus } from './api';
import { fractionTone, moveId, numberText, percentText, pointsText, QUESTION_TYPE_LABELS, REVIEW_LABELS, TEST_STATE_LABELS, testRules } from './logic';
import { TestRunner } from './TestRunner';
import './lernen.css';

const TONE = { entwurf: 'badge-warning', offen: 'badge-success', geschlossen: 'badge-primary', geplant: 'badge-info' } as const;

// ------------------------------------------------------------------------------------------ Bearbeiten
function TestEditor({ channelId, test, onClose, onSaved }: { channelId: number; test: Selftest | null; onClose: () => void; onSaved: () => void }) {
  const bank = useApi((signal) => learnApi.questions(channelId, signal), [channelId]);
  const [title, setTitle] = useState(test?.title ?? '');
  const [description, setDescription] = useState(test?.description ?? '');
  const [status, setStatus] = useState<TestStatus>(test?.status ?? 'entwurf');
  const [ids, setIds] = useState<number[]>(test?.question_ids ?? []);
  const [attempts, setAttempts] = useState(test?.max_attempts ? String(test.max_attempts) : '');
  const [minutes, setMinutes] = useState(test?.time_limit_min ? String(test.time_limit_min) : '');
  const [pass, setPass] = useState(test?.pass_percent !== null && test?.pass_percent !== undefined ? String(test.pass_percent) : '');
  const [shuffleQ, setShuffleQ] = useState(test?.shuffle_questions ?? false);
  const [shuffleA, setShuffleA] = useState(test?.shuffle_answers ?? true);
  const [immediate, setImmediate] = useState(test?.immediate_feedback ?? false);
  const [review, setReview] = useState<ReviewMode>(test?.review ?? 'full');
  const [opens, setOpens] = useState(toLocalInput(test?.opens_at));
  const [closes, setCloses] = useState(toLocalInput(test?.closes_at));
  const [search, setSearch] = useState('');
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const byId = useMemo(() => new Map((bank.data?.questions ?? []).map((q) => [q.id, q])), [bank.data]);
  const chosen = ids.map((i) => byId.get(i)).filter((q): q is BankQuestion => !!q);
  const total = chosen.reduce((s, q) => s + q.points, 0);
  const rest = (bank.data?.questions ?? []).filter((q) => !ids.includes(q.id) && (!search.trim() || q.title.toLowerCase().includes(search.trim().toLowerCase())));
  const num = (s: string): number | null => (s.trim() === '' || Number.isNaN(Number(s.replace(',', '.'))) ? null : Number(s.replace(',', '.')));

  const save = async () => {
    setError(null);
    if (!title.trim()) return setError('Bitte einen Titel eingeben.');
    if (status === 'offen' && !ids.length) return setError('Zum Freigeben braucht der Test mindestens eine Frage.');
    const passPct = num(pass);
    if (passPct !== null && (passPct < 0 || passPct > 100)) return setError('Bestehensgrenze: 0 bis 100 Prozent.');
    const body = {
      title: title.trim(),
      description,
      status,
      question_ids: ids,
      shuffle_questions: shuffleQ,
      shuffle_answers: shuffleA,
      immediate_feedback: immediate,
      review,
    };
    try {
      if (test) {
        await learnApi.patchTest(channelId, test.id, {
          ...body,
          max_attempts: num(attempts),
          clear_max_attempts: num(attempts) === null,
          time_limit_min: num(minutes),
          clear_time_limit: num(minutes) === null,
          pass_percent: passPct,
          clear_pass_percent: passPct === null,
          opens_at: fromLocalInput(opens),
          clear_opens_at: !opens,
          closes_at: fromLocalInput(closes),
          clear_closes_at: !closes,
        });
      } else {
        await learnApi.createTest(channelId, { ...body, max_attempts: num(attempts), time_limit_min: num(minutes), pass_percent: passPct, opens_at: fromLocalInput(opens), closes_at: fromLocalInput(closes) });
      }
      toast.success('Selbsttest gespeichert');
      onSaved();
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  return (
    <Modal
      title={test ? 'Selbsttest bearbeiten' : 'Neuer Selbsttest'}
      size="lg"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={save}>
            Speichern
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        {error && <Alert kind="error">{error}</Alert>}
        <Field label="Titel" htmlFor="st-title">
          <input id="st-title" type="text" maxLength={200} value={title} onChange={(e) => setTitle(e.target.value)} />
        </Field>
        <Field label="Beschreibung (optional)" htmlFor="st-desc">
          <textarea id="st-desc" rows={2} maxLength={3000} value={description} onChange={(e) => setDescription(e.target.value)} />
        </Field>
        <Field label="Status" htmlFor="st-status" help="Entwürfe sehen nur Lehrende. Beendete Tests können nicht mehr begonnen werden.">
          <select id="st-status" value={status} onChange={(e) => setStatus(e.target.value as TestStatus)}>
            <option value="entwurf">Entwurf</option>
            <option value="offen">Offen</option>
            <option value="geschlossen">Beendet</option>
          </select>
        </Field>

        <fieldset className="ln-fieldset">
          <legend>
            Fragen ({chosen.length}, {numberText(total, 2)} Punkte)
          </legend>
          {bank.loading && !bank.data ? <Loading /> : null}
          {chosen.length > 0 && (
            <ol className="ln-pick-list">
              {chosen.map((q, i) => (
                <li key={q.id} className="ln-edit-row">
                  <span className="ln-gap-no">{i + 1}.</span>
                  <span className="ln-pick-title">{q.title}</span>
                  <span className="small muted">{numberText(q.points, 2)} P.</span>
                  <button type="button" className="btn btn-sm btn-ghost" aria-label="Nach oben" disabled={i === 0} onClick={() => setIds((l) => moveId(l, q.id, -1))}>
                    ↑
                  </button>
                  <button type="button" className="btn btn-sm btn-ghost" aria-label="Nach unten" disabled={i === chosen.length - 1} onClick={() => setIds((l) => moveId(l, q.id, 1))}>
                    ↓
                  </button>
                  <button type="button" className="btn btn-sm btn-ghost" aria-label={`Frage ${i + 1} entfernen`} onClick={() => setIds((l) => l.filter((x) => x !== q.id))}>
                    <Icon name="trash" />
                  </button>
                </li>
              ))}
            </ol>
          )}
          {bank.data && bank.data.questions.length === 0 && <p className="muted small">Die Fragensammlung ist noch leer – legen Sie zuerst Fragen an.</p>}
          {rest.length > 0 || search ? (
            <details open={chosen.length === 0}>
              <summary>Fragen hinzufügen</summary>
              <Field label="Suche" htmlFor="st-search">
                <input id="st-search" type="search" value={search} onChange={(e) => setSearch(e.target.value)} />
              </Field>
              <ul className="ln-pick-list">
                {rest.map((q) => (
                  <li key={q.id}>
                    <label className="check">
                      <input type="checkbox" checked={false} onChange={() => setIds((l) => [...l, q.id])} />
                      <span>{q.title}</span> <span className="badge badge-info">{QUESTION_TYPE_LABELS[q.type]}</span>
                    </label>
                  </li>
                ))}
              </ul>
            </details>
          ) : null}
        </fieldset>

        <div className="ln-three">
          <Field label="Versuche (leer = beliebig)" htmlFor="st-att">
            <input id="st-att" type="number" min={1} max={50} value={attempts} onChange={(e) => setAttempts(e.target.value)} />
          </Field>
          <Field label="Zeitlimit in Minuten (optional)" htmlFor="st-min">
            <input id="st-min" type="number" min={1} max={600} value={minutes} onChange={(e) => setMinutes(e.target.value)} />
          </Field>
          <Field label="Bestehen ab Prozent (optional)" htmlFor="st-pass" help="Wird als Abschlussbedingung und im Notenbuch genutzt. Gewertet wird der beste Versuch.">
            <input id="st-pass" type="text" inputMode="decimal" value={pass} onChange={(e) => setPass(e.target.value)} />
          </Field>
        </div>
        <div className="ln-two">
          <Field label="Beginn (optional)" htmlFor="st-open">
            <input id="st-open" type="datetime-local" value={opens} onChange={(e) => setOpens(e.target.value)} />
          </Field>
          <Field label="Ende (optional)" htmlFor="st-close">
            <input id="st-close" type="datetime-local" value={closes} onChange={(e) => setCloses(e.target.value)} />
          </Field>
        </div>
        <div className="ln-two">
          <label className="check">
            <input type="checkbox" checked={shuffleQ} onChange={(e) => setShuffleQ(e.target.checked)} /> Fragen mischen
          </label>
          <label className="check">
            <input type="checkbox" checked={shuffleA} onChange={(e) => setShuffleA(e.target.checked)} /> Antworten mischen
          </label>
          <label className="check">
            <input type="checkbox" checked={immediate} onChange={(e) => setImmediate(e.target.checked)} /> Rückmeldung sofort nach jeder Frage
          </label>
        </div>
        <Field label="Nach dem Abgeben zeigen" htmlFor="st-review">
          <select id="st-review" value={review} onChange={(e) => setReview(e.target.value as ReviewMode)}>
            {(Object.keys(REVIEW_LABELS) as ReviewMode[]).map((k) => (
              <option key={k} value={k}>
                {REVIEW_LABELS[k]}
              </option>
            ))}
          </select>
        </Field>
      </div>
    </Modal>
  );
}

// ------------------------------------------------------------------------------------------ Auswertung
function ResultsDialog({ channelId, test, onClose }: { channelId: number; test: Selftest; onClose: () => void }) {
  const q = useApi<TestResults>((signal) => learnApi.testResults(channelId, test.id, signal), [channelId, test.id]);
  const [view, setView] = useState<number | null>(null);
  const data = q.data;
  return (
    <>
      <Modal
        title={`Auswertung: ${test.title}`}
        size="lg"
        onClose={onClose}
        footer={
          <>
            <a className="btn" href={learnApi.testCsvUrl(channelId, test.id)} download>
              <Icon name="download" /> CSV
            </a>
            <button type="button" className="btn btn-primary" onClick={onClose}>
              Schließen
            </button>
          </>
        }
      >
        {q.error && !data ? (
          <ErrorBox error={q.error} onRetry={q.reload} />
        ) : !data ? (
          <Loading />
        ) : (
          <div className="stack">
            <p className="small muted">
              {data.students.filter((s) => s.finished).length} von {data.students.length} Teilnehmenden haben mindestens einen Versuch beendet · {numberText(data.max_points, 2)} Punkte möglich
            </p>
            <div className="ln-table-wrap">
              <table className="ln-table">
                <thead>
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Versuche</th>
                    <th scope="col">Punkte</th>
                    <th scope="col">Prozent</th>
                    {data.questions.map((qq, i) => (
                      <th key={qq.qid} scope="col" title={qq.title}>
                        F{i + 1}
                      </th>
                    ))}
                    <th scope="col">
                      <span className="sr-only">Ansehen</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[...data.students].sort((x, y) => Number(y.attempts > 0) - Number(x.attempts > 0)).map((s) => (
                    <tr key={s.user_id}>
                      <th scope="row">
                        {s.name}
                        {s.running ? <span className="badge badge-info ln-gap-badge">läuft</span> : null}
                      </th>
                      <td>{s.attempts}</td>
                      <td>{s.best_points === null ? '–' : numberText(s.best_points, 2)}</td>
                      <td>
                        {percentText(s.best_percent)}
                        {s.passed === true ? <span className="sr-only"> bestanden</span> : null}
                        {s.passed === false ? <span className="sr-only"> nicht bestanden</span> : null}
                      </td>
                      {data.questions.map((qq) => {
                        const f = s.per_question[String(qq.qid)];
                        return (
                          <td key={qq.qid} className={`ln-cell ln-${fractionTone(f)}`} title={f === undefined ? 'nicht bearbeitet' : `${numberText(f * qq.max, 2)} von ${numberText(qq.max, 2)}`}>
                            {f === undefined ? '' : f >= 0.999 ? '✓' : f > 0 ? '≈' : '✗'}
                          </td>
                        );
                      })}
                      <td>
                        {s.attempt_ids.length > 0 && (
                          <button type="button" className="btn btn-sm btn-ghost" onClick={() => setView(s.attempt_ids[s.attempt_ids.length - 1] as number)}>
                            Ansehen
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {data.questions.length > 0 && (
              <>
                <h4>Fragen</h4>
                <ol className="ln-qstats">
                  {data.questions.map((qq, i) => (
                    <li key={qq.qid}>
                      <span className="ln-qstat-no">F{i + 1}</span>
                      <span className="ln-qstat-title">{qq.title}</span>
                      <span className="small muted">
                        {QUESTION_TYPE_LABELS[qq.type]} · {qq.correct_share === null ? 'noch keine Antworten' : `${Math.round(qq.correct_share * 100)} % richtig (${qq.attempts} Versuche)`}
                      </span>
                    </li>
                  ))}
                </ol>
              </>
            )}
          </div>
        )}
      </Modal>
      {view !== null && <TestRunner channelId={channelId} testId={test.id} attemptId={view} onClose={() => setView(null)} onChanged={() => undefined} />}
    </>
  );
}

// ------------------------------------------------------------------------------------------ Liste
export default function SelftestsPanel({ channelId, student, teacher }: { channelId: number; student: boolean; teacher: boolean }) {
  const q = useApi((signal) => learnApi.tests(channelId, signal), [channelId], { live: [`channel:${channelId}:`] });
  const [editing, setEditing] = useState<Selftest | 'new' | null>(null);
  const [running, setRunning] = useState<{ test: Selftest; attempt?: number } | null>(null);
  const [results, setResults] = useState<Selftest | null>(null);
  const toast = useToast();
  if (q.error && !q.data) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!q.data) return <Loading />;
  const { tests, can_create } = q.data;
  const act = async (fn: () => Promise<unknown>, message: string) => {
    await fn();
    toast.success(message);
    q.reload();
  };
  const openEditor = async (t: Selftest) => setEditing(await learnApi.test(channelId, t.id));

  return (
    <section className="stack" aria-label="Selbsttests">
      {can_create && (
        <div>
          <button type="button" className="btn btn-primary" onClick={() => setEditing('new')}>
            <Icon name="plus" /> Neuer Selbsttest
          </button>
        </div>
      )}
      {tests.length === 0 ? (
        <Empty icon="exam" title="Noch kein Selbsttest">
          {can_create ? 'Legen Sie Fragen in der Fragensammlung an und stellen Sie daraus einen Test zusammen.' : 'Sobald ein Selbsttest freigegeben ist, erscheint er hier.'}
        </Empty>
      ) : (
        <ul className="ln-cards">
          {tests.map((t) => {
            const m = t.mine;
            const canStart = t.state === 'offen' && (m?.attempts_left === null || (m?.attempts_left ?? 0) > 0);
            return (
              <li key={t.id} className="card ln-card">
                <div className="ln-card-head">
                  <h3 className="ln-card-title">{t.title}</h3>
                  <span className={`badge ${TONE[t.state]}`}>{TEST_STATE_LABELS[t.state]}</span>
                </div>
                <p className="small muted">{testRules(t).join(' · ')}</p>
                {t.closes_at && t.state === 'offen' && <p className="small muted">bis {formatDateTime(t.closes_at)}</p>}
                {student && m && m.attempts > 0 && (
                  <p className="small">
                    {m.attempts} {m.attempts === 1 ? 'Versuch' : 'Versuche'}
                    {m.best_percent !== null && t.review !== 'none' ? ` · Bestes Ergebnis: ${pointsText(m.best_points, m.max_points)} (${percentText(m.best_percent)})` : ''}
                    {m.passed === true ? ' · bestanden' : ''}
                  </p>
                )}
                <div className="ln-card-actions">
                  {(student || teacher) && m?.running_attempt && (
                    <button type="button" className="btn btn-primary btn-sm" onClick={() => setRunning({ test: t })}>
                      Fortsetzen
                    </button>
                  )}
                  {student && !m?.running_attempt && canStart && (
                    <button type="button" className="btn btn-primary btn-sm" onClick={() => setRunning({ test: t })}>
                      {m && m.attempts > 0 ? 'Neuer Versuch' : 'Starten'}
                    </button>
                  )}
                  {student && m?.last_attempt && t.review !== 'none' && (
                    <button type="button" className="btn btn-sm" onClick={() => setRunning({ test: t, attempt: m.last_attempt as number })}>
                      Letztes Ergebnis
                    </button>
                  )}
                  {teacher && !m?.running_attempt && t.question_count > 0 && (
                    <button type="button" className="btn btn-sm" onClick={() => setRunning({ test: t })}>
                      <Icon name="play" /> Ausprobieren
                    </button>
                  )}
                  {t.editable && (
                    <>
                      <button type="button" className="btn btn-sm" onClick={() => setResults(t)}>
                        Auswertung{t.attempt_count ? ` (${t.attempt_count})` : ''}
                      </button>
                      <button type="button" className="btn btn-sm" onClick={() => openEditor(t)}>
                        <Icon name="edit" /> Bearbeiten
                      </button>
                      {t.status === 'offen' && (
                        <AsyncButton className="btn btn-sm" confirm="Selbsttest beenden? Danach kann niemand mehr beginnen." onClick={() => act(() => learnApi.patchTest(channelId, t.id, { status: 'geschlossen' }), 'Selbsttest beendet')}>
                          Beenden
                        </AsyncButton>
                      )}
                      {t.status !== 'offen' && (
                        <AsyncButton className="btn btn-sm" onClick={() => act(() => learnApi.patchTest(channelId, t.id, { status: 'offen' }), 'Selbsttest freigegeben')}>
                          Freigeben
                        </AsyncButton>
                      )}
                      <AsyncButton className="btn btn-sm btn-ghost" confirm="Selbsttest samt aller Versuche löschen?" onClick={() => act(() => learnApi.deleteTest(channelId, t.id), 'Selbsttest gelöscht')}>
                        <Icon name="trash" />
                        <span className="sr-only">Löschen</span>
                      </AsyncButton>
                    </>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
      {editing && <TestEditor channelId={channelId} test={editing === 'new' ? null : editing} onClose={() => setEditing(null)} onSaved={q.reload} />}
      {running && <TestRunner channelId={channelId} testId={running.test.id} attemptId={running.attempt} onClose={() => setRunning(null)} onChanged={q.reload} />}
      {results && <ResultsDialog channelId={channelId} test={results} onClose={() => setResults(null)} />}
    </section>
  );
}

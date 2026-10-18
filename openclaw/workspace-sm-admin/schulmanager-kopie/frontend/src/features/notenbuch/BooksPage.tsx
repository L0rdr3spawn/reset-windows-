/**
 * `/notenbuch` – Übersicht der Notenbücher eines Halbjahres (eigene Kurse bzw. alle für die Schulleitung), neues
 * Notenbuch für einen Kurs anlegen, Zugang zu Klassenübersichten und Verwaltung.
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Icon } from '../../components/Icon';
import { AsyncButton, Empty, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useTitle } from '../../hooks/misc';
import { useApi } from '../../hooks/useApi';
import { gbApi } from './api';
import type { CourseOption } from './types';
import './notenbuch.css';

export default function BooksPage() {
  useTitle('Notenbuch');
  const nav = useNavigate();
  const toast = useToast();
  const meta = useApi((signal) => gbApi.meta(signal), []);
  const [term, setTerm] = useState<string>('');
  const cur = term || meta.data?.term || '';
  const books = useApi((signal) => gbApi.books(cur || undefined, signal), [cur], { live: ['gradebook'], enabled: !!meta.data });
  const [classId, setClassId] = useState('');
  const [creating, setCreating] = useState(false);
  const courses = useApi((signal) => gbApi.courses(cur, classId || undefined, signal), [cur, classId, creating], { enabled: !!meta.data && creating });
  const [pick, setPick] = useState('');
  const [copy, setCopy] = useState(true);

  if (meta.error) return <div className="page"><ErrorBox error={meta.error} onRetry={meta.reload} /></div>;
  if (!meta.data) return <div className="page"><Loading /></div>;
  const m = meta.data;
  const free: CourseOption[] = (courses.data?.courses ?? []).filter((c) => c.book_id === null && c.access === 'edit');
  const chosen = free.find((c) => `${c.course_id}#${c.part}` === pick);

  return (
    <div className="page stack">
      <div className="page-head">
        <h1>Notenbuch</h1>
        <div className="gbk-bar">
          <label className="sr-only" htmlFor="gbk-term">
            Halbjahr
          </label>
          <select id="gbk-term" value={cur} onChange={(e) => setTerm(e.target.value)}>
            {m.terms.map((t) => (
              <option key={t.id} value={t.id}>
                {t.label}
              </option>
            ))}
          </select>
          {(m.can.read_class || m.can.manage) && m.classes.length > 0 && (
            <ClassPicker classes={m.classes} term={cur} />
          )}
          {(m.can.manage || m.can.export) && (
            <Link className="btn" to="/notenbuch/verwaltung">
              <Icon name="cog" /> Verwaltung
            </Link>
          )}
        </div>
      </div>

      {books.error ? <ErrorBox error={books.error} onRetry={books.reload} /> : null}
      {!books.data && books.loading && <Loading />}
      {books.data && books.data.books.length === 0 && <Empty icon="exam">Für dieses Halbjahr gibt es noch kein Notenbuch.</Empty>}
      {books.data && books.data.books.length > 0 && (
        <ul className="gbk-list">
          {books.data.books.map((b) => (
            <li key={b.id}>
              <div className="gbk-li-main">
                <Link to={`/notenbuch/${b.id}`}>
                  <strong>{b.title}</strong>
                </Link>
                <div className="small muted">
                  {b.students} Schüler/innen · {b.scale?.name}
                  {b.teacher_name ? ` · ${b.teacher_name}` : ''}
                </div>
              </div>
              <div className="gbk-chips">
                {b.locked && (
                  <span className="badge badge-danger">
                    <Icon name="lock" /> gesperrt
                  </span>
                )}
                {b.access === 'read' && <span className="badge badge-info">nur lesen</span>}
                <Link className="btn btn-sm" to={`/notenbuch/${b.id}`}>
                  Öffnen
                </Link>
              </div>
            </li>
          ))}
        </ul>
      )}

      {m.can.use && (
        <section className="card stack" aria-labelledby="gbk-new">
          <div className="row-between">
            <h2 id="gbk-new">Neues Notenbuch</h2>
            {!creating && (
              <button type="button" className="btn btn-primary" onClick={() => setCreating(true)}>
                <Icon name="plus" /> Kurs wählen
              </button>
            )}
          </div>
          {creating && (
            <div className="stack">
              {m.can.manage && (
                <Field label="Klasse" htmlFor="gbk-new-class" help="Die Schulleitung wählt zuerst die Klasse; Lehrkräfte sehen ihre eigenen Kurse.">
                  <select id="gbk-new-class" value={classId} onChange={(e) => { setClassId(e.target.value); setPick(''); }}>
                    <option value="">Alle Klassen</option>
                    {m.classes.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </Field>
              )}
              {courses.error ? <ErrorBox error={courses.error} onRetry={courses.reload} /> : null}
              {!courses.data && courses.loading && <Loading />}
              {courses.data && free.length === 0 && <p className="muted">Alle Kurse haben in diesem Halbjahr schon ein Notenbuch.</p>}
              {free.length > 0 && (
                <>
                  <Field label="Kurs" htmlFor="gbk-new-course">
                    <select id="gbk-new-course" value={pick} onChange={(e) => setPick(e.target.value)}>
                      <option value="">Bitte wählen …</option>
                      {free.map((c) => (
                        <option key={`${c.course_id}#${c.part}`} value={`${c.course_id}#${c.part}`}>
                          {c.title}
                          {c.teacher_name ? ` – ${c.teacher_name}` : ''}
                        </option>
                      ))}
                    </select>
                  </Field>
                  <label className="check">
                    <input type="checkbox" checked={copy} onChange={(e) => setCopy(e.target.checked)} /> Leistungsarten und Gewichte vom letzten Halbjahr übernehmen, wenn vorhanden
                  </label>
                  <div className="gbk-bar">
                    <AsyncButton
                      className="btn btn-primary"
                      disabled={!chosen}
                      onClick={async () => {
                        if (!chosen) return;
                        try {
                          let copyFrom: number | undefined;
                          if (copy) {
                            const idx = m.terms.findIndex((t) => t.id === cur);
                            const prev = idx > 0 ? m.terms[idx - 1] : undefined;
                            if (prev) {
                              const old = await gbApi.courses(prev.id, undefined);
                              copyFrom = old.courses.find((c) => c.course_id === chosen.course_id && c.part === chosen.part)?.book_id ?? undefined;
                            }
                          }
                          const t = await gbApi.create({ course_id: chosen.course_id, part: chosen.part, term: cur, copy_from: copyFrom });
                          toast.success('Notenbuch angelegt');
                          nav(`/notenbuch/${t.book.id}`);
                        } catch (e) {
                          toast.error(e);
                        }
                      }}
                    >
                      Notenbuch anlegen
                    </AsyncButton>
                    <button type="button" className="btn" onClick={() => setCreating(false)}>
                      Abbrechen
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </section>
      )}
    </div>
  );
}

function ClassPicker({ classes, term }: { classes: { id: string; name: string }[]; term: string }) {
  const nav = useNavigate();
  return (
    <select aria-label="Klassenübersicht öffnen" value="" onChange={(e) => e.target.value && nav(`/notenbuch/klasse/${encodeURIComponent(e.target.value)}?term=${encodeURIComponent(term)}`)}>
      <option value="">Klassenübersicht …</option>
      {classes.map((c) => (
        <option key={c.id} value={c.id}>
          {c.name}
        </option>
      ))}
    </select>
  );
}

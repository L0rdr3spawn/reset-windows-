/**
 * Notenbuch-Sicht für Schüler/innen und Eltern (eingebettet in „Meine Noten“, `features/students/GradesPage.tsx`):
 * je Fach Endnote, Schnitte und Einzelnoten – so weit die Schule Einsicht erlaubt (`visibility`).
 */
import { useState } from 'react';
import { HelpTip } from '../../components/HelpTip';
import { Loading } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { formatDate } from '../../lib/dates';
import { gbApi } from './api';
import { fmtNum, gradeTone, STATUS_NAMES } from './logic';
import type { MySubject } from './types';
import './notenbuch.css';

export default function MyGradebook({ studentId }: { studentId?: string }) {
  const [term, setTerm] = useState<string>('');
  const q = useApi((signal) => gbApi.my(studentId, term || undefined, signal), [studentId, term], { live: ['gradebook'], keepPrevious: true });
  const d = q.data;
  if (q.error && !d) return null; // Fehler (z. B. Elternfreigabe) zeigt „Meine Noten“ bereits selbst
  if (!d) return q.loading ? <Loading /> : null;
  const selected = term || d.term;
  return (
    <section className="stack" aria-labelledby="gbk-my">
      <div className="gbk-my-head">
        <h2 id="gbk-my">
          Notenbuch{' '}
          <HelpTip>
            Hier stehen Noten und Schnitte aus dem Notenbuch der Lehrkräfte. Was Sie sehen, legt die Schule fest. Die Endnote erscheint erst, wenn die Lehrkraft die Halbjahresnoten festgelegt hat.
          </HelpTip>
        </h2>
        {d.terms && (
          <select aria-label="Halbjahr" value={selected} onChange={(e) => setTerm(e.target.value)}>
            {d.terms.map((t) => (
              <option key={t.id} value={t.id}>
                {t.label}
              </option>
            ))}
          </select>
        )}
      </div>
      {d.subjects.length === 0 && <p className="muted">Im {d.term_label} sind noch keine Noten sichtbar.</p>}
      {d.subjects.map((s) => (
        <SubjectCard key={s.book_id} s={s} showAverages={d.show_averages !== false} />
      ))}
    </section>
  );
}

function SubjectCard({ s, showAverages }: { s: MySubject; showAverages: boolean }) {
  const kind = s.scale.kind;
  const cats = new Map(s.categories.map((c) => [c.id, c.name]));
  return (
    <article className="card stack" aria-labelledby={`gbk-s-${s.book_id}`}>
      <div className="gbk-my-head">
        <h3 id={`gbk-s-${s.book_id}`}>
          {s.subject_name}
          {s.teacher_name ? <span className="small muted"> · {s.teacher_name}</span> : null}
        </h3>
        <div className="gbk-chips">
          {showAverages && s.average !== null && <span className="badge">Ø {fmtNum(s.average, 2)}</span>}
          {s.final && (
            <span className="gbk-final-badge">
              <span className="small muted">Note</span> {s.final}
            </span>
          )}
        </div>
      </div>
      {s.final_note && <p className="small">{s.final_note}</p>}
      {showAverages && s.categories.length > 0 && (
        <div className="gbk-chips">
          {s.categories.map((c) => (
            <span key={c.id} className="badge">
              {c.name}: {fmtNum(c.average, 2)}
            </span>
          ))}
        </div>
      )}
      {s.items.length > 0 && (
        <div className="table-wrap">
          <table className="table table-compact">
            <thead>
              <tr>
                <th>Datum</th>
                <th>Leistung</th>
                <th className="num">Note</th>
                <th>Bemerkung</th>
              </tr>
            </thead>
            <tbody>
              {s.items.map((i) => {
                const label = i.status ? STATUS_NAMES[i.status] : i.label || i.value;
                const tone = i.status ? 'none' : gradeTone(i.label || i.value, kind);
                return (
                  <tr key={i.item_id}>
                    <td className="nowrap">{i.date ? formatDate(i.date) : '–'}</td>
                    <td>
                      {i.title}
                      {i.category_id !== null && cats.get(i.category_id) ? <span className="small muted"> · {cats.get(i.category_id)}</span> : null}
                    </td>
                    <td className={`num ${tone === 'none' ? '' : `gbk-tone-${tone}`}`}>
                      <strong>{label}</strong>
                      {i.max_points && i.value && !i.status ? <span className="gbk-sub">{i.value} von {i.max_points} Punkten</span> : null}
                      {i.status === 'nachschreiben' && i.makeup_date ? <span className="gbk-sub">Termin {formatDate(i.makeup_date)}</span> : null}
                    </td>
                    <td className="small">{i.note}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </article>
  );
}

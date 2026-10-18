/**
 * Startseiten-Kachel des Personals „Atteste & Dokumente“ (Klassenleitung: eigene Klasse, inkl. heutiger
 * Krankmeldungen). Die Familien-Inhalte stehen in `FamilyHome.tsx` (Start) und `FamilyAbsences.tsx` (Krankmeldungen).
 */
import { Link } from 'react-router-dom';
import { studentAbsences as saApi } from '../../api/endpoints';
import type { StudentAbsence } from '../../api/types';
import { Loading } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useApi } from '../../hooks/useApi';
import { useSettings } from '../../hooks/useCollection';
import { currentSchoolDay, relativeDayLabel, todayISO } from '../../lib/dates';
import { schoolDaysOf } from '../../lib/weeks';
import { documentsApi } from './api';
import './students.css';

function SickList({ rows, presence }: { rows: StudentAbsence[]; presence?: boolean }) {
  if (!rows.length) return <p className="small muted">Niemand.</p>;
  return (
    <ul className="st-list">
      {rows.map((a) => (
        <li key={`${a.view}-${a.id}`} className="st-row">
          <div className="st-row-main">
            <strong>
              {a.student_name}
              {presence && a.class_id ? ` (${a.class_id})` : ''}
            </strong>
            <span className="small muted">
              {a.periods?.length ? `${a.periods.map((p) => p + 1).join(', ')}. Std.` : 'ganztägig'}
              {!presence && a.reason ? ` · ${a.reason}` : ''}
              {!presence && a.reported_by_name ? ` · ${a.reported_by_name}` : ''}
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}

export function StaffWidget() {
  const user = useUser();
  const q = useApi((signal) => documentsApi.summary(signal), [], { live: ['student_documents', 'student_absences'] });
  const classTeacherOf = q.data?.class_teacher_of;
  const isTeacher = user.role === 'lehrer';
  const { data: settings } = useSettings();
  // heute bzw. am Wochenende der nächste Schultag
  const day = currentSchoolDay(new Date(), schoolDaysOf(settings));
  // Schulschalter „fehlt heute in meiner Stunde“ (B-06): nur an Schultagen, nur heute
  const presence = isTeacher && settings?.subject_teacher_absence_view === 'presence' && day === todayISO();
  const sick = useApi(() => saApi.list({ from: day, to: day }), [day], {
    enabled: !!classTeacherOf?.length || presence,
    live: ['student_absences', 'class_absences', 'settings'],
  });
  if (q.error || !q.data) return null;
  const mine = (sick.data ?? []).filter((a) => a.view === 'full' && a.class_id && classTeacherOf?.includes(a.class_id));
  const lessons = (sick.data ?? []).filter((a) => a.view === 'presence');
  if (isTeacher && !classTeacherOf?.length) {
    // Fachlehrkräfte sehen keine Atteste – höchstens, wer heute in ihren Stunden fehlt
    if (!presence) return null;
    return (
      <section className="card" aria-labelledby="st-lessons-h">
        <div className="card-head">
          <h2 id="st-lessons-h">Fehlt heute in meinen Stunden</h2>
        </div>
        {sick.initialLoading ? <Loading /> : <SickList rows={lessons} presence />}
      </section>
    );
  }
  return (
    <section className="card" aria-labelledby="st-staff-h">
      <div className="card-head">
        <h2 id="st-staff-h">{isTeacher ? `Meine Klasse ${classTeacherOf?.join(', ')}: Krankmeldungen` : 'Atteste & Dokumente'}</h2>
        <Link to="/dokumente" className="small">
          Öffnen
        </Link>
      </div>
      <div className="row">
        <Link to="/dokumente" className={`badge ${q.data.open ? 'badge-info' : ''}`}>
          {q.data.open} neu eingereicht
        </Link>
        <Link to="/dokumente" className={`badge ${q.data.attest_missing ? 'badge-danger' : ''}`}>
          {q.data.attest_missing} Attest fehlt
        </Link>
      </div>
      {isTeacher && (
        <div className="stack-sm st-widget-section">
          <strong className="small">Krank gemeldet – {relativeDayLabel(day, todayISO())}</strong>
          {sick.initialLoading ? <Loading /> : <SickList rows={mine} />}
          {presence && lessons.length > 0 && (
            <>
              <strong className="small">Fehlt heute in meinen Stunden</strong>
              <SickList rows={lessons} presence />
            </>
          )}
        </div>
      )}
    </section>
  );
}

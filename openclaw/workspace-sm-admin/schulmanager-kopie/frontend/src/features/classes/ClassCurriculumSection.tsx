/**
 * Stundentafel im Dialog „Klasse anlegen/bearbeiten“ (Stammdaten): bei bestehenden Klassen die aktuelle Tafel, bei
 * neuen Klassen vorausgefüllt mit der Stundentafel der Klassenstufe. Gespeichert wird zusammen mit der Klasse.
 */
import { HelpTip } from '../../components/HelpTip';
import { useEffect, useRef } from 'react';
import { ErrorBox, Loading } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { useCollection } from '../../hooks/useCollection';
import { effectiveEntries } from '../../pages/planning/curricula';
import { classesApi } from './api';
import { CurriculumEditor } from './CurriculumTab';
import type { CurriculumRow, CurriculumSubject } from './types';

export function ClassCurriculumSection({
  classId,
  grade,
  profile,
  rows,
  onRows,
  onEdit,
  disabled,
}: {
  /** `null` = neue Klasse */
  classId: string | null;
  grade: number;
  /** Jahrgang der (neuen) Klasse: seine Stundentafel füllt vor */
  profile?: string | null;
  rows: CurriculumRow[] | null;
  /** Startwerte (geladen bzw. aus der Tafel der Klassenstufe) */
  onRows: (rows: CurriculumRow[]) => void;
  /** Änderung durch die Nutzerin/den Nutzer */
  onEdit: (rows: CurriculumRow[]) => void;
  disabled?: boolean;
}) {
  const existing = useApi((signal) => (classId ? classesApi.curriculum(classId, signal) : Promise.resolve(null)), [classId]);
  const curricula = useCollection('curricula', !classId);
  const profiles = useCollection('grade_profiles', !classId);
  const subjectsCol = useCollection('subjects', !classId);
  const edited = useRef(false);

  // Startwerte: bestehende Klasse → geladene Tafel; neue Klasse → Tafel des Jahrgangs (solange nicht bearbeitet)
  useEffect(() => {
    if (edited.current) return;
    if (classId) {
      if (existing.data) onRows(existing.data.entries.map((e) => ({ subject: e.subject, hours: e.hours, double: e.double, teachers: e.teachers })));
      return;
    }
    const all = curricula.data ?? [];
    const viaProfile = profile ? all.find((c) => c.id === (profiles.data ?? []).find((p) => p.id === profile)?.curriculum) : undefined;
    const cur = viaProfile ?? all.find((c) => !(c.classes ?? []).length && (c.grades ?? []).includes(grade));
    onRows(cur ? effectiveEntries(all, cur).map((e) => ({ subject: e.subject, hours: e.hours, double: !!e.double })) : []);
  }, [classId, existing.data, curricula.data, profiles.data, grade, profile]); // eslint-disable-line react-hooks/exhaustive-deps

  const subjects: CurriculumSubject[] = classId
    ? existing.data?.subjects ?? []
    : (subjectsCol.data ?? []).map((s) => ({ id: s.id, name: s.name, room_type: s.room_type ?? null })).sort((a, b) => a.name.localeCompare(b.name, 'de'));

  if (existing.error) return <ErrorBox error={existing.error} onRetry={existing.reload} />;
  if (!rows) return <Loading />;
  const source = existing.data?.source;
  return (
    <div className="span-all stack-sm">
      <h3 style={{ margin: '8px 0 0' }}>
        Stundentafel{' '}
        <HelpTip label="Hilfe zur Stundentafel">
          Wie viele Stunden pro Woche hat die Klasse in welchem Fach?{' '}
          {classId
            ? source === 'grade' || source === 'profile'
              ? 'Zurzeit gilt die Stundentafel des Jahrgangs – Änderungen hier gelten nur für diese Klasse.'
              : ''
            : 'Vorausgefüllt mit der Stundentafel des Jahrgangs; ohne Änderung bleibt die Klasse bei der Tafel ihres Jahrgangs.'}{' '}
          Nach dem Speichern entstehen die Kurse sofort und der Stundenplan wird automatisch ergänzt.
        </HelpTip>
      </h3>
      <CurriculumEditor
        rows={rows}
        subjects={subjects}
        disabled={disabled}
        onChange={(r) => {
          edited.current = true;
          onEdit(r);
        }}
      />
    </div>
  );
}

/**
 * Lernstand einer Schülerin/eines Schülers: Kompetenzen, Lernplan und Abzeichen. Gemeinsam für die Lehrkraft-Ansicht,
 * die Schüler-Ansicht (selbst einschätzen) und die Elternansicht (nur lesen); die Sicht bestimmt der Server (`kind`).
 */
import './kompetenzen.css';
import { useMemo, useState } from 'react';
import { ErrorBox, Loading, ProgressBar, Tabs, SegmentedControl, AsyncButton } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { formatDate } from '../../lib/dates';
import { compApi, type CompetencyState, type StudentView } from './api';
import { AssessDialog } from './AssessDialog';
import { BadgeIcon } from './BadgeIcon';
import { LevelsView } from './LevelsView';
import { PlanView, type CompetencyOption } from './PlanView';

type Tab = 'kompetenzen' | 'plan' | 'abzeichen';

export function StudentPanel({ studentId }: { studentId: string }) {
  const toast = useToast();
  const q = useApi<StudentView>((signal) => compApi.student(studentId, undefined, signal), [studentId], { live: ['competency'] });
  const [tab, setTab] = useState<Tab>('kompetenzen');
  const [fwId, setFwId] = useState<number | null>(null);
  const [onlySupport, setOnlySupport] = useState(false);
  const [dialog, setDialog] = useState<{ comp: CompetencyState; confirm: boolean } | null>(null);
  const data = q.data;
  const options = useMemo<CompetencyOption[]>(
    () => (data ? data.frameworks.flatMap((f) => f.areas.flatMap((a) => a.competencies.map((c) => ({ id: c.id, title: c.title, area: a.name, framework: f.name })))) : []),
    [data],
  );
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!data) return <Loading />;
  const staff = data.kind === 'staff';
  const pupil = data.kind === 'self';
  const fw = data.frameworks.find((f) => f.id === fwId) ?? data.frameworks[0];

  return (
    <div className="stack">
      <div className="row-between cp-panel-head">
        <div>
          <h2 className="cp-name">{data.student.name}</h2>
          <span className="small muted">{data.student.class_id}</span>
        </div>
        {staff && (
          <a className="btn" href={compApi.reportUrl(studentId, fw?.id)} target="_blank" rel="noopener noreferrer">
            Lernentwicklungsbericht (PDF)
          </a>
        )}
      </div>
      <Tabs<Tab>
        label="Lernstand"
        active={tab}
        onChange={setTab}
        tabs={[
          { key: 'kompetenzen', label: pupil ? 'Das kann ich' : 'Kompetenzen' },
          { key: 'plan', label: pupil ? 'Wochenplan' : 'Lernplan' },
          { key: 'abzeichen', label: `Abzeichen (${data.badges.length})` },
        ]}
      />
      {tab === 'kompetenzen' && (
        <>
          {!fw && <p className="muted">Es gibt noch keinen Kompetenzrahmen.</p>}
          {fw && (
            <div className="stack">
              <div className="cp-filters">
                {data.frameworks.length > 1 && (
                  <SegmentedControl<number>
                    label="Kompetenzrahmen"
                    value={fw.id}
                    onChange={setFwId}
                    options={data.frameworks.map((f) => ({ value: f.id, label: f.name }))}
                  />
                )}
                {staff && (
                  <label className="cp-check">
                    <input type="checkbox" checked={onlySupport} onChange={(e) => setOnlySupport(e.target.checked)} /> Nur Unterstützung nötig
                  </label>
                )}
              </div>
              <ProgressBar value={fw.progress} label={pupil ? `${fw.name}: Das kann ich schon (${fw.assessed} von ${fw.total} eingeschätzt)` : `${fw.name} (${fw.assessed} von ${fw.total} eingeschätzt)`} />
              <LevelsView
                fw={fw}
                mode={data.kind}
                filterSupport={onlySupport}
                onAssess={staff && data.can_assess ? (comp) => setDialog({ comp, confirm: false }) : undefined}
                onConfirm={staff && data.can_assess ? (comp) => setDialog({ comp, confirm: true }) : undefined}
                onSelf={
                  pupil
                    ? async (comp, level) => {
                        try {
                          await compApi.selfAssess(comp.id, level);
                          toast.success('Gespeichert – Ihre Lehrkraft sieht es und bestätigt');
                          q.reload();
                        } catch (e) {
                          toast.error(e, 'Selbsteinschätzung');
                        }
                      }
                    : undefined
                }
              />
            </div>
          )}
        </>
      )}
      {tab === 'plan' && <PlanView studentId={studentId} options={options} pupil={pupil} />}
      {tab === 'abzeichen' && <BadgesSection data={data} studentId={studentId} onChanged={q.reload} />}
      {dialog && fw && (
        <AssessDialog
          fw={fw}
          comp={dialog.comp}
          confirmSelf={dialog.confirm}
          studentId={studentId}
          studentName={data.student.name}
          onClose={() => setDialog(null)}
          onSaved={q.reload}
        />
      )}
    </div>
  );
}

function BadgesSection({ data, studentId, onChanged }: { data: StudentView; studentId: string; onChanged: () => void }) {
  const toast = useToast();
  const staff = data.kind === 'staff' && data.can_assess;
  const catalog = useApi((signal) => compApi.badges(signal), [], { live: ['competency'], enabled: staff });
  const [pick, setPick] = useState('');
  const have = new Set(data.badges.map((b) => b.badge_id));
  const available = (catalog.data ?? []).filter((b) => b.active && !have.has(b.id));
  return (
    <div className="stack">
      {!data.badges.length && <p className="muted">{data.kind === 'self' ? 'Sie haben noch keine Abzeichen. Sie kommen mit den erreichten Kompetenzen.' : 'Noch keine Abzeichen vergeben.'}</p>}
      <ul className="cp-badge-grid">
        {data.badges.map((b) => (
          <li key={b.award_id} className="card cp-badge-card">
            <BadgeIcon icon={b.icon} color={b.color} size="lg" label={b.name} />
            <strong>{b.name}</strong>
            {b.description && <span className="small muted">{b.description}</span>}
            <span className="xsmall muted">
              {formatDate(b.date)}
              {b.auto ? ' · automatisch' : ''}
            </span>
            {b.note && <span className="small">{b.note}</span>}
            {staff && (
              <AsyncButton
                className="btn btn-sm"
                confirm={`Abzeichen „${b.name}“ zurücknehmen?`}
                onClick={async () => {
                  await compApi.revoke(b.badge_id, studentId);
                  onChanged();
                }}
              >
                Zurücknehmen
              </AsyncButton>
            )}
          </li>
        ))}
      </ul>
      {staff && available.length > 0 && (
        <div className="row cp-award">
          <label htmlFor="cp-award-pick" className="small">
            Abzeichen vergeben
          </label>
          <select id="cp-award-pick" value={pick} onChange={(e) => setPick(e.target.value)}>
            <option value="">Auswählen …</option>
            {available.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
          <AsyncButton
            className="btn btn-primary"
            disabled={!pick}
            onClick={async () => {
              try {
                await compApi.award(Number(pick), [studentId]);
                toast.success('Abzeichen vergeben');
                setPick('');
                onChanged();
              } catch (e) {
                toast.error(e, 'Abzeichen');
              }
            }}
          >
            Vergeben
          </AsyncButton>
        </div>
      )}
    </div>
  );
}

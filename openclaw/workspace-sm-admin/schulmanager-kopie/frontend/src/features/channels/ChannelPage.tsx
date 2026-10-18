/**
 * `/kursraeume/:id` – ein Kursraum mit den Bereichen Material (Ordner, Dateien, Links, Textseiten, Freigaben),
 * Aufgaben (Abgabe/Rückmeldung), Pinnwand und Teilnehmende. Bereich und Auswahl stehen in der Adresse
 * (`?tab=aufgaben&aufgabe=12`, `?ordner=3`); Klassenräume beginnen mit dem Bereich „Klasse“ (`?tab=klasse`), damit Links von der Startseite direkt dorthin führen.
 */
import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { ApiError, errorMessage } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { FeatureBoundary } from '../../components/Layout';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton, ErrorBox, Field, Loading, Tabs } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useTitle } from '../../hooks/misc';
import { formatLong } from '../../lib/dates';
import { examDetailLink } from './examRoom';
import { channelsApi } from './api';
import { RoleBadge } from './components';
import type { ChannelDetail } from './types';
import { withoutInfoCards } from './classInfo';
import MaterialTab from './MaterialTab';
import { MyProgressBar } from './ProgressTab';
import './channels.css';

const AssignmentsTab = lazy(() => import('./AssignmentsTab'));
const UnterrichtTab = lazy(() => import('./UnterrichtTab'));
const ClassTab = lazy(() => import('./ClassTab'));
const BoardTab = lazy(() => import('./BoardTab'));
const MembersTab = lazy(() => import('./MembersTab'));
const GroupsTab = lazy(() => import('./assign/GroupsTab'));
const ProgressTab = lazy(() => import('./ProgressTab'));
const TrashDialog = lazy(() => import('./TrashDialog'));
const ActivitiesTab = lazy(() => import('../lernen/ActivitiesTab'));

type TabKey = 'klasse' | 'material' | 'unterricht' | 'aufgaben' | 'tests' | 'fortschritt' | 'pinnwand' | 'gruppen' | 'teilnehmende';
const TABS: TabKey[] = ['material', 'unterricht', 'aufgaben', 'tests', 'fortschritt', 'pinnwand', 'gruppen', 'teilnehmende'];
/** Klassenräume beginnen mit dem Bereich „Klasse“ (Regelplan, Termine, Infos, Ansprechpersonen). */
const CLASS_TABS: TabKey[] = ['klasse', ...TABS];
const TAB_LABELS: Record<TabKey, string> = { klasse: 'Klasse', material: 'Material', unterricht: 'Unterricht', aufgaben: 'Hausaufgaben', tests: 'Tests & Umfragen', fortschritt: 'Fortschritt', pinnwand: 'Pinnwand', gruppen: 'Gruppen', teilnehmende: 'Teilnehmende' };

function SettingsDialog({ detail, onClose, onSaved }: { detail: ChannelDetail; onClose: () => void; onSaved: () => void }) {
  const ch = detail.channel;
  const [description, setDescription] = useState(ch.description);
  const [canPost, setCanPost] = useState(ch.settings.students_can_post);
  const [canReply, setCanReply] = useState(ch.settings.students_can_reply);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  return (
    <Modal
      title="Einstellungen des Kursraums"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton
            className="btn btn-primary"
            onClick={async () => {
              try {
                await channelsApi.patch(ch.id, { description, students_can_post: canPost, students_can_reply: canReply });
                toast.success('Einstellungen gespeichert');
                onSaved();
                onClose();
              } catch (e) {
                setError(errorMessage(e));
              }
            }}
          >
            Speichern
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        <Field label="Beschreibung für Teilnehmende" htmlFor="kr-set-desc" hint="z. B. Ablauf, Bewertung, Sprechzeiten" error={error}>
          <textarea id="kr-set-desc" rows={4} maxLength={2000} value={description} onChange={(e) => setDescription(e.target.value)} />
        </Field>
        <fieldset className="kr-fieldset">
          <legend>Pinnwand</legend>
          <label className="check">
            <input type="checkbox" checked={canPost} onChange={(e) => setCanPost(e.target.checked)} /> Teilnehmende dürfen neue Beiträge schreiben
          </label>
          <label className="check">
            <input type="checkbox" checked={canReply} onChange={(e) => setCanReply(e.target.checked)} /> Teilnehmende dürfen antworten
          </label>
        </fieldset>
      </div>
    </Modal>
  );
}

export default function ChannelPage() {
  const { id } = useParams();
  const channelId = Number(id);
  const valid = Number.isInteger(channelId) && channelId > 0;
  const [params, setParams] = useSearchParams();
  const tabParam = params.get('tab') as TabKey | null;
  const childParam = params.get('child');
  const q = useApi<ChannelDetail>((signal) => channelsApi.get(channelId, signal, childParam), [channelId, childParam], {
    enabled: valid,
    live: [`channel:${channelId}:`, 'parent_access'],
  });
  const isClass = q.data?.channel.kind === 'class';
  const allTabs = isClass ? CLASS_TABS : TABS;
  const pm = q.data?.permissions;
  const showProgress = !!pm && (pm.manage || q.data?.channel.role === 'student' || !!pm.progress_parents);
  const tabs = allTabs.filter((t) => (t !== 'teilnehmende' || pm?.members !== false) && (t !== 'fortschritt' || showProgress) && (t !== 'gruppen' || !!pm?.manage));
  const tab: TabKey = tabParam && tabs.includes(tabParam) ? tabParam : isClass ? 'klasse' : 'material';
  const [settings, setSettings] = useState(false);
  const [trash, setTrash] = useState(false);
  const detail = q.data;
  const ch = detail?.channel;
  useTitle(ch ? ch.title : 'Kursraum');

  // Besuch merken (danach ist nichts mehr „neu“) – Hervorhebungen dieser Ansicht bleiben stehen
  const seenFor = useRef<number | null>(null);
  useEffect(() => {
    if (!detail || seenFor.current === channelId) return;
    seenFor.current = channelId;
    channelsApi.seen(channelId, detail.child?.id).catch(() => undefined);
  }, [detail, channelId]);

  // zeitgesteuerte Freigaben: pünktlich neu laden
  const { reload } = q;
  useEffect(() => {
    const next = detail?.next_release_at ? new Date(detail.next_release_at).getTime() : NaN;
    if (!Number.isFinite(next)) return undefined;
    const wait = Math.max(1000, next - Date.now() + 1500);
    if (wait > 24 * 3600 * 1000) return undefined;
    const t = window.setTimeout(reload, wait);
    return () => window.clearTimeout(t);
  }, [detail?.next_release_at, reload]);

  const setTab = (t: TabKey) => {
    const next = new URLSearchParams(params);
    next.set('tab', t);
    next.delete('aufgabe');
    setParams(next, { replace: true });
  };

  if (!valid) return <ErrorBox error={new ApiError(404, 'Kursraum nicht gefunden', null)} />;
  if (q.error && !detail) {
    const forbidden = q.error instanceof ApiError && (q.error.status === 403 || q.error.status === 404);
    return (
      <div className="page stack">
        {forbidden ? (
          <Alert kind="warning" title={q.error instanceof ApiError && q.error.status === 404 ? 'Kursraum nicht gefunden' : 'Kein Zugriff auf diesen Kursraum'}>
            {errorMessage(q.error)} <Link to="/kursraeume">Zu den Kursräumen</Link>
          </Alert>
        ) : (
          <ErrorBox error={q.error} onRetry={q.reload} />
        )}
      </div>
    );
  }
  if (!detail || !ch) return <Loading />;
  const perms = detail.permissions;
  const openTasks = ch.role === 'teacher' ? ch.to_grade ?? 0 : ch.open_assignments ?? 0;
  const materialDetail = withoutInfoCards(detail);
  // Sprung von einer Klausur/einem Test: `?klausur=ID&datum=…&art=klausur|test|nachschreiben`
  const examDate = params.get('datum');
  const examArt = params.get('art');
  const examId = params.get('klausur');
  const examNote =
    examId && examDate && /^\d{4}-\d{2}-\d{2}$/.test(examDate)
      ? {
          art: examArt,
          title: `${examArt === 'test' ? 'Test' : examArt === 'nachschreiben' ? 'Nachschreibtermin' : 'Klausur'} am ${formatLong(examDate)}`,
          detail: examArt === 'nachschreiben' ? null : examDetailLink(examId, examDate),
        }
      : null;
  const taskCount = detail.items.filter((i) => i.type === 'assignment' || i.submittable).length;

  return (
    <div className="page stack kr-page">
      <div className="page-head kr-head">
        <div style={{ minWidth: 0 }}>
          <nav aria-label="Pfad" className="small">
            <Link to="/kursraeume">Kursräume</Link> <span aria-hidden="true">›</span> <span className="muted">{ch.kind_label}</span>
          </nav>
          <h1 className="kr-title">{ch.title}</h1>
          {ch.subtitle && <p className="muted small kr-subtitle">{ch.subtitle}</p>}
          <div className="row" style={{ marginTop: 'var(--space-1)' }}>
            <RoleBadge role={ch.role} />
            {detail.child && <span className="badge badge-info">{detail.child.name}</span>}
            {ch.archived && <span className="badge badge-warning">archiviert – nur lesen</span>}
            {ch.orphaned && <span className="badge badge-warning">Kurs/Klasse gibt es nicht mehr</span>}
          </div>
        </div>
        <div className="row kr-head-actions">
          {perms.trash && (
            <button type="button" className="btn btn-sm" onClick={() => setTrash(true)}>
              <Icon name="trash" /> Papierkorb
            </button>
          )}
          {perms.manage && (
            <button type="button" className="btn btn-sm" onClick={() => setSettings(true)}>
              <Icon name="cog" /> Einstellungen
            </button>
          )}
        </div>
      </div>
      {ch.role === 'parent' && (
        <Alert
          kind="info"
          title={
            <>
              Elternansicht – nur lesen
              <HelpTip>Sie sehen den Kursraum Ihres Kindes: freigegebenes Material, Aufgaben und Pinnwand. Abgeben und schreiben können nur die Teilnehmenden.</HelpTip>
            </>
          }
        />
      )}
      {ch.role === 'supervisor' && (
        <Alert
          kind="info"
          title={
            <>
              Nur lesender Zugriff
              <HelpTip>
                Sie sehen diesen Kursraum als Schulleitung/Administration: Material inkl. verborgener Inhalte, Pinnwand und Teilnehmende, aber keine Abgaben-Inhalte oder Bewertungen. Zum Eingreifen tragen Sie sich unter „Teilnehmende“ als
                Lehrende/r ein (wird protokolliert).
              </HelpTip>
            </>
          }
        />
      )}
      {examNote && (
        <Alert kind="info" title={examNote.title}>
          {examNote.detail && <Link to={examNote.detail}>Details zur {examNote.art === 'test' ? 'Test' : 'Klausur'}</Link>}
        </Alert>
      )}
      {ch.description && <p className="kr-description">{ch.description}</p>}
      {tab !== 'fortschritt' && (ch.role === 'student' || (ch.role === 'parent' && perms.progress_parents)) && <MyProgressBar channelId={channelId} studentId={detail.child?.id} />}

      <div>
        <Tabs<TabKey>
          label="Bereiche des Kursraums"
          active={tab}
          onChange={setTab}
          tabs={[
            ...(isClass ? [{ key: 'klasse' as const, label: 'Klasse' }] : []),
            { key: 'material', label: 'Material' },
            { key: 'unterricht', label: 'Unterricht' },
            {
              key: 'aufgaben',
              label: (
                <>
                  Hausaufgaben{taskCount ? <span className="kr-tab-count">{taskCount}</span> : null}
                  {openTasks ? <span className="sr-only">, {openTasks} {ch.role === 'teacher' ? 'zu bewerten' : 'offen'}</span> : null}
                  {openTasks ? <span className="kr-dot" aria-hidden="true" /> : null}
                </>
              ),
            },
            { key: 'tests', label: 'Tests & Umfragen' },
            {
              key: 'pinnwand',
              label: (
                <>
                  Pinnwand{(ch.new_posts ?? 0) > 0 ? <span className="kr-tab-count kr-tab-new">{ch.new_posts} neu</span> : null}
                </>
              ),
            },
            ...(showProgress ? [{ key: 'fortschritt' as const, label: 'Fortschritt' }] : []),
            ...(perms.manage ? [{ key: 'gruppen' as const, label: 'Gruppen' }] : []),
            ...(perms.members === false ? [] : [{ key: 'teilnehmende' as const, label: 'Teilnehmende' }]),
          ]}
        />
        <div role="tabpanel" aria-label={TAB_LABELS[tab]}>
          <FeatureBoundary label={`kursraum-${tab}`} resetKey={`${channelId}-${tab}`}>
            <Suspense fallback={<Loading />}>
              {/* bleibt eingehängt: laufende Uploads gehen beim Reiterwechsel nicht verloren */}
              <div hidden={tab !== 'material'}>
                <MaterialTab detail={materialDetail} reload={q.reload} />
              </div>
              {tab === 'klasse' && isClass && <ClassTab detail={detail} reload={q.reload} />}
              {tab === 'unterricht' && <UnterrichtTab detail={detail} />}
              {tab === 'aufgaben' && <AssignmentsTab detail={detail} reload={q.reload} />}
              {tab === 'tests' && <ActivitiesTab detail={detail} />}
              {tab === 'fortschritt' && <ProgressTab detail={detail} reload={q.reload} />}
              {tab === 'pinnwand' && <BoardTab detail={detail} />}
              {tab === 'gruppen' && <GroupsTab detail={detail} />}
              {tab === 'teilnehmende' && <MembersTab detail={detail} reload={q.reload} />}
            </Suspense>
          </FeatureBoundary>
        </div>
      </div>
      {trash && (
        <Suspense fallback={null}>
          <TrashDialog channelId={channelId} onClose={() => setTrash(false)} onChanged={q.reload} />
        </Suspense>
      )}
      {settings && <SettingsDialog detail={detail} onClose={() => setSettings(false)} onSaved={q.reload} />}
    </div>
  );
}

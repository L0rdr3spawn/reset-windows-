/**
 * `/kursraeume` – eigene Kursräume (Kursteile, Klassen, eigene) mit Suche nach Kurs/Klasse/Fach/Lehrkraft;
 * Schulleitung/Admin: alle Kursräume der Schule (nur lesend) und eigene Kursräume anlegen; Eltern: Kursräume des
 * gewählten Kindes (nur lesen). Lehrkraft-Konto ohne Zuordnung: Hinweis statt leerer Liste.
 */
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Icon } from '../../components/Icon';
import { Modal } from '../../components/Modal';
import { Alert, AsyncButton, Empty, ErrorBox, Field, Loading, SegmentedControl } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useDebounced, useStoredState, useTitle } from '../../hooks/misc';
import { ApiError, errorMessage } from '../../api/client';
import { channelsApi } from './api';
import { Glyph, NewBadge, RoleBadge } from './components';
import { formatWhen, KIND_ORDER, matchChannel } from './logic';
import type { Channel, ChannelKind, ChannelListResponse } from './types';
import './channels.css';

type KindFilter = '' | ChannelKind;
const PAGE = 120;

function ChannelCard({ ch, childId }: { ch: Channel; childId?: string | null }) {
  const counts: string[] = [];
  if (ch.open_assignments) counts.push(`${ch.open_assignments} ${ch.open_assignments === 1 ? 'offene Aufgabe' : 'offene Aufgaben'}`);
  if (ch.to_grade) counts.push(`${ch.to_grade} zu bewerten`);
  return (
    <li className="kr-card">
      <Link to={childId ? `/kursraeume/${ch.id}?child=${encodeURIComponent(childId)}` : `/kursraeume/${ch.id}`} className="kr-card-link">
        <span className="kr-card-icon" aria-hidden="true">
          <Glyph name={ch.kind === 'class' ? 'room' : ch.kind === 'custom' ? 'board' : 'folder'} size={22} />
        </span>
        <span className="kr-card-main">
          <span className="kr-card-title">{ch.title}</span>
          {ch.subtitle && <span className="kr-card-sub">{ch.subtitle}</span>}
          <span className="kr-card-meta">
            <span className="badge">{ch.kind_label}</span>
            <RoleBadge role={ch.role} />
            {ch.archived && <span className="badge badge-warning">archiviert</span>}
            {ch.orphaned && <span className="badge badge-warning">Kurs/Klasse entfernt</span>}
            {(ch.new_items ?? 0) > 0 && <NewBadge n={ch.new_items} label={ch.new_items === 1 ? 'neues Material' : 'neue Materialien'} />}
            {(ch.new_posts ?? 0) > 0 && <NewBadge n={ch.new_posts} label={ch.new_posts === 1 ? 'neuer Beitrag' : 'neue Beiträge'} />}
            {counts.map((c) => (
              <span key={c} className="badge badge-warning">
                {c}
              </span>
            ))}
          </span>
          {ch.last_activity && <span className="xsmall muted">Zuletzt aktiv: {formatWhen(ch.last_activity)}</span>}
        </span>
        <Icon name="chevronRight" />
      </Link>
    </li>
  );
}

function CreateChannelDialog({ onClose }: { onClose: () => void }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [canPost, setCanPost] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const toast = useToast();
  const submit = async () => {
    if (!title.trim()) {
      setError('Bitte einen Titel angeben.');
      return;
    }
    try {
      const ch = await channelsApi.create({ title: title.trim(), description, students_can_post: canPost });
      toast.success('Kursraum angelegt');
      navigate(`/kursraeume/${ch.id}`);
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <Modal
      title="Eigenen Kursraum anlegen"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={submit}>
            Anlegen
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        <Field
          label="Titel"
          htmlFor="kr-new-title"
          error={error}
          help="Für AGs, Projekte oder Fachschaften. Sie werden Lehrende/r; Mitglieder tragen Sie anschließend unter „Teilnehmende“ ein."
        >
          <input id="kr-new-title" value={title} maxLength={200} onChange={(e) => setTitle(e.target.value)} />
        </Field>
        <Field label="Beschreibung (optional)" htmlFor="kr-new-desc">
          <textarea id="kr-new-desc" rows={3} maxLength={2000} value={description} onChange={(e) => setDescription(e.target.value)} />
        </Field>
        <label className="check">
          <input type="checkbox" checked={canPost} onChange={(e) => setCanPost(e.target.checked)} /> Teilnehmende dürfen auf der Pinnwand schreiben
        </label>
      </div>
    </Modal>
  );
}

export default function ChannelListPage() {
  useTitle('Kursräume');
  const [query, setQuery] = useState('');
  const [kind, setKind] = useStoredState<KindFilter>('kr.kind', '');
  const [showAll, setShowAll] = useStoredState<boolean>('kr.all', false);
  const [limit, setLimit] = useState(PAGE);
  const [creating, setCreating] = useState(false);
  const [archived, setArchived] = useState(false);
  const [child, setChild] = useStoredState<string>('sm-child', '');
  const q = useApi<ChannelListResponse>(
    (signal) => channelsApi.list({ all: showAll, archived, studentId: child || null }, signal),
    [showAll, archived, child],
    { live: ['channels', 'parent_access'] },
  );
  const debounced = useDebounced(query, 150);
  const data = q.data;
  const isParent = !!data?.parent;
  // gemerktes Kind gehört nicht (mehr) zu diesem Konto → zurücksetzen
  useEffect(() => {
    if (child && q.error instanceof ApiError && q.error.status === 403) setChild('');
  }, [child, q.error, setChild]);
  const children = data?.children ?? [];
  const childName = children.find((c) => c.id === data?.student_id)?.name ?? '';
  const supervisor = !!data?.supervisor;
  // Schulleitung ohne eigene Kursräume: gleich alle zeigen
  const autoAll = supervisor && !showAll && data && data.channels.length === 0;

  const list = useMemo(() => {
    const items = (data?.channels ?? []).filter((c) => (!kind || c.kind === kind) && matchChannel(c, debounced));
    return [...items].sort(
      (a, b) =>
        Number(a.archived) - Number(b.archived) ||
        (KIND_ORDER[a.kind] ?? 3) - (KIND_ORDER[b.kind] ?? 3) ||
        a.title.localeCompare(b.title, 'de', { numeric: true }),
    );
  }, [data, kind, debounced]);

  return (
    <div className="page stack">
      <div className="page-head">
        <div>
          <h1>Kursräume</h1>
          <p className="muted small" style={{ margin: 0 }}>
            {isParent && childName ? `${childName} · nur lesen` : 'Material, Aufgaben und Pinnwand je Kurs und Klasse'}
          </p>
        </div>
        {data?.can_create && (
          <button type="button" className="btn btn-primary" onClick={() => setCreating(true)}>
            <Icon name="plus" /> Eigener Kursraum
          </button>
        )}
      </div>

      <div className="card kr-filters">
        <div className="field kr-search">
          <label htmlFor="kr-q">Suchen</label>
          <div className="kr-search-box">
            <Icon name="search" />
            <input id="kr-q" type="search" value={query} placeholder="Kurs, Klasse, Fach oder Lehrkraft" onChange={(e) => setQuery(e.target.value)} />
          </div>
        </div>
        <div className="field">
          <span className="field-label" id="kr-kind-l">
            Art
          </span>
          <SegmentedControl<KindFilter>
            label="Art des Kursraums"
            value={kind}
            onChange={setKind}
            options={[
              { value: '', label: 'Alle' },
              { value: 'course', label: 'Kurse' },
              { value: 'class', label: 'Klassen' },
              { value: 'custom', label: 'Eigene' },
            ]}
          />
        </div>
        <div className="kr-filter-checks">
          {supervisor && (
            <label className="check">
              <input type="checkbox" checked={showAll} onChange={(e) => setShowAll(e.target.checked)} /> Alle Kursräume der Schule (nur lesen)
            </label>
          )}
          {!isParent && (
            <label className="check">
              <input type="checkbox" checked={archived} onChange={(e) => setArchived(e.target.checked)} /> Archivierte anzeigen
            </label>
          )}
        </div>
      </div>

      {isParent && children.length > 1 && (
        <div className="field" style={{ maxWidth: 360 }}>
          <label htmlFor="kr-child">Kind</label>
          <select id="kr-child" value={data?.student_id ?? ''} onChange={(e) => setChild(e.target.value)}>
            {children.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
                {c.class_id ? ` (${c.class_id})` : ''}
              </option>
            ))}
          </select>
        </div>
      )}
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {data?.notice === 'no_teacher_link' && (
        <Alert kind="warning" title="Konto ohne Lehrkraft-Zuordnung">
          {data.notice_text}
        </Alert>
      )}
      {isParent && data?.restricted && (
        <Alert kind="info" title={`${childName || 'Ihr Kind'} ist volljährig`}>
          Die Kursräume sind für Sie nicht freigegeben.
        </Alert>
      )}
      {autoAll && (
        <Alert
          kind="info"
          title="Sie unterrichten keinen eigenen Kurs"
          action={
            <button type="button" className="btn btn-sm" onClick={() => setShowAll(true)}>
              Alle anzeigen
            </button>
          }
        >
          Als Schulleitung sehen Sie alle Kursräume der Schule nur lesend.
        </Alert>
      )}
      {data && !autoAll && (
        <section aria-labelledby="kr-list-h">
          <h2 id="kr-list-h" className="sr-only">
            Liste der Kursräume
          </h2>
          <p className="small muted" aria-live="polite" style={{ marginTop: 0 }}>
            {list.length === data.channels.length ? `${list.length} Kursräume` : `${list.length} von ${data.channels.length} Kursräumen`}
          </p>
          {list.length === 0 ? (
            <Empty icon="search">
              {data.channels.length
                ? 'Keine Kursräume passen zur Suche.'
                : data.notice === 'no_teacher_link' || data.restricted
                  ? 'Keine Kursräume.'
                  : isParent
                    ? 'Für Ihr Kind gibt es noch keine Kursräume.'
                    : 'Für Ihr Konto gibt es noch keine Kursräume.'}
            </Empty>
          ) : (
            <ul className="kr-cards">
              {list.slice(0, limit).map((ch) => (
                <ChannelCard key={ch.id} ch={ch} childId={isParent ? data.student_id : null} />
              ))}
            </ul>
          )}
          {list.length > limit && (
            <div className="center" style={{ marginTop: 'var(--space-3)' }}>
              <button type="button" className="btn" onClick={() => setLimit((l) => l + PAGE)}>
                Weitere {Math.min(PAGE, list.length - limit)} anzeigen
              </button>
            </div>
          )}
        </section>
      )}
      {creating && <CreateChannelDialog onClose={() => setCreating(false)} />}
    </div>
  );
}

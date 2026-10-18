import { useMemo, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { announcements as annApi } from '../api/endpoints';
import type { Announcement, Role } from '../api/types';
import { Icon } from '../components/Icon';
import { Modal } from '../components/Modal';
import { MultiSelect, type SelectOption } from '../components/SearchSelect';
import { AsyncButton, Empty, ErrorBox, Field, Loading } from '../components/ui';
import { useUser } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useApi } from '../hooks/useApi';
import { useCollection } from '../hooks/useCollection';
import { formatDate, formatDateTime } from '../lib/dates';
import { sortBy } from '../lib/format';
import { ALL_ROLES, can, ROLE_LABELS } from '../lib/permissions';

const AUDIENCE: Record<string, string> = {
  all: 'alle',
  staff: 'nur Kollegium',
  classes: 'bestimmte Klassen',
};

function AnnouncementModal({ initial, onClose }: { initial: Partial<Announcement>; onClose: () => void }) {
  const toast = useToast();
  const user = useUser();
  const classes = useCollection('classes');
  const sites = useCollection('sites');
  const [a, setA] = useState<Partial<Announcement>>(() => ({
    audience: user.role === 'lehrer' ? 'classes' : 'all',
    class_ids: [],
    priority: 'normal',
    monitor: false,
    audience_roles: [],
    ...initial,
  }));
  const classOptions: SelectOption[] = useMemo(
    () =>
      sortBy(classes.data ?? [], (c) => c.name).map((c) => ({
        value: c.id,
        label: c.name,
      })),
    [classes.data],
  );
  // Lehrkräfte (Scope own_classes): nur an eigene Klassen, ohne Anheften/Monitor
  const ownClassesOnly = user.role === 'lehrer';
  const save = async () => {
    if (!a.title?.trim()) {
      toast.warning('Bitte einen Titel angeben.');
      return;
    }
    const body: Partial<Announcement> = {
      title: a.title,
      body: a.body ?? '',
      audience: a.audience,
      class_ids: a.audience === 'classes' ? a.class_ids : [],
      audience_roles: a.audience_roles ?? [],
      site: a.site || null,
      valid_from: a.valid_from || null,
      valid_to: a.valid_to || null,
      priority: a.priority,
      monitor: !!a.monitor,
      pinned: !!a.pinned,
    };
    try {
      if (a.id !== undefined) await annApi.update(a.id, body);
      else await annApi.create(body);
      toast.success('Mitteilung veröffentlicht');
      onClose();
    } catch (e) {
      toast.error(e, 'Speichern');
    }
  };
  return (
    <Modal
      size="lg"
      title={a.id !== undefined ? 'Mitteilung bearbeiten' : 'Neue Mitteilung'}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={save}>
            Veröffentlichen
          </AsyncButton>
        </>
      }
    >
      <div className="form-grid">
        <Field label="Titel *" htmlFor="an-title" className="span-all">
          <input id="an-title" type="text" value={a.title ?? ''} onChange={(e) => setA({ ...a, title: e.target.value })} maxLength={200} />
        </Field>
        <Field label="Text" htmlFor="an-body" className="span-all">
          <textarea id="an-body" rows={6} value={a.body ?? ''} onChange={(e) => setA({ ...a, body: e.target.value })} />
        </Field>
        <Field label="Empfänger" htmlFor="an-aud">
          <select id="an-aud" value={a.audience ?? 'all'} onChange={(e) => setA({ ...a, audience: e.target.value })}>
            {Object.entries(AUDIENCE).map(([k, v]) => (
              <option key={k} value={k} disabled={ownClassesOnly && k !== 'classes'}>
                {v}
              </option>
            ))}
          </select>
        </Field>
        {(sites.data?.length ?? 0) > 1 && (
          <Field label="Standort" htmlFor="an-site">
            <select id="an-site" value={a.site ?? ''} onChange={(e) => setA({ ...a, site: e.target.value || null })}>
              <option value="">alle Standorte</option>
              {(sites.data ?? []).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </Field>
        )}
        <Field label="gültig ab" htmlFor="an-from">
          <input id="an-from" type="date" value={a.valid_from ?? ''} onChange={(e) => setA({ ...a, valid_from: e.target.value || null })} />
        </Field>
        <Field label="gültig bis" htmlFor="an-to">
          <input id="an-to" type="date" value={a.valid_to ?? ''} onChange={(e) => setA({ ...a, valid_to: e.target.value || null })} />
        </Field>
        {a.audience === 'classes' && (
          <div className="span-all">
            <MultiSelect
              label={ownClassesOnly ? 'Klassen (Ihre Klassen)' : 'Klassen'}
              options={classOptions}
              values={a.class_ids ?? []}
              onChange={(v) => setA({ ...a, class_ids: v })}
            />
          </div>
        )}
        <div className="span-all">
          <MultiSelect
            label="Nur für Rollen (optional)"
            options={ALL_ROLES.filter((r) => r !== 'monitor').map((r) => ({
              value: r,
              label: ROLE_LABELS[r],
            }))}
            values={a.audience_roles ?? []}
            onChange={(v) => setA({ ...a, audience_roles: v as Role[] })}
          />
        </div>
        <div className="span-all row">
          <label className="check">
            <input
              type="checkbox"
              checked={a.priority === 'wichtig'}
              onChange={(e) =>
                setA({
                  ...a,
                  priority: e.target.checked ? 'wichtig' : 'normal',
                })
              }
            />{' '}
            wichtig (hervorheben)
          </label>
          {!ownClassesOnly && (
            <label className="check">
              <input type="checkbox" checked={!!a.pinned} onChange={(e) => setA({ ...a, pinned: e.target.checked })} /> oben anheften
            </label>
          )}
          {can(user, 'monitor.read') && user.role !== 'lehrer' && (
            <label className="check">
              <input type="checkbox" checked={!!a.monitor} onChange={(e) => setA({ ...a, monitor: e.target.checked })} /> auf Monitoren anzeigen
            </label>
          )}
        </div>
      </div>
    </Modal>
  );
}

/** `/mitteilungen` gibt es nicht mehr als eigene Seite – die Mitteilungen gehören zu den Nachrichten. */
export default function AnnouncementsPage() {
  return <Navigate to="/nachrichten?f=mitteilungen" replace />;
}

/** Mitteilungen der Schule (Aushang) – im Postfach als Ordner „Mitteilungen“. */
export function AnnouncementsPanel() {
  const user = useUser();
  const toast = useToast();
  const poster = can(user, 'announcement.post');
  const [showAll, setShowAll] = useState(false);
  const [edit, setEdit] = useState<Partial<Announcement> | null>(null);
  const q = useApi(() => annApi.list(showAll ? { all: 1 } : undefined), [showAll], { live: ['announcements'] });
  return (
    <div className="stack ann-panel">
      <div className="row-between">
        <h2 style={{ margin: 0 }}>Mitteilungen</h2>
        <div className="actions">
          {poster && (
            <label className="check">
              <input type="checkbox" checked={showAll} onChange={(e) => setShowAll(e.target.checked)} /> auch abgelaufene/künftige
            </label>
          )}
          {poster && (
            <button type="button" className="btn btn-primary" onClick={() => setEdit({})}>
              <Icon name="plus" /> Neue Mitteilung
            </button>
          )}
        </div>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {q.data && q.data.length === 0 && <Empty icon="megaphone">Keine Mitteilungen.</Empty>}
      <div className="stack">
        {(q.data ?? []).map((a) => (
          <article key={a.id} className={`card announcement${a.priority === 'wichtig' ? ' important' : ''}`}>
            <div className="row-between">
              <h2 style={{ fontSize: 'var(--fs-lg)', margin: 0 }}>
                {a.pinned && <span aria-label="angeheftet">📌 </span>}
                {a.priority === 'wichtig' && (
                  <span className="badge badge-danger" style={{ marginRight: 6 }}>
                    Wichtig
                  </span>
                )}
                {a.title}
              </h2>
              {a.can_delete && (
                <div className="row">
                  <button type="button" className="btn btn-ghost btn-sm" onClick={() => setEdit(a)} aria-label={`Mitteilung ${a.title} bearbeiten`}>
                    <Icon name="edit" />
                  </button>
                  <AsyncButton
                    className="btn btn-ghost btn-sm"
                    confirm={`Mitteilung „${a.title}“ löschen?`}
                    onClick={async () => {
                      try {
                        await annApi.remove(a.id);
                        toast.success('Mitteilung gelöscht');
                        q.reload();
                      } catch (e) {
                        toast.error(e);
                      }
                    }}
                  >
                    <Icon name="trash" />
                    <span className="sr-only">löschen</span>
                  </AsyncButton>
                </div>
              )}
            </div>
            {a.body && (
              <div className="body" style={{ marginTop: 8 }}>
                {a.body}
              </div>
            )}
            <div className="xsmall faint" style={{ marginTop: 8 }}>
              {[
                a.author_name,
                a.created_at ? formatDateTime(a.created_at) : null,
                a.audience ? `für ${AUDIENCE[a.audience] ?? a.audience}${a.class_ids?.length ? `: ${a.class_ids.join(', ')}` : ''}` : null,
                a.valid_from || a.valid_to ? `gültig ${a.valid_from ? `ab ${formatDate(a.valid_from)}` : ''} ${a.valid_to ? `bis ${formatDate(a.valid_to)}` : ''}` : null,
                a.monitor ? 'Monitor' : null,
              ]
                .filter(Boolean)
                .join(' · ')}
            </div>
          </article>
        ))}
      </div>
      {edit && (
        <AnnouncementModal
          initial={edit}
          onClose={() => {
            setEdit(null);
            q.reload();
          }}
        />
      )}
    </div>
  );
}

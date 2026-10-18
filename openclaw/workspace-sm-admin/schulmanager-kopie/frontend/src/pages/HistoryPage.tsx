import { useState } from 'react';
import { history as historyApi } from '../api/endpoints';
import type { AuditEntry, HistoryEntry } from '../api/types';
import { HelpTip } from '../components/HelpTip';
import { Icon } from '../components/Icon';
import { VirtualTable, type Column } from '../components/VirtualTable';
import { AsyncButton, ErrorBox, Field, Loading, Tabs } from '../components/ui';
import { useUser } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useApi } from '../hooks/useApi';
import { invalidateAll } from '../hooks/useCollection';
import { useDebounced, useTitle } from '../hooks/misc';
import { formatDateTime } from '../lib/dates';
import { can } from '../lib/permissions';

function scopeText(s: HistoryEntry['scope']): string {
  if (!s) return '';
  return Array.isArray(s) ? s.join(', ') : String(s);
}

function VersionsTab() {
  const toast = useToast();
  const [limit, setLimit] = useState(100);
  const q = useApi(() => historyApi.list(limit), [limit], { live: ['*'] });
  const columns: Column<HistoryEntry>[] = [
    { key: 'v', header: 'Version', className: 'num', render: (h) => h.version, sortValue: (h) => h.version, width: '90px' },
    { key: 'at', header: 'Zeitpunkt', render: (h) => formatDateTime(h.created_at), sortValue: (h) => h.created_at, width: '170px' },
    { key: 'user', header: 'Benutzer', render: (h) => h.user_display_name || h.user || '', width: '170px' },
    {
      key: 'msg',
      header: 'Änderung',
      render: (h) => (
        <>
          {h.current && <span className="badge badge-primary">aktuell</span>} {h.message}
          {h.restored_from ? <span className="small muted"> (aus Version {h.restored_from})</span> : null}
        </>
      ),
    },
    { key: 'scope', header: 'Bereich', render: (h) => <span className="small muted">{scopeText(h.scope)}</span>, width: '190px' },
    {
      key: 'act',
      header: <span className="sr-only">Aktionen</span>,
      className: 'actions',
      width: '180px',
      render: (h) => (
        <AsyncButton
          className="btn btn-sm"
          confirm={`Stand von Version ${h.version} („${h.message}“) wiederherstellen? Dies erzeugt eine neue Version.`}
          onClick={async () => {
            try {
              const r = (await historyApi.restore(h.version)) as { version?: number };
              toast.success(`Version ${h.version} wiederhergestellt${r?.version ? ` (neu: ${r.version})` : ''}`);
              invalidateAll();
              q.reload();
            } catch (e) {
              toast.error(e);
            }
          }}
        >
          <Icon name="history" /> Wiederherstellen
        </AsyncButton>
      ),
    },
  ];
  return (
    <div className="stack">
      <div className="row">
        <AsyncButton
          className="btn btn-primary"
          confirm="Letzte Änderung rückgängig machen?"
          onClick={async () => {
            try {
              await historyApi.undo();
              toast.success('Letzte Änderung rückgängig gemacht');
              invalidateAll();
              q.reload();
            } catch (e) {
              toast.error(e, 'Rückgängig');
            }
          }}
        >
          <Icon name="undo" /> Rückgängig
        </AsyncButton>
        <HelpTip>Jede Änderung an den Planungsdaten erzeugt eine Version. „Rückgängig“ macht die letzte Änderung schrittweise rückgängig.</HelpTip>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {q.data && <VirtualTable rows={q.data} columns={columns} rowKey={(h) => String(h.version)} caption="Versionen" height="60vh" />}
      {q.data && q.data.length >= limit && (
        <button type="button" className="btn" onClick={() => setLimit((l) => l + 200)}>
          Ältere laden
        </button>
      )}
    </div>
  );
}

function AuditTab() {
  const [user, setUser] = useState('');
  const [action, setAction] = useState('');
  const du = useDebounced(user, 300);
  const da = useDebounced(action, 300);
  const q = useApi(() => historyApi.audit({ limit: 1000, user: du || undefined, action: da || undefined }), [du, da]);
  const columns: Column<AuditEntry>[] = [
    { key: 'at', header: 'Zeitpunkt', render: (a) => formatDateTime(a.created_at), sortValue: (a) => a.created_at, width: '170px' },
    { key: 'user', header: 'Benutzer', render: (a) => a.user ?? (a as AuditEntry & { username?: string }).username ?? '', width: '150px' },
    { key: 'action', header: 'Aktion', render: (a) => <span className="mono small">{a.action}</span>, sortValue: (a) => a.action, width: '200px' },
    { key: 'target', header: 'Ziel', render: (a) => <span className="small">{a.target ?? ''}</span>, width: '180px' },
    {
      key: 'details',
      header: 'Details',
      render: (a) => {
        const d = typeof a.details === 'string' ? a.details : a.details ? JSON.stringify(a.details) : '';
        return (
          <span className="small muted" title={d}>
            {d}
          </span>
        );
      },
    },
    { key: 'ip', header: 'IP', render: (a) => <span className="small mono">{a.ip ?? ''}</span>, width: '120px' },
  ];
  return (
    <div>
      <div className="toolbar">
        <Field label="Benutzername" htmlFor="au-user">
          <input id="au-user" type="search" value={user} onChange={(e) => setUser(e.target.value)} />
        </Field>
        <Field label="Aktion (Präfix)" htmlFor="au-action" hint="z. B. auth., user., system.">
          <input id="au-action" type="search" value={action} onChange={(e) => setAction(e.target.value)} />
        </Field>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {q.data && <VirtualTable rows={q.data} columns={columns} rowKey={(a) => String(a.id)} caption="Audit-Protokoll" height="60vh" />}
    </div>
  );
}

export default function HistoryPage() {
  useTitle('Verlauf & Audit');
  const me = useUser();
  const canHistory = can(me, 'history.restore');
  const canAudit = can(me, 'audit.read');
  const [tab, setTab] = useState<'verlauf' | 'audit'>(canHistory ? 'verlauf' : 'audit');
  return (
    <div className="page">
      <div className="page-head">
        <h1>Verlauf & Audit</h1>
      </div>
      <Tabs
        label="Bereiche"
        tabs={[
          { key: 'verlauf', label: 'Versionen (Undo)', hidden: !canHistory },
          { key: 'audit', label: 'Audit-Protokoll', hidden: !canAudit },
        ]}
        active={tab}
        onChange={setTab}
      />
      {tab === 'verlauf' && canHistory && <VersionsTab />}
      {tab === 'audit' && canAudit && <AuditTab />}
    </div>
  );
}

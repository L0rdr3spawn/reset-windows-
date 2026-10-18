import { useEffect, useId, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Empty, ErrorBox, AsyncButton, Loading, SegmentedControl, Tabs } from '../../components/ui';
import { HelpTip } from '../../components/HelpTip';
import { useToast } from '../../context/ToastContext';
import { useUser } from '../../context/AuthContext';
import { useApi } from '../../hooks/useApi';
import { useTitle } from '../../hooks/misc';
import { can } from '../../lib/permissions';
import {
  notificationsApi,
  type AppNotification,
  type NotificationMode,
  type NotificationSettings,
  type SchoolNotificationSettings,
} from './api';
import { NotificationItem } from './NotificationItem';
import { changedModes, changedSchoolRules, groupByDay, groupKinds, safeLink, validRetention, validTime } from './logic';
import './benachrichtigungen.css';

type TabKey = 'liste' | 'einstellungen' | 'schule';

// ------------------------------------------------------------------------- Liste
function ListTab() {
  const toast = useToast();
  const navigate = useNavigate();
  const [filter, setFilter] = useState<'alle' | 'ungelesen'>('alle');
  const [older, setOlder] = useState<AppNotification[]>([]);
  const q = useApi((signal) => notificationsApi.list({ unread: filter === 'ungelesen', limit: 50 }, signal), [filter], {
    live: ['notifications'],
    keepPrevious: true,
  });
  useEffect(() => setOlder([]), [filter]);
  const first = q.data?.items ?? [];
  const items = useMemo(() => {
    const seen = new Set(first.map((n) => n.id));
    return [...first, ...older.filter((n) => !seen.has(n.id))];
  }, [first, older]);
  const lastId = items.length ? items[items.length - 1].id : undefined;
  const unread = q.data?.unread ?? 0;

  const run = async (fn: () => Promise<unknown>) => {
    try {
      await fn();
      q.reload();
      setOlder([]);
    } catch (e) {
      toast.error(e);
    }
  };
  const open = async (n: AppNotification) => {
    if (!n.read) await run(() => notificationsApi.markRead([n.id]));
    const target = safeLink(n.link);
    if (target) navigate(target);
  };
  const more = async () => {
    try {
      const r = await notificationsApi.list({ unread: filter === 'ungelesen', limit: 50, before: lastId });
      setOlder((o) => [...o, ...r.items]);
    } catch (e) {
      toast.error(e);
    }
  };

  return (
    <section aria-label="Benachrichtigungen" className="stack-sm">
      <div className="nt-toolbar">
        <SegmentedControl
          label="Anzeigen"
          value={filter}
          onChange={setFilter}
          options={[
            { value: 'alle', label: 'Alle' },
            { value: 'ungelesen', label: unread ? `Ungelesen (${unread})` : 'Ungelesen' },
          ]}
        />
        <span className="spacer" />
        <AsyncButton className="btn" disabled={unread === 0} onClick={() => run(() => notificationsApi.markRead(null))}>
          Alle als gelesen
        </AsyncButton>
        <AsyncButton className="btn" confirm="Alle gelesenen Benachrichtigungen löschen?" onClick={() => run(() => notificationsApi.clearRead())}>
          Gelesene löschen
        </AsyncButton>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading ? <Loading /> : null}
      {!q.initialLoading && items.length === 0 && !q.error ? <Empty icon="bell" title={filter === 'ungelesen' ? 'Alles gelesen' : 'Noch keine Benachrichtigungen'} /> : null}
      {groupByDay(items).map((g) => (
        <div key={g.label} className="card nt-group">
          <h2 className="nt-group-title">{g.label}</h2>
          <ul className="nt-list">
            {g.items.map((n) => (
              <NotificationItem
                key={n.id}
                n={n}
                onOpen={(x) => void open(x)}
                onToggleRead={(x) => void run(() => notificationsApi.markRead([x.id], !x.read))}
                onRemove={(x) => void run(() => notificationsApi.remove(x.id))}
              />
            ))}
          </ul>
        </div>
      ))}
      {q.data?.more || older.length >= 50 ? (
        <button type="button" className="btn nt-more" onClick={() => void more()}>
          Ältere laden
        </button>
      ) : null}
    </section>
  );
}

// ------------------------------------------------------------------------- Einstellungen
function ModeSelect({ id, value, onChange, disabled, mailAvailable, options }: { id: string; value: NotificationMode; onChange: (m: NotificationMode) => void; disabled?: boolean; mailAvailable: boolean; options: { value: NotificationMode; label: string }[] }) {
  return (
    <select id={id} value={value} disabled={disabled} onChange={(e) => onChange(e.target.value as NotificationMode)}>
      {options.map((o) => (
        <option key={o.value} value={o.value} disabled={o.value === 'mail' && !mailAvailable && value !== 'mail'}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

function SettingsForm({ data, onSaved }: { data: NotificationSettings; onSaved: (d: NotificationSettings) => void }) {
  const toast = useToast();
  const uid = useId();
  const [modes, setModes] = useState<Record<string, NotificationMode>>({});
  const [digest, setDigest] = useState(data.digest);
  const [quiet, setQuiet] = useState(data.quiet_enabled);
  const [from, setFrom] = useState(data.quiet_from);
  const [to, setTo] = useState(data.quiet_to);
  const changed = changedModes(data.kinds, modes);
  const timesOk = !quiet || (validTime(from) && validTime(to));
  const dirty = Object.keys(changed).length > 0 || digest !== data.digest || quiet !== data.quiet_enabled || (quiet && (from !== data.quiet_from || to !== data.quiet_to));
  const save = async () => {
    try {
      const next = await notificationsApi.saveSettings({ modes: changed, digest, quiet_enabled: quiet, quiet_from: from, quiet_to: to });
      setModes({});
      onSaved(next);
      toast.success('Einstellungen gespeichert');
    } catch (e) {
      toast.error(e);
    }
  };
  return (
    <div className="stack-sm">
      {groupKinds(data.kinds).map((g) => (
        <section key={g.group} className="card" aria-label={g.group}>
          <h2 className="nt-group-title">{g.group}</h2>
          <ul className="nt-settings">
            {g.kinds.map((k) => (
              <li key={k.kind} className="nt-setting">
                <label htmlFor={`${uid}-${k.kind}`}>
                  {k.label}
                  {k.help ? <HelpTip>{k.help}</HelpTip> : null}
                </label>
                <ModeSelect id={`${uid}-${k.kind}`} value={modes[k.kind] ?? k.mode} disabled={k.locked} mailAvailable={data.mail_available} options={data.modes} onChange={(m) => setModes((s) => ({ ...s, [k.kind]: m }))} />
                {k.locked ? <span className="badge">Von der Schule vorgegeben</span> : null}
              </li>
            ))}
          </ul>
        </section>
      ))}
      <section className="card stack-sm" aria-label="E-Mail">
        <h2 className="nt-group-title">
          E-Mail
          {!data.mail_available ? <HelpTip>Der E-Mail-Versand ist an dieser Schule nicht eingerichtet. Bis dahin gibt es Benachrichtigungen nur in der App.</HelpTip> : null}
        </h2>
        <label className="check">
          <input type="checkbox" checked={digest} disabled={!data.mail_available} onChange={(e) => setDigest(e.target.checked)} /> Statt einzelner E-Mails eine tägliche Zusammenfassung
        </label>
        <label className="check">
          <input type="checkbox" checked={quiet} disabled={!data.mail_available} onChange={(e) => setQuiet(e.target.checked)} /> Ruhezeiten: in dieser Zeit keine E-Mails
          <HelpTip>Die Benachrichtigungen erscheinen weiterhin sofort in der App. Zurückgehaltene E-Mails gehen danach gesammelt raus.</HelpTip>
        </label>
        {quiet && data.mail_available ? (
          <div className="nt-times">
            <label htmlFor={`${uid}-von`}>von</label>
            <input id={`${uid}-von`} type="time" value={from} aria-invalid={!validTime(from) || undefined} onChange={(e) => setFrom(e.target.value)} />
            <label htmlFor={`${uid}-bis`}>bis</label>
            <input id={`${uid}-bis`} type="time" value={to} aria-invalid={!validTime(to) || undefined} onChange={(e) => setTo(e.target.value)} />
          </div>
        ) : null}
      </section>
      <div>
        <AsyncButton className="btn btn-primary" disabled={!dirty || !timesOk} onClick={save}>
          Speichern
        </AsyncButton>
      </div>
    </div>
  );
}

function SettingsTab() {
  const q = useApi((signal) => notificationsApi.settings(signal), []);
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!q.data) return <Loading />;
  return <SettingsForm key={JSON.stringify([q.data.digest, q.data.quiet_enabled, q.data.quiet_from, q.data.quiet_to])} data={q.data} onSaved={(d) => q.setData(d)} />;
}

// ------------------------------------------------------------------------- Schulvorgaben
function SchoolForm({ data, onSaved }: { data: SchoolNotificationSettings; onSaved: (d: SchoolNotificationSettings) => void }) {
  const toast = useToast();
  const uid = useId();
  const [rules, setRules] = useState<Record<string, { mode: NotificationMode; locked: boolean }>>(() => Object.fromEntries(data.kinds.map((k) => [k.kind, { mode: k.mode, locked: k.locked }])));
  const [days, setDays] = useState(String(data.retention_days));
  const changed = changedSchoolRules(data.kinds, rules);
  const daysOk = validRetention(days, data.retention_min, data.retention_max);
  const dirty = Object.keys(changed).length > 0 || Number(days) !== data.retention_days;
  const save = async () => {
    try {
      const next = await notificationsApi.saveSchool(changed, Number(days));
      onSaved(next);
      toast.success('Schulvorgaben gespeichert');
    } catch (e) {
      toast.error(e);
    }
  };
  return (
    <div className="stack-sm">
      {groupKinds(data.kinds).map((g) => (
        <section key={g.group} className="card" aria-label={g.group}>
          <h2 className="nt-group-title">{g.group}</h2>
          <ul className="nt-settings">
            {g.kinds.map((k) => (
              <li key={k.kind} className="nt-setting">
                <label htmlFor={`${uid}-${k.kind}`}>{k.label}</label>
                <ModeSelect id={`${uid}-${k.kind}`} value={rules[k.kind]?.mode ?? k.mode} mailAvailable={data.mail_available} options={data.modes} onChange={(m) => setRules((s) => ({ ...s, [k.kind]: { ...(s[k.kind] ?? { locked: false }), mode: m } }))} />
                <label className="check">
                  <input type="checkbox" checked={rules[k.kind]?.locked ?? false} onChange={(e) => setRules((s) => ({ ...s, [k.kind]: { mode: s[k.kind]?.mode ?? k.mode, locked: e.target.checked } }))} /> Pflicht
                  <HelpTip>Gesperrt: Alle erhalten diese Art genau so; Einzelne können sie nicht ändern.</HelpTip>
                </label>
              </li>
            ))}
          </ul>
        </section>
      ))}
      <section className="card">
        <div className="field">
          <label htmlFor={`${uid}-tage`}>
            Aufbewahrung in Tagen
            <HelpTip>Ältere Benachrichtigungen werden automatisch gelöscht.</HelpTip>
          </label>
          <input id={`${uid}-tage`} type="number" min={data.retention_min} max={data.retention_max} value={days} aria-invalid={!daysOk || undefined} onChange={(e) => setDays(e.target.value)} />
          {!daysOk ? (
            <span className="error-text">
              {data.retention_min} bis {data.retention_max} Tage
            </span>
          ) : null}
        </div>
      </section>
      <div>
        <AsyncButton className="btn btn-primary" disabled={!dirty || !daysOk} onClick={save}>
          Speichern
        </AsyncButton>
      </div>
    </div>
  );
}

function SchoolTab() {
  const q = useApi((signal) => notificationsApi.school(signal), []);
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!q.data) return <Loading />;
  return <SchoolForm key={JSON.stringify(q.data.kinds.map((k) => [k.kind, k.mode, k.locked]))} data={q.data} onSaved={(d) => q.setData(d)} />;
}

export default function NotificationsPage() {
  useTitle('Benachrichtigungen');
  const user = useUser();
  const [tab, setTab] = useState<TabKey>('liste');
  const admin = can(user, 'settings.edit');
  return (
    <div className="page">
      <div className="page-head">
        <h1>Benachrichtigungen</h1>
      </div>
      <Tabs<TabKey>
        label="Bereiche"
        active={tab}
        onChange={setTab}
        tabs={[
          { key: 'liste', label: 'Liste' },
          { key: 'einstellungen', label: 'Einstellungen' },
          { key: 'schule', label: 'Schulvorgaben', hidden: !admin },
        ]}
      />
      {tab === 'liste' && <ListTab />}
      {tab === 'einstellungen' && <SettingsTab />}
      {tab === 'schule' && admin && <SchoolTab />}
    </div>
  );
}

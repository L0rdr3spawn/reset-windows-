/**
 * Bereich „Gruppen“ (Lehrende): Einteilungen mit Gruppen anlegen – von Hand oder automatisch (zufällig/alphabetisch,
 * nach Gruppenzahl oder Gruppengröße) –, Mitglieder festlegen und Material/Ordner auf Gruppen beschränken.
 * Gruppenabgaben stellt man an der Aufgabe ein („Bewertung“).
 */
import { useMemo, useState } from 'react';
import { errorMessage } from '../../../api/client';
import { Icon } from '../../../components/Icon';
import { Modal } from '../../../components/Modal';
import { HelpTip } from '../../../components/HelpTip';
import { AsyncButton, Empty, ErrorBox, Field, Loading, SegmentedControl } from '../../../components/ui';
import { useToast } from '../../../context/ToastContext';
import { useApi } from '../../../hooks/useApi';
import type { ChannelDetail } from '../types';
import { assignApi } from './api';
import { GateDialog, type GateTarget } from './GateDialog';
import type { GroupEntry, GroupMember, GroupSet, GroupsResponse } from './types';
import './aufgaben.css';

function NameDialog({ title, label, initial, onClose, onSave }: { title: string; label: string; initial: string; onClose: () => void; onSave: (name: string) => Promise<unknown> }) {
  const [name, setName] = useState(initial);
  const [error, setError] = useState<string | null>(null);
  const go = async () => {
    if (!name.trim()) {
      setError('Bitte einen Namen angeben.');
      return;
    }
    try {
      await onSave(name.trim());
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <Modal
      title={title}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={go}>
            Speichern
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        {error && (
          <p role="alert" className="kr-error">
            {error}
          </p>
        )}
        <Field label={label} htmlFor="au-name">
          <input id="au-name" value={name} maxLength={120} onChange={(e) => setName(e.target.value)} />
        </Field>
      </div>
    </Modal>
  );
}

function MembersDialog({ set, group, onClose, onSave }: { set: GroupSet; group: GroupEntry; onClose: () => void; onSave: (ids: number[]) => Promise<unknown> }) {
  const [picked, setPicked] = useState<number[]>(group.members.map((m) => m.user_id));
  const [error, setError] = useState<string | null>(null);
  const pool = useMemo(() => {
    const rows: { m: GroupMember; where: string | null }[] = [];
    for (const g of set.groups) for (const m of g.members) rows.push({ m, where: g.id === group.id ? null : g.name });
    for (const m of set.unassigned ?? []) rows.push({ m, where: null });
    return rows.sort((a, b) => a.m.name.localeCompare(b.m.name, 'de'));
  }, [set, group.id]);
  const toggle = (id: number) => setPicked(picked.includes(id) ? picked.filter((x) => x !== id) : [...picked, id]);
  const go = async () => {
    try {
      await onSave(picked);
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <Modal
      title={`Mitglieder – ${group.name}`}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={go}>
            Speichern ({picked.length})
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        {error && (
          <p role="alert" className="kr-error">
            {error}
          </p>
        )}
        <div className="row">
          <strong>Teilnehmende</strong>
          <HelpTip>Wer schon in einer anderen Gruppe dieser Einteilung ist, wird hierher umgesetzt.</HelpTip>
        </div>
        <div className="au-pool" role="group" aria-label="Teilnehmende">
          {pool.map(({ m, where }) => (
            <label key={m.user_id} className="check">
              <input type="checkbox" checked={picked.includes(m.user_id)} onChange={() => toggle(m.user_id)} /> {m.name}
              {m.class_id ? <span className="xsmall muted"> · {m.class_id}</span> : null}
              {where ? <span className="xsmall muted"> · jetzt in {where}</span> : null}
            </label>
          ))}
          {!pool.length && <p className="small muted">Keine Teilnehmenden mit Konto.</p>}
        </div>
      </div>
    </Modal>
  );
}

function AutoDialog({ set, onClose, onRun }: { set: GroupSet; onClose: () => void; onRun: (body: Parameters<typeof assignApi.autoGroups>[2]) => Promise<unknown> }) {
  const [by, setBy] = useState<'size' | 'count'>('size');
  const [n, setN] = useState('3');
  const [shuffle, setShuffle] = useState(true);
  const [mode, setMode] = useState<'new' | 'fill'>(set.groups.length ? 'fill' : 'new');
  const [error, setError] = useState<string | null>(null);
  const go = async () => {
    const num = Number(n);
    if (mode === 'new' && (!Number.isInteger(num) || num < 1)) {
      setError('Bitte eine ganze Zahl ab 1 angeben.');
      return;
    }
    try {
      await onRun({ ...(mode === 'new' ? (by === 'size' ? { size: num } : { count: num }) : {}), shuffle, mode });
      onClose();
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  return (
    <Modal
      title={`Automatisch einteilen – ${set.name}`}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" onClick={go}>
            Einteilen
          </AsyncButton>
        </>
      }
    >
      <div className="stack-sm">
        {error && (
          <p role="alert" className="kr-error">
            {error}
          </p>
        )}
        <SegmentedControl<'new' | 'fill'>
          label="Vorgehen"
          value={mode}
          onChange={setMode}
          options={[
            { value: 'new', label: 'Neu einteilen (ersetzt alle Gruppen)' },
            { value: 'fill', label: 'Nur noch nicht Eingeteilte verteilen', title: 'Verteilt auf die vorhandenen Gruppen, immer in die kleinste' },
          ]}
        />
        {mode === 'new' && (
          <div className="form-grid">
            <Field label="Einteilen nach" htmlFor="au-by">
              <select id="au-by" value={by} onChange={(e) => setBy(e.target.value as 'size' | 'count')}>
                <option value="size">Gruppengröße</option>
                <option value="count">Gruppenzahl</option>
              </select>
            </Field>
            <Field label={by === 'size' ? 'Personen je Gruppe' : 'Anzahl Gruppen'} htmlFor="au-n">
              <input id="au-n" inputMode="numeric" value={n} onChange={(e) => setN(e.target.value)} />
            </Field>
          </div>
        )}
        <label className="check">
          <input type="checkbox" checked={shuffle} onChange={(e) => setShuffle(e.target.checked)} /> Zufällig (sonst alphabetisch)
        </label>
      </div>
    </Modal>
  );
}

type Dialog =
  | { kind: 'newSet' }
  | { kind: 'renameSet'; set: GroupSet }
  | { kind: 'newGroup'; set: GroupSet }
  | { kind: 'renameGroup'; group: GroupEntry }
  | { kind: 'members'; set: GroupSet; group: GroupEntry }
  | { kind: 'auto'; set: GroupSet }
  | { kind: 'gate'; target: GateTarget };

export default function GroupsTab({ detail }: { detail: ChannelDetail }) {
  const ch = detail.channel;
  const toast = useToast();
  const q = useApi<GroupsResponse>((signal) => assignApi.groups(ch.id, signal), [ch.id], { live: [`channel:${ch.id}:`] });
  const [dialog, setDialog] = useState<Dialog | null>(null);
  const [adding, setAdding] = useState('');
  const data = q.data;

  const run = async (fn: () => Promise<unknown>, ok?: string) => {
    try {
      await fn();
      if (ok) toast.success(ok);
      q.reload();
    } catch (e) {
      toast.error(e);
      throw e;
    }
  };
  const gateRows = useMemo(() => {
    if (!data?.gates) return [];
    const names = new Map(data.sets.flatMap((s) => s.groups.map((g) => [g.id, g.name] as const)));
    const rows: { target: GateTarget; groups: string[] }[] = [];
    for (const [id, gids] of Object.entries(data.gates.items)) {
      const it = detail.items.find((i) => i.id === Number(id));
      if (it && gids.length) rows.push({ target: { kind: 'item', id: it.id, title: it.title }, groups: gids.map((g) => names.get(g) ?? '?') });
    }
    for (const [id, gids] of Object.entries(data.gates.folders)) {
      const f = detail.folders.find((x) => x.id === Number(id));
      if (f && gids.length) rows.push({ target: { kind: 'folder', id: f.id, title: f.name }, groups: gids.map((g) => names.get(g) ?? '?') });
    }
    return rows;
  }, [data, detail.items, detail.folders]);

  const addable = [
    ...detail.folders.map((f) => ({ key: `f${f.id}`, target: { kind: 'folder', id: f.id, title: f.name } as GateTarget, label: `Ordner: ${f.name}` })),
    ...detail.items.filter((i) => !i.info_card).map((i) => ({ key: `i${i.id}`, target: { kind: 'item', id: i.id, title: i.title } as GateTarget, label: `${i.type_label}: ${i.title}` })),
  ];

  return (
    <div className="stack-sm">
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {data && (
        <>
          <div className="kr-toolbar">
            <button type="button" className="btn btn-sm btn-primary" onClick={() => setDialog({ kind: 'newSet' })} disabled={data.sets.length >= data.limits.sets}>
              <Icon name="plus" /> Neue Einteilung
            </button>
            {(data.without_account ?? 0) > 0 && <span className="small muted">{data.without_account} Teilnehmende ohne Konto können keiner Gruppe angehören.</span>}
          </div>
          {!data.sets.length && <Empty icon="users">Noch keine Gruppen. Legen Sie eine Einteilung an (z. B. „Projektgruppen“) – für Gruppenabgaben und Material nur für bestimmte Gruppen.</Empty>}
          <div className="au-sets">
            {data.sets.map((s) => (
              <section key={s.id} className="card stack-sm" aria-labelledby={`au-set-${s.id}`}>
                <div className="row-between">
                  <h3 id={`au-set-${s.id}`} style={{ margin: 0 }}>
                    {s.name}
                  </h3>
                  <div className="row">
                    <button type="button" className="btn btn-sm" onClick={() => setDialog({ kind: 'newGroup', set: s })}>
                      <Icon name="plus" /> Gruppe
                    </button>
                    <button type="button" className="btn btn-sm" onClick={() => setDialog({ kind: 'auto', set: s })}>
                      <Icon name="sparkles" /> Automatisch einteilen
                    </button>
                    <button type="button" className="btn btn-sm btn-ghost" onClick={() => setDialog({ kind: 'renameSet', set: s })} aria-label={`Einteilung ${s.name} umbenennen`}>
                      <Icon name="edit" />
                    </button>
                    <AsyncButton className="btn btn-sm btn-ghost" confirm={`Einteilung „${s.name}“ mit allen Gruppen löschen?`} onClick={() => run(() => assignApi.deleteSet(ch.id, s.id), 'Einteilung gelöscht')}>
                      <Icon name="trash" />
                      <span className="sr-only">Einteilung {s.name} löschen</span>
                    </AsyncButton>
                  </div>
                </div>
                {(s.unassigned?.length ?? 0) > 0 && s.groups.length > 0 && (
                  <p className="small muted">
                    Noch keiner Gruppe zugeordnet ({s.unassigned!.length}): {s.unassigned!.map((m) => m.name).join(', ')}
                  </p>
                )}
                <div className="au-groups">
                  {s.groups.map((g) => (
                    <div key={g.id} className="au-group-card">
                      <div className="row-between">
                        <strong>{g.name}</strong>
                        <span className="xsmall muted">{g.members.length} Personen</span>
                      </div>
                      <ul className="au-members">
                        {g.members.map((m) => (
                          <li key={m.user_id}>
                            <span>{m.name}</span>
                            {m.class_id ? <span className="xsmall muted">{m.class_id}</span> : null}
                          </li>
                        ))}
                        {!g.members.length && <li className="small muted">Noch leer</li>}
                      </ul>
                      <div className="row">
                        <button type="button" className="btn btn-sm" onClick={() => setDialog({ kind: 'members', set: s, group: g })}>
                          <Icon name="users" /> Mitglieder
                        </button>
                        <button type="button" className="btn btn-sm btn-ghost" onClick={() => setDialog({ kind: 'renameGroup', group: g })} aria-label={`Gruppe ${g.name} umbenennen`}>
                          <Icon name="edit" />
                        </button>
                        <AsyncButton className="btn btn-sm btn-ghost" confirm={`Gruppe „${g.name}“ löschen?`} onClick={() => run(() => assignApi.deleteGroup(ch.id, g.id), 'Gruppe gelöscht')}>
                          <Icon name="trash" />
                          <span className="sr-only">Gruppe {g.name} löschen</span>
                        </AsyncButton>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            ))}
          </div>

          {data.sets.some((s) => s.groups.length) && (
            <section className="card stack-sm" aria-labelledby="au-gates-h">
              <h3 id="au-gates-h" style={{ margin: 0 }}>
                Material nur für bestimmte Gruppen
              </h3>
              {gateRows.length ? (
                <ul className="au-gate-list">
                  {gateRows.map((r) => (
                    <li key={`${r.target.kind}${r.target.id}`}>
                      <span>
                        <Icon name={r.target.kind === 'folder' ? 'folder' : 'list'} /> {r.target.title} <span className="xsmall muted">→ {r.groups.join(', ')}</span>
                      </span>
                      <button type="button" className="btn btn-sm" onClick={() => setDialog({ kind: 'gate', target: r.target })}>
                        Ändern
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="small muted">Alles ist für alle Teilnehmenden sichtbar.</p>
              )}
              <Field label="Beschränkung hinzufügen" htmlFor="au-gate-add">
                <select
                  id="au-gate-add"
                  value={adding}
                  onChange={(e) => {
                    const hit = addable.find((a) => a.key === e.target.value);
                    setAdding('');
                    if (hit) setDialog({ kind: 'gate', target: hit.target });
                  }}
                >
                  <option value="">– Material oder Ordner wählen –</option>
                  {addable.map((a) => (
                    <option key={a.key} value={a.key}>
                      {a.label}
                    </option>
                  ))}
                </select>
              </Field>
            </section>
          )}
        </>
      )}

      {dialog?.kind === 'newSet' && <NameDialog title="Neue Einteilung" label="Name (z. B. Projektgruppen)" initial="" onClose={() => setDialog(null)} onSave={(name) => run(() => assignApi.createSet(ch.id, name))} />}
      {dialog?.kind === 'renameSet' && <NameDialog title="Einteilung umbenennen" label="Name" initial={dialog.set.name} onClose={() => setDialog(null)} onSave={(name) => run(() => assignApi.renameSet(ch.id, dialog.set.id, name))} />}
      {dialog?.kind === 'newGroup' && <NameDialog title="Neue Gruppe" label="Name" initial={`Gruppe ${dialog.set.groups.length + 1}`} onClose={() => setDialog(null)} onSave={(name) => run(() => assignApi.createGroup(ch.id, dialog.set.id, name))} />}
      {dialog?.kind === 'renameGroup' && <NameDialog title="Gruppe umbenennen" label="Name" initial={dialog.group.name} onClose={() => setDialog(null)} onSave={(name) => run(() => assignApi.renameGroup(ch.id, dialog.group.id, name))} />}
      {dialog?.kind === 'members' && <MembersDialog set={dialog.set} group={dialog.group} onClose={() => setDialog(null)} onSave={(ids) => run(() => assignApi.setMembers(ch.id, dialog.group.id, ids), 'Mitglieder gespeichert')} />}
      {dialog?.kind === 'auto' && <AutoDialog set={dialog.set} onClose={() => setDialog(null)} onRun={(body) => run(() => assignApi.autoGroups(ch.id, dialog.set.id, body), 'Eingeteilt')} />}
      {dialog?.kind === 'gate' && <GateDialog channelId={ch.id} target={dialog.target} onClose={() => setDialog(null)} onDone={q.reload} />}
    </div>
  );
}

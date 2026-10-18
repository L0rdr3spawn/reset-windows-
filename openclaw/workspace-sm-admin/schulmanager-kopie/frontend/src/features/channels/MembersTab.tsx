/**
 * Bereich „Teilnehmende“: Lehrende, Teilnehmende (Stundenplan + eingetragen), ausgetragene Schüler/innen und Eltern.
 * Lehrende des Kursraums tragen Schüler/innen ein und aus (deren Eltern lesen dann mit, bei Volljährigen nur mit
 * Freigabe), die Schulleitung/Administration zusätzlich Lehrende. Wer den Kursraum erstellt hat, bleibt immer drin.
 */
import { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { AsyncButton, ErrorBox, Loading, SegmentedControl } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { useDebounced } from '../../hooks/misc';
import { channelsApi } from './api';
import type { ChannelDetail, MemberCandidate, MembersResponse } from './types';

type AddRole = 'student' | 'teacher';

function AddMembers({ channelId, canAddTeachers, onDone }: { channelId: number; canAddTeachers: boolean; onDone: () => void }) {
  const toast = useToast();
  const [role, setRole] = useState<AddRole>('student');
  const [q, setQ] = useState('');
  const term = useDebounced(q.trim(), 250);
  const [found, setFound] = useState<MemberCandidate[] | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (term.length < 2) {
      setFound(null);
      return undefined;
    }
    const ctl = new AbortController();
    setBusy(true);
    channelsApi
      .candidates(channelId, term, role, ctl.signal)
      .then((r) => setFound(r.candidates))
      .catch(() => undefined)
      .finally(() => setBusy(false));
    return () => ctl.abort();
  }, [channelId, term, role]);

  const add = async (c: MemberCandidate) => {
    try {
      await channelsApi.addMembers(channelId, [c.user_id], role);
      toast.success(`${c.name} eingetragen`);
      setFound((list) => (list ? list.map((x) => (x.user_id === c.user_id ? { ...x, member: true } : x)) : list));
      onDone();
    } catch (e) {
      toast.error(e);
    }
  };

  return (
    <section className="card stack-sm" aria-labelledby="kr-m-add">
      <h3 id="kr-m-add" className="kr-section-h">
        Mitglieder eintragen
        {role === 'student' && (
          <HelpTip>
            Eingetragene Schüler/innen sehen den Kursraum sofort. Ihre Eltern lesen automatisch mit, bei volljährigen Schüler/innen nur, wenn sie das freigegeben haben.
          </HelpTip>
        )}
      </h3>
      {canAddTeachers && (
        <SegmentedControl<AddRole>
          label="Rolle"
          value={role}
          onChange={(r) => {
            setRole(r);
            setFound(null);
          }}
          options={[
            { value: 'student', label: 'Schüler/innen' },
            { value: 'teacher', label: 'Lehrende' },
          ]}
        />
      )}
      <div className="field">
        <label htmlFor="kr-m-q">{role === 'student' ? 'Name, Benutzername oder Klasse (z. B. „7b“)' : 'Name oder Benutzername'}</label>
        <input id="kr-m-q" type="search" value={q} placeholder="mindestens 2 Zeichen" onChange={(e) => setQ(e.target.value)} />
      </div>
      {busy && <p className="xsmall muted">Suche …</p>}
      {found && found.length === 0 && <p className="small muted">Keine passenden Konten.</p>}
      {found && found.length > 0 && (
        <ul className="kr-people">
          {found.map((c) => (
            <li key={c.user_id}>
              <span className="kr-person">{c.name}</span>
              {c.class_id && <span className="badge">{c.class_id}</span>}
              <span className="xsmall muted">{c.username}</span>
              {c.member ? (
                <span className="badge badge-success">schon Mitglied</span>
              ) : (
                <AsyncButton className="btn btn-sm" onClick={() => add(c)}>
                  <Icon name="plus" /> Eintragen
                </AsyncButton>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function MembersTab({ detail, reload }: { detail: ChannelDetail; reload: () => void }) {
  const ch = detail.channel;
  const q = useApi<MembersResponse>((signal) => channelsApi.members(ch.id, signal), [ch.id], { live: [`channel:${ch.id}:`] });
  const { user } = useAuth();
  const toast = useToast();
  const data = q.data;
  const staff = ch.role === 'teacher' || ch.role === 'supervisor';
  const manage = !!data?.can_manage_members;
  const self = data?.extra.find((e) => e.self);
  const byClass = new Map<string, MembersResponse['students']>();
  for (const s of data?.students ?? []) {
    const key = s.class_id ?? '';
    byClass.set(key, [...(byClass.get(key) ?? []), s]);
  }
  const refresh = () => {
    q.reload();
    reload();
  };
  const joinAsTeacher = async () => {
    if (!user) return;
    try {
      await channelsApi.addMembers(ch.id, [Number(user.id)], 'teacher');
      toast.success('Sie sind jetzt Lehrende/r in diesem Kursraum');
      refresh();
    } catch (e) {
      toast.error(e);
    }
  };
  const remove = async (userId: number, name: string) => {
    try {
      await channelsApi.removeMember(ch.id, userId);
      toast.success(`${name} ausgetragen`);
      refresh();
    } catch (e) {
      toast.error(e);
    }
  };
  const readmit = async (userId: number, name: string) => {
    try {
      await channelsApi.readmit(ch.id, userId);
      toast.success(`${name} ist wieder Mitglied`);
      refresh();
    } catch (e) {
      toast.error(e);
    }
  };
  const removeButton = (userId: number | null | undefined, name: string, allowed: boolean) =>
    allowed && userId ? (
      <AsyncButton className="btn btn-sm btn-ghost" confirm={`${name} austragen?`} onClick={() => remove(userId, name)}>
        <Icon name="close" /> Austragen
      </AsyncButton>
    ) : null;

  return (
    <div className="stack-sm">
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {data && (
        <>
          {data.can_add_teachers && !self && ch.role === 'supervisor' && (
            <div className="row">
              <AsyncButton className="btn btn-sm" confirm="Sich als Lehrende/r eintragen? Das wird protokolliert." onClick={joinAsTeacher}>
                <Icon name="plus" /> Mich als Lehrende/n eintragen
              </AsyncButton>
              <span className="xsmall muted">z. B. um die Pinnwand zu moderieren oder Material zu verwalten</span>
            </div>
          )}
          {manage && <AddMembers channelId={ch.id} canAddTeachers={!!data.can_add_teachers} onDone={refresh} />}
          <section className="card" aria-labelledby="kr-m-t">
            <h3 id="kr-m-t" className="kr-section-h">
              Lehrende <span className="muted small">({data.counts.teachers})</span>
            </h3>
            <ul className="kr-people">
              {data.teachers.map((t) => (
                <li key={t.id}>
                  <span className="kr-person">{t.name}</span>
                  {t.class_teacher && <span className="badge badge-primary">Klassenleitung</span>}
                  {staff && t.has_account === false && <span className="badge">kein Konto</span>}
                </li>
              ))}
              {data.extra
                .filter((e) => e.role === 'teacher')
                .map((e) => (
                  <li key={`x${e.user_id ?? e.name}`}>
                    <span className="kr-person">{e.name}</span>
                    {e.creator ? <span className="badge badge-primary">hat den Kursraum erstellt</span> : <span className="badge">zusätzlich</span>}
                    {removeButton(e.user_id, e.name, !e.creator && (!!data.can_add_teachers || e.self))}
                  </li>
                ))}
              {!data.teachers.length && !data.extra.some((e) => e.role === 'teacher') && <li className="muted small">Keine Lehrkraft eingetragen.</li>}
            </ul>
          </section>
          <section className="card" aria-labelledby="kr-m-s">
            <h3 id="kr-m-s" className="kr-section-h">
              Teilnehmende <span className="muted small">({data.counts.students})</span>
              {ch.kind === 'course' && (
                <HelpTip>Teilnehmende ergeben sich aus der Kurswahl im Stundenplan (Kursteil); zusätzlich lassen sich Schüler/innen eintragen oder austragen.</HelpTip>
              )}
            </h3>
            {[...byClass.entries()].map(([cls, list]) => (
              <div key={cls || 'ohne'} className="kr-people-group">
                {byClass.size > 1 && <div className="small muted">{cls ? `Klasse ${cls}` : 'ohne Klasse'}</div>}
                <ul className="kr-people kr-people-cols">
                  {list.map((s, i) => (
                    <li key={s.id ?? `${s.name}-${i}`}>
                      <span className="kr-person">{s.name}</span>
                      {staff && s.has_account === false && <span className="badge">kein Konto</span>}
                      {removeButton(s.user_id, s.name, manage)}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
            {data.extra.filter((e) => e.role === 'student').length > 0 && (
              <div className="kr-people-group">
                <div className="small muted">Zusätzlich eingetragen</div>
                <ul className="kr-people">
                  {data.extra
                    .filter((e) => e.role === 'student')
                    .map((e) => (
                      <li key={`xs${e.user_id ?? e.name}`}>
                        <span className="kr-person">{e.name}</span>
                        {e.class_id && <span className="badge">{e.class_id}</span>}
                        {removeButton(e.user_id, e.name, manage || e.self)}
                      </li>
                    ))}
                </ul>
              </div>
            )}
            {!data.students.length && !data.extra.some((e) => e.role === 'student') && <p className="muted small">Keine Teilnehmenden.</p>}
          </section>
          {staff && data.excluded.length > 0 && (
            <section className="card" aria-labelledby="kr-m-x">
              <h3 id="kr-m-x" className="kr-section-h">
                Ausgetragen <span className="muted small">({data.excluded.length})</span>
              </h3>
              <ul className="kr-people">
                {data.excluded.map((e) => (
                  <li key={`ex${e.user_id ?? e.name}`}>
                    <span className="kr-person">{e.name}</span>
                    {e.class_id && <span className="badge">{e.class_id}</span>}
                    {manage && e.user_id && (
                      <AsyncButton className="btn btn-sm btn-ghost" onClick={() => readmit(e.user_id!, e.name)}>
                        <Icon name="undo" /> Wieder aufnehmen
                      </AsyncButton>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          )}
          {staff && (
            <section className="card" aria-labelledby="kr-m-p">
              <h3 id="kr-m-p" className="kr-section-h">
                Eltern (lesen mit) <span className="muted small">({data.parents.length})</span>
                <HelpTip>
                  Eltern sehen freigegebenes Material, Aufgaben und Pinnwand, ohne Abgaben und ohne schreiben zu können. Volljährige Schüler/innen entscheiden selbst, ob ihre Eltern mitlesen.
                </HelpTip>
              </h3>
              {data.parents.length ? (
                <ul className="kr-people kr-people-cols">
                  {data.parents.map((p) => (
                    <li key={p.user_id}>
                      <span className="kr-person">{p.name}</span>
                      <span className="xsmall muted">{p.children.join(', ')}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="muted small">Keine Elternkonten mit Zugang.</p>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}

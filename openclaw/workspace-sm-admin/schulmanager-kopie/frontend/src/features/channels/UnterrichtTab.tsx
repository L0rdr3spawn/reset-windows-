/**
 * Bereich „Unterricht“: die Stunden, die stattgefunden haben (Entfall nicht, Verlegungen am tatsächlichen Tag) – je
 * Stunde das Unterrichtsmaterial des Tages und die gestellten Hausaufgaben (Links). Thema und Hausaufgaben-Text aus dem
 * Klassenbuch sehen nur Lehrende/Schulleitung (Schulinterna). Schüler/innen und Eltern sehen nur, wann sie gefehlt
 * haben (rot: krank / beurlaubt / gefehlt – anwesend: nichts), und Material, das sie noch nicht geöffnet haben.
 * Klick auf eine Stunde klappt Material und Hausaufgaben auf.
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { fileUrl } from '../../api/files';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Alert, Empty, ErrorBox, Loading } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { addDays, formatLong, todayISO } from '../../lib/dates';
import { channelsApi, type LessonLogEntry } from './api';
import { Glyph } from './components';
import { TextViewer } from './dialogs';
import { safeHref } from './logic';
import type { ChannelDetail, Item } from './types';

type LogItem = Item & { viewed?: boolean };

function MaterialLinks({ items, onView, onOpen }: { items: LogItem[]; onView: (i: Item) => void; onOpen: (i: LogItem) => void }) {
  return (
    <ul className="kr-log-items">
      {items.map((it) => {
        const href = it.type === 'link' ? safeHref(it.url) : null;
        return (
          <li key={it.id}>
            <Glyph name={it.type === 'file' ? 'file' : it.type} size={16} />{' '}
            {it.type === 'file' && it.file ? (
              <a href={fileUrl(it.file.id)} download={it.file.filename} onClick={() => onOpen(it)}>
                {it.title}
              </a>
            ) : href ? (
              <a href={href} target="_blank" rel="noopener noreferrer nofollow" onClick={() => onOpen(it)}>
                {it.title}
              </a>
            ) : it.type === 'assignment' ? (
              <Link to={`?tab=aufgaben&aufgabe=${it.id}`} onClick={() => onOpen(it)}>
                {it.title}
              </Link>
            ) : (
              <button
                type="button"
                className="kr-linkbtn"
                onClick={() => {
                  onOpen(it);
                  onView(it);
                }}
              >
                {it.title}
              </button>
            )}
            {it.viewed === false && <span className="badge badge-info kr-new">neu</span>}
            {it.submittable && (
              <Link className="badge badge-primary" style={{ marginLeft: 6 }} to={`?tab=aufgaben&aufgabe=${it.id}`} onClick={() => onOpen(it)}>
                {it.submission ? `Abgabe: ${it.submission.status_label}` : 'Abgabe möglich'}
              </Link>
            )}
          </li>
        );
      })}
    </ul>
  );
}

function LessonRow({ l, register, onView, onOpen }: { l: LessonLogEntry; register: boolean; onView: (i: Item) => void; onOpen: (i: LogItem) => void }) {
  const att = l.attendance === 'absent' ? 'absent' : null;
  const tasks = l.assignments ?? [];
  const [open, setOpen] = useState(att === 'absent');
  return (
    <li className={`card kr-log${att ? ` kr-att-${att}` : ''}`}>
      <button type="button" className="kr-log-head" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        <span className="kr-log-when">
          <strong>{formatLong(l.date)}</strong> · {l.period_label ?? `${l.period + 1}.`} Stunde{l.time ? ` (${l.time})` : ''}
        </span>
        <span className="kr-log-meta">
          {att && <span className={`badge kr-att-badge kr-att-badge-${att}`}>{l.attendance_label}</span>}
          {(l.unviewed ?? 0) > 0 && <span className="badge badge-info">{l.unviewed} neu</span>}
          {l.materials.length > 0 && (
            <span className="small muted" title="Material zur Stunde">
              <Glyph name="file" size={14} /> {l.materials.length}
            </span>
          )}
          {tasks.length > 0 && (
            <span className="badge badge-primary" title="Hausaufgaben">
              HA {tasks.length}
            </span>
          )}
          <span className={`kr-chev${open ? ' open' : ''}`} aria-hidden="true">
            <Icon name="chevronDown" />
          </span>
        </span>
      </button>
      {open && (
        <div className="stack-sm kr-log-body">
          <div className="small muted">{[l.subject_name || l.subject, l.teachers.join(', ')].filter(Boolean).join(' · ')}</div>
          {l.changes.length > 0 && (
            <div className="small">
              {l.changes.map((c) => (
                <span key={c} className="badge badge-warning" style={{ marginRight: 4 }}>
                  {c}
                </span>
              ))}
            </div>
          )}
          {register &&
            (l.topic ? (
              <p style={{ margin: 0 }}>
                <span className="muted small">Thema (Klassenbuch): </span>
                {l.topic}
              </p>
            ) : (
              <p className="small muted" style={{ margin: 0 }}>
                Kein Thema im Klassenbuch eingetragen.
              </p>
            ))}
          {register && l.homework && (
            <p style={{ margin: 0 }}>
              <span className="muted small">Hausaufgabe (Klassenbuch): </span>
              {l.homework}
            </p>
          )}
          {l.materials.length > 0 ? (
            <MaterialLinks items={l.materials} onView={onView} onOpen={onOpen} />
          ) : (
            <p className="small muted" style={{ margin: 0 }}>
              Kein Material zu dieser Stunde.
            </p>
          )}
          {tasks.length > 0 && (
            <div className="stack-sm">
              <span className="muted small">Hausaufgaben:</span>
              <MaterialLinks items={tasks} onView={onView} onOpen={onOpen} />
            </div>
          )}
        </div>
      )}
    </li>
  );
}

export default function UnterrichtTab({ detail }: { detail: ChannelDetail }) {
  const ch = detail.channel;
  const [to, setTo] = useState(todayISO());
  const from = addDays(to, -27);
  const q = useApi((signal) => channelsApi.lessonLog(ch.id, { from, days: 28 }, signal), [ch.id, from], { live: ['channels'] });
  const [view, setView] = useState<Item | null>(null);
  const data = q.data;
  const onOpen = (it: LogItem) => {
    if (it.viewed !== false) return;
    void channelsApi
      .markViewed(ch.id, it.id)
      .then(() => q.reload())
      .catch(() => undefined);
  };
  const missed = data?.lessons.filter((l) => l.attendance === 'absent') ?? [];
  const register = !!data?.register;
  const unviewed = data?.unviewed ?? 0;
  return (
    <div className="stack-sm">
      <div className="row-between">
        <span className="small muted">
          Stunden der letzten 4 Wochen{' '}
          <HelpTip>
            {register
              ? 'Nur Stunden, die stattgefunden haben (verlegte am tatsächlichen Tag). Klick auf eine Stunde zeigt Thema und Hausaufgabe aus dem Klassenbuch, das Material des Tages und die gestellten Hausaufgaben.'
              : 'Nur Stunden, die stattgefunden haben. Rot markiert sind Stunden, in denen Sie gefehlt haben (krank, beurlaubt oder gefehlt). Klick auf eine Stunde zeigt das Material und die Hausaufgaben dazu.'}
          </HelpTip>
        </span>
        <div className="row">
          <button type="button" className="btn btn-sm" onClick={() => setTo(addDays(to, -28))}>
            <Icon name="chevronLeft" /> Früher
          </button>
          {to < todayISO() && (
            <button type="button" className="btn btn-sm" onClick={() => setTo(todayISO())}>
              Aktuell
            </button>
          )}
        </div>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!data && q.loading && <Loading />}
      {data && (unviewed > 0 || missed.length > 0) && (
        <Alert kind="info">
          {unviewed > 0 && (unviewed === 1 ? '1 Material noch nicht angesehen. ' : `${unviewed} Materialien noch nicht angesehen. `)}
          {missed.length > 0 &&
            (missed.length === 1 ? '1 Stunde verpasst – Material und Hausaufgabe stehen bei der Stunde.' : `${missed.length} Stunden verpasst – Material und Hausaufgaben stehen bei den Stunden.`)}
        </Alert>
      )}
      {data && !data.lessons.length && !data.other_materials.length && <Empty>Für diesen Zeitraum gibt es keine Stunden.</Empty>}
      {data && data.other_materials.length > 0 && (
        <section className="card stack-sm">
          <strong>Weiteres Unterrichtsmaterial</strong>
          <MaterialLinks items={data.other_materials} onView={setView} onOpen={onOpen} />
        </section>
      )}
      {data && (
        <ul className="kr-log-list">
          {data.lessons.map((l) => (
            <LessonRow key={`${l.date}-${l.period}`} l={l} register={register} onView={setView} onOpen={onOpen} />
          ))}
        </ul>
      )}
      {view && <TextViewer channelId={ch.id} item={view} onClose={() => setView(null)} />}
    </div>
  );
}

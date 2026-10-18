/**
 * Sichtbarkeit wählen: sofort, verborgen, ab Zeitpunkt, **zur nächsten Stunde** oder **zur Unterrichtsstunde**
 * (sichtbar ab Stundenbeginn laut Zeitraster; entfällt die Stunde, gibt der Server zur nächsten stattfindenden
 * Stunde frei). Die Stundenliste kommt aus `GET /channels/{id}/lessons` (Woche, Ferien, Entfall/Verlegung).
 */
import { useId, useState } from 'react';
import { HelpText, PageHelp } from '../../components/Help';
import { ErrorBox, Loading } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { addDays, formatShort, relativeDayLabel, todayISO } from '../../lib/dates';
import { channelsApi } from './api';
import { LessonStatusBadge } from './components';
import { groupByDate, lessonLine, nextHeldLesson, type VisibilityDraft } from './logic';

export { DEFAULT_DRAFT, draftToInput, type VisibilityDraft } from './logic';
import type { ChannelKind, LessonsResponse, UpcomingLesson, VisibilityChoice } from './types';

const LESSON_MODES: VisibilityChoice[] = ['lesson', 'next_lesson'];
const MODES: { value: VisibilityChoice; label: string }[] = [
  { value: 'visible', label: 'Sofort sichtbar' },
  { value: 'hidden', label: 'Verborgen' },
  { value: 'next_lesson', label: 'Zur nächsten Stunde' },
  { value: 'scheduled', label: 'Ab Zeitpunkt' },
  { value: 'lesson', label: 'Zur Unterrichtsstunde' },
];

/** Anzeige der Stunde, an die „Zur nächsten Stunde“ bindet. */
function NextLessonInfo({ channelId }: { channelId: number }) {
  const q = useApi<LessonsResponse>((signal) => channelsApi.lessons(channelId, { days: 56 }, signal), [channelId], {
    live: [`channel:${channelId}:`, 'substitutions', 'timetable'],
  });
  if (q.initialLoading) return <Loading label="Nächste Stunde wird gesucht …" />;
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  const next = q.data ? nextHeldLesson(q.data.lessons) : null;
  return (
    <p className="small" style={{ margin: 'var(--space-2) 0 0' }} aria-live="polite">
      {next ? (
        <>
          Nächste Stunde: <strong>{next.label}</strong>
        </>
      ) : (
        <span className="muted">In den nächsten acht Wochen findet keine Stunde statt.</span>
      )}
    </p>
  );
}

export function VisibilityPicker({
  channelId,
  kind,
  value,
  onChange,
  allowLesson,
  legend = 'Sichtbarkeit für Teilnehmende und Eltern',
  modes,
}: {
  channelId: number;
  kind: ChannelKind;
  value: VisibilityDraft;
  onChange: (v: VisibilityDraft) => void;
  allowLesson: boolean;
  legend?: string;
  /** nur diese Modi anbieten (Standard: alle erlaubten) */
  modes?: VisibilityChoice[];
}) {
  const name = useId();
  const options = MODES.filter((m) => (!LESSON_MODES.includes(m.value) || allowLesson) && (!modes || modes.includes(m.value)));
  return (
    <fieldset className="kr-fieldset">
      <legend className="with-help">
        {legend}
        <PageHelp label="Hilfe zur Sichtbarkeit">
          Verborgenes sehen nur Lehrende. „Zur nächsten Stunde“ und „Zur Unterrichtsstunde“ geben ab Stundenbeginn frei; fällt
          die Stunde aus oder wird der Tag schulfrei, ab der nächsten stattfindenden Stunde desselben Kurses. „Ab Zeitpunkt“
          gibt zum gewählten Datum und zur Uhrzeit frei.
        </PageHelp>
      </legend>
      <div className="kr-vis-modes" role="radiogroup">
        {options.map((m) => (
          <label key={m.value} className={`kr-vis-mode${value.mode === m.value ? ' active' : ''}`}>
            <input type="radio" name={name} value={m.value} checked={value.mode === m.value} onChange={() => onChange({ ...value, mode: m.value })} />
            <strong>{m.label}</strong>
          </label>
        ))}
      </div>
      {value.mode === 'scheduled' && (
        <div className="field" style={{ marginTop: 'var(--space-3)' }}>
          <label htmlFor={`${name}-from`}>Sichtbar ab</label>
          <input id={`${name}-from`} type="datetime-local" value={value.from} onChange={(e) => onChange({ ...value, from: e.target.value })} required />
        </div>
      )}
      {value.mode === 'next_lesson' && <NextLessonInfo channelId={channelId} />}
      {value.mode === 'lesson' && (
        <div style={{ marginTop: 'var(--space-3)' }}>
          <LessonPicker channelId={channelId} kind={kind} selected={value.lesson?.key ?? null} onSelect={(lesson) => onChange({ ...value, lesson })} />
        </div>
      )}
    </fieldset>
  );
}

/** Liste kommender Stunden eines Kursraums zur Auswahl (Radio-Gruppe nach Tagen). */
export function LessonPicker({
  channelId,
  kind,
  selected,
  onSelect,
}: {
  channelId: number;
  kind: ChannelKind;
  selected: string | null;
  onSelect: (lesson: UpcomingLesson) => void;
}) {
  const [past, setPast] = useState(false);
  const [all, setAll] = useState(false);
  const today = todayISO();
  const from = past ? addDays(today, -14) : today;
  const days = past ? 14 + 28 : 28;
  const q = useApi<LessonsResponse>((signal) => channelsApi.lessons(channelId, { from, days, all }, signal), [channelId, from, days, all], {
    live: [`channel:${channelId}:`, 'substitutions', 'timetable'],
  });
  const name = useId();
  const data = q.data;
  const groups = data ? groupByDate(data.lessons) : [];
  const skippedByReason = new Map<string, { dates: string[]; count: number }>();
  for (const s of data?.skipped ?? []) {
    const e = skippedByReason.get(s.reason) ?? { dates: [], count: 0 };
    e.dates.push(s.date);
    e.count += s.count;
    skippedByReason.set(s.reason, e);
  }
  return (
    <div className="kr-lessons">
      <div className="row-between" style={{ marginBottom: 'var(--space-2)' }}>
        <strong className="small">Unterrichtsstunde wählen</strong>
        <div className="row">
          {kind === 'class' && (
            <label className="check small">
              <input type="checkbox" checked={all} onChange={(e) => setAll(e.target.checked)} />{' '}
              <HelpText help="Ohne Haken stehen hier nur Ihre eigenen Stunden in dieser Klasse.">alle Stunden der Klasse</HelpText>
            </label>
          )}
          <button type="button" className="btn btn-sm btn-ghost" onClick={() => setPast((p) => !p)} aria-pressed={past}>
            {past ? 'Nur heute und später' : 'Frühere Stunden anzeigen'}
          </button>
        </div>
      </div>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading label="Stunden werden geladen …" />}
      {data && data.custom && <p className="small muted">Dieser Kursraum hat keine Stunden im Stundenplan.</p>}
      {data && !data.custom && !data.lessons.length && <p className="small muted">In diesem Zeitraum gibt es keine Stunden.</p>}
      <div role="radiogroup" aria-label="Unterrichtsstunden" className="kr-lesson-days">
        {groups.map((g) => (
          <div key={g.date} className="kr-lesson-day">
            <div className="kr-lesson-date">{relativeDayLabel(g.date, today) === formatShort(g.date) ? formatShort(g.date) : `${relativeDayLabel(g.date, today)} · ${formatShort(g.date)}`}</div>
            {g.lessons.map((l) => (
              <label key={l.key} className={`kr-lesson${selected === l.key ? ' active' : ''}${l.status === 'entfall' ? ' cancelled' : ''}`}>
                <input type="radio" name={name} checked={selected === l.key} onChange={() => onSelect(l)} />
                <span className="kr-lesson-body">
                  <span className="kr-lesson-line">
                    <strong>{lessonLine(l)}</strong>
                    {l.week_no ? <span className="badge">Woche {l.week_no}</span> : null}
                    {l.started ? <span className="badge badge-success">begonnen – sofort sichtbar</span> : null}
                    {l.status === 'entfall' ? <span className="badge badge-warning">entfällt – Freigabe zur nächsten Stunde</span> : null}
                  </span>
                  <span className="xsmall muted">
                    {l.subject_name || l.subject}
                    {l.classes.length ? ` · ${l.classes.join(', ')}` : ''}
                    {l.items.length ? ` · ${l.items.length} Material bereits gebunden` : ''}
                  </span>
                  <LessonStatusBadge status={l.status} changes={l.changes} />
                </span>
              </label>
            ))}
          </div>
        ))}
      </div>
      {skippedByReason.size > 0 && (
        <ul className="xsmall muted kr-skipped">
          {[...skippedByReason.entries()].map(([reason, e]) => (
            <li key={reason}>
              {reason}: {e.count} {e.count === 1 ? 'Stunde fällt' : 'Stunden fallen'} aus ({formatShort(e.dates[0]!)}
              {e.dates.length > 1 ? ` – ${formatShort(e.dates[e.dates.length - 1]!)}` : ''})
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

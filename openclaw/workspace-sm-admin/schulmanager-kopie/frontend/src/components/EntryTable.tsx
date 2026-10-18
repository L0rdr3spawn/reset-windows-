import { Fragment } from 'react';
import type { Entry } from '../api/types';
import { classAbsenceText, groupWithClassRows, kindInfo, shortNote, sortEntries, type ClassAbsenceRow } from '../lib/substitution';
import { formatShort } from '../lib/dates';
import { ClassAbbr, RoomAbbr, SubjectAbbr, TeacherAbbr } from './Abbr';
import { Icon } from './Icon';
import { KindBadge } from './ui';

function roomCell(e: Entry) {
  if (e.new_room && e.new_room !== e.room) {
    return (
      <>
        {e.room && (
          <span className="strike faint nowrap">
            <RoomAbbr id={e.room} />
          </span>
        )}{' '}
        <strong className="nowrap">
          <RoomAbbr id={e.new_room} />
        </strong>
      </>
    );
  }
  return <span className="nowrap">{e.room ? <RoomAbbr id={e.room} /> : '–'}</span>;
}

/** Klassenliste: Umbruch nur zwischen den Klassen, nie innerhalb („Q1-1“). */
function classesCell(e: Entry) {
  if (!e.classes.length) return e.kind === 'aufsicht' ? ((e as Entry & { area?: string }).area ?? '') : '–';
  return e.classes.map((c, i) => (
    <Fragment key={c}>
      {i > 0 && ', '}
      <span className="nowrap">
        <ClassAbbr id={c} />
      </span>
    </Fragment>
  ));
}

function teacherCell(e: Entry) {
  if (e.substitute && e.substitute !== e.teacher) {
    return (
      <>
        {e.teacher && (
          <span className="strike faint" aria-label={`statt ${e.teacher}`}>
            <TeacherAbbr id={e.teacher} />
          </span>
        )}{' '}
        <strong>
          <TeacherAbbr id={e.substitute} />
        </strong>
      </>
    );
  }
  if (e.kind === 'entfall' && e.teacher) {
    return (
      <span className="strike">
        <TeacherAbbr id={e.teacher} />
      </span>
    );
  }
  return e.teacher ? <TeacherAbbr id={e.teacher} /> : '–';
}

function noteCell(e: Entry, short: boolean) {
  const extra: string[] = [];
  // Nur ergänzen, wenn der Hinweis der Engine die Herkunft nicht schon nennt
  if (e.moved_from !== null && e.moved_from !== undefined && e.moved_from !== '' && !/verlegt|vorgezogen/i.test(e.note ?? '')) {
    extra.push(typeof e.moved_from === 'number' ? `verlegt von ${e.moved_from + 1}. Std.` : `verlegt von ${e.moved_from}`);
  }
  const full = [...extra, e.note].filter(Boolean).join(' · ');
  const text = short ? [...extra, shortNote(e.note)].filter(Boolean).join(' · ') : full;
  const shortened = short && text !== full;
  return (
    <>
      {e.warning && (
        <span className="badge badge-warning" title="Bitte prüfen">
          <Icon name="alert" className="icon" /> prüfen
        </span>
      )}{' '}
      {e.proposed && (
        <span className="badge badge-info" title="Automatischer Vorschlag – erst nach Freigabe für alle sichtbar">
          Vorschlag
        </span>
      )}{' '}
      {e.manual && <span className="badge badge-primary">manuell</span>}{' '}
      {shortened ? (
        <span title={full}>
          {text}
          <span className="sr-only"> ({full})</span>
        </span>
      ) : (
        text
      )}
    </>
  );
}

/**
 * Tabelle der Vertretungsplan-Einträge, farbig nach Art, gruppiert nach Klasse.
 * `classAbsences`: gemeldete Klassen-Abwesenheiten als eine Zeile je Klasse (statt einer Zeile je Stunde).
 */
export function EntryTable({
  entries,
  classAbsences = [],
  onSelect,
  selectedId,
  grouped = true,
  showDate,
  caption,
  showSite,
  shortNotes,
}: {
  entries: Entry[];
  classAbsences?: ClassAbsenceRow[];
  onSelect?: (e: Entry) => void;
  selectedId?: string | null;
  grouped?: boolean;
  showDate?: boolean;
  caption: string;
  showSite?: boolean;
  /** lange Aufsichtshinweise kürzen (voller Text im Tooltip) – nicht für den Druck */
  shortNotes?: boolean;
}) {
  const cols = 7 + (showDate ? 1 : 0) + (showSite ? 1 : 0);
  const renderClassRow = (r: ClassAbsenceRow) => (
    <tr key={`abwesend-${r.class}`} className={`kind-row ${kindInfo('klasse_abwesend').cls}`}>
      {showDate && <td />}
      <td className="nowrap">
        <strong>{r.when}</strong>
      </td>
      <td className="nowrap">{r.class}</td>
      <td>–</td>
      <td>–</td>
      <td>–</td>
      <td>
        <KindBadge kind="klasse_abwesend" />
      </td>
      <td>{classAbsenceText(r)}</td>
      {showSite && <td />}
    </tr>
  );
  const renderRow = (e: Entry) => {
    const info = kindInfo(e.kind);
    const clickable = !!onSelect;
    return (
      <tr
        key={e.id}
        className={`kind-row ${info.cls}${clickable ? ' clickable' : ''}${selectedId === e.id ? ' selected' : ''}`}
        onClick={clickable ? () => onSelect?.(e) : undefined}
        onKeyDown={
          clickable
            ? (ev) => {
                if (ev.key === 'Enter' || ev.key === ' ') {
                  ev.preventDefault();
                  onSelect?.(e);
                }
              }
            : undefined
        }
        tabIndex={clickable ? 0 : undefined}
        aria-selected={clickable ? selectedId === e.id : undefined}
      >
        {showDate && <td className="nowrap">{formatShort(e.date)}</td>}
        <td>
          <strong className="nowrap">{e.period_label || `${e.period + 1}.`}</strong> <span className="xsmall nowrap">{e.time}</span>
        </td>
        {/* Klassenlisten (Kurse „Q1-1, Q1-2, …“) und Raum alt/neu dürfen umbrechen – sonst verdrängen sie den Hinweis */}
        <td>{classesCell(e)}</td>
        <td>{e.subject ? <SubjectAbbr id={e.subject} /> : '–'}</td>
        <td className="nowrap">{teacherCell(e)}</td>
        <td>{roomCell(e)}</td>
        <td>
          <KindBadge kind={e.kind} />
        </td>
        <td className="note-col">{noteCell(e, !!shortNotes)}</td>
        {showSite && <td>{e.site ?? ''}</td>}
      </tr>
    );
  };

  const header = (
    <thead>
      <tr>
        {showDate && <th scope="col">Datum</th>}
        <th scope="col">Std.</th>
        <th scope="col">Klasse</th>
        <th scope="col">Fach</th>
        <th scope="col">Lehrkraft</th>
        <th scope="col">Raum</th>
        <th scope="col">Art</th>
        <th scope="col" className="note-col">Hinweis</th>
        {showSite && <th scope="col">Standort</th>}
      </tr>
    </thead>
  );

  return (
    <div className="table-wrap">
      <table className="table">
        <caption className="sr-only">{caption}</caption>
        {header}
        <tbody>
          {grouped ? (
            groupWithClassRows(entries, classAbsences).map(([cls, absence, list]) => (
              <Fragment key={cls}>
                <tr>
                  <th colSpan={cols} scope="colgroup" style={{ position: 'static', background: 'var(--surface-3)', color: 'var(--text)' }}>
                    {cls}
                  </th>
                </tr>
                {absence && renderClassRow(absence)}
                {list.map(renderRow)}
              </Fragment>
            ))
          ) : (
            <>
              {classAbsences.map(renderClassRow)}
              {sortEntries(entries, 'period').map(renderRow)}
            </>
          )}
        </tbody>
      </table>
    </div>
  );
}

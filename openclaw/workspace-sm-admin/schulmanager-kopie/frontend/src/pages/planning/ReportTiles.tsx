import { useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { planning } from '../../api/endpoints';
import type { ReportDetails, ReportRange } from '../../api/types';
import { AbbrList, TeacherAbbr } from '../../components/Abbr';
import { HelpTip } from '../../components/HelpTip';
import { Empty, ErrorBox, Loading } from '../../components/ui';
import { Modal } from '../../components/Modal';
import { useApi } from '../../hooks/useApi';
import { WEEKDAYS_SHORT } from '../../lib/dates';
import {
  TILE_BY_KEY,
  courseLink,
  formatNumber,
  tileTone,
  tileValue,
  tileVisible,
  timetableLink,
  type ReportDetailKind,
  type TileDef,
} from '../../lib/reportTiles';

/** Kacheln je `detail`-Art (für `initialOpen`). */
const TILES_WITH_DETAIL = new Map<string, TileDef>(Object.values(TILE_BY_KEY).filter((d) => d.detail).map((d) => [d.detail as string, d]));

/** Kennzahlen als Kacheln: Wert, deutscher Titel, Einheit, Erklärung (Hover/Antippen) und Klick auf die Liste dahinter. */
export function ReportTiles({
  keys,
  stats,
  ranges,
  compact,
  initialOpen,
}: {
  keys: string[];
  stats: Record<string, number | string> | undefined;
  ranges?: Record<string, ReportRange>;
  /** Startseite: kürzer, ohne Einheit */
  compact?: boolean;
  /** Liste dieser Kennzahl (`detail`-Art) beim ersten Anzeigen öffnen, z. B. aus dem Tab „Regeln“ */
  initialOpen?: string;
}) {
  const defs = keys.map((k) => TILE_BY_KEY[k]).filter((d): d is TileDef => !!d && tileVisible(d, stats));
  const [open, setOpen] = useState<TileDef | null>(() => (initialOpen ? TILES_WITH_DETAIL.get(initialOpen) ?? null : null));
  return (
    <>
      <div className="stats">
        {defs.map((def) => {
          const v = tileValue(def, stats, ranges);
          const tone = tileTone(def, stats);
          const body = (
            <>
              <span className="kpi-value">{v.value}</span>
              <span className="kpi-label">{def.title}</span>
              {!compact && <span className="kpi-unit">{v.note ? `${def.unit}, ${v.note}` : def.unit}</span>}
            </>
          );
          return (
            <div key={def.key} className={`kpi report-tile${tone ? ` ${tone}` : ''}`}>
              {def.nav ? (
                <Link to={def.nav} className="report-tile-open" aria-label={`${def.title}: ${v.value} – Liste öffnen`}>
                  {body}
                </Link>
              ) : (
                <button type="button" className="report-tile-open" aria-label={`${def.title}: ${v.value} – Liste öffnen`} onClick={() => setOpen(def)}>
                  {body}
                </button>
              )}
              <span className="report-tile-help">
                <HelpTip label={`Erklärung: ${def.title}`}>{def.help}</HelpTip>
              </span>
            </div>
          );
        })}
      </div>
      {open?.detail && <ReportDetailDialog def={open} kind={open.detail} ranges={ranges} onClose={() => setOpen(null)} />}
    </>
  );
}

const day = (d: number) => WEEKDAYS_SHORT[d] ?? String(d);

function Table({ head, children }: { head: ReactNode[]; children: ReactNode }) {
  return (
    <div className="table-wrap" style={{ maxHeight: '55vh' }}>
      <table className="table table-compact">
        <thead>
          <tr>
            {head.map((h, i) => (
              <th key={i} scope="col">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

function ReportDetailDialog({
  def,
  kind,
  ranges,
  onClose,
}: {
  def: TileDef;
  kind: ReportDetailKind;
  ranges?: Record<string, ReportRange>;
  onClose: () => void;
}) {
  const q = useApi((signal) => planning.reportDetails(signal), [], { live: ['timetable', 'courses', 'classes', 'teachers'] });
  const range = ranges?.[def.key];
  return (
    <Modal
      title={
        <>
          {def.title}{' '}
          <HelpTip label={`Erklärung: ${def.title}`}>{`${def.help.replace(/ Klick:.*$/, '')} Nur Ansicht – hier wird nichts am Stundenplan geändert.`}</HelpTip>
        </>
      }
      onClose={onClose}
      size="lg"
    >
      <div className="stack">
        {def.weekly && range && range.min !== range.max && (
          <p className="small" style={{ margin: 0 }}>
            Je nach Woche {formatNumber(range.min)} bis {formatNumber(range.max)} (Durchschnitt {formatNumber(range.avg)}){' '}
            <HelpTip label="Erklärung: Unterschiede je Woche">
              Manche Kurse oder Sperrzeiten gelten nur in bestimmten Wochen, daher unterscheiden sich die Wochen. Die Liste zeigt, in welchen Wochen die Stelle auftritt.
            </HelpTip>
          </p>
        )}
        {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
        {!q.data && !q.error && <Loading />}
        {q.data && q.data.details[kind].length >= 400 && (
          <p className="small muted" style={{ margin: 0 }}>
            Es werden die ersten 400 Einträge angezeigt.
          </p>
        )}
        {q.data && <DetailBody kind={kind} details={q.data.details} onClose={onClose} />}
      </div>
    </Modal>
  );
}

function DetailBody({ kind, details, onClose }: { kind: ReportDetailKind; details: ReportDetails; onClose: () => void }) {
  const close = { onClick: onClose };
  switch (kind) {
    case 'class_gaps':
    case 'teacher_gaps': {
      const rows = details[kind];
      if (!rows.length) return <Empty icon="check" title="Keine Treffer" />;
      const who = kind === 'class_gaps' ? 'Klasse' : 'Lehrkraft';
      return (
        <Table head={[who, 'Tag', 'Stunde', 'Wochen', 'Stundenplan']}>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>
                <AbbrList kind={r.kind} ids={r.id} passive />
              </td>
              <td>{day(r.day)}</td>
              <td>{r.period}. Std.</td>
              <td>{r.weeks_text}</td>
              <td>
                <Link to={timetableLink(r.kind, r.id)} {...close}>
                  öffnen
                </Link>
              </td>
            </tr>
          ))}
        </Table>
      );
    }
    case 'site_changes': {
      const rows = details.site_changes;
      if (!rows.length) return <Empty icon="check" title="Keine Treffer" />;
      return (
        <Table head={['Lehrkraft', 'Tag', 'vor der Stunde', 'Wechsel', 'Wochen', 'Stundenplan']}>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>
                <TeacherAbbr id={r.id} passive />
              </td>
              <td>{day(r.day)}</td>
              <td>{r.period}. Std.</td>
              <td>
                {r.from_site} → {r.to_site}
              </td>
              <td>{r.weeks_text}</td>
              <td>
                <Link to={timetableLink('teacher', r.id)} {...close}>
                  öffnen
                </Link>
              </td>
            </tr>
          ))}
        </Table>
      );
    }
    case 'conflicts': {
      const rows = details.conflicts;
      if (!rows.length) return <Empty icon="check" title="Keine Konflikte" />;
      return (
        <Table head={['Wer / was', 'Tag', 'Stunde', 'Wochen', 'Stundenplan']}>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>
                {r.kind === 'class' ? 'Klasse' : r.kind === 'teacher' ? 'Lehrkraft' : 'Raum'} <strong>{r.id}</strong>
              </td>
              <td>{day(r.day)}</td>
              <td>{r.period}. Std.</td>
              <td>{r.weeks_text}</td>
              <td>
                <Link to={timetableLink(r.kind, r.id)} {...close}>
                  öffnen
                </Link>
              </td>
            </tr>
          ))}
        </Table>
      );
    }
    case 'core_late': {
      const rows = details.core_late;
      if (!rows.length) return <Empty icon="check" title="Keine Treffer" />;
      return (
        <Table head={['Kurs', 'Klassen', 'Tag', 'endet in', 'Stundenplan']}>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>
                <Link to={courseLink(r.course)} {...close}>
                  {r.label}
                </Link>
              </td>
              <td>
                <AbbrList kind="class" ids={r.classes} passive />
              </td>
              <td>{day(r.day)}</td>
              <td>{r.period}. Std.</td>
              <td>
                {r.classes[0] ? (
                  <Link to={timetableLink('class', r.classes[0])} {...close}>
                    öffnen
                  </Link>
                ) : (
                  '–'
                )}
              </td>
            </tr>
          ))}
        </Table>
      );
    }
    case 'unplaced': {
      const rows = details.unplaced;
      if (!rows.length) return <Empty icon="check" title="Alle Stunden sind verplant" />;
      return (
        <Table head={['Kurs', 'Wochen', 'fehlen', 'Grund']}>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>
                <Link to={courseLink(r.course)} {...close}>
                  {r.label || r.course}
                </Link>
              </td>
              <td>{r.weeks_text}</td>
              <td className="num">{r.missing}</td>
              <td>{r.reason ?? '–'}</td>
            </tr>
          ))}
        </Table>
      );
    }
    case 'overplaced': {
      const rows = details.overplaced;
      if (!rows.length) return <Empty icon="check" title="Nichts zu viel verplant" />;
      return (
        <Table head={['Kurs', 'Wochen', 'Soll', 'im Plan', 'zu viel']}>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>
                <Link to={courseLink(r.course)} {...close}>
                  {r.label || r.course}
                </Link>
              </td>
              <td>{r.weeks_text}</td>
              <td className="num">{r.hours}</td>
              <td className="num">{r.placed}</td>
              <td className="num">{r.extra}</td>
            </tr>
          ))}
        </Table>
      );
    }
    case 'teachers': {
      const rows = details.teachers;
      if (!rows.length) return <Empty icon="users" title="Keine Lehrkräfte" />;
      return (
        <Table head={['Lehrkraft', 'Deputat (Soll)', 'Ist (Kursstunden)', 'Differenz', 'Stundenplan']}>
          {rows.map((r) => (
            <tr key={r.id}>
              <td>
                <Link to={`/stammdaten/teachers?lehrkraft=${encodeURIComponent(r.id)}`} {...close}>
                  {r.name}
                </Link>
              </td>
              <td className="num">{r.max_hours}</td>
              <td className="num">{r.load}</td>
              <td className="num">{r.over > 0 ? <strong className="text-danger">+{r.over}</strong> : r.load - r.max_hours}</td>
              <td>
                <Link to={timetableLink('teacher', r.id)} {...close}>
                  öffnen
                </Link>
              </td>
            </tr>
          ))}
        </Table>
      );
    }
    case 'weeks': {
      const rows = details.weeks;
      return (
        <Table head={['Wochenart', 'Schulwochen', 'Hohlstunden Klassen', 'Springstunden Lehrkräfte', 'Standortwechsel']}>
          {rows.map((r, i) => (
            <tr key={i}>
              <td>{r.weeks_text}</td>
              <td className="num">{r.week_count}</td>
              <td className="num">{r.class_gaps}</td>
              <td className="num">{r.teacher_gaps}</td>
              <td className="num">{r.site_changes}</td>
            </tr>
          ))}
        </Table>
      );
    }
  }
}

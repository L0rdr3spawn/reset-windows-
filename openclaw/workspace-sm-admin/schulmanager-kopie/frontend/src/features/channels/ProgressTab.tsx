/**
 * Bereich „Fortschritt“ eines Kursraums.
 *  - Teilnehmende (und Eltern, wenn die Lehrkraft es freigegeben hat): Fortschrittsbalken + Liste der Elemente mit
 *    „Erledigt“-Häkchen bzw. „Verfügbar, sobald …“.
 *  - Lehrende: Tabelle Schüler/in × Elemente mit Filter und CSV-Export.
 */
import { useId, useState } from 'react';
import { errorMessage } from '../../api/client';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Alert, AsyncButton, Empty, ErrorBox, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { channelsApi } from './api';
import {
  cellText,
  csvFileName,
  filterStudents,
  noFilter,
  progressApi,
  toCsv,
  type MyProgress,
  type ProgressTable,
  type TableFilter,
} from './progress';
import type { ChannelDetail } from './types';

/** Balken „x von y erledigt“. */
export function ProgressBar({ done, total, percent, label = 'Fortschritt' }: { done: number; total: number; percent: number; label?: string }) {
  return (
    <div className="kr-progress">
      <div className="kr-progress-text">
        <strong>{label}</strong>
        <span>
          {done} von {total} erledigt ({percent} %)
        </span>
      </div>
      <div className="progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent} aria-label={`${label}: ${percent} Prozent`}>
        <div className="progress-bar" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

/** Balken für den Kopf des Kursraums (nichts, solange keine Abschlussbedingung festgelegt ist). */
export function MyProgressBar({ channelId, studentId }: { channelId: number; studentId?: string | null }) {
  const q = useApi<MyProgress>((signal) => progressApi.mine(channelId, signal, studentId), [channelId, studentId], { live: [`channel:${channelId}:`] });
  if (!q.data || !q.data.enabled) return null;
  return <ProgressBar done={q.data.done} total={q.data.total} percent={q.data.percent} />;
}

function MyProgressView({ detail, reload }: { detail: ChannelDetail; reload: () => void }) {
  const ch = detail.channel;
  const toast = useToast();
  const childId = detail.child?.id ?? null;
  const q = useApi<MyProgress>((signal) => progressApi.mine(ch.id, signal, childId), [ch.id, childId], { live: [`channel:${ch.id}:`] });
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!q.data) return <Loading />;
  const p = q.data;
  if (!p.enabled) return <Empty icon="checkCircle">Die Lehrkraft hat noch keine Aufgaben oder Materialien zum Abhaken festgelegt.</Empty>;
  const toggle = async (id: number, type: string, done: boolean) => {
    try {
      await progressApi.markDone(ch.id, type, id, done);
      q.reload();
      reload();
    } catch (e) {
      toast.error(e);
    }
  };
  return (
    <div className="stack-sm">
      <ProgressBar done={p.done} total={p.total} percent={p.percent} />
      <ul className="kr-list" aria-label="Elemente mit Fortschritt">
        {p.elements.map((el) => (
          <li key={`${el.element_type}:${el.element_id}`} className={`kr-item${el.locked ? ' kr-item-muted' : ''}`}>
            {el.can_toggle ? (
              <input type="checkbox" className="kr-item-check" checked={el.done} onChange={(e) => void toggle(el.element_id, el.element_type, e.target.checked)} aria-label={`${el.title} erledigt`} />
            ) : (
              <span className={`kr-done-mark${el.done ? ' is-done' : ''}`} role="img" aria-label={el.done ? 'erledigt' : el.locked ? 'gesperrt' : 'offen'}>
                <Icon name={el.done ? 'checkCircle' : el.locked ? 'lock' : 'clock'} />
              </span>
            )}
            <div className="kr-item-main">
              <div className="kr-item-title">{el.title}</div>
              <div className="kr-item-meta">
                {el.kind_label} · {el.mode_label}
              </div>
              {el.locked && <div className="kr-locked-text">Verfügbar, sobald {el.locked_text}</div>}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function cellSymbol(v: boolean | null): { icon: string; cls: string } {
  if (v === true) return { icon: 'check', cls: 'is-done' };
  if (v === false) return { icon: 'x', cls: 'is-open' };
  return { icon: 'lock', cls: 'is-na' };
}

function TeacherProgress({ detail, reload }: { detail: ChannelDetail; reload: () => void }) {
  const ch = detail.channel;
  const toast = useToast();
  const ids = { q: useId(), cls: useId(), open: useId(), key: useId() };
  const q = useApi<ProgressTable>((signal) => progressApi.table(ch.id, signal), [ch.id], { live: [`channel:${ch.id}:`] });
  const [filter, setFilter] = useState<TableFilter>(noFilter);
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!q.data) return <Loading />;
  const t = q.data;
  const rows = filterStudents(t.students, filter);
  const parents = ch.settings.progress_parents ?? t.progress_parents;

  const exportCsv = () => {
    const blob = new Blob([toCsv(t, rows)], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = csvFileName(ch.title);
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  const setParents = async (on: boolean) => {
    try {
      await channelsApi.patch(ch.id, { progress_parents: on });
      toast.success(on ? 'Eltern sehen den Fortschritt ihres Kindes' : 'Eltern sehen den Fortschritt nicht mehr');
      reload();
      q.reload();
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  return (
    <div className="stack-sm">
      <div className="row-between kr-progress-head">
        <label className="check">
          <input type="checkbox" checked={!!parents} onChange={(e) => void setParents(e.target.checked)} /> Eltern sehen den Fortschritt ihres Kindes
          <HelpTip>Eltern sehen nur das Häkchen-Ergebnis des eigenen Kindes – nie Abgaben, Noten oder andere Schüler/innen. Volljährige Kinder entscheiden selbst, ob Eltern Kursräume sehen.</HelpTip>
        </label>
        <button type="button" className="btn btn-sm" onClick={exportCsv} disabled={!t.elements.length || !rows.length}>
          <Icon name="download" /> CSV exportieren
        </button>
      </div>

      {!t.elements.length ? (
        <Empty icon="checkCircle" title="Noch keine Abschlussbedingungen">
          Im Reiter „Material“ oder „Hausaufgaben“ bei einem Element auf „Abschluss &amp; Bedingungen“ klicken und festlegen, wann es als erledigt gilt.
        </Empty>
      ) : (
        <>
          <div className="kr-filter" role="search" aria-label="Fortschritt filtern">
            <div className="field">
              <label htmlFor={ids.q}>Name</label>
              <input id={ids.q} type="search" value={filter.q} onChange={(e) => setFilter({ ...filter, q: e.target.value })} placeholder="Suchen …" />
            </div>
            {t.classes.length > 1 && (
              <div className="field">
                <label htmlFor={ids.cls}>Klasse</label>
                <select id={ids.cls} value={filter.classId} onChange={(e) => setFilter({ ...filter, classId: e.target.value })}>
                  <option value="">Alle</option>
                  {t.classes.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div className="field">
              <label htmlFor={ids.key}>Offen bei</label>
              <select id={ids.key} value={filter.openKey} onChange={(e) => setFilter({ ...filter, openKey: e.target.value })}>
                <option value="">egal</option>
                {t.elements.map((e) => (
                  <option key={e.key} value={e.key}>
                    {e.title}
                  </option>
                ))}
              </select>
            </div>
            <label className="check kr-filter-check" htmlFor={ids.open}>
              <input id={ids.open} type="checkbox" checked={filter.onlyOpen} onChange={(e) => setFilter({ ...filter, onlyOpen: e.target.checked })} /> Nur mit offenen Elementen
            </label>
          </div>
          <p className="small muted" role="status">
            {rows.length} von {t.students.length} Schüler/innen
          </p>
          <div className="table-wrap kr-progress-table">
            <table className="table table-compact">
              <caption className="sr-only">Fortschritt der Schüler/innen je Element</caption>
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  {t.elements.map((e) => (
                    <th key={e.key} scope="col" className="kr-progress-col" title={`${e.title} – ${e.mode_label}`}>
                      <span className="kr-progress-colname">{e.title}</span>
                      <span className="xsmall muted">{e.mode_label}</span>
                    </th>
                  ))}
                  <th scope="col">Gesamt</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((s) => (
                  <tr key={`${s.user_id ?? s.student_id ?? s.name}`}>
                    <th scope="row">
                      {s.name}
                      {s.class_id && <span className="xsmall muted"> {s.class_id}</span>}
                      {!s.has_account && <span className="xsmall muted"> (kein Konto)</span>}
                    </th>
                    {t.elements.map((e) => {
                      const v = s.cells[e.key] ?? null;
                      const sym = cellSymbol(v);
                      return (
                        <td key={e.key} className={`kr-progress-cell ${sym.cls}`}>
                          <Icon name={sym.icon} />
                          <span className="sr-only">{cellText(v) || 'nicht einsehbar'}</span>
                        </td>
                      );
                    })}
                    <td>
                      <strong>{s.percent} %</strong> <span className="xsmall muted">({s.done}/{s.total})</span>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <th scope="row">Erledigt</th>
                  {t.elements.map((e) => (
                    <td key={e.key} className="xsmall">
                      {e.restricted ? '–' : `${e.done}/${e.of}`}
                    </td>
                  ))}
                  <td />
                </tr>
              </tfoot>
            </table>
          </div>
          {t.elements.some((e) => e.restricted) && (
            <Alert kind="info">Mit Schloss markiert: Abgaben anderer Lehrkräfte, nicht einsehbar.</Alert>
          )}
        </>
      )}
      <div className="row">
        <AsyncButton className="btn btn-sm btn-ghost" onClick={async () => q.reload()}>
          <Icon name="refresh" /> Aktualisieren
        </AsyncButton>
      </div>
    </div>
  );
}

export default function ProgressTab({ detail, reload }: { detail: ChannelDetail; reload: () => void }) {
  return detail.permissions.manage ? <TeacherProgress detail={detail} reload={reload} /> : <MyProgressView detail={detail} reload={reload} />;
}

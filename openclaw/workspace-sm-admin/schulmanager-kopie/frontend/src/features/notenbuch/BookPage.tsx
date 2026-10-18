/**
 * `/notenbuch/:bookId` – Notentabelle eines Kursteils: Schüler/in × Leistungen, schnelles Eintragen (Tastatur am PC,
 * Antippen am Handy), Schnitte je Leistungsart und gesamt, Vorschlagsnote, festgelegte Endnote mit Kennzeichnung
 * „überschrieben“, Sperren, Übernahme aus anderen Bereichen, Änderungsprotokoll.
 */
import { useCallback, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Abbr } from '../../components/Abbr';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { AsyncButton, Empty, ErrorBox, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useTitle, useMediaQuery } from '../../hooks/misc';
import { useApi } from '../../hooks/useApi';
import { formatDate } from '../../lib/dates';
import { gbApi } from './api';
import { BookSettingsDialog, CategoriesDialog, EntryDialog, ItemDialog, LogDialog, SourcesDialog, StudentDialog } from './dialogs';
import { cellText, fmtNum, fmtWeight, gradeTone, moveTarget, orderedColumns, parseQuick, shortDate, STATUS_NAMES, topCategories } from './logic';
import type { Entry, EntryPatch, Item, Meta, ScaleKind, StudentRow, Table } from './types';
import './notenbuch.css';

/** Antwort einer Änderung einarbeiten: Kopf, Arten, Leistungen komplett; Zeilen nur die gelieferten. */
export function mergeTable(prev: Table | undefined, next: Table, partial = false): Table {
  if (!prev || !partial) return next;
  const byId = new Map(next.students.map((s) => [s.student_id, s]));
  return { ...next, students: prev.students.map((s) => byId.get(s.student_id) ?? s) };
}

export default function BookPage() {
  const { bookId } = useParams();
  const id = Number(bookId);
  const toast = useToast();
  const coarse = useMediaQuery('(pointer: coarse)');
  const meta = useApi((signal) => gbApi.meta(signal), []);
  const q = useApi((signal) => gbApi.book(id, signal), [id], { live: ['gradebook'] });
  const t = q.data;
  useTitle(t ? `Notenbuch ${t.book.title}` : 'Notenbuch');
  const [itemDlg, setItemDlg] = useState<Item | 'new' | null>(null);
  const [dlg, setDlg] = useState<'cats' | 'settings' | 'sources' | 'log' | null>(null);
  const [entryDlg, setEntryDlg] = useState<{ sid: string; item: number } | null>(null);
  const [personDlg, setPersonDlg] = useState<string | null>(null);
  const [allCats, setAllCats] = useState(false);

  const apply = useCallback((next: Table, partial = false) => q.setData((prev) => mergeTable(prev, next, partial)), [q]);
  const applyFull = useCallback((next: Table) => apply(next), [apply]);

  const saveEntry = useCallback(
    async (itemId: number, patch: EntryPatch) => {
      try {
        const r = await gbApi.entries(itemId, [patch]);
        apply(r, true);
      } catch (e) {
        toast.error(e);
        q.reload();
      }
    },
    [apply, q, toast],
  );
  const saveFinal = useCallback(
    async (sid: string, value: string | undefined, note: string | undefined) => {
      if (!t) return;
      try {
        const r = await gbApi.finals(t.book.id, [{ student_id: sid, value, note }]);
        apply(r, true);
      } catch (e) {
        toast.error(e);
        q.reload();
      }
    },
    [t, apply, q, toast],
  );

  if (q.error && !t) return <div className="page"><ErrorBox error={q.error} onRetry={q.reload} /></div>;
  if (!t || !meta.data) return <div className="page"><Loading /></div>;
  const book = t.book;
  const scale = book.scale;
  const cols = orderedColumns(t.categories, t.items);
  const tops = allCats ? t.categories : topCategories(t.categories);
  const dec = book.decimals;
  const edit = book.can_edit;
  const numeric = !!scale?.numeric;
  const rowsCount = t.students.length;
  const focusCell = (r: number, c: number) => document.querySelector<HTMLInputElement>(`[data-gb="${r}:${c}"]`)?.focus();
  const personRow = personDlg ? t.students.find((s) => s.student_id === personDlg) : undefined;
  const entryTarget = entryDlg ? { row: t.students.find((s) => s.student_id === entryDlg.sid), item: t.items.find((i) => i.id === entryDlg.item) } : null;

  return (
    <div className="page stack">
      <div className="page-head">
        <div>
          <p className="small muted">
            <Link to="/notenbuch">Notenbücher</Link> · {book.term_label}
          </p>
          <h1>{book.title}</h1>
        </div>
        <div className="gbk-chips">
          <span className="badge">{scale?.name}</span>
          {book.locked ? (
            <span className="badge badge-danger">
              <Icon name="lock" /> gesperrt{book.locked_by ? ` von ${book.locked_by}` : ''}
            </span>
          ) : book.access === 'read' ? (
            <span className="badge badge-info">nur lesen</span>
          ) : null}
        </div>
      </div>

      <div className="gbk-bar">
        {edit && (
          <button type="button" className="btn btn-primary" onClick={() => setItemDlg('new')}>
            <Icon name="plus" /> Leistung
          </button>
        )}
        {book.access && (
          <button type="button" className="btn" onClick={() => setDlg('cats')}>
            Leistungsarten
          </button>
        )}
        {edit && (
          <button type="button" className="btn" onClick={() => setDlg('sources')}>
            Übernehmen{t.pending_sources ? ` (${t.pending_sources})` : ''}
          </button>
        )}
        {edit && (
          <button type="button" className="btn" onClick={() => setDlg('settings')}>
            <Icon name="cog" /> Einstellungen
          </button>
        )}
        <button type="button" className="btn" onClick={() => setDlg('log')}>
          <Icon name="history" /> Protokoll
        </button>
        <span className="grow" />
        {edit && numeric && (
          <AsyncButton
            className="btn"
            onClick={async () => {
              const r = await gbApi.applyProposals(book.id);
              apply(r);
              toast.success(r.changed ? `${r.changed} Vorschläge als Note festgelegt` : 'Nichts zu übernehmen');
            }}
          >
            Vorschläge übernehmen
          </AsyncButton>
        )}
        {book.can_lock && (
          <AsyncButton
            className="btn btn-danger"
            confirm="Halbjahresnoten sperren? Danach lässt sich nichts mehr ändern; nur die Schulleitung kann das Notenbuch wieder öffnen."
            onClick={async () => {
              const r = await gbApi.lock(book.id);
              apply(r);
              toast[r.missing_finals ? 'warning' : 'success'](r.missing_finals ? `Gesperrt – bei ${r.missing_finals} Schüler/innen fehlt noch die festgelegte Note` : 'Notenbuch gesperrt');
            }}
          >
            <Icon name="lock" /> Sperren
          </AsyncButton>
        )}
        {book.can_unlock && (
          <AsyncButton
            className="btn"
            onClick={async () => {
              apply(await gbApi.unlock(book.id));
              toast.success('Notenbuch geöffnet');
            }}
          >
            <Icon name="unlock" /> Wieder öffnen
          </AsyncButton>
        )}
      </div>

      {t.items.length === 0 && edit && <Empty icon="list" action={<button type="button" className="btn btn-primary" onClick={() => setItemDlg('new')}>Erste Leistung anlegen</button>}>Noch keine Leistung im Notenbuch.</Empty>}

      {t.students.length === 0 ? (
        <Empty icon="users">Dem Kurs sind keine Schüler/innen zugeordnet.</Empty>
      ) : (
        <div className="gbk-scroll" role="region" aria-label="Notentabelle" tabIndex={0}>
          <table className="gbk-table">
            <thead>
              <tr>
                <th className="gbk-name" scope="col">
                  Schüler/in
                  {cols.length > 0 && !coarse && (
                    <HelpTip label="Tastatur">
                      Note eintippen und mit Enter zur nächsten Zeile. Kürzel: e = entschuldigt, a = ausgelassen, n = Nachschreiben, u = unentschuldigt
                      gefehlt, „-“ löscht. F2 öffnet Bemerkung und Einzelheiten.
                    </HelpTip>
                  )}
                </th>
                {cols.map(({ item, path }) => (
                  <th key={item.id} scope="col">
                    <button type="button" className="gbk-head-btn" onClick={() => setItemDlg(item)} aria-label={`Leistung ${item.title} bearbeiten`}>
                      <span className="gbk-head-title">{item.title}</span>
                      <span className="gbk-head-meta">
                        {[shortDate(item.date), item.weight !== 1 ? `×${fmtWeight(item.weight)}` : '', item.max_points ? `/${fmtWeight(item.max_points)}` : ''].filter(Boolean).join(' · ')}
                      </span>
                      {path && <span className="gbk-group">{path}</span>}
                      {item.released && (
                        <span className="gbk-head-meta" title="Für Schüler/innen freigegeben">
                          <Icon name="eye" /> frei
                        </span>
                      )}
                      {item.source_label && <span className="gbk-head-meta">{item.source_label}</span>}
                    </button>
                  </th>
                ))}
                {numeric &&
                  tops.map((c) => (
                    <th key={`c${c.id}`} scope="col" className="gbk-avg">
                      Ø {c.name}
                      <span className="gbk-head-meta"> {fmtWeight(c.weight)}</span>
                    </th>
                  ))}
                {numeric && (
                  <th scope="col" className="gbk-avg">
                    Ø gesamt
                    {t.categories.length > tops.length || allCats ? (
                      <button type="button" className="btn btn-ghost btn-sm" aria-pressed={allCats} onClick={() => setAllCats(!allCats)} title="Auch Unterarten zeigen">
                        {allCats ? '−' : '+'}
                      </button>
                    ) : null}
                  </th>
                )}
                {numeric && <th scope="col">Vorschlag</th>}
                <th scope="col">Endnote</th>
              </tr>
            </thead>
            <tbody>
              {t.students.map((row, r) => (
                <tr key={row.student_id}>
                  <th scope="row" className="gbk-name">
                    <button type="button" className="gbk-name-btn" onClick={() => setPersonDlg(row.student_id)}>
                      {row.name}
                    </button>{' '}
                    {row.support && <Abbr text={<span className="gbk-flag">NTA</span>} full="Nachteilsausgleich – Einzelheiten unter Schülerdaten" />}
                    <span className="xsmall muted"> {row.class_id}</span>
                  </th>
                  {cols.map(({ item }, c) => (
                    <td key={item.id} className={`gbk-cell ${toneClass(row.entries[String(item.id)], item, scale?.kind)}`}>
                      <GradeCell
                        entry={row.entries[String(item.id)]}
                        item={item}
                        label={`${row.name}, ${item.title}`}
                        pos={`${r}:${c}`}
                        editable={edit}
                        coarse={coarse}
                        kind={scale?.kind}
                        onCommit={(p) => saveEntry(item.id, { student_id: row.student_id, ...p })}
                        onOpen={() => setEntryDlg({ sid: row.student_id, item: item.id })}
                        onMove={(key, shift) => {
                          const [nr, nc] = moveTarget(r, c, key, rowsCount, shift);
                          focusCell(nr, nc);
                        }}
                      />
                    </td>
                  ))}
                  {numeric &&
                    tops.map((c) => (
                      <td key={`c${c.id}`} className="gbk-avg">
                        {fmtNum(row.categories[String(c.id)], dec)}
                      </td>
                    ))}
                  {numeric && <td className="gbk-avg gbk-avg-strong">{fmtNum(row.average, dec)}</td>}
                  {numeric && <td className="gbk-avg-strong">{row.proposal || '–'}</td>}
                  <td className="gbk-final">
                    <FinalCell row={row} editable={edit} numeric={numeric} onSave={(v) => saveFinal(row.student_id, v, undefined)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {itemDlg && meta.data && <ItemDialog table={t} meta={meta.data as Meta} item={itemDlg === 'new' ? null : itemDlg} onClose={() => setItemDlg(null)} onApply={applyFull} />}
      {dlg === 'cats' && <CategoriesDialog table={t} onClose={() => setDlg(null)} onApply={applyFull} />}
      {dlg === 'settings' && meta.data && <BookSettingsDialog table={t} meta={meta.data} onClose={() => setDlg(null)} onApply={applyFull} />}
      {dlg === 'sources' && <SourcesDialog table={t} onClose={() => setDlg(null)} onApply={applyFull} />}
      {dlg === 'log' && <LogDialog book={book} onClose={() => setDlg(null)} />}
      {entryTarget?.row && entryTarget.item && (
        <EntryDialog
          table={t}
          row={entryTarget.row}
          item={entryTarget.item}
          entry={entryTarget.row.entries[String(entryTarget.item.id)]}
          onClose={() => setEntryDlg(null)}
          onSave={(p) => saveEntry(entryTarget.item?.id ?? 0, p)}
        />
      )}
      {personRow && <StudentDialog table={t} row={personRow} onClose={() => setPersonDlg(null)} onSaveFinal={(v, n) => saveFinal(personRow.student_id, v, n)} />}
      {book.locked_at && <p className="xsmall muted">Gesperrt am {formatDate(book.locked_at.slice(0, 10))}.</p>}
    </div>
  );
}

function toneClass(e: Entry | undefined, item: Item, kind: ScaleKind | undefined): string {
  if (!e || e.status) return '';
  const label = item.max_points ? e.label : e.value;
  const tone = gradeTone(label, kind ?? 'note6');
  return tone === 'none' ? '' : `gbk-tone-${tone}`;
}

/** Eine Zelle der Notentabelle: am PC ein Eingabefeld, am Handy (grober Zeiger) ein Antippfeld mit Dialog. */
function GradeCell({
  entry,
  item,
  label,
  pos,
  editable,
  coarse,
  kind,
  onCommit,
  onOpen,
  onMove,
}: {
  entry: Entry | undefined;
  item: Item;
  label: string;
  pos: string;
  editable: boolean;
  coarse: boolean;
  kind: ScaleKind | undefined;
  onCommit: (p: { value: string; status: Entry['status'] }) => void;
  onOpen: () => void;
  onMove: (key: string, shift: boolean) => void;
}) {
  const shown = cellText(entry);
  const [text, setText] = useState(shown);
  const [focused, setFocused] = useState(false);
  const sent = useRef(shown);
  if (!focused) {
    if (text !== shown) setText(shown);
    sent.current = shown;
  }
  const commit = () => {
    if (text.trim() === sent.current.trim()) return;   // Enter und anschließendes Verlassen speichern nur einmal
    sent.current = text.trim();
    onCommit(parseQuick(text, kind));
  };
  const title = entry?.status ? STATUS_NAMES[entry.status] : entry?.invalid ? 'Ungültige Eingabe für diese Skala' : entry?.note || undefined;
  return (
    <>
      <input
        className={`gbk-input${entry?.status ? ' gbk-status' : ''}`}
        data-gb={pos}
        aria-label={label}
        aria-invalid={entry?.invalid ? true : undefined}
        title={title}
        value={text}
        readOnly={coarse || !editable}
        disabled={!editable && !entry}
        inputMode={kind === 'verbal' || kind === 'custom' ? 'text' : 'decimal'}
        autoComplete="off"
        maxLength={40}
        onFocus={(e) => {
          setFocused(true);
          if (!coarse) e.currentTarget.select();
        }}
        onBlur={() => {
          setFocused(false);
          if (editable && !coarse) commit();
        }}
        onClick={() => {
          if (coarse) onOpen();
        }}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            e.preventDefault();
            if (editable) commit();
            onMove(e.key, e.shiftKey);
          } else if (e.key === 'F2' || (e.key === 'Enter' && e.altKey)) {
            e.preventDefault();
            onOpen();
          } else if (e.key === 'Escape') {
            setText(shown);
          }
        }}
      />
      {item.max_points && entry?.label && !entry.status ? <span className="gbk-sub">{entry.label}</span> : null}
      {entry?.status === 'nachschreiben' && (entry.makeup_date || item.makeup_date) ? <span className="gbk-sub">{shortDate(entry.makeup_date || item.makeup_date)}</span> : null}
      {entry?.note ? <span className="gbk-sub" aria-hidden="true">✎</span> : null}
    </>
  );
}

function FinalCell({ row, editable, numeric, onSave }: { row: StudentRow; editable: boolean; numeric: boolean; onSave: (v: string) => void }) {
  const [text, setText] = useState(row.final);
  const [focused, setFocused] = useState(false);
  const sent = useRef(row.final);
  if (!focused) {
    if (text !== row.final) setText(row.final);
    sent.current = row.final;
  }
  const commit = () => {
    if (text.trim() === sent.current.trim()) return;
    sent.current = text.trim();
    onSave(text.trim());
  };
  return (
    <div className="gbk-final-row">
      <input
        className="gbk-input"
        aria-label={`Endnote ${row.name}`}
        value={text}
        placeholder={row.proposal}
        readOnly={!editable}
        maxLength={500}
        onFocus={() => setFocused(true)}
        onBlur={() => {
          setFocused(false);
          if (editable) commit();
        }}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') e.currentTarget.blur();
        }}
      />
      {editable && numeric && row.proposal && row.final !== row.proposal && (
        <button type="button" className="btn btn-ghost btn-sm" title={`Vorschlag ${row.proposal} übernehmen`} aria-label={`Vorschlag ${row.proposal} für ${row.name} übernehmen`} onClick={() => onSave(row.proposal)}>
          <Icon name="undo" />
        </button>
      )}
      {row.overridden && (
        <span className="badge badge-warning" title={`Weicht vom Vorschlag ${row.proposal} ab`}>
          überschrieben
        </span>
      )}
    </div>
  );
}

/** Dialoge des Notenbuchs: Leistung, Leistungsarten, Einstellungen, Übernahme, Protokoll, Einzelwert, Person. */
import { useEffect, useState } from 'react';
import { Modal } from '../../components/Modal';
import { AsyncButton, Empty, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { formatDate } from '../../lib/dates';
import { gbApi } from './api';
import { categoryOptions, fmtNum, fmtWeight, parseDecimal, quickLabels, STATUS_NAMES, termText, weightShare } from './logic';
import type { BookInfo, Category, Entry, EntryPatch, EntryStatus, GradeKey, Item, Meta, StudentRow, Table } from './types';

type Apply = (t: Table) => void;

const STATUS_ORDER: EntryStatus[] = ['', 'entschuldigt', 'ausgelassen', 'nachschreiben', 'unentschuldigt'];

/* ------------------------------------------------------------------------------------------------ Leistung */
export function ItemDialog({ table, item, meta, onClose, onApply }: { table: Table; item: Item | null; meta: Meta; onClose: () => void; onApply: Apply }) {
  const book = table.book;
  const toast = useToast();
  const [title, setTitle] = useState(item?.title ?? '');
  const [category, setCategory] = useState<string>(item?.category_id ? String(item.category_id) : '');
  const [date, setDate] = useState(item?.date ?? '');
  const [weight, setWeight] = useState(fmtWeight(item?.weight ?? 1));
  const [points, setPoints] = useState(item?.max_points ? fmtWeight(item.max_points) : '');
  const [keyId, setKeyId] = useState(item?.key_id ?? '');
  const [makeup, setMakeup] = useState(item?.makeup_date ?? '');
  const [released, setReleased] = useState(item?.released ?? false);
  const keys = meta.keys.filter((k) => k.scale_id === book.scale_id);
  const usesPoints = points.trim() !== '';
  const save = async () => {
    const w = parseDecimal(weight);
    const p = parseDecimal(points);
    if (!title.trim()) throw new Error('Bitte einen Titel eingeben');
    if (w === null || w < 0) throw new Error('Das Gewicht muss eine Zahl ab 0 sein');
    if (usesPoints && (p === null || p <= 0)) throw new Error('Die Höchstpunktzahl muss größer als 0 sein');
    const body: Record<string, unknown> = { title: title.trim(), date, weight: w, key_id: keyId, makeup_date: makeup };
    if (item) {
      body.released = released;
      if (usesPoints) body.max_points = p;
      else body.clear_points = true;
      if (category) body.category_id = Number(category);
      else body.clear_category = true;
      onApply(await gbApi.patchItem(item.id, body));
    } else {
      body.category_id = category ? Number(category) : null;
      body.max_points = usesPoints ? p : null;
      onApply(await gbApi.addItem(book.id, body));
    }
    onClose();
  };
  return (
    <Modal
      title={item ? 'Leistung bearbeiten' : 'Leistung hinzufügen'}
      onClose={onClose}
      footer={
        <>
          {item && !book.locked && (
            <AsyncButton
              className="btn btn-danger"
              confirm={`Leistung „${item.title}“ mit allen Noten entfernen?`}
              onClick={async () => {
                onApply(await gbApi.deleteItem(item.id));
                toast.success('Leistung entfernt');
                onClose();
              }}
            >
              Entfernen
            </AsyncButton>
          )}
          <span className="grow" />
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton
            className="btn btn-primary"
            onClick={async () => {
              try {
                await save();
              } catch (e) {
                toast.error(e);
              }
            }}
          >
            Speichern
          </AsyncButton>
        </>
      }
    >
      <div className="stack">
        <Field label="Titel" htmlFor="gbk-i-title">
          <input id="gbk-i-title" value={title} maxLength={120} onChange={(e) => setTitle(e.target.value)} />
        </Field>
        <div className="grid grid-2">
          <Field label="Leistungsart" htmlFor="gbk-i-cat" help="Bestimmt, wie stark die Leistung zählt: Die Gewichte der Leistungsarten legen Sie unter „Leistungsarten“ fest.">
            <select id="gbk-i-cat" value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">(keine – zählt direkt)</option>
              {categoryOptions(table.categories).map((o) => (
                <option key={o.id} value={o.id}>
                  {o.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Datum" htmlFor="gbk-i-date">
            <input id="gbk-i-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </Field>
          <Field label="Gewicht in der Leistungsart" htmlFor="gbk-i-weight" help="Eine Klausur mit Gewicht 2 zählt doppelt so stark wie ein Test mit Gewicht 1. Gewicht 0 nimmt die Leistung aus der Rechnung.">
            <input id="gbk-i-weight" inputMode="decimal" value={weight} onChange={(e) => setWeight(e.target.value)} />
          </Field>
          <Field label="Höchstpunktzahl" htmlFor="gbk-i-points" help="Leer lassen, wenn Sie direkt Noten eintragen. Mit Punktzahl tragen Sie erreichte Punkte ein; die Note ergibt sich aus dem Notenschlüssel.">
            <input id="gbk-i-points" inputMode="decimal" value={points} placeholder="leer = Note" onChange={(e) => setPoints(e.target.value)} />
          </Field>
        </div>
        {usesPoints && (
          <Field label="Notenschlüssel" htmlFor="gbk-i-key" help="Prozentgrenzen, nach denen Punkte in Noten umgerechnet werden. Leer = Standard des Notenbuchs bzw. der Schule.">
            <select id="gbk-i-key" value={keyId} onChange={(e) => setKeyId(e.target.value)}>
              <option value="">Standard</option>
              {keys.map((k) => (
                <option key={k.id} value={k.id}>
                  {k.name}
                </option>
              ))}
            </select>
          </Field>
        )}
        <Field label="Nachschreibtermin" htmlFor="gbk-i-makeup" help="Wird bei Schüler/innen mit dem Status „Nachschreiben“ angezeigt.">
          <input id="gbk-i-makeup" type="date" value={makeup} onChange={(e) => setMakeup(e.target.value)} />
        </Field>
        {item && (
          <label className="check">
            <input type="checkbox" checked={released} onChange={(e) => setReleased(e.target.checked)} /> Für Schüler/innen freigegeben
          </label>
        )}
      </div>
    </Modal>
  );
}

/* ------------------------------------------------------------------------------------------ Leistungsarten */
export function CategoriesDialog({ table, onClose, onApply }: { table: Table; onClose: () => void; onApply: Apply }) {
  const toast = useToast();
  const [name, setName] = useState('');
  const [weight, setWeight] = useState('1');
  const [parent, setParent] = useState('');
  const share = weightShare(table.categories);
  const run = async (fn: () => Promise<Table>) => {
    try {
      onApply(await fn());
    } catch (e) {
      toast.error(e);
    }
  };
  return (
    <Modal title="Leistungsarten und Gewichtung" onClose={onClose} size="lg" footer={<button type="button" className="btn btn-primary" onClick={onClose}>Fertig</button>}>
      <div className="stack">
        {table.categories.length === 0 && <Empty icon="list">Noch keine Leistungsart.</Empty>}
        <div>
          {table.categories.map((c) => (
            <CategoryRow key={`${c.id}-${c.name}-${c.weight}`} cat={c} share={share[c.id] ?? 0} locked={table.book.locked} table={table} run={run} />
          ))}
        </div>
        {!table.book.locked && (
          <fieldset className="stack-sm">
            <legend>Leistungsart hinzufügen</legend>
            <div className="gbk-cat-row">
              <input aria-label="Name" value={name} placeholder="z. B. Referate" maxLength={120} onChange={(e) => setName(e.target.value)} />
              <input aria-label="Gewicht" inputMode="decimal" value={weight} onChange={(e) => setWeight(e.target.value)} />
              <AsyncButton
                className="btn btn-primary btn-sm"
                disabled={!name.trim()}
                onClick={() =>
                  run(async () => {
                    const t = await gbApi.addCategory(table.book.id, { name: name.trim(), weight: parseDecimal(weight) ?? 1, parent_id: parent ? Number(parent) : null });
                    setName('');
                    return t;
                  })
                }
              >
                Hinzufügen
              </AsyncButton>
            </div>
            <Field label="Unterhalb von" htmlFor="gbk-c-parent">
              <select id="gbk-c-parent" value={parent} onChange={(e) => setParent(e.target.value)}>
                <option value="">(oberste Ebene)</option>
                {categoryOptions(table.categories)
                  .filter((o) => (table.categories.find((c) => c.id === o.id)?.depth ?? 0) < 3)
                  .map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.label}
                    </option>
                  ))}
              </select>
            </Field>
          </fieldset>
        )}
      </div>
    </Modal>
  );
}

function CategoryRow({ cat, share, locked, table, run }: { cat: Category; share: number; locked: boolean; table: Table; run: (fn: () => Promise<Table>) => Promise<void> }) {
  const [name, setName] = useState(cat.name);
  const [weight, setWeight] = useState(fmtWeight(cat.weight));
  const used = table.items.some((i) => i.category_id === cat.id) || table.categories.some((c) => c.parent_id === cat.id);
  const commit = () => {
    const w = parseDecimal(weight);
    if (name.trim() === cat.name && w === cat.weight) return;
    if (!name.trim() || w === null || w < 0) return;
    void run(() => gbApi.patchCategory(cat.id, { name: name.trim(), weight: w }));
  };
  return (
    <div className="gbk-cat-row">
      <div className={`gbk-ind-${Math.min(cat.depth, 3)}`}>
        <input aria-label={`Name ${cat.name}`} value={name} disabled={locked} maxLength={120} onChange={(e) => setName(e.target.value)} onBlur={commit} />
      </div>
      <div>
        <input aria-label={`Gewicht ${cat.name}`} inputMode="decimal" value={weight} disabled={locked} onChange={(e) => setWeight(e.target.value)} onBlur={commit} />
        <span className="xsmall muted"> {share} %</span>
      </div>
      <button
        type="button"
        className="btn btn-sm btn-ghost"
        disabled={locked || used}
        title={used ? 'Erst Leistungen und Unterarten entfernen oder verschieben' : 'Leistungsart entfernen'}
        onClick={() => void run(() => gbApi.deleteCategory(cat.id))}
      >
        Entfernen
      </button>
    </div>
  );
}

/* ---------------------------------------------------------------------------------------------- Einstellungen */
export function BookSettingsDialog({ table, meta, onClose, onApply }: { table: Table; meta: Meta; onClose: () => void; onApply: Apply }) {
  const book = table.book;
  const toast = useToast();
  const [scale, setScale] = useState(book.scale_id);
  const [keyId, setKeyId] = useState(book.key_id);
  const [rounding, setRounding] = useState<string>(book.rounding);
  const [decimals, setDecimals] = useState(String(book.decimals));
  const keys: GradeKey[] = meta.keys.filter((k) => k.scale_id === scale);
  return (
    <Modal
      title="Notenbuch einstellen"
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton
            className="btn btn-primary"
            onClick={async () => {
              try {
                const body: Record<string, unknown> = { key_id: scale === book.scale_id ? keyId : '', rounding, decimals: Number(decimals) };
                if (scale !== book.scale_id) body.scale_id = scale;
                onApply(await gbApi.patchBook(book.id, body));
                onClose();
              } catch (e) {
                toast.error(e);
              }
            }}
          >
            Speichern
          </AsyncButton>
        </>
      }
    >
      <div className="stack">
        <Field label="Notenskala" htmlFor="gbk-s-scale" help="Die Skala lässt sich nur ändern, solange noch keine Noten eingetragen sind.">
          <select id="gbk-s-scale" value={scale} onChange={(e) => setScale(e.target.value)}>
            {meta.scales.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </Field>
        {keys.length > 0 && (
          <Field label="Notenschlüssel" htmlFor="gbk-s-key" help="Rechnet erreichte Punkte über Prozentgrenzen in Noten um. Leer = Standard der Schule.">
            <select id="gbk-s-key" value={scale === book.scale_id ? keyId : ''} onChange={(e) => setKeyId(e.target.value)}>
              <option value="">Standard der Schule</option>
              {keys.map((k) => (
                <option key={k.id} value={k.id}>
                  {k.name}
                </option>
              ))}
            </select>
          </Field>
        )}
        <div className="grid grid-2">
          <Field label="Vorschlagsnote runden" htmlFor="gbk-s-round" help="„Ganze Note“ rundet den Schnitt auf 1 bis 6; „mit Tendenz“ schlägt auch 2+ oder 3- vor. Ab 0,5 wird aufgerundet.">
            <select id="gbk-s-round" value={rounding} onChange={(e) => setRounding(e.target.value)}>
              <option value="ganz">Ganze Note</option>
              <option value="tendenz">Mit Tendenz</option>
            </select>
          </Field>
          <Field label="Nachkommastellen im Schnitt" htmlFor="gbk-s-dec">
            <select id="gbk-s-dec" value={decimals} onChange={(e) => setDecimals(e.target.value)}>
              {[0, 1, 2, 3].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </Field>
        </div>
      </div>
    </Modal>
  );
}

/* ---------------------------------------------------------------------------------------------- Übernehmen */
export function SourcesDialog({ table, onClose, onApply }: { table: Table; onClose: () => void; onApply: Apply }) {
  const book = table.book;
  const toast = useToast();
  const q = useApi((signal) => gbApi.sources(book.id, signal), [book.id, table.items.length]);
  const [cat, setCat] = useState<Record<string, string>>({});
  const run = async (fn: () => Promise<Table>) => {
    try {
      onApply(await fn());
      q.reload();
    } catch (e) {
      toast.error(e);
    }
  };
  return (
    <Modal title="Ergebnisse übernehmen" onClose={onClose} size="lg" footer={<button type="button" className="btn btn-primary" onClick={onClose}>Fertig</button>}>
      <div className="stack">
        {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
        {!q.data && q.loading && <Loading />}
        {q.data && q.data.sources.length === 0 && <Empty icon="exam">Keine Ergebnisse aus Klausuren, Aufgaben oder Selbsttests für diesen Kurs.</Empty>}
        <ul className="gbk-list">
          {q.data?.sources.map((s) => {
            const key = `${s.source_type}:${s.source_id}`;
            return (
              <li key={key}>
                <div className="gbk-li-main">
                  <strong>{s.title || s.source_label}</strong>{' '}
                  <span className="badge">{s.source_label}</span>
                  <div className="small muted">
                    {s.date ? `${formatDate(s.date)} · ` : ''}
                    {s.count} Ergebnisse{s.max_points ? ` · max. ${fmtWeight(s.max_points)} Punkte` : ''}
                  </div>
                </div>
                {s.state === 'open' && (
                  <div className="gbk-bar">
                    <select aria-label="Leistungsart" value={cat[key] ?? ''} onChange={(e) => setCat({ ...cat, [key]: e.target.value })}>
                      <option value="">(keine Leistungsart)</option>
                      {categoryOptions(table.categories).map((o) => (
                        <option key={o.id} value={o.id}>
                          {o.label}
                        </option>
                      ))}
                    </select>
                    <AsyncButton className="btn btn-primary btn-sm" disabled={book.locked} onClick={() => run(() => gbApi.adopt(book.id, { source_type: s.source_type, source_id: s.source_id, category_id: cat[key] ? Number(cat[key]) : null }))}>
                      Übernehmen
                    </AsyncButton>
                    <AsyncButton className="btn btn-sm" disabled={book.locked} onClick={() => run(() => gbApi.dismiss(book.id, { source_type: s.source_type, source_id: s.source_id }))}>
                      Abwählen
                    </AsyncButton>
                  </div>
                )}
                {s.state === 'adopted' && (
                  <div className="gbk-bar">
                    <span className="badge badge-success">übernommen</span>
                    <AsyncButton
                      className="btn btn-sm"
                      disabled={book.locked}
                      confirm="Die übernommene Leistung samt Noten aus dem Notenbuch entfernen?"
                      onClick={() => run(() => gbApi.dismiss(book.id, { source_type: s.source_type, source_id: s.source_id }))}
                    >
                      Abwählen
                    </AsyncButton>
                  </div>
                )}
                {s.state === 'dismissed' && (
                  <div className="gbk-bar">
                    <span className="badge">abgewählt</span>
                    <AsyncButton
                      className="btn btn-sm"
                      onClick={async () => {
                        await gbApi.restore(book.id, { source_type: s.source_type, source_id: s.source_id });
                        q.reload();
                      }}
                    >
                      Wieder anzeigen
                    </AsyncButton>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
        {q.data?.sources.some((s) => s.state === 'adopted') && !book.locked && (
          <div>
            <AsyncButton
              className="btn btn-sm"
              onClick={async () => {
                try {
                  const r = await gbApi.sync(book.id);
                  onApply(r);
                  toast.success(r.changed ? `${r.changed} Eintragungen aktualisiert` : 'Alles aktuell');
                } catch (e) {
                  toast.error(e);
                }
              }}
            >
              Übernommene Ergebnisse abgleichen
            </AsyncButton>
          </div>
        )}
      </div>
    </Modal>
  );
}

/* ----------------------------------------------------------------------------------------------- Protokoll */
const ACTIONS: Record<string, string> = { entry: 'Note', final: 'Endnote', item: 'Leistung', category: 'Leistungsart', book: 'Notenbuch', settings: 'Einstellung', lock: 'Gesperrt', unlock: 'Geöffnet', source: 'Übernahme' };

export function LogDialog({ book, onClose }: { book: BookInfo; onClose: () => void }) {
  const q = useApi((signal) => gbApi.log(book.id, signal), [book.id]);
  return (
    <Modal title="Änderungsprotokoll" onClose={onClose} size="lg" footer={<button type="button" className="btn btn-primary" onClick={onClose}>Schließen</button>}>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!q.data && q.loading && <Loading />}
      {q.data && q.data.log.length === 0 && <Empty icon="history">Noch keine Änderungen.</Empty>}
      {q.data && q.data.log.length > 0 && (
        <div className="table-wrap">
          <table className="table table-compact">
            <thead>
              <tr>
                <th>Zeit</th>
                <th>Wer</th>
                <th>Was</th>
                <th>Schüler/in</th>
                <th>Änderung</th>
              </tr>
            </thead>
            <tbody>
              {q.data.log.map((r) => (
                <tr key={r.id}>
                  <td className="nowrap small">{new Date(r.at).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })}</td>
                  <td>{r.actor}</td>
                  <td>
                    {ACTIONS[r.action] ?? r.action}
                    {r.item ? ` · ${r.item}` : ''}
                  </td>
                  <td>{r.student}</td>
                  <td className="small">{describeChange(r.detail)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Modal>
  );
}

function describeChange(d: Record<string, unknown>): string {
  const from = d.from !== undefined ? String(d.from || '–') : null;
  const to = d.to !== undefined ? String(d.to || '–') : null;
  if (from !== null && to !== null) return `${from} → ${to}${d.removed ? ' (entfernt)' : ''}`;
  const parts: string[] = [];
  for (const [k, v] of Object.entries(d)) if (typeof v !== 'object') parts.push(`${k}: ${String(v)}`);
  return parts.join(', ');
}

/* -------------------------------------------------------------------------------------------- Einzelwert */
export function EntryDialog({ table, row, item, entry, onClose, onSave }: { table: Table; row: StudentRow; item: Item; entry: Entry | undefined; onClose: () => void; onSave: (p: EntryPatch) => Promise<void> }) {
  const scale = table.book.scale;
  const [value, setValue] = useState(entry?.value ?? '');
  const [status, setStatus] = useState<EntryStatus>(entry?.status ?? '');
  const [note, setNote] = useState(entry?.note ?? '');
  const [makeup, setMakeup] = useState(entry?.makeup_date ?? '');
  const labels = item.max_points ? [] : quickLabels(scale);
  const editable = table.book.can_edit;
  return (
    <Modal
      title={`${row.name} · ${item.title}`}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            {editable ? 'Abbrechen' : 'Schließen'}
          </button>
          {editable && (
            <AsyncButton
              className="btn btn-primary"
              onClick={async () => {
                await onSave({ student_id: row.student_id, value, status, note, makeup_date: status === 'nachschreiben' ? makeup : '' });
                onClose();
              }}
            >
              Speichern
            </AsyncButton>
          )}
        </>
      }
    >
      <div className="stack">
        {labels.length > 0 && editable && (
          <div className="gbk-quick" role="group" aria-label="Note wählen">
            {labels.map((l) => (
              <button key={l} type="button" className="btn btn-sm" aria-pressed={value === l && status === ''} onClick={() => { setValue(l); setStatus(''); }}>
                {l}
              </button>
            ))}
          </div>
        )}
        <Field label={item.max_points ? `Erreichte Punkte (von ${fmtWeight(item.max_points)})` : 'Note'} htmlFor="gbk-e-value">
          <input id="gbk-e-value" inputMode={scale?.kind === 'verbal' ? 'text' : 'decimal'} value={value} disabled={!editable} onChange={(e) => { setValue(e.target.value); if (status === 'nachschreiben') setStatus(''); }} />
        </Field>
        <Field label="Status" htmlFor="gbk-e-status" help="Entschuldigte und ausgelassene Leistungen und solche, die noch nachgeschrieben werden, zählen nicht in den Schnitt. Unentschuldigtes Fehlen zählt als ungenügend.">
          <select id="gbk-e-status" value={status} disabled={!editable} onChange={(e) => setStatus(e.target.value as EntryStatus)}>
            {STATUS_ORDER.map((s) => (
              <option key={s} value={s}>
                {STATUS_NAMES[s]}
              </option>
            ))}
          </select>
        </Field>
        {status === 'nachschreiben' && (
          <Field label="Nachschreibtermin" htmlFor="gbk-e-makeup">
            <input id="gbk-e-makeup" type="date" value={makeup} disabled={!editable} onChange={(e) => setMakeup(e.target.value)} />
          </Field>
        )}
        <Field label="Bemerkung" htmlFor="gbk-e-note" help="Sehen die Schülerin/der Schüler und die Eltern, sobald die Note sichtbar ist. Wird verschlüsselt gespeichert.">
          <textarea id="gbk-e-note" rows={3} maxLength={500} value={note} disabled={!editable} onChange={(e) => setNote(e.target.value)} />
        </Field>
        {entry?.label && item.max_points ? <p className="small muted">Entspricht der Note {entry.label}.</p> : null}
      </div>
    </Modal>
  );
}

/* ------------------------------------------------------------------------------------------------- Person */
export function StudentDialog({ table, row, onClose, onSaveFinal }: { table: Table; row: StudentRow; onClose: () => void; onSaveFinal: (value: string, note: string) => Promise<void> }) {
  const [final, setFinal] = useState(row.final);
  const [note, setNote] = useState(row.final_note);
  useEffect(() => {
    setFinal(row.final);
    setNote(row.final_note);
  }, [row.final, row.final_note]);
  const dec = table.book.decimals;
  const editable = table.book.can_edit;
  return (
    <Modal
      title={row.name}
      onClose={onClose}
      size="lg"
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            {editable ? 'Abbrechen' : 'Schließen'}
          </button>
          {editable && (
            <AsyncButton
              className="btn btn-primary"
              onClick={async () => {
                await onSaveFinal(final, note);
                onClose();
              }}
            >
              Speichern
            </AsyncButton>
          )}
        </>
      }
    >
      <div className="stack">
        <div className="table-wrap">
          <table className="table table-compact">
            <thead>
              <tr>
                <th>Leistungsart</th>
                <th className="num">Gewicht</th>
                <th className="num">Schnitt</th>
              </tr>
            </thead>
            <tbody>
              {table.categories.map((c) => (
                <tr key={c.id}>
                  <td>{`${' '.repeat(c.depth)}${c.name}`}</td>
                  <td className="num">{fmtWeight(c.weight)}</td>
                  <td className="num">{fmtNum(row.categories[String(c.id)], dec)}</td>
                </tr>
              ))}
              <tr>
                <th>Gesamt</th>
                <td />
                <th className="num">{fmtNum(row.average, dec)}</th>
              </tr>
            </tbody>
          </table>
        </div>
        <p>
          Vorschlag: <strong>{row.proposal || '–'}</strong>
          {row.overridden && <span className="badge badge-warning"> überschrieben</span>}
        </p>
        <div className="grid grid-2">
          <Field label="Festgelegte Note" htmlFor="gbk-p-final" help="Die Halbjahres- bzw. Zeugnisnote. Weicht sie vom Vorschlag ab, wird sie als „überschrieben“ gekennzeichnet.">
            <input id="gbk-p-final" value={final} disabled={!editable} maxLength={500} placeholder={row.proposal} onChange={(e) => setFinal(e.target.value)} />
          </Field>
        </div>
        <Field label="Bemerkung zur Note" htmlFor="gbk-p-note" help="Wird verschlüsselt gespeichert und mit der Endnote für Schüler/in und Eltern sichtbar.">
          <textarea id="gbk-p-note" rows={3} maxLength={500} value={note} disabled={!editable} onChange={(e) => setNote(e.target.value)} />
        </Field>
        <h3>Einzelnoten</h3>
        {table.items.length === 0 ? (
          <p className="muted">Keine Leistungen.</p>
        ) : (
          <ul className="gbk-list">
            {table.items.map((it) => {
              const e = row.entries[String(it.id)];
              if (!e) return null;
              return (
                <li key={it.id}>
                  <span className="gbk-li-main">
                    {it.title}
                    {e.note ? <span className="small muted"> – {e.note}</span> : null}
                  </span>
                  <strong>{e.status ? STATUS_NAMES[e.status] : e.label || e.value}</strong>
                </li>
              );
            })}
          </ul>
        )}
        <p className="xsmall muted">{termText(table.book.term)}</p>
      </div>
    </Modal>
  );
}

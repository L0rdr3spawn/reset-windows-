/**
 * Schülerliste eingeben (Klassen-Assistent und „Schüler/in hinzufügen“, §11.3): Liste aus Excel/Word/Text einfügen →
 * Vorschau als bearbeitbare Zeilen (Vorname, Nachname, E-Mail, Geburtsdatum, volljährig, bis zu zwei Eltern) mit
 * Fehlern/Hinweisen je Zeile. Auf dem Handy werden die Zeilen zu Karten (kein waagerechtes Scrollen).
 */
import { useId, useMemo, useState } from 'react';
import { Icon } from '../../components/Icon';
import { Alert, Field } from '../../components/ui';
import { checkRows, emptyDraft, isAdult, MAX_STUDENTS, parseStudentList, type ParentDraft, type StudentDraft } from './studentList';
import { confirmAsk } from '../../lib/confirm';

const FORMAT_TEXT: Record<string, string> = { tabelle: 'Tabelle', komma: '„Nachname, Vorname“', text: '„Vorname Nachname“', leer: '' };

export function studentListErrors(rows: readonly StudentDraft[], existing: readonly string[] = []): number {
  return checkRows(rows, existing).reduce((n, c) => n + c.errors.length, 0) + (rows.length > MAX_STUDENTS ? 1 : 0);
}

function RowEditor({
  row,
  pos,
  errors,
  warnings,
  onChange,
  onRemove,
}: {
  row: StudentDraft;
  pos: number;
  errors: string[];
  warnings: string[];
  onChange: (r: StudentDraft) => void;
  onRemove: () => void;
}) {
  const id = useId();
  const [open, setOpen] = useState(row.parents.length > 0);
  const set = (patch: Partial<StudentDraft>) => onChange({ ...row, ...patch });
  const setParent = (i: number, patch: Partial<ParentDraft>) => {
    const parents = [...row.parents];
    while (parents.length <= i) parents.push({ name: '', email: '' });
    parents[i] = { ...(parents[i] as ParentDraft), ...patch };
    set({ parents });
  };
  const adultFromDate = !!row.birth_date;
  const label = `Zeile ${pos}${row.first_name || row.last_name ? ` (${row.first_name} ${row.last_name})` : ''}`;
  return (
    <li className={`kl-sl-row${errors.length ? ' kl-sl-bad' : ''}`} aria-label={label}>
      <div className="kl-sl-head">
        <span className="kl-sl-num" aria-hidden="true">
          {pos}
        </span>
        <span className="kl-sl-status" aria-live="polite">
          {errors.map((e) => (
            <span key={e} className="error-text small">
              <Icon name="alert" /> {e}
            </span>
          ))}
          {warnings.map((w) => (
            <span key={w} className="small kl-sl-warn">
              <Icon name="info" /> {w}
            </span>
          ))}
        </span>
        <button type="button" className="btn btn-ghost btn-sm" onClick={onRemove} aria-label={`${label} entfernen`}>
          <Icon name="trash" />
        </button>
      </div>
      <div className="kl-sl-fields">
        <label className="kl-sl-field">
          <span>Vorname</span>
          <input
            type="text"
            value={row.first_name}
            maxLength={100}
            onChange={(e) => set({ first_name: e.target.value })}
            aria-invalid={!row.first_name.trim()}
          />
        </label>
        <label className="kl-sl-field">
          <span>Nachname</span>
          <input type="text" value={row.last_name} maxLength={100} onChange={(e) => set({ last_name: e.target.value })} aria-invalid={!row.last_name.trim()} />
        </label>
        <label className="kl-sl-field">
          <span>E-Mail (optional)</span>
          <input type="email" value={row.email} maxLength={254} autoCapitalize="none" onChange={(e) => set({ email: e.target.value })} />
        </label>
        <label className="kl-sl-field">
          <span>Geburtsdatum (optional)</span>
          <input type="date" value={/^\d{4}-\d{2}-\d{2}$/.test(row.birth_date) ? row.birth_date : ''} onChange={(e) => set({ birth_date: e.target.value })} />
        </label>
        <label className="check kl-sl-adult" title={adultFromDate ? 'aus dem Geburtsdatum berechnet' : undefined}>
          <input type="checkbox" checked={isAdult(row)} disabled={adultFromDate} onChange={(e) => set({ adult: e.target.checked })} /> volljährig
          {adultFromDate && <span className="small muted"> (aus Geburtsdatum)</span>}
        </label>
      </div>
      <button type="button" className="btn btn-ghost btn-sm kl-sl-parents-toggle" aria-expanded={open} aria-controls={`${id}-p`} onClick={() => setOpen(!open)}>
        <Icon name={open ? 'chevronDown' : 'chevronRight'} /> Eltern
        {row.parents.filter((p) => p.name || p.email).length ? ` (${row.parents.filter((p) => p.name || p.email).length})` : ''}
      </button>
      {open && (
        <div className="kl-sl-fields kl-sl-parents" id={`${id}-p`}>
          {[0, 1].map((i) => (
            <fieldset key={i} className="kl-sl-parent">
              <legend className="small">Elternteil {i + 1}</legend>
              <label className="kl-sl-field">
                <span>Name</span>
                <input type="text" value={row.parents[i]?.name ?? ''} maxLength={200} onChange={(e) => setParent(i, { name: e.target.value })} />
              </label>
              <label className="kl-sl-field">
                <span>E-Mail</span>
                <input
                  type="email"
                  value={row.parents[i]?.email ?? ''}
                  maxLength={254}
                  autoCapitalize="none"
                  onChange={(e) => setParent(i, { email: e.target.value })}
                />
              </label>
            </fieldset>
          ))}
        </div>
      )}
    </li>
  );
}

export function StudentListEditor({
  rows,
  onChange,
  existing = [],
}: {
  rows: StudentDraft[];
  onChange: (rows: StudentDraft[]) => void;
  existing?: readonly string[];
}) {
  const [text, setText] = useState('');
  const [info, setInfo] = useState<string | null>(null);
  const textId = useId();
  const checks = useMemo(() => checkRows(rows, existing), [rows, existing]);
  const errors = checks.reduce((n, c) => n + c.errors.length, 0);
  const warnings = checks.reduce((n, c) => n + c.warnings.length, 0);

  const take = () => {
    const res = parseStudentList(text);
    if (!res.rows.length) {
      setInfo('Keine Namen erkannt – bitte je Zeile eine Person einfügen.');
      return;
    }
    onChange([...rows, ...res.rows]);
    const cols = res.columns.length ? ` (Spalten: ${res.columns.join(', ')})` : '';
    setInfo(
      `${res.rows.length} ${res.rows.length === 1 ? 'Person' : 'Personen'} übernommen – erkannt: ${FORMAT_TEXT[res.format]}${res.header ? ' mit Kopfzeile' : ''}${cols}. Bitte prüfen.`,
    );
    setText('');
  };

  return (
    <div className="stack">
      <Field
        label="Liste einfügen"
        htmlFor={textId}
        help="Je Zeile eine Person: „Nachname, Vorname“, „Vorname Nachname“ oder Zeilen aus Excel/Word (mit oder ohne Kopfzeile; Spalten E-Mail, Geburtsdatum, volljährig, Elternteil 1/2 und E-Mail Eltern werden erkannt). Volljährigkeit wird aus dem Geburtsdatum berechnet."
      >
        <textarea
          id={textId}
          rows={6}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={'Mustermann, Max\nAnna-Lena von der Heide\n\noder aus Excel: Nachname ⇥ Vorname ⇥ E-Mail ⇥ Geburtsdatum ⇥ Eltern ⇥ E-Mail Eltern'}
          className="kl-sl-text"
        />
      </Field>
      <div className="row">
        <button type="button" className="btn btn-primary" onClick={take} disabled={!text.trim()}>
          <Icon name="list" /> In die Liste übernehmen
        </button>
        <button type="button" className="btn" onClick={() => onChange([...rows, emptyDraft()])}>
          <Icon name="plus" /> Zeile hinzufügen
        </button>
        {rows.length > 0 && (
          <button type="button" className="btn btn-ghost" onClick={async () => {
              if (await confirmAsk({ title: 'Liste leeren', message: 'Alle Zeilen entfernen?', confirmLabel: 'Leeren', danger: true })) onChange([]);
            }}>
            <Icon name="trash" /> Liste leeren
          </button>
        )}
      </div>
      <div aria-live="polite">
        {info && <p className="small">{info}</p>}
        {rows.length > MAX_STUDENTS && (
          <Alert kind="error" title={`Höchstens ${MAX_STUDENTS} Schüler/innen auf einmal`}>
            Bitte die Liste aufteilen und den Rest danach über „Schüler/in hinzufügen“ ergänzen.
          </Alert>
        )}
        {rows.length > 0 && (
          <p className="small" style={{ margin: 0 }}>
            <strong>{rows.length === 1 ? '1 Schüler/in' : `${rows.length} Schüler/innen`}</strong>
            {errors ? <span className="error-text"> · {errors === 1 ? '1 Fehler' : `${errors} Fehler`}</span> : null}
            {warnings ? <span> · {warnings === 1 ? '1 Hinweis' : `${warnings} Hinweise`}</span> : null}
          </p>
        )}
      </div>
      {rows.length > 0 && (
        <ol className="kl-sl-rows">
          {rows.map((r, i) => (
            <RowEditor
              key={r.key}
              row={r}
              pos={i + 1}
              errors={checks[i]?.errors ?? []}
              warnings={checks[i]?.warnings ?? []}
              onChange={(next) => onChange(rows.map((x) => (x.key === r.key ? next : x)))}
              onRemove={() => onChange(rows.filter((x) => x.key !== r.key))}
            />
          ))}
        </ol>
      )}
    </div>
  );
}

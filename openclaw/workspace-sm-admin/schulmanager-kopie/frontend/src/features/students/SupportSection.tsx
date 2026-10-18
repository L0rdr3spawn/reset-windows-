/**
 * Förderung & Nachteilsausgleich eines Kindes: Merkmale aus dem Katalog der Schule (Zeitzuschlag, Hilfsmittel, ADHS …),
 * ggf. je Fach, gültig von/bis, mit Nachweisen (PDF/Fotos). Pflegen: Sekretariat, Schulleitung, Klassenleitung.
 * Vollsicht (Details, Nachweise): Verwaltung, Klassenleitung, Familie. Fachlehrkräfte sehen nur die Art des Ausgleichs.
 */
import { useMemo, useState } from 'react';
import { fileUrl, type StoredFileInfo } from '../../api/files';
import { FileUpload } from '../../components/FileUpload';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { MultiSelect } from '../../components/SearchSelect';
import { AsyncButton, ErrorBox, Field } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useCollection } from '../../hooks/useCollection';
import { useApi } from '../../hooks/useApi';
import { formatDate } from '../../lib/dates';
import { entryText, supportApi, type CatalogItem, type SupportEntry, type SupportKind } from './supportApi';

function NewEntry({ sid, catalog, onDone }: { sid: string; catalog: CatalogItem[]; onDone: () => void }) {
  const toast = useToast();
  const subjects = useCollection('subjects');
  const [catId, setCatId] = useState<string>(catalog[0] ? String(catalog[0].id) : '');
  const cat = catalog.find((c) => String(c.id) === catId) ?? null;
  const [minutes, setMinutes] = useState<string>(cat?.uses_minutes && cat.default_minutes ? String(cat.default_minutes) : '');
  const [subjectIds, setSubjectIds] = useState<string[]>([]);
  const [aids, setAids] = useState('');
  const [title, setTitle] = useState('');
  const [details, setDetails] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [uploaded, setUploaded] = useState<StoredFileInfo[]>([]);
  const [key, setKey] = useState(0);
  const subjectOptions = (subjects.data ?? []).map((x) => ({ value: x.id, label: x.name }));
  const pick = (v: string) => {
    setCatId(v);
    const c = catalog.find((x) => String(x.id) === v);
    setMinutes(c?.uses_minutes && c.default_minutes ? String(c.default_minutes) : '');
  };
  return (
    <div className="stack-sm">
      <div className="form-grid">
        <Field label="Art" htmlFor="sp-cat" help="Die Arten legt die Schule im Katalog fest (Stammdaten → Schüler/innen → Katalog der Merkmale).">
          <select id="sp-cat" value={catId} onChange={(e) => pick(e.target.value)}>
            {catalog.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
            <option value="">Sonstiges (freie Beschreibung)</option>
          </select>
        </Field>
        {cat?.uses_minutes && (
          <Field label="Zeitzuschlag (Minuten)" htmlFor="sp-min">
            <input id="sp-min" type="number" min={0} max={600} value={minutes} onChange={(e) => setMinutes(e.target.value)} />
          </Field>
        )}
        {!cat && (
          <Field label="Kurzbeschreibung" htmlFor="sp-title">
            <input id="sp-title" value={title} maxLength={200} onChange={(e) => setTitle(e.target.value)} />
          </Field>
        )}
        <Field label="Gültig ab" htmlFor="sp-from">
          <input id="sp-from" type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
        </Field>
        <Field label="Gültig bis" htmlFor="sp-to">
          <input id="sp-to" type="date" value={to} onChange={(e) => setTo(e.target.value)} />
        </Field>
      </div>
      <MultiSelect label="Nur in diesen Fächern (leer = alle Fächer)" options={subjectOptions} values={subjectIds} onChange={setSubjectIds} placeholder="Fach hinzufügen …" />
      <Field label="Hilfsmittel" htmlFor="sp-aids" help="Wird Lehrkräften bei Klausuren angezeigt, z. B. „Duden“, „Taschenrechner“.">
        <input id="sp-aids" value={aids} maxLength={500} onChange={(e) => setAids(e.target.value)} />
      </Field>
      <Field label="Details (nur für Berechtigte)" htmlFor="sp-details" help="Diagnose, Ansprechpersonen u. Ä. sehen Fachlehrkräfte nicht.">
        <textarea id="sp-details" rows={3} value={details} maxLength={5000} onChange={(e) => setDetails(e.target.value)} />
      </Field>
      <FileUpload key={key} purpose="student_document" label="Nachweise (z. B. Bescheid als PDF)" accept=".pdf,.jpg,.jpeg,.png,.heic,.webp,.doc,.docx" onChange={setUploaded} />
      <div className="row">
        <AsyncButton
          className="btn btn-primary"
          disabled={!cat && !title.trim()}
          onClick={async () => {
            try {
              await supportApi.create(sid, {
                catalog_id: cat ? cat.id : null,
                kind: (cat?.kind ?? 'sonstiges') as SupportKind,
                title,
                details,
                minutes: cat?.uses_minutes && minutes ? Number(minutes) : null,
                subjects: subjectIds,
                aids,
                valid_from: from || null,
                valid_to: to || null,
                file_ids: uploaded.map((f) => f.id),
              });
              toast.success('Gespeichert');
              setTitle('');
              setDetails('');
              setAids('');
              setSubjectIds([]);
              setUploaded([]);
              setKey((k) => k + 1);
              onDone();
            } catch (e) {
              toast.error(e);
            }
          }}
        >
          <Icon name="plus" /> Eintragen
        </AsyncButton>
      </div>
    </div>
  );
}

export function SupportSection({ studentId, embedded = false }: { studentId: string; embedded?: boolean }) {
  const toast = useToast();
  const q = useApi((signal) => supportApi.list(studentId, signal), [studentId], { live: ['student_support', 'support_catalog'] });
  const data = q.data;
  const subjects = useCollection('subjects', !!data && (data.can_edit || data.entries.some((e) => e.subjects.length > 0)));
  const names = useMemo(() => new Map((subjects.data ?? []).map((x) => [x.id, x.name])), [subjects.data]);
  if (q.error) return embedded ? null : <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!data) return null;
  if (!data.entries.length && !data.can_edit && !embedded) return null;
  const Head = embedded ? 'h3' : 'h2';
  const line = (e: SupportEntry) =>
    entryText(
      e,
      e.subjects.map((x) => names.get(x) ?? x),
    );
  return (
    <section className={embedded ? 'stack-sm' : 'card stack-sm'} aria-labelledby={`sp-h-${studentId}`}>
      <Head id={`sp-h-${studentId}`} style={{ margin: 0 }}>
        Förderung &amp; Nachteilsausgleich
        <HelpTip>
          {data.level === 'full'
            ? 'Vollsicht: Details und Nachweise sehen nur Schulleitung, Sekretariat, Klassenleitung und die Familie. Jeder Aufruf steht im Protokoll.'
            : 'Sie sehen nur die Art des Ausgleichs, damit Sie ihn bei Tests und Klausuren berücksichtigen – keine Diagnose, keine Nachweise.'}
        </HelpTip>
      </Head>
      {!data.entries.length && <p className="muted small">Keine Einträge.</p>}
      <ul className="st-list">
        {data.entries.map((e) => (
          <li key={e.id} className="st-row">
            <div className="st-row-main">
              <strong>
                <span className="badge badge-primary">{e.kind_label}</span> {line(e)}
              </strong>
              {e.title && e.title !== e.label && <span className="small">{e.title}</span>}
              {e.details && <span className="small">{e.details}</span>}
              <span className="xsmall muted">
                {e.valid_from || e.valid_to ? `gültig ${e.valid_from ? `ab ${formatDate(e.valid_from)}` : ''}${e.valid_to ? ` bis ${formatDate(e.valid_to)}` : ''}` : ''}
                {e.created_by_name ? `${e.valid_from || e.valid_to ? ' · ' : ''}eingetragen von ${e.created_by_name}` : ''}
              </span>
            </div>
            <div className="st-row-side">
              {e.files.map((f) => (
                <a key={f.id} className="btn btn-sm" href={fileUrl(f.id, { inline: true })} target="_blank" rel="noopener noreferrer">
                  <Icon name="eye" /> {f.filename}
                </a>
              ))}
              {e.can_edit && (
                <AsyncButton
                  className="btn btn-sm btn-ghost"
                  confirm={`„${e.label}“ löschen?`}
                  onClick={async () => {
                    try {
                      await supportApi.remove(studentId, e.id);
                      q.reload();
                    } catch (err) {
                      toast.error(err);
                    }
                  }}
                >
                  <Icon name="trash" />
                  <span className="sr-only">löschen</span>
                </AsyncButton>
              )}
            </div>
          </li>
        ))}
      </ul>
      {data.can_edit && (
        <details className="st-details">
          <summary>Neuen Eintrag anlegen</summary>
          <NewEntry sid={studentId} catalog={data.catalog} onDone={q.reload} />
        </details>
      )}
    </section>
  );
}

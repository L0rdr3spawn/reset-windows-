import { useMemo, useState } from 'react';
import { exportUrls, imports, type CsvWhat } from '../api/endpoints';
import type { ImportReport } from '../api/types';
import { HelpTip } from '../components/HelpTip';
import { Icon } from '../components/Icon';
import { Alert, AsyncButton, Field } from '../components/ui';
import { useUser } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { invalidateAll } from '../hooks/useCollection';
import { useTitle } from '../hooks/misc';
import { previewCsv, suggestMapping, type CsvPreview } from '../lib/csv';
import { CSV_FIELDS, CSV_PRESETS } from '../lib/csvFields';
import { addDays, todayISO } from '../lib/dates';
import { can } from '../lib/permissions';
import { confirmAsk } from '../lib/confirm';

const CSV_WHAT: { key: CsvWhat; label: string }[] = [
  { key: 'teachers', label: 'Lehrkräfte' },
  { key: 'classes', label: 'Klassen' },
  { key: 'rooms', label: 'Räume' },
  { key: 'subjects', label: 'Fächer' },
  { key: 'students', label: 'Schüler/innen' },
  { key: 'curricula', label: 'Stundentafeln' },
  { key: 'lessons', label: 'Unterricht/Stunden' },
];

const PRESET_LABELS: Record<string, string> = { 'schild-nrw': 'SchILD-NRW', asv: 'ASV (BW/BY)', lusd: 'LUSD (Hessen)', magellan: 'Magellan' };

const REPORT_LABELS: Record<string, string> = {
  what: 'Art',
  rows: 'Zeilen',
  created: 'neu',
  updated: 'geändert',
  skipped: 'übersprungen',
  delimiter: 'Trennzeichen',
  mode: 'Modus',
  sites: 'Standorte',
  subjects: 'Fächer',
  teachers: 'Lehrkräfte',
  rooms: 'Räume',
  classes: 'Klassen',
  students: 'Schüler/innen',
  courses: 'Kurse',
  lessons: 'Stunden',
  curricula: 'Stundentafeln',
  substitutions: 'Vertretungen',
  absences: 'Abwesenheiten',
  holidays: 'Ferien',
  merge: 'zusammenführen',
  replace: 'ersetzen',
};
const HIDDEN_REPORT_KEYS = ['warnings', 'errors', 'counts', 'files', 'dry_run', 'encoding', 'danger', 'partial', 'would_delete'];
const reportLabel = (k: string) => REPORT_LABELS[k] ?? k;
const reportValue = (v: unknown) => (typeof v === 'string' ? REPORT_LABELS[v] ?? v : String(v));

function ReportView({ report, dry }: { report: ImportReport; dry: boolean }) {
  const counts = (report.counts ?? null) as Record<string, number> | null;
  const warnings = (report.warnings ?? []) as string[];
  const errors = (report.errors ?? []) as string[];
  const danger = (Array.isArray(report.danger) ? report.danger : []) as string[];
  const simple = Object.entries(report).filter(([k, v]) => !HIDDEN_REPORT_KEYS.includes(k) && (typeof v === 'number' || typeof v === 'string'));
  return (
    <Alert kind={errors.length || danger.length ? 'error' : warnings.length ? 'warning' : 'success'} title={dry ? 'Probelauf – nichts gespeichert' : 'Import abgeschlossen'}>
      {danger.length > 0 && (
        <ul>
          {danger.map((d, i) => (
            <li key={i}>
              <strong>{d}</strong>
            </li>
          ))}
        </ul>
      )}
      {simple.length > 0 && <div className="small">{simple.map(([k, v]) => `${reportLabel(k)}: ${reportValue(v)}`).join(' · ')}</div>}
      {counts && (
        <div className="small">
          {Object.entries(counts)
            .filter(([, v]) => v)
            .map(([k, v]) => `${reportLabel(k)}: ${v}`)
            .join(' · ')}
        </div>
      )}
      {errors.length > 0 && (
        <ul className="small">
          {errors.slice(0, 30).map((w, i) => (
            <li key={i}>{w}</li>
          ))}
        </ul>
      )}
      {warnings.length > 0 && (
        <details>
          <summary className="small">{warnings.length} Hinweise</summary>
          <ul className="small">
            {warnings.slice(0, 100).map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </details>
      )}
    </Alert>
  );
}

function UntisImport() {
  const toast = useToast();
  const [files, setFiles] = useState<File[]>([]);
  const [mode, setMode] = useState<'merge' | 'replace'>('merge');
  const [result, setResult] = useState<{ report: ImportReport; dry: boolean } | null>(null);
  const run = async (dry: boolean) => {
    if (!dry && mode === 'replace' && !(await confirmAsk({ title: 'Planungsdaten ersetzen', message: 'Alle Planungsdaten durch den Import ersetzen? (Rückgängig über „Verlauf“ möglich)', confirmLabel: 'Ersetzen', danger: true }))) return;
    try {
      const report = await imports.untis(files, mode, dry);
      setResult({ report, dry });
      if (!dry) {
        invalidateAll();
        toast.success('Untis-Import abgeschlossen');
      }
    } catch (e) {
      toast.error(e, 'Untis-Import');
    }
  };
  return (
    <section className="card">
      <h2>
        Untis (GPU-Dateien)
        <HelpTip>GPU001 (Stundenplan), GPU002 (Unterricht), GPU003–006 (Klassen, Lehrer, Räume, Fächer), GPU010 (Schüler), einzeln oder als ZIP.</HelpTip>
      </h2>
      <div className="form-grid" style={{ marginTop: 12 }}>
        <Field label="Dateien" htmlFor="untis-files">
          <input id="untis-files" type="file" multiple accept=".zip,.txt,.csv,.gpu" onChange={(e) => setFiles(Array.from(e.target.files ?? []))} />
        </Field>
        <fieldset>
          <legend>Modus</legend>
          <label className="check">
            <input type="radio" name="untis-mode" checked={mode === 'merge'} onChange={() => setMode('merge')} /> ergänzen/aktualisieren
          </label>
          <label className="check">
            <input type="radio" name="untis-mode" checked={mode === 'replace'} onChange={() => setMode('replace')} /> alles ersetzen
          </label>
        </fieldset>
      </div>
      <div className="row" style={{ marginTop: 12 }}>
        <AsyncButton className="btn" disabled={!files.length} onClick={() => run(true)}>
          <Icon name="eye" /> Probelauf
        </AsyncButton>
        <AsyncButton className="btn btn-primary" disabled={!files.length} onClick={() => run(false)}>
          <Icon name="upload" /> Importieren
        </AsyncButton>
      </div>
      {result && (
        <div style={{ marginTop: 12 }}>
          <ReportView report={result.report} dry={result.dry} />
        </div>
      )}
    </section>
  );
}

function CsvImport() {
  const toast = useToast();
  const [what, setWhat] = useState<CsvWhat>('students');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<CsvPreview | null>(null);
  /** Spalte in Datei → Zielfeld */
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [result, setResult] = useState<{ report: ImportReport; dry: boolean } | null>(null);
  const [preset, setPreset] = useState('');
  const fields = CSV_FIELDS[what];
  const presets = CSV_PRESETS[what];

  const load = async (f: File | null, w: CsvWhat = what) => {
    setFile(f);
    setResult(null);
    if (!f) {
      setPreview(null);
      return;
    }
    const buf = await f.arrayBuffer();
    let text = new TextDecoder('utf-8').decode(buf);
    if (text.includes('�')) text = new TextDecoder('windows-1252').decode(buf);
    const p = previewCsv(text);
    setPreview(p);
    const sug = suggestMapping(p.headers, CSV_FIELDS[w]); // Zielfeld → Spalte
    const m: Record<string, string> = {};
    for (const [field, col] of Object.entries(sug)) m[col] = field;
    setMapping(m);
  };

  const mappedFields = useMemo(() => new Set(Object.values(mapping)), [mapping]);

  const run = async (dry: boolean) => {
    if (!file) return;
    try {
      const m: Record<string, string> = { ...mapping };
      if (preset) m.preset = preset;
      const report = await imports.csv(what, file, m, dry);
      setResult({ report, dry });
      if (!dry) {
        invalidateAll();
        toast.success('CSV-Import abgeschlossen');
      }
    } catch (e) {
      toast.error(e, 'CSV-Import');
    }
  };

  return (
    <section className="card">
      <h2>
        CSV mit Spalten-Zuordnung
        <HelpTip>Für Exporte aus SchILD-NRW, ASV-BW/BY, Excel u. a. Trennzeichen „;“ oder „,“, Kodierung UTF-8 oder Windows-1252.</HelpTip>
      </h2>
      <div className="form-grid" style={{ marginTop: 12 }}>
        <Field label="Daten" htmlFor="csv-what">
          <select
            id="csv-what"
            value={what}
            onChange={(e) => {
              const w = e.target.value as CsvWhat;
              setWhat(w);
              setPreset('');
              void load(file, w);
            }}
          >
            {CSV_WHAT.map((w) => (
              <option key={w.key} value={w.key}>
                {w.label}
              </option>
            ))}
          </select>
        </Field>
        {presets.length > 0 && (
          <Field label="Vorlage (Quelle)" htmlFor="csv-preset" hint="Erkennt die Spalten typischer Exporte automatisch">
            <select id="csv-preset" value={preset} onChange={(e) => setPreset(e.target.value)}>
              <option value="">automatisch / eigene Zuordnung</option>
              {presets.map((p) => (
                <option key={p} value={p}>
                  {PRESET_LABELS[p] ?? p}
                </option>
              ))}
            </select>
          </Field>
        )}
        <Field label="CSV-Datei" htmlFor="csv-file">
          <input id="csv-file" type="file" accept=".csv,.txt" onChange={(e) => void load(e.target.files?.[0] ?? null)} />
        </Field>
      </div>
      {preview && (
        <div className="stack" style={{ marginTop: 12 }}>
          <h3>Spalten zuordnen</h3>
          <div className="table-wrap">
            <table className="table table-compact">
              <thead>
                <tr>
                  <th scope="col">Spalte in der Datei</th>
                  <th scope="col">Beispielwerte</th>
                  <th scope="col">Zielfeld</th>
                </tr>
              </thead>
              <tbody>
                {preview.headers.map((h, i) => (
                  <tr key={`${h}-${i}`}>
                    <td>
                      <strong>{h || `(Spalte ${i + 1})`}</strong>
                    </td>
                    <td className="small muted">
                      {preview.rows
                        .map((r) => r[i])
                        .filter(Boolean)
                        .slice(0, 3)
                        .join(' | ')}
                    </td>
                    <td>
                      <label className="sr-only" htmlFor={`map-${i}`}>
                        Zielfeld für {h}
                      </label>
                      <select
                        id={`map-${i}`}
                        className="input-sm"
                        value={mapping[h] ?? ''}
                        onChange={(e) =>
                          setMapping((m) => {
                            const n = { ...m };
                            if (e.target.value) n[h] = e.target.value;
                            else delete n[h];
                            return n;
                          })
                        }
                      >
                        <option value="">– ignorieren –</option>
                        {fields.map((f) => (
                          <option key={f.key} value={f.key} disabled={mappedFields.has(f.key) && mapping[h] !== f.key}>
                            {f.label}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="xsmall muted">
            Erkanntes Trennzeichen: „{preview.delimiter === '\t' ? 'Tab' : preview.delimiter}“
            <HelpTip>Nicht zugeordnete Spalten werden ignoriert, sofern die Vorlage sie nicht kennt. Leere Zellen ändern bestehende Werte nicht.</HelpTip>
          </p>
          <div className="row">
            <AsyncButton className="btn" onClick={() => run(true)}>
              <Icon name="eye" /> Probelauf
            </AsyncButton>
            <AsyncButton className="btn btn-primary" onClick={() => run(false)}>
              <Icon name="upload" /> Importieren
            </AsyncButton>
          </div>
        </div>
      )}
      {result && (
        <div style={{ marginTop: 12 }}>
          <ReportView report={result.report} dry={result.dry} />
        </div>
      )}
    </section>
  );
}

function JsonImport() {
  const toast = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<{ report: ImportReport; dry: boolean } | null>(null);
  const run = async (dry: boolean) => {
    if (!file) return;
    try {
      if (!dry) {
        const check = await imports.json(file, true);
        const danger = (Array.isArray(check.danger) ? check.danger : []) as string[];
        const text = danger.length
          ? `ACHTUNG – Teil-Dokument:\n${danger.join('\n')}\n\nTrotzdem alles ersetzen? (Rückgängig über „Verlauf“ möglich)`
          : 'Das komplette Planungsdokument wird ersetzt. Fortfahren? (Rückgängig über „Verlauf“ möglich)';
        if (!(await confirmAsk({ title: 'Planungsdokument ersetzen', message: text, confirmLabel: 'Ersetzen', danger: true }))) {
          setResult({ report: check, dry: true });
          return;
        }
      }
      const report = await imports.json(file, dry);
      setResult({ report, dry });
      if (!dry) {
        invalidateAll();
        toast.success('JSON-Import abgeschlossen');
      }
    } catch (e) {
      toast.error(e, 'JSON-Import');
    }
  };
  return (
    <section className="card">
      <h2>
        JSON (komplette Sicherung)
        <HelpTip>Stellt einen JSON-Export dieses Systems wieder her. Alle Planungsdaten werden ersetzt, Konten bleiben unverändert.</HelpTip>
      </h2>
      <div className="row" style={{ marginTop: 12, alignItems: 'flex-end' }}>
        <Field label="JSON-Datei" htmlFor="json-file">
          <input id="json-file" type="file" accept=".json,application/json" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </Field>
        <AsyncButton className="btn" disabled={!file} onClick={() => run(true)}>
          <Icon name="eye" /> Prüfen
        </AsyncButton>
        <AsyncButton className="btn btn-danger" disabled={!file} onClick={() => run(false)}>
          <Icon name="upload" /> Ersetzen
        </AsyncButton>
      </div>
      {result && (
        <div style={{ marginTop: 12 }}>
          <ReportView report={result.report} dry={result.dry} />
        </div>
      )}
    </section>
  );
}

export default function ImportExportPage() {
  useTitle('Import / Export');
  const user = useUser();
  const [from, setFrom] = useState(todayISO());
  const [to, setTo] = useState(addDays(todayISO(), 7));
  const [withStudents, setWithStudents] = useState(true);
  const canImportPlan = can(user, 'timetable.edit');
  const canImportMaster = can(user, 'masterdata.edit');
  const canStudents = can(user, 'students.read');

  return (
    <div className="page">
      <div className="page-head">
        <h1>Import / Export</h1>
      </div>
      <div className="stack">
        <section className="card">
          <h2>
            Export
            <HelpTip>Für Untis, Schulmanager Online (dateibasierter Import) und Tabellenkalkulation. Vertretungen werden für den gewählten Zeitraum mitexportiert.</HelpTip>
          </h2>
          <div className="form-grid" style={{ marginTop: 12 }}>
            <Field label="Vertretungen von" htmlFor="ex-from">
              <input id="ex-from" type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
            </Field>
            <Field label="bis" htmlFor="ex-to">
              <input id="ex-to" type="date" value={to} min={from} onChange={(e) => setTo(e.target.value)} />
            </Field>
          </div>
          <div className="row" style={{ marginTop: 12 }}>
            <a className="btn" href={exportUrls.untis({ from, to })} download>
              <Icon name="download" /> Untis GPU (ZIP)
            </a>
            <a className="btn" href={exportUrls.schulmanagerOnline({ from, to, students: withStudents ? 1 : 0 })} download>
              <Icon name="download" /> Schulmanager-Online-Paket
            </a>
            {canStudents && (
              <label className="check">
                <input type="checkbox" checked={withStudents} onChange={(e) => setWithStudents(e.target.checked)} /> mit Schülerdaten
              </label>
            )}
            <a className="btn" href={exportUrls.json()} download>
              <Icon name="download" /> JSON (komplett)
            </a>
          </div>
          <h3 style={{ marginTop: 16 }}>CSV</h3>
          <div className="row">
            {CSV_WHAT.filter((w) => w.key !== 'students' || canStudents).map((w) => (
              <a key={w.key} className="btn btn-sm" href={exportUrls.csv(w.key)} download>
                <Icon name="download" /> {w.label}
              </a>
            ))}
          </div>
        </section>
        {canImportPlan && <UntisImport />}
        {(canImportMaster || canImportPlan) && <CsvImport />}
        {canImportPlan && canImportMaster && <JsonImport />}
      </div>
    </div>
  );
}

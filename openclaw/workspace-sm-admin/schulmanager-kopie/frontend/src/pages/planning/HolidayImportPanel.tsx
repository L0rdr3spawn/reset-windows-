/**
 * Planung › „Zeitraster & Schuljahr“: Ferien und Feiertage automatisch aus einer öffentlichen API übernehmen
 * (Land + Bundesland, Automatik an/aus, Vorschau, „Jetzt übernehmen“). Server: `server/holiday_import.py`.
 */
import { useEffect, useState } from 'react';
import { Alert, AsyncButton, ErrorBox, Field, Loading } from '../../components/ui';
import { HelpTip } from '../../components/HelpTip';
import { useToast } from '../../context/ToastContext';
import { invalidate } from '../../hooks/useCollection';
import { formatDate, formatDateTime } from '../../lib/dates';
import { ACTION_LABELS, holidayImportApi, regionOptions, summaryText, visibleChanges, type HolidayCountry, type HolidayImportResult, type HolidayImportState, type HolidayRegion } from './holidayImport';

export function HolidayImportPanel() {
  const toast = useToast();
  const [state, setState] = useState<HolidayImportState | null>(null);
  const [draft, setDraft] = useState<{ enabled: boolean; country: string; region: string } | null>(null);
  const [countries, setCountries] = useState<HolidayCountry[]>([]);
  const [regions, setRegions] = useState<HolidayRegion[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [result, setResult] = useState<{ data: HolidayImportResult; applied: boolean } | null>(null);

  useEffect(() => {
    let alive = true;
    Promise.all([holidayImportApi.get(), holidayImportApi.countries()])
      .then(([s, c]) => {
        if (!alive) return;
        setState(s);
        setCountries(c);
        setDraft({ enabled: s.enabled, country: s.country, region: s.region });
      })
      .catch((e) => alive && setError(e));
    return () => {
      alive = false;
    };
  }, []);

  const country = draft?.country;
  useEffect(() => {
    if (!country) return;
    let alive = true;
    holidayImportApi
      .regions(country)
      .then((r) => alive && setRegions(r))
      .catch(() => alive && setRegions([]));
    return () => {
      alive = false;
    };
  }, [country]);

  if (error) return <ErrorBox error={error} />;
  if (!state || !draft) return <Loading />;

  const dirty = draft.enabled !== state.enabled || draft.country !== state.country || draft.region !== state.region;
  const source = countries.find((c) => c.code === draft.country)?.source;
  const options = regionOptions(regions);

  const save = async () => {
    if (!dirty) return;
    setState(await holidayImportApi.put({ enabled: draft.enabled, country: draft.country, region: draft.region, language: state.language }));
    setResult(null);
  };
  const run = async (apply: boolean) => {
    await save();
    const data = await (apply ? holidayImportApi.apply() : holidayImportApi.preview());
    setResult({ data, applied: apply });
    if (apply) {
      invalidate('holidays');
      toast.success(`Ferien und Feiertage: ${summaryText(data.counts)}`);
      setState(await holidayImportApi.get());
    }
  };

  const rows = result ? visibleChanges(result.data.changes) : [];
  const st = state.status;

  return (
    <section className="card">
      <h2>
        Ferien &amp; Feiertage automatisch{' '}
        <HelpTip>Holt gesetzliche Feiertage und Schulferien aus einer öffentlichen Quelle (openholidaysapi.org). Von Hand angelegte oder geänderte Einträge bleiben unverändert, nichts wird gelöscht.</HelpTip>
      </h2>
      {!state.available && <Alert kind="info">Der automatische Abruf ist auf diesem Server abgeschaltet (SM_HOLIDAY_IMPORT=0).</Alert>}
      <div className="form-grid">
        <Field
          label="Land"
          htmlFor="hi-country"
          help={source === 'nager' ? 'Für dieses Land gibt es nur gesetzliche Feiertage, keine Schulferien.' : undefined}
        >
          <select id="hi-country" value={draft.country} onChange={(e) => setDraft({ ...draft, country: e.target.value, region: '' })}>
            {!countries.some((c) => c.code === draft.country) && <option value={draft.country}>{draft.country}</option>}
            {countries.map((c) => (
              <option key={c.code} value={c.code}>
                {c.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Bundesland / Region" htmlFor="hi-region" hint={options.length === 0 ? 'Keine Regionen verfügbar – nur landesweite Feiertage.' : undefined}>
          <select id="hi-region" value={draft.region} disabled={options.length === 0} onChange={(e) => setDraft({ ...draft, region: e.target.value })}>
            <option value="">– landesweit –</option>
            {options.map((o) => (
              <option key={o.code} value={o.code}>
                {o.label}
              </option>
            ))}
          </select>
        </Field>
        <div className="field">
          <span className="field-label">&nbsp;</span>
          <label className="check">
            <input type="checkbox" checked={draft.enabled} disabled={!state.available} onChange={(e) => setDraft({ ...draft, enabled: e.target.checked })} /> Jedes Schuljahr automatisch übernehmen
          </label>
        </div>
      </div>
      <div className="row" style={{ gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
        <AsyncButton
          className="btn"
          disabled={!dirty}
          onClick={async () => {
            await save();
            toast.success('Gespeichert');
          }}
        >
          Speichern
        </AsyncButton>
        <AsyncButton className="btn" onClick={() => run(false)}>
          Vorschau
        </AsyncButton>
        <AsyncButton className="btn btn-primary" onClick={() => run(true)}>
          Jetzt übernehmen
        </AsyncButton>
      </div>
      <p className="muted" style={{ marginTop: 8 }}>
        Schuljahre {state.school_years.map((y) => `${y}/${String(y + 1).slice(2)}`).join(' und ')}
        {st.last_run ? ` · zuletzt ${formatDateTime(st.last_run)}` : ''}
      </p>
      {st.last_error && <Alert kind="warning">Letzter automatischer Abruf fehlgeschlagen: {st.last_error}</Alert>}
      {result && (
        <div style={{ marginTop: 8 }}>
          <strong>
            {result.applied ? 'Übernommen' : 'Vorschau'}: {summaryText(result.data.counts)}
          </strong>
          {rows.length > 0 && (
            <div className="table-wrap">
              <table className="table table-compact">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Zeitraum</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((c) => (
                    <tr key={`${c.name}-${c.date_from}-${c.action}`}>
                      <td>{c.name}</td>
                      <td>{c.date_to === c.date_from ? formatDate(c.date_from) : `${formatDate(c.date_from)} – ${formatDate(c.date_to)}`}</td>
                      <td>{ACTION_LABELS[c.action]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

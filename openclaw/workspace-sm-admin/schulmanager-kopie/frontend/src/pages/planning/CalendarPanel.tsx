/**
 * Planung › „Zeitraster & Schuljahr“ (R3, Entwurf §8, §15.2 V4, Texte §15.5): Schule, Schuljahr und Wochenzählung,
 * Unterrichtstage Mo–So, Wochenübersicht 1 … Y, Zeitraster (Stunden, Pausen). „Wirkung anzeigen“ fragt
 * `POST /settings/calendar-preview`; eine 409-Bestätigung beim Speichern erscheint als Liste mit „Trotzdem
 * übernehmen“ (`?force=1`). Wochenangaben (Kurse, Sperrzeiten …) zählen die laufenden Wochen ab dem Schuljahresbeginn.
 *
 * Herausgelöst aus `SettingsPanels.tsx` (`SchoolSettingsPanel`), damit Spur D dort nur `WeightsPanel` bearbeitet; in
 * `SettingsPanels.tsx` bleibt der Einhängepunkt (Webhooks über `extra`). Der Zeitraster-Editor aus R4 hängt hier.
 */
import { useEffect, useId, useState, type ReactNode } from 'react';
import { settings as settingsApi } from '../../api/endpoints';
import type { BreakDef, CalendarPreview, Settings, WeekNumbering, YearStartMode } from '../../api/types';
import { useConfirmChanges } from '../../components/ConfirmChanges';
import { HelpText } from '../../components/Help';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { Alert, AsyncButton, ErrorBox, Field, Loading } from '../../components/ui';
import { useSchoolYear } from '../../components/WeekNav';
import { DayChips } from '../../components/WeekPatternInput';
import { PlanPeriodsPanel } from './PlanPeriodsPanel';
import { useUser } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { invalidate, useSettings } from '../../hooks/useCollection';
import { formatDate, mondayOf, todayISO, WEEKDAYS, weekdayIndex } from '../../lib/dates';
import { can } from '../../lib/permissions';
import { schoolDaysOf, schoolYearSpan, weekRangeText } from '../../lib/weeks';
import '../../components/weeks.css';

/** Felder, die `GET /settings` ggf. nur abgeleitet liefert (W3) – `SettingsIn` nimmt sie nicht an. */
const READ_ONLY_KEYS = ['school_year_end'] as const;

/**
 * Körper für `PUT /settings`: ohne abgeleitete Felder, `days` passend zu den Unterrichtstagen (Altaufrufer).
 */
export function settingsBody(d: Settings): Settings {
  const body = { ...d } as Settings & Record<string, unknown>;
  for (const k of READ_ONLY_KEYS) delete body[k];
  if (d.school_days?.length) body.days = Math.max(...d.school_days) + 1;
  return body;
}

/** Körper für die Vorschau (§15.3): nur die Kalenderfelder. */
export function previewBody(d: Settings): Partial<Settings> {
  return {
    week_numbering: d.week_numbering ?? 'iso',
    year_start_mode: d.year_start_mode ?? 'auto',
    school_year_start: d.school_year_start ?? '',
    school_days: d.school_days ?? [],
  };
}

/** Prüfung wie `SettingsIn` (Grenzen §14.6/§15.3); Texte §15.5. */
export function calendarErrors(d: Settings): string[] {
  const errs: string[] = [];
  if (!schoolDaysOf(d).length) errs.push('Bitte mindestens einen Unterrichtstag wählen.');
  return errs;
}

function useCalendarDraft() {
  const s = useSettings();
  const [draft, setDraft] = useState<Settings | null>(null);
  const [dirty, setDirty] = useState(false);
  useEffect(() => {
    if (s.data && !dirty) setDraft(structuredClone(s.data));
  }, [s.data, dirty]);
  const update = (fn: (d: Settings) => Settings) => {
    setDraft((d) => (d ? fn(d) : d));
    setDirty(true);
  };
  const reset = () => {
    setDirty(false);
    if (s.data) setDraft(structuredClone(s.data));
  };
  return { s, draft, dirty, update, reset, setDirty };
}

function int(v: string, lo: number, hi: number, fallback: number): number {
  const n = parseInt(v, 10);
  return Number.isFinite(n) ? Math.min(hi, Math.max(lo, n)) : fallback;
}

export function CalendarPanel({
  canEdit,
  extra,
}: {
  canEdit: boolean;
  /** weitere Abschnitte desselben Entwurfs (z. B. Webhooks aus `SettingsPanels.tsx`) */
  extra?: (draft: Settings, update: (fn: (d: Settings) => Settings) => void) => ReactNode;
}) {
  const id = useId();
  const toast = useToast();
  const user = useUser();
  const { s, draft, dirty, update, reset, setDirty } = useCalendarDraft();
  const [preview, setPreview] = useState<CalendarPreview | null>(null);
  const confirm = useConfirmChanges();
  const today = todayISO();
  const { year } = useSchoolYear(today, { enabled: !!s.data });
  useEffect(() => setPreview(null), [draft]);
  if (s.error) return <ErrorBox error={s.error} onRetry={s.reload} />;
  if (!draft) return <Loading />;

  const errors = calendarErrors(draft);
  const save = async () => {
    if (errors.length) {
      toast.warning('Bitte die Eingaben prüfen', errors);
      return;
    }
    try {
      const done = await confirm.run(async (force) => {
        await settingsApi.put(settingsBody(draft), { force });
        return true;
      });
      if (!done) return;
      toast.success('Einstellungen gespeichert');
      setDirty(false);
      invalidate('settings');
    } catch (e) {
      toast.error(e, 'Speichern');
    }
  };
  const showPreview = async () => {
    try {
      setPreview(await settingsApi.calendarPreview(previewBody(draft)));
    } catch (e) {
      toast.error(e, 'Wirkung anzeigen');
    }
  };

  const auto = (draft.year_start_mode ?? 'auto') === 'auto';
  const detected = year?.detected_start ?? '';
  const start = (auto && detected) || draft.school_year_start || draft.cycle_start || '';
  const savedStart = s.data?.school_year_start || s.data?.cycle_start || '';
  const span = start === savedStart && year ? { end: year.end, weeks: year.weeks_in_year } : schoolYearSpan(start);
  const setBreak = (i: number, b: Partial<BreakDef>) => update((d) => ({ ...d, breaks: d.breaks.map((x, j) => (j === i ? { ...x, ...b } : x)) }));
  const days = schoolDaysOf(draft);
  const currentMonday = mondayOf(today);

  return (
    <div className="stack">
      <section className="card">
        <h2>
          Schule{' '}
          <HelpTip label="Erklärung: Schule">
            Höchstzahlen für Klassenarbeiten je Woche und Tag stehen bei den Klassen. Die Vorgabe für Schule und Jahrgänge ändern Sie unter „Klausuren“, eigene Werte je Klasse im Klassen-Editor.
          </HelpTip>
        </h2>
        <div className="form-grid">
          <Field label="Name der Schule" htmlFor="st-name">
            <input id="st-name" type="text" value={draft.school_name} disabled={!canEdit} onChange={(e) => update((d) => ({ ...d, school_name: e.target.value }))} />
          </Field>
        </div>
      </section>

      <section className="card">
        <h2>Schuljahr</h2>
        <div className="form-grid">
          <Field
            label="Schuljahresbeginn"
            htmlFor="st-ymode"
            help="Automatisch: Das Schuljahr beginnt am ersten Schultag nach den Sommerferien (aus den Ferien der Schule). Eigener Schulstart: Sie tragen das Datum selbst ein."
          >
            <select id="st-ymode" value={draft.year_start_mode ?? 'auto'} disabled={!canEdit} onChange={(e) => update((d) => ({ ...d, year_start_mode: e.target.value as YearStartMode }))}>
              <option value="auto">Automatisch (nach den Sommerferien)</option>
              <option value="own">Eigener Schulstart</option>
            </select>
          </Field>
          <Field label="Beginn" htmlFor="st-ystart" help={auto ? 'Kommt aus den Sommerferien; Ferien anlegen oder importieren, dann erscheint das Datum hier.' : 'Das Datum des ersten Schultages. Ferienwochen zählen mit.'}>
            <input
              id="st-ystart"
              type="date"
              value={start}
              disabled={!canEdit || auto}
              onChange={(e) => update((d) => ({ ...d, school_year_start: e.target.value, year_start_mode: 'own' }))}
            />
            {auto && !detected && <span className="small muted">Noch keine Sommerferien gefunden – es gilt das bisherige Datum.</span>}
          </Field>
          <div className="field">
            <span className="field-label">
              <HelpText help="Ergibt sich aus dem Beginn des nächsten Schuljahres.">Ende</HelpText>
            </span>
            <span>{span ? `${WEEKDAYS[weekdayIndex(span.end)]}, ${formatDate(span.end)} · ${span.weeks} Wochen` : '–'}</span>
          </div>
          <Field label="Wochenzählung" htmlFor="st-numbering" help="Kalenderwochen: KW 1 ist die erste Woche des Jahres, die Zählung läuft über Neujahr weiter (…, KW 52, KW 1, …). Rhythmen wie „alle 2 Wochen ab KW 38“ laufen ohne Sprung durch.">
            <select
              id="st-numbering"
              value={draft.week_numbering ?? 'iso'}
              disabled={!canEdit}
              onChange={(e) => update((d) => ({ ...d, week_numbering: e.target.value as WeekNumbering }))}
            >
              <option value="iso">Kalenderwochen (KW)</option>
              <option value="school_year">Wochen ab Schuljahresbeginn</option>
            </select>
          </Field>
        </div>
        {(year?.warnings ?? []).map((w) => (
          <Alert key={w} kind="warning">
            {w}
          </Alert>
        ))}
      </section>

      <section className="card">
        <h2>
          <HelpText help="Gilt für alle Klassen ohne eigene Unterrichtstage.">Unterrichtstage</HelpText>
        </h2>
        <DayChips
          value={days}
          label="Unterrichtstage der Schule"
          disabled={!canEdit}
          onChange={(dd) => update((d) => ({ ...d, school_days: dd }))}
        />
      </section>

      <PlanPeriodsPanel canEdit={canEdit} canPlan={can(user, 'timetable.generate')} />

      {canEdit && (
        <section className="card stack-sm" aria-labelledby={`${id}-prev`}>
          <h2 id={`${id}-prev`}>Vorschau</h2>
          <div>
            <AsyncButton className="btn" onClick={showPreview} disabled={errors.length > 0}>
              <Icon name="eye" /> Wirkung anzeigen
            </AsyncButton>
          </div>
          {preview && (
            <div className="stack-sm" aria-live="polite">
              <p style={{ margin: 0 }}>
                Heute: {preview.today_before.week_text} → {preview.today_after.week_text}
              </p>
              {preview.warnings.map((w) => (
                <Alert key={w} kind="warning">
                  {w}
                </Alert>
              ))}
            </div>
          )}
        </section>
      )}

      <section className="card">
        <details className="disclosure">
          <summary>
            Wochenübersicht{year ? ` (${year.weeks_in_year} Wochen)` : ''}
          </summary>
          {year ? (
            <div className="table-wrap">
              <table className="week-table">
                <caption className="sr-only">Wochenübersicht des Schuljahres</caption>
                <thead>
                  <tr>
                    <th scope="col" className="num">
                      Woche
                    </th>
                    <th scope="col" className="num">
                      KW
                    </th>
                    <th scope="col">Zeitraum</th>
                    <th scope="col">Ferien</th>
                  </tr>
                </thead>
                <tbody>
                  {year.weeks.map((w) => (
                    <tr key={w.week_start} className={[w.holiday_week ? 'holiday' : '', w.week_start === currentMonday ? 'current' : ''].filter(Boolean).join(' ') || undefined}>
                      <td className="num">{w.week_no}</td>
                      <td className="num">{w.iso_week}</td>
                      <td>{weekRangeText(w.week_start, w.week_end)}</td>
                      <td>
                        {w.holiday_week ? <span className="badge badge-warning">{w.holidays[0] || 'Ferien'}</span> : w.holidays.length ? <span className="small">{w.holidays.join(', ')}</span> : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="small muted">Keine Wochen geladen.</p>
          )}
        </details>
      </section>

      <section className="card">
        <h2>Zeitraster</h2>
        <div className="form-grid">
          <Field label="Stunden pro Tag" htmlFor="st-periods">
            <input
              id="st-periods"
              type="number"
              min={1}
              max={16}
              value={draft.periods}
              disabled={!canEdit}
              onChange={(e) => {
                const k = int(e.target.value, 1, 16, 1);
                update((d) => ({ ...d, periods: k, period_times: Array.from({ length: k }, (_, i) => d.period_times[i] ?? '') }));
              }}
            />
          </Field>
          <Field
            label="Dauer einer Stunde (Minuten)"
            htmlFor="st-pmin"
            hint="Für Arbeitszeitfenster der Lehrkräfte und Kalender (eine Stunde zählt nur, wenn sie ganz im Fenster liegt)"
          >
            <input
              id="st-pmin"
              type="number"
              min={5}
              max={240}
              value={draft.period_minutes ?? 45}
              disabled={!canEdit}
              onChange={(e) => update((d) => ({ ...d, period_minutes: int(e.target.value, 5, 240, 45) }))}
            />
          </Field>
        </div>
        <div className="grid grid-4" style={{ marginTop: 12 }}>
          {Array.from({ length: draft.periods }, (_, i) => (
            <Field key={i} label={`${i + 1}. Stunde`} htmlFor={`st-pt-${i}`}>
              <input
                id={`st-pt-${i}`}
                type="time"
                value={draft.period_times[i] ?? ''}
                disabled={!canEdit}
                onChange={(e) => update((d) => ({ ...d, period_times: Array.from({ length: d.periods }, (_, j) => (j === i ? e.target.value : d.period_times[j] ?? '')) }))}
              />
            </Field>
          ))}
        </div>
        <h3 style={{ marginTop: 16 }}>
          <HelpText help="Pausen liegen nach der angegebenen Stunde; für jede Pause werden Aufsichten geplant.">Pausen</HelpText>
        </h3>
        {draft.breaks.map((b, i) => (
          <div key={i} className="row" style={{ marginTop: 8, alignItems: 'flex-end' }}>
            <Field label="Name" htmlFor={`br-n-${i}`} className="grow">
              <input id={`br-n-${i}`} type="text" value={b.name} disabled={!canEdit} onChange={(e) => setBreak(i, { name: e.target.value })} />
            </Field>
            <Field label="nach Stunde" htmlFor={`br-a-${i}`}>
              <input id={`br-a-${i}`} type="number" min={1} max={draft.periods} value={b.after + 1} disabled={!canEdit} onChange={(e) => setBreak(i, { after: Math.max(0, parseInt(e.target.value || '1', 10) - 1) })} />
            </Field>
            <Field label="Minuten" htmlFor={`br-m-${i}`}>
              <input id={`br-m-${i}`} type="number" min={5} max={90} value={b.minutes} disabled={!canEdit} onChange={(e) => setBreak(i, { minutes: parseInt(e.target.value || '0', 10) })} />
            </Field>
            {canEdit && (
              <button type="button" className="btn btn-ghost" onClick={() => update((d) => ({ ...d, breaks: d.breaks.filter((_, j) => j !== i) }))} aria-label={`Pause ${b.name} entfernen`}>
                <Icon name="trash" />
              </button>
            )}
          </div>
        ))}
        {canEdit && (
          <button type="button" className="btn btn-sm" style={{ marginTop: 8 }} onClick={() => update((d) => ({ ...d, breaks: [...d.breaks, { after: 1, name: 'Pause', minutes: 15 }] }))}>
            <Icon name="plus" /> Pause hinzufügen
          </button>
        )}
      </section>

      {extra?.(draft, update)}

      {errors.length > 0 && dirty && (
        <Alert kind="warning" title="Bitte die Eingaben prüfen">
          <ul>
            {errors.map((e) => (
              <li key={e}>{e}</li>
            ))}
          </ul>
        </Alert>
      )}
      {canEdit && (
        <div className="row-end" style={{ position: 'sticky', bottom: 0, background: 'var(--bg)', padding: '8px 0', zIndex: 5 }}>
          {dirty && <span className="small muted">Ungespeicherte Änderungen</span>}
          <button type="button" className="btn" onClick={reset} disabled={!dirty}>
            Verwerfen
          </button>
          <AsyncButton className="btn btn-primary" onClick={save} disabled={!dirty}>
            Speichern
          </AsyncButton>
        </div>
      )}
      {confirm.dialog}
    </div>
  );
}

import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { planning, settings as settingsApi } from '../../api/endpoints';
import type { PlanningReport, Settings, SubstitutionPolicy } from '../../api/types';
import { Icon } from '../../components/Icon';
import { Alert, AsyncButton, ErrorBox, Field, Loading } from '../../components/ui';
import { SubjectAbbr } from '../../components/Abbr';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { invalidate, useCollection, useSettings } from '../../hooks/useCollection';
import { HelpTip } from '../../components/HelpTip';
import { sortBy } from '../../lib/format';
import { APP_NAME } from '../../brand';
import { QUALITY_KEYS, STOCK_KEYS } from '../../lib/reportTiles';
import { ReportTiles } from './ReportTiles';
import { CalendarPanel } from './CalendarPanel';
import { useUser } from '../../context/AuthContext';
import { can } from '../../lib/permissions';
import { HolidayImportPanel } from './HolidayImportPanel';

// ---------------------------------------------------------------- Qualitätsbericht

export function ReportPanel() {
  const r = useApi<PlanningReport>(() => planning.report(), [], { live: ['timetable', 'courses', 'classes', 'teachers', 'rooms', 'settings'] });
  // `?detail=class_gaps` (z. B. aus dem Tab „Regeln“): die Liste hinter der Kennzahl gleich öffnen
  const [params] = useSearchParams();
  const openDetail = params.get('detail') ?? undefined;
  if (r.error) return <ErrorBox error={r.error} onRetry={r.reload} />;
  if (!r.data) return <Loading label="Bericht wird berechnet …" />;
  const d = r.data;
  const unplaced = Array.isArray(d.unplaced_hours) ? d.unplaced_hours : [];
  const overplaced = d.overplaced_hours ?? [];
  const gaps = sortBy(Object.entries(d.class_gaps ?? {}), ([, v]) => -v);
  return (
    <div className="stack">
      <div className="row-between">
        <p className="muted small" style={{ margin: 0 }}>
          Stand: Version {d.version ?? '–'}
        </p>
        <span className="row" style={{ gap: 4 }}>
          <button type="button" className="btn btn-sm" onClick={r.reload}>
            <Icon name="refresh" /> Kennzahlen aktualisieren
          </button>
          <HelpTip>Lädt die Kennzahlen neu und prüft den aktuellen Stundenplan. Es wird nichts am Plan geändert – einen neuen Plan erzeugt nur der Generator.</HelpTip>
        </span>
      </div>
      <h3 className="small muted" style={{ margin: 0 }}>
        Bestand
      </h3>
      <ReportTiles keys={STOCK_KEYS} stats={d.stats} ranges={d.ranges} />
      <h3 className="small muted" style={{ margin: 0 }}>
        Qualität des Stundenplans
      </h3>
      <ReportTiles keys={QUALITY_KEYS} stats={d.stats} ranges={d.ranges} initialOpen={openDetail} />
      {(d.conflicts?.length ?? 0) > 0 && (
        <Alert kind="error" title={`${d.conflicts?.length} Konflikte`}>
          <ul className="small">
            {d.conflicts?.slice(0, 50).map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </Alert>
      )}
      {d.warnings.length > 0 && (
        <div className="card">
          <h3>Hinweise</h3>
          <ul className="warning-list small">
            {d.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
      {(d.capacity_warnings?.length ?? 0) > 0 && (
        <div className="card">
          <h3>Kapazität (Lehrkräfte, Räume)</h3>
          <ul className="warning-list small">
            {d.capacity_warnings?.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
      <div className="grid grid-2">
        {unplaced.length > 0 && (
          <div className="card">
            <h3>Unverplante Stunden</h3>
            <div className="table-wrap" style={{ maxHeight: 360 }}>
              <table className="table table-compact">
                <thead>
                  <tr>
                    <th scope="col">Kurs</th>
                    <th scope="col">Woche</th>
                    <th scope="col" className="num">
                      fehlend
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {unplaced.map((u, i) => (
                    <tr key={i}>
                      <td>{u.label || u.course}</td>
                      <td>{u.weeks_text}</td>
                      <td className="num">{u.missing}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {overplaced.length > 0 && (
          <div className="card">
            <h3>Zu viel verplante Stunden</h3>
            <div className="table-wrap" style={{ maxHeight: 360 }}>
              <table className="table table-compact">
                <thead>
                  <tr>
                    <th scope="col">Kurs</th>
                    <th scope="col">Woche</th>
                    <th scope="col" className="num">
                      Soll
                    </th>
                    <th scope="col" className="num">
                      im Plan
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {overplaced.map((u, i) => (
                    <tr key={i}>
                      <td>{u.label || u.course}</td>
                      <td>{u.weeks_text}</td>
                      <td className="num">{u.hours}</td>
                      <td className="num">{u.placed}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {gaps.length > 0 && (
          <div className="card">
            <h3>
              Hohlstunden je Klasse <HelpTip>Durchschnitt je Schulwoche. Weicht ein Wert von einer ganzen Zahl ab, tritt die Lücke nur in manchen Wochen auf (Kurse im Rhythmus).</HelpTip>
            </h3>
            <div className="table-wrap" style={{ maxHeight: 360 }}>
              <table className="table table-compact">
                <thead>
                  <tr>
                    <th scope="col">Klasse</th>
                    <th scope="col" className="num">
                      Hohlstunden
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {gaps.map(([k, v]) => (
                    <tr key={k}>
                      <td>{k}</td>
                      <td className="num">{v}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {(d.open_parts?.length ?? 0) > 0 && (
          <div className="card">
            <h3>Kursteile ohne Lehrkraft ({d.open_parts?.length})</h3>
            <ul className="list-plain small" style={{ maxHeight: 360, overflowY: 'auto' }}>
              {d.open_parts?.map((p, i) => (
                <li key={i}>
                  {p.label} · Teil {p.part + 1} · <SubjectAbbr id={p.subject} />
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- Vertretungsregeln, Wegezeiten, Schule & Abwesenheit
// Die Prioritäten der Stundenplan-Optimierung (ehemals Gewichte, Doppelstunden, Auto-Neuplanung) stehen jetzt als
// Bausteine in `rules/RulesPanel.tsx` (Tab „Regeln“, docs/REGELN-UND-PRIORITAETEN.md).

/** Felder aus Erweiterung 2 (§9.1), die `api/types.ts` noch nicht kennt. */
type SelfServiceMode = 'approval' | 'direct';
type SettingsEx = Settings & { period_minutes?: number; teacher_self_service?: SelfServiceMode };
const SELF_SERVICE_TEXT: Record<SelfServiceMode, string> = {
  approval: 'als Antrag – die Stundenplanung bzw. Schulleitung genehmigt oder lehnt ab (empfohlen).',
  direct: 'sofort gültig – Änderungen werden direkt übernommen und nur protokolliert.',
};

const EDGE_TEXT: Record<SubstitutionPolicy['edge_strategy'], string> = {
  cancel: 'Randstunden entfallen – die Klasse beginnt später bzw. geht früher nach Hause.',
  substitute_if_qualified: 'Randstunden werden nur vertreten, wenn eine Fachlehrkraft frei ist – sonst Entfall.',
  substitute: 'Randstunden werden immer vertreten (kein Entfall).',
};
const MIDDLE_TEXT: Record<SubstitutionPolicy['middle_strategy'], string> = {
  shift_first: 'Lücken in der Tagesmitte zuerst durch Verlegen einer Randstunde der Klasse schließen, sonst Vertretung.',
  substitute_first: 'Lücken in der Tagesmitte zuerst durch Vertretung schließen, Verlegung nur als Ausweichlösung.',
};

function useSettingsDraft() {
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

function SaveBar({ dirty, onSave, onReset, canEdit }: { dirty: boolean; onSave: () => Promise<void>; onReset: () => void; canEdit: boolean }) {
  if (!canEdit) return null;
  return (
    <div className="row-end" style={{ position: 'sticky', bottom: 0, background: 'var(--bg)', padding: '8px 0', zIndex: 5 }}>
      {dirty && <span className="small muted">Ungespeicherte Änderungen</span>}
      <button type="button" className="btn" onClick={onReset} disabled={!dirty}>
        Verwerfen
      </button>
      <AsyncButton className="btn btn-primary" onClick={onSave} disabled={!dirty}>
        Speichern
      </AsyncButton>
    </div>
  );
}

export function WeightsPanel({ canEdit }: { canEdit: boolean }) {
  const toast = useToast();
  const { s, draft, dirty, update, reset, setDirty } = useSettingsDraft();
  const sites = useCollection('sites').data ?? [];
  if (s.error) return <ErrorBox error={s.error} onRetry={s.reload} />;
  if (!draft) return <Loading />;
  const travel = draft.site_travel ?? [];
  const minutesOf = (a: string, b: string) => travel.find((r) => (r.a === a && r.b === b) || (r.a === b && r.b === a))?.minutes;
  const setMinutes = (a: string, b: string, v: string) =>
    update((d) => {
      const rest = (d.site_travel ?? []).filter((r) => !((r.a === a && r.b === b) || (r.a === b && r.b === a)));
      return { ...d, site_travel: v === '' ? rest : [...rest, { a, b, minutes: Math.max(0, Math.min(240, parseInt(v, 10) || 0)) }] };
    });
  const p = draft.policy;
  const save = async () => {
    try {
      await settingsApi.put(draft);
      toast.success('Einstellungen gespeichert');
      setDirty(false);
      invalidate('settings');
    } catch (e) {
      toast.error(e, 'Speichern');
    }
  };
  return (
    <div className="stack">
      <p className="small" style={{ margin: 0 }}>
        <Link to="/planung/regeln">Prioritäten &amp; Regeln</Link>{' '}
        <HelpTip label="Erklärung: Prioritäten und Regeln">
          Prioritäten und Regeln für den Stundenplan (Hohlstunden, Hauptfächer, Doppelstunden, automatische Neuplanung) stellen Sie im Tab „Regeln“ ein.
        </HelpTip>
      </p>
      {sites.length > 1 && (
        <section className="card">
          <h2>Wegezeit je Standortpaar</h2>
          <fieldset className="stack-sm" style={{ marginTop: 12 }}>
            <legend>
              Wegezeit je Standortpaar (Minuten){' '}
              <HelpTip label="Erklärung: Wegezeit">
                Wie lange dauert der Weg zwischen zwei Standorten? Zwischen Unterricht an beiden Orten muss mindestens diese Pause liegen (inklusive Hofpausen und Freistunden). Ohne Eintrag gilt die Zahl freier Stunden aus dem Baustein „Standortwechsel vermeiden“ (Tab „Regeln“).
              </HelpTip>
            </legend>
            {sites.flatMap((a, i) =>
              sites.slice(i + 1).map((b) => (
                <Field key={`${a.id}-${b.id}`} label={`${a.name} ↔ ${b.name}`} htmlFor={`travel-${a.id}-${b.id}`}>
                  <input
                    id={`travel-${a.id}-${b.id}`}
                    type="number"
                    min={0}
                    max={240}
                    step={5}
                    value={minutesOf(a.id, b.id) ?? ''}
                    placeholder="nicht festgelegt"
                    disabled={!canEdit}
                    onChange={(e) => setMinutes(a.id, b.id, e.target.value)}
                  />
                </Field>
              )),
            )}
          </fieldset>
        </section>
      )}

      <section className="card">
        <h2>
          Regeln für die Vertretungsplanung{' '}
          <HelpTip label="Erklärung: Vertretungsregeln">
            Grundsatz: Unterricht entfällt nur am Rand des Schultags. Lücken in der Mitte werden durch Verlegung oder Vertretung geschlossen.
          </HelpTip>
        </h2>
        <div className="form-grid" style={{ marginTop: 12 }}>
          <Field label="Entfall erlaubt ab Klassenstufe" htmlFor="p-grade" hint="Jüngere Klassen werden immer vertreten oder betreut.">
            <input
              id="p-grade"
              type="number"
              min={1}
              max={13}
              value={p.cancel_min_grade}
              disabled={!canEdit}
              onChange={(e) => update((d) => ({ ...d, policy: { ...d.policy, cancel_min_grade: parseInt(e.target.value || '1', 10) } }))}
            />
          </Field>
          <Field label="Max. Vertretungen je Lehrkraft und Tag" htmlFor="p-max">
            <input
              id="p-max"
              type="number"
              min={0}
              max={8}
              value={p.max_subs_per_day}
              disabled={!canEdit}
              onChange={(e) => update((d) => ({ ...d, policy: { ...d.policy, max_subs_per_day: parseInt(e.target.value || '0', 10) } }))}
            />
          </Field>
          <Field
            label="Abwesende Lehrkräfte auf Monitor und Aushang"
            htmlFor="p-public-teachers"
            help="Gründe, Stunden und Fallzahlen erscheinen dort nie. Schüler und Eltern sehen abwesende Lehrkräfte in der App nicht."
          >
            <select
              id="p-public-teachers"
              value={draft.public_absent_teachers ?? 'short'}
              disabled={!canEdit}
              onChange={(e) => update((d) => ({ ...d, public_absent_teachers: e.target.value as NonNullable<Settings['public_absent_teachers']> }))}
            >
              <option value="short">nur Kürzel</option>
              <option value="name">Kürzel und Name</option>
              <option value="off">nicht anzeigen</option>
            </select>
          </Field>
        </div>
        <fieldset style={{ marginTop: 12 }}>
          <legend>Randstunden (erste/letzte Stunde des Tages)</legend>
          {(Object.keys(EDGE_TEXT) as SubstitutionPolicy['edge_strategy'][]).map((k) => (
            <label key={k} className="check" style={{ alignItems: 'flex-start', display: 'flex', marginBottom: 6 }}>
              <input
                type="radio"
                name="edge"
                checked={p.edge_strategy === k}
                disabled={!canEdit}
                onChange={() => update((d) => ({ ...d, policy: { ...d.policy, edge_strategy: k } }))}
                style={{ marginTop: 3 }}
              />
              <span>{EDGE_TEXT[k]}</span>
            </label>
          ))}
        </fieldset>
        <fieldset style={{ marginTop: 12 }}>
          <legend>Lücken in der Tagesmitte</legend>
          {(Object.keys(MIDDLE_TEXT) as SubstitutionPolicy['middle_strategy'][]).map((k) => (
            <label key={k} className="check" style={{ alignItems: 'flex-start', display: 'flex', marginBottom: 6 }}>
              <input
                type="radio"
                name="middle"
                checked={p.middle_strategy === k}
                disabled={!canEdit}
                onChange={() => update((d) => ({ ...d, policy: { ...d.policy, middle_strategy: k } }))}
                style={{ marginTop: 3 }}
              />
              <span>{MIDDLE_TEXT[k]}</span>
            </label>
          ))}
        </fieldset>
        <label className="check" style={{ marginTop: 12 }}>
          <input
            type="checkbox"
            checked={p.allow_unqualified}
            disabled={!canEdit}
            onChange={(e) => update((d) => ({ ...d, policy: { ...d.policy, allow_unqualified: e.target.checked } }))}
          />
          Betreuung durch fachfremde Lehrkräfte erlauben (wenn keine Fachlehrkraft frei ist)
        </label>
        <label className="check" style={{ marginTop: 8 }}>
          <input
            type="checkbox"
            checked={draft.substitution_confirm === true}
            disabled={!canEdit}
            onChange={(e) => update((d) => ({ ...d, substitution_confirm: e.target.checked }))}
          />{' '}
          Vertretungsvorschläge erst nach Freigabe aktiv{' '}
          <HelpTip label="Hilfe zum Bestätigungsmodus">
            Ist der Bestätigungsmodus an, berechnet das System die Vertretungen weiterhin automatisch, zeigt sie aber nur der Vertretungsplanung als „Vorschlag“. Erst
            nach „Freigeben“ sehen Lehrkräfte, Schüler, Eltern und Monitor die Vertretung und es gehen Benachrichtigungen raus. Ausfälle, Verlegungen und manuelle
            Entscheidungen sind davon nicht betroffen.
          </HelpTip>
        </label>
      </section>

      <section className="card">
        <h2>
          Lehrer-Selbstverwaltung{' '}
          <HelpTip label="Erklärung: Lehrer-Selbstverwaltung">
            Lehrkräfte pflegen Fächer, Klassen, Deputat und Arbeitszeiten (z. B. „erst ab 10:00“, „nur abends ab 16:00“) unter „Profil als Lehrkraft“. Arbeitszeiten werden beim Übernehmen zu harten Sperrzeiten.
          </HelpTip>
        </h2>
        <fieldset style={{ marginTop: 12 }}>
          <legend>Änderungen der Lehrkräfte</legend>
          {(Object.keys(SELF_SERVICE_TEXT) as SelfServiceMode[]).map((k) => (
            <label key={k} className="check" style={{ alignItems: 'flex-start', display: 'flex', marginBottom: 6 }}>
              <input
                type="radio"
                name="self-service"
                checked={((draft as SettingsEx).teacher_self_service ?? 'approval') === k}
                disabled={!canEdit}
                onChange={() => update((d) => ({ ...d, teacher_self_service: k }) as Settings)}
                style={{ marginTop: 3 }}
              />
              <span>{SELF_SERVICE_TEXT[k]}</span>
            </label>
          ))}
        </fieldset>
      </section>

      <section className="card">
        <h2>
          Krankmeldungen &amp; Atteste{' '}
          <HelpTip label="Erklärung: Krankmeldungen und Atteste">
            Eltern melden ihre Kinder krank, volljährige Schüler/innen sich selbst (Schalter „volljährig“ in der Benutzerverwaltung). Ab der eingestellten Zahl von Schultagen wird ein ärztliches Attest verlangt. Fehlt es, erscheint „Attest fehlt“ bei Familie, Klassenleitung und Sekretariat.
          </HelpTip>
        </h2>
        <Field
          label="Ärztliches Attest ab … Schultagen in Folge"
          htmlFor="st-sick-note"
          hint={`0 = keine Attestpflicht. Bei der Krankmeldung zeigt ${APP_NAME} sofort „Attest nötig“ bzw. „Unterschriebene Entschuldigung reicht“. Fehlt jemand bei einer Klausur, ist immer ein Attest nötig (Nachschreibtermine).`}
        >
          <input
            id="st-sick-note"
            type="number"
            min={0}
            max={30}
            value={draft.sick_note_after_days ?? 3}
            disabled={!canEdit}
            onChange={(e) => update((d) => ({ ...d, sick_note_after_days: Math.min(30, Math.max(0, parseInt(e.target.value || '0', 10))) }))}
          />
        </Field>
        <Field
          label="Fachlehrkräfte sehen"
          htmlFor="st-subject-view"
          help="Gründe, Status, Atteste und die meldende Person sehen beim Schulpersonal nur Klassenleitung, Sekretariat und Schulleitung. „Wer heute in meiner Stunde fehlt“ zeigt Fachlehrkräften nur Name und Stunde."
        >
          <select
            id="st-subject-view"
            value={draft.subject_teacher_absence_view ?? 'none'}
            disabled={!canEdit}
            onChange={(e) => update((d) => ({ ...d, subject_teacher_absence_view: e.target.value === 'presence' ? 'presence' : 'none' }))}
          >
            <option value="none">keine Krankmeldungen</option>
            <option value="presence">wer heute in meiner Stunde fehlt</option>
          </select>
        </Field>
        <div className="form-grid" style={{ marginTop: 12 }}>
          <Field
            label="Zulässige Fehlzeit je Fach (%)"
            htmlFor="st-abs-limit"
            help="Optional. Ist eine Grenze eingestellt, zeigt die Fehlzeiten-Übersicht je Fach eine Ampel (unter der Grenze, ab 80 % der Grenze „nahe dran“, überschritten) und wie viele Stunden noch fehlen dürfen. 0 = keine Grenze."
          >
            <input
              id="st-abs-limit"
              type="number"
              min={0}
              max={100}
              step={1}
              value={draft.absence_limit_percent ?? 0}
              disabled={!canEdit}
              onChange={(e) => update((d) => ({ ...d, absence_limit_percent: Math.min(100, Math.max(0, Number(e.target.value) || 0)) }))}
            />
          </Field>
          <Field label="Davon unentschuldigt (%)" htmlFor="st-abs-limit-un" hint="0 = keine eigene Grenze für unentschuldigte Fehlzeiten">
            <input
              id="st-abs-limit-un"
              type="number"
              min={0}
              max={100}
              step={1}
              value={draft.absence_limit_unexcused_percent ?? 0}
              disabled={!canEdit}
              onChange={(e) => update((d) => ({ ...d, absence_limit_unexcused_percent: Math.min(100, Math.max(0, Number(e.target.value) || 0)) }))}
            />
          </Field>
        </div>
        <div className="form-grid" style={{ marginTop: 12 }}>
          <Field label="Telefon für Krankmeldungen" htmlFor="st-sick-phone" hint="Wird Eltern und Schüler/innen beim Krankmelden und auf dem Formular angezeigt.">
            <input
              id="st-sick-phone"
              type="tel"
              maxLength={60}
              value={draft.sick_phone ?? ''}
              disabled={!canEdit}
              placeholder="z. B. 0221 12345-0"
              onChange={(e) => update((d) => ({ ...d, sick_phone: e.target.value }))}
            />
          </Field>
          <Field label="Erreichbar (Zeiten)" htmlFor="st-sick-hours" hint="z. B. „Mo–Fr 7:15–8:00 Uhr“">
            <input
              id="st-sick-hours"
              type="text"
              maxLength={120}
              value={draft.sick_phone_hours ?? ''}
              disabled={!canEdit}
              onChange={(e) => update((d) => ({ ...d, sick_phone_hours: e.target.value }))}
            />
          </Field>
        </div>
      </section>
      <section className="card">
        <h2>Kursräume</h2>
        <Field
          label="Papierkorb: Aufbewahrung in Tagen"
          htmlFor="st-trash-days"
          help="Gelöschtes Material, gelöschte Aufgaben und Ordner im Kursraum bleiben so lange wiederherstellbar und werden danach automatisch endgültig entfernt (inkl. Abgaben und Dateien). Standard 30 Tage."
        >
          <input
            id="st-trash-days"
            type="number"
            min={1}
            max={365}
            value={draft.trash_retention_days ?? 30}
            disabled={!canEdit}
            onChange={(e) => update((d) => ({ ...d, trash_retention_days: Math.min(365, Math.max(1, parseInt(e.target.value || '30', 10) || 30)) }))}
          />
        </Field>
      </section>
      <SaveBar dirty={dirty} onSave={save} onReset={reset} canEdit={canEdit} />
    </div>
  );
}

// ---------------------------------------------------------------- Zeitraster & Schuljahr

/**
 * Einhängepunkt (R3, Entwurf §15.2 V4): Schule, Schuljahr, Unterrichtstage, Wochenübersicht und
 * Zeitraster stehen in `CalendarPanel.tsx` (Spur A); hier bleiben nur die Webhooks als Zusatzabschnitt.
 */
export function SchoolSettingsPanel({ canEdit }: { canEdit: boolean }) {
  const user = useUser();
  return (
    <CalendarPanel
      canEdit={canEdit}
      extra={(draft, update) => (
        <>
          {can(user, 'masterdata.edit') && <HolidayImportPanel />}
          <WebhooksSection draft={draft} update={update} canEdit={canEdit} />
        </>
      )}
    />
  );
}

/**
 * Webhook = Schnittstelle für andere Programme (nur für Administration/IT, im Alltag nicht nötig). Bleibt eingeklappt
 * unter „Erweitert“; ohne Bearbeitungsrecht erscheint der Abschnitt nur, wenn Adressen eingetragen sind.
 */
function WebhooksSection({ draft, update, canEdit }: { draft: Settings; update: (fn: (d: Settings) => Settings) => void; canEdit: boolean }) {
  if (!canEdit && !draft.webhooks.length) return null;
  const count = draft.webhooks.filter(Boolean).length;
  return (
    <section className="card">
      <details className="disclosure">
        <summary>
          Erweitert: Vertretungsplan an andere Programme senden (Webhook){count ? ` · ${count} Adresse${count === 1 ? '' : 'n'}` : ''}
        </summary>
        <div className="stack-sm">
          <h3 className="small">
            Webhook-Adressen{' '}
            <HelpTip label="Erklärung: Webhook">
              Ändert sich der Vertretungsplan für heute oder morgen, schickt {APP_NAME} eine kurze Nachricht an die hier eingetragene Internetadresse. So kann ein anderes Programm sofort reagieren, zum Beispiel eine Schul-App, ein Infobildschirm oder ein Automatisierungsdienst (n8n, Zapier). Wenn Sie so etwas nicht nutzen, lassen Sie die Liste leer. Gesendet werden nur Änderungen am Vertretungsplan (Datum, hinzugefügte, geänderte und entfallene Einträge mit Klassen und Stunden), keine Schülerdaten. Die Adresse beginnt mit https:// und muss von diesem Server aus erreichbar sein. Jede Nachricht ist signiert (Header X-Schulmanager-Signature). Das gemeinsame Geheimnis trägt die Administration beim Betrieb des Servers ein (SM_WEBHOOK_SECRET).
            </HelpTip>
          </h3>
          {draft.webhooks.map((u, i) => (
            <div key={i} className="row" style={{ marginTop: 6 }}>
              <label className="sr-only" htmlFor={`wh-${i}`}>
                Adresse {i + 1}
              </label>
              <input
                id={`wh-${i}`}
                type="url"
                className="grow"
                value={u}
                disabled={!canEdit}
                onChange={(e) => update((d) => ({ ...d, webhooks: d.webhooks.map((x, j) => (j === i ? e.target.value : x)) }))}
                placeholder="https://beispiel.de/schulmanager-hook"
                style={{ flex: 1 }}
              />
              {canEdit && (
                <button type="button" className="btn btn-ghost" onClick={() => update((d) => ({ ...d, webhooks: d.webhooks.filter((_, j) => j !== i) }))} aria-label="Adresse entfernen">
                  <Icon name="trash" />
                </button>
              )}
            </div>
          ))}
          {canEdit && (
            <div>
              <button type="button" className="btn btn-sm" onClick={() => update((d) => ({ ...d, webhooks: [...d.webhooks, ''] }))}>
                <Icon name="plus" /> Adresse hinzufügen
              </button>
            </div>
          )}
        </div>
      </details>
    </section>
  );
}

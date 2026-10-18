/**
 * `/einrichtung` – Einrichtungs-Assistent einer neuen Schule: führt Schritt für Schritt von der Sicherung des
 * Administrationskontos über Schuldaten, Schuljahr und Ferien, Zeitraster, Import (SchILD, ASV, LUSD, Untis, CSV),
 * Stundentafeln und Stundenplan bis zu Konten, Rechten, E-Mail-Versand und optionaler Anmeldung über Schulkonto.
 * Der Stand je Schritt wird automatisch erkannt; Schritte lassen sich als erledigt vermerken oder überspringen, der
 * Fortschritt bleibt gespeichert (`PUT /setup/steps/{key}`), man kann jederzeit später weitermachen.
 */
import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { http } from '../api/client';
import { HelpTip } from '../components/HelpTip';
import { Icon } from '../components/Icon';
import { Alert, AsyncButton, ErrorBox, Field, Loading, ProgressBar } from '../components/ui';
import { useToast } from '../context/ToastContext';
import { useApi } from '../hooks/useApi';
import { useTitle } from '../hooks/misc';
import { IMPORT_ORDER, STEP_TITLES, importSummary, logoProblem, nextOpen, progress, type SetupStep } from './setupLogic';

interface SetupStatus {
  school_name: string;
  license: { state: string; enforced: boolean; message: string };
  counts: Record<string, number>;
  accounts: Record<string, number>;
  steps: SetupStep[];
  current: string | null;
  finished: boolean;
  ready_to_finish: boolean;
  empty: boolean;
  mode: string;
  mail: { smtp: boolean; dev_outbox: boolean };
  bundesland: string;
  profile: Profile & { has_logo: boolean };
}

interface Profile {
  school_type: string;
  state: string;
  street: string;
  zip: string;
  city: string;
  phone: string;
  email: string;
  website: string;
}

interface ProfileMeta {
  school_name: string;
  school_types: Record<string, string>;
  states: Record<string, string>;
}

const n = (c: Record<string, number>, k: string) => c[k] ?? 0;

function LinkButton({ to, children, primary }: { to: string; children: ReactNode; primary?: boolean }) {
  return (
    <Link className={primary ? 'btn btn-primary' : 'btn btn-sm'} to={to}>
      {children}
    </Link>
  );
}

function Step({
  step,
  n: num,
  open,
  onToggle,
  onMark,
  help,
  children,
}: {
  step: SetupStep;
  n: number;
  open: boolean;
  onToggle: () => void;
  onMark: (state: 'done' | 'skipped' | 'open') => Promise<void>;
  help: ReactNode;
  children: ReactNode;
}) {
  const state = step.done ? 'erledigt' : step.skipped ? 'übersprungen' : 'offen';
  const badge = step.done ? 'badge-success' : step.skipped ? 'badge-info' : 'badge-warning';
  return (
    <section className={`card stack-sm setup-step${step.done ? ' done' : ''}`} aria-labelledby={`setup-${step.key}`}>
      <div className="row" style={{ gap: 10 }}>
        <span className={`setup-num${step.done ? ' done' : ''}`} aria-hidden="true">
          {step.done ? <Icon name="check" /> : num}
        </span>
        <h2 id={`setup-${step.key}`} style={{ margin: 0, flex: 1 }}>
          <button type="button" aria-expanded={open} onClick={onToggle} style={{ font: 'inherit', background: 'none', border: 0, padding: 0, color: 'inherit', cursor: 'pointer', textAlign: 'left' }}>
            {STEP_TITLES[step.key] ?? step.key}
          </button>{' '}
          <HelpTip>{help}</HelpTip>
        </h2>
        <span className={`badge ${badge}`}>{state}</span>
      </div>
      {open && (
        <>
          {children}
          <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
            {!step.done && !step.auto && (
              <AsyncButton className="btn btn-sm" onClick={() => onMark('done')}>
                <Icon name="check" /> Als erledigt vermerken
              </AsyncButton>
            )}
            {!step.done && !step.skipped && (
              <AsyncButton className="btn btn-ghost btn-sm" onClick={() => onMark('skipped')}>
                Überspringen
              </AsyncButton>
            )}
            {(step.skipped || (step.done && step.marked === 'done')) && (
              <AsyncButton className="btn btn-ghost btn-sm" onClick={() => onMark('open')}>
                Wieder öffnen
              </AsyncButton>
            )}
          </div>
        </>
      )}
    </section>
  );
}

function ProfileForm({ initial, onSaved }: { initial: Profile & { has_logo: boolean }; onSaved: () => void }) {
  const toast = useToast();
  const meta = useApi((signal) => http.get<ProfileMeta>('/setup/profile', undefined, { signal }), []);
  const [form, setForm] = useState<Profile & { school_name: string }>({ ...initial, school_name: '' });
  const [logo, setLogo] = useState<string | null | undefined>(undefined); // undefined = unverändert, '' = entfernen
  const file = useRef<HTMLInputElement>(null);
  const loaded = useRef(false);
  useEffect(() => {
    if (meta.data && !loaded.current) {
      loaded.current = true;
      setForm({ ...initial, school_name: meta.data.school_name === 'Meine Schule' ? '' : meta.data.school_name });
    }
  }, [meta.data, initial]);
  if (!meta.data) return meta.error ? <ErrorBox error={meta.error} onRetry={meta.reload} /> : <Loading />;
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const pick = (f: File | undefined) => {
    if (!f) return;
    const problem = logoProblem(f);
    if (problem) {
      toast.error(problem, 'Logo');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => setLogo(String(reader.result));
    reader.readAsDataURL(f);
  };
  const logoShown = logo === undefined ? initial.has_logo : !!logo;
  return (
    <form
      className="stack-sm"
      onSubmit={(e) => {
        e.preventDefault();
      }}
    >
      <div className="form-grid">
        <Field label="Name der Schule" htmlFor="sp-name">
          <input id="sp-name" value={form.school_name} maxLength={200} onChange={set('school_name')} />
        </Field>
        <Field label="Schulform" htmlFor="sp-type">
          <select id="sp-type" value={form.school_type} onChange={set('school_type')}>
            <option value="">bitte wählen</option>
            {Object.entries(meta.data.school_types).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Bundesland" htmlFor="sp-state" help="Bestimmt die Schulferien und Feiertage, die der Assistent übernimmt.">
          <select id="sp-state" value={form.state} onChange={set('state')}>
            <option value="">bitte wählen</option>
            {Object.entries(meta.data.states).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Straße und Hausnummer" htmlFor="sp-street">
          <input id="sp-street" value={form.street} maxLength={200} autoComplete="street-address" onChange={set('street')} />
        </Field>
        <Field label="PLZ" htmlFor="sp-zip">
          <input id="sp-zip" value={form.zip} maxLength={10} inputMode="numeric" autoComplete="postal-code" onChange={set('zip')} />
        </Field>
        <Field label="Ort" htmlFor="sp-city">
          <input id="sp-city" value={form.city} maxLength={100} autoComplete="address-level2" onChange={set('city')} />
        </Field>
        <Field label="Telefon" htmlFor="sp-phone">
          <input id="sp-phone" type="tel" value={form.phone} maxLength={40} onChange={set('phone')} />
        </Field>
        <Field label="E-Mail der Schule" htmlFor="sp-email">
          <input id="sp-email" type="email" value={form.email} maxLength={200} onChange={set('email')} />
        </Field>
        <Field label="Webseite" htmlFor="sp-web" hint="mit https://" hintInline>
          <input id="sp-web" type="url" value={form.website} maxLength={200} onChange={set('website')} />
        </Field>
        <Field label="Logo" htmlFor="sp-logo" help="PNG oder JPEG, höchstens 300 kB. Erscheint später auf Anmeldeseite und Briefen.">
          <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
            {logo ? <img src={logo} alt="Vorschau des Logos" style={{ maxHeight: 48, maxWidth: 120 }} /> : null}
            {logo === undefined && initial.has_logo ? <img src="/api/v1/school-logo" alt="Aktuelles Logo" style={{ maxHeight: 48, maxWidth: 120 }} /> : null}
            <input id="sp-logo" ref={file} type="file" accept="image/png,image/jpeg" onChange={(e) => pick(e.target.files?.[0])} />
            {logoShown && (
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => { setLogo(''); if (file.current) file.current.value = ''; }}>
                Logo entfernen
              </button>
            )}
          </div>
        </Field>
      </div>
      <div>
        <AsyncButton
          className="btn btn-primary"
          disabled={!form.school_name.trim()}
          onClick={async () => {
            const body: Record<string, unknown> = { ...form, school_name: form.school_name.trim() };
            if (logo !== undefined) body.logo = logo;
            await http.put('/setup/profile', body);
            toast.success('Schuldaten gespeichert');
            setLogo(undefined);
            onSaved();
          }}
        >
          Speichern
        </AsyncButton>
      </div>
    </form>
  );
}

function HolidayImport({ state, bundesland, onDone }: { state: string; bundesland: string; onDone: () => void }) {
  const toast = useToast();
  return (
    <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
      <AsyncButton
        className="btn"
        disabled={!state}
        title={state ? undefined : 'Zuerst das Bundesland bei den Schuldaten wählen'}
        onClick={async () => {
          try {
            const r = await http.post<{ counts?: Record<string, number> }>('/setup/holidays');
            const c = r.counts ?? {};
            const total = Object.values(c).reduce((a, b) => a + (typeof b === 'number' ? b : 0), 0);
            toast.success(total ? `Ferien und Feiertage für ${bundesland} übernommen (${total} Einträge)` : 'Ferien sind bereits aktuell');
            onDone();
          } catch (e) {
            toast.error(e, 'Ferien-Import');
          }
        }}
      >
        <Icon name="download" /> Ferien und Feiertage{bundesland ? ` für ${bundesland}` : ''} übernehmen
      </AsyncButton>
    </div>
  );
}

function TestMail({ smtp }: { smtp: boolean }) {
  const toast = useToast();
  const [to, setTo] = useState('');
  const [result, setResult] = useState<{ ok: boolean; error: string } | null>(null);
  if (!smtp) return null;
  return (
    <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
      <input aria-label="Empfängeradresse für die Testmail" type="email" value={to} placeholder="adresse@schule.de" style={{ flex: '1 1 240px' }} onChange={(e) => setTo(e.target.value)} />
      <AsyncButton
        className="btn"
        disabled={!to.includes('@')}
        onClick={async () => {
          try {
            const r = await http.post<{ ok: boolean; error: string }>('/setup/test-mail', { to });
            setResult(r);
            if (r.ok) toast.success('Testmail verschickt');
          } catch (e) {
            toast.error(e, 'Testmail');
          }
        }}
      >
        Testmail senden
      </AsyncButton>
      {result && !result.ok && <span className="error-text">{result.error}</span>}
    </div>
  );
}

export default function SetupPage() {
  useTitle('Schule einrichten');
  const toast = useToast();
  const q = useApi((signal) => http.get<SetupStatus>('/setup/status', undefined, { signal }), [], {
    live: ['settings', 'teachers', 'classes', 'students', 'rooms', 'subjects', 'courses', 'timetable', 'holidays'],
  });
  const st = q.data;
  const [open, setOpen] = useState<string | null>(null);
  const initialised = useRef(false);
  useEffect(() => {
    if (st && !initialised.current) {
      initialised.current = true;
      setOpen(st.current);
    }
  }, [st]);

  const mark = (key: string) => async (state: 'done' | 'skipped' | 'open') => {
    await http.put(`/setup/steps/${key}`, { state });
    q.reload();
    if (state !== 'open' && st) setOpen(nextOpen(st.steps.map((s) => (s.key === key ? { ...s, done: state === 'done', skipped: state === 'skipped' } : s)), key));
  };

  const c = st?.counts ?? {};
  const prog = st ? progress(st.steps) : null;
  const stepOf = (k: string) => st!.steps.find((s) => s.key === k)!;
  const idx = (k: string) => (st ? st.steps.findIndex((s) => s.key === k) + 1 : 0);
  const toggle = (k: string) => () => setOpen((o) => (o === k ? null : k));

  const wrap = (key: string, help: ReactNode, body: ReactNode) =>
    st && (
      <Step key={key} step={stepOf(key)} n={idx(key)} open={open === key} onToggle={toggle(key)} onMark={mark(key)} help={help}>
        {body}
      </Step>
    );

  return (
    <div className="page page-narrow stack">
      <div className="page-head">
        <h1>
          Schule einrichten{' '}
          <HelpTip>Der Assistent zeigt, was für den Start noch fehlt. Jeder Schritt führt zur passenden Seite; erledigte Schritte erkennt er selbst. Sie können Schritte überspringen und jederzeit später weitermachen.</HelpTip>
        </h1>
        {prog && (
          <span className="badge">
            {prog.done} von {prog.total} erledigt
          </span>
        )}
      </div>
      {prog && <ProgressBar value={prog.percent / 100} label="Fortschritt der Einrichtung" />}
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!st && !q.error && <Loading />}
      {st && (
        <>
          {wrap('admin', 'Das Administrationskonto hat weitreichende Rechte. Ein zweiter Faktor (Authenticator-App) schützt es auch dann, wenn das Passwort bekannt wird.', (
            <>
              <p className="small" style={{ margin: 0 }}>
                {stepOf('admin').done ? 'Zwei-Faktor-Anmeldung ist eingerichtet.' : 'Ihr Passwort ist gesetzt. Richten Sie zusätzlich die Zwei-Faktor-Anmeldung ein.'}
              </p>
              <div>
                <LinkButton to="/profil">
                  <Icon name="lock" /> Zwei-Faktor einrichten
                </LinkButton>
              </div>
            </>
          ))}
          {wrap('lizenz', 'Den Lizenzschlüssel erhalten Sie vom Anbieter. Dieser Server fragt täglich beim Anbieter nach; ohne gültige Lizenz ist die Anwendung gesperrt, vor dem Ablauf des Abos erinnert sie Sie, danach gibt es eine Kulanzzeit zum Lesen.', (
            <>
              <p className="small" style={{ margin: 0 }}>
                {!st.license.enforced ? 'Für diese Instanz ist keine Lizenzprüfung aktiv.' : st.license.state === 'valid' || st.license.state === 'grace' ? 'Lizenz gültig.' : st.license.message || 'Noch keine Lizenz eingespielt.'}
              </p>
              <div>
                <LinkButton to="/lizenz">
                  <Icon name="lock" /> Lizenz ansehen oder neu eingeben
                </LinkButton>
              </div>
            </>
          ))}
          {wrap('schule', 'Name, Schulform und Bundesland brauchen der Ferien-Import und die Briefe. Standorte sind Gebäude oder Außenstellen – eine Schule hat mindestens einen.', (
            <>
              <ProfileForm initial={st.profile} onSaved={q.reload} />
              <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
                <LinkButton to="/stammdaten/sites">Standorte ({n(c, 'sites')})</LinkButton>
              </div>
            </>
          ))}
          {wrap('schuljahr', 'Schuljahresbeginn und Ferien bestimmen die Wochenzählung und die unterrichtsfreien Tage. Die Ferien kommen aus einer öffentlichen Quelle und lassen sich danach von Hand ergänzen.', (
            <>
              <HolidayImport state={st.profile.state} bundesland={st.bundesland} onDone={q.reload} />
              <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
                <LinkButton to="/planung/zeitraster">Schuljahr und Kalender</LinkButton>
                <LinkButton to="/stammdaten/holidays">Ferien und Feiertage ({n(c, 'holidays')})</LinkButton>
              </div>
            </>
          ))}
          {wrap('zeitraster', 'Anfangszeiten, Länge der Stunden und Pausen. Der Assistent kann nicht erkennen, ob das Raster zur Schule passt – vermerken Sie den Schritt nach der Prüfung als erledigt.', (
            <div>
              <LinkButton to="/planung/zeitraster">
                <Icon name="clock" /> Zeitraster prüfen
              </LinkButton>
            </div>
          ))}
          {wrap('stammdaten', 'Am schnellsten per Import aus SchILD-NRW, ASV (Bayern, Baden-Württemberg), LUSD (Hessen), Untis (GPU-Dateien) oder CSV. Reihenfolge: Fächer, Räume, Klassen, Lehrkräfte, danach Schüler/innen. Mit „Probelauf“ prüfen Sie jede Datei vorher.', (
            <>
              <p className="small" style={{ margin: 0 }}>
                {importSummary(c)}
              </p>
              <div>
                <LinkButton to="/daten" primary>
                  <Icon name="transfer" /> Import (SchILD, ASV, LUSD, Untis, CSV)
                </LinkButton>
              </div>
              <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
                {IMPORT_ORDER.filter((i) => i.key !== 'students').map((i) => (
                  <LinkButton key={i.key} to={`/stammdaten/${i.key}`}>
                    {i.label} ({n(c, i.key)})
                  </LinkButton>
                ))}
              </div>
            </>
          ))}
          {wrap('schueler', 'Per Import oder einzeln in den Stammdaten. Die Klassen müssen vorher angelegt sein. Eltern bekommen ihre Konten später je Kind.', (
            <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
              <LinkButton to="/daten" primary>
                <Icon name="transfer" /> Schüler/innen importieren
              </LinkButton>
              <LinkButton to="/stammdaten/students">Schüler/innen ({n(c, 'students')})</LinkButton>
            </div>
          ))}
          {wrap('unterricht', 'Stundentafeln legen fest, wie viele Stunden welches Fach je Jahrgang oder Klasse unterrichtet wird. Daraus entstehen die Kurse, denen Sie Lehrkräfte zuweisen.', (
            <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
              <LinkButton to="/planung/stundentafeln">Stundentafeln ({n(c, 'curricula')})</LinkButton>
              <LinkButton to="/planung/kurse">Kurse ({n(c, 'courses')})</LinkButton>
            </div>
          ))}
          {wrap('stundenplan', 'Der Generator verteilt alle Stunden ohne Doppelbelegung. Ein importierter Untis-Plan kann auch direkt übernommen werden.', (
            <div>
              <LinkButton to="/planung/generator">Stundenplan erzeugen ({n(c, 'lessons')} Stunden)</LinkButton>
            </div>
          ))}
          {wrap('konten', 'Konten für Lehrkräfte, Schüler/innen und Eltern auf einmal anlegen; die Startpasswörter stehen auf den Zugangsbriefen (Druck oder PDF).', (
            <>
              <p className="small" style={{ margin: 0 }}>
                {Object.entries(st.accounts)
                  .map(([role, count]) => `${role}: ${count}`)
                  .join(' · ') || 'Noch keine Konten.'}
              </p>
              <div className="row" style={{ flexWrap: 'wrap', gap: 8 }}>
                <LinkButton to="/benutzer">
                  <Icon name="users" /> Konten anlegen
                </LinkButton>
              </div>
            </>
          ))}
          {wrap('rechte', 'Wer in Ihrer Schule was sehen und tun darf: Lehrkraft, Klassenleitung, Abteilungsleitung, Sekretariat, Schulleitung, Hausmeister/in, Schulbegleitung. Die Standardwerte passen für die meisten Schulen.', (
            <div>
              <LinkButton to="/rechte">
                <Icon name="lock" /> Rollen und Rechte prüfen
              </LinkButton>
            </div>
          ))}
          {wrap('mail', 'Für „Passwort vergessen“, Benachrichtigungen und Briefe per E-Mail braucht die Installation einen Mailserver (SMTP). Er wird in der Konfiguration der Installation eingetragen, nicht hier.', (
            <>
              {st.mail.dev_outbox ? (
                <Alert kind="warning">Test-Postausgang aktiv: Mails werden nicht zugestellt.</Alert>
              ) : st.mail.smtp ? (
                <p className="small" style={{ margin: 0 }}>
                  SMTP ist eingerichtet.
                </p>
              ) : (
                <Alert kind="warning" title="Kein Mailserver eingerichtet">
                  Tragen Sie SM_SMTP_HOST und SM_SMTP_FROM in der Konfiguration ein (siehe Installationsanleitung).
                </Alert>
              )}
              <TestMail smtp={st.mail.smtp} />
            </>
          ))}
          {wrap('sso', 'Lehrkräfte und Schüler/innen können sich mit dem vorhandenen Schulkonto (Microsoft, Google, Apple oder eigener Anmeldedienst) anmelden. Das ist freiwillig und lässt sich später einrichten.', (
            <div>
              <LinkButton to="/anmeldedienste">
                <Icon name="key" /> Anmeldedienste einrichten
              </LinkButton>
            </div>
          ))}
          <section className="card stack-sm">
            {st.finished ? (
              <>
                <p style={{ margin: 0 }}>Die Einrichtung ist abgeschlossen. Der Hinweis im Kopf der Seite ist ausgeblendet.</p>
                <div>
                  <AsyncButton className="btn btn-sm" onClick={async () => { await http.del('/setup/finish'); q.reload(); }}>
                    Assistenten wieder öffnen
                  </AsyncButton>
                </div>
              </>
            ) : (
              <>
                <p className="small" style={{ margin: 0 }}>
                  {st.ready_to_finish ? 'Alle Schritte sind erledigt oder übersprungen.' : 'Es sind noch Schritte offen. Sie können den Assistenten trotzdem beenden und später wieder öffnen.'}
                </p>
                <div>
                  <AsyncButton
                    className="btn btn-primary"
                    onClick={async () => {
                      await http.post('/setup/finish');
                      toast.success('Einrichtung abgeschlossen');
                      q.reload();
                    }}
                  >
                    <Icon name="check" /> Einrichtung abschließen
                  </AsyncButton>
                </div>
              </>
            )}
          </section>
        </>
      )}
    </div>
  );
}

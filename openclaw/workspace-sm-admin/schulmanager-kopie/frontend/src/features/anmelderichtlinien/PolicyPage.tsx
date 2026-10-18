/**
 * Verwaltungsseite „Anmelde-Richtlinien“ (`/anmelde-richtlinien`, Recht `login_policy.manage`, §11.5):
 * Bereiche Standard · Rollen · Jahrgänge · Klassen (Zielgruppe Alle/Schüler/innen/Eltern) · Personen, Regel-Editor je
 * Feld „erben“ oder festlegen, Vorschau „Was gilt für …?“ und Bericht „Wer hat noch nicht verbunden?“.
 */
import { useId, useMemo, useState } from 'react';
import { HelpTip } from '../../components/HelpTip';
import { users as usersApi } from '../../api/endpoints';
import type { ManagedUser } from '../../api/types';
import { Icon } from '../../components/Icon';
import { Alert, Empty, ErrorBox, Field, Loading, SegmentedControl, Tabs } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { useDebounced, useStoredState, useTitle } from '../../hooks/misc';
import { formatDateTime } from '../../lib/dates';
import { plural } from '../../lib/format';
import { ROLE_LABELS } from '../../lib/permissions';
import { resetApi } from '../konto/api';
import { policyApi } from './api';
import { AUDIENCE_LABELS, METHOD_LABELS, effectiveRows, filterClasses, indexRules, listText, ruleKey, summarizeRule } from './logic';
import { RuleEditor, type EditTarget } from './RuleEditor';
import type { Audience, EffectiveResponse, PoliciesResponse, PolicyRule } from './types';
import './anmelderichtlinien.css';

type Area = 'standard' | 'rollen' | 'jahrgaenge' | 'klassen' | 'personen' | 'vorschau' | 'bericht';
const AUDIENCES: Audience[] = ['alle', 'schueler', 'eltern'];

function roleLabel(role: string): string {
  return (ROLE_LABELS as Record<string, string>)[role] ?? role;
}

// =================================================================== Bausteine
function TargetRow({
  target,
  rule,
  onEdit,
  locked,
}: {
  target: EditTarget;
  rule: PolicyRule | undefined;
  onEdit: (t: EditTarget) => void;
  locked?: string;
}) {
  const lines = summarizeRule(rule);
  return (
    <li className="ar-row">
      <div className="ar-row-main">
        <div className="ar-row-title">
          <strong>{target.label}</strong>
          {rule ? <span className="badge badge-primary">eigene Regel</span> : <span className="badge">erbt alles</span>}
          {rule?.orphan && <span className="badge badge-warning">nicht mehr vorhanden</span>}
        </div>
        {lines.length > 0 && (
          <ul className="ar-summary small">
            {lines.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        )}
        {rule?.note && <p className="small muted ar-note">„{rule.note}“</p>}
        {rule?.updated_at && (
          <p className="small muted">
            Geändert {formatDateTime(rule.updated_at)}
            {rule.updated_by?.name ? ` von ${rule.updated_by.name}` : ''}
          </p>
        )}
      </div>
      <button
        type="button"
        className="btn btn-sm"
        onClick={() => onEdit(target)}
        disabled={!!locked}
        title={locked}
        aria-label={`${rule ? 'Regel bearbeiten' : 'Regel festlegen'}: ${target.label}`}
      >
        <Icon name={locked ? 'lock' : 'edit'} /> {rule ? 'Bearbeiten' : 'Festlegen'}
      </button>
      {locked && <p className="small muted ar-locked">{locked}</p>}
    </li>
  );
}

function AudienceGroup({
  title,
  scope,
  refId,
  grade,
  rules,
  onEdit,
  extra,
}: {
  title: string;
  scope: 'grade' | 'class';
  refId: string;
  grade?: string;
  rules: Map<string, PolicyRule>;
  onEdit: (t: EditTarget) => void;
  extra?: string;
}) {
  const own = AUDIENCES.map((a) => rules.get(ruleKey({ scope, ref: refId, audience: a }))).filter(Boolean).length;
  return (
    <details className="ar-group">
      <summary>
        <span className="ar-group-title">{title}</span>
        {extra && <span className="small muted">{extra}</span>}
        {own > 0 ? <span className="badge badge-primary">{own === 1 ? '1 Regel' : `${own} Regeln`}</span> : <span className="badge">erbt</span>}
      </summary>
      <ul className="ar-rows">
        {AUDIENCES.map((a) => (
          <TargetRow
            key={a}
            target={{ scope, ref: refId, audience: a, grade, label: a === 'alle' ? title : `${title} · ${AUDIENCE_LABELS[a]}` }}
            rule={rules.get(ruleKey({ scope, ref: refId, audience: a }))}
            onEdit={onEdit}
          />
        ))}
      </ul>
    </details>
  );
}

function PersonSearch({ onPick, label, canAdmins }: { onPick: (u: ManagedUser) => void; label: string; canAdmins: boolean }) {
  const id = useId();
  const [q, setQ] = useState('');
  const debounced = useDebounced(q.trim(), 300);
  const result = useApi(() => usersApi.list({ q: debounced, limit: 20 }), [debounced], {
    enabled: debounced.length >= 2,
  });
  return (
    <div className="stack ar-search">
      <Field label={label} htmlFor={id} hint="Name oder Benutzername, mindestens 2 Zeichen">
        <input id={id} type="search" value={q} onChange={(e) => setQ(e.target.value)} autoComplete="off" />
      </Field>
      {debounced.length >= 2 && (
        <div aria-live="polite">
          {result.initialLoading ? (
            <Loading />
          ) : result.error ? (
            <ErrorBox error={result.error} onRetry={result.reload} />
          ) : (result.data ?? []).length === 0 ? (
            <p className="small muted">Keine Treffer.</p>
          ) : (
            <ul className="ar-people">
              {(result.data ?? []).map((u) => {
                const locked = u.role === 'admin' && !canAdmins;
                return (
                  <li key={u.id}>
                    <button type="button" className="ar-person" onClick={() => onPick(u)} disabled={locked}>
                      <span className="ar-person-name">{u.display_name || u.username}</span>
                      <span className="small muted">
                        {u.username} · {roleLabel(u.role)}
                        {u.class ? ` · Klasse ${u.class}` : ''}
                        {locked ? ' · nur durch die Administration' : ''}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function EffectiveTable({ data }: { data: EffectiveResponse }) {
  const rows = effectiveRows(data.policy);
  return (
    <div className="stack">
      <div className="table-wrap">
        <table className="ar-table">
          <caption className="sr-only">Wirksame Anmelde-Richtlinie</caption>
          <thead>
            <tr>
              <th scope="col">Einstellung</th>
              <th scope="col">Gilt</th>
              <th scope="col">Herkunft</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.field}>
                <th scope="row">{r.label}</th>
                <td>{r.value}</td>
                <td className="muted">{r.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data.target.kind === 'user' && (
        <ul className="ar-facts small">
          {data.target.students.length > 0 && (
            <li>
              <span className="muted">Gehört zu:</span>{' '}
              {data.target.students.map((s) => `${s.name}${s.class ? ` (Klasse ${s.class.name})` : ''}`).join(', ')}
            </li>
          )}
          <li>
            <span className="muted">Verbunden:</span> {listText(data.linked ?? [], METHOD_LABELS)}
          </li>
          <li>
            <span className="muted">Fehlt noch:</span>{' '}
            {data.missing_links?.length ? <strong>{listText(data.missing_links, METHOD_LABELS)}</strong> : 'nichts'}
          </li>
          <li>
            <span className="muted">Anmeldung mit Passwort:</span>{' '}
            {data.password_login === 'ok' ? 'erlaubt' : data.password_login === 'setup' ? 'nur zur Ersteinrichtung (Konten verbinden)' : 'nicht erlaubt'}
          </li>
        </ul>
      )}
    </div>
  );
}

// =================================================================== Bereiche
function PreviewArea({ data }: { data: PoliciesResponse }) {
  const [mode, setMode] = useState<'person' | 'klasse' | 'rolle'>('klasse');
  const [person, setPerson] = useState<ManagedUser | null>(null);
  const [classId, setClassId] = useState(data.options.classes[0]?.id ?? '');
  const [audience, setAudience] = useState<'schueler' | 'eltern'>('schueler');
  const [role, setRole] = useState('lehrer');
  const classSel = useId();
  const roleSel = useId();
  const result = useApi(
    (signal) =>
      mode === 'person'
        ? policyApi.effectiveUser(Number(person?.id), signal)
        : mode === 'klasse'
          ? policyApi.effectiveGroup({ class_id: classId, audience }, signal)
          : policyApi.effectiveGroup({ role }, signal),
    [mode, person?.id, classId, audience, role, data],
    { enabled: mode !== 'person' ? (mode === 'klasse' ? !!classId : true) : !!person },
  );
  return (
    <section className="card stack" aria-labelledby="ar-preview-h">
      <h2 id="ar-preview-h">
        Was gilt für …?
        <HelpTip>Zeigt die wirksamen Einstellungen und woher jede einzelne stammt.</HelpTip>
      </h2>
      <SegmentedControl
        label="Vorschau für"
        value={mode}
        onChange={setMode}
        options={[
          { value: 'klasse', label: 'Klasse' },
          { value: 'person', label: 'Person' },
          { value: 'rolle', label: 'Rolle' },
        ]}
      />
      {mode === 'klasse' && (
        <div className="toolbar ar-toolbar">
          <Field label="Klasse" htmlFor={classSel}>
            <select id={classSel} value={classId} onChange={(e) => setClassId(e.target.value)}>
              {data.options.classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </Field>
          <SegmentedControl
            label="Zielgruppe"
            value={audience}
            onChange={setAudience}
            options={[
              { value: 'schueler', label: 'Schüler/innen' },
              { value: 'eltern', label: 'Eltern' },
            ]}
          />
        </div>
      )}
      {mode === 'rolle' && (
        <Field label="Rolle" htmlFor={roleSel} hint="Ohne Klassen- und Personen-Regeln">
          <select id={roleSel} value={role} onChange={(e) => setRole(e.target.value)}>
            {data.options.roles.map((r) => (
              <option key={r.id} value={r.id}>
                {r.label}
              </option>
            ))}
          </select>
        </Field>
      )}
      {mode === 'person' && (
        <>
          <PersonSearch label="Person suchen" onPick={setPerson} canAdmins />
          {person && (
            <p className="small">
              Ausgewählt: <strong>{person.display_name || person.username}</strong> ({roleLabel(person.role)})
            </p>
          )}
        </>
      )}
      <div aria-live="polite">
        {result.initialLoading ? <Loading /> : result.error ? <ErrorBox error={result.error} onRetry={result.reload} /> : result.data ? <EffectiveTable data={result.data} /> : null}
      </div>
    </section>
  );
}

function ReportArea({ data }: { data: PoliciesResponse }) {
  const [classId, setClassId] = useState(data.options.classes[0]?.id ?? '');
  const [audience, setAudience] = useState<Audience>('alle');
  const sel = useId();
  const report = useApi((signal) => policyApi.report(classId, audience, signal), [classId, audience, data], { enabled: !!classId });
  const r = report.data;
  return (
    <section className="card stack" aria-labelledby="ar-report-h">
      <h2 id="ar-report-h">
        Wer hat noch nicht verbunden?
        <HelpTip>Konten der Klasse, denen Pflicht-Verknüpfungen fehlen, z. B. zum Nachfassen im Unterricht oder per Elternbrief.</HelpTip>
      </h2>
      <div className="toolbar ar-toolbar">
        <Field label="Klasse" htmlFor={sel}>
          <select id={sel} value={classId} onChange={(e) => setClassId(e.target.value)}>
            {data.options.classes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </Field>
        <SegmentedControl
          label="Zielgruppe"
          value={audience}
          onChange={setAudience}
          options={AUDIENCES.map((a) => ({ value: a, label: AUDIENCE_LABELS[a] }))}
        />
      </div>
      <div aria-live="polite">
        {report.initialLoading ? (
          <Loading />
        ) : report.error ? (
          <ErrorBox error={report.error} onRetry={report.reload} />
        ) : r ? (
          <div className="stack">
            <ul className="ar-counts">
              {(['schueler', 'eltern'] as const)
                .filter((g) => audience === 'alle' || audience === g)
                .map((g) => {
                  const c = r.counts[g];
                  return (
                    <li key={g} className="ar-count">
                      <strong>{AUDIENCE_LABELS[g]}</strong>
                      <span>
                        {plural(c.accounts, 'Konto', 'Konten')} · {c.required} mit Pflicht ·{' '}
                        <span className="ar-ok">{c.complete} vollständig</span> ·{' '}
                        <span className={c.missing ? 'ar-miss' : ''}>
                          {plural(c.missing, 'fehlt', 'fehlen')} noch
                        </span>
                      </span>
                    </li>
                  );
                })}
            </ul>
            {r.students_without_account ? (
              <p className="small muted">{r.students_without_account} Schüler/innen der Klasse haben noch kein Konto.</p>
            ) : null}
            {r.items.length === 0 ? (
              <Empty icon="checkCircle">Niemandem fehlt eine Pflicht-Verknüpfung.</Empty>
            ) : (
              <div className="table-wrap">
                <table className="ar-table">
                  <caption className="sr-only">Fehlende Pflicht-Verknüpfungen in Klasse {r.class.name}</caption>
                  <thead>
                    <tr>
                      <th scope="col">Name</th>
                      <th scope="col">Gruppe</th>
                      <th scope="col">Fehlt</th>
                      <th scope="col">Verbunden</th>
                      <th scope="col">Zuletzt angemeldet</th>
                    </tr>
                  </thead>
                  <tbody>
                    {r.items.map((i) => (
                      <tr key={i.user.id}>
                        <th scope="row">
                          {i.user.display_name}
                          <div className="small muted">
                            {i.user.username}
                            {i.group === 'eltern' && i.students.length ? ` · Eltern von ${i.students.map((s) => s.name).join(', ')}` : ''}
                          </div>
                        </th>
                        <td>{i.group === 'eltern' ? 'Eltern' : 'Schüler/in'}</td>
                        <td>
                          <strong>{listText(i.missing, METHOD_LABELS)}</strong>
                        </td>
                        <td>{listText(i.linked, METHOD_LABELS)}</td>
                        <td>{i.last_login ? formatDateTime(i.last_login) : <span className="muted">noch nie</span>}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </section>
  );
}

// =================================================================== Seite
export default function PolicyPage() {
  useTitle('Anmelde-Richtlinien');
  const state = useApi((signal) => policyApi.list(signal), []);
  const caps = useApi((signal) => resetApi.options(signal), []);
  const [area, setArea] = useStoredState<Area>('ar-area', 'standard');
  const [editing, setEditing] = useState<EditTarget | null>(null);
  const [classQ, setClassQ] = useState('');
  const [onlyOwn, setOnlyOwn] = useState(false);
  const classSearch = useId();
  const data = state.data;
  const rules = useMemo(() => indexRules(data?.rules ?? []), [data]);

  if (state.initialLoading) return <Loading />;
  if (!data) return <ErrorBox error={state.error} onRetry={state.reload} />;

  const canAdmins = data.can_manage_admins;
  const unavailable = data.options.providers.filter((p) => !p.available);
  const mocks = data.options.providers.filter((p) => p.available && p.mock);
  const personRules = data.rules.filter((r) => r.scope === 'user');
  const classes = filterClasses(data.options.classes, classQ).filter(
    (c) => !onlyOwn || AUDIENCES.some((a) => rules.has(ruleKey({ scope: 'class', ref: c.id, audience: a }))),
  );
  const openPreset = () => setEditing({ scope: 'role', ref: 'schueler', audience: 'alle', label: 'Rolle Schüler/in', preset: true });

  return (
    <div className="page stack ar-page">
      <div className="page-head">
        <h1>Anmelde-Richtlinien</h1>
      </div>
      <section className="card stack" aria-labelledby="ar-intro-h">
        <h2 id="ar-intro-h">
          So funktioniert es
          <HelpTip>
            <p>
              Hier legen Sie fest, wie sich Konten anmelden dürfen (Passwort, Microsoft, Apple, Google, Schulkonto) und welche Anbieter-Konten verbunden sein müssen. Regeln gibt es für die ganze Schule (Standard), für Rollen, Jahrgänge, Klassen
              (jeweils für alle, nur Schüler/innen oder nur Eltern) und für einzelne Personen.
            </p>
            <p>
              Jede Einstellung wird einzeln vererbt: Person › Klasse › Jahrgang › Rolle › Standard. Eltern mit Kindern in mehreren Klassen erhalten die Einstellungen aller Klassen zusammen. Für die Administration bleibt die Anmeldung mit Passwort
              immer möglich.
            </p>
          </HelpTip>
        </h2>
        <div className="row ar-preset">
          <button type="button" className="btn" onClick={openPreset}>
            <Icon name="sparkles" /> Beispiel: Schüler/innen nur Microsoft + Apple, beide Pflicht
          </button>
        </div>
        {caps.data && (!caps.data.channels.email || !caps.data.channels.sms) && (
          <Alert kind="info" title="Versand für „Passwort vergessen“">
            {[
              !caps.data.channels.email ? 'E-Mail-Versand ist nicht eingerichtet (SMTP-Einstellungen des Servers)' : '',
              !caps.data.channels.sms ? 'SMS-Versand ist nicht eingerichtet (SMS-Anbieter des Servers)' : '',
            ]
              .filter(Boolean)
              .join('; ')}
            .
          </Alert>
        )}
        {unavailable.length > 0 && (
          <Alert kind="info" title="Noch nicht eingerichtete Anbieter">
            {listText(
              unavailable.map((p) => p.id),
              Object.fromEntries(data.options.providers.map((p) => [p.id, p.label])),
            )}{' '}
            – erst nutzbar, wenn die Administration den Anbieter einrichtet.
          </Alert>
        )}
        {mocks.length > 0 && (
          <p className="small muted">
            Test-Anbieter aktiv ({mocks.map((p) => p.label).join(', ')})
            <HelpTip>In der Vorschau lässt sich die Anmeldung ohne echte Konten ausprobieren.</HelpTip>
          </p>
        )}
      </section>

      <Tabs<Area>
        label="Bereiche"
        active={area}
        onChange={setArea}
        tabs={[
          { key: 'standard', label: 'Standard' },
          { key: 'rollen', label: 'Rollen' },
          { key: 'jahrgaenge', label: 'Jahrgänge' },
          { key: 'klassen', label: 'Klassen' },
          { key: 'personen', label: `Personen${personRules.length ? ` (${personRules.length})` : ''}` },
          { key: 'vorschau', label: 'Vorschau' },
          { key: 'bericht', label: 'Bericht' },
        ]}
      />

      {area === 'standard' && (
        <section className="card stack" aria-label="Standard">
          <h3>
            Standard
            <HelpTip>Gilt für alle Konten, solange Rolle, Jahrgang, Klasse oder Person nichts anderes festlegen.</HelpTip>
          </h3>
          <ul className="ar-rows">
            <TargetRow target={{ scope: 'default', ref: '', audience: 'alle', label: 'Standard' }} rule={rules.get(ruleKey({ scope: 'default', ref: '', audience: 'alle' }))} onEdit={setEditing} />
          </ul>
        </section>
      )}

      {area === 'rollen' && (
        <section className="card stack" aria-label="Rollen">
          <h3>
            Rollen
            <HelpTip>Personal hat keine Klassen: Für Lehrkräfte, Sekretariat usw. gelten Person › Rolle › Standard.</HelpTip>
          </h3>
          <ul className="ar-rows">
            {data.options.roles.map((r) => (
              <TargetRow
                key={r.id}
                target={{ scope: 'role', ref: r.id, audience: 'alle', label: `Rolle ${r.label}`, admin: r.id === 'admin' }}
                rule={rules.get(ruleKey({ scope: 'role', ref: r.id, audience: 'alle' }))}
                onEdit={setEditing}
                locked={r.manageable ? undefined : 'Nur die Administration darf Regeln für die Administration festlegen.'}
              />
            ))}
          </ul>
        </section>
      )}

      {area === 'jahrgaenge' && (
        <section className="card stack" aria-label="Jahrgänge">
          <h3>
            Jahrgänge
            <HelpTip>Gilt für alle Klassen des Jahrgangs. Öffnen Sie einen Jahrgang, um die Zielgruppe zu wählen.</HelpTip>
          </h3>
          {data.options.grades.length === 0 ? (
            <Empty>Im Planungsdokument gibt es noch keine Klassen.</Empty>
          ) : (
            data.options.grades.map((g) => (
              <AudienceGroup
                key={g.id}
                title={g.label}
                extra={g.classes === 1 ? '1 Klasse' : `${g.classes} Klassen`}
                scope="grade"
                refId={g.id}
                rules={rules}
                onEdit={setEditing}
              />
            ))
          )}
          {data.rules.filter((r) => r.scope === 'grade' && r.orphan).map((r) => (
            <ul className="ar-rows" key={r.id}>
              <TargetRow target={{ scope: 'grade', ref: r.ref, audience: r.audience, label: r.label }} rule={r} onEdit={setEditing} />
            </ul>
          ))}
        </section>
      )}

      {area === 'klassen' && (
        <section className="card stack" aria-label="Klassen">
          <div className="toolbar ar-toolbar">
            <Field label="Klasse suchen" htmlFor={classSearch} className="wide">
              <input id={classSearch} type="search" value={classQ} onChange={(e) => setClassQ(e.target.value)} placeholder="z. B. 5a oder 11" />
            </Field>
            <label className="check">
              <input type="checkbox" checked={onlyOwn} onChange={(e) => setOnlyOwn(e.target.checked)} /> nur mit eigener Regel
            </label>
          </div>
          {classes.length === 0 ? (
            <Empty icon="search">Keine passende Klasse.</Empty>
          ) : (
            classes.map((c) => (
              <AudienceGroup
                key={c.id}
                title={`Klasse ${c.name}`}
                extra={`Jahrgang ${c.grade}`}
                scope="class"
                refId={c.id}
                grade={c.grade}
                rules={rules}
                onEdit={setEditing}
              />
            ))
          )}
          {data.rules.filter((r) => r.scope === 'class' && r.orphan).map((r) => (
            <ul className="ar-rows" key={r.id}>
              <TargetRow target={{ scope: 'class', ref: r.ref, audience: r.audience, label: r.label }} rule={r} onEdit={setEditing} />
            </ul>
          ))}
        </section>
      )}

      {area === 'personen' && (
        <section className="card stack" aria-label="Personen">
          <h3>
            Personen
            <HelpTip>Personen-Regeln haben Vorrang vor allem anderen, z. B. Ausnahmen für einzelne Schüler/innen.</HelpTip>
          </h3>
          <PersonSearch
            label="Person suchen und Regel festlegen"
            canAdmins={canAdmins}
            onPick={(u) =>
              setEditing({ scope: 'user', ref: String(u.id), audience: 'alle', label: u.display_name || u.username, admin: u.role === 'admin' })
            }
          />
          <h3>Personen mit eigener Regel</h3>
          {personRules.length === 0 ? (
            <Empty>Noch keine Personen-Regeln.</Empty>
          ) : (
            <ul className="ar-rows">
              {personRules.map((r) => {
                const t = r.target && 'username' in r.target ? r.target : null;
                return (
                  <TargetRow
                    key={r.id}
                    target={{ scope: 'user', ref: r.ref, audience: 'alle', label: t ? `${t.display_name} (${roleLabel(t.role)})` : r.label, admin: t?.role === 'admin' }}
                    rule={r}
                    onEdit={setEditing}
                    locked={t?.role === 'admin' && !canAdmins ? 'Nur die Administration darf Regeln für Administrationskonten festlegen.' : undefined}
                  />
                );
              })}
            </ul>
          )}
        </section>
      )}

      {area === 'vorschau' && <PreviewArea data={data} />}
      {area === 'bericht' && <ReportArea data={data} />}

      {editing && (
        <RuleEditor
          key={`${ruleKey(editing)}|${editing.preset ? 'p' : ''}`}
          target={editing}
          rule={rules.get(ruleKey(editing))}
          data={data}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            state.reload();
          }}
        />
      )}
    </div>
  );
}

/** Abzeichen der Schule: definieren (Symbol, Farbe, Vergabekriterien), manuell vergeben, automatisch prüfen. */
import { useState } from 'react';
import { Modal } from '../../components/Modal';
import { AsyncButton, Empty, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { compApi, type Badge, type Framework } from './api';
import { BadgeIcon } from './BadgeIcon';
import { BADGE_COLORS, BADGE_ICONS, COLOR_LABEL, ICON_LABEL, criteriaDraft, criteriaError, criteriaOf, type CriteriaDraft, type CriteriaKind } from './logic';

export function BadgesTab({ canManage, canAssess }: { canManage: boolean; canAssess: boolean }) {
  const toast = useToast();
  const q = useApi((signal) => compApi.badges(signal), [], { live: ['competency'] });
  const [editing, setEditing] = useState<Badge | 'new' | null>(null);
  const [awarding, setAwarding] = useState<Badge | null>(null);
  if (q.error) return <ErrorBox error={q.error} onRetry={q.reload} />;
  if (!q.data) return <Loading />;
  return (
    <div className="stack">
      {canManage && (
        <div className="row">
          <button type="button" className="btn btn-primary" onClick={() => setEditing('new')}>
            Neues Abzeichen
          </button>
          <AsyncButton
            className="btn"
            onClick={async () => {
              const r = await compApi.evaluateBadges();
              toast.success(r.awarded ? `${r.awarded} Abzeichen automatisch vergeben` : 'Keine neuen Abzeichen fällig');
              q.reload();
            }}
          >
            Automatische Abzeichen prüfen
          </AsyncButton>
        </div>
      )}
      {!q.data.length && <Empty icon="sparkles">Noch keine Abzeichen definiert.</Empty>}
      <ul className="cp-badge-grid">
        {q.data.map((b) => (
          <li key={b.id} className={`card cp-badge-card${b.active ? '' : ' cp-archived'}`}>
            <BadgeIcon icon={b.icon} color={b.color} size="lg" label={b.name} />
            <strong>{b.name}</strong>
            {b.description && <span className="small">{b.description}</span>}
            <span className="xsmall muted">{b.criteria_text}</span>
            {canManage && (
              <span className="xsmall muted">
                {b.awarded}× vergeben{b.active ? '' : ' · inaktiv'}
              </span>
            )}
            <div className="row cp-fw-actions">
              {canAssess && !b.auto && b.active && (
                <button type="button" className="btn btn-sm" onClick={() => setAwarding(b)}>
                  Vergeben
                </button>
              )}
              {canManage && (
                <>
                  <button type="button" className="btn btn-sm" onClick={() => setEditing(b)}>
                    Bearbeiten
                  </button>
                  <AsyncButton
                    className="btn btn-sm btn-danger"
                    confirm={`Abzeichen „${b.name}“ löschen? ${b.awarded} Vergaben gehen verloren.`}
                    onClick={async () => {
                      await compApi.deleteBadge(b.id);
                      q.reload();
                    }}
                  >
                    Löschen
                  </AsyncButton>
                </>
              )}
            </div>
          </li>
        ))}
      </ul>
      {editing && <BadgeEditor badge={editing === 'new' ? null : editing} onClose={() => setEditing(null)} onSaved={q.reload} />}
      {awarding && <AwardDialog badge={awarding} onClose={() => setAwarding(null)} onDone={q.reload} />}
    </div>
  );
}

function BadgeEditor({ badge, onClose, onSaved }: { badge: Badge | null; onClose: () => void; onSaved: () => void }) {
  const toast = useToast();
  const [name, setName] = useState(badge?.name ?? '');
  const [description, setDescription] = useState(badge?.description ?? '');
  const [icon, setIcon] = useState(badge?.icon ?? 'star');
  const [color, setColor] = useState(badge?.color ?? 'gold');
  const [active, setActive] = useState(badge?.active ?? true);
  const [crit, setCrit] = useState<CriteriaDraft>(() => criteriaDraft(badge?.criteria ?? null));
  const fws = useApi(async (signal) => {
    const list = await compApi.frameworks(false, signal);
    return Promise.all(list.map((f) => compApi.framework(f.id, signal)));
  }, []);
  const frameworks: Framework[] = fws.data ?? [];
  const err = !name.trim() ? 'Bitte einen Namen eingeben.' : criteriaError(crit);
  const setKind = (kind: CriteriaKind) => setCrit({ ...crit, kind });
  const maxLevel = Math.min(...frameworks.map((f) => f.levels.length), 6) || 4;

  const save = async () => {
    const body = { name: name.trim(), description: description.trim(), icon, color, criteria: criteriaOf(crit), active };
    if (badge) await compApi.saveBadge(badge.id, body);
    else await compApi.createBadge(body);
    toast.success('Abzeichen gespeichert');
    onSaved();
    onClose();
  };

  return (
    <Modal
      size="lg"
      title={badge ? 'Abzeichen bearbeiten' : 'Neues Abzeichen'}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton className="btn btn-primary" disabled={!!err} title={err ?? undefined} onClick={save}>
            Speichern
          </AsyncButton>
        </>
      }
    >
      <div className="stack">
        <div className="cp-badge-preview">
          <BadgeIcon icon={icon} color={color} size="lg" label={name || 'Vorschau'} />
          <strong>{name || 'Name'}</strong>
        </div>
        <Field label="Name" htmlFor="cp-bd-name">
          <input id="cp-bd-name" value={name} maxLength={100} onChange={(e) => setName(e.target.value)} />
        </Field>
        <Field label="Beschreibung" htmlFor="cp-bd-desc">
          <input id="cp-bd-desc" value={description} maxLength={300} onChange={(e) => setDescription(e.target.value)} />
        </Field>
        <fieldset className="cp-pick">
          <legend>Symbol</legend>
          {BADGE_ICONS.map((i) => (
            <label key={i} className="cp-pick-opt" title={ICON_LABEL[i]}>
              <input type="radio" name="cp-bd-icon" checked={icon === i} onChange={() => setIcon(i)} />
              <BadgeIcon icon={i} color={color} size="sm" label={ICON_LABEL[i]} />
            </label>
          ))}
        </fieldset>
        <fieldset className="cp-pick">
          <legend>Farbe</legend>
          {BADGE_COLORS.map((c) => (
            <label key={c} className="cp-pick-opt" title={COLOR_LABEL[c]}>
              <input type="radio" name="cp-bd-color" checked={color === c} onChange={() => setColor(c)} />
              <BadgeIcon icon="medal" color={c} size="sm" label={COLOR_LABEL[c]} />
            </label>
          ))}
        </fieldset>
        <Field label="Vergabe" htmlFor="cp-bd-kind" help="Manuell vergibt die Lehrkraft. Automatisch wird das Abzeichen vergeben, sobald die Einschätzungen der Lehrkräfte die Kriterien erfüllen.">
          <select id="cp-bd-kind" value={crit.kind} onChange={(e) => setKind(e.target.value as CriteriaKind)}>
            <option value="manual">Manuell durch die Lehrkraft</option>
            <option value="competencies">Automatisch: bestimmte Kompetenzen</option>
            <option value="area">Automatisch: Bereich</option>
            <option value="framework">Automatisch: ganzer Rahmen</option>
          </select>
        </Field>
        {crit.kind !== 'manual' && (
          <Field label="Mindestens Stufe" htmlFor="cp-bd-level">
            <select id="cp-bd-level" value={crit.min_level} onChange={(e) => setCrit({ ...crit, min_level: Number(e.target.value) })}>
              {Array.from({ length: maxLevel }, (_, i) => i + 1).map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </select>
          </Field>
        )}
        {(crit.kind === 'area' || crit.kind === 'framework') && (
          <Field label="Anteil der Kompetenzen" htmlFor="cp-bd-share">
            <select id="cp-bd-share" value={crit.share} onChange={(e) => setCrit({ ...crit, share: Number(e.target.value) })}>
              {[0.5, 0.6, 0.7, 0.8, 0.9, 1].map((s) => (
                <option key={s} value={s}>
                  {Math.round(s * 100)} %
                </option>
              ))}
            </select>
          </Field>
        )}
        {crit.kind === 'area' && (
          <Field label="Bereich" htmlFor="cp-bd-area">
            <select id="cp-bd-area" value={crit.area_id ?? ''} onChange={(e) => setCrit({ ...crit, area_id: e.target.value ? Number(e.target.value) : null })}>
              <option value="">Auswählen …</option>
              {frameworks.map((f) => (
                <optgroup key={f.id} label={f.name}>
                  {f.areas.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </Field>
        )}
        {crit.kind === 'framework' && (
          <Field label="Rahmen" htmlFor="cp-bd-fw">
            <select id="cp-bd-fw" value={crit.framework_id ?? ''} onChange={(e) => setCrit({ ...crit, framework_id: e.target.value ? Number(e.target.value) : null })}>
              <option value="">Auswählen …</option>
              {frameworks.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name}
                </option>
              ))}
            </select>
          </Field>
        )}
        {crit.kind === 'competencies' && (
          <fieldset className="cp-comp-pick">
            <legend>Kompetenzen</legend>
            {frameworks.map((f) =>
              f.areas.map((a) => (
                <div key={`${f.id}-${a.id}`}>
                  <div className="small muted">
                    {f.name}: {a.name}
                  </div>
                  {a.competencies.map((c) => (
                    <label key={c.id} className="cp-check">
                      <input
                        type="checkbox"
                        checked={crit.competency_ids.includes(c.id)}
                        onChange={(e) => setCrit({ ...crit, competency_ids: e.target.checked ? [...crit.competency_ids, c.id] : crit.competency_ids.filter((x) => x !== c.id) })}
                      />{' '}
                      {c.title}
                    </label>
                  ))}
                </div>
              )),
            )}
          </fieldset>
        )}
        <label className="cp-check">
          <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} /> Aktiv
        </label>
      </div>
    </Modal>
  );
}

function AwardDialog({ badge, onClose, onDone }: { badge: Badge; onClose: () => void; onDone: () => void }) {
  const toast = useToast();
  const [classId, setClassId] = useState<string | null>(null);
  const [chosen, setChosen] = useState<string[]>([]);
  const [note, setNote] = useState('');
  const q = useApi((signal) => compApi.overview({ class_id: classId ?? undefined }, signal), [classId]);
  const data = q.data;
  return (
    <Modal
      title={`Abzeichen „${badge.name}“ vergeben`}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" onClick={onClose}>
            Abbrechen
          </button>
          <AsyncButton
            className="btn btn-primary"
            disabled={!chosen.length}
            onClick={async () => {
              const r = await compApi.award(badge.id, chosen, note.trim());
              toast.success(r.awarded ? `${r.awarded} Abzeichen vergeben` : 'Alle hatten das Abzeichen schon');
              onDone();
              onClose();
            }}
          >
            Vergeben
          </AsyncButton>
        </>
      }
    >
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {!data && !q.error && <Loading />}
      {data && (
        <div className="stack">
          <Field label="Klasse" htmlFor="cp-aw-class">
            <select id="cp-aw-class" value={data.class?.id ?? ''} onChange={(e) => { setClassId(e.target.value); setChosen([]); }}>
              {data.classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </Field>
          <fieldset className="cp-comp-pick">
            <legend>Schüler/innen</legend>
            {data.students.map((s) => (
              <label key={s.id} className="cp-check">
                <input type="checkbox" checked={chosen.includes(s.id)} onChange={(e) => setChosen(e.target.checked ? [...chosen, s.id] : chosen.filter((x) => x !== s.id))} /> {s.name}
              </label>
            ))}
          </fieldset>
          <Field label="Notiz" htmlFor="cp-aw-note" help="Erscheint beim Abzeichen der Schülerin bzw. des Schülers.">
            <input id="cp-aw-note" value={note} maxLength={300} onChange={(e) => setNote(e.target.value)} />
          </Field>
        </div>
      )}
    </Modal>
  );
}

/**
 * Profil-Abschnitt „Was dürfen meine Eltern sehen?“ (A-44) – nur für Schüler/innen. Volljährige legen je Bereich
 * fest, was verknüpfte Elternkonten sehen, und wohin Rundschreiben der Schule gehen (`PUT /parent-access`,
 * protokolliert); Minderjährige sehen den Stand ausgegraut („ab 18“). Einhängepunkt: `ProfilePage`.
 * `ParentAccessBanner` (Layout) erinnert Volljährige, die noch nie gespeichert haben. Backend: `server/parent_access.py`.
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { http } from '../../api/client';
import { PageHelp } from '../../components/Help';
import { Icon } from '../../components/Icon';
import { ErrorBox, Loading } from '../../components/ui';
import { useUser } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';

export interface ParentAccessArea {
  key: string;
  label: string;
  allowed: boolean;
}

export type Delivery = 'self' | 'parents' | 'both';

export interface ParentAccessState {
  adult: boolean;
  editable: boolean;
  needs_decision: boolean;
  delivery: Delivery;
  delivery_options: { key: Delivery; label: string }[];
  areas: ParentAccessArea[];
  parents: { name: string }[];
}

export const parentAccessApi = {
  get: (signal?: AbortSignal) => http.get<ParentAccessState>('/parent-access', undefined, { signal }),
  save: (body: { areas?: Record<string, boolean>; delivery?: Delivery; confirm?: boolean }) => http.put<ParentAccessState>('/parent-access', body),
};

function Section() {
  const q = useApi<ParentAccessState>((signal) => parentAccessApi.get(signal), [], { live: ['parent_access'] });
  const [saving, setSaving] = useState<string | null>(null);
  const toast = useToast();
  const data = q.data;
  const run = async (key: string, body: Parameters<typeof parentAccessApi.save>[0], message: string) => {
    setSaving(key);
    try {
      await parentAccessApi.save(body);
      toast.success(message);
      q.reload();
    } catch (e) {
      toast.error(e);
    } finally {
      setSaving(null);
    }
  };
  const toggle = (area: ParentAccessArea) =>
    run(area.key, { areas: { [area.key]: !area.allowed } }, area.allowed ? `${area.label}: für Ihre Eltern nicht mehr sichtbar` : `${area.label}: für Ihre Eltern sichtbar`);
  return (
    <section className="card" aria-labelledby="pa-h" id="eltern-freigabe">
      <h2 id="pa-h" className="with-help">
        Was dürfen meine Eltern sehen?
        <PageHelp label="Hilfe zu „Was dürfen meine Eltern sehen?“">
          Bis zu Ihrem 18. Geburtstag sehen Ihre Eltern, was Sie sehen. Danach legen Sie hier je Bereich fest, was Ihre
          verknüpften Elternkonten sehen dürfen; ohne Haken sehen sie den Bereich nicht. Auch wohin Rundschreiben der Schule gehen,
          bestimmen Sie dann selbst. Jede Änderung wird protokolliert.
        </PageHelp>
        {data && !data.adult && <span className="badge">ab 18</span>}
      </h2>
      {q.error ? <ErrorBox error={q.error} onRetry={q.reload} /> : null}
      {q.initialLoading && <Loading />}
      {data && (
        <div className="stack-sm">
          {data.adult && data.needs_decision && (
            <div className="alert alert-info" role="note">
              <Icon name="info" /> Sie sind volljährig: Entscheiden Sie, was Ihre Eltern weiterhin sehen. Bis Sie speichern, gilt: nichts, Rundschreiben gehen nur an Sie.
            </div>
          )}
          <fieldset className="stack-sm" disabled={!data.editable}>
            <legend className="sr-only">Bereiche</legend>
            {data.areas.map((a) => (
              <div key={a.key}>
                <label className="check">
                  <input type="checkbox" checked={a.allowed} disabled={!data.editable || saving !== null} onChange={() => void toggle(a)} /> {a.label}
                </label>
              </div>
            ))}
          </fieldset>
          <fieldset className="stack-sm" disabled={!data.editable}>
            <legend className="small">Informationen der Schule (Rundschreiben im Postfach) gehen an</legend>
            {data.delivery_options.map((o) => (
              <label key={o.key} className="check">
                <input type="radio" name="pa-delivery" checked={data.delivery === o.key} disabled={!data.editable || saving !== null} onChange={() => void run('delivery', { delivery: o.key }, `Rundschreiben: ${o.label.toLowerCase()}`)} /> {o.label}
              </label>
            ))}
          </fieldset>
          {data.adult && data.needs_decision && (
            <button type="button" className="btn btn-primary" disabled={saving !== null} onClick={() => void run('confirm', { confirm: true }, 'Einstellung gespeichert')}>
              So übernehmen
            </button>
          )}
          <p className="xsmall muted">
            {data.parents.length ? `Verknüpfte Elternkonten: ${data.parents.map((p) => p.name).join(', ')}` : 'Kein Elternkonto verknüpft.'}
          </p>
        </div>
      )}
    </section>
  );
}

/** Nur für Schülerkonten – sonst nichts. */
export function ParentAccessSection() {
  const user = useUser();
  if (user.role !== 'schueler') return null;
  return <Section />;
}

/** Hinweis im Kopfbereich: volljährig, aber die Freigaben wurden noch nie gespeichert. */
export function ParentAccessBanner() {
  const user = useUser();
  const isPupil = user.role === 'schueler';
  const q = useApi<ParentAccessState>((signal) => parentAccessApi.get(signal), [], { enabled: isPupil, live: ['parent_access'] });
  if (!isPupil || !q.data?.needs_decision) return null;
  return (
    <div className="alert alert-info readonly-banner" role="note">
      <Icon name="info" /> Sie sind jetzt volljährig. Legen Sie fest, was Ihre Eltern weiterhin sehen dürfen. <Link to="/profil#eltern-freigabe">Jetzt festlegen</Link>
    </div>
  );
}

export default ParentAccessSection;

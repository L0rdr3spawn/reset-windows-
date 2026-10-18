/**
 * Benutzerverwaltung → Reiter „Verbundene Konten“: Verknüpfungen eines Kontos ansehen, lösen und eine E-Mail-Adresse
 * vormerken (bei der ersten Anmeldung mit dieser, vom Anbieter bestätigten Adresse wird automatisch verbunden).
 */
import { useId, useState, type FormEvent } from 'react';
import { errorMessage } from '../../api/client';
import { Icon } from '../../components/Icon';
import { HelpTip } from '../../components/HelpTip';
import { AsyncButton, ErrorBox, Field, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { formatDateTime } from '../../lib/dates';
import { ssoApi } from './api';
import { dayOf } from './logic';

export default function UserIdentitiesPanel({ userId }: { userId: number }) {
  const toast = useToast();
  const id = useId();
  const q = useApi((signal) => ssoApi.ofUser(userId, signal), [userId]);
  const [provider, setProvider] = useState('');
  const [email, setEmail] = useState('');
  const [busy, setBusy] = useState(false);

  if (q.initialLoading) return <Loading />;
  if (q.error && !q.data) return <ErrorBox error={q.error} onRetry={q.reload} />;
  const data = q.data;
  if (!data) return null;
  const chosen = provider || data.providers.find((p) => p.available)?.id || data.providers[0]?.id || '';
  const labelOf = (pid: string) => data.providers.find((p) => p.id === pid)?.label ?? pid;

  const remove = async (pid: string, linked: boolean) => {
    try {
      q.setData(await ssoApi.remove(userId, pid));
      toast.success(linked ? `Verknüpfung mit ${labelOf(pid)} gelöst.` : 'Vormerkung gelöscht.');
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  const reserve = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      q.setData(await ssoApi.reserve(userId, chosen, email.trim()));
      setEmail('');
      toast.success('Adresse vorgemerkt.');
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="stack-sm">
      {data.required.length > 0 && (
        <p className="small">
          Pflicht laut Anmelde-Richtlinie: <strong>{data.required.map(labelOf).join(', ')}</strong>
          {!data.self_link && ' · selbst verbinden/trennen ist für dieses Konto nicht erlaubt'}
        </p>
      )}
      {data.items.length === 0 ? (
        <p className="muted small">Noch keine verbundenen oder vorgemerkten Konten.</p>
      ) : (
        <ul className="list-plain ad-list">
          {data.items.map((it) => (
            <li key={it.provider} className="ad-item">
              <div className="ad-item-main">
                <div className="ad-item-title">
                  <strong>{it.label}</strong>
                  {it.linked ? <span className="badge badge-success">Verbunden</span> : <span className="badge badge-info">Vorgemerkt</span>}
                  {it.mock && <span className="badge badge-warning">Test</span>}
                  {data.required.includes(it.provider) && <span className="badge badge-primary">Pflicht</span>}
                </div>
                <div className="small muted">
                  {it.email ?? 'ohne E-Mail-Adresse'}
                  {it.linked ? ` · seit ${dayOf(it.created_at)}` : ' · wird bei der ersten Anmeldung verbunden'}
                  {it.last_login_at && ` · zuletzt angemeldet ${formatDateTime(it.last_login_at)}`}
                </div>
              </div>
              <div className="ad-item-actions">
                <AsyncButton
                  className="btn btn-sm"
                  confirm={it.linked ? `Verknüpfung mit ${it.label} lösen? Die Anmeldung damit ist danach nicht mehr möglich.` : 'Vormerkung löschen?'}
                  onClick={() => remove(it.provider, it.linked)}
                >
                  <Icon name="trash" /> {it.linked ? 'Lösen' : 'Löschen'}
                </AsyncButton>
              </div>
            </li>
          ))}
        </ul>
      )}
      <form className="ad-reserve" onSubmit={reserve} aria-labelledby={`${id}-h`}>
        <h3 id={`${id}-h`} className="ad-subhead">
          E-Mail-Adresse vormerken
          <HelpTip>
            Meldet sich die Person zum ersten Mal mit genau dieser, vom Anbieter bestätigten Adresse an, wird das Konto automatisch verbunden, z. B. die Apple-ID oder das Microsoft-Konto, das die Schule ausgegeben hat.
          </HelpTip>
        </h3>
        <div className="ad-reserve-row">
          <Field label="Anbieter" htmlFor={`${id}-p`}>
            <select id={`${id}-p`} value={chosen} onChange={(e) => setProvider(e.target.value)}>
              {data.providers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                  {p.mock ? ' (Test)' : !p.available ? ' (nicht eingerichtet)' : ''}
                </option>
              ))}
            </select>
          </Field>
          <Field label="E-Mail-Adresse beim Anbieter" htmlFor={`${id}-e`}>
            <input id={`${id}-e`} type="email" autoComplete="off" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="vorname.nachname@schule.de" />
          </Field>
        </div>
        <button type="submit" className="btn btn-sm" disabled={busy || !email.includes('@') || !chosen}>
          <Icon name="plus" /> Vormerken
        </button>
      </form>
    </div>
  );
}

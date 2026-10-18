/**
 * Profil → „Verbundene Konten“: je Anbieter Status (verbunden als …, seit …), Verbinden/Trennen, Pflicht-Kennzeichen,
 * Hinweis „wird von der Schule verwaltet“. Nach der Rückkehr vom Anbieter (`?verbunden=` / `?sso_error=`) eine Meldung.
 */
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import { Icon } from '../../components/Icon';
import { HelpTip } from '../../components/HelpTip';
import { Alert, AsyncButton, ErrorBox, Loading } from '../../components/ui';
import { useToast } from '../../context/ToastContext';
import { useApi } from '../../hooks/useApi';
import { ssoApi } from './api';
import { returnNotice, statusLine, type Notice } from './logic';
import type { MyProvider } from './types';

const LABELS: Record<string, string> = { microsoft: 'Microsoft', apple: 'Apple', google: 'Google', oidc: 'Schulkonto' };

export default function IdentitiesSection() {
  const toast = useToast();
  const [params, setParams] = useSearchParams();
  const q = useApi((signal) => ssoApi.mine(signal), []);
  const [notice, setNotice] = useState<Notice | null>(() => returnNotice(params, (id) => LABELS[id] ?? id));

  // Rückkehr-Parameter nur einmal anzeigen (nicht beim Neuladen/Teilen der Adresse)
  useEffect(() => {
    if (!params.has('verbunden') && !params.has('sso_error')) return;
    const nextParams = new URLSearchParams(params);
    nextParams.delete('verbunden');
    nextParams.delete('sso_error');
    setParams(nextParams, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const connect = async (p: MyProvider) => {
    try {
      const { url } = await ssoApi.link(p.id, '/profil');
      window.location.assign(url);
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };
  const disconnect = async (p: MyProvider) => {
    try {
      q.setData(await ssoApi.unlink(p.id));
      setNotice(null);
      toast.success(`${p.label} wurde getrennt.`);
    } catch (e) {
      toast.error(errorMessage(e));
    }
  };

  const heading = (
    <h2 id="ad-ids-h">
      Verbundene Konten
      <HelpTip>Mit einem verbundenen Microsoft-, Apple- oder Google-Konto bzw. dem Schulkonto melden Sie sich ohne eigenes Passwort an.</HelpTip>
    </h2>
  );
  if (q.initialLoading) {
    return (
      <section className="card" aria-labelledby="ad-ids-h">
        {heading}
        <Loading />
      </section>
    );
  }
  if (q.error && !q.data) {
    return (
      <section className="card" aria-labelledby="ad-ids-h">
        {heading}
        <ErrorBox error={q.error} onRetry={q.reload} />
      </section>
    );
  }
  const data = q.data;
  if (!data || (!data.providers.length && !notice)) return null;
  return (
    <section className="card stack-sm" aria-labelledby="ad-ids-h">
      {heading}
      <div aria-live="polite">
        {notice && (
          <Alert kind={notice.kind} title={notice.kind === 'success' ? 'Verbunden' : 'Verbinden fehlgeschlagen'}>
            {notice.text}
          </Alert>
        )}
      </div>
      {!data.self_link && (
        <Alert kind="info" title="Wird von der Schule verwaltet">
          Verbundene Konten legt die Schule fest. {data.required.length > 0 ? 'Pflicht-Verknüpfungen können Sie selbst herstellen.' : 'Bei Fragen hilft das Sekretariat.'}
        </Alert>
      )}
      {data.providers.length === 0 ? (
        <p className="muted">Derzeit sind keine Anmeldedienste eingerichtet.</p>
      ) : (
        <ul className="list-plain ad-list">
          {data.providers.map((p) => (
            <li key={p.id} className="ad-item">
              <div className="ad-item-main">
                <div className="ad-item-title">
                  <strong>{p.label}</strong>
                  {p.mock && <span className="badge badge-warning">Test</span>}
                  {p.required && <span className="badge badge-primary">Pflicht</span>}
                  {p.linked && <span className="badge badge-success">Verbunden</span>}
                  {p.identity?.managed && <span className="badge badge-info">{p.linked ? 'von der Schule eingerichtet' : 'von der Schule vorgemerkt'}</span>}
                </div>
                <div className="small muted">{statusLine(p)}</div>
                {p.linked && !p.can_unlink && p.unlink_block && <div className="small faint">{p.unlink_block.message}</div>}
              </div>
              <div className="ad-item-actions">
                {p.can_link && (
                  <AsyncButton className={`btn btn-sm${p.required ? ' btn-primary' : ''}`} onClick={() => connect(p)}>
                    <Icon name="link" /> Verbinden
                  </AsyncButton>
                )}
                {p.linked && p.can_unlink && (
                  <AsyncButton className="btn btn-sm" confirm={`${p.label}-Konto wirklich trennen? Danach ist die Anmeldung damit nicht mehr möglich.`} onClick={() => disconnect(p)}>
                    <Icon name="unlock" /> Trennen
                  </AsyncButton>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

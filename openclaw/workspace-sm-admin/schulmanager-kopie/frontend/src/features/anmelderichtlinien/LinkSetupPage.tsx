/**
 * Seite `/konten-verbinden` (§11.5): Pflicht-Verknüpfungen laut Anmelde-Richtlinie herstellen.
 *
 * Der Guard in `App.tsx` leitet hierher, solange `user.login_setup.missing_links` nicht leer ist; die API antwortet bis
 * dahin mit `403 link_required`. „Jetzt verbinden“ → `POST /me/identities/{provider}/link` (Agent Anbieter) → `{url}` →
 * Anbieter → zurück hierher; beim Laden wird der Benutzer neu gelesen (`refresh`).
 */
import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { errorMessage } from '../../api/client';
import { Icon } from '../../components/Icon';
import { Alert, AsyncButton, Loading } from '../../components/ui';
import { APP_NAME } from '../../brand';
import { useAuth, useUser } from '../../context/AuthContext';
import { useApi } from '../../hooks/useApi';
import { useTitle } from '../../hooks/misc';
import { homePath } from '../../lib/permissions';
import { SSO_ERROR_MESSAGES } from '../anmeldedienste/slots';
import { linkApi } from './api';
import { linkItems } from './logic';
import './anmelderichtlinien.css';

export default function LinkSetupPage() {
  useTitle('Konten verbinden');
  const user = useUser();
  const { refresh, logout } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const providers = useApi((signal) => linkApi.providers(signal), []);
  const missing = user.login_setup?.missing_links ?? [];
  const setupOnly = !!user.login_setup?.setup_only;
  const ssoError = params.get('sso_error') ?? params.get('link_error');

  // Nach der Rückkehr vom Anbieter: aktuellen Stand holen
  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Anbieterliste nicht abrufbar → trotzdem anbieten (das Backend prüft beim Verbinden)
  const available = providers.error ? missing.map((id) => ({ id })) : providers.data ?? null;
  const items = linkItems(missing, available);

  const connect = async (provider: string) => {
    setError(null);
    try {
      const { url } = await linkApi.start(provider);
      if (!url || !/^(https?:)?\//.test(url)) throw new Error('Der Anmeldedienst hat keine gültige Adresse geliefert.');
      window.location.assign(url);
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  return (
    <div className="login-wrap">
      <main className="card login-card stack ar-link-wrap">
        <h1>Konten verbinden</h1>
        {missing.length === 0 ? (
          <>
            <Alert kind="success" title="Alles verbunden">
              {`Ihre Konten sind verbunden. Sie können ${APP_NAME} jetzt nutzen.`}
            </Alert>
            <Link className="btn btn-primary" to={homePath(user)} replace>
              Weiter zur Startseite <Icon name="chevronRight" />
            </Link>
          </>
        ) : (
          <>
            <p>
              {`Ihre Schule verlangt, dass Sie folgende Konten mit ${APP_NAME} verbinden. Erst danach können Sie ${APP_NAME} nutzen.`}
            </p>
            {setupOnly && (
              <Alert kind="info" title="Anmeldung künftig über diese Konten">
                Mit dem Startpasswort können Sie nur die Konten verbinden. Danach melden Sie sich mit einem verbundenen Konto an.
              </Alert>
            )}
            {ssoError && (
              <Alert kind="error" title="Verbinden fehlgeschlagen">
                {SSO_ERROR_MESSAGES[ssoError] ?? 'Der Anmeldedienst hat die Verbindung nicht bestätigt. Bitte erneut versuchen.'}
              </Alert>
            )}
            {providers.initialLoading ? (
              <Loading label="Anmeldedienste werden geladen …" />
            ) : (
              <ul className="ar-links" aria-label="Noch zu verbindende Konten">
                {items.map((p) => (
                  <li key={p.id} className="ar-link">
                    <span className="ar-link-name">{p.label}</span>
                    {p.available ? (
                      <AsyncButton className="btn btn-primary" onClick={() => connect(p.id)}>
                        <Icon name="link" /> Jetzt verbinden
                      </AsyncButton>
                    ) : (
                      <span className="small muted">Derzeit nicht verfügbar – bitte an das Sekretariat wenden.</span>
                    )}
                  </li>
                ))}
              </ul>
            )}
            <div aria-live="polite">{error && <Alert kind="error">{error}</Alert>}</div>
            <p className="small muted">Sie werden zur Anmeldeseite des Anbieters weitergeleitet.</p>
          </>
        )}
        <div className="row ar-preset">
          {missing.length > 0 && (
            <AsyncButton className="btn" onClick={refresh}>
              <Icon name="refresh" /> Erneut prüfen
            </AsyncButton>
          )}
          <button
            type="button"
            className="btn btn-ghost"
            onClick={async () => {
              await logout();
              navigate('/login', { replace: true });
            }}
          >
            <Icon name="logout" /> Abmelden
          </button>
        </div>
      </main>
    </div>
  );
}

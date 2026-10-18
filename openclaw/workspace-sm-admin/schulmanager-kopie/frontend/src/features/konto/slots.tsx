/**
 * Einhängepunkte des Features „konto“ (§11.2) in geteilten Seiten.
 * LoginPage: <ForgotPasswordLink />, ProfilePage: <ContactSection /> (nach „Konto“), UsersPage/UserModal:
 * <UserContactPanel userId /> (Reiter „Kontakt“, optional `onEmailChange`). Signaturen bleiben stabil.
 */
import { Link, useSearchParams } from 'react-router-dom';
import { Alert } from '../../components/ui';
import { useApi } from '../../hooks/useApi';
import { resetApi } from './api';
import { resetUsable } from './logic';
import './konto.css';

export { ContactSection } from './ContactSection';
export { UserContactPanel } from './UserContactPanel';

/** Link „Passwort vergessen?“ unter dem Anmeldeknopf (+ Erfolgsmeldung nach dem Zurücksetzen, `?reset=ok`). */
export function ForgotPasswordLink() {
  const [params] = useSearchParams();
  const ok = params.get('reset') === 'ok';
  // Link ausblenden, sobald feststeht, dass „Passwort vergessen“ nicht gehen kann (kein Versand eingerichtet, keine Rolle darf es
  // selbst nutzen); solange unbekannt (Laden/Fehler) bleibt er sichtbar
  const caps = useApi((signal) => resetApi.options(signal), []);
  const show = caps.data ? resetUsable(caps.data) : true;
  return (
    <div className="ko-forgot">
      {ok && (
        <div aria-live="polite">
          <Alert kind="success" title="Passwort geändert">
            Bitte melden Sie sich neu an.
          </Alert>
        </div>
      )}
      {show && (
        <p>
          <Link to="/passwort-vergessen">Passwort vergessen?</Link>
        </p>
      )}
      {!show && (
        <p className="small muted">Passwort vergessen? Bitte wenden Sie sich an das Sekretariat.</p>
      )}
    </div>
  );
}

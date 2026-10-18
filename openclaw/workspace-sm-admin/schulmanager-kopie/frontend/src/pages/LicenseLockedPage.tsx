/**
 * Sperrseite bei ungültiger oder fehlender Lizenz (`licensing`, Stufe „gesperrt“): ersetzt die ganze Anwendung
 * (`App.tsx` → `Guard`). Alle Konten sehen die kurze Mitteilung und können sich abmelden; Konten mit dem Recht
 * `license.manage` (Administration, Schulleitung) bekommen darunter die Lizenzseite, um eine neue Lizenz einzugeben.
 * Frische Instanz ohne Lizenz (Auslieferung mit Admin-Zugang): Begrüßung „Willkommen – bitte Lizenz eingeben“; nach
 * der gültigen Lizenz geht es direkt in den Einrichtungsassistenten (`/einrichtung`). Erklärungen nur im (i).
 */
import { APP_NAME } from '../brand';
import { BrandLogo } from '../components/BrandLogo';
import { HelpTip } from '../components/HelpTip';
import { Icon } from '../components/Icon';
import { Alert } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { useTitle } from '../hooks/misc';
import { canManageLicense, isWelcome, lockedTitle } from '../lib/license';
import LicensePage from './LicensePage';

export default function LicenseLockedPage() {
  const { user, logout } = useAuth();
  const manager = canManageLicense(user);
  const lic = user?.license;
  const welcome = isWelcome(lic?.reason);
  const title = lockedTitle(lic?.reason);
  useTitle(welcome ? 'Willkommen' : 'Lizenz gesperrt');
  const brand = (
    <div className="row-between">
      <div className="login-brand">
        <span className="brand-logo" aria-hidden="true">
          <BrandLogo />
        </span>
        {APP_NAME}
      </div>
      <button type="button" className="btn btn-ghost" onClick={() => void logout()}>
        <Icon name="logout" /> Abmelden
      </button>
    </div>
  );
  const info = (
    <HelpTip label="Erklärung zur Sperre">
      {welcome
        ? 'Diese Anwendung wurde noch nicht freigeschaltet. Mit der Lizenz, die Sie vom Anbieter erhalten haben, geht es sofort mit der Einrichtung der Schule weiter. Bis dahin ist nichts anderes erreichbar.'
        : `${lic?.message ? `${lic.message} ` : ''}Solange die Lizenz nicht erneuert ist, sind alle Seiten und Daten für alle Konten gesperrt. Es gehen keine Daten verloren – mit einer gültigen Lizenz ist sofort alles wieder da.`}
    </HelpTip>
  );
  if (!manager) {
    return (
      <div className="login-wrap">
        <main className="card login-card stack">
          {brand}
          <h1>
            {title} {info}
          </h1>
          <p>{welcome ? 'Diese Anwendung wird gerade eingerichtet. Bitte wenden Sie sich an die Administration.' : 'Bitte wenden Sie sich an die Schulleitung bzw. Administration.'}</p>
        </main>
      </div>
    );
  }
  return (
    <main className="page page-narrow stack">
      {brand}
      <h1>
        {title} {info}
      </h1>
      {welcome ? (
        <Alert kind="info">Lizenz eingeben, um fortzufahren.</Alert>
      ) : (
        <Alert kind="error">Die Anwendung ist für alle Konten gesperrt. Geben Sie unten eine neue Lizenz ein oder prüfen Sie die Lizenz erneut.</Alert>
      )}
      <LicensePage embedded onInstalled={welcome ? () => window.location.assign('/einrichtung') : undefined} />
    </main>
  );
}

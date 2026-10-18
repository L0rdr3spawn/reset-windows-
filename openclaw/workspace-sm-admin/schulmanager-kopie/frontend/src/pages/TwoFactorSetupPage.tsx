import { Navigate } from 'react-router-dom';
import { HelpTip } from '../components/HelpTip';
import { Alert } from '../components/ui';
import { useAuth, useUser } from '../context/AuthContext';
import { useTitle } from '../hooks/misc';
import { homePath } from '../lib/permissions';
import { TwoFactor } from './ProfilePage';

/** Pflichtseite, wenn die Rolle laut SM_REQUIRE_2FA_ROLES Zwei-Faktor-Anmeldung braucht. */
export default function TwoFactorSetupPage() {
  useTitle('Zwei-Faktor-Anmeldung einrichten');
  const user = useUser();
  const { logout } = useAuth();
  if (user.totp_enabled || !user.totp_setup_required) return <Navigate to={homePath(user)} replace />;
  return (
    <div className="login-wrap">
      <main className="card login-card">
        <h1>Zwei-Faktor-Anmeldung einrichten</h1>
        <Alert kind="info" title="Für Ihre Rolle verpflichtend">
          Scannen Sie den QR-Code mit einer Authenticator-App und bestätigen Sie mit dem angezeigten Code.
          <HelpTip>Zum Schutz der Schülerdaten ist für Ihr Konto eine Zwei-Faktor-Anmeldung vorgeschrieben. Geeignet sind z. B. FreeOTP, Aegis, Microsoft oder Google Authenticator.</HelpTip>
        </Alert>
        <TwoFactor />
        <div className="row-end" style={{ marginTop: 12 }}>
          <button type="button" className="btn btn-ghost" onClick={() => void logout()}>
            Abmelden
          </button>
        </div>
      </main>
    </div>
  );
}

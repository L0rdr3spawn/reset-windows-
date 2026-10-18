import { Link } from 'react-router-dom';
import { HelpTip } from '../../components/HelpTip';
import { Icon } from '../../components/Icon';
import { useUser } from '../../context/AuthContext';

/** Startseiten-Hinweis: die Schule empfiehlt Zwei-Faktor für diese Rolle, das Konto hat sie noch nicht. */
export default function TwoFactorHint() {
  const user = useUser();
  if (!user.totp_recommended || user.totp_enabled) return null;
  return (
    <section className="card" aria-label="Zwei-Faktor-Anmeldung empfohlen">
      <div className="card-head">
        <h2>
          Konto besser schützen
          <HelpTip>Für Ihre Rolle empfiehlt die Schule die Zwei-Faktor-Anmeldung mit einer Authenticator-App. Die Einrichtung dauert etwa eine Minute.</HelpTip>
        </h2>
        <Link className="btn btn-sm btn-primary" to="/zwei-faktor">
          <Icon name="shield" /> Jetzt einrichten
        </Link>
      </div>
    </section>
  );
}

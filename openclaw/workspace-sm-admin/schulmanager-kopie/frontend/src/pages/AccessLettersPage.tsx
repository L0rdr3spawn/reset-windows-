import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { http } from '../api/client';
import { Icon } from '../components/Icon';
import { Alert, AsyncButton } from '../components/ui';
import { useToast } from '../context/ToastContext';
import { useSettings } from '../hooks/useCollection';
import { useTitle } from '../hooks/misc';
import { formatLong, todayISO } from '../lib/dates';
import { ROLE_LABELS } from '../lib/permissions';
import type { LetterData } from './UsersPage';
import { APP_NAME } from '../brand';

/**
 * Druckbare Zugangsbriefe (Print-CSS). Daten kommen nur über den Router-State
 * (keine Speicherung von Passwörtern im Browser).
 */
export default function AccessLettersPage() {
  useTitle('Zugangsbriefe');
  const location = useLocation();
  const { data: settings } = useSettings();
  const navigate = useNavigate();
  // Daten einmalig übernehmen und aus dem Verlaufseintrag entfernen (Passwörter nicht im Browser-Verlauf)
  const [letters] = useState<LetterData[]>(() => ((location.state as { letters?: LetterData[] } | null)?.letters ?? []) as LetterData[]);
  const [onePerPage, setOnePerPage] = useState(true);
  const origin = window.location.origin;
  const toast = useToast();
  const downloadPdf = async () => {
    try {
      const blob = await http.post<Blob>('/users/letters.pdf', { letters, address: origin, one_per_page: onePerPage }, { blob: true });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Zugangsbriefe-${todayISO()}.pdf`;
      a.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 10_000);
    } catch (e) {
      toast.error(e, 'PDF');
    }
  };

  useEffect(() => {
    if (location.state) navigate(location.pathname, { replace: true, state: null });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!letters.length) {
    return (
      <div className="print-page">
        <Alert kind="info" title="Keine Zugangsdaten vorhanden">
          Zugangsbriefe entstehen direkt beim Anlegen oder Zurücksetzen. Passwörter werden nicht gespeichert.
        </Alert>
        <Link to="/benutzer" className="btn">
          Zur Benutzerverwaltung
        </Link>
      </div>
    );
  }

  return (
    <div className="print-page">
      <div className="print-toolbar">
        <Link to="/benutzer" className="btn">
          <Icon name="chevronLeft" /> Zurück
        </Link>
        <button type="button" className="btn btn-primary" onClick={() => window.print()}>
          <Icon name="print" /> Drucken ({letters.length})
        </button>
        <AsyncButton className="btn" onClick={downloadPdf}>
          <Icon name="download" /> Als PDF
        </AsyncButton>
        <label className="check">
          <input type="checkbox" checked={onePerPage} onChange={(e) => setOnePerPage(e.target.checked)} /> ein Brief pro Seite
        </label>
      </div>
      <div className={`letters${onePerPage ? ' one-per-page' : ''}`}>
        {letters.map((l) => (
          <section className="letter" key={l.username} aria-label={`Zugangsbrief ${l.display_name}`}>
            <div className="print-header">
              <h1>{settings?.school_name ?? APP_NAME}</h1>
              <span>{formatLong(todayISO())}</span>
            </div>
            <h2>Ihre Zugangsdaten zum {APP_NAME}</h2>
            <p>
              für <strong>{l.display_name}</strong>
              {l.class ? ` (Klasse ${l.class})` : ''}
              {l.role ? ` – ${ROLE_LABELS[l.role as keyof typeof ROLE_LABELS] ?? l.role}` : ''}
            </p>
            <dl className="cred">
              <dt>Adresse</dt>
              <dd>{origin}</dd>
              <dt>Benutzername</dt>
              <dd>{l.username}</dd>
              <dt>Startpasswort</dt>
              <dd>{l.temp_password}</dd>
            </dl>
            <p className="small">
              Bei der ersten Anmeldung werden Sie aufgefordert, ein eigenes Passwort festzulegen. Bitte bewahren Sie diesen Brief sicher auf und geben Sie Ihre Zugangsdaten nicht
              weiter. Auf dem Handy können Sie die Seite über „Zum Startbildschirm hinzufügen“ wie eine App nutzen. Optional lässt sich im Profil eine Zwei-Faktor-Anmeldung
              einrichten.
            </p>
          </section>
        ))}
      </div>
    </div>
  );
}

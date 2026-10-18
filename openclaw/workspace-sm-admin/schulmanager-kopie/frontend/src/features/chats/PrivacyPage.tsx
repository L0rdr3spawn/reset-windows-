/**
 * `/datenschutz` – Datenschutzhinweise für alle Nutzer/innen (Schüler/innen, Eltern, Lehrkräfte, Verwaltung):
 * welche Daten, wer sieht was, Verschlüsselung, Speicherdauer, Rechte. Ergänzt `docs/SICHERHEIT.md` (für die
 * Schulleitung); verbindlich ist die Datenschutzinformation der Schule.
 */
import { useSettings } from '../../hooks/useCollection';
import { useTitle } from '../../hooks/misc';

export default function PrivacyPage() {
  useTitle('Datenschutz');
  const { data: settings } = useSettings();
  const school = settings?.school_name || 'Ihre Schule';
  return (
    <div className="page stack" style={{ maxWidth: 860 }}>
      <div className="page-head">
        <h1>Datenschutz</h1>
      </div>
      <section className="card stack-sm">
        <h2 style={{ margin: 0 }}>Wer ist verantwortlich?</h2>
        <p>
          Verantwortlich für Ihre Daten ist <strong>{school}</strong> (Schulleitung). Die Plattform läuft auf einem Server der Schule bzw. ihres Schulträgers – Ihre Daten werden nicht an
          Werbe- oder Analysedienste weitergegeben und nicht für andere Zwecke genutzt. Fragen zum Datenschutz beantworten die Schulleitung und die/der Datenschutzbeauftragte der Schule.
        </p>
      </section>
      <section className="card stack-sm">
        <h2 style={{ margin: 0 }}>Welche Daten gibt es – und wer sieht sie?</h2>
        <ul>
          <li>
            <strong>Stundenplan, Vertretungen, Termine:</strong> alle Mitglieder der Schule, soweit sie sie betreffen (z. B. der eigene Plan, der Plan der Klasse).
          </li>
          <li>
            <strong>Krankmeldungen, Fehlzeiten, Entschuldigungen:</strong> das Kind bzw. die Eltern, die Klassenleitung, das Sekretariat und die Schulleitung. Fachlehrkräfte sehen nur, dass
            jemand fehlt – nicht den Grund. Gründe und Dokumente (z. B. Atteste) liegen verschlüsselt auf dem Server.
          </li>
          <li>
            <strong>Noten:</strong> die Schülerin/der Schüler, die Eltern (bei Volljährigen nur mit deren Freigabe) und die Lehrkräfte, die die Note vergeben haben bzw. die Klasse betreuen.
          </li>
          <li>
            <strong>Förderinformationen (z. B. Nachteilsausgleich):</strong> Familie, Klassenleitung, Lehrkräfte der Klasse (lesend), Sekretariat, Schulleitung – verschlüsselt gespeichert.
          </li>
          <li>
            <strong>Kursräume:</strong> Material und Aufgaben sehen die Mitglieder des Kurses. Abgaben sieht nur die abgebende Person und die Lehrkraft – nie andere Schüler/innen.
          </li>
          <li>
            <strong>Postfach:</strong> Betreff und Text sind auf dem Server verschlüsselt gespeichert. Lesen können nur Absender und Empfänger. Nur wenn eine Nachricht gemeldet wird, sieht die
            Moderation diese eine Nachricht (das wird protokolliert).
          </li>
        </ul>
      </section>
      <section className="card stack-sm">
        <h2 style={{ margin: 0 }}>Chats &amp; Gruppen: Ende-zu-Ende-Verschlüsselung</h2>
        <p>
          Chats werden <strong>auf Ihrem Gerät</strong> verschlüsselt (Verfahren wie bei Signal/libsodium: X25519 und XSalsa20-Poly1305). Den Schlüssel zum Lesen hat nur jedes Gerät der
          Mitglieder; er verlässt das Gerät nie. Der Server speichert nur unlesbare Daten sowie, wer Mitglied ist und wann geschrieben wurde. <strong>Auch die Schule und die Administration
          können Chats nicht lesen.</strong>
        </p>
        <ul>
          <li>Ein neues Gerät (oder ein gelöschter Browser-Speicher) kann ältere Nachrichten nicht mehr lesen – wie bei Signal.</li>
          <li>Wer später zu einer Gruppe hinzukommt, sieht keine älteren Nachrichten.</li>
          <li>Unter „Geräte“ sehen Sie Ihre Geräte mit Schlüssel-Fingerabdruck und können alte Geräte entfernen.</li>
          <li>
            Melden Sie eine Nachricht (z. B. bei Beleidigungen), schicken Sie freiwillig den Inhalt dieser einen Nachricht (Text und Bilder) an die Schulleitung mit – nur so kann die Schule helfen.
          </li>
        </ul>
      </section>
      <section className="card stack-sm">
        <h2 style={{ margin: 0 }}>Sicherheit</h2>
        <ul>
          <li>Passwörter werden nur als Hash gespeichert; Anmeldung optional mit Zwei-Faktor-Code.</li>
          <li>Vertrauliche Inhalte (Gründe, Dokumente, Noten, Nachrichten) sind in der Datenbank verschlüsselt; Schlüssel liegen getrennt von den Daten.</li>
          <li>Jede/r sieht nur, was er/sie für die eigene Aufgabe braucht (Rollen und Rechte). Änderungen werden protokolliert – ohne vertrauliche Inhalte.</li>
          <li>Für die Nutzung außerhalb des Schulnetzes muss die Verbindung verschlüsselt sein (HTTPS) – das stellt die Schule bei der Einrichtung sicher.</li>
        </ul>
      </section>
      <section className="card stack-sm">
        <h2 style={{ margin: 0 }}>Speicherdauer und Ihre Rechte</h2>
        <p>
          Daten werden gelöscht, wenn sie nicht mehr gebraucht werden (z. B. Postfach-Nachrichten nach der von der Schule eingestellten Frist, Konten nach dem Verlassen der Schule). Sie haben
          das Recht auf Auskunft, Berichtigung, Löschung bzw. Einschränkung im gesetzlichen Rahmen sowie auf Beschwerde bei der Datenschutz-Aufsichtsbehörde Ihres Landes. Wenden Sie sich
          dafür an die Schulleitung.
        </p>
      </section>
    </div>
  );
}

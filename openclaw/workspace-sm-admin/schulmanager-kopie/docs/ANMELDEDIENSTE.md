# Anmeldedienste einrichten (Microsoft, Google, Apple, Schulkonto)

Kurzanleitung für die Administration. Einstellungen: im Schulmanager unter **Anmeldedienste** (nur Rolle `admin`).
Dort stehen pro Anbieter die Adressen zum Kopieren, die beim Anbieter einzutragen sind, und ein Knopf „Verbindung testen“.
Client-ID, Geheimnisse und Schlüssel trägt nur die Administration selbst ein (Geheimnisse werden verschlüsselt gespeichert und nie wieder angezeigt).
Alternativ per Umgebungsvariablen (`SM_SSO_*`, `SM_OIDC_*`) – die haben Vorrang.

Wichtig vorab:

* `SM_BASE_URL` muss die Adresse sein, unter der die Leute die Seite öffnen – beim Heimserver
  `https://schulmanager.l0rdr3spawn.duckdns.org:10489` (mit Port!). Alle Adressen unten werden daraus gebildet.
* Wer sich anmelden darf, bestimmen weiterhin die **Anmelde-Richtlinien**. Die Anmeldung legt **kein** Konto an
  (außer die Schule erlaubt es ausdrücklich, `sso_create`): Das Anbieter-Konto muss mit einem Schulmanager-Konto verbunden
  sein (Profil → „Verbundene Konten“) oder in der Benutzerverwaltung für dessen E-Mail-Adresse vorgemerkt sein.
* Ohne eingeschalteten Anbieter lädt die Anmeldeseite **nichts** von Dritten. Erst wenn Google bzw. Apple eingeschaltet ist,
  wird deren Skript geladen (Google: `accounts.google.com/gsi/client`, Apple: `appleid.cdn-apple.com`) und die
  Content-Security-Policy dafür erweitert. Microsoft braucht kein Skript (nur Weiterleitung).
* Zwei-Faktor: Bei der Anmeldung über einen Anbieter gilt dessen eigene Anmeldung (inkl. dessen 2FA); die TOTP-Abfrage des
  Schulmanagers betrifft nur Benutzername + Passwort.
* Nach dem Abmelden ist die automatische Anmeldung (siehe unten) bis zur nächsten Anmeldung aus.
* nginx: Die App setzt die CSP selbst. Eine feste `Content-Security-Policy` im nginx würde zusätzlich gelten und die
  Anbieter-Skripte blockieren (Beispiel `deploy/nginx/schulmanager.conf`: Zeile entfernen). Caddy (`?Content-Security-Policy`)
  überschreibt nichts.

## Microsoft (Schul-/Arbeitskonten, Entra ID)

Kosten: kostenlos (Microsoft-Entra-Mandant der Schule, Rolle mit Recht zum Registrieren von Apps).

1. [entra.microsoft.com](https://entra.microsoft.com) → Entra ID → App-Registrierungen → **Neue Registrierung**.
   Unterstützte Kontotypen: „Nur dieses Verzeichnis“ (empfohlen) oder „Mehrere Verzeichnisse“.
2. Umleitungs-URI, Plattform **Web**: `https://schulmanager.l0rdr3spawn.duckdns.org:10489/api/v1/auth/sso/microsoft/callback`
   (genau so, mit Port – Entra erlaubt Ports bei https-Adressen).
3. Zertifikate & Geheimnisse → **Neuer geheimer Clientschlüssel** → den *Wert* kopieren (nur einmal sichtbar; läuft ab, Termin notieren).
4. Im Schulmanager: Client-ID (= Anwendungs-ID), Client-Secret, bei einer einzigen Schule die **Verzeichnis-ID** als Mandant eintragen
   (dann gelten die E-Mail-Adressen als bestätigt), einschalten, speichern, „Verbindung testen“.

Ablauf: offizieller Knopf „Mit Microsoft anmelden“ (Logo nach den Microsoft-Richtlinien), Weiterleitung, Code-Ablauf mit
PKCE und Nonce.
**Automatische Anmeldung (stilles SSO, abschaltbar, Standard aus):** Wer sich zuletzt mit Microsoft angemeldet hat und noch bei
Microsoft angemeldet ist, wird beim Öffnen der Anmeldeseite ohne Klick angemeldet (`prompt=none` mit `login_hint`, einmal je Tab).
Geht es nicht, erscheint ohne Fehlermeldung die gewohnte Seite. Bewusst **ohne MSAL.js**: Die Bibliothek wäre ein zusätzliches
Fremdskript, und sie bräuchte außerdem eine SPA-Registrierung; die serverseitige Weiterleitung leistet dasselbe.

## Google

Kosten: kostenlos.

1. [console.cloud.google.com](https://console.cloud.google.com) → Projekt anlegen → APIs & Dienste → **OAuth-Zustimmungsbildschirm**
   einrichten (Typ „Intern“ bei Google Workspace der Schule, sonst „Extern“; ein Test-/Veröffentlichungsstatus gilt nur für „Extern“).
2. Anmeldedaten → **OAuth-Client-ID erstellen**, Typ **Webanwendung**.
3. *Autorisierte JavaScript-Quellen*: `https://schulmanager.l0rdr3spawn.duckdns.org:10489` (nur Schema + Host + Port, kein Pfad).
   *Autorisierte Weiterleitungs-URIs*: `https://schulmanager.l0rdr3spawn.duckdns.org:10489/api/v1/auth/sso/google/callback`.
4. Client-ID und Clientschlüssel im Schulmanager eintragen; optional die Workspace-Domain (`hd`) und erlaubte E-Mail-Domains.

Ablauf: offizieller Knopf „Mit Google anmelden“ (Google Identity Services; Google liefert ein ID-Token an den Browser, der Server
prüft Signatur über Googles Schlüssel, `iss`, `aud`, `exp` und den Nonce). Fehlt das Skript (Werbeblocker), erscheint der gewöhnliche Knopf mit Weiterleitung.
**Automatische Anmeldung (One Tap mit Auto-Auswahl, abschaltbar, Standard aus):** blendet beim Öffnen der Anmeldeseite „Weiter als …“
ein; wer sich zuletzt mit Google angemeldet hat und in diesem Browser bei Google angemeldet ist, kommt ohne Klick hinein. Nur
auf eigenen Geräten sinnvoll, nicht auf gemeinsam genutzten Schulrechnern. Google schreibt künftig FedCM vor; der Knopf nutzt es.

Einschränkung Port: Google nennt Ports bei den JavaScript-Quellen in der Dokumentation nur für lokale Entwicklung. In der Praxis
werden Quellen mit Port meist akzeptiert, **zugesichert ist es nicht** – nach dem Eintragen mit einer Probeanmeldung prüfen. One Tap
zeigt Google zudem nur auf https-Seiten. Notfalls reicht die Weiterleitung (funktioniert mit Port).

## Apple („Mit Apple anmelden“)

Kosten und Voraussetzungen: **Apple Developer Program, 99 US-Dollar pro Jahr** (Schulen/Organisationen: DUNS-Nummer, ggf. Gebührenbefreiung
für Bildungseinrichtungen beantragbar). Außerdem eine Adresse **auf Port 443** (siehe Einschränkung).

1. [developer.apple.com](https://developer.apple.com/account) → Certificates, Identifiers & Profiles → **Identifiers**:
   falls nötig eine *App ID* (Haupt-ID) mit „Sign in with Apple“ anlegen, dann eine **Services ID** (z. B. `de.schule.anmeldung`) –
   das ist die Client-ID.
2. Services ID → „Sign in with Apple“ aktivieren → **Configure**: Haupt-App-ID wählen, *Domains* (nur Domain, **ohne Port**) und
   *Return URLs* eintragen: `https://<domain>/api/v1/auth/sso/apple/callback`.
3. **Keys** → neuer Schlüssel, „Sign in with Apple“ aktivieren → **.p8-Datei herunterladen** (nur einmal möglich) und Schlüssel-ID notieren.
4. Team-ID steht oben rechts im Developer-Konto.
5. Im Schulmanager: Services-ID, Team-ID, Schlüssel-ID und den Inhalt der .p8-Datei eintragen. Der Server erzeugt das Client-Secret
   selbst (ES256, kurz gültig). Einschalten, speichern, testen.

Ablauf: offizieller Apple-Knopf (Sign in with Apple JS, Popup); der Browser liefert ID-Token + Code, der Server prüft Signatur über
Apples Schlüssel (`appleid.apple.com/auth/keys`), `iss`, `aud`, `exp` und Nonce. Rückfall: Weiterleitung (`form_post`).
Apple kennt **keine stille/automatische Anmeldung** – es gibt sie hier deshalb nicht; die Anmeldung beginnt immer mit einem Klick.
Apple liefert Name und E-Mail nur bei der ersten Anmeldung; private Relay-Adressen (`…@privaterelay.appleid.com`) werden normal behandelt,
passen aber nicht zu vorgemerkten Schul-Adressen – dann im Profil verbinden.

**Einschränkung Port 10489:** Laut Apple-Entwicklerforum (Aussage der Apple-DTS) unterstützt „Sign in with Apple“ weder localhost noch
Adressen mit eigenem Port. Mit `…:10489` ist Apple also voraussichtlich **nicht** nutzbar. Lösung: den Schulmanager zusätzlich über
eine Adresse auf Port 443 erreichbar machen (Reverse-Proxy bzw. Router-Weiterleitung 443 → Heimserver, eigene Subdomain mit
Zertifikat) und `SM_BASE_URL` darauf stellen. Die Einstellungsseite zeigt bei Apple einen Hinweis, solange die Adresse einen Port hat.
Die CSP-Quellen für Apple (Skript, Popup, Schaltfläche) stammen aus Praxisberichten, nicht aus einer offiziellen Liste – bitte beim
ersten Test in der Browser-Konsole auf CSP-Meldungen achten.

## Schulkonto (OpenID Connect, z. B. Keycloak, IServ, Authentik)

1. Beim Identity Provider einen Client („Vertraulich“, Code-Ablauf) anlegen.
2. Weiterleitungs-URI: `…/api/v1/auth/oidc/callback` (unverändert, wie bisher).
3. Im Schulmanager: Aussteller-Adresse (Issuer), Client-ID, ggf. Client-Secret. Die Prüfung erfolgt wie bisher über den Token-Abruf per TLS.

## Welche Daten fließen wohin?

| Anbieter | Beim Laden der Anmeldeseite | Beim Anmelden |
| --- | --- | --- |
| keiner eingeschaltet | nichts von Dritten | – |
| Microsoft | nichts (kein Skript) | Browser wird zu `login.microsoftonline.com` geleitet; der Server tauscht den Code (Client-ID, Secret) |
| Google | Skript und Knopf von `accounts.google.com` (Google sieht IP-Adresse und Browser) | ID-Token (Kennung `sub`, Name, E-Mail) geht an den Schulmanager |
| Apple | Skript von `appleid.cdn-apple.com`, Knopf von `appleid.apple.com` | ID-Token (Kennung, E-Mail, ggf. Name) an den Schulmanager |

Der Schulmanager erhält nie ein Passwort. Er speichert die Kennung, die E-Mail-Adresse und den Zeitpunkt der letzten Anmeldung der
Verknüpfung. Im Browser liegt nur das Cookie `sm_sso_hint` (Anbieter + E-Mail für die automatische Anmeldung, 90 Tage, wird beim Abmelden gelöscht).
Auf der Anmeldeseite erklärt ein Hilfe-Knopf („?“) neben „oder“ den Datenschutz in Kürze.

## Kontowechsel

„Weiteres Konto anmelden“ im Benutzermenü zeigt dieselben Knöpfe; das bisherige Konto bleibt angemeldet (bis zu 5 Konten je Browser).

## Testbetrieb

Nur mit ausdrücklichem `SM_SSO_DEV_MOCK=1` **und** `SM_ENV=development` (Standard aus; nie in Produktion oder Demo, der Server startet sonst nicht) erscheinen nicht eingerichtete Anbieter als „Mit … anmelden (Test)“ – die
Anmeldung wird nur simuliert. Sobald ein Anbieter eingerichtet und eingeschaltet ist, verschwindet die Kennzeichnung für ihn.

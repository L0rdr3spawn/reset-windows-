# SSO-Anbieter einrichten: Anleitung für den Betreiber

Stand 16.10.2026. Diese Anleitung richtet sich an Sie als Betreiber von Schulpuls (Einzelperson, noch keine Firma). Sie beschreibt,
was Sie bei Google, Microsoft und Apple anlegen müssen, damit die Knöpfe „Mit Google/Microsoft/Apple anmelden“ echt funktionieren,
und was Sie in Schulpuls eintragen. Die Einstellungsseite im Programm ist **Anmeldedienste** (nur Administration);
die technischen Einzelheiten je Anbieter stehen in `docs/ANMELDEDIENSTE.md`. Die Bewertung am Ende ist keine Rechtsberatung.

## 1. Was Schulpuls jetzt tut

* Ein Knopf erscheint auf der Anmeldeseite nur, wenn der Anbieter **wirklich eingerichtet und eingeschaltet** ist
  (Client-ID, Geheimnis bzw. Schlüssel vorhanden). Sonst erscheint nichts, und es wird nichts von Dritten geladen.
* Der Knopf „Mit Schulkonto anmelden“ ist nicht mehr Teil der festen Knopfreihe und wird nie simuliert. Er erscheint nur, wenn eine
  Schule tatsächlich einen eigenen OIDC-Anbieter (Keycloak, IServ, Authentik, Schul-IdP) eingerichtet hat.
* Simulierte „(Test)“-Anbieter gibt es nur mit **beiden** Bedingungen: `SM_ENV=development` und `SM_SSO_DEV_MOCK=1`.
  Standard ist aus. In Produktion und in der Demo verweigert der Server den Start, wenn der Schalter gesetzt ist.
* Die Knöpfe folgen den Vorgaben der Anbieter: Google über das offizielle Skript „Sign in with Google“ (Google zeichnet den Knopf selbst),
  Apple über „Sign in with Apple JS“ (Knopf von Apple, schwarz, Beschriftung „Mit Apple anmelden“ über die Sprachvariante `de_DE`),
  Microsoft als „Mit Microsoft anmelden“ mit dem vierfarbigen Logo, 41 px hoch, Rand `#8C8C8C`, Text `#5E5E5E`, Schrift Segoe UI 15 px
  (dunkle Fläche `#2F2F2F` im dunklen Schema). Das Microsoft-Logo liegt als eingebettetes SVG im Code
  (`OfficialButtons.tsx`); Microsoft stellt es für diesen Zweck bereit, es darf nicht verändert werden. Google- und Apple-Logos liegen **nicht**
  im Repository, sie kommen zur Laufzeit vom Anbieter. Quellen der Vorgaben:
  [Microsoft: Branding guidelines](https://learn.microsoft.com/en-us/entra/identity-platform/howto-add-branding-in-apps),
  [Google: Sign in with Google branding](https://developers.google.com/identity/branding-guidelines),
  [Apple: Human Interface Guidelines, Sign in with Apple](https://developer.apple.com/design/human-interface-guidelines/sign-in-with-apple).
* Das Anmelden mit Zwei-Faktor ist jetzt zweistufig (Benutzername und Passwort, danach nur bei Bedarf der Code); siehe `docs/SICHERHEIT.md`.

## 2. Wichtigste Entscheidung vorab: eine Adresse oder viele Subdomains?

Das Problem: Eine Instanz je Schule unter einer eigenen Subdomain (`gym-musterstadt.schulpuls.de`) braucht bei jedem Anbieter
eine eigene Weiterleitungs-URI. Die Anbieter erlauben das unterschiedlich:

| Anbieter | Weiterleitungs-URIs | Wildcards | Grenze |
| --- | --- | --- | --- |
| Google | genau eine pro Eintrag, https Pflicht | nein | im Konsolen-Formular keine feste Zahl dokumentiert, in der Praxis einige Hundert |
| Microsoft | genau eine pro Eintrag, https Pflicht | nur bei Registrierungen, die ausschließlich Schul-/Arbeitskonten zulassen, und nur über das Manifest (von Microsoft nicht empfohlen) | 256 (nur Schul-/Arbeitskonten) bzw. 100 (mit privaten Konten), nicht erhöhbar |
| Apple | Domains und Return-URLs je Services-ID | nicht dokumentiert, verschachtelte Subdomains melden Entwickler als fehlerhaft | 10 Website-URLs bei Einzelperson, 100 bei Organisation |

Die drei Möglichkeiten:

**(a) Eine App-Registrierung je Schule.** Jede Schule (oder Sie für jede Schule) legt bei Google, Microsoft und Apple eigene Zugangsdaten an.
Für Microsoft ist das gut (die Schule registriert in ihrem eigenen Mandanten, kein Admin-Consent über Mandantengrenzen). Für Apple ist es
unbrauchbar (99 US-Dollar je Entwicklerkonto, Services-IDs je Schule) und für Google nur mit großem Pflegeaufwand. Sinnvoll nur für Schulen, die
ausdrücklich ihren eigenen Anmeldedienst wollen (das geht schon heute: Anbieter in der Instanz eintragen).

**(b) Eine zentrale Registrierung mit allen Adressen.** Einfach, solange es wenige Schulen sind. Apple (10 URLs bei Einzelperson), Microsoft (100 bis 256)
und das manuelle Eintragen jeder neuen Schule skalieren nicht; Wildcards sind keine Lösung. Jede neue Schule heißt: bei drei Anbietern Konsole öffnen.

**(c) Ein zentraler Anmelde-Vermittler `login.schulpuls.de` (Empfehlung).** Bei den Anbietern steht nur **eine** Adresse
(`https://login.schulpuls.de/callback/<anbieter>`). Der Vermittler führt den Anmeldeablauf aus und gibt das Ergebnis signiert an die Schul-Instanz zurück.
Pro Anbieter einmal einrichten, neue Schulen kosten keinen Aufwand bei den Anbietern, und Apple-Domainprüfung und Port-443-Pflicht gelten nur für eine Adresse.
Nachteil: Der Vermittler ist eine zusätzliche Komponente, die Sie betreiben und absichern müssen; er sieht kurzzeitig E-Mail-Adresse und Kennung der Anmeldung
(Auftragsverarbeitung klären, Abschnitt 7).

Ablauf bei (c) und Sicherheitsanforderungen:

1. Die Schul-Instanz erzeugt `state` (Zufallswert, an Sitzungs-Cookie gebunden), `nonce` und bei Bedarf PKCE-`code_verifier`, und leitet an
   `login.schulpuls.de/start?school=<kennung>&provider=google&state=<state>&return=<signierter Rückgabe-Hinweis>`.
2. Der Vermittler prüft, dass `school` zu einer **registrierten** Instanz gehört und die Rückgabeadresse exakt zu deren hinterlegter Adresse passt
   (Allowlist, kein freies `return=`; sonst Open Redirect und Token-Diebstahl).
3. Der Vermittler startet den Ablauf beim Anbieter mit eigenem `state`/`nonce`/PKCE (`code_challenge_method=S256`) und tauscht den Code serverseitig ein.
   Er prüft das ID-Token vollständig (Signatur, `iss`, `aud`, `exp`, `nonce`) und beim Mandanten-Anbieter Microsoft zusätzlich `tid`.
4. Er gibt **kein** Anbieter-Token weiter, sondern eine eigene, kurzlebige (höchstens 60 Sekunden), **einmal einlösbare** und signierte Behauptung
   (JWT mit Ed25519 oder ES256; `aud` = Schul-Instanz, `iss` = Vermittler, `sub`, `email`, `email_verified`, `nonce`, `jti`) per Browser-Weiterleitung
   (POST-Formular oder Fragment, nicht in der Abfragezeichenfolge, damit sie nicht in Logs landet).
5. Die Instanz prüft Signatur gegen den öffentlichen Schlüssel des Vermittlers, `aud` (nur die eigene Adresse), `exp`, `jti` (einmalig) und ihren eigenen `state`/`nonce`;
   ein Wert aus einer anderen Schule wird abgewiesen. Danach läuft die bestehende Verknüpfungs- und Richtlinienprüfung unverändert.
6. Der Vermittler speichert keine Personendaten außer einer kurzen Zwischenablage (ein paar Minuten) und kein Anmeldeprotokoll mit E-Mail im Klartext.

**Empfehlung:** (c) für Google und Apple; für Microsoft zusätzlich über denselben Vermittler, mit der Registrierung als „Mehrere Verzeichnisse“.
**Zu Beginn mit einer einzigen Schule reicht (b) mit genau einer Adresse**, sofern Sie eine feste Adresse auf Port 443 haben; der Vermittler (c) wird erst gebaut, wenn die zweite Schule mit eigener Subdomain kommt.
Der Vermittler ist noch **nicht** gebaut; Schulpuls enthält heute den Ablauf je Instanz (Abschnitte 3 bis 5).

## 3. Google

Kosten: kostenlos. Als Einzelperson möglich (normales Google-Konto).

1. [console.cloud.google.com](https://console.cloud.google.com): Projekt anlegen (z. B. „Schulpuls Anmeldung“).
2. APIs und Dienste, **OAuth-Zustimmungsbildschirm** (heute „Google Auth Platform“): Nutzertyp **Extern**; App-Name, Support-E-Mail, Logo (optional),
   Link zur Datenschutzerklärung und zu den Nutzungsbedingungen, autorisierte Domain (Ihre Hauptdomain).
3. Bereiche (Scopes): nur `openid`, `email`, `profile`. Das sind nicht-sensible Bereiche; eine Überprüfung (Verification) ist dafür **nicht** vorgeschrieben.
   Für den Betrieb für alle Nutzer den Status von „Test“ auf **„In Produktion“** stellen (Knopf „App veröffentlichen“). Im Teststatus sind nur eingetragene Testnutzer zugelassen.
   Wer Name und Logo auf dem Zustimmungsbildschirm sehen will, braucht die leichte Markenüberprüfung (Brand Verification, dafür eine bestätigte Domain).
   Hinweis: In Drittquellen ist von einer Grenze von 100 Konten für nicht überprüfte Apps die Rede; bei ausschließlich Basis-Bereichen gilt laut Google keine Warnung und keine Ablaufzeit.
   Prüfen Sie die aktuelle Seite [Google: Überprüfung einreichen](https://support.google.com/cloud/answer/13461325), bevor Sie mehrere Schulen anbinden.
4. Anmeldedaten, **OAuth-Client-ID**, Typ **Webanwendung**:
   * Autorisierte JavaScript-Quellen: `https://<ihre-adresse>` (bei Variante (c) `https://login.schulpuls.de`; bei Variante (b) je Schule eine).
   * Autorisierte Weiterleitungs-URIs: `https://<ihre-adresse>/api/v1/auth/sso/google/callback`. Muster oder `*` sind nicht erlaubt; https ist Pflicht; Pfad, Groß-/Kleinschreibung und Schrägstrich am Ende müssen exakt stimmen.
5. In Schulpuls (Anmeldedienste, Google): Client-ID und Clientschlüssel eintragen, optional erlaubte E-Mail-Domains, einschalten, „Verbindung testen“.
   Das Geheimnis wird verschlüsselt gespeichert und nie wieder angezeigt.

## 4. Microsoft (Entra ID)

Kosten: kostenlos. Ein Entra-Mandant ist nötig (mit einem kostenlosen Microsoft-Konto lässt sich einer anlegen, wenn Ihr Konto noch keinen hat; in der Azure-Anmeldung als „Verzeichnis“ sichtbar).

1. [entra.microsoft.com](https://entra.microsoft.com): Entra ID, App-Registrierungen, **Neue Registrierung**.
2. Unterstützte Kontotypen:
   * Eine Schule mit Microsoft 365, die Ihre App im eigenen Mandanten nutzt: „Nur dieses Verzeichnis“ (Schule registriert selbst, Variante (a)).
   * Mehrere Schulen aus einer zentralen Registrierung: **„Konten in einem beliebigen Organisationsverzeichnis (mehrmandantenfähig)“**. Private Microsoft-Konten
     bewusst nicht dazunehmen (sonst nur 100 statt 256 Weiterleitungs-URIs, keine Wildcards, keine Abfrageparameter).
3. Plattform **Web**, Umleitungs-URI `https://<ihre-adresse>/api/v1/auth/sso/microsoft/callback`.
4. Zertifikate und Geheimnisse: neuer Clientschlüssel (Wert sofort kopieren; läuft ab, Termin notieren).
5. API-Berechtigungen: nur `openid`, `profile`, `email` (delegiert, Standard `User.Read` kann bleiben). Das braucht keine Administratorzustimmung durch Sie;
   ob **Nutzer der Schule** selbst zustimmen dürfen, entscheidet der Administrator des Schul-Mandanten (Einstellung „Benutzereinwilligung“). Ist sie abgeschaltet oder auf „verifizierte
   Herausgeber“ begrenzt, sieht der Nutzer „Genehmigung erforderlich“. Dann muss der Schul-IT-Admin einmalig die **Administratorzustimmung** für die ganze Schule erteilen
   (Entra, Unternehmensanwendungen, Berechtigungen, „Administratorzustimmung erteilen“; er erhält dafür einen Link der Form `https://login.microsoftonline.com/<schul-tenant>/adminconsent?client_id=<ihre-client-id>`).
   Eine **Herausgeber-Verifizierung** (Publisher Verification) setzt ein Microsoft-AI-Partnerprogramm-Konto voraus und ist als Privatperson praktisch nicht zu bekommen; ohne sie ist die Einwilligung durch Nutzer in streng eingestellten Schulen meist gesperrt, mit Administratorzustimmung geht es trotzdem.
6. In Schulpuls: Client-ID (= Anwendungs-ID), Clientschlüssel; Feld Mandant: Verzeichnis-ID der Schule (nur bei einer Schule) oder `organizations` (mehrere); einschalten, testen.
   Nur bei fester Verzeichnis-ID gelten die E-Mail-Adressen als bestätigt.

## 5. Apple

Kosten und Voraussetzungen: **Apple Developer Program, 99 US-Dollar pro Jahr.** Als Einzelperson möglich (volljährig, Apple-Konto mit Zwei-Faktor, echter Name; keine Firma und keine
D-U-N-S-Nummer nötig). Für eine Organisation (Verein, GmbH) braucht es eine D-U-N-S-Nummer. Schulen und gemeinnützige Einrichtungen können eine Gebührenbefreiung beantragen.
Einschränkungen als Einzelperson: höchstens 10 Website-URLs je Services-ID (Organisation 100).

1. [developer.apple.com/account](https://developer.apple.com/account): Zertifikate, IDs und Profile, **Identifiers**. Zuerst eine **App-ID** (Haupt-ID, Typ App) mit „Sign in with Apple“ anlegen (ohne App genügt eine Platzhalter-ID).
2. Eine **Services-ID** anlegen (z. B. `de.schulpuls.anmeldung`), „Sign in with Apple“ aktivieren, **Konfigurieren**: Haupt-App-ID wählen; **Domains und Subdomains** (nur Domain, **ohne Port**, **Ihre** Domain) und
   **Return URLs** (`https://<ihre-adresse>/api/v1/auth/sso/apple/callback`). Eine Domain-Datei muss laut aktueller Dokumentation nicht hochgeladen werden. Wildcards sind nicht dokumentiert; verschachtelte Subdomains
   (`a.b.schulpuls.de`) werden laut Entwicklerberichten nicht zuverlässig übernommen. Hier ist der Vermittler (c) fast zwingend.
3. **Schlüssel** (Keys): neuer Schlüssel mit „Sign in with Apple“, **.p8-Datei herunterladen** (nur einmal möglich) und Schlüssel-ID notieren. Die Team-ID steht oben rechts im Konto.
4. Apple verlangt Adressen auf **Port 443** und kein localhost.
5. In Schulpuls: Services-ID, Team-ID, Schlüssel-ID und Inhalt der .p8-Datei eintragen. Der Server erzeugt das Client-Secret selbst (ES256, kurz gültig; Apple erlaubt höchstens sechs Monate).
6. Hinweise: Apple liefert Name und E-Mail **nur bei der ersten Anmeldung**. Wählt die Person „E-Mail-Adresse verbergen“, kommt eine Relay-Adresse (`…@privaterelay.appleid.com`) statt der Schul-Adresse; sie passt nicht zu vorgemerkten Adressen,
   die Verknüpfung muss dann im Profil („Verbundene Konten“) angestoßen werden. Soll Schulpuls selbst Mails an diese Adresse schicken, müssen Sie Ihre Absenderdomain bei Apple für den privaten E-Mail-Relay registrieren (SPF/DKIM).

## 6. Was Sie in Schulpuls eintragen

| Wo | Was |
| --- | --- |
| Umgebung `SM_BASE_URL` | die Adresse, unter der die Instanz erreichbar ist (mit https, bei Apple Port 443) |
| Anmeldedienste, je Anbieter | Client-ID, Geheimnis bzw. Apple-Schlüssel, Mandant (Microsoft), erlaubte Domains; dann „Einschalten“ und „Verbindung testen“ |
| Anmelde-Richtlinien | wer sich über welchen Anbieter anmelden darf; der Anbieter-Login legt standardmäßig **kein** Konto an |
| Benutzerverwaltung / Profil | E-Mail der Person vormerken oder im Profil unter „Verbundene Konten“ verbinden |

Alternativ per Umgebungsvariablen `SM_SSO_*` (haben Vorrang). Echte Geheimnisse gehören nie in den Code, nie ins Repository und nicht in Chats.

## 7. Datenschutz, Bewertung und Alternativen (keine Rechtsberatung)

* **Google und Apple für Minderjährige.** Schüler unter 16 haben meist kein eigenes Google- oder Apple-Konto oder nur ein elterlich verwaltetes (Family Link, Apple-Familienfreigabe, Mindestalter je Dienst 13 bis 16). Eine
  verpflichtende Anmeldung über diese Dienste würde Kinder zwingen, ein Konto bei einem US-Konzern zu führen, und die Schule fördert damit die Weitergabe von IP-Adresse und Nutzungszeitpunkt an diesen Konzern (Drittlandübermittlung,
  Schrems-II-Diskussion; Google lädt außerdem ein Skript beim Seitenaufruf). Datenschutzaufsichten sehen in vielen Ländern Schul-Logins über Social-Login kritisch; üblich ist, dass es **freiwillig** und nur für Volljährige/Personal bleibt.
  Die Einwilligung muss freiwillig sein, die Passwort-Anmeldung muss gleichwertig bleiben. **Empfehlung:** Google und Apple in Schulpuls nur als freiwillige Zusatzoption für Personal und Eltern, für Schüler standardmäßig aus (steuerbar über die Anmelde-Richtlinien je Rolle).
* **Microsoft.** Sinnvoll für Schulen, die bereits Microsoft 365 / Entra als Schulkonto-System nutzen: kein zusätzliches Konto, Verwaltung und Datenschutz liegen beim bestehenden Vertrag der Schule. Für Schulen ohne Microsoft 365 nutzlos.
* **Bessere Alternativen für den Schulbetrieb.**
  1. **Schulconnex / VIDIS** (Landes-Anmeldedienste, z. B. NRW über die Landesplattform, bundesweit die Vermittlung von Identitäten und Schulconnex-Daten): Die Schule hat dort bereits Konten für Schüler und Lehrkräfte; Anbieter wie Schulpuls müssen sich als Dienst anbinden lassen (Antrag beim Land bzw. bei VIDIS, Prüfung, Vertrag). Das ist der naheliegende Standard, kostet aber Zeit und Nachweise (Datenschutz, Sicherheit). Aktuelle Bedingungen und Ansprechpartner bei Ihrem Land erfragen; diese Angaben sind hier nicht geprüft.
  2. **Eigener Schul-IdP über OpenID Connect** (Keycloak, IServ, Authentik, Entra der Schule): Schulpuls unterstützt das bereits als „Schulkonto“; die Schule trägt Issuer, Client-ID und Geheimnis selbst ein. Kein Dritter im Spiel, keine Gebühren, voll im Datenschutzrahmen der Schule.
  3. **Eigenes Passwort + Zwei-Faktor** bleibt der robuste Grundweg für alle.
* **Auftragsverarbeitung.** Bei einem Vermittler (c) verarbeiten Sie E-Mail-Adressen und Kennungen im Auftrag der Schulen: Vertrag zur Auftragsverarbeitung, Eintrag im Verzeichnis der Verarbeitungstätigkeiten, TLS, knappe Speicherung. Außerdem Datenschutzerklärung und Nutzungsbedingungen (bei Google nötig).

**Gesamtbewertung:** Technisch ist alles vorhanden. Sinnvoll für Schulpuls ist: zuerst Microsoft (Schulen mit M365) und „Schulkonto“ per OIDC bzw. später Schulconnex/VIDIS;
Google und Apple nur als freiwillige Option für Erwachsene. Apple kostet 99 US-Dollar im Jahr und verlangt eine Adresse auf Port 443; den Aufwand lohnt es erst, wenn Nutzer das ausdrücklich wollen.

## 8. Checkliste für Sie

1. Entscheiden: Variante (b) mit einer Adresse jetzt, (c) später.
2. Adresse auf Port 443 mit gültigem Zertifikat und `SM_BASE_URL` setzen.
3. Je Anbieter die Schritte oben ausführen; Geheimnisse nur in der Einstellungsseite eintragen.
4. Datenschutzerklärung und Nutzungsbedingungen veröffentlichen (für Google verlangt).
5. Anmelde-Richtlinien setzen (Rollen, die den Anbieter nutzen dürfen), „Verbindung testen“, Probeanmeldung.
6. Erneuerungstermine notieren: Microsoft-Clientschlüssel, Apple-Entwicklerkonto (jährlich), Apple-Schlüssel.
7. Auf dem Server `SM_SSO_DEV_MOCK` nicht setzen (oder auf 0), `SM_ENV=production`.

## Quellen

* [Google: Weiterleitungs-URI-Regeln, OAuth 2.0 für Webserver-Anwendungen](https://developers.google.com/identity/protocols/oauth2/web-server)
* [Google: App-Überprüfung einreichen](https://support.google.com/cloud/answer/13461325)
* [Microsoft: Redirect URI best practices and limitations](https://learn.microsoft.com/en-us/entra/identity-platform/reply-url)
* [Microsoft: User and admin consent overview](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/user-admin-consent-overview)
* [Apple: Configure Sign in with Apple for the web](https://developer.apple.com/help/account/configure-app-capabilities/configure-sign-in-with-apple-for-the-web)
* [Apple: Enroll in the Apple Developer Program](https://developer.apple.com/programs/enroll/)

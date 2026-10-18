Du übernimmst ein laufendes Projekt. Lies zuerst den Skill `schulpuls-atlas` und mein Gedächtnis (MEMORY.md), dann die unten genannten Berichte. Antworte auf Deutsch, siez alle.

# Projekt
„Schulpuls“ (interner Arbeitstitel, technisch `schulmanager`): Schulverwaltungs- und Lernplattform, FastAPI + SQLAlchemy + React. Ziel: vollständig an deutsche Schulen verkaufbar.
- Repo/Arbeitsbaum: `C:\Users\reiss\Documents\claude\Claude.Code-merge` (Branch `claude/magical-newton-dcni3v`, viel UNCOMMITTET, nichts ohne meine Ansage committen/pushen, kein git checkout/stash/reset/clean).
- Externer Code-Atlas (nie ausliefern): `C:\Users\reiss\Documents\claude\schulpuls-atlas\`. Immer zuerst dort nachschlagen (`atlas.py find`, `INDEX.md`, `features/<bereich>.md`).
- Code-Wissensgraph (Graphify, lokal, ohne KI): `schulpuls-atlas\graph\graphify-out\`, Abfrage `graphify query "<frage>" --graph .../graph.json`, Update `tools\schulpuls-atlas\graph-update.sh`.
- Lizenzserver (nur beim Anbieter, nie an Schulen): `lizenzserver/`. Updater: `updater/`.

# Regeln (wichtig)
- Sichtbarer Produktname nur über `PRODUCT_NAME` (`schulmanager/branding.py`) bzw. `APP_NAME` (`frontend/src/brand.ts`); technisch heißt alles `schulmanager`.
- Sie-Form überall (auch Schüler), Erklärungen nur als (i)/HelpTip, App-Dialoge statt Browser-Popups, ein Raster (DayPeriodGrid/TimetableGrid), fremde Daten → 404, jede schreibende Aktion `audit()`, Freitexte verschlüsselt, Schema nur per Alembic (aktueller Migrationskopf: 0068), Planungsdokument nur über `mutate`.
- Subagenten: NICHT Fable (zu teuer) – komplexe Arbeit auf Sonnet, einfache Scans/Bewertungen auf Haiku. Dateihoheit je Agent festlegen, Atlas-Pfad + Graph-Update in den Auftrag schreiben, „nur Tests der geänderten Bereiche“, „nicht committen“, keine Keys/Passwörter in Prompts.
- Server NUR auf dem Heimserver (`ssh server`), nie dauerhaft auf dem PC. Der PC verliert gelegentlich Daten auf Loopback → **Backend-Gesamttest besser auf dem Heimserver** laufen lassen (`docker build --target dev -t schulmanager:testlauf-dev .`, dann Image mit gemountetem src, `pytest`). Vor CPU-schweren Läufen kurz Bescheid sagen.
- Credentials/Lizenzschlüssel nur in Desktop-Dateien, nie in den Chat.

# Stand (17.10.2026) – auf allen 3 Instanzen deployt (Image `schulmanager:neu-2026-10-17`)
Hauptserver `schulmanager`, Demo `schulmanager-demo`, Test-Instanz `schulmanager-neu` (alle unter `l0rdr3spawn.duckdns.org:10489`, laufen mit `SM_ENV=development`).
Live seit heute: Welle 1 (11 Sicherheits-/Qualitätspakete), API-Schreibzugang + API-Protokoll, frei vergebbare Rechte + eigene Rollen, Einrichtung einer neuen Schule von Null (Import optional), Betatester-Beobachtung + Inhaber-Schutz, Impressum/Datenschutz als Mustertexte der Schule (Platzhalter, kein Anbietername), Betreiber-Hilfe (Anleitungen nur für Zuständige), Monitor-Menü (Abmelden/Konto wechseln), Abmeldelink in Mails, Tempo-Limit, Doppelsende-Schutz Chat, Fetch-Timeout, viele Aufräum-Fixes der Code-Durchsicht.
- Vorfall vom 16.10. (fremdes Admin-Konto `thorsten`/`luemmel`) ist bereinigt.
- Betatester-Konto `betatester` auf dem Hauptserver: Admin, beobachtet, darf keine Admins anlegen; Startpasswort nur in `Desktop\Schulmanager Testzugaenge.txt`.

# Wichtige Berichte (im Atlas unter doku/intern)
- `SICHERHEITSAUDIT-2026-10-17.md` – 49 Funde (1 kritisch live entschärft, 11 hoch) gegen real verklagte Fehler.
- `PENTEST-DYNAMISCH-2026-10-17.md` – dynamischer Pentest, 3 hohe Lücken live ausgenutzt, viele Abwehrmechanismen bestätigt.
- `CODE-DURCHSICHT-2026-10-17.md`, `CHECKLISTE-REELS-2026-10-17.md`, `RESTORE-TEST-2026-10-17.md`.

# NÄCHSTER SCHRITT: Sicherheits-Welle 1 (hoch) – bitte umsetzen, mit Regressionstests, dann auf dem Heimserver testen und deployen
Live bestätigte hohe Lücken:
1. **Inhaber-Schutz zentral:** Ein zweiter Admin kann das Inhaber-Passwort über `POST /letters/batches` (Zugangsbrief-Stapel) zurücksetzen, obwohl die direkten Wege 403 liefern. Schutzprüfung in die zentrale Konto-Änderung (`accounts.py`) verlegen, damit auch Massen-/Brief-Reset, Token- und Sitzungslöschung des Inhabers geschützt sind. (`watch.py` `guard_owner`, `routes/features_letters.py`, `routes/users.py`)
2. **Export-Scope + Audit:** `GET /api/v1/export/json` und `/export/schulmanager-online.zip` geben alle Schüler inkl. Geburtsdatum aus – auch an die Rolle `zuschauer` und schon mit `masterdata.edit`/`timetable.edit`. An `students.read` + Scope binden, Geburtsdatum nur mit eigenem Recht, alle Stammdaten-Exporte protokollieren.
3. **API-Token-Lebenszyklus:** Jede Rolle (auch Schüler) kann Tokens ausstellen; sie sind unbefristet und überleben Passwortwechsel/Reset/Sperre/2FA-Reset. Ausstellen nur mit Recht/Freigabe, Pflichtlaufzeit, Widerruf bei allen Konto-Ereignissen; Schreib-Tokens per Allowlist statt Blocklist (Export-/Auskunftswege sperren).
4. **2FA-Pflicht für Admins** (Standard an) + Wiederherstellungscodes.
5. **IP-Kürzung + Datenschutztext:** Datenschutzerklärung/VVT versprechen gekürzte IPs, gespeichert werden sie voll (Audit 365 Tage). IP kürzen bzw. Frist senken UND die Mustertexte an die Wirklichkeit anpassen; bei aktivem Google/Apple-Login den „keine fremden Skripte“-Hinweis bedingt ergänzen.
Danach Sicherheits-Welle 2 (mittel): Scope-Grenzen bei freier Rechtevergabe, SSE-Rechte nach Logout, Volljährigkeit (iCal/Dokumente), Beobachtung für Betroffene unsichtbar + Zeitleisten-Audit, CSV-Formel-Schutz in 5 Exporten (`forms.csv_cell`), Alarm bei Massenzugriffen, Erklärung zur Barrierefreiheit, Auskunft vollständig (Protokolle zu Schülern), Löschfristen mit Landesbezug.

# Offene Fragen an mich (noch nicht beantwortet)
- Test-Instanz „neu“ (und künftige Schulen) auf `SM_MODE=production` umstellen? (Im Dev-Modus fehlen Härtungen.)
- Untis-Import: 8 Feldzuordnungen brauchen einen echten Untis-Export zur Bestätigung.
- Danach: große Fehlerbehebungs-Runden 2–4 und die 10 kleinen Wettbewerbs-Lücken aus `BEWERTUNG-2026-10-16.md` / `WETTBEWERB-KLEINE-LUECKEN.md`.

# Deploy-Rezept (kurz)
Arbeitsbaum über temporäres GIT_INDEX_FILE als tar.gz archivieren (core.autocrlf=false), nach `~/schulmanager/src.new` entpacken, Image bauen, Dry-Run mit DB-Kopie, dann `Desktop\schulmanager-deploy-update.sh` anpassen (`NEW=`) und `ssh server 'sh -s' < script`. Details im Projekt-Gedächtnis `schulmanager-deploy` und in `schulpuls-atlas`.

# Schulmanager – Speicher-, Verkehrs- und Lastkalkulation (1 Jahr Heimserver)

Stand: 2026-10-12. Reine Rechnung auf Basis des Codes (Repo `Claude.Code-merge`) und lesender Messung am
Testserver. **Es wurde nichts geändert.** Alle Nutzungszahlen sind **Annahmen** (Abschnitt 1) – die Faktoren
sind so aufgeschrieben, dass man sie austauschen und neu rechnen kann. Eine Messung unter echter Last gibt es
nicht (außer dem früheren lokalen Lasttest mit 150 gleichzeitigen Nutzern ohne Fehler); CPU-Werte sind daher
**Schätzungen**.

---

## 0. Ergebnis in 30 Sekunden

| | Klein (1.000 Schüler) | Mittel (2.500) | Groß (5.000) |
|---|---|---|---|
| Konten gesamt (Schüler + Lehrer + Eltern 1,5/Kind) | 2.580 | 6.450 | 12.900 |
| **Jahr 1, Standardbetrieb, ohne Chat-Bilder** (Dateien + DB) | **≈ 51 GB** | **≈ 127 GB** | **≈ 255 GB** |
| Jahr 1 **mit** Chat-Bildern (1 Bild/Schüler/Woche, DB-BLOBs) | ≈ 117 GB | ≈ 291 GB | ≈ 583 GB |
| Jahr 1 **optimiert** + Löschkonzept | ≈ 37 GB | ≈ 92 GB | ≈ 184 GB |
| Stand nach 5 Jahren: Standard / optimiert | 244 GB / 60 GB | 611 GB / 149 GB | 1,2 TB / 299 GB |
| **Backup-Bedarf** Jahr 1 mit Standard-Rotation (34 Voll-Archive) | ≈ 1,4 TB | ≈ 3,5 TB | ≈ 7,1 TB |
| Backup-Bedarf Jahr 1 mit inkrementellem Backup (restic/borg) | ≈ 36 GB | ≈ 90 GB | ≈ 180 GB |
| Anfragen je Schultag / Spitze beim Unterrichtsbeginn | 46 k / ≈ 40 req/s | 115 k / ≈ 100 req/s | 231 k / ≈ 190 req/s |
| Ausgehender Datenverkehr je Schultag (Standard, ohne / mit Chat-Bildern) | 0,8 / 2,5 GB | 1,9 / 6,2 GB | 3,9 / 12,5 GB |
| Mindest-**Upload** des Heimanschlusses (inkl. Reserve) | 10 Mbit/s | 25 Mbit/s | 50 Mbit/s (Glasfaser) |

Die zwei größten Hebel sind keine Nutzerdaten, sondern **Architektur-Details**:
1. Das Backup (`scripts/backup.sh`) packt die Dateiablage **jede Nacht komplett neu** in ein `tar.gz`
   (verschlüsselte Dateien sind nicht komprimierbar) und hält 14 + 8 + 12 Generationen – das vervielfacht den
   Bedarf um ≈ 30 und ist über einen Heim-Upload nicht auslagerbar.
2. **Chat-Bilder liegen als BLOB in der Datenbank** (`ChatAttachment.data`) und werden vor dem Senden nur dann
   verkleinert, wenn sie > 5 MB sind. Damit wächst die DB (und jedes DB-Backup) um Größenordnungen schneller als
   ohne Bilder.

---

## 1. Annahmen (offen gelegt)

### 1.1 Schulgrößen

| Größe | Schüler | Lehrkräfte | Eltern (1,5/Kind) | Konten | Klassen (à 25) |
|---|---|---|---|---|---|
| Klein | 1.000 | 80 | 1.500 | 2.580 | 40 |
| Mittel | 2.500 | 200 | 3.750 | 6.450 | 100 |
| Groß | 5.000 | 400 | 7.500 | 12.900 | 200 |

Schuljahr: 38 Schulwochen = **190 Schultage**. Der Testserver (≈ 5.500 Konten, 14 Klassen/Jahrgang) liegt
zwischen „Mittel“ und „Groß“.

### 1.2 Nutzungsprofil (für alle Größen gleich, je Kopf)

| Bereich | Annahme | Anmerkung |
|---|---|---|
| Hausaufgaben/Abgaben | 1,5 Abgaben/Schüler/Woche, davon 40 % mit Datei; Datei = 50 % Foto (Standard **2,5 MB**, Spanne 1–4 MB) / 50 % PDF (0,8 MB, Spanne 0,2–2 MB) | → Ø 1,65 MB je Abgabedatei; 0,6 Dateien/Schüler/Woche |
| Unterrichtsmaterial | 2,5 Dateien/Lehrkraft/Woche à 1,0 MB (PDF/DOCX/PPTX) | bleibt liegen, solange nicht gelöscht |
| Atteste/Dokumente | 4 Fehlzeiten/Schüler/Jahr, 25 % mit Scan (50 % Foto 2,5 MB / 50 % PDF 0,3 MB) | Frist 400 Tage (`config.py:188`) |
| Postfach (Einzel) | Lehrer 15, Schüler 1, Eltern 0,7 Nachrichten/Woche; 2 % mit Anhang à 0,4 MB; Antworten +50 % | |
| Rundschreiben | Klein/Mittel/Groß: 4 / 8 / 15 je Woche, Ø 300 / 800 / 1.500 Empfänger, 30 % mit Anhang 0,4 MB | |
| Chat-Text | **5 Nachrichten/Schüler/Schultag** (Ø über alle, inkl. Inaktive); 60 % Zweier-Chats, 40 % Gruppen à Ø 20 Mitglieder; **1,3 Geräte/Person** | → Ø 12 Empfangsgeräte je Nachricht |
| Chat-Bilder | Variante „ohne“: 0; Variante „mit“: **0,2 Bild/Schüler/Schultag** (≈ 1/Woche), Ø 1,5 MB (Handyfoto/GIF/Screenshot-Mix; nur > 5 MB wird verkleinert) | größte Unsicherheit! |
| Klassenbuch | 6 Stunden/Klasse/Tag, 800 B je Eintrag (verschlüsselt, inkl. Index) | |
| Fehlzeiten/Noten | 25 Fehlzeit-Einträge à 450 B und 30 Noten à 150 B je Schüler/Jahr | |
| Audit-Log | 0,3 Logins/Konto/Schultag + 4 Klassenbuch-Speicherungen/Lehrer/Tag + 0,4 Abgabe-Ereignisse/Schüler/Tag + 100 Planänderungen/Tag; Ø **220 B/Zeile** (gemessen: Details Ø 38 Zeichen) | wird nie gelöscht (siehe 2.7) |
| Aktive Nutzer je Schultag | Schüler 80 %, Lehrer 95 %, Eltern 25 % | |
| Verkehr je aktivem Nutzer/Tag | Schüler 35 Requests/100 KB JSON, Lehrer 180 Req/1 MB, Eltern 12 Req/50 KB (gzip) | Annahme, nicht gemessen |
| Backups | Standard-Rotation des Repos: täglich 14, wöchentlich 8, monatlich 12 (`BACKUP_KEEP_*`) | |

### 1.3 Varianten der Rechnung

* **A – Standard, ohne Chat-Bilder** (Code wie heute, Chat nur Text)
* **B – Standard, mit Chat-Bildern** (wie A + 0,2 Bild/Schüler/Tag als DB-BLOB)
* **C – Optimiert + Löschkonzept** (Maßnahmen aus Abschnitt 4: Bilder clientseitig verkleinern, schlankeres
  Chat-Schlüsselschema, Fristen für Audit/Chat/Abgaben, inkrementelles Backup)

Pauschaler DB-Aufschlag: +15 % (SQLite-Freiseiten/WAL; PostgreSQL ähnlich).

---

## 2. Speicher – Rechnung je Bereich

### 2.1 Grundlagen aus dem Code (Beleg)

| Befund | Stelle |
|---|---|
| Datei-Upload max. **25 MB** (`SM_UPLOAD_MAX_MB`), Zweck-Regeln: Beiträge 10 MB, Schüler-Dokumente 15 MB (nur PDF/Bild) | `schulmanager/server/config.py:180`, `routes/features_channels.py:1233`, `routes/features_student_self.py:48` |
| **Kontingent** je Konto: Lehrkräfte 2.000 MB, Schüler 200 MB (zählt nicht gelöschte Dateien) → harte Obergrenze: Klein 200 GB/160 GB, Mittel 500/400 GB, Groß 1.000/800 GB (Schüler/Lehrer) | `config.py:181-182`, `files.py:894-915` |
| Dateien liegen **verschlüsselt** als `files/xx/yy/<id>`; AES-256-GCM-Stream, Blöcke à 64 KiB + 16 Byte Tag, Kopf ≈ 100 Byte → Aufschlag **≈ 0,03 %** (vernachlässigbar) | `crypto.py:31-32`, `crypto.py:73`, `files.py:1020` |
| Keine Komprimierung, **keine Deduplizierung** (SHA-256 wird gespeichert, aber nur zur Integritätsprüfung; jede Datei hat einen eigenen zufälligen Schlüssel → identischer Inhalt = anderer Chiffretext) | `files.py:1020`, `files.py:1201` |
| Gelöschte Dateien werden nach 30 Tagen endgültig entfernt | `files.py:61`, `files.py:1420` |
| Postfach: Nachricht **einmal** gespeichert (`messages`), je Empfänger nur eine Zeile `conversation_participants` (Lesestand etc.). Rundschreiben/Anhänge werden **nicht** je Empfänger kopiert. Text max. 20.000 Zeichen, max. 10 Anhänge, max. 20.000 Empfänger | `messaging.py:48-54`, `feature_models/messages.py:72-117`, `routes/features_messages.py:672` |
| Postfach-Frist: Standard **365 Tage** (`messaging_retention_days`), danach Löschung inkl. Anhängen | `routes/features_messages.py:273-274`, `:1894-1908` |
| Chat (E2E): Nachricht = 1 Zeile (`nonce`+`ciphertext` Base64) **plus je Empfängergerät eine Schlüsselzeile** (`chat_message_keys`, `wrapped` ≈ 64 Zeichen + `nonce` 32 Zeichen + 3 Indizes); max. 400 Mitglieder, 10 Geräte/Person, Text ≤ 120.000 Base64-Zeichen | `routes/features_chats.py:60-62`, `:631-637`, `feature_models/chats.py:68-93` |
| Chat-Bilder: ≤ 5 MB, max. 4 je Nachricht, **Kontingent je Konto/Chat (Abschnitt 2.6)**, **als BLOB in der DB** (`chat_attachments.data`); Browser verkleinert **nur wenn > 5 MB** (Kante 2048 px, JPEG 0,85); GIFs nie | `routes/features_chats.py:63-66`, `feature_models/chats.py:115-127`, `frontend/src/features/chats/images.tsx:22-52` |
| Chat hat **keine Aufbewahrungsfrist** (nur manuelles Löschen) | `routes/features_chats.py:659-662`, `maintenance.py:21-60` |
| Kursräume: max. 3.000 Einträge/Kanal, Abgaben-Text 50.000 Zeichen, 20 Anhänge | `routes/features_channels.py:94-111` |
| Planungsdokument: bei **jeder** Änderung eine neue Vollversion (zlib-JSON) in `school_versions`; Standard 300 Versionen, danach Löschen der ältesten | `db_models.py:143-150`, `store.py:135-143`, `config.py:101` |
| Audit-Log: unbegrenzt, keine Bereinigung in der Wartung | `db_models.py:129-138`, `maintenance.py:21-60` |
| Sitzungen: 30 Tage, abgelaufene werden bereinigt | `config.py:134`, `maintenance.py:24` |
| Atteste: Frist 400 Tage, danach Löschung samt Datei | `config.py:188`, `maintenance.py:38-44` |

### 2.2 Messung am Testserver (nur lesend, 2026-10-12)

| Messwert | Ergebnis |
|---|---|
| SQLite `schulmanager.db` | **3,3 MB** (5.462 Konten) |
| `users` + 6 Indizes | 1,41 MB → **≈ 260 B/Konto**; `parent_links` ≈ 70 B/Zeile |
| `school_versions` | 15 Versionen, Ø **66 KB** (max. 72 KB) = 1,0 MB → bei 300 Versionen ≈ **20 MB** |
| Audit-Log | 100 Zeilen, Details Ø 38 Zeichen |
| `/app/data/files` | 764 KB, 5 Dateien |
| Frontend `dist` | 1,3 MB, größtes Bundle 364 KB (`index-*.js`, Erstladung gzip ≈ 400 KB gesamt) |
| Platte des Servers | 467 GB, 157 GB belegt |

Das Rechenmodell nutzt 400 B/Konto (Sicherheitsaufschlag) und 35 / 70 / 130 KB je Planversion
(Klein/Mittel/Groß).

### 2.3 Jahr 1 – Rechnung je Bereich (Standardcode, Variante A/B)

Werte in **MB je Jahr** (Wachstum), ohne den 15-%-DB-Aufschlag. „DB“ = Datenbank, „Dat.“ = Dateiablage.

| Bereich | Ort | Formel | Klein | Mittel | Groß |
|---|---|---|---|---|---|
| Abgaben (Dateien) | Dat. | Schüler × 1,5 × 38 × 0,4 × (0,5×2,5 + 0,5×0,8) MB | 37.620 | 94.050 | 188.100 |
| Unterrichtsmaterial | Dat. | Lehrer × 2,5 × 38 × 1,0 MB | 7.600 | 19.000 | 38.000 |
| Atteste/Dokumente | Dat. | Schüler × 4 × 0,25 × Ø 1,4 MB | 1.400 | 3.500 | 7.000 |
| Postfach-Anhänge (Frist 365 T. → Plateau) | Dat. | s. 1.2 | 1.006 | 2.507 | 5.008 |
| **Summe Dateien** | | | **47.626** | **119.057** | **238.108** |
| Chat-Schlüsselzeilen | DB | Nachrichten × 12 Geräte × 190 B | 2.159 | 5.397 | 10.794 |
| Chat-Text | DB | Nachrichten × 290 B (Σ 0,95 / 2,4 / 4,75 Mio.) | 276 | 689 | 1.378 |
| Audit-Log | DB | Zeilen × 220 B (Σ 0,30 / 0,73 / 1,44 Mio.) | 67 | 160 | 316 |
| Postfach-Text + Teilnehmerzeilen | DB | Plateau (Frist 365 T.) | 167 | 431 | 903 |
| Kursräume (Abgaben-Zeilen, Beiträge, Ansichten) | DB | s. Modell | 137 | 342 | 684 |
| Klassenbuch | DB | Klassen × 6 × 190 × 800 B | 37 | 91 | 182 |
| Fehlzeiten + Noten | DB | | 16 | 39 | 79 |
| Sonstiges (Benachrichtigungen, Sitzungen, Konten) | DB | | 20 | 49 | 98 |
| Planversionen (Obergrenze 300, **konstant**) | DB | 300 × 35/70/130 KB | 11 | 21 | 39 |
| **Summe DB ohne Chat-Bilder** | | | **≈ 2.900** | **≈ 7.200** | **≈ 14.400** |
| Chat-Bilder (Variante B) | DB | Schüler × 0,2 × 190 × 1,5 MB | **57.000** | **142.500** | **285.000** |

Kennzahlen je Schüler (Variante A): **≈ 47,6 MB Dateien + ≈ 2,9 MB DB pro Jahr** ≈ 1,33 MB/Woche ≈
**0,27 MB je Schultag**. Chat-Bilder (B) kosten zusätzlich ≈ 57 MB/Schüler/Jahr.

> Empfindlichkeit: Die **Abgaben-Fotos dominieren die Dateiablage (≈ 79 %)**. Je +0,1 Abgabedatei/Schüler/Woche
> kommen ≈ 6,3 MB/Schüler/Jahr hinzu; halbiert sich die Foto-Größe auf 1,25 MB, sinkt der Jahreswert Dateien um
> ≈ 30 %. Beim Chat dominieren die **Schlüsselzeilen (≈ 89 % des Chat-Texts)**, nicht der Text selbst.

### 2.4 Chat-Wachstum mit der Gruppengröße (E2E-Schlüssel)

Je Nachricht wird für **jedes Empfängergerät** (inkl. eigener weiterer Geräte) ein Schlüssel gespeichert:
Ø 190 B/Gerät (Zeilenkopf + `nonce` + `wrapped` als Base64-Text + 2 Indizes + Unique-Index).

| Chat-Größe | Mitglieder | Geräte (×1,3) | Schlüssel-Speicher je Nachricht | Upload je Nachricht (≈ 110 B JSON je Gerät) | Anteil Text am Gesamt |
|---|---|---|---|---|---|
| Zweier-Chat | 2 | 2,6 | 0,5 KB | 0,3 KB | ≈ 37 % |
| Kleingruppe | 8 | 10 | 2,0 KB | 1,1 KB | ≈ 13 % |
| Klassenchat | 30 | 39 | 7,4 KB | 4,3 KB | ≈ 4 % |
| Jahrgangschat (Maximum) | 400 | 520 | **99 KB** | 57 KB | ≈ 0,3 % |

Eine einzige Nachricht in einem 400er-Chat belegt also so viel wie ≈ 340 Nachrichten in Zweier-Chats. Pro Tag
mit 50 solchen Nachrichten: ≈ 5 MB DB. Hinweis: Schreibt jemand in einen Chat und ändern sich Geräte, antwortet
der Server mit 409 `devices_changed` und der Client sendet erneut (`features_chats.py:622`) – doppelter Upload.

### 2.5 Wachstum über 1–5 Jahre (Dateien + DB, in GB, mit 15 % DB-Aufschlag)

Annahmen: Variante A/B – nichts wird gelöscht außer den bestehenden Fristen (Postfach 365 T., Atteste 400 T.,
Sitzungen, Planversionen 300). Variante C – Abgaben/Kursdaten 18 Monate, Chat und Audit 12 Monate, Material zu
50 % wiederverwendet; Chat-Bilder 83 % kleiner.

| | Jahr 1 | Jahr 2 | Jahr 3 | Jahr 4 | Jahr 5 |
|---|---|---|---|---|---|
| **Klein A** (Dat. / DB / Σ) | 48 / 3 / **51** | 93 / 6 / **99** | 138 / 10 / **148** | 183 / 13 / **196** | 229 / 16 / **244** |
| Klein B (mit Chat-Bildern) | 48 / 69 / **117** | 93 / 138 / **231** | 138 / 206 / **344** | 183 / 275 / **458** | 229 / 344 / **572** |
| Klein C (optimiert) | 24 / 13 / **37** | 35 / 13 / **48** | 39 / 13 / **52** | 43 / 13 / **56** | 47 / 13 / **60** |
| **Mittel A** | 119 / 8 / **127** | 233 / 16 / **249** | 346 / 24 / **369** | 459 / 32 / **490** | 572 / 39 / **611** |
| Mittel B | 119 / 172 / **291** | 233 / 344 / **576** | 346 / 516 / **861** | 459 / 687 / **1.146** | 572 / 859 / **1.430** |
| Mittel C | 60 / 32 / **92** | 88 / 33 / **120** | 97 / 33 / **130** | 107 / 33 / **140** | 116 / 33 / **149** |
| **Groß A** | 238 / 17 / **255** | 465 / 32 / **497** | 691 / 48 / **739** | 917 / 63 / **980** | 1.143 / 79 / **1.222** |
| Groß B | 238 / 344 / **583** | 465 / 688 / **1.153** | 691 / 1.031 / **1.722** | 917 / 1.374 / **2.291** | 1.143 / 1.718 / **2.861** |
| Groß C | 119 / 65 / **184** | 175 / 66 / **241** | 194 / 66 / **260** | 213 / 66 / **280** | 232 / 66 / **299** |

(Dateien in A/B wachsen linear, bis das Kontingent greift: 200 MB je Schüler wird bei 47,6 MB/Jahr erst nach
≈ 4–5 Jahren erreicht – das Kontingent ist eine Obergrenze, kein Löschkonzept; Abschlussjahrgänge werden nicht
automatisch entfernt.)

### 2.6 Backups

Ist-Verhalten: `scripts/backup.sh` erzeugt je Lauf (a) einen DB-Dump (`pg_dump` bzw. SQLite-`.backup` + gzip) und
(b) – wenn `BACKUP_DATA_DIR` gesetzt ist (so im `docker-compose.yml:296`) – ein **vollständiges** `tar -czf` der
Dateiablage (`scripts/backup.sh:155-171`), optional GPG-verschlüsselt (kein Platzgewinn). Rotation 14 täglich + 8
wöchentlich + 12 monatlich (`backup.sh:203-228`, `docker-compose.yml:299-302`) + bis 10 manuelle. Da die Blobs
verschlüsselt sind, komprimiert gzip sie nicht (Faktor ≈ 1,0); die DB komprimiert wegen Base64-Chiffretext nur auf
≈ 70–75 %.

Näherung Gesamtbedarf = (14 + 8×0,97 + 12×a) × Größe(Dateien + 0,75 × DB), a = Auslastung der Monatsstände
(0,54 / 0,77 / 0,85 / 0,89 / 0,91 in Jahr 1–5):

| Backup-Bedarf (GB) | Jahr 1 | Jahr 3 | Jahr 5 |
|---|---|---|---|
| Klein A (Standard-Rotation) | 1.415 | 4.646 | 7.859 |
| Klein B (mit Chat-Bildern) | 3.266 | 10.931 | 18.570 |
| Klein C (inkrementell, dedupliziert, 14 Tage Verlauf + zstd) | 36 | 50 | 58 |
| Mittel A | 3.538 | 11.614 | 19.646 |
| Mittel B | 8.166 | 27.327 | 46.423 |
| Mittel C | 90 | 126 | 145 |
| Groß A | 7.077 | 23.229 | 39.293 |
| Groß B | 16.332 | 54.654 | 92.847 |
| Groß C | 179 | 252 | 290 |

Konsequenzen für einen Heimserver:
* **Laufzeit:** `gzip -6` schafft auf nicht komprimierbaren Daten ≈ 40–80 MB/s: 119 GB (Mittel, Jahr 1) ≈ 25–50
  Minuten, 238 GB (Groß) ≈ 1–1,5 h; dazu volle Lese-I/O. Läuft um 02:30, ist aber im Schuljahr 3+ ein Fenster
  bis in die Frühe.
* **Offsite (rclone):** ein neues 119-GB-Archiv pro Nacht über 20 Mbit/s Upload = ≈ 13 h → **schafft die Nacht
  nicht**; mit `BACKUP_RCLONE_MODE=sync` wird zusätzlich die komplette Rotation gespiegelt. Inkrementell
  (restic/borg/rsync `--link-dest`) werden nur die Tagesänderungen übertragen: Jahr 1 ≈ Jahreswachstum / 190 =
  **0,2 / 0,5 / 1,0 GB je Schultag** (Klein/Mittel/Groß, optimiert) bzw. 0,3 / 0,7 / 1,3 GB (Standard).
* **Variante B:** Jedes DB-Backup enthält die Chat-Bilder (SQLite-`.backup` einer 70–290 GB-Datei, jede Nacht,
  34 Generationen) – praktisch nicht betreibbar.
* Der Verschlüsselungsschlüssel (`SM_ENCRYPTION_KEYS`) muss **getrennt** vom Backup liegen (`docs/BETRIEB.md:579`);
  ohne ihn sind alle Backups wertlos – Schlüssel gehört zusätzlich ausgedruckt/offline gesichert.

### 2.7 Logs, Audit, Sonstiges

| Posten | Wert | Beleg/Annahme |
|---|---|---|
| Audit-Log | 67 / 160 / 316 MB je Jahr (0,3 / 0,7 / 1,4 Mio. Zeilen) – **unbegrenzt**, 3 Indizes (`created_at`, `user_id`, `action`) | `db_models.py:129-138` |
| Docker-Logs (JSON-File) | hart gedeckelt: 10 MB × 5 Dateien je Container (komprimiert), 8 Container ≤ ≈ 400 MB | `docker-compose.yml:19-23` |
| Caddy-Zugriffslog | JSON mit allen Headern ≈ 0,8–1,2 KB/Request → Mittel: 115 k Req/Tag ≈ 100–140 MB/Tag; bei 50-MB-Deckel reicht die Historie nur **≈ 8–10 Stunden** (Fehlersuche!) – IP wird gekürzt (DSGVO) | `deploy/Caddyfile:56-76` |
| nginx-Variante | Zeile ≈ 200 B → Mittel ≈ 23 MB/Tag, 14 Tage ≈ 320 MB (komprimiert ≈ 40 MB) | `deploy/nginx/schulmanager.conf:31-33` |
| App-Log | gering; Fehler/Wartung, im Deckel oben enthalten | |
| Prometheus/Grafana (optional) | 15 Tage TSDB ≈ 0,3–1 GB | Profil `monitoring` |
| PostgreSQL | WAL ≤ `max_wal_size` (Standard 1 GB), Log nur Langsam-Abfragen > 2 s | `docker-compose.yml:207` |
| Docker-Images | ≈ 2 GB (`docs/BETRIEB.md:66`) | |
| Planversionen | 300 Vollversionen = 10 / 21 / 39 MB; aber **Verlauf nur wenige Tage**: bei 100 Planänderungen/Tag deckt der Deckel nur ≈ 3 Tage ab (`store.py:135`); jede Änderung schreibt 35–130 KB (≈ 3,5–13 MB/Tag Schreiblast + WAL) | gemessen: 66 KB/Version |

### 2.6 Obergrenze für Chat-Bilder durch Kontingent (seit Sicherheitsprüfung S-13)

Chat-Bilder zählen nicht mehr „unbegrenzt“ in die Datenbank: Jedes Konto hat ein eigenes Kontingent
(`SM_CHAT_QUOTA_MB_STUDENT` = 100 MB, `SM_CHAT_QUOTA_MB_STAFF` = 500 MB), jeder Chat insgesamt `SM_CHAT_QUOTA_MB_CHAT` = 1000 MB,
und höchstens `SM_CHAT_UPLOADS_PER_10MIN` = 30 Uploads je 10 Minuten. Gezählt wird die Summe der Blob-Größen
(`chat_attachments.size`, gesendete und noch nicht gesendete); Löschen einer Nachricht gibt den Platz frei. Die Werte sind
**Obergrenzen gegen Missbrauch**, nicht die Erwartung – der Erwartungswert der Variante B (Abschnitt 2.3) bleibt maßgeblich.

| | Klein (1.000 Schüler, 80 Lehrkräfte) | Mittel (2.500 / 200) | Groß (5.000 / 400) |
|---|---|---|---|
| Erwartung Chat-Bilder Jahr 1 (Variante B, GB) | 57 | 142 | 285 |
| **Harte Obergrenze** aus Konto-Kontingenten (GB) | 140 | 350 | 700 |
| davon ohne Eltern-Konten (Eltern zählen wie Schüler: +1,5 Konten/Kind) | + bis 150 | + bis 375 | + bis 750 |

Die Obergrenze gilt, solange nichts gelöscht wird; Kontingente lassen sich in `.env` anpassen (0 = unbegrenzt). Wer die DB klein
halten will, senkt `SM_CHAT_QUOTA_MB_STUDENT` (z. B. 50) – bei der Annahme „≈ 57 MB je Schüler und Jahr“ wäre das Limit nach etwa
einem Schuljahr erreicht, danach hilft Löschen älterer Bildnachrichten (Abschnitt 4, Löschkonzept).

---

## 3. Datenverkehr und Serverlast

### 3.1 Architektur-Fakten

* **Ein** uvicorn-Prozess/Worker, Planungsdokument im Speicher, Live-Updates per SSE – keine horizontale
  Skalierung, nur vertikal (`docs/BETRIEB.md:474-500`). Ein Python-Prozess nutzt effektiv **einen** Kern für
  Request-Verarbeitung (GIL); Threadpool für synchrone Endpunkte.
* SQLite nutzt `NullPool` (jede Anfrage öffnet eine Verbindung, `db.py:94`); PostgreSQL Pool 20 (`config.py:84`).
* SSE-Ping alle 20 s (`config.py:147`, `routes/events.py:19`) → pro Verbindung ≈ 25 B/20 s ≈ 4,5 KB/Stunde;
  Zahl gleichzeitiger Verbindungen = Zahl offener Tabs (Annahme ≈ 60 % der Aktiven zu Spitzenzeiten).
  Speicher je SSE-Verbindung (Python asyncio + Queue + Caddy) Schätzung ≈ 40–80 KB.
* Caddy: `encode zstd gzip` (`deploy/Caddyfile:127`); nginx-Variante: `gzip on`, Stufe 5, > 1 KB
  (`deploy/nginx/schulmanager.conf:77-82`); App: `SelectiveGZipMiddleware` für alles außer Datei-Downloads
  (`app.py:190-219`) – **richtig**, da Downloads (PDF/JPEG/verschlüsselte Chat-Blobs) nicht weiter komprimierbar sind.
* Statische Assets `/assets/*` unveränderlich 1 Jahr gecacht (`app.py:170`, nginx `:133-137`); alle API-Antworten
  mit `Cache-Control: no-store` (`middleware.py:109`), **keine ETags** → jede Wiederholung lädt voll.
* Monitore (Vertretungsplan) laden alle **120 s** komplett nach (`frontend/src/pages/MonitorPage.tsx:186`),
  Klassenbuch-Register alle 5 min (`features/classes/RegisterPage.tsx:321`).

### 3.2 Anfragen und Volumen je Schultag (Standardcode)

| | Klein | Mittel | Groß |
|---|---|---|---|
| Aktive Nutzer/Tag (80 % / 95 % / 25 %) | 1.251 | 3.138 | 6.275 |
| Requests/Schultag (API + Seiten) | **46 k** | **115 k** | **231 k** |
| API-JSON (gzip) ausgehend | 0,18 GB | 0,44 GB | 0,87 GB |
| Material-Downloads Schüler (≈ 2 MB/Schüler/Woche) | 0,40 GB | 1,0 GB | 2,0 GB |
| Abgaben-Ansicht durch Lehrkräfte | 0,20 GB | 0,50 GB | 0,99 GB |
| **Summe ohne Chat-Bilder** | **0,8 GB** | **1,9 GB** | **3,9 GB** |
| Chat-Bilder (Variante B): 0,2 Bild/Schüler × Ø 5,7 Betrachter × 1,5 MB | +1,7 GB | +4,3 GB | +8,6 GB |
| **Summe mit Chat-Bildern** | **2,5 GB** | **6,2 GB** | **12,5 GB** |
| Eingehend (Uploads Abgaben, Material, Chat-Bilder) | 0,5 GB | 1,3 GB | 2,7 GB |
| Jahresverkehr ausgehend (190 Tage + Ferien/Wochenende ≈ 20 %) ohne / mit Bilder | ≈ 0,2 / 0,6 TB | ≈ 0,4 / 1,4 TB | ≈ 0,9 / 2,9 TB |
| Einmalig je Release/Deploy (Kaltstart-Cache, ≈ 0,4 MB/Gerät) | 0,26 GB | 0,64 GB | 1,3 GB |

Chat-Bilder sind der größte Verkehrstreiber: Jedes Bild wird von **jedem Gruppenmitglied einzeln** geladen (nicht
komprimierbar, Chiffretext).

### 3.3 Spitzen

| Spitze | Klein | Mittel | Groß | Bemerkung |
|---|---|---|---|---|
| **Unterrichtsbeginn** (07:30–07:40: 60 % der Aktiven öffnen die App, ≈ 12 Req je Sitzung) | 638 Sitzungen → Ø 13, **Spitze ≈ 40 req/s** | 1.595 → Ø 32, **≈ 100 req/s** | 3.190 → Ø 64, **≈ 190 req/s** | Faktor 3 auf den 10-Min-Schnitt |
| Pausen (5 pro Tag, 20 % der Schüler fragen Plan/Chat ab) | ≈ 5 req/s | ≈ 12 req/s | ≈ 25 req/s | |
| Tagesprofil (18 % der Tageslast in der Spitzenstunde, ×2,5 Burst) | 6 req/s | 14 req/s | 29 req/s | |
| Gleichzeitige SSE-Verbindungen | ≈ 600 | ≈ 1.500 | ≈ 3.000 | → ≈ 25–240 MB RAM |
| **Abgabe-Abend** (Frist 19–22 Uhr, Upload Fotos) | 0,5 Mbit/s | 1,2 | 2,5 | auf Schülerseite Heim-Upload, bei uns Download |
| Bandbreite ausgehend, Spitze, ohne / mit Chat-Bildern | 1,0 / 2,9 Mbit/s | 2,5 / 7,3 | 5,0 / 14,6 | Mittel über 5 min |
| Zusätzlich nach einem Deploy (Kaltstart) | + 3,4 Mbit/s | + 8,5 | + 17 | 0,4 MB × Sitzungen in 10 min |
| Plan-Änderung → SSE `change` an **alle** Clients → Voll-Reload (Thundering Herd) | 600 Req in Sekunden | 1.500 | 3.000 | jede Änderung der Vertretungsplanung zwischen 07:00–08:00 |

**Planungswert Upload (mit 3× Reserve für Fotos/Fristen):** Klein ≥ 10 Mbit/s, Mittel ≥ 25 Mbit/s, Groß ≥ 50
Mbit/s – und das **dauerhaft**, nicht „bis zu“. Ein klassischer DSL-/Kabelanschluss mit 10–40 Mbit/s Upload reicht
also für Klein sicher, für Mittel knapp (ohne Chat-Bilder gut), für Groß nicht.

### 3.4 CPU-/Request-Last (Schätzung)

* Ein Python/FastAPI-Prozess schafft bei einfachen, authentifizierten JSON-Abfragen (Session-Lookup in DB,
  Entschlüsselung einzelner Felder mit AES-GCM in C) größenordnungsmäßig **150–300 req/s auf einem schnellen Kern**;
  schwere Endpunkte (Klassenbuch, Planansichten, Listen mit Entschlüsselung) deutlich weniger.
* Ergebnis: Klein (≈ 40 req/s Spitze) und Mittel (≈ 100 req/s) liegen im Rahmen (der frühere Lasttest mit 150
  gleichzeitigen Nutzern ohne Fehler passt dazu); **Groß (≈ 190 req/s) kratzt an der Grenze eines einzelnen
  Prozesses** – Maßnahmen: Kaltstart-Spitze entzerren (Staffelung, Jitter), `/me/today` & Co. cachen, schnelle
  Einzelkern-CPU, PostgreSQL.
* Dateien: AES-GCM-Streaming ≈ 1+ GB/s mit AES-NI → vernachlässigbar; ClamAV-Scan (optional, Profil `antivirus`)
  ≈ 20–60 MB/s und **1,5–2 GB RAM** zusätzlich.
* Schreiblast: Chat 4,75 Mio. Nachrichten/Jahr (Groß) × 13 Zeilen ≈ 62 Mio. Inserts/Jahr ≈ 0,3 Mio./Tag –
  trivial im Mittel; die Spitze (≈ 20 Nachrichten/s × 13 Zeilen) ist für SQLite mit Einzel-Schreiber noch machbar,
  für BLOB-Uploads (5 MB) im selben File aber ungünstig.
* **SQLite → PostgreSQL:** Klein ist mit SQLite okay (DB ohne Bilder < 5 GB). Ab **Mittel**, sobald die DB > ≈ 5 GB
  wird, Chat-Bilder in der DB liegen oder parallel viel geschrieben wird, auf PostgreSQL wechseln (konsistente
  `pg_dump`-Sicherung ohne Sperren, Pool statt `NullPool`, `docs/BETRIEB.md` empfiehlt es ohnehin).

---

## 4. Optimierungen (Ersparnis / Aufwand)

Ersparnis bezieht sich auf die Rechnung oben (Jahr 1; „Mittel“ als Beispiel, Rest proportional).
Aufwand: **N**iedrig (Konfiguration/≤ 1 Tag), **M**ittel (Code-Änderung, ≈ 2–5 Tage), **H**och (Protokoll-/Architekturänderung).

| # | Maßnahme | Geschätzte Ersparnis | Aufwand |
|---|---|---|---|
| 1 | **Inkrementelles, dedupliziertes Backup** statt 34 Voll-Archive: Dateien per restic/borg/rsync-`--link-dest`, DB als `pg_dump` + zstd. Offsite überträgt nur Änderungen | Backup-Platte: **−97 %** (Mittel Jahr 1: 3.538 → ≈ 90 GB); Offsite: statt 119 GB/Nacht nur ≈ 0,5 GB/Tag | N–M (Skript/Container; Wiederherstellungstest!) |
| 2 | **Bilder clientseitig verkleinern** vor Upload/Verschlüsselung – nicht nur bei > 5 MB: max. Kante 1280–2048 px, WebP/AVIF q≈0,7 (≈ 0,3–0,6 MB statt 2,5 MB); gilt für Chat (Code existiert: `images.tsx:22-40`, auf immer anwenden, GIF → Größenlimit/Hinweis), **Abgaben-Fotos** und **Atteste** (aktuell kein Resize im Frontend) | Abgaben −60 % (Mittel: −57 GB/Jahr), Atteste −70 %, Chat-Bilder −83 % (−119 GB), Download-Verkehr −80 % | M |
| 3 | **Chat-Bilder aus der DB in die Dateiablage** (Blob-Dateien wie `files.py`, ggf. mit Frist) | Größe gleich, aber DB bleibt klein (−95 % DB-Größe in B), DB-Backup/Restore, Schreib-Locks und Speicherdruck weg | M |
| 4 | **Chat-Schlüsselzeilen verschlankern**: `wrapped`/`nonce` als Binär statt Base64 (−25 %), Nonce ableiten statt speichern, Tabelle mit zusammengesetztem Primärschlüssel `(message_id, device_id)` ohne Zeilen-ID/Zusatzindizes (`WITHOUT ROWID`) → 190 → ≈ 90 B | Chat-DB −53 % (Mittel: −2,8 GB/Jahr), schnellere Gruppennachrichten | M |
| 5 | **Gruppenschlüssel statt Schlüssel je Nachricht** (Sender-Keys/Chat-Schlüssel, nur bei Mitglieder-/Gerätewechsel neu verteilt) | Chat-Schlüssel −90…95 %, Upload je Nachricht im 30er-Chat 4,3 KB → < 0,2 KB; Nachteil: schwächere Forward Secrecy, größere Änderung | H |
| 6 | **Aufbewahrungsfristen/Löschkonzept** (DSGVO): Audit-Log 12–24 Monate (Maintenance-Job), Chat-Nachrichten + Bilder 6–12 Monate, Abgaben/Hausaufgaben-Dateien 1 Schuljahr + 6 Monate, Abschlussjahrgang automatisch archivieren/löschen; Postfach (365 T.) und Atteste (400 T.) bestehen schon | verhindert das lineare Wachstum: Jahr 5 Mittel **611 → 149 GB** (A→C); Audit −100 % ab Jahr 2 | N–M |
| 7 | **Archivierung alter Schuljahre**: kalte Abgaben/Materialien auf externe Platte/NAS (tar + zstd, gleiche Verschlüsselung, Schlüssel sichern) | aktive Platte −50…70 % ab Jahr 3 | M |
| 8 | **HTTP-Optimierung:** ETag/`If-None-Match` + `Cache-Control: private, max-age=…` für wiederholte Abfragen (`/me/today`, Listen, Monitor), Monitor-Reload 120 s → ETag (304, nur Header); Caddy `encode zstd gzip` und statische Assets (immutable) sind bereits vorhanden | API-Verkehr −30…50 %, Monitore ≈ −95 % | N–M |
| 9 | **Thundering Herd entschärfen:** SSE-`change` nur an betroffene Scopes/Klassen, Clients mit zufälligem Jitter 0–3 s neu laden, mehrere Events zusammenfassen | Spitze nach Planänderung −70…90 % | N |
| 10 | **Logs:** Caddy-JSON-Log auf wenige Felder (Header löschen: `request>headers`), Ausgabe in Datei mit `roll_size`/`roll_keep` (14 Tage) statt nur Docker-Deckel; Logrotation mit komprimierter Archivierung | Log-Menge −70 %, Historie von 8 h auf Tage; DSGVO-Frist definierbar | N |
| 11 | **Rundschreiben**: bereits einmal gespeichert (nur Teilnehmerzeilen ≈ 110 B/Empfänger) – nichts zu tun. Optional Teilnehmerzeilen bei Lesen lazy anlegen (Gruppenreferenz statt 1.500 Zeilen) | Mittel: −20 MB je 1.000 Rundschreiben | H (nicht lohnend) |
| 12 | **Deduplizierung gleicher Dateien:** auf Plattenebene wegen zufälliger Schlüssel je Datei **nicht möglich**; sinnvoll nur logisch (beim Kopieren von Material im Kursraum, `MAX_COPY`, denselben Blob referenzieren statt neu verschlüsseln – Stelle vor Umsetzung prüfen) bzw. konvergente Verschlüsselung (Sicherheitsabwägung!) | Material ≈ −5…15 % | M–H |
| 13 | **Chat-Text komprimieren** (deflate/brotli im Browser vor Verschlüsselung) | **nicht lohnend**: Payload ≈ 110 B, Komprimierung erst ab ~ 300 B wirksam; Text macht nur ≈ 11 % des Chat-Speichers aus, Schlüssel 89 % → < 1–2 % Gesamtersparnis | – (Aufwand M, Nutzen gering) |
| 14 | **Thumbnails** für Abgaben-/Material-Listen (clientseitig beim Upload erzeugt und separat gespeichert, ≈ 30–60 KB) | Lehrer-Review-Verkehr −80…90 % (Mittel ≈ −0,4 GB/Tag) – entfällt weitgehend, wenn #2 umgesetzt ist | M |
| 15 | **Planversionen**: Verlauf nach Tagen statt nach Anzahl bemessen (z. B. 90 Tage, Delta-Speicherung oder tägliche Stände + letzte 50 Versionen) | gleicher Speicher (≈ 20 MB), aber Verlauf 3 Tage → Monate | M |
| 16 | **SQLite → PostgreSQL** ab Mittel bzw. ab DB > 5 GB, Chat-Bilder > 0 oder > 20 Schreibvorgängen/s | Stabilität/Backup, kein Platzgewinn | N–M (Compose-Standard) |
| 17 | **ClamAV** nur bei Bedarf (RAM), `SM_UPLOAD_MAX_MB` auf 10–15 MB senken (Zweck-Regeln bestehen) | −1,5…2 GB RAM / Platzspitzen | N |

### Top 5 (Nutzen/Aufwand)
1. **Inkrementelles Backup (#1)** – größter Einzelposten (−97 %), macht Offsite überhaupt erst möglich.
2. **Bild-Verkleinerung im Browser für Abgaben, Atteste und Chat (#2)** – halbiert Dateiablage und Verkehr.
3. **Löschkonzept/Fristen (#6)** – kappt das lineare Wachstum (Jahr 5: −75 %) und ist DSGVO-Pflicht.
4. **Chat-Bilder aus der DB (#3) + schlankere Schlüsseltabelle (#4)** – DB bleibt klein und sicherbar.
5. **ETag/Caching + Herde entschärfen (#8, #9)** – senkt Spitzen-Requests und Rechenzeit am Schulbeginn.

---

## 5. Empfohlene Mindestausstattung Heimserver

Annahme: Linux, Docker-Compose-Stack aus dem Repo (App + PostgreSQL ab Mittel + Caddy + Backup), Daten auf SSD,
Backups auf **zweitem Datenträger** und zusätzlich offsite/offline. Platzwerte für **5 Jahre mit Variante C**
(optimiert) – ohne Optimierung die Zahlen der Tabelle 2.5 einsetzen.

| | Klein (≤ 1.000 Schüler) | Mittel (≤ 2.500) | Groß (≤ 5.000) |
|---|---|---|---|
| CPU | 2 Kerne (4 Threads) | 4 Kerne, gute Einzelkernleistung | 6–8 Kerne mit **starker Einzelkernleistung** (ein Prozess!) |
| RAM | 4 GB | 8 GB (App 1 GB + PG 2 GB + Cache + SSE) | 16 GB (+ 2 GB bei ClamAV) |
| System/Daten-SSD | 256 GB (Daten 5 J. ≈ 60 GB) | 500 GB–1 TB (≈ 150 GB) | 1–2 TB NVMe (≈ 300 GB) |
| Ohne Optimierung (A, 5 J.) | 0,5 TB | 1 TB | 2 TB |
| Mit Chat-Bildern ohne Optimierung (B, 5 J.) | 1 TB | 2 TB | 4 TB (nicht empfohlen) |
| Backup-Medium | 500 GB HDD/NAS + Offsite | 1 TB HDD/NAS (inkrementell) | 2–4 TB NAS + Offsite |
| Datenbank | SQLite möglich, PostgreSQL empfohlen | PostgreSQL | PostgreSQL (zwingend) |
| **Upload** (dauerhaft) | ≥ 10 Mbit/s | ≥ 25 Mbit/s (Glasfaser/Kabel ≥ 50) | ≥ 50, besser 100+ Mbit/s **symmetrisch** |
| Spitzenlast Wert | ≈ 40 req/s, 600 SSE | ≈ 100 req/s, 1.500 SSE | ≈ 190 req/s, 3.000 SSE (Grenzbereich) |
| Betrieb | Mini-PC genügt | Mini-/Tower-Server | besser Rechenzentrum/Hoster statt Heimanschluss |

Weitere Punkte für den Heimbetrieb:
* **USV** und Dateisystem-Prüfung (SQLite/PG nach Stromausfall), SMART-Überwachung; Stromverbrauch ≈ 15–40 W
  rund um die Uhr ≈ 130–350 kWh/Jahr.
* **Erreichbarkeit:** feste IP oder DynDNS; bei Carrier-Grade-NAT/DS-Lite funktioniert Port-Freigabe nicht
  (Tunnel/Hoster-Proxy → Datenschutz/AVV prüfen, Verkehr läuft dann dauerhaft durch den Tunnel).
* **Ausfallsicherheit:** kein Active/Active (In-Memory-Design); Cold-Standby = Offsite-Backup + zweite Maschine
  (`docs/BETRIEB.md:504-514`). Für Mittel/Groß ist ein Heimanschluss ohne SLA ein Betriebsrisiko in der
  Unterrichtszeit.
* **Datenschutz:** Heimserver einer Schule = Verarbeitung durch den Schulträger – Räumlichkeit, Zugriff,
  Auftragsverarbeitung und Löschkonzept (#6) vorher klären.

---

## 6. Offene Punkte / Grenzen der Rechnung

* Alle Nutzungsraten (Abschnitt 1.2) sind **Annahmen**; am stärksten schwanken Chat-Bilder, Abgabe-Fotos und
  Chat-Nachrichtenzahl. Nach 4–6 Wochen Echtbetrieb sollten die Werte aus der DB nachgemessen werden:
  `SELECT name, SUM(pgsize) FROM dbstat GROUP BY name`, Dateigröße je `purpose` aus `stored_files`
  (`GROUP BY purpose`), Zeilen in `chat_message_keys`/`audit_log`.
* Nicht gemessen: Antwortzeiten unter Last, tatsächlicher RAM der App bei Mittel/Groß, Verhalten von 3.000 SSE-
  Verbindungen. Empfehlung: Lasttest mit dem gewählten Profil (Schulbeginn-Burst 100 / 190 req/s) vor dem
  Echtbetrieb.
* Klassenbuch und Noten wurden nur grob nach Tabellenstruktur geschätzt (`feature_models/grades.py`,
  `routes/features_classes.py`); Anteil an der Gesamtsumme < 3 %.
* Mailbridge/Test-Postausgang, Zugangsbriefe-PDFs und Excel-/Untis-Importe (bis 50 MB, `nginx client_max_body_size`)
  sind einmalig und nicht eingerechnet.
* Video-/Audiodateien im Unterrichtsmaterial (bis 25 MB je Datei, Typen u. a. `mp4`, `mp3`, vgl. `routes/features_channels.py:117`) können die
  Dateiablage stark erhöhen; pro 10 Videos à 25 MB/Lehrkraft/Jahr + 250 MB (Mittel: +50 GB).

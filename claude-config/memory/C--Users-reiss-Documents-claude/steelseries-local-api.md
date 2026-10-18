---
name: steelseries-local-api
description: "SteelSeries GG lokal steuern (Sonar-Audio, Maus-DPI, Akku per HID) - Endpunkte, Schreibformat und die Falle mit leeren PUTs"
metadata:
  node_type: memory
  type: reference
  originSessionId: 8b1f5fa3-0154-4d43-a98b-177017acb7f4
  modified: 2026-09-23T18:06:31.645Z
---

SteelSeries GG bietet lokale APIs ohne Cloud (2026-09-23 auf diesem PC verifiziert), genutzt von `voice-browser/gear.py` + `hidbattery.py` ([[voice-browser]]).

**Einstieg:** `C:\ProgramData\SteelSeries\SteelSeries Engine 3\coreProps.json` → `ggEncryptedAddress` (6327) → `GET https://<gg>/subApps` nennt die Adressen der Unter-Apps. Engine ist **https mit selbst ausgestelltem Zertifikat** (ssl-Prüfung abschalten), Sonar ist **http**. Ports wechseln bei jedem GG-Start → nie hart verdrahten.

- **Sonar:** `GET /volumeSettings/classic` (Kanäle: masters, game, chatRender, chatCapture=Mikrofon, media, aux), Schreiben `PUT /volumeSettings/classic/<kanal>/Volume/<0..1>` und `/Mute/<true|false>`; master liegt unter `masters/classic`.
- **Engine:** `GET /devices`, `GET /device/<id>`, `GET /configuration/<uuid>` (Feld `settings` ist ein JSON-**String**). Schreiben: `PUT /configuration/<uuid>` mit **`{"name": ..., "settings": "<json-string>"}`** (flach, nicht in `configuration` gewickelt), danach `POST /configuration/<uuid>/deploy`.
- **DPI** steckt in `settings.batch_resolution.resolution_N` als Sensor-Byte, **nicht** als DPI-Zahl. TrueMove Air: Tabelle mit Lücken (0x01 und 0x08 fehlen), 0x09 = 800 DPI → `voice-browser/dpi_truemove_air.json` (aus rivalcfg).
- **Akkustand gibt die API NICHT her.** Nur per HID: Output-Report `0x92` (Kabel) bzw. `0xD2` (Funk, = 0x92|0x40) an die Schnittstelle mit `usage_page 0xFFC0`, Antwort z.B. `00 d2 06 …` → Byte nach dem Echo, `((b & 0x7F) - 1) * 5` Prozent, Bit 7 = lädt. Aerox 5 Wireless: PID 0x1854 Kabel, 0x1852 Funk.

**Gefahr, teuer gelernt:** Ein **leeres `PUT /configuration/<uuid>`** (Methoden-Abtasten!) löscht Name und Einstellungen des Profils. Nie mit leeren Bodys an Konfigurations-APIs tasten. Rettung damals: die Engine schreibt in `C:\ProgramData\SteelSeries\GG\apps\engine\db\database.db` per WAL, die Hauptdatei war noch alt → Kopie mit `sqlite3 mode=ro&immutable=1` öffnen, `select settings from configurations where id=<uuid>` und per PUT zurückspielen. `gear.py` sichert deshalb vor jedem Schreiben nach `voice-browser/backups/`.

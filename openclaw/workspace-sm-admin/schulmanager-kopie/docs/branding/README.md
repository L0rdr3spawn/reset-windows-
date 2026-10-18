# Marke: Schulpuls

Produktname der Anwendung, die intern weiter `schulmanager` heißt (Python-Paket, `SM_*`-Variablen, Cookies `sm_*`,
Docker-Namen, Routen, Header `X-Schulmanager-*`, Lizenzserver, Testnamen). Nur die sichtbare Marke ist neu.

## Name: Schulpuls

- **Warum:** kurz (zwei Silben), eindeutig deutsch, sofort aussprechbar. „Puls“ steht für das, was die App ist: der
  Takt der Schule – Stundenplan und Live-Vertretungsplan, Klassenbuch, Nachrichten, Kursräume in einem. Freundlich
  genug für Kinder und Eltern („am Puls der Schule“), seriös genug für Schulleitungen (Puls fühlen = Überblick haben).
- **Grammatik:** *der* Schulpuls – „im Schulpuls“, „den Schulpuls nutzen“ – passt ohne Satzumbau an alle Stellen, an
  denen bisher „der Schulmanager“ stand.
- **Geprüft (Websuche, Oktober 2026):** kein Treffer für eine Schulsoftware, Bildungs-App oder Domain „Schulpuls“.
  Nächste Namensnachbarn ohne Konflikt: „klasse.im.puls“ (bayerisches Musikprogramm), „School Pulse“ (US-Familienkalender),
  „PULS+“ (Forschungsprojekt Schulbau). Keine Überschneidung mit Schulmanager Online, schul.cloud, SchulCloud,
  Schulportal, schulNetz, Orff-Schulwerk.
- **Verworfen:** Schulkompass (Plattform des österreichischen Bildungsministeriums geplant), Schulwerk (Orff-Schulwerk),
  Schulportal (belegt), Schulnest (zu nah an „schulNetz“, Schweizer Schulverwaltung). Frei, aber schwächer:
  Schultor (das Tor – Satzumbau nötig, Doppelsinn), Schulkern, Schulkreis, Schulfeld, Schulfluss.
- **Kein Markenrechts-Gutachten.** Vor Veröffentlichung bitte selbst im DPMA-Register (register.dpma.de) und bei der
  EUIPO (euipo.europa.eu, eSearch plus) nach „Schulpuls“ in den Klassen 9, 41 und 42 suchen sowie die Domain prüfen.

Kurzname: **Puls**. Slogan: *Stundenplan, Klassenbuch und Nachrichten – im Takt der Schule.*

## Logo

Hand-gebautes SVG ohne fremde Grafiken: abgerundete Kachel, eine Pulslinie mit einem Schlag, rechts ein Punkt
(„live“ – wie der Live-Punkt in der Kopfleiste). Die Linie liest sich auch als liegendes „S“ aus Schule/Schulpuls.
Geometrie (ViewBox 0 0 64 64): Kachel `rx 14`, Pfad `M11 37 h10 l6-18 l8 28 l6-10 h12`, Strich 6, runde Enden, Punkt
`(53,37) r 5`. Funktioniert bei 16 px (Favicon) bis App-Icon-Größe.

| Datei | Verwendung |
| --- | --- |
| `frontend/src/assets/logo.svg` | Bildmarke farbig (Kachel + weiße Linie + Bernstein-Punkt) |
| `frontend/src/assets/logo-mono.svg` | Bildmarke einfarbig in `currentColor`, ohne Kachel (helle und dunkle Flächen, Druck) |
| `frontend/src/assets/logo-wordmark.svg` | Wortmarke hell (dunkle Schrift, „puls“ in Primärblau) |
| `frontend/src/assets/logo-wordmark-dark.svg` | Wortmarke dunkel (helle Schrift, „puls“ in hellem Blau) |
| `frontend/public/favicon.svg` | Favicon (Kopie der Bildmarke) |
| `frontend/public/favicon-32.png`, `frontend/public/apple-touch-icon.png` (180 px) | PNG-Fallbacks, per Python-Bordmitteln gerastert |
| `docs/branding/schulpuls-logo-512.png` | Bildmarke als PNG (transparent) |
| `docs/branding/schulpuls-login.jpg`, `schulpuls-kopfleiste.jpg` | Screenshots Login (dunkel) und Kopfleiste (hell) |

Im Frontend zeichnet `components/BrandLogo.tsx` die Linie inline in `currentColor`; die Kachel liefert die bestehende
Klasse `.brand-logo` (`--primary` / `--on-primary`), damit das Logo den Design-Tokens und dem Farbschema folgt.
In PDFs zeichnet `schulmanager/branding.py` (`draw_logo`, `draw_logo_simple`) dieselbe Geometrie mit den neuen
Grundformen `Page.polyline`/`Page.circle` (`server/pdf.py`) bzw. `Page.polyline`/`Page.disc` (`server/pdf_simple.py`).

## Farben (aus `frontend/src/styles/tokens.css`)

| Rolle | hell | dunkel |
| --- | --- | --- |
| Kachel / Linie farbig | `#1d4ed8` (`--primary`) | Kachel bleibt `#1d4ed8`; in der Oberfläche `--primary` `#60a5fa` |
| Linie auf Kachel | `#ffffff` | `--on-primary` `#0b1220` (Oberfläche) |
| Live-Punkt | `#fbbf24` (`--warning` dunkel) | `#fbbf24` |
| Wortmarke Schrift | `#111827` (`--text`) | `#e6edf3` (`--text`) |

Mindestabstand um die Bildmarke: ein Viertel der Kantenlänge. Nicht verzerren, nicht drehen, keine Schatten.

## Wo der Name zentral steht

- Frontend: `frontend/src/brand.ts` (`APP_NAME`, `APP_SHORT_NAME`, `APP_TAGLINE`, Logo-URLs, `pageTitle()`, `withSchool()`).
- Backend: `schulmanager/branding.py` (`PRODUCT_NAME`, `PRODUCT_SHORT`, `TAGLINE`, `product_with_school()`, Logo-Zeichner).
  `SM_APP_NAME` überschreibt den Namen weiterhin je Instanz (`config.app_name`, Standard = `PRODUCT_NAME`).
- Der Schulname aus den Einstellungen bleibt unberührt und steht zusätzlich (Seitenleiste unten, Briefkopf);
  `withSchool()` / `product_with_school()` liefern „Schulpuls · Schulname“.

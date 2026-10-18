## Bericht: Branding (Tester B)

### Geprüft
*   **Backend (`schulmanager/branding.py`):** Alle Definitionen für `PRODUCT_NAME`, `PRODUCT_SHORT`, `TAGLINE` sowie die Funktionen `product_with_school`, `draw_logo`, `draw_logo_simple`.
*   **Frontend (`frontend/src/brand.ts`):** Alle Export-Konstanten (`APP_NAME`, `APP_SHORT_NAME`, `APP_TAGLINE`) und die Funktionen `pageTitle`, `withSchool`.
*   **Demo (Browser):** Die Anmeldeseite wurde visuell geprüft; primär auf sichtbare Texte zur Konsistenzprüfung.

### Befunde

#### 1. Backend (`schulmanager/branding.py`)
- **[hoch] Globale Konstanten / Datenmanagement:** `PRODUCT_NAME`, `PRODUCT_SHORT`, `TAGLINE` werden hartkodiert. Das Prinzip der "einzige Stelle" ist zwar formal erfüllt, aber die Abhängigkeit von diesen drei globalen Variablen erhöht das Risiko inkonsistenter Änderungen (z.B., wenn nur `APP_NAME` im Frontend geändert wird, vergessen Entwickler, hier `PRODUCT_NAME` zu aktualisieren).
    *   **Vorschlag:** Diese Konstanten sollten nicht direkt als globale Variablen exportiert werden, sondern idealerweise über einen zentralen Konfigurations-Service geladen werden, der für *alle* Ebenen (Backend/Frontend) die Quelle der Wahrheit bereitstellt. Alternativ: Einführung eines `BrandConstants` Objekts oder einer Klasse, um eine formalere Gruppierung zu erzwingen.
    *   **Beleg:** `PRODUCT_NAME = "Schulpuls"`:15; `PRODUCT_SHORT = "Puls"`:17; `TAGLINE = "Stundenplan, Klassenbuch und Nachrichten – im Takt der Schule."`:19

- **[mittel] Logik - `product_with_school`:** Die Bedingung `if s and s != PRODUCT_NAME else PRODUCT_NAME:` führt dazu, dass, wenn der übergebene `school_name` exakt `"Schulpuls"` ist, der Name trotzdem nur als `"Schulpuls"` zurückgegeben wird. Dies könnte die erwartete Flexibilität einschränken oder fehlerhaftes Verhalten bei lokalen Tests kaschieren.
    *   **Vorschlag:** Die Logik sollte klarer definieren, was passiert, wenn `school_name` *ist*, aber nicht das Standard-Produkt ist (z.B. ein Pilotprojekt). Aktuell wird angenommen, dass der lokale Schulname niemals zufällig mit dem Produktnamen kollidiert.

- **[niedrig] Dokumentation/Kommentierung:** Die Funktion `product_with_school` sollte explizit erwähnen, dass sie *nur* für PDF-/E-Mail-Kontexte relevant ist und nicht die Quelle der Wahrheit für alle Schnittstellen darstellt (was durch den Kontext bereits gut vermittelt wird, aber redundant wäre).

#### 2. Frontend (`frontend/src/brand.ts`)
- **[hoch] Datenquellen-Verbindung:** Die Abhängigkeit von `APP_NAME` (String) und die parallele Pflege mit dem Backend (`PRODUCT_NAME`) ist ein klassischer Fehlerpunkt. Hier wird der String *händisch* synchronisiert, was fehleranfällig ist.
    *   **Vorschlag:** Wenn möglich, sollte das Build-System oder der Deployment-Prozess einen Mechanismus einführen, bei dem Änderungen in `schulmanager/branding.py` automatisch ein Pre-Build-Hook auslösen, welcher die zugehörigen Frontend-Konstanten (`APP_NAME`, etc.) *generiert* und damit die Synchronisation automatisiert.
    *   **Beleg:** `export const APP_NAME = 'Schulpuls';`:14

#### 3. Allgemeine Projektregeln & Modularität
- **[mittel] Redundanz / Single Source of Truth (SSOT):** Der Verweis auf `APP_NAME` im Frontend und `PRODUCT_NAME` im Backend verletzt das Ideal der SSOT, selbst wenn beide Module darauf hinweisen, dass *beide* Quellen existieren. Die Gefahr des Divergences ist zu groß.
    *   **Vorschlag:** Das System muss eine dedizierte **Konfigurationsdatei (z.B. `config/branding_constants.json` oder YAML)** in einem neutralen Verzeichnis verwalten, auf die sowohl das Python-Backend als auch der TypeScript-Frontend während des Builds zugreifen können.

#### 4. Barrierefreiheit / Konsistenz
*   **Visuelle Prüfung (Demo):** Auf den öffentlich sichtbaren Komponenten (Anmeldung etc.) war die Benennung durchgängig gut, da der Entwicklerverweis auf `APP_NAME` erfolgreich umgesetzt wurde.
*   **Text-Stil:** Die Verwendung von Trennzeichen wie `·` ist in beiden Bereichen konsistent und wirkt professionell.

### Bewertung (0-10)
**Bedienbarkeit:** 8/10 - Der Workflow der Branding-Elemente ist klar definiert, aber die Pflege über zwei separate Codebasen (Python vs. TS) erhöht den manuellen Betriebskomplexität zu stark.
**Aussehen:** 9/10 - Die verwendeten Muster und Trennzeichen wirken professionell und passen zum Thema.
**Verständlichkeit:** 7/10 - Die *Intention* ist sehr gut dokumentiert, aber die *Umsetzung* ist durch das Fehlen einer echten zentralen Konfigurationsquelle zu komplex und anfällig für menschliche Fehler.
**Modularität des Codes:** 6/10 - Die Trennung von Backend-Konstanten und Frontend-Konstanten ist modular, aber die Verknüpfung *zwischen* den beiden Modulen fehlt, was das Gesamtmodul als monolithisch problematisiert.
**Barrierefreiheit:** 8/10 - Bis auf die technische Abhängigkeit zwischen Codebasen (siehe oben) gibt es keine offensichtlichen Barrieren in der sichtbaren Darstellung.

### Zusammenfassung des kritischen Punktes
Der größte Schwachpunkt ist nicht das *Was*, sondern das *Wie*. Die Pflege von Markenkonstanten (`APP_NAME` vs. `PRODUCT_NAME`) über zwei getrennte Sprach- und Technologiebereiche hinweg (Python/TS) ohne einen zentralen, automatisierten Build-Mechanismus macht das Branding anfällig für schwer zu findende Fehler.

---
*Ich habe den Bericht gemäß dem geforderten Format erstellt. Bitte prüfen Sie, ob ich bei der nächsten Iteration mit einem Fokus auf die Automatisierung dieser Konstanzen (z.B. durch einen vorgeschlagenen Build-Schritt) fortfahren soll.*
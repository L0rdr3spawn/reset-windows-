## Bericht: Branding (Tester A)

### Geprüft
*   **Code-Basis:** Backend (`schulmanager/branding.py`, Konstanten `PRODUCT_NAME`, etc.).
*   **Code-Basis:** Frontend (`frontend/src/brand.ts` und `frontend/src/components/BrandLogo.tsx`).
*   **Projektregeln:** Konsistenzprüfung der Marke "Schulpuls" in allen definierten Stellen (Backend vs. Frontend).

### Befunde
1.  **[hoch] Konstanz-Verletzung im Backend (`schulmanager/branding.py`):** Die Funktion `product_with_school` ist redundant, wenn `s` leer oder gleich dem Produktnamen ist: `return f"{PRODUCT_NAME} · {s}" if s and s != PRODUCT_NAME else PRODUCT_NAME`. Wenn `s == PRODUCT_NAME`, sollte der Ausdruck einfach nur `PRODUCT_NAME` liefern. Die Bedingung `s != PRODUCT_NAME` impliziert, dass bei Gleichheit das Produkt *nicht* angezeigt wird, was konsistent ist, aber die Logik könnte vereinfacht werden, um Missverständnisse zu vermeiden.
    *   **Vorschlag:** Vereinfachung der Bedingungslogik in `product_with_school`: Wenn `s` leer ist, gib `PRODUCT_NAME`. Andernfalls gib `${PRODUCT_NAME} · ${s}`. Die aktuelle Logik funktioniert zwar, aber die Komplexität erhöht das Risiko eines Fehlers bei Wartungen (Beleg: `schulmanager/branding.py`:33).
2.  **[mittel] Inkonsistenz der Nutzung des Produktnamens im Frontend (`frontend/src/brand.ts`):** Es existieren sowohl `APP_NAME`, `APP_SHORT_NAME` als auch die Funktion `withSchool`. Die Verwendung von `APP_TAGLINE` ist für *alle* sichtbaren Orte (Login, Über-Seite, Druck) vorgesehen; dies muss in der Frontend-Komponentenlogik garantiert sein. Die Trennung des Slogans vom Hauptnamen (`APP_NAME`) ist gut, aber es gibt keine zentrale Stelle, die sicherstellt, dass bei neuen UI-Elementen **immer** `APP_TAGLINE` genutzt wird und nicht ein hartkodierter Text (Beleg: *implizite Abhängigkeit*).
3.  **[niedrig] Semantische Überlappung in Komponenten (`frontend/src/components/BrandLogo.tsx`):** Das SVG nutzt `currentColor` für die Füllung des Punktes und der Linie, was perfekt mit dem Design-Token-Prinzip harmoniert (Beleg: `BrandLogo`:10). Jedoch wird das `<title>` Element dynamisch hinzugefügt (`{title ? <title>{title ?? APP_NAME}</title> : null}`). Wenn keine `title` Prop übergeben wird, fällt auf den generischen Platzhalter `APP_NAME` zurück. Dies ist gut für die Barrierefreiheit (ARIA-Kontext), sollte aber bei einem **fehlenden Titel** durch eine spezifischere Meldung ersetzt werden, z.B. "Logo von Schulpuls" (Beleg: `BrandLogo`:13).
4.  **[niedrig] Dokumentation der Nutzung:** Die Projektregeln verlangen, dass Komponenten nur eingebunden werden und keine eigenen Routen haben. Dies wird zwar eingehalten, aber es wäre sinnvoll, eine globale Komponente für das Branding zu schaffen (z.B. `<BrandProvider />`), die `APP_NAME`, `APP_TAGLINE` und die Logo-Komponenten konsolidiert anbietet und so sicherstellt, dass Entwickler nicht auf manuell importierte Konstanten zurückgreifen.

### Bewertung (0-10)
**Bedienbarkeit:** 8/10 (Die Trennung der Komponenten ist gut, aber das Risiko von Inkonsistenzen bleibt hoch).
**Aussehen:** 9/10 (Der Einsatz von Design-Tokens und die SVG-Struktur sind sehr modern und sauber).
**Verständlichkeit:** 8/10 (Sehr klar definiert, welche Konstante wann zu nutzen ist; die Trennung zwischen `APP_NAME` und `withSchool` ist ein Stärke).
**Modularität des Codes:** 9/10 (Die Komponenten sind klein und fokussiert. Die Abhängigkeit von zentralen Konstanten ist gut gelöst).
**Barrierefreiheit:** 7/10 (Das `<title>` Element in der SVG-Komponente ist ein guter Versuch, aber die explizite Überprüfung des Fallbacks bei fehlendem Titel könnte verbessert werden).

***

**Zusammenfassendes Fazit für Luis:** Die Implementierung des Brandings ist auf einem sehr hohen Niveau. Es gibt keine offensichtlichen kritischen Fehler im Code, sondern eher Optimierungspunkte bezüglich der Abstraktion und Redundanzprüfung (z.B. die Vereinfachung von `product_with_school`).
# Feature-Module (Erweiterung 2)

Jedes Feature (Lehrkraft, Kursräume, Postfach, Schüler-Selbstbedienung …) liegt in einem eigenen Ordner und meldet
seine Seiten, Menüeinträge, Startseiten-Kacheln und Badges über **ein** Modul an. Die Kernanwendung muss dafür
nicht geändert werden: `registry.ts` lädt alle `src/features/*/module.tsx` per
`import.meta.glob('./*/module.tsx', { eager: true })`; `App.tsx` (Routen + Guard), `lib/permissions.ts`
(Menü, Zugriff) und `pages/DashboardPage.tsx` (Kacheln) lesen die Registry.
Vertrag: `docs/ARCHITECTURE.md` §9.2.

> **Feature-Agenten ändern keine geteilten Dateien** (`App.tsx`, `lib/permissions.ts`, `api/types.ts`,
> `api/endpoints.ts`, `components/Layout.tsx`, `components/Icon.tsx`, `pages/DashboardPage.tsx`, `styles/*`).
> Bedarf (z. B. neues Icon, neuer Typ in `types.ts`) → `docs/AGENT_NOTES.md`, der Integrations-Agent erledigt das.

## Aufbau

```
src/features/<feature>/
  module.tsx      Pflicht: default export (siehe unten)
  *.tsx, *.ts     Seiten, Komponenten, API-Aufrufe, Typen – frei
  <feature>.css   optional, Klassen mit Feature-Präfix (z. B. .pf-thread), nur CSS-Variablen aus styles/tokens.css
  *.test.ts       vitest (Node-Umgebung, kein DOM) – siehe „Tests“
```

## `module.tsx` – Beispiel

```tsx
import { lazy } from 'react';
import { defineFeature, getBadge } from '../registry';
import { InboxWidget, UnreadBadge } from './widgets';

// Seiten immer per lazy() – sie landen in eigenen Chunks und werden erst bei Bedarf geladen
const InboxPage = lazy(() => import('./InboxPage'));
const ThreadPage = lazy(() => import('./ThreadPage'));

export default defineFeature({
  id: 'postfach',                                        // eindeutig: a–z, 0–9, „-“
  routes: [
    { path: '/postfach', element: <InboxPage />, anyOf: ['messages.use'], title: 'Postfach' },
    { path: '/postfach/:id', element: <ThreadPage /> },   // ohne eigene Regeln → Regeln des Menüeintrags /postfach
  ],
  nav: [
    {
      path: '/postfach', label: 'Postfach', icon: 'megaphone', group: 'kommunikation', anyOf: ['messages.use'],
      badge: () => getBadge('postfach.unread'), badgeLabel: (n) => `${n} ungelesen`,
    },
  ],
  widgets: [{ id: 'ungelesen', element: <InboxWidget />, order: -10, anyOf: ['messages.use'] }],
  background: UnreadBadge,                               // unsichtbar, setzt den Badge (siehe unten)
});
```

### Felder

| Feld | Bedeutung |
|---|---|
| `routes[].path` | absoluter Pfad im Stil von React Router (`/kursraeume/:id`, `:id?`, `*`). Kernpfade (`/`, `/stundenplan`, `/planung`, `/profil` …, siehe `CORE_PATHS` in `registry.ts`) sind gesperrt, **Unterpfade** erlaubt (z. B. `/planung/antraege`). Doppelte Pfade werden mit Warnung übersprungen. |
| `routes[].element` | React-Element (Seite per `lazy()`); läuft in einer Fehlergrenze + `Suspense`. |
| `routes[].anyOf` / `roles` / `notRoles` | Rechte (mindestens eines) / nur diese Rollen / diese Rollen nicht – Regeln siehe unten. |
| `routes[].title` | Text der Kopfzeile (Standard: Beschriftung des passenden Menüeintrags). |
| `routes[].layout` | `false` = ohne App-Rahmen (Vollbild/Druck), Standard: mit Menü. |
| `nav[]` | `NavItem` aus `lib/permissions.ts`: `path`, `label`, `icon` (Name aus `components/Icon`, unbekannt → Info-Symbol), `group` (`alltag`, `kommunikation`, `planung`, `verwaltung`, `konto`), `anyOf`/`roles`/`notRoles`, `order` (Kern-Einträge 0, 10, 20 …; Features Standard 1000 = hinter den Kern-Einträgen der Gruppe), `badge`, `badgeLabel`. |
| `widgets[]` | Startseiten-Kachel: `id`, `element`, `order` (`< 0` = über den Standard-Bereichen der Rolle, sonst darunter; stabil sortiert), `roles`, `notRoles`, `anyOf`, `wide` (volle Breite). Jede Kachel bringt ihre eigene `card` mit und läuft in einer Fehlergrenze. |
| `background` | Komponente ohne Ausgabe, dauerhaft im App-Rahmen gerendert (nur angemeldet), z. B. für Badges per Live-Ereignis. Prüft Rechte selbst (`useUser()` + `can()` aus `lib/permissions`). |

### Rechte

* **Das Frontend blendet nur aus – entscheidend ist das Backend.** Jede Route im Backend prüft Recht **und**
  Datenumfang (Scopes, z. B. Lehrkräfte nur eigene Kurse); das Frontend schützt nichts.
* Route **mit** eigenen Regeln (`anyOf`/`roles`/`notRoles`): es gelten **nur diese** – auch im Guard von `App.tsx`
  (`canAccessPath`). So ist `/planung/antraege` mit `anyOf: ['teacher_requests.review']` für die Schulleitung
  erreichbar, obwohl das Menü „Planung“ andere Rechte verlangt.
* Route **ohne** eigene Regeln: es gelten die des Menüeintrags mit dem längsten passenden Präfix (wie bei den
  Kernseiten). Bei Unterseiten, die mehr verlangen als ihr Menüeintrag, die Regeln also **ausdrücklich** angeben.
* Nicht berechtigt → Seite „Kein Zugriff“ (Monitor-Konten → ihre Vollbildansicht).

### Importzyklus – was beim Laden erlaubt ist

Vite stellt die Glob-Importe an den **Anfang** von `registry.ts`: `module.tsx` (und alles, was es importiert) wird
ausgewertet, **bevor** der Rest der Registry läuft. Deshalb:

* Typen nur mit `import type { FeatureModule, FeatureRoute, FeatureWidget } from '../registry'`.
* Beim Laden (auf Modulebene) nur die Funktionsdeklarationen `defineFeature`, `getBadge`, `setBadge`, `badgeStore`
  benutzen. `badges` (Objekt) und `FEATURES` nur **innerhalb** von Funktionen/Effekten/Komponenten.
* `module.tsx` ohne Seiteneffekte halten (keine Abfragen, keine Timer) – ein Fehler beim Import legt sonst die ganze
  App lahm. Seiten per `lazy()` laden.

### Badges (Zahlen am Menü)

```tsx
// widgets.tsx
import { useEffect } from 'react';
import { setBadge } from '../registry';

export function UnreadBadge() {
  const user = useUser();
  const enabled = can(user, 'messages.use');
  const { data } = useApi((signal) => api.unreadCount(signal), [], { enabled, live: ['messages'] });
  useEffect(() => setBadge('postfach.unread', enabled ? data?.unread ?? 0 : 0), [enabled, data]);
  useEffect(() => () => setBadge('postfach.unread', 0), []);   // beim Abmelden entfernen
  return null;
}
```

* Schlüssel mit Feature-Präfix (`postfach.unread`); `null`/0 entfernt den Badge, Kommazahlen werden abgerundet.
* Menüeintrag: `badge: () => getBadge('postfach.unread')`, optional `badgeLabel: (n) => \`${n} ungelesen\`` (Text für
  Bildschirmleser; angezeigt wird `1 … 99`, darüber `99+`). Das Layout zeichnet bei jeder Änderung neu und markiert den
  Menüknopf auf dem Handy mit einem Punkt.
* In Komponenten lesen: `useBadge('postfach.unread')`. Für Tests: `createBadgeStore()`.
* Bei Abmeldung, Sitzungsablauf (401) und Kontowechsel leert die App alle Badges (`lib/session.ts`).

## Kontobezogene Zwischenspeicher

Was ein Feature modulweit zwischenspeichert (Übersichten, Limits, Zähler), gehört zum angemeldeten Konto und muss bei
Abmeldung **und** 401 weg – sonst sieht das nächste Konto im selben Tab fremde Daten (U-01). Dafür auf oberster Ebene
der Datei anmelden:

```ts
import { onSessionReset } from '../../lib/session';
let overviewCache: Cache | null = null;
onSessionReset(() => { overviewCache = null; });
```

`useCollection`, Datei-Limits (`FileUpload`), die Kursraum-Übersicht und Badges sind schon angemeldet.

## Live-Aktualisierung

`useApi(fn, deps, { live: ['messages'] })` bzw. `useLive('messages')` (Hooks in `src/hooks/`) laden bei passenden
SSE-Ereignissen neu. Backend: `bus.publish("change", {"version": None, "scope": ["messages"], "dates": []},
user_ids=[...])` – zielgerichtet an die betroffenen Konten, **ohne Inhalt** (nur Scope/IDs). Die Dateiablage sendet
`scope: ["files"]` an die eigenen Sitzungen nach Upload/Löschen.

## Dateien hochladen und anzeigen (Basisdienst)

Backend-Ablauf (siehe `schulmanager/server/files.py`): Upload → `id` → das Feature hängt die Datei beim Speichern an
sein Objekt (`files.attach(db, file_id, user, "message", msg.id)` bzw. `files.attach_many`) und registriert eine
Zugriffsprüfung (`files.register_access_check("message", fn)`). Nicht angehängte Uploads verfallen nach 24 h.
Listen liefert das Feature über `files.files_info(db, ids, user)` – genau das Format von `StoredFileInfo`.

### `src/api/files.ts`

| Export | Zweck |
|---|---|
| `uploadFile(file, { purpose, filename?, onProgress?, signal? })` | Upload per XMLHttpRequest mit Fortschritt, CSRF-Header, `?purpose=`; → `StoredFileInfo`; Fehler `ApiError` mit deutscher Meldung, Abbruch `AbortError` |
| `fileUrl(id, { inline? })` | Download-Adresse (`?inline=1`: PDF/Bilder im Browser; SVG/Office immer Download) |
| `filesApi.limits(purpose?)`, `.mine({purpose, unattached})`, `.meta(id)`, `.remove(id)` | Limits/Kontingent, eigene Dateien, Metadaten, eigene lose Datei löschen |
| `precheckFile`, `uploadErrorMessage`, `fileErrorCode`, `formatFileSize`, `isAbortError` | Vorabprüfung, Meldungen (`file_too_large`, `quota_exceeded`, `blocked_type`, `unsupported_type`, `virus_found`, `scan_failed` …), deutsches Format |

### `<FileUpload>` (`src/components/FileUpload.tsx`)

```tsx
// Kursmaterial: große Ablagefläche, mehrere Dateien
<FileUpload purpose="channel_material" label="Material hochladen" onChange={(files) => setIds(files.map((f) => f.id))} />

// Nachrichtenanhänge: kompakter Knopf
<FileUpload purpose="message" compact maxFiles={10} onChange={setAttachments} />

// Attest: genau eine Datei, nur PDF/Bilder
<FileUpload purpose="student_document" multiple={false} accept=".pdf,.jpg,.jpeg,.png,.heic" onChange={([f]) => setFile(f ?? null)} />
```

Drag & Drop + Auswahlknopf (tastaturbedienbar), Uploads nacheinander mit Fortschrittsbalken, Abbrechen, „Erneut
versuchen“ (Netz/Server), Entfernen (löscht den losen Upload auch auf dem Server; `deleteOnRemove={false}` schaltet
das ab), Meldungen für 413/415/Kontingent/Virus, Ansagen für Bildschirmleser. Weitere Props: `disabled`, `hint`,
`onUploaded(file)`, `showList`. **Nach dem Speichern** die Komponente per `key` neu aufbauen, um sie zu leeren.
`useFileLimits(purpose)` liefert Limits/Kontingent für eigene Anzeigen.

### `<FileList>` (`src/components/FileList.tsx`)

```tsx
<FileList files={item.files} />                                          // Download + „Ansehen“ (PDF/Bilder)
<FileList files={mine} onDelete={(f) => filesApi.remove(f.id).then(reload)} />   // Löschen nur bei can_delete
<FileList files={attachments} compact emptyText={null} previews={false} />
```

Props: `onDelete` + `canDelete(file)` (Standard `file.can_delete`), `confirmDelete` (Standard ja), `deleteLabel`,
`actions(file)` (eigene Knöpfe), `emptyText` (`null` = nichts), `compact`, `previews` (kleine Bildvorschau, nur für
kurze Listen), `label`. Hinweis „nicht virengeprüft“, wenn der Scanner beim Upload nicht erreichbar war.

### Zwecke (`purpose`)

Im Backend registriert: `channel_material`, `submission`, `channel_post`, `message`, `student_document`. Strengere
Regeln je Zweck legt das Feature im **Backend** fest, z. B.
`files.register_purpose("student_document", kinds=["pdf", "image"], max_mb=10)` – `GET /files/limits?purpose=…`
und damit `<FileUpload>` übernehmen sie automatisch.

## Gestaltung

* UI-Texte Deutsch, Bezeichner Englisch; vorhandene Klassen nutzen (`card`, `card-head`, `btn`, `btn-sm`,
  `btn-ghost`, `badge-*`, `row`, `row-between`, `stack`, `grid grid-2`, `muted`, `small`, `alert-*`) und Bausteine aus
  `components/ui.tsx` (`Alert`, `ErrorBox`, `Loading`, `Empty`, `Field`, `Tabs`, `AsyncButton`, `ProgressBar`).
* Hell/dunkel: nur CSS-Variablen aus `styles/tokens.css` (`var(--surface)`, `var(--text-muted)`, `var(--danger)` …).
* Handy (390 px) ohne horizontales Scrollen: `minWidth: 0` in Flex/Grid-Kindern, lange Namen mit
  `overflowWrap: 'anywhere'`, Raster mit `minmax(min(320px, 100%), 1fr)`, Tabellen in `.table-wrap`.
* Barrierearm: echte Buttons/Links, sichtbare Beschriftungen (`Field`), `aria-live` für Statusmeldungen, Fokus nach
  Dialogen zurück, Bedeutung nie nur über Farbe.
* Innerhalb einer Seite eigene Fehlergrenzen: `FeatureBoundary` aus `components/Layout` (`label`, `silent`, `resetKey`).
* Fehlermeldungen: `toast.error(e)` bzw. `ErrorBox` zeigen deutsche Texte (Validierungsfehler übersetzt, Feldcodes als
  Beschriftung, Unerwartetes als „Das hat nicht geklappt …“ mit Fehlernummer). Fehler am Feld: Formular in
  `<FormErrors error={saveError} labels={{ ref: 'Lehrkraft' }}>` legen und `Field name="<feldcode>"` setzen; eigene
  Beschriftungen auch für Toasts: `toast.error(e, undefined, { labels })`. Neue Backend-Codes (`detail` als String)
  gehören nach `KNOWN_DETAILS` (`api/client.ts`). `AsyncButton` meldet nicht abgefangene Fehler selbst als Toast.

## Tests

* `src/features/<feature>/*.test.ts` mit vitest (`environment: node`, nur `*.test.ts`): reine Logik direkt testen;
  Komponenten mit `createElement` + `renderToStaticMarkup` aus `react-dom/server` (siehe `api/files.test.ts`).
* Registry-Verhalten mit eigenem Testmodul: `loadModules({ './demo/module.tsx': { default: demo } })`
  (siehe `registry.test.ts`) – keine Testmodule im echten `features/`-Ordner ablegen.
* Prüfen: `cd frontend && npx tsc --noEmit -p tsconfig.json && npx vitest run`; Build nur in einen eigenen Ordner
  (`npx vite build --outDir <scratchpad>`), nie nach `frontend/dist`.

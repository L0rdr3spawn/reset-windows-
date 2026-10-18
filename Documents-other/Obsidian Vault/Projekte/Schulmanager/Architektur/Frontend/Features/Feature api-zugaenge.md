---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/features/api-zugaenge/"
stand: 2026-10-12 20:35
generator: schulmanager-regen
---

# Feature api-zugaenge

> Frontend · 6 Datei(en) · 823 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Feature-Modul „API-Zugänge“ (docs/API-ZUGAENGE.md) für die Registry (`features/registry.ts`). * `/api-zugaenge` – Zugänge für Apps/KI-Werkzeuge ausgeben (Recht `api.own`), mit `api.manage` auch alle sehen und widerrufen. Bereichsliste und Filterwerte kommen vom Server (`GET /api-access/meta`) – nichts doppelt pflegen. Importzyklus (siehe registry.ts): beim Laden nur `defineFeature`; Seiten per lazy().

## Routen des Moduls (`module.tsx`)

| Pfad | Seite | Rechte/Rollen | Titel |
|---|---|---|---|
| `/api-zugaenge` | `ApiAccessPage` | anyOf: ANY_OF | API-Zugänge |

Das Modul meldet sich über `defineFeature({routes, nav, widgets, background})` bei der Feature-Registry an ([[Frontend App und Routing]]); Seiten werden per `lazy()` geladen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/features/api-zugaenge/ApiAccessPage.tsx` | 498 | Seite „API-Zugänge“ (`/api-zugaenge`, Recht `api.own` bzw. `api.manage`; docs/API-ZUGAENGE.md): Liste der Zugänge (eigene, mit `a… |
| `frontend/src/features/api-zugaenge/api-zugaenge.css` | 142 | Stylesheet |
| `frontend/src/features/api-zugaenge/api.ts` | 13 | Endpunkte der API-Zugänge (docs/API-ZUGAENGE.md). |
| `frontend/src/features/api-zugaenge/logic.ts` | 57 | Reine Logik der Seite „API-Zugänge“ (ohne React). |
| `frontend/src/features/api-zugaenge/module.tsx` | 22 | Feature-Modul „API-Zugänge“ (docs/API-ZUGAENGE.md) für die Registry (`features/registry.ts`). * `/api-zugaenge` – Zugänge für App… |
| `frontend/src/features/api-zugaenge/types.ts` | 91 | Typen der API-Zugänge (Server: `routes/features_api_access.py`, docs/API-ZUGAENGE.md). |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/api-access` | [[Routen features_api_access]] · `list_access` (`features_api_access.py:175`) |
| POST | `/api-access` | [[Routen features_api_access]] · `create_access` (`features_api_access.py:189`) |
| GET | `/api-access/{…}` | [[Routen features_api_access]] · `get_access` (`features_api_access.py:220`) |
| GET | `/api-access/meta` | [[Routen features_api_access]] · `access_meta` (`features_api_access.py:125`) |
| POST | `/api-access/preview` | [[Routen features_api_access]] · `access_preview` (`features_api_access.py:164`) |

## Backend-Notizen

[[Routen features_api_access]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `client`, `types`
- [[Frontend App und Routing]] – `registry`
- [[Frontend Basis]] – `ToastContext`, `dates`, `misc`, `useApi`
- [[Frontend Komponenten]] – `HelpTip`, `Icon`, `Modal`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]] – die Feature-Registry lädt `./*/module.tsx` automatisch (`import.meta.glob`)


## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->

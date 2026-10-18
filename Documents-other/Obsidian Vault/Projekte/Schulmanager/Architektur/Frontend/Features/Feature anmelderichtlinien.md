---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/features/anmelderichtlinien/"
stand: 2026-10-12 22:26
generator: schulmanager-regen
---

# Feature anmelderichtlinien

> Frontend · 8 Datei(en) · 1854 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Anmelde-Richtlinien (`/anmelde-richtlinien`): wer darf sich wie anmelden; Pflicht-Verknüpfungsseite `/konten-verbinden`.

## Routen des Moduls (`module.tsx`)

| Pfad | Seite | Rechte/Rollen | Titel |
|---|---|---|---|
| `/anmelde-richtlinien` | `PolicyPage` | anyOf: ANY_OF | Anmelde-Richtlinien |

Das Modul meldet sich über `defineFeature({routes, nav, widgets, background})` bei der Feature-Registry an ([[Frontend App und Routing]]); Seiten werden per `lazy()` geladen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/features/anmelderichtlinien/LinkSetupPage.tsx` | 132 | Seite `/konten-verbinden` (§11.5): Pflicht-Verknüpfungen laut Anmelde-Richtlinie herstellen. Der Guard in `App.tsx` leitet hierhe… |
| `frontend/src/features/anmelderichtlinien/PolicyPage.tsx` | 624 | Verwaltungsseite „Anmelde-Richtlinien“ (`/anmelde-richtlinien`, Recht `login_policy.manage`, §11.5): Bereiche Standard · Rollen ·… |
| `frontend/src/features/anmelderichtlinien/RuleEditor.tsx` | 321 | Regel-Editor (Dialog): je Feld „erben“ oder festlegen, Anzeige des geerbten Werts mit Herkunft, Beispiel-Voreinstellung „nur Micr… |
| `frontend/src/features/anmelderichtlinien/anmelderichtlinien.css` | 262 | Stylesheet |
| `frontend/src/features/anmelderichtlinien/api.ts` | 36 | Endpunkte der Anmelde-Richtlinien (§11.5) und der Verknüpfung (Agent Anbieter, §11.4). |
| `frontend/src/features/anmelderichtlinien/logic.ts` | 312 | Reine Logik der Anmelde-Richtlinien (§11.5): Vererbung für die Anzeige „erbt …“ (gleicher Vorrang wie das Backend `server/login_p… |
| `frontend/src/features/anmelderichtlinien/module.tsx` | 24 | Feature-Modul „Anmelde-Richtlinien“ (§11.5) für die Registry (`features/registry.ts`). * `/anmelde-richtlinien` – Verwaltung (Rec… |
| `frontend/src/features/anmelderichtlinien/types.ts` | 143 | Typen der Anmelde-Richtlinien (§11.5, Backend `routes/features_login_policy.py`). |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| GET | `/auth/password-reset/options` | [[Routen features_contact]] · `reset_options` (`features_contact.py:887`) |
| GET | `/login-policies` | [[Routen features_login_policy]] · `list_policies` (`features_login_policy.py:212`) |
| GET | `/login-policies/effective` | [[Routen features_login_policy]] · `effective` (`features_login_policy.py:324`) |
| GET | `/login-policies/report` | [[Routen features_login_policy]] · `report` (`features_login_policy.py:373`) |
| GET | `/auth/sso/providers` | [[Routen features_sso]] · `sso_provider_list` (`features_sso.py:151`) |
| POST | `/me/identities/{…}/link` | [[Routen features_sso]] · `link_start` (`features_sso.py:578`) |
| GET | `/users` | [[Routen users]] · `list_users` (`users.py:126`) |

## Backend-Notizen

[[Routen features_contact]], [[Routen features_login_policy]], [[Routen features_sso]], [[Routen users]]

## Nutzt (Frontend)

- [[Feature anmeldedienste]] – `slots`
- [[Feature konto]] – `api`
- [[Frontend API-Schicht]] – `client`, `endpoints`, `types`
- [[Frontend App und Routing]] – `registry`
- [[Frontend Basis]] – `AuthContext`, `ToastContext`, `dates`, `format`, `misc` …
- [[Frontend Komponenten]] – `Icon`, `Modal`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]] – die Feature-Registry lädt `./*/module.tsx` automatisch (`import.meta.glob`)
- [[Frontend App und Routing]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->

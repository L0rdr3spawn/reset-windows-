---
tags: [schulmanager, architektur, frontend]
quelle: "frontend/src/features/anmeldedienste/"
stand: 2026-10-12 21:09
generator: schulmanager-regen
---

# Feature anmeldedienste

> Frontend · 10 Datei(en) · 1400 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Frontend Übersicht]]

## Zweck

Anmeldedienste (`/anmeldedienste`, nur Administration): Microsoft, Apple, Google und Schulkonto einrichten und testen; Verbindungs-Panel am Konto.

## Routen des Moduls (`module.tsx`)

| Pfad | Seite | Rechte/Rollen | Titel |
|---|---|---|---|
| `/anmeldedienste` | `SetupPage` | roles: ['admin'] | Anmeldedienste |

Das Modul meldet sich über `defineFeature({routes, nav, widgets, background})` bei der Feature-Registry an ([[Frontend App und Routing]]); Seiten werden per `lazy()` geladen.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `frontend/src/features/anmeldedienste/IdentitiesSection.tsx` | 125 | Profil → „Verbundene Konten“: je Anbieter Status (verbunden als …, seit …), Verbinden/Trennen, Pflicht-Kennzeichen, Hinweis „wird… |
| `frontend/src/features/anmeldedienste/OfficialButtons.tsx` | 204 | Offizielle Anmelde-Knöpfe der Anbieter (§11.4), nur für Anbieter, die in den Anmeldediensten eingeschaltet sind: - Google: „Sign… |
| `frontend/src/features/anmeldedienste/SetupPage.tsx` | 278 | `/anmeldedienste` (nur Administration): Microsoft, Apple, Google und Schulkonto (OIDC) einrichten – Felder je Anbieter, Weiterlei… |
| `frontend/src/features/anmeldedienste/UserIdentitiesPanel.tsx` | 120 | Benutzerverwaltung → Reiter „Verbundene Konten“: Verknüpfungen eines Kontos ansehen, lösen und eine E-Mail-Adresse vormerken (bei… |
| `frontend/src/features/anmeldedienste/anmeldedienste.css` | 159 | Stylesheet |
| `frontend/src/features/anmeldedienste/api.ts` | 27 | Endpunkte der Anmeldedienste (§11.4). |
| `frontend/src/features/anmeldedienste/logic.ts` | 216 | Reine Logik der Anmeldedienste (§11.4) – ohne React, mit vitest getestet. |
| `frontend/src/features/anmeldedienste/module.tsx` | 20 | Feature-Modul „Anmeldedienste“ (ARCHITECTURE.md §11.4) für die Registry (`features/registry.ts`). * `/anmeldedienste` (nur Admini… |
| `frontend/src/features/anmeldedienste/slots.tsx` | 105 | Einhängepunkte des Features „anmeldedienste“ (§11.4) in geteilten Seiten. LoginPage: <SsoButtons next hidden /> + SSO_ERROR_MESSA… |
| `frontend/src/features/anmeldedienste/types.ts` | 146 | Typen der Anmeldedienste (§11.4) – Antworten von `routes/features_sso.py`. |

## API-Aufrufe

| Methode | Aufruf im Code | Backend |
|---|---|---|
| POST | `/auth/sso/{…}/nonce` | [[Routen features_sso]] · `sso_nonce` (`features_sso.py:327`) |
| POST | `/auth/sso/{…}/token` | [[Routen features_sso]] · `sso_token` (`features_sso.py:338`) |
| GET | `/auth/sso/providers` | [[Routen features_sso]] · `sso_provider_list` (`features_sso.py:151`) |
| GET | `/me/identities` | [[Routen features_sso]] · `my_identities` (`features_sso.py:573`) |
| DELETE | `/me/identities/{…}` | [[Routen features_sso]] · `unlink_mine` (`features_sso.py:609`) |
| POST | `/me/identities/{…}/link` | [[Routen features_sso]] · `link_start` (`features_sso.py:578`) |
| PUT | `/sso/providers/{…}` | [[Routen features_sso]] · `update_provider` (`features_sso.py:836`) |
| POST | `/sso/providers/{…}/test` | [[Routen features_sso]] · `test_provider` (`features_sso.py:905`) |
| GET | `/sso/providers/config` | [[Routen features_sso]] · `provider_config` (`features_sso.py:808`) |
| GET | `/users/{…}/identities` | [[Routen features_sso]] · `user_identities` (`features_sso.py:664`) |
| POST | `/users/{…}/identities` | [[Routen features_sso]] · `reserve_identity` (`features_sso.py:670`) |
| DELETE | `/users/{…}/identities/{…}` | [[Routen features_sso]] · `remove_identity` (`features_sso.py:698`) |

## Backend-Notizen

[[Routen features_sso]]

## Nutzt (Frontend)

- [[Frontend API-Schicht]] – `client`
- [[Frontend App und Routing]] – `registry`
- [[Frontend Basis]] – `ToastContext`, `dates`, `misc`, `useApi`
- [[Frontend Komponenten]] – `HelpTip`, `Icon`, `ui`

## Wird genutzt von

- [[Frontend App und Routing]] – die Feature-Registry lädt `./*/module.tsx` automatisch (`import.meta.glob`)
- [[Feature anmelderichtlinien]]
- [[Frontend Komponenten]]
- [[Seite LoginPage]]
- [[Seite ProfilePage]]
- [[Seite UsersPage]]

## Siehe auch

- [[Frontend Übersicht]] · [[Rollen und Rechte]] (Sichtbarkeit nach Recht, `lib/permissions.ts`) · [[Abhängigkeiten]]

<!-- eigene Notizen -->

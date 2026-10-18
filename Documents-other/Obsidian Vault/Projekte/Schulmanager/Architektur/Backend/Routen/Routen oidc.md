---
tags: [schulmanager, architektur, routen]
quelle: "schulmanager/server/routes/oidc.py"
stand: 2026-10-12 20:25
generator: schulmanager-regen
---

# Routen oidc

> API-Routen · 1 Datei(en) · 74 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Routen Übersicht]]

## Zweck

Single Sign-on über das Schulkonto (OpenID Connect) – alte Pfade `/auth/oidc/*`.

Seit §11.4 (Anmeldedienste) ist das Schulkonto der Anbieter `oidc` der gemeinsamen Umsetzung in `routes/features_sso.py` und `server/sso_providers.py` (Authorization Code Flow + PKCE + nonce). Diese Pfade bleiben, weil die Redirect-URI beim Identity Provider eingetragen ist.

Konfiguration: `SM_OIDC_ISSUER`, `SM_OIDC_CLIENT_ID`, `SM_OIDC_CLIENT_SECRET` (optional bei Public Clients), `SM_OIDC_SCOPES` (`openid profile email`), `SM_OIDC_USERNAME_CLAIM` (`preferred_username`), `SM_OIDC_AUTO_CREATE` (0), `SM_OIDC_DEFAULT_ROLE` (`lehrer`), `SM_OIDC_LABEL` – oder im Admin-Bereich „Anmeldedienste“ (Umgebungsvariablen haben Vorrang). Redirect-URI beim Identity Provider eintragen (unverändert): `{SM_BASE_URL}/api/v1/auth/oidc/callback`.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/routes/oidc.py` | 74 | Single Sign-on über das Schulkonto (OpenID Connect) – alte Pfade `/auth/oidc/*`. |

## Endpunkte (2)

Alle Pfade unter `/api/v1`.

| Methode | Pfad | Funktion | Recht | Frontend |
|---|---|---|---|---|
| GET | `/api/v1/auth/oidc/login` | `oidc_login` (`oidc.py:59`) | - | – |
| GET | `/api/v1/auth/oidc/callback` | `oidc_callback` (`oidc.py:67`) | - | – |

*Recht: Name = per `require()` im Dekorator geprüft; „(angemeldet)“ = nur Anmeldung im Dekorator, Rechte und Datenumfang prüft der Handler selbst (`need`, `has`, Scope-Hilfen); „-“ = öffentlich.*

## Wichtige Hilfsfunktionen und Modelle

- Funktion `discovery` (`schulmanager/server/routes/oidc.py:43`) – Metadaten des per Umgebung eingerichteten Schulkontos (kompatibel zur alten Schnittstelle).
- Funktion `decode_id_token` (`schulmanager/server/routes/oidc.py:48`)

## Hängt ab von

- [[Routen features_sso]] – `features_sso` *(nur zur Laufzeit importiert)*
- [[Server db]] – `db`
- [[Server konten und anmeldung]] – `sso_providers`

## Wird genutzt von

- [[Server konten und anmeldung]] – `sso_providers`

## Tests

`tests/test_server_core.py`, `tests/test_sso.py`

*(Zuordnung über Importe bzw. Pfad-Treffer, Näherung)*

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->

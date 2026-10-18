---
tags: [schulmanager, architektur, server]
quelle: "schulmanager/server/events.py"
stand: 2026-10-12 21:40
generator: schulmanager-regen
---

# Server events

> Server-Kern · 1 Datei(en) · 173 Zeilen · Einstieg: [[Schulmanager Architektur]] → [[Backend Übersicht]]

## Zweck

Ereignisbus für Live-Updates: `bus.publish("change" | "job", …)` ist thread-sicher; SSE-Clients (`GET /api/v1/events`) bekommen die Ereignisse über je eine Queue, synchrone Listener (z. B. [[Server notify]], [[Server autoplan]]) werden direkt aufgerufen. Das Frontend hält eine Verbindung (`api/events.ts`) und lädt per `useLive` / `useApi(…, {live})` neu.

## Dateien

| Datei | Zeilen | Aufgabe |
|---|---|---|
| `schulmanager/server/events.py` | 173 | Ereignisbus für Live-Updates (Server-Sent Events). |

## Wichtige Funktionen und Klassen

- Klasse `Subscription` (`schulmanager/server/events.py:28`)
- Klasse `EventBus` (`schulmanager/server/events.py:37`)
  - Methoden: `subscribe`:47, `unsubscribe`:56, `client_count`:62, `add_listener`:67, `remove_listener`:73, `publish`:79, `clear`:103
- Funktion `format_sse` (`schulmanager/server/events.py:124`) – Formatiert eine SSE-Nachricht.
- Funktion `sse_stream` (`schulmanager/server/events.py:137`) – Async-Generator für die SSE-Antwort.

## Hängt ab von

- –

## Wird genutzt von

- [[Routen admin]]
- [[Routen events]]
- [[Routen features_channels]]
- [[Routen features_chats]]
- [[Routen features_common]]
- [[Routen features_forms]]
- [[Routen features_mail]]
- [[Routen features_messages]]
- [[Routen features_parent_access]]
- [[Routen features_student_absences]]
- [[Routen features_teacher_profile]]
- [[Routen files]]
- [[Server app]] – `app`
- [[Server autoplan]]
- [[Server betrieb]] – `demo_loader`
- [[Server jobs]]
- [[Server notify]]
- [[Server runtime]]
- [[Server store]]

## Tests

`tests/test_classes.py`, `tests/test_messages.py`, `tests/test_server_core_store.py`, `tests/test_server_features.py`, `tests/test_teacher_profile.py`

## Siehe auch

- [[Schulmanager Architektur]] · [[Abhängigkeiten]] · [[Datenmodell]] · [[Rollen und Rechte]]

<!-- eigene Notizen -->

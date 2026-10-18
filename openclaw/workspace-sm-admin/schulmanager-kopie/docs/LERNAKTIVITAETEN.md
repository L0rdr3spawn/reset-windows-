# Lernaktivitäten: Abstimmung, Umfrage, Selbsttest, Formeln

Eigene Umsetzung der Moodle-Bausteine `choice`, `feedback` und eines einfachen `quiz` (kein volles Quiz-System, kein Moodle-Code).
Code: Logik `schulmanager/learning.py` (rein), Dienste `server/learning_service.py`, Meldungen `server/learning_notify.py`, Demo
`server/learning_demo.py`, Tabellen `feature_models/learning.py` (Migration `0038_learning`), Routen `routes/features_learning_polls.py`,
`…_surveys.py`, `…_tests.py`; Oberfläche `frontend/src/features/lernen/*` (Kursraum-Bereich „Tests & Umfragen“, `?tab=tests&bereich=`),
Chat-Umfragen in `features/chats`. Tests: `tests/test_learning_logic.py`, `tests/test_learning_api.py`, `lernen/logic.test.ts`,
`channels/math.test.ts`.

## 1. Rechte
Keine neuen Rechte: Es gelten die Rollen im Kursraum. Lehrende (`channels.manage`) legen an, ändern, werten aus; Teilnehmende
stimmen ab, antworten und machen Tests; Eltern lesen nur Abstimmungen; die Aufsicht liest Abstimmungen. In Klassenräumen ändern und
werten aus nur die Ersteller/innen, Klassenleitung und Kursraum-Verwaltung (`Ctx.may_edit`). Chat-Umfragen: wer schreiben darf.
Jede Schreibaktion steht im Audit (`poll.*`, `survey.*`, `question.*`, `selftest.*`), nie mit Inhalten oder gewählten Antworten.

## 2. Abstimmung
Eine oder mehrere Antworten (optional Höchstzahl), anonym oder namentlich, Ergebnis sofort / nach der eigenen Stimme / nach dem Ende,
Enddatum, vorzeitig beenden, Ergebnis als Balken. Namentlich: Stimmen änderbar, Namen sichtbar für alle, die das Ergebnis sehen (Eltern nie).
**Anonym**: gespeichert werden nur „hat abgestimmt“ (`learning_poll_participants`) und ein Zähler je Antwort (`learning_poll_tally`);
`learning_poll_votes` bleibt leer – Person und Stimme sind nicht verknüpft, daher nicht änderbar. Frage und Antworten im Kursraum
serverseitig verschlüsselt. **Chat**: Frage und Antworten stehen nur im Ende-zu-Ende-verschlüsselten Inhalt (`Payload.poll.options`,
Frage = `text`); der Server kennt nur Einstellungen, Zahl der Antworten und Stimmen (`POST /chats/{id}/messages` mit `poll`,
`PUT …/messages/{mid}/vote`, `POST …/poll/close`). Löschen der Nachricht oder des Chats entfernt Abstimmung und Stimmen.

## 3. Umfrage (Feedback)
Der Formular-Baukasten wurde erweitert statt gedoppelt: neue Feldart **Skala 1–5** (`scale`, mit Beschriftung der Enden) in
`forms.py`, Editor und Ausfüllen; `forms.normalize_fields(…, allowed=)` und `clean_answers` prüfen die Umfragefragen, `FieldEditor` und
`FormFields` der Oberfläche werden wiederverwendet. Erlaubt: Auswahl, Mehrfachauswahl, Ja/Nein, Skala, Freitext, kurzer Text, Zahl.
Nicht übernommen wurden Einreichungen, Eingang und Genehmigung, weil sie an Personen, Kinder und Prüfschritte gebunden sind – Umfragen
brauchen eine Kursraum-Zielgruppe und echte Anonymität. Anonym: Antworten ohne Konto, nur mit Tagesdatum, getrennt davon „hat geantwortet“,
Einzelantworten in zufälliger Reihenfolge. Fragen und Anonymität sind nach der ersten Antwort gesperrt. Auswertung: Balken, Mittelwert,
Texte, CSV (`export.csv`, Semikolon, BOM, Formel-Schutz); Teilnehmende sehen sie nur nach dem Ende und bei Freigabe.

## 4. Selbsttest
Fragensammlung je Kursraum (`learning_questions`, verschlüsselt, wiederverwendbar, aus anderen eigenen Kursräumen kopierbar):
Einfachauswahl, Mehrfachauswahl (Teilpunkte: (Treffer − Fehler) / Richtige, nie negativ), Wahr/Falsch, Lückentext (`___`, exakte Antwort,
mehrere zulässige, Groß-/Kleinschreibung wählbar, Teilpunkte je Lücke), Zuordnung, Zahl mit Toleranz (Komma erlaubt). Test: Versuche,
Zeitlimit, Fragen und Antworten mischen (fester Startwert je Versuch), Rückmeldung sofort je Frage (Antwort danach gesperrt), Anzeige nach
dem Abgeben (nichts / Punktestand / mit Lösungen), Bestehensgrenze, Beginn und Ende. Gewertet wird nur auf dem Server mit dem **Abbild der
Fragen beim Start** des Versuchs; die Lösung geht vor dem Abgeben nie an den Browser. Abgelaufene Versuche werden beim nächsten Zugriff mit
den gespeicherten Antworten abgeschlossen. Lehrkräfte können probieren (zählt nicht in der Auswertung). Auswertung je Schüler/in und Frage,
Fragenstatistik, CSV, einzelne Versuche ansehen. **GIFT** Import/Export (Auswahl, Wahr/Falsch, Kurzantwort als Lückentext, Zuordnung, Zahl;
ein Lückentext mit mehreren Lücken wird beim Export übersprungen und gemeldet). Moodle-XML ist nicht umgesetzt.

### Anbindung für Notenbuch (M4) und Abschlussbedingung (M2)
Element = **Typ + ID**: `selftest` (`learning_selftests.id`), `survey`, `poll`; Punkte = bester Versuch, `points` von `max_points`.

* Notenbuch: `learning_service.publish_grades` ruft `gradebook_sources.publish_results(source_type="selbsttest", source_id=<Test-ID>, …)`
  beim Abgeben und Ändern auf (nur Kursraum eines Kursteils), `withdraw_results` beim Löschen. Übernehmen bleibt Entscheidung der
  Lehrkraft. Für Auswahllisten: `GET /channels/{id}/learning/elements`, Punkte je Person `GET /channels/{id}/selftests/{tid}/grades`.
* Abschlussbedingung: `learning_service.element_status(db, typ, id, user_id)` liefert `{done, points, max_points, percent, passed}`;
  dazu `selftest_done` (beendeter Versuch, Bestehensgrenze erreicht), `survey_done`, `poll_done`.

## 5. Mathe-Formeln
`$…$` (Text) und `$$…$$` (Block) in `MarkdownView` (Material, Aufgaben, Selbsttest, Pinnwand, Klasseninfos …). KaTeX ist lokal gebündelt
(`katex` 0.19 über npm; wird erst beim ersten Text mit Formel nachgeladen, Schriften und Stil lokal, kein CDN). Sicher: Der Parser liefert
nur den Formel-Quelltext, gesetzt wird mit `katex.render` ins Element (kein `innerHTML`), `trust: false`, Grenzen für Größe und
Makro-Erweiterung, Fehler erscheinen als Quelltext. „5 $ und 6 $“ bleibt Text (Pandoc-Regel), `\$` maskiert. Nachrichten und Chats sind
kein Markdown und zeigen keine Formeln.

## 6. Benachrichtigungen
Neue Abstimmung, Umfrage oder Selbsttest (freigegeben) → Teilnehmende (Schüler/innen) erhalten `poll` bzw. `selftest` mit Kursraum-Link;
der Text nennt nur den Kursraum (`learning_notify.announce`).

## 7. Demo
`learning_demo.seed_demo`: Klassen 5a und 7a: sechs Fragen (eine mit Formeln), Selbsttest mit Versuchen, namentliche Abstimmung,
anonyme Umfrage.

## 8. Offen
Moodle-XML-Import; Fragen mit Bildern oder Dateien; Umfragen außerhalb des Kursraums (Elternabend o. Ä.); Abstimmung und Umfrage als
Abschlussbedingung nur über die Python-Funktionen (kein HTTP); Formeln in Nachrichten; Medienplayer.

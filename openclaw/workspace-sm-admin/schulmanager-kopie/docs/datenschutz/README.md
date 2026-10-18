# Datenschutz-Unterlagen für den Betrieb (Vorlagen)

> **Vorlagen und Entwürfe – keine Rechtsberatung.** Die Dokumente in diesem Ordner helfen der Schule, ihre Pflichten nach DSGVO und Landesschul- bzw. Landesdatenschutzgesetz zu erfüllen. Sie müssen von der Schulleitung, der bzw. dem Datenschutzbeauftragten und gegebenenfalls dem Schulträger geprüft, an die Schule angepasst und freigegeben werden. Die Verantwortung für die Verarbeitung trägt die Schule.

| Datei | Inhalt | Wer füllt aus |
|---|---|---|
| [`vvt-vorlage.md`](vvt-vorlage.md) | Verzeichnis der Verarbeitungstätigkeiten (Art. 30 DSGVO), vorbefüllt für Schulpuls | Schulleitung mit DSB |
| [`toms.md`](toms.md) | Technische und organisatorische Maßnahmen (Art. 32 DSGVO), aus dem tatsächlichen Verhalten der Software abgeleitet, mit Fundstellen | IT/Administration, DSB |
| [`datenschutzhinweise-eltern.md`](datenschutzhinweise-eltern.md) | Information nach Art. 13/14 DSGVO für Eltern | Schulleitung |
| [`datenschutzhinweise-schueler.md`](datenschutzhinweise-schueler.md) | Information für Schülerinnen und Schüler in einfacher Sprache | Schulleitung |
| [`datenschutzhinweise-lehrkraefte.md`](datenschutzhinweise-lehrkraefte.md) | Information für Lehrkräfte und weiteres Personal | Schulleitung, ggf. Personalrat |

Löschfristen, Auskunft und Löschprotokoll der Software: [`../DATENSCHUTZ-LOESCHKONZEPT.md`](../DATENSCHUTZ-LOESCHKONZEPT.md). Sicherheitskonzept mit Härtung und Meldeablauf bei Datenpannen: [`../SICHERHEIT.md`](../SICHERHEIT.md).

## Auftragsverarbeitung (AV-Vertrag, Art. 28 DSGVO)

Die Software wird **auf einem Server der Schule oder ihres Dienstleisters** betrieben; der Softwareanbieter erhält ohne weitere Vereinbarung **keinen Zugriff** auf personenbezogene Daten. Ein AV-Vertrag ist nötig, sobald eine andere Stelle im Auftrag der Schule Daten verarbeitet oder darauf zugreifen kann:

| Stelle | AV-Vertrag nötig? | Anmerkung |
|---|---|---|
| Hoster / Rechenzentrum (Server, Speicher) | ja | Standort Deutschland/EU bevorzugen; Zertifizierung (z. B. ISO 27001) erfragen |
| IT-Dienstleister des Schulträgers (Administration) | ja | Zugriffe auf die Instanz regeln, Administrationskonten personengebunden |
| Softwareanbieter bei Fernwartung, Support mit Zugriff auf Daten oder gehostetem Betrieb | ja | nur dann; Muster des Anbieters verwenden und prüfen |
| E-Mail-Versand (SMTP-Anbieter) | ja | es werden Namen, Betreffzeilen und Nachrichtentexte übertragen |
| SMS-Anbieter (falls `SM_SMS_PROVIDER` genutzt) | ja | Telefonnummern und Codes |
| Offsite-Backup-Speicher | ja | Backups sind mit `BACKUP_GPG_PASSPHRASE` verschlüsselt; der Anbieter sieht keinen Klartext |
| Anmeldedienste Microsoft, Google, Apple (falls genutzt) | prüfen | eigene Verantwortlichkeit bzw. Auftragsverarbeitung je nach Vertrag; Datenschutzbeauftragte/n einbinden |
| Let's Encrypt | nein | erhält nur Domainname und Kontaktadresse |
| Lizenzserver des Anbieters | prüfen | übermittelt Lizenzkennung und Konto-Anzahl, keine Personendaten (Prüfung vor Einsatz dokumentieren) |

Die Schule schließt den Vertrag mit jeder dieser Stellen. Muster stellen häufig die Landesdatenschutzbehörden, die Kultusministerien oder der Schulträger bereit.

## Datenschutz-Folgenabschätzung (DSFA, Art. 35 DSGVO)

Eine DSFA ist nötig, wenn die Verarbeitung voraussichtlich ein hohes Risiko für die Betroffenen hat. Für Schulverwaltungssoftware sprechen mehrere Punkte dafür, **zumindest eine dokumentierte Schwellwertanalyse** durchzuführen:

- Daten Minderjähriger in großer Zahl,
- Gesundheitsbezug (Krankmeldungen, Atteste) und mittelbare besondere Kategorien (Religionskurse, Förderbedarf),
- Kommunikationsfunktionen mit Meldeverfahren (Chats),
- Auswertung von Leistungs- und Fehlzeitdaten.

Prüfen Sie außerdem die **Muss-Liste** Ihrer Landesdatenschutzbehörde (Liste der Verarbeitungsvorgänge, für die eine DSFA durchzuführen ist). Dokumentieren Sie das Ergebnis auch dann, wenn keine DSFA nötig ist. Hilfreiche Bausteine aus der Software: Rollen- und Rechtekonzept (`../ROLLEN-RECHTE.md`), Verschlüsselung (`toms.md`), Löschkonzept, Audit-Protokoll.

## Reihenfolge für die Schule

1. Datenschutzbeauftragte/n einbinden, Zuständigkeiten klären.
2. `vvt-vorlage.md` ausfüllen und ins Verzeichnis der Schule übernehmen.
3. AV-Verträge abschließen (Tabelle oben).
4. DSFA-Schwellwertanalyse durchführen und ablegen.
5. `toms.md` mit der tatsächlichen Installation abgleichen (Hoster, Server, Organisation ergänzen).
6. Datenschutzhinweise anpassen, verteilen und den Erhalt nachweisen (soweit Landesrecht das verlangt).
7. Personal schulen: Passwörter, Zwei-Faktor, Zugangsbriefe, Umgang mit Exporten.
8. Jährlich prüfen (zum Schuljahreswechsel).

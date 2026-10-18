# Kurzanleitung für die Administration

## Erste Schritte
1. Melden Sie sich mit dem Erst-Administrator an und vergeben Sie ein eigenes Passwort.
2. Richten Sie im **Profil** die Zwei-Faktor-Anmeldung ein.
3. Folgen Sie dem **Einrichtungsassistenten** (Menü „Schule einrichten“).

## Status und Betrieb
Das Menü **Betrieb** zeigt auf einen Blick, ob alles in Ordnung ist: Datenbank und Schemastand, freier Speicher, letzte Sicherung, E-Mail-Versand, Verschlüsselung, Lizenz und Wartungslauf. Darunter finden Sie die Sicherungen und das Fehlerprotokoll.

- **Sicherung erstellen** legt sofort eine App-Sicherung an. Zusätzlich sichert der Backup-Dienst der Installation täglich Datenbank und Dateien.
- **Prüfen** spielt eine Sicherung in eine Wegwerf-Kopie ein und kontrolliert sie (Test-Restore). Machen Sie das mindestens monatlich.
- **Fehlerprotokoll**: Fehler der letzten 30 Tage mit Fehlernummer. Die Nummer nennen Nutzerinnen und Nutzer, wenn etwas schiefgeht.
- Hinweise (gelb) sind Empfehlungen, Fehler (rot) brauchen Ihre Aufmerksamkeit.

## Schlüssel
Der Verschlüsselungsschlüssel (`SM_ENCRYPTION_KEYS`) steht in der Konfiguration der Installation. Bewahren Sie ihn getrennt von den Sicherungen auf. Ohne ihn sind verschlüsselte Inhalte nach einer Wiederherstellung nicht lesbar.

## Konten
Unter **Benutzer** verwalten Sie Konten, setzen Passwörter zurück und entsperren Konten nach Fehlversuchen. Die Kommandozeile bietet dasselbe, wenn niemand mehr anmelden kann (`schulmanager-admin`).

## Updates
Updates, Migrationen und Rollback beschreibt die Installationsanleitung. Erstellen Sie vor jedem Update eine Sicherung.

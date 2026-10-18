-- Hauptserver: Änderungen von "thorsten" (Protokoll Nr. 129 und 130 vom 16.10. 22:11/22:12) rückgängig machen.
-- Nur bei gestopptem Server ausführen. Sicherung: ~/backups/schulmanager-data-vor-kontosperre-20261017-001458
PRAGMA foreign_keys=ON;
BEGIN;
-- 129: admin war von admin auf sekretariat herabgestuft worden -> zurück auf admin
UPDATE users SET role='admin', active=1 WHERE id=1 AND username='admin';
-- 130: von thorsten angelegtes Admin-Konto "luemmel" (Luis der lümmel), nie angemeldet -> löschen
DELETE FROM users WHERE id=5464 AND username='luemmel';
-- thorsten selbst: niedrigste Stufe, deaktiviert, angemeldete Sitzungen beenden
UPDATE users SET role='schueler', active=0 WHERE id=5463 AND username='thorsten';
DELETE FROM sessions WHERE user_id=5463;
INSERT INTO audit_log(created_at, user_id, username, action, target, details, ip)
 VALUES (datetime('now'), NULL, 'system', 'admin.incident_revert', 'user:5463',
  '{"reverted": [129, 130], "admin_role": "admin", "deleted_user": 5464, "thorsten": "schueler, deaktiviert"}', NULL);
COMMIT;
SELECT id, username, role, active FROM users WHERE id IN (1,5463,5464);
PRAGMA integrity_check;

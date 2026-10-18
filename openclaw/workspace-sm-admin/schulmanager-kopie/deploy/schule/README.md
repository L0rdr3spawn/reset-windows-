# Compose-Beispiel für Schulen

Das fertige Beispiel für den Echtbetrieb ist [`docker-compose.yml`](../../docker-compose.yml) im Wurzelverzeichnis: Anwendung (`SM_MODE=production`), PostgreSQL im internen Netz, Caddy mit automatischem HTTPS (Let's Encrypt), Backup-Dienst mit täglicher verschlüsselter Sicherung (Cron-Zeit `BACKUP_TIMES`) und benannte Volumes. Für sehr kleine Schulen ohne PostgreSQL: [`docker-compose.sqlite.yml`](../../docker-compose.sqlite.yml).

```bash
scripts/init-env.sh --domain plan.meine-schule.de --email it@meine-schule.de   # .env mit Zufallsgeheimnissen
docker compose run --rm app python -m schulmanager.server.cli check-config     # Konfiguration prüfen
docker compose up -d --build
```

Schritt für Schritt mit Prüfliste: [`docs/INSTALLATION.md`](../../docs/INSTALLATION.md). Alle Variablen: [`.env.example`](../../.env.example).

#!/bin/sh
# Update aller drei Schulmanager-Instanzen auf das neue Image (Datenbank-Updates laufen beim Start automatisch).
# Sicherung vorher: DB-Kopien in ~/schulmanager/backups, voriges Image als schulmanager:vor-update-<Zeit>.
set -e
TS=$(date +%Y%m%d-%H%M)
NEW=schulmanager:neu-2026-10-17
mkdir -p ~/schulmanager/backups
docker tag schulmanager:test schulmanager:vor-update-$TS
for v in schulmanager_data schulmanager-neu_data; do
  docker run --rm -v $v:/d -v $HOME/schulmanager/backups:/b alpine sh -c \
    "apk add --no-cache sqlite >/dev/null 2>&1; sqlite3 /d/schulmanager.db \".backup /b/$v-vor-update-$TS.db\" || cp -a /d/schulmanager.db /b/$v-vor-update-$TS.db"
done
echo "== Sicherungen:"; ls -la ~/schulmanager/backups | grep vor-update-$TS
docker tag $NEW schulmanager:test
cd ~/schulmanager && rm -rf src.old && mv src src.old && mv src.new src
docker compose up -d app
cd ~/schulmanager-neu && docker compose up -d
echo "== Demo neu aufsetzen (Demo-Zugänge dz-… bleiben)"
~/schulmanager-demo/reset.sh
tail -4 ~/logs/schulmanager-demo.log
sleep 20
docker ps --format "{{.Names}} {{.Status}}" | grep schulmanager
echo "fertig – zurück: docker tag schulmanager:vor-update-$TS schulmanager:test, DB aus ~/schulmanager/backups zurückkopieren"

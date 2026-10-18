#!/bin/sh
# Neuen Stand (Image schulmanager:neu-2026-10-12, Quelle ~/schulmanager/src.new) auf alle drei Schulmanager-Instanzen.
# Sicherung: DB-Kopien in ~/schulmanager/backups, altes Image schulmanager:vor-merge, alter Code ~/schulmanager/src.old
set -e
TS=$(date +%Y%m%d-%H%M)
NEW=schulmanager:neu-2026-10-12
mkdir -p ~/schulmanager/backups
docker image inspect schulmanager:vor-merge >/dev/null 2>&1 || docker tag schulmanager:test schulmanager:vor-merge
echo "== Haupt- und saubere Instanz anhalten"
docker stop schulmanager schulmanager-neu >/dev/null
for v in schulmanager_data schulmanager-neu_data; do
  docker run --rm -v $v:/d -v $HOME/schulmanager/backups:/b alpine cp -a /d/schulmanager.db /b/$v-vor-merge-$TS.db
  echo "== Datenbank $v umstellen"
  docker run --rm -e SM_HOLIDAY_IMPORT=0 -v $v:/app/data -v /tmp/migrate_copy.py:/mig.py:ro --entrypoint python $NEW /mig.py \
    2>&1 | grep -E "alte|neue|PROBLEME|Verstöße|!"
done
docker tag $NEW schulmanager:test
cd ~/schulmanager && rm -rf src.old && mv src src.old && mv src.new src
docker compose up -d app
cd ~/schulmanager-neu && docker compose up -d
echo "== Demo neu aufsetzen (Demo-Zugänge dz-… bleiben)"
~/schulmanager-demo/reset.sh
tail -6 ~/logs/schulmanager-demo.log
sleep 20
docker ps --format "{{.Names}} {{.Status}}" | grep schulmanager
echo "fertig – Sicherungen: ~/schulmanager/backups/*-vor-merge-$TS.db"
# Zurück: docker stop schulmanager schulmanager-neu; docker tag schulmanager:vor-merge schulmanager:test;
#   je Volume schulmanager.vor-merge.db zurück in schulmanager.db umbenennen; docker start …; ~/schulmanager-demo/reset.sh

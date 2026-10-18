# syntax=docker/dockerfile:1
#
# Schulmanager – Backup-Sidecar
# Basis: offizielles postgres-Image → pg_dump/pg_restore/psql passen exakt zur Server-Version.
# Zusätzlich: sqlite (SQLite-Betrieb), gnupg (Verschlüsselung), rclone (Offsite: S3, SFTP, WebDAV …).
#
# Build-Kontext ist das Repository-Root (siehe docker-compose.yml):
#   docker build -f deploy/backup/Dockerfile -t schulmanager-backup .
ARG POSTGRES_VERSION=16
FROM postgres:${POSTGRES_VERSION}-alpine

# Optional: CA-Bundle für TLS-inspizierende Proxys (--secret id=ca_bundle,src=…), landet nicht im Image
RUN --mount=type=secret,id=ca_bundle \
    if [ -f /run/secrets/ca_bundle ]; then export SSL_CERT_FILE=/run/secrets/ca_bundle; fi; \
    apk add --no-cache bash coreutils findutils tar gzip sqlite gnupg rclone curl tzdata util-linux \
 && mkdir -p /backups

COPY --chmod=0755 scripts/backup.sh /usr/local/bin/backup.sh
COPY --chmod=0755 scripts/restore.sh /usr/local/bin/restore.sh
COPY --chmod=0755 deploy/backup/backup-loop.sh /usr/local/bin/backup-loop.sh

ENV BACKUP_DIR=/backups \
    BACKUP_TIMES=02:30 \
    TZ=Europe/Berlin

WORKDIR /backups
VOLUME ["/backups"]

# Gesund = letztes erfolgreiches Backup jünger als BACKUP_MAX_AGE_HOURS (Default 26 h)
HEALTHCHECK --interval=5m --timeout=10s --start-period=15m --retries=1 \
    CMD ["backup-loop.sh", "--check"]

STOPSIGNAL SIGTERM
ENTRYPOINT ["backup-loop.sh"]

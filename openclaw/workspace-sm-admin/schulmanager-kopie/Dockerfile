# syntax=docker/dockerfile:1
#
# Schulmanager – Container-Image (Produktion)
#
#   Stage "frontend": baut die React/Vite-SPA nach frontend/dist
#   Stage "pydeps":   installiert die Python-Abhängigkeiten aus requirements.lock (Hashes) in ein venv
#                     (eigener Layer → wird nur neu gebaut, wenn sich das Lockfile ändert)
#   Stage "dev":      Entwicklungs-Image (Abhängigkeiten inkl. [dev]); Quellcode wird gemountet
#   Stage "runtime":  schlankes Laufzeit-Image, non-root, Healthcheck  (Standard-Target)
#
# Bauen:   docker build -t schulmanager:latest .
# Starten: docker run -p 8000:8000 -v schulmanager-data:/app/data \
#            -e SM_SECRET_KEY=$(openssl rand -hex 32) -e SM_ADMIN_USER=admin \
#            -e SM_ADMIN_PASSWORD='…' schulmanager:latest
#
# Build hinter einem TLS-inspizierenden Proxy (z. B. Schulträger-Netz): vollständiges CA-Bundle
# (System-CAs + Proxy-CA) als Build-Secret übergeben – es landet NICHT im Image:
#   docker build --secret id=ca_bundle,src=/etc/ssl/certs/ca-certificates.crt -t schulmanager .
#
# Wichtig: Die App hält die Planungsdaten im Speicher (SchoolStore) und verteilt Live-Updates
# per SSE prozesslokal. Deshalb läuft genau EIN uvicorn-Worker pro Container (SM_WORKERS=1).

ARG PYTHON_VERSION=3.12
ARG NODE_VERSION=22

# ---------------------------------------------------------------------------
# Stage 1: Frontend bauen
# ---------------------------------------------------------------------------
FROM node:${NODE_VERSION}-alpine AS frontend
WORKDIR /build/frontend
ENV CI=true \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false \
    NPM_CONFIG_AUDIT=false
# Erst nur die Manifeste kopieren → npm-Layer bleibt gecacht, solange sich Abhängigkeiten nicht ändern.
COPY frontend/package.json frontend/package-lock.json* ./
RUN --mount=type=cache,target=/root/.npm \
    --mount=type=secret,id=ca_bundle \
    if [ -f /run/secrets/ca_bundle ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/ca_bundle; fi; \
    if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY frontend/ ./
RUN npm run build && test -f dist/index.html

# ---------------------------------------------------------------------------
# Stage 2: Python-Abhängigkeiten (venv)
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS pydeps
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH
RUN python -m venv /opt/venv
WORKDIR /build
COPY pyproject.toml README.md* requirements.lock requirements-dev.lock ./
# Nur die Abhängigkeiten installieren – exakt die gesperrten Versionen mit Hashes (S-14, requirements.lock;
# erneuern mit `make lock`). setuptools/wheel bleiben im venv (für die Editable-Installation im Runtime-Image).
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=secret,id=ca_bundle \
    if [ -f /run/secrets/ca_bundle ]; then export PIP_CERT=/run/secrets/ca_bundle; fi; \
    pip install --upgrade pip setuptools wheel \
 && pip install --require-hashes --no-deps -r requirements.lock

# ---------------------------------------------------------------------------
# Stage 3: Entwicklungs-Image (docker-compose.dev.yml) – Quellcode wird nach /app gemountet
# ---------------------------------------------------------------------------
FROM pydeps AS dev
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=secret,id=ca_bundle \
    if [ -f /run/secrets/ca_bundle ]; then export PIP_CERT=/run/secrets/ca_bundle; fi; \
    pip install --require-hashes --no-deps -r requirements-dev.lock
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    SM_ENV=development
WORKDIR /app
EXPOSE 8000
CMD ["uvicorn", "schulmanager.server.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app/schulmanager"]

# ---------------------------------------------------------------------------
# Hilfs-Stage: Quellbaum ohne Frontend-Quellen/Tests (tolerant gegenüber optionalen Pfaden
# wie alembic.ini oder migrations/ – der Build-Kontext ist per .dockerignore gefiltert)
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS source
COPY . /src
RUN rm -rf /src/frontend /src/deploy /src/tests \n && find /src/docs -mindepth 1 -maxdepth 1 ! -name hilfe -exec rm -rf {} + 2>/dev/null || true

# ---------------------------------------------------------------------------
# Stage 4: Laufzeit-Image
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime

ARG APP_VERSION=dev
ARG VCS_REF=unknown
ARG BUILD_DATE=unknown
LABEL org.opencontainers.image.title="Schulmanager" \
      org.opencontainers.image.description="Schulverwaltung mit Stundenplan-Generator und Live-Vertretungsplanung" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.licenses="NOASSERTION"

# tzdata (Europe/Berlin) und ca-certificates (SMTP/Webhooks/OIDC über TLS) bringt das
# python:*-slim-Basisimage bereits mit – kein apt nötig.
RUN groupadd --system --gid 10001 schulmanager \
 && useradd --system --uid 10001 --gid schulmanager --home-dir /app --no-create-home \
            --shell /usr/sbin/nologin schulmanager

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    TZ=Europe/Berlin \
    SM_ENV=production \
    SM_DATABASE_URL=sqlite:////app/data/schulmanager.db \
    SM_FRONTEND_DIST=/app/frontend/dist \
    SM_HOST=0.0.0.0 \
    SM_PORT=8000 \
    SM_WORKERS=1 \
    SM_APP_VERSION=${APP_VERSION}

WORKDIR /app
COPY --from=pydeps /opt/venv /opt/venv
COPY --from=source /src /app
COPY --from=frontend /build/frontend/dist /app/frontend/dist
COPY deploy/docker/entrypoint.sh /usr/local/bin/schulmanager-entrypoint

# Editable-Installation: Paket-Metadaten (Version, Entry-Points) im venv, Code bleibt unter /app
# (inkl. Nicht-Python-Dateien wie Alembic-Templates). Danach Bytecode vorkompilieren, da das
# Dateisystem im Betrieb schreibgeschützt sein darf (read_only in Compose).
RUN pip install --no-deps --no-build-isolation -e /app \
 && python -m compileall -q /app/schulmanager \
 && chmod 0755 /usr/local/bin/schulmanager-entrypoint /app/scripts/*.sh \
 && mkdir -p /app/data \
 && chown -R schulmanager:schulmanager /app/data

USER schulmanager:schulmanager
VOLUME ["/app/data"]
EXPOSE 8000

# Der erste Start mit SM_LOAD_DEMO=1 erzeugt einen kompletten Stundenplan → großzügige start-period.
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD ["/app/scripts/healthcheck.sh", "--quiet"]

ENTRYPOINT ["schulmanager-entrypoint"]
CMD ["serve"]

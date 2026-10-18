# Schulmanager – häufige Aufgaben
#
#   make help        Übersicht
#   make install     Entwicklungsumgebung einrichten (.venv + npm)
#   make dev         Backend + Frontend mit Hot-Reload
#   make up          Produktionsstack (Docker Compose) starten
#
# Variablen: COMPOSE="docker compose -f docker-compose.sqlite.yml", FILE=…, PYTHON=…

SHELL := /usr/bin/env bash
.SHELLFLAGS := -euo pipefail -c
.DEFAULT_GOAL := help

COMPOSE     ?= docker compose
COMPOSE_DEV ?= docker compose -f docker-compose.dev.yml
VENV        ?= .venv
PYTHON      ?= $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,python3)
NPM         ?= npm
IMAGE       ?= schulmanager:latest
VERSION     ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo dev)
SHELL_FILES := $(wildcard scripts/*.sh) deploy/docker/entrypoint.sh deploy/backup/backup-loop.sh

export DEV_UID := $(shell id -u)
export DEV_GID := $(shell id -g)

.PHONY: help lock audit install install-backend install-frontend dev dev-backend dev-frontend dev-docker \
        test test-backend test-frontend lint lint-backend lint-frontend lint-shell format typecheck \
        build build-frontend build-backup config up down restart ps logs shell \
        migrate create-admin demo demo-docker backup backup-list backup-verify restore restore-test \
        healthcheck monitoring-up uptime-up update caddy-ratelimit clean

help: ## Diese Übersicht
	@awk 'BEGIN {FS = ":.*?## "; printf "\nSchulmanager – make-Ziele\n\n"} \
	     /^[a-zA-Z0-9_-]+:.*?## / {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo

# ---------------------------------------------------------------------------
# Entwicklung
# ---------------------------------------------------------------------------
install: install-backend install-frontend ## Entwicklungsumgebung einrichten (Python-venv + npm)

lock: ## Python-Abhängigkeiten neu sperren (requirements*.lock mit Hashes, braucht uv)
	uv pip compile pyproject.toml --generate-hashes --universal --no-header -o requirements.lock
	uv pip compile pyproject.toml --extra dev --generate-hashes --universal --no-header -o requirements-dev.lock
	@for f in requirements.lock requirements-dev.lock; do \
	  sed -i '1i # Gesperrte Python-Abhängigkeiten MIT Hashes (S-14) – erzeugt mit: make lock  (uv pip compile --universal)\n# Nicht von Hand ändern; Änderungen an pyproject.toml → make lock, dann prüfen und einchecken.' $$f; done

audit: ## Python-Abhängigkeiten auf bekannte Schwachstellen prüfen (pip-audit)
	uvx pip-audit -r requirements-dev.lock --require-hashes --disable-pip

install-backend:
	@test -x $(VENV)/bin/python || python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install --require-hashes --no-deps -r requirements-dev.lock
	$(VENV)/bin/pip install --no-deps -e .

install-frontend:
	@if [ -f frontend/package-lock.json ]; then $(NPM) --prefix frontend ci; else $(NPM) --prefix frontend install; fi

dev: ## Backend (:8000) + Frontend (:5173) mit Hot-Reload, SQLite, Demo-Schule
	scripts/dev.sh

dev-backend: ## Nur Backend mit Reload
	scripts/dev.sh --backend-only

dev-frontend: ## Nur Vite-Dev-Server
	scripts/dev.sh --frontend-only

dev-docker: ## Entwicklungsumgebung komplett in Containern (docker-compose.dev.yml)
	$(COMPOSE_DEV) up --build

demo: ## Entwicklung mit frischer Datenbank und Demo-Schule starten
	SM_LOAD_DEMO=1 scripts/dev.sh --fresh

# ---------------------------------------------------------------------------
# Qualität
# ---------------------------------------------------------------------------
test: test-backend test-frontend ## Alle Tests (pytest + vitest)

test-backend: ## Python-Tests
	$(PYTHON) -m pytest -q

test-frontend: ## Frontend-Tests (vitest)
	$(NPM) --prefix frontend test --if-present

lint: lint-backend lint-frontend lint-shell ## Linter (ruff, tsc, shellcheck, compose config)

lint-backend:
	$(PYTHON) -m ruff check .

lint-frontend:
	$(NPM) --prefix frontend run lint --if-present

lint-shell:
	@if command -v shellcheck >/dev/null; then shellcheck $(SHELL_FILES); \
	 else echo "shellcheck nicht installiert – übersprungen (apt install shellcheck)"; fi
	@for f in $(SHELL_FILES); do bash -n "$$f"; done
	@if command -v docker >/dev/null; then \
	   SM_DOMAIN=example.org ACME_EMAIL=a@example.org SM_SECRET_KEY=x SM_ENCRYPTION_KEYS=x POSTGRES_PASSWORD=x \
	   $(COMPOSE) --env-file /dev/null config -q && echo "docker-compose.yml OK"; fi

typecheck: ## TypeScript-Typprüfung
	$(NPM) --prefix frontend run typecheck

format: ## Code formatieren (ruff format + ruff --fix)
	$(PYTHON) -m ruff format schulmanager tests
	$(PYTHON) -m ruff check --fix .

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
build: ## Docker-Image bauen (IMAGE=schulmanager:latest)
	docker build --build-arg APP_VERSION=$(VERSION) \
	  --build-arg VCS_REF=$$(git rev-parse --short HEAD 2>/dev/null || echo unknown) \
	  --build-arg BUILD_DATE=$$(date -u +%Y-%m-%dT%H:%M:%SZ) -t $(IMAGE) .

build-frontend: ## Nur das Frontend bauen (frontend/dist)
	$(NPM) --prefix frontend run build

build-backup: ## Backup-Sidecar-Image bauen
	docker build -f deploy/backup/Dockerfile -t schulmanager-backup:latest .

caddy-ratelimit: ## Caddy mit Rate-Limit-Plugin bauen (→ CADDY_IMAGE=schulmanager-caddy:latest)
	docker build -t schulmanager-caddy:latest deploy/caddy

# ---------------------------------------------------------------------------
# Betrieb (Docker Compose)
# ---------------------------------------------------------------------------
config: ## Compose-Konfiguration mit .env prüfen und anzeigen
	$(COMPOSE) config

up: ## Stack starten/aktualisieren (baut Images bei Bedarf)
	@test -f .env || { echo "Keine .env gefunden: cp .env.example .env und anpassen"; exit 1; }
	SM_VERSION=$(VERSION) $(COMPOSE) up -d --build --remove-orphans
	@$(COMPOSE) ps

down: ## Stack stoppen (Daten bleiben erhalten)
	$(COMPOSE) down

restart: ## App neu starten (lädt Daten neu aus der Datenbank)
	$(COMPOSE) restart app

ps: ## Status der Container
	$(COMPOSE) ps

logs: ## Logs verfolgen (SERVICE=app für einen Dienst)
	$(COMPOSE) logs -f --tail=200 $(SERVICE)

shell: ## Shell im App-Container
	$(COMPOSE) exec app bash

monitoring-up: ## Prometheus + Grafana starten (Profil monitoring)
	$(COMPOSE) --profile monitoring up -d

uptime-up: ## Uptime-Kuma starten (Profil uptime)
	$(COMPOSE) --profile uptime up -d

migrate: ## Datenbank-Migrationen (Docker; lokal: scripts/migrate.sh)
	@if $(COMPOSE) ps --status running --services 2>/dev/null | grep -qx app; then \
	   $(COMPOSE) exec -T app schulmanager-entrypoint migrate; \
	 else scripts/migrate.sh; fi

ADMIN ?= admin
create-admin: ## Admin-Konto anlegen (ADMIN=name; im Stack, falls er läuft)
	@if $(COMPOSE) ps --status running --services 2>/dev/null | grep -qx app; then \
	   scripts/create-admin.sh --compose -u "$(ADMIN)"; \
	 else scripts/create-admin.sh -u "$(ADMIN)"; fi

demo-docker: ## Demo-Schule in den laufenden Stack laden (überschreibt Planungsdaten!) und App neu starten
	$(COMPOSE) exec -T app python -m schulmanager.server.cli load-demo
	$(COMPOSE) restart app

healthcheck: ## /healthz prüfen (URL=https://plan.schule.de für extern)
	@if [ -n "$(URL)" ]; then scripts/healthcheck.sh "$(URL)"; \
	 else $(COMPOSE) exec -T app /app/scripts/healthcheck.sh; fi

update: ## Update: Backup, git pull, Images neu bauen, Neustart
	$(COMPOSE) exec -T backup backup.sh --label vor-update
	git pull --ff-only
	SM_VERSION=$$(git describe --tags --always 2>/dev/null || echo dev) $(COMPOSE) up -d --build --remove-orphans
	$(COMPOSE) exec -T app /app/scripts/healthcheck.sh --wait 240

# ---------------------------------------------------------------------------
# Backup & Restore
# ---------------------------------------------------------------------------
backup: ## Sofort-Backup (Docker: Sidecar; ohne Docker: scripts/backup.sh)
	@if $(COMPOSE) ps --status running --services 2>/dev/null | grep -qx backup; then \
	   $(COMPOSE) exec -T backup backup.sh --label manuell; \
	 else scripts/backup.sh --label manuell; fi

backup-list: ## Vorhandene Backups anzeigen
	@if $(COMPOSE) ps --status running --services 2>/dev/null | grep -qx backup; then \
	   $(COMPOSE) exec -T backup backup.sh --list; \
	 else scripts/backup.sh --list; fi

backup-verify: ## Backup-Datei prüfen (FILE=backups/daily/…)
	@test -n "$(FILE)" || { echo "Aufruf: make backup-verify FILE=backups/daily/<datei>"; exit 1; }
	scripts/backup.sh --verify "$(FILE)"

restore: ## Backup wiederherstellen (FILE=backups/daily/…) – mit Sicherheitsabfrage
	@test -n "$(FILE)" || { echo "Aufruf: make restore FILE=backups/daily/<datei>"; exit 1; }
	@if $(COMPOSE) ps --status running --services 2>/dev/null | grep -qx backup; then \
	   COMPOSE="$(COMPOSE)" scripts/restore.sh --compose "$(FILE)"; \
	 else scripts/restore.sh "$(FILE)"; fi

restore-test: ## Test-Restore in temporäre Datenbank (FILE=…, ändert nichts)
	@test -n "$(FILE)" || { echo "Aufruf: make restore-test FILE=backups/daily/<datei>"; exit 1; }
	@if $(COMPOSE) ps --status running --services 2>/dev/null | grep -qx backup; then \
	   $(COMPOSE) cp "$(FILE)" "backup:/tmp/$(notdir $(FILE))"; \
	   rc=0; $(COMPOSE) exec -T -e RESTORE_TEST_DB=schulmanager_restore_test backup \
	     restore.sh --test "/tmp/$(notdir $(FILE))" || rc=$$?; \
	   $(COMPOSE) exec -T backup rm -f "/tmp/$(notdir $(FILE))"; exit $$rc; \
	 else scripts/restore.sh --test "$(FILE)"; fi

# ---------------------------------------------------------------------------
clean: ## Build-Artefakte und Caches entfernen (keine Daten!)
	rm -rf frontend/dist .pytest_cache .ruff_cache
	find . -path ./frontend/node_modules -prune -o -name __pycache__ -type d -print -exec rm -rf {} + 2>/dev/null || true

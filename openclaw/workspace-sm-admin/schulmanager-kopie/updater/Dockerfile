# Schulpuls – Update-Agent (Begleitdienst neben der App)
#
# Bauen (aus dem Projektordner):
#   docker build -f updater/Dockerfile --build-arg VENDOR_PUBKEY="<öffentlicher Schlüssel des Anbieters, base64>" -t schulpuls-updater .
#
# Der öffentliche Anbieter-Schlüssel wird beim Bauen fest eingetragen (Schlüssel-Pinning) – der Agent installiert
# ausschließlich Releases, die damit signiert sind. Laufzeit: siehe docker-compose.yml (Profil "updater").
FROM docker:27-cli

ARG VENDOR_PUBKEY=""
RUN test -n "$VENDOR_PUBKEY" || (echo "FEHLER: --build-arg VENDOR_PUBKEY=... fehlt (öffentlicher Anbieter-Schlüssel)" >&2; exit 1)

RUN apk add --no-cache python3 py3-cryptography tini \
    && mkdir -p /etc/schulpuls /state /appdata \
    && printf '%s\n' "$VENDOR_PUBKEY" > /etc/schulpuls/vendor.pub

WORKDIR /opt/updater
COPY updater/__init__.py updater/__main__.py updater/agent.py updater/client.py updater/policy.py updater/runtime.py /opt/updater/updater/

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UPDATER_PUBKEY_FILE=/etc/schulpuls/vendor.pub
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["python3", "-m", "updater"]

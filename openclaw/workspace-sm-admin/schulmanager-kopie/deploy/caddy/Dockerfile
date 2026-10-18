# syntax=docker/dockerfile:1
#
# Optional: Caddy mit Rate-Limit-Plugin (github.com/mholt/caddy-ratelimit)
#   docker build -t schulmanager-caddy:latest deploy/caddy
#   → in .env: CADDY_IMAGE=schulmanager-caddy:latest
#   → deploy/caddy/conf.d/ratelimit.caddy.example nach ratelimit.caddy kopieren
ARG CADDY_VERSION=2.11
FROM caddy:${CADDY_VERSION}-builder-alpine AS builder
# Optional: CA-Bundle für TLS-inspizierende Proxys (--secret id=ca_bundle,src=…), landet nicht im Image
RUN --mount=type=secret,id=ca_bundle \
    if [ -f /run/secrets/ca_bundle ]; then export SSL_CERT_FILE=/run/secrets/ca_bundle; fi; \
    xcaddy build --with github.com/mholt/caddy-ratelimit

FROM caddy:${CADDY_VERSION}-alpine
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
RUN caddy list-modules | grep -q http.handlers.rate_limit

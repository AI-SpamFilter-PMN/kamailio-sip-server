#!/bin/sh

set -e

: "${HOST_IP:?HOST_IP must be set in .env or as an environment variable}"
: "${DATABASE_URL:?DATABASE_URL must be set in .env or as an environment variable}"

echo "=================================================="
echo "=== [ENTRYPOINT] Kamailio starting"
echo "=== [ENTRYPOINT] HOST_IP=${HOST_IP}"
echo "=== [ENTRYPOINT] DATABASE_URL is configured"
echo "=================================================="

KAMAILIO_DATABASE_URL="${DATABASE_URL}"

KAMAILIO_DATABASE_URL="$(printf '%s' "$KAMAILIO_DATABASE_URL" | sed 's/^postgresql:\/\//postgres:\/\//')"

echo "=== [ENTRYPOINT] PostgreSQL URL converted for Kamailio db_postgres ==="

sed \
    -e "s|__HOST_IP__|${HOST_IP}|g" \
    -e "s|__DATABASE_URL__|${KAMAILIO_DATABASE_URL}|g" \
    /etc/kamailio/kamailio.cfg.template \
    > /etc/kamailio/kamailio.cfg

echo "=== [ENTRYPOINT] kamailio.cfg generated ==="

echo "=== [ENTRYPOINT] Starting Kamailio ==="

exec kamailio -DD -E
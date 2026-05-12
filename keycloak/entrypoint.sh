#!/bin/bash
set -e

PGDATA="${PGDATA:-/var/lib/postgresql/data}"
KC_DB_NAME="${KC_DB_NAME:-keycloak}"

: "${KC_DB_USERNAME:?KC_DB_USERNAME is required}"
: "${KC_DB_PASSWORD:?KC_DB_PASSWORD is required}"
: "${KC_BOOTSTRAP_ADMIN_USERNAME:?KC_BOOTSTRAP_ADMIN_USERNAME is required}"
: "${KC_BOOTSTRAP_ADMIN_PASSWORD:?KC_BOOTSTRAP_ADMIN_PASSWORD is required}"

PG_BIN="/usr/lib/postgresql/$(ls /usr/lib/postgresql | sort -V | tail -1)/bin"

# Ensure correct ownership (handles stale volumes from a different postgres image)
install -d -m 0700 -o postgres -g postgres "$PGDATA"
chown -R postgres:postgres "$PGDATA"

# Initialize data directory on first run
if [ ! -f "$PGDATA/PG_VERSION" ]; then
    su -s /bin/bash postgres -c "$PG_BIN/initdb -D '$PGDATA' --no-locale --encoding=UTF8"
fi

# Start PostgreSQL, bound to localhost only
su -s /bin/bash postgres -c "$PG_BIN/postgres -D '$PGDATA' -h 127.0.0.1" &
PGPID=$!

echo "Waiting for PostgreSQL..."
until su -s /bin/bash postgres -c "$PG_BIN/pg_isready -h 127.0.0.1 -q" 2>/dev/null; do sleep 1; done
echo "PostgreSQL ready"

# Create Keycloak user and database (idempotent)
su -s /bin/bash postgres -c "$PG_BIN/psql -h 127.0.0.1 -tAc \"SELECT 1 FROM pg_roles WHERE rolname='$KC_DB_USERNAME'\" | grep -q 1 \
    || $PG_BIN/psql -h 127.0.0.1 -c \"CREATE USER \\\"$KC_DB_USERNAME\\\" WITH PASSWORD '$KC_DB_PASSWORD'\""
su -s /bin/bash postgres -c "$PG_BIN/psql -h 127.0.0.1 -tAc \"SELECT 1 FROM pg_database WHERE datname='$KC_DB_NAME'\" | grep -q 1 \
    || $PG_BIN/createdb -h 127.0.0.1 -O '$KC_DB_USERNAME' '$KC_DB_NAME'"

export KC_DB_URL="jdbc:postgresql://127.0.0.1:5432/$KC_DB_NAME"

# Start Keycloak in background
echo "Starting Keycloak..."
/opt/keycloak/bin/kc.sh start --optimized --import-realm &
KCPID=$!

trap 'kill $PGPID $KCPID 2>/dev/null' TERM INT

# Wait for Keycloak management port
echo "Waiting for Keycloak management port..."
until bash -c 'exec 3<>/dev/tcp/127.0.0.1/9000' 2>/dev/null; do sleep 2; done

# Set sslRequired=NONE on master realm (127.0.0.1 bypasses ssl_required check)
echo "Configuring master realm..."
until /opt/keycloak/bin/kcadm.sh config credentials \
    --server http://127.0.0.1:8080 --realm master \
    --user "$KC_BOOTSTRAP_ADMIN_USERNAME" \
    --password "$KC_BOOTSTRAP_ADMIN_PASSWORD" 2>/dev/null; do
    sleep 2
done
/opt/keycloak/bin/kcadm.sh update realms/master -s sslRequired=NONE
echo "Keycloak ready"

# Exit when either process dies
wait -n $PGPID $KCPID 2>/dev/null || true
kill $PGPID $KCPID 2>/dev/null
wait $PGPID $KCPID 2>/dev/null

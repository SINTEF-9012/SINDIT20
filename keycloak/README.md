# Keycloak

Keycloak 26 with a PostgreSQL backend, built for local development and production deployment.

## Prerequisites

- Docker and Docker Compose v2 (`docker compose version`)

## Local development

**1. Create your env file**

```bash
cp .env.example .env
```

The defaults in `.env.example` work out of the box for local use — no changes needed.

**2. Build and start**

```bash
docker compose --env-file .env -f docker-compose.keycloak.yaml up -d
```

> `docker-compose.keycloak.yaml` uses `start-dev` which disables SSL enforcement,
> allowing plain HTTP access from any IP. No reverse proxy needed for local use.

**3. Access**

| Service | URL |
|---|---|
| Keycloak admin console | http://localhost:8081 |
| Health endpoint | http://localhost:9000/health/ready (management port — internal only) |

Log in with the credentials set in `KC_BOOTSTRAP_ADMIN_USERNAME` / `KC_BOOTSTRAP_ADMIN_PASSWORD` (default: `sindit` / `sindit123`).

**4. Stop**

```bash
docker compose -f docker-compose.keycloak.yaml down
```

To also delete the database volume:

```bash
docker compose -f docker-compose.keycloak.yaml down -v
```

---

## Realm import

Any `.json` realm export placed in `./import/` is automatically imported on the **first** start (`--import-realm` flag). Re-importing requires wiping the database volume first.

---

## Production deployment

**1. Create and fill your env file**

```bash
cp .env.example .env
```

Update these values in `.env`:

| Variable | Description |
|---|---|
| `KC_DB_PASSWORD` | Strong random password |
| `KC_HOSTNAME` | Public HTTPS URL, e.g. `https://auth.example.com` |
| `KC_ADMIN_PASSWORD` | Strong random password — rotate after first login |
| `KC_HTTP_BIND` | Set to `127.0.0.1` (reverse proxy on same host) |

**2. Build and start**

```bash
docker compose --env-file .env -f docker-compose.keycloak.yaml up -d --build
```

**3. Reverse proxy**

Keycloak expects a reverse proxy (Nginx, Traefik, etc.) to terminate TLS and forward requests.
The proxy must send `X-Forwarded-Proto` and `X-Forwarded-Host` headers.

Minimal Nginx location block:

```nginx
location / {
    proxy_pass         http://127.0.0.1:8081;
    proxy_set_header   Host              $host;
    proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto $scheme;
    proxy_set_header   X-Forwarded-Host  $host;
}
```

---

## Useful commands

```bash
# Follow logs
docker compose -f docker-compose.keycloak.yaml logs -f keycloak

# Rebuild image after Dockerfile changes
docker compose --env-file .env -f docker-compose.keycloak.yaml up -d --build keycloak

# Open a shell inside the running container
docker compose -f docker-compose.keycloak.yaml exec keycloak bash
```

FROM quay.io/keycloak/keycloak:26.6 AS builder

ENV KC_DB=postgres
ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true
ENV KC_HTTP_ENABLED=true
ENV KC_PROXY_HEADERS=xforwarded
ENV KC_FEATURES=admin-fine-grained-authz:v1

WORKDIR /opt/keycloak
RUN /opt/keycloak/bin/kc.sh build

FROM ubuntu:24.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      openjdk-21-jre-headless \
      postgresql \
      bash \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/keycloak/ /opt/keycloak/

ENV PGDATA=/var/lib/postgresql/data
ENV KC_DB=postgres
ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true
ENV KC_HTTP_ENABLED=true
ENV KC_PROXY_HEADERS=xforwarded

COPY import/ /opt/keycloak/data/import/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080 9000

ENTRYPOINT ["/entrypoint.sh"]

FROM quay.io/keycloak/keycloak:26.3 as builder

# Enable health and metrics support
ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true
ENV KC_HTTP_ENABLED=true
ENV KC_PROXY_HEADER=xforwarded

# Configure a database vendor
ENV KC_DB=postgres

WORKDIR /opt/keycloak
# for demonstration purposes only, please make sure to use proper certificates in production instead
RUN keytool -genkeypair \
    -storepass password \
    -storetype PKCS12 \
    -keyalg RSA \
    -keysize 2048 \
    -dname "CN=localhost,OU=Development,O=SINDIT,L=Trondheim,ST=Trondelag,C=NO" \
    -alias server \
    -ext "SAN=DNS:localhost,DNS:keycloak,DNS:host.docker.internal,IP:127.0.0.1,IP:0.0.0.0" \
    -keystore conf/server.keystore \
    -validity 365
RUN /opt/keycloak/bin/kc.sh build

FROM quay.io/keycloak/keycloak:26.3
COPY --from=builder /opt/keycloak/ /opt/keycloak/

# change these values to point to a running postgres instance
ENV KC_DB=postgres
ENV KC_DB_URL=jdbc:postgresql://postgres_keycloak:5432/keycloak
ENV KC_DB_USERNAME=keycloak
ENV KC_DB_PASSWORD=keycloak123
ENV KC_HOSTNAME=localhost

ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true
ENV KC_HTTP_ENABLED=true
ENV KC_PROXY_HEADER=xforwarded

# Keycloak Admin User (ADD THESE LINES)
ENV KC_BOOTSTRAP_ADMIN_USERNAME="sindit"
ENV KC_BOOTSTRAP_ADMIN_PASSWORD="sindit123"

#RUN /opt/keycloak/bin/kc.sh bootstrap-admin user --username $KC_BOOTSTRAP_ADMIN_USERNAME --password:env KC_BOOTSTRAP_ADMIN_PASSWORD

ENTRYPOINT ["/opt/keycloak/bin/kc.sh", "start", "--optimized"]

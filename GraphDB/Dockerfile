# Stage 1: Build stage
FROM eclipse-temurin:21.0.5_11-jre AS build
# FROM eclipse-temurin:21.0.5_11-jdk-alpine AS build

# Build time arguments
ARG version=10.2.2

# Environment variables
ENV GRAPHDB_PARENT_DIR=/opt/graphdb
ENV GRAPHDB_HOME=${GRAPHDB_PARENT_DIR}/home
ENV GRAPHDB_INSTALL_DIR=${GRAPHDB_PARENT_DIR}/dist
ENV PATH=${GRAPHDB_INSTALL_DIR}/bin:$PATH
ENV JAVA_OPTS="-Xmx4g"


# Working directory
WORKDIR /tmp

# Install GraphDB & Import data
RUN apk add --no-cache bash curl util-linux procps net-tools busybox-extras wget less gcompat && \
    apk upgrade libssl3 libcrypto3 busybox && \
    curl -fsSL "https://maven.ontotext.com/repository/owlim-releases/com/ontotext/graphdb/graphdb/${version}/graphdb-${version}-dist.zip" > \
    graphdb-${version}.zip && \
    bash -c 'md5sum -c - <<<"$(curl -fsSL https://maven.ontotext.com/repository/owlim-releases/com/ontotext/graphdb/graphdb/${version}/graphdb-${version}-dist.zip.md5)  graphdb-${version}.zip"' && \
    mkdir -p ${GRAPHDB_PARENT_DIR} && \
    cd ${GRAPHDB_PARENT_DIR} && \
    unzip /tmp/graphdb-${version}.zip && \
    rm /tmp/graphdb-${version}.zip && \
    mv graphdb-${version} dist && \
    mkdir -p ${GRAPHDB_HOME} && \
    mkdir -p ${GRAPHDB_PARENT_DIR}/tmp

# Copy files
COPY repo-config.ttl ${GRAPHDB_PARENT_DIR}/
COPY graph_model ${GRAPHDB_PARENT_DIR}/graph_model
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# Make the entrypoint script executable
RUN chmod +x /usr/local/bin/entrypoint.sh

# Expose port
EXPOSE 7200

# Entrypoint
ENTRYPOINT ["entrypoint.sh"]

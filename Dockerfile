# Use an official Python runtime as a parent image
FROM python:3.11-slim AS build

# Set the working directory in the container
WORKDIR /app

# Install system dependencies and uv via pip
RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install --no-cache-dir uv \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (for better caching)
COPY pyproject.toml README.md /app/

# Create virtual environment and install dependencies
RUN uv venv /app/.venv \
    && uv pip install --python /app/.venv/bin/python -e .

# Now copy the application code
COPY src/sindit /app/sindit/

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Runtime stage (smaller image)
FROM python:3.11-slim

# Runtime environment variables
ENV APPNAME=SINDIT  \
    FAST_API_HOST='0.0.0.0' \
    FAST_API_PORT='9017' \
    GRAPHDB_HOST='localhost' \
    GRAPHDB_PORT='7200' \
    GRAPHDB_USERNAME='sindit20' \
    GRAPHDB_PASSWORD='sindit20' \
    GRPAPHDB_REPOSITORY='SINDIT' \
    LOG_LEVEL='DEBUG' \
    USE_HASHICORP_VAULT='False' \
    FSVAULT_PATH='/app/data/vault.properties' \
    DOCKER_ENV=True \
    USE_KEYCLOAK=False \
    KEYCLOAK_SERVER_URL="http://localhost:8080" \
    KEYCLOAK_REALM="sindit" \
    KEYCLOAK_CLIENT_ID="sindit" \
    KEYCLOAK_CLIENT_SECRET="your_client_secret_here" \
    USER_PATH='/app/data/user.json' \
    WORKSPACE_PATH='/app/data/workspace.json' \
    PYTHONPATH="/app:${PYTHONPATH}"

# Install only runtime dependencies (not gcc)
RUN apt-get update \
    && apt-get -y install libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from build stage
COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/sindit /app/sindit
COPY --from=build /usr/local/bin/docker-entrypoint.sh /usr/local/bin/
COPY --from=build /app/pyproject.toml /app/pyproject.toml

ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 9017

WORKDIR /app/sindit

# Use entrypoint script to initialize data directory
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Run run_sindit.py when the container launches
CMD ["python", "run_sindit.py"]

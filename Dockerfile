# Use an official Python runtime as a parent image
FROM python:3.11-slim AS build

# Environment variables for Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set the working directory in the container
WORKDIR /app

# Install system dependencies in one layer
RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install poetry==1.8.2 \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (for better caching)
COPY pyproject.toml poetry.lock* /app/

# Install dependencies only (cached if pyproject.toml doesn't change)
RUN poetry install --no-root --no-directory && rm -rf $POETRY_CACHE_DIR

# Now copy the application code (changes frequently, but deps are cached)
COPY src/sindit /app/sindit/

# Install the project itself
RUN poetry install --only-root

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

ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 9017

WORKDIR /app/sindit

# Use entrypoint script to initialize data directory
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Run run_sindit.py when the container launches
CMD ["python", "run_sindit.py"]

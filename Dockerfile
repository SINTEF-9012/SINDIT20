# Use an official Python runtime as a parent image
FROM python:3.11-slim AS build

# Environment variables
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
    FSVAULT_PATH='environment_and_configuration/vault.properties' \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

ENV DOCKER_ENV=True

# Keycloak configuration
ENV USE_KEYCLOAK=False
ENV KEYCLOAK_SERVER_URL="http://localhost:8080"
ENV KEYCLOAK_REALM="sindit"
ENV KEYCLOAK_CLIENT_ID="sindit"
ENV KEYCLOAK_CLIENT_SECRET="your_client_secret_here"

# InMemory authentication configuration
ENV USER_PATH='environment_and_configuration/user.json'
ENV WORKSPACE_PATH='environment_and_configuration/workspace.json'

# Set the working directory in the container
WORKDIR /app

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install poetry==1.8.2

# Copy the current directory contents into the container at /app
#COPY src/sindit/api /app/sindit/api
#COPY src/sindit/util /app/sindit/util
#COPY src/sindit/common /app/sindit/common
#COPY src/sindit/connectors /app/sindit/connectors
#COPY src/sindit/knowledge_graph /app/sindit/knowledge_graph
#COPY src/sindit/environment_and_configuration /app/sindit/environment_and_configuration
#COPY src/sindit/run_sindit.py src/sindit/initialize_kg_connectors.py src/sindit/initialize_vault.py /app/sindit/
COPY src/sindit /app/sindit/
COPY pyproject.toml /app/

# Install any needed packages specified in requirements.txt
RUN poetry install

# Expose port
EXPOSE 9017

WORKDIR /app/sindit
#Set PYTHONPATH to /app, so that sindit package can be found
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Run run_sindit.py when the container launches
CMD ["poetry", "run", "python", "run_sindit.py"]

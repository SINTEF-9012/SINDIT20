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

# Set the working directory in the container
WORKDIR /app

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install poetry==1.8.2

# Copy the current directory contents into the container at /app
COPY api /app/api
COPY util /app/util
COPY common /app/common
COPY connectors /app/connectors
COPY knowledge_graph /app/knowledge_graph
COPY environment_and_configuration /app/environment_and_configuration
COPY run_sindit.py pyproject.toml initialize_kg_connectors.py initialize_vault.py /app/

# Install any needed packages specified in requirements.txt
RUN poetry install

# Expose port
EXPOSE 9017

# Run run_sindit.py when the container launches
CMD ["poetry", "run", "python", "run_sindit.py"]

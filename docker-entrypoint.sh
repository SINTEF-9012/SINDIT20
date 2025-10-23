#!/bin/bash
set -e

# Create /app/data directory if it doesn't exist
mkdir -p /app/data

# Copy initial configuration files if they don't exist in the mounted volume
# and if the source file exists
if [ ! -f /app/data/user.json ] && [ -f /app/sindit/environment_and_configuration/user.json ]; then
    echo "Copying initial user.json to /app/data"
    cp /app/sindit/environment_and_configuration/user.json /app/data/user.json
fi

if [ ! -f /app/data/workspace.json ] && [ -f /app/sindit/environment_and_configuration/workspace.json ]; then
    echo "Copying initial workspace.json to /app/data"
    cp /app/sindit/environment_and_configuration/workspace.json /app/data/workspace.json
fi

if [ ! -f /app/data/vault.properties ] && [ -f /app/sindit/environment_and_configuration/vault.properties ]; then
    echo "Copying initial vault.properties to /app/data"
    cp /app/sindit/environment_and_configuration/vault.properties /app/data/vault.properties
fi

# Execute the main command
exec "$@"

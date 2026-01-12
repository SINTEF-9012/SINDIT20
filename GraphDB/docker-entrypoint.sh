#!/bin/bash
set -e

# Check if the data directory is empty (first run with volume mount)
if [ ! -d "/opt/graphdb/dist/data/repositories" ] || [ -z "$(ls -A /opt/graphdb/dist/data/repositories 2>/dev/null)" ]; then
    echo "Data directory is empty. Initializing with preloaded data..."
    cp -r /opt/graphdb/preload/data/* /opt/graphdb/dist/data/
    echo "Preloaded data copied successfully."
else
    echo "Data directory already contains data. Skipping initialization."
fi

# Start GraphDB
exec /opt/graphdb/dist/bin/graphdb "$@"

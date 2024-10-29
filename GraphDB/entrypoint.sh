#!/bin/bash

# Run importrdf
/opt/graphdb/dist/bin/importrdf -Dgraphdb.home=${GRAPHDB_HOME} preload --force --recursive -q ${GRAPHDB_PARENT_DIR}/tmp/ -c ${GRAPHDB_PARENT_DIR}/repo-config.ttl ${GRAPHDB_PARENT_DIR}/graph_model

# Start GraphDB server
/opt/graphdb/dist/bin/graphdb -Dgraphdb.home=${GRAPHDB_HOME}

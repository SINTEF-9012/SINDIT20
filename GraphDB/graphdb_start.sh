#! /bin/bash

export version=10.2.2
export GRAPHDB_PARENT_DIR=.
export GRAPHDB_HOME=${GRAPHDB_PARENT_DIR}/home
export GRAPHDB_INSTALL_DIR=${GRAPHDB_PARENT_DIR}/dist
export PATH=${GRAPHDB_INSTALL_DIR}/graphdb-${version}/bin:$PATH

graphdb -Dgraphdb.home=${GRAPHDB_HOME}

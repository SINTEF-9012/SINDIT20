#! /bin/bash

export version=10.2.2
export GRAPHDB_PARENT_DIR=.
export GRAPHDB_HOME=${GRAPHDB_PARENT_DIR}/home
export GRAPHDB_INSTALL_DIR=${GRAPHDB_PARENT_DIR}/dist
export PATH=${GRAPHDB_INSTALL_DIR}/graphdb-${version}/bin:$PATH

mkdir -p ${GRAPHDB_PARENT_DIR}/tmp

importrdf -Dgraphdb.home=${GRAPHDB_HOME} preload --force --recursive -q ${GRAPHDB_PARENT_DIR}/tmp/ -c ${GRAPHDB_PARENT_DIR}/repo-config.ttl  ${GRAPHDB_PARENT_DIR}/graph_model

rm -rf ${GRAPHDB_PARENT_DIR}/tmp
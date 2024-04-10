export version=10.2.2
export GRAPHDB_PARENT_DIR=.
export GRAPHDB_HOME=${GRAPHDB_PARENT_DIR}/home
export GRAPHDB_INSTALL_DIR=${GRAPHDB_PARENT_DIR}/dist
export PATH=${GRAPHDB_INSTALL_DIR}/graphdb-${version}/bin:$PATH

mkdir -p ${GRAPHDB_HOME}
mkdir -p ${GRAPHDB_INSTALL_DIR}

curl -fsSL "https://maven.ontotext.com/repository/owlim-releases/com/ontotext/graphdb/graphdb/${version}/graphdb-${version}-dist.zip" > graphdb-${version}.zip

unzip graphdb-${version}.zip -d ${GRAPHDB_INSTALL_DIR}
rm graphdb-${version}.zip
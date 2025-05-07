#!/bin/bash

# Config
export version=10.2.2
export GRAPHDB_PARENT_DIR=.
export INPUT_DIR=${GRAPHDB_PARENT_DIR}/graph_model
export GRAPHDB_URL=http://localhost:7200
export REPO_ID=SINDIT

# Upload RDF files (assumes Turtle format)
for file in "${INPUT_DIR}"/*.ttl; do
  if [[ -f "$file" ]]; then
    echo "Uploading $file to repository ${REPO_ID}..."
    curl -X POST \
      -H "Content-Type: text/turtle" \
      --data-binary @"$file" \
      "${GRAPHDB_URL}/repositories/${REPO_ID}/statements"
  fi
done


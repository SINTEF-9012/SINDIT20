import logging

import uvicorn

from common.semantic_knowledge_graph.GraphDBPersistenceService import (
    GraphDBPersistenceService,
)
from common.semantic_knowledge_graph.SemanticKGPersistenceService import (
    SemanticKGPersistenceService,
)
from common.vault.vault import FsVault, Vault
from knowledge_graph.kg_connector import SINDITKGConnector
from util.environment_and_configuration import (
    get_environment_variable,
    get_environment_variable_bool,
    get_environment_variable_int,
)
from util.log import logger

# from api.api import app

logger.setLevel(get_environment_variable("LOG_LEVEL", optional=True, default="INFO"))

kg_service: SemanticKGPersistenceService = GraphDBPersistenceService(
    get_environment_variable("GRAPHDB_HOST"),
    get_environment_variable("GRAPHDB_PORT"),
    get_environment_variable("GRPAPHDB_REPOSITORY"),
    get_environment_variable("GRAPHDB_USERNAME"),
    get_environment_variable("GRAPHDB_PASSWORD"),
)

sindit_kg_connector = SINDITKGConnector(kg_service)


use_hashicorp_vault = get_environment_variable_bool(
    "USE_HASHICORP_VAULT", optional=True, default="false"
)
if not use_hashicorp_vault:
    secret_vault: Vault = FsVault(get_environment_variable("FSVAULT_PATH"))
else:
    # setting up hashicorp vault
    pass


if __name__ == "__main__":
    logger.log(logging.INFO, "Starting SINDIT")

    # secret_vault:Vault = FsVault(get_environment_variable("VAULT_PATH"))

    # Run fast API
    logger.info("Running FastAPI...")
    uvicorn.run(
        "api.api:app",
        host=get_environment_variable("FAST_API_HOST"),
        port=get_environment_variable_int("FAST_API_PORT"),
        workers=1,
        access_log=True,
    )

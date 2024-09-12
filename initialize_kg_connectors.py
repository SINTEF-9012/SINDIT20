from common.semantic_knowledge_graph.GraphDBPersistenceService import (
    GraphDBPersistenceService,
)
from common.semantic_knowledge_graph.SemanticKGPersistenceService import (
    SemanticKGPersistenceService,
)
from knowledge_graph.kg_connector import SINDITKGConnector
from util.environment_and_configuration import (
    get_environment_variable,
)
from util.log import logger

logger.setLevel(get_environment_variable("LOG_LEVEL", optional=True, default="INFO"))

logger.info("Initializing kg connector from environment variables...")

kg_service: SemanticKGPersistenceService = GraphDBPersistenceService(
    get_environment_variable("GRAPHDB_HOST"),
    get_environment_variable("GRAPHDB_PORT"),
    get_environment_variable("GRPAPHDB_REPOSITORY"),
    get_environment_variable("GRAPHDB_USERNAME"),
    get_environment_variable("GRAPHDB_PASSWORD"),
)

sindit_kg_connector = SINDITKGConnector(kg_service)

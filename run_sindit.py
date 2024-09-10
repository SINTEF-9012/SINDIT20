import uvicorn
from util.environment_and_configuration import (
    get_environment_variable,
    get_environment_variable_int,
)
from util.log import logger

from api import kg_endpoints  # noqa: F401
from api import vault_endpoints  # noqa: F401
from api import connection_endpoints  # noqa: F401
from api import workspace_endpoints  # noqa: F401
from api import metamodel_endpoints  # noqa: F401


# from connectors.setup_connectors import initialize_connections_and_properties

# logger.info("Starting connections and properties...")
# initialize_connections_and_properties()

logger.info("Starting SINDIT")

# Run fast API
logger.info("Running FastAPI...")
uvicorn.run(
    "api.api:app",
    host=get_environment_variable("FAST_API_HOST"),
    port=get_environment_variable_int("FAST_API_PORT"),
    workers=1,
    access_log=True,
)

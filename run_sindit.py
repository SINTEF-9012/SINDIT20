from dotenv import load_dotenv

load_dotenv("./environment_and_configuration/dev_environment_backend.env")

import uvicorn  # noqa: E402
from util.environment_and_configuration import (  # noqa: E402
    get_environment_variable,
    get_environment_variable_int,
)  # noqa: E402
from util.log import logger  # noqa: E402

from api import kg_endpoints  # noqa: F401, E402
from api import vault_endpoints  # noqa: F401, E402
from api import connection_endpoints  # noqa: F401, E402
from api import workspace_endpoints  # noqa: F401, E402
from api import metamodel_endpoints  # noqa: F401, E402


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

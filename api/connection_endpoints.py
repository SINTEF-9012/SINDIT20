from connectors.setup_connectors import initialize_connections_and_properties

from util.log import logger
from api.api import app


@app.get(
    "/connection/refresh",
    tags=["Connection"],
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Connections and properties refreshed",
                    }
                }
            },
        }
    },
)
async def refresh_connections_and_properties():
    """
    Refresh connections and properties.
    """
    initialize_connections_and_properties(replace=False)
    logger.info("Connections and properties refreshed")

    return {"message": "Connections and properties refreshed"}

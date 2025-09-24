from sindit.connectors.setup_connectors import initialize_connections_and_properties

from sindit.util.log import logger
from sindit.api.api import app
from sindit.api.authentication_endpoints import User, get_current_active_user
from fastapi import Depends


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
async def refresh_connections_and_properties(
    current_user: User = Depends(get_current_active_user),
):
    """
    Refresh connections and properties.
    """
    initialize_connections_and_properties(replace=False)
    logger.info("Connections and properties refreshed")

    return {"message": "Connections and properties refreshed"}

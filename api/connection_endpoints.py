from connectors.setup_connectors import initialize_connections_and_properties

from util.log import logger
from api.api import app

@app.get("/connection/refresh", tags=["Connection"])
async def refresh_connections_and_properties():
    """
    Refresh connections and properties.
    """
    initialize_connections_and_properties()
    logger.info("Connections and properties refreshed")
    
    return {"message": "Connections and properties refreshed"}
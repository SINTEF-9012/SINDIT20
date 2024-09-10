from fastapi import HTTPException
from initialize_kg_connectors import sindit_kg_connector

from util.log import logger

from api.api import app


@app.post(
    "/metamodel/search_unit",
    tags=["Metamodel"],
)
async def search_unit(search_term: str):
    """
    Search for a unit in the meta-model based on a string.
    """
    try:
        return sindit_kg_connector.search_unit(search_term)
    except Exception as e:
        logger.error(f"Error searching for unit: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@app.get(
    "/metamodel/get_all_units",
    tags=["Metamodel"],
)
async def get_all_units():
    """
    Get all units in the meta-model.
    Warning: This can be a large response.
    """
    try:
        return sindit_kg_connector.get_all_units()
    except Exception as e:
        logger.error(f"Error getting all units: {e}")
        raise HTTPException(status_code=404, detail=str(e))

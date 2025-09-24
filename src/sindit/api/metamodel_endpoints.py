from fastapi import HTTPException
from sindit.initialize_kg_connectors import sindit_kg_connector

from sindit.util.log import logger

from sindit.api.api import app


@app.get(
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
    "/metamodel/unit",
    tags=["Metamodel"],
)
async def get_unit_by_uri(uri: str):
    """
    Get a unit in the meta-model based on its URI.
    """
    try:
        return sindit_kg_connector.get_unit_by_uri(uri)
    except Exception as e:
        logger.error(f"Error getting unit by URI: {e}")
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


@app.get(
    "/metamodel/get_data_type",
    tags=["Metamodel"],
)
async def get_all_data_type():
    """
    Get all data types in the meta-model.
    """
    try:
        return sindit_kg_connector.get_all_data_types()
    except Exception as e:
        logger.error(f"Error getting all data types: {e}")
        raise HTTPException(status_code=404, detail=str(e))

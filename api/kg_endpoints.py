from typing import Union

from api.api import app
from knowledge_graph.graph_model import (
    SINDITKG,
    AbstractAsset,
    AbstractAssetProperty,
    Connection,
    DatabaseProperty,
    File,
    StreamingProperty,
    TimeseriesProperty,
)
from run_sindit import sindit_kg_connector
from util.log import logger


@app.get(
    "/kg/node",
    tags=["Knowledge Graph"],
    response_model_exclude_none=True,
    response_model=Union[
        AbstractAsset,
        SINDITKG,
        Connection,
        AbstractAssetProperty,
        DatabaseProperty,
        StreamingProperty,
        TimeseriesProperty,
        File,
    ],
)
async def get_node(
    node_uri: str,
    depth: int = 1,
):
    """
    Get a node from the knowledge graph by its URI.
    """
    try:
        return sindit_kg_connector.load_node_by_uri(node_uri, depth=depth)
    except Exception as e:
        logger.error(f"Error getting node by URI {node_uri}: {e}")
        return {"error": str(e)}


@app.delete("/kg/node", tags=["Knowledge Graph"])
async def delete_node(node_uri: str) -> dict:
    """
    Delete a node from the knowledge graph by its URI.
    """
    try:
        result = sindit_kg_connector.delete_node(node_uri)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error deleting node by URI {node_uri}: {e}")
        return {"error": str(e)}


# SINDITKG
@app.post("kg/sindit_kg", tags=["Knowledge Graph"])
async def save_sindit_kg(node: SINDITKG) -> dict:
    """
    Create or save a SINDITKG node to the knowledge graph.
    """
    try:
        return sindit_kg_connector.save_node(node)

    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        return {"error": str(e)}


@app.post("kg/asset", tags=["Knowledge Graph"])
async def save_asset(node: AbstractAsset) -> dict:
    """
    Create or save an abstract asset node to the knowledge graph.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        return {"error": str(e)}


@app.post("/kg/connection", tags=["Knowledge Graph"])
async def save_connection(node: Connection) -> dict:
    """
    Create or save a connection node to the knowledge graph.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        return {"error": str(e)}


# AbstractAssetProperty
@app.post("kg/asset_property", tags=["Knowledge Graph"])
async def save_asset_property(node: AbstractAssetProperty) -> dict:
    """
    Create or save an abstract asset property node to the knowledge graph.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        return {"error": str(e)}


# DatabaseProperty
@app.post("kg/database_property", tags=["Knowledge Graph"])
async def save_database_property(node: DatabaseProperty) -> dict:
    """
    Create or save a database property node to the knowledge graph.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        return {"error": str(e)}


# StreamingProperty
@app.post("kg/streaming_property", tags=["Knowledge Graph"])
async def save_streaming_property(node: StreamingProperty) -> dict:
    """
    Create or save a streaming property node to the knowledge graph.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        return {"error": str(e)}


# TimeseriesProperty
@app.post("kg/timeseries_property", tags=["Knowledge Graph"])
async def save_timeseries_property(node: TimeseriesProperty) -> dict:
    """
    Create or save a timeseries property node to the knowledge graph.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        return {"error": str(e)}


# File
@app.post("kg/file", tags=["Knowledge Graph"])
async def save_file(node: File) -> dict:
    """
    Create or save a file node to the knowledge graph.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        return {"error": str(e)}

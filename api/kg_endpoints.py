from typing import Union, List

from fastapi import HTTPException
from initialize_connectors import update_connection_node, update_propery_node
from initialize_kg_connectors import sindit_kg_connector
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
from util.log import logger

from api.api import app


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
        raise HTTPException(status_code=404, detail=str(e))


@app.get(
    "/kg/nodes_by_class",
    tags=["Knowledge Graph"],
    response_model_exclude_none=True,
    response_model=List[
        Union[
            AbstractAsset,
            SINDITKG,
            Connection,
            AbstractAssetProperty,
            DatabaseProperty,
            StreamingProperty,
            TimeseriesProperty,
            File,
        ]
    ],
)
async def get_nodes_by_class(
    node_class: str,
    depth: int = 1,
):
    """
    Get a node from the knowledge graph by its class.
    """
    try:
        return sindit_kg_connector.load_nodes_by_class(node_class, depth=depth)
    except Exception as e:
        logger.error(f"Error getting node by class {node_class}: {e}")
        raise HTTPException(status_code=404, detail=str(e))


# get all nodes
@app.get(
    "/kg/nodes",
    tags=["Knowledge Graph"],
    response_model_exclude_none=True,
    response_model=List[
        Union[
            AbstractAsset,
            SINDITKG,
            Connection,
            AbstractAssetProperty,
            DatabaseProperty,
            StreamingProperty,
            TimeseriesProperty,
            File,
        ]
    ],
)
async def get_nodes():
    """
    Get all nodes from the knowledge graph.
    """
    try:
        return sindit_kg_connector.load_all_nodes()
    except Exception as e:
        logger.error(f"Error getting all nodes: {e}")
        raise HTTPException(status_code=404, detail=str(e))


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
        raise HTTPException(status_code=404, detail=str(e))


# SINDITKG
@app.post("/kg/sindit_kg", tags=["Knowledge Graph"])
async def save_sindit_kg(node: SINDITKG) -> dict:
    """
    Create or save a SINDITKG node to the knowledge graph.
    """
    try:
        return sindit_kg_connector.save_node(node)

    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/kg/asset", tags=["Knowledge Graph"])
async def save_asset(node: AbstractAsset) -> dict:
    """
    Create or save an abstract asset node to the knowledge graph.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/kg/connection", tags=["Knowledge Graph"])
async def save_connection(node: Connection) -> dict:
    """
    Create or save a connection node to the knowledge graph.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        if result:
            update_connection_node(node)
            
        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AbstractAssetProperty
@app.post("/kg/asset_property", tags=["Knowledge Graph"])
async def save_asset_property(node: AbstractAssetProperty) -> dict:
    """
    Create or save an abstract asset property node to the knowledge graph.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        
        if result:
            update_propery_node(node)
            
        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# DatabaseProperty
@app.post("/kg/database_property", tags=["Knowledge Graph"])
async def save_database_property(node: DatabaseProperty) -> dict:
    """
    Create or save a database property node to the knowledge graph.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# StreamingProperty
@app.post("/kg/streaming_property", tags=["Knowledge Graph"])
async def save_streaming_property(node: StreamingProperty) -> dict:
    """
    Create or save a streaming property node to the knowledge graph.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        
        if result:
            update_propery_node(node)
            
        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# TimeseriesProperty
@app.post("/kg/timeseries_property", tags=["Knowledge Graph"])
async def save_timeseries_property(node: TimeseriesProperty) -> dict:
    """
    Create or save a timeseries property node to the knowledge graph.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# File
@app.post("/kg/file", tags=["Knowledge Graph"])
async def save_file(node: File) -> dict:
    """
    Create or save a file node to the knowledge graph.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

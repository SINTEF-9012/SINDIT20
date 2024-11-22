import asyncio
from typing import Union, List
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from initialize_kg_connectors import sindit_kg_connector
from connectors.setup_connectors import (
    remove_connection_node,
    remove_property_node,
    update_connection_node,
    update_propery_node,
)

from knowledge_graph.graph_model import (
    SINDITKG,
    AbstractAsset,
    AbstractAssetProperty,
    Connection,
    DatabaseProperty,
    File,
    S3ObjectProperty,
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
        S3ObjectProperty,
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
            S3ObjectProperty,
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
            S3ObjectProperty,
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
        node = sindit_kg_connector.load_node_by_uri(node_uri)

        result = sindit_kg_connector.delete_node(node_uri)

        if result and node is not None:
            if isinstance(node, Connection):
                remove_connection_node(node)
            elif isinstance(node, AbstractAssetProperty):
                remove_property_node(node)

        return {"result": result}
    except Exception as e:
        logger.error(f"Error deleting node by URI {node_uri}: {e}")
        raise HTTPException(status_code=404, detail=str(e))


# SINDITKG
@app.post("/kg/sindit_kg", tags=["Knowledge Graph"])
async def create_sindit_kg(node: SINDITKG) -> dict:
    """
    Create or save a SINDITKG node to the knowledge graph.

    **Important**: All existing information related to this node will be
    completely removed before adding the new node.

    If you want to update a node without removing all its old information,
    use the update node endpoint instead.
    """
    try:
        return sindit_kg_connector.save_node(node)

    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/kg/asset", tags=["Knowledge Graph"])
async def create_asset(node: AbstractAsset) -> dict:
    """
    Create or save an abstract asset node to the knowledge graph.

    **Important**: All existing information related to this node will be
    completely removed before adding the new node.

    If you want to update a node without removing all its old information,
    use the update node endpoint instead.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/kg/connection", tags=["Knowledge Graph"])
async def create_connection(node: Connection) -> dict:
    """
    Create or save a connection node to the knowledge graph.

    **Important**: All existing information related to this node will be
    completely removed before adding the new node.

    If you want to update a node without removing all its old information,
    use the update node endpoint instead.
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
async def create_asset_property(node: AbstractAssetProperty) -> dict:
    """
    Create or save an abstract asset property node to the knowledge graph.

    **Important**: All existing information related to this node will be
    completely removed before adding the new node.

    If you want to update a node without removing all its old information,
    use the update node endpoint instead.
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
async def create_database_property(node: DatabaseProperty) -> dict:
    """
    Create or save a database property node to the knowledge graph.

    **Important**: All existing information related to this node will be
    completely removed before adding the new node.

    If you want to update a node without removing all its old information,
    use the update node endpoint instead.
    """
    try:
        result = sindit_kg_connector.save_node(node)

        if result:
            update_propery_node(node)

        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# StreamingProperty
@app.post("/kg/streaming_property", tags=["Knowledge Graph"])
async def create_streaming_property(node: StreamingProperty) -> dict:
    """
    Create or save a streaming property node to the knowledge graph.

    **Important**: All existing information related to this node will be
    completely removed before adding the new node.

    If you want to update a node without removing all its old information,
    use the update node endpoint instead.
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
async def create_timeseries_property(node: TimeseriesProperty) -> dict:
    """
    Create or save a timeseries property node to the knowledge graph.

    **Important**: All existing information related to this node will be
    completely removed before adding the new node.

    If you want to update a node without removing all its old information,
    use the update node endpoint instead.
    """
    try:
        result = sindit_kg_connector.save_node(node)

        if result:
            update_propery_node(node)

        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# File
@app.post("/kg/file", tags=["Knowledge Graph"])
async def create_file(node: File) -> dict:
    """
    Create or save a file node to the knowledge graph.

    **Important**: All existing information related to this node will be
    completely removed before adding the new node.

    If you want to update a node without removing all its old information,
    use the update node endpoint instead.
    """
    try:
        result = sindit_kg_connector.save_node(node)

        if result:
            update_propery_node(node)

        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# S3 File object
@app.post("/kg/s3_object", tags=["Knowledge Graph"])
async def create_s3_object(node: S3ObjectProperty) -> dict:
    """
    Create or save a S3 object node to the knowledge graph.

    TODO: Add more details on how to use this endpoint.
    """
    try:
        result = sindit_kg_connector.save_node(node)

        if result:
            update_propery_node(node)

        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/kg/node", tags=["Knowledge Graph"])
async def update_node(node: dict, overwrite: bool = True) -> dict:
    """
    Updates a node in the knowledge graph.

    - If `overwrite` is `True`, existing information will be replaced.
    - If `overwrite` is `False`, new information will be added without
      overwriting existing data.

    **Note**: To create new nodes, use the "create node" endpoints instead.

    **Examples**:

    1. **Overwrite existing properties** (e.g., label and description):

    ```json
    {
        "uri": "http://example.org/node",
        "label": "New label",
        "assetDescription": "New description"
    }
    ```

    2. **Add new properties without overwriting** (e.g., adding a property to an asset):

    ```json
    {
        "uri": "http://example.org/node",
        "assetProperties": [
            {
                "uri": "http://example.org/property"
            }
        ]
    }
    ```
    """
    try:
        result = sindit_kg_connector.update_node(node, overwrite=overwrite)
        if result:
            return {"result": result}
    except Exception as e:
        logger.error(f"Error updating node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_streaming_property(node_uri: str, refresh_rate: int = 5):
    if refresh_rate < 1:
        refresh_rate = 1

    pre_timestamp = None

    while True:
        node = sindit_kg_connector.load_node_by_uri(node_uri)

        cur_timestamp = node.propertyValueTimestamp

        if cur_timestamp != pre_timestamp:
            yield node.model_dump_json(indent=4) + "\n"
            pre_timestamp = cur_timestamp

        await asyncio.sleep(refresh_rate)


@app.get("/kg/stream", tags=["Knowledge Graph"])
async def stream_property(node_uri: str, refresh_rate: int = 5):
    """
    Streams updates from a streaming or timeseries property node in the knowledge
    graph.

    This endpoint enters an **infinite loop**, continuously checking for updates
    from a specified node (either a StreamingProperty or TimeseriesProperty) and
    streaming new data to the client in real time.

    **Important**: The client must handle this continuous stream of data, as the
    loop will not terminate unless the connection is closed by the client or a
    server error occurs. Each new chunk of data is sent whenever the node's
    `propertyValueTimestamp` is updated.

    Parameters:
    - node_uri (str): The URI of the node to stream. Must refer to a
      StreamingProperty or TimeseriesProperty.
    - refresh_rate (int): The interval in seconds at which the node's state is
      checked for updates. Defaults to 5 seconds, with a minimum refresh rate of
      1 second.

    Response:
    - A JSON stream of updates from the node. Each update is sent as a new chunk
      of JSON data whenever the node's `propertyValueTimestamp` changes.

    Example:
    - To stream updates from a node with a URI of "http://example.org/node", send
      a GET request to:
      `/kg/stream?node_uri=http://example.org/node&refresh_rate=5`
    - Curl example:
       ```
      curl -X 'GET' \
      'http://localhost:9017/kg/stream?node_uri=http://example.org/node' \
      -H 'accept: application/json'
      ```
    """
    try:
        # Perform a pre-check to verify if the node exists
        # and is valid before starting the streaming response.
        node = sindit_kg_connector.load_node_by_uri(node_uri)
        if not isinstance(node, StreamingProperty) and not isinstance(
            node, TimeseriesProperty
        ):
            raise ValueError(
                f"Node {node_uri} is not a streaming or timeseries property"
            )

        # If the pre-check passes, then start the streaming response
        return StreamingResponse(
            get_streaming_property(node_uri=node_uri, refresh_rate=refresh_rate),
            media_type="application/json",
        )

    except Exception as e:
        logger.error(f"Error streaming node {node_uri}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error streaming node {node_uri}: {e}"
        )

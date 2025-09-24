import asyncio
from typing import Union, List
from fastapi import HTTPException, Depends
from fastapi.responses import StreamingResponse
from sindit.api.authentication_endpoints import User, get_current_active_user
from sindit.initialize_kg_connectors import sindit_kg_connector
from sindit.connectors.setup_connectors import (
    remove_connection_node,
    remove_property_node,
    update_connection_node,
    update_propery_node,
)

from sindit.knowledge_graph.graph_model import (
    SINDITKG,
    AbstractAsset,
    AbstractAssetProperty,
    Connection,
    DatabaseProperty,
    File,
    S3ObjectProperty,
    StreamingProperty,
    TimeseriesProperty,
    PropertyCollection,
)
from sindit.util.log import logger

from sindit.api.api import app


@app.get("/kg/node_types", tags=["Knowledge Graph"])
async def get_all_node_types(
    current_user: User = Depends(get_current_active_user),
) -> list:
    """
    Get all node types.
    """
    try:
        return sindit_kg_connector.get_node_types()
    except Exception as e:
        logger.error(f"Error getting node types: {e}")
        raise HTTPException(status_code=404, detail=str(e))


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
        PropertyCollection,
    ],
)
async def get_node_by_uri(
    node_uri: str, depth: int = 1, current_user: User = Depends(get_current_active_user)
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
    "/kg/nodes_by_type",
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
            PropertyCollection,
        ]
    ],
)
async def get_nodes_by_type(
    type_uri: str,
    depth: int = 1,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a node from the knowledge graph by its type.
    To get type uri, use the `/kg/node_types` endpoint.
    """
    try:
        return sindit_kg_connector.load_nodes_by_class(type_uri, depth=depth)
    except Exception as e:
        logger.error(f"Error getting node by type {type_uri}: {e}")
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
            PropertyCollection,
        ]
    ],
)
async def get_all_nodes(current_user: User = Depends(get_current_active_user)):
    """
    Get all nodes from the knowledge graph.
    """
    try:
        return sindit_kg_connector.load_all_nodes()
    except Exception as e:
        logger.error(f"Error getting all nodes: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/kg/node", tags=["Knowledge Graph"])
async def delete_node(
    node_uri: str, current_user: User = Depends(get_current_active_user)
) -> dict:
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
async def create_sindit_kg(
    node: SINDITKG, current_user: User = Depends(get_current_active_user)
) -> dict:
    """
    Create or save a SINDITKG node to the knowledge graph.

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


@app.post("/kg/asset", tags=["Knowledge Graph"])
async def create_asset(
    node: AbstractAsset, current_user: User = Depends(get_current_active_user)
) -> dict:
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
async def create_connection(
    node: Connection, current_user: User = Depends(get_current_active_user)
) -> dict:
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
async def create_asset_property(
    node: AbstractAssetProperty, current_user: User = Depends(get_current_active_user)
) -> dict:
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
async def create_database_property(
    node: DatabaseProperty, current_user: User = Depends(get_current_active_user)
) -> dict:
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
async def create_streaming_property(
    node: StreamingProperty, current_user: User = Depends(get_current_active_user)
) -> dict:
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
async def create_timeseries_property(
    node: TimeseriesProperty, current_user: User = Depends(get_current_active_user)
) -> dict:
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
@app.post("/kg/file", tags=["Knowledge Graph"], deprecated=True)
async def create_file(
    node: File, current_user: User = Depends(get_current_active_user)
) -> dict:
    """
    Create or save a file node to the knowledge graph.

    **Important**: All existing information related to this node will be
    completely removed before adding the new node.

    If you want to update a node without removing all its old information,
    use the update node endpoint instead.

    **Deprecated**: This API is deprecated and may be removed in future versions.
    Use S3ObjectProperty instead.
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
async def create_s3_object(
    node: S3ObjectProperty, current_user: User = Depends(get_current_active_user)
) -> dict:
    """
    Create new or add existing S3 object node to the knowledge graph.

    Adding an existing S3 object to the knowledge graph will create
    a download url for the object. Query the node to get the download url.

    Adding a key that does not exist in the S3 bucket will generate
    a json-object that can be used to upload the object.
    Query the node to get the json-object with the upload url.
    """
    try:
        result = sindit_kg_connector.save_node(node)

        if result:
            update_propery_node(node)

        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/kg/property_collection", tags=["Knowledge Graph"])
async def create_property_collection(
    node: PropertyCollection, current_user: User = Depends(get_current_active_user)
) -> dict:
    """
    Create or save a property collection node to the knowledge graph.

    **Important**: All existing information related to this node will be
    completely removed before adding the new node.

    If you want to update a node without removing all its old information,
    use the update node endpoint instead.
    """
    try:
        result = sindit_kg_connector.save_node(node)

        if result:
            for prop in node.collectionProperties:
                if isinstance(prop, AbstractAssetProperty):
                    update_propery_node(prop)

        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/kg/node", tags=["Knowledge Graph"])
async def update_node(
    node: dict,
    overwrite: bool = True,
    current_user: User = Depends(get_current_active_user),
) -> dict:
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


async def get_streaming_property(
    node_uri: str,
    refresh_rate: int = 5,
    current_user: User = Depends(get_current_active_user),
):
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
async def stream_property(
    node_uri: str,
    refresh_rate: int = 5,
    current_user: User = Depends(get_current_active_user),
):
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


@app.get(
    "/kg/advanced_search_node",
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
            PropertyCollection,
        ]
    ],
)
async def advanced_search_node(
    type_uri: str = None,
    attribute: str = None,
    attribute_value: str = None,
    is_value_uri: bool = False,
    filtering_condition: str = None,
    current_user: User = Depends(get_current_active_user),
):
    """
    Advanced search for nodes in the knowledge graph.

    This endpoint allows you to search for nodes based on their type and
    specific attributes. You can filter nodes by their type and one or more
    attributes.

    Parameters:
    - type_uri (str): The type of the node to search for. This is optinal.
    - attribute (str): The attribute name of the node to search for. This is optional
    - attribute_value (str): The value of the attribute to search
      for. This can be a string or a URI. For numbere, try to indicate the
      type of the number (e.g., "int", "float", etc.) in the value.
      Example: `"7.847"^^xsd:float`
    - is_value_uri (bool): If `True`, the `attribute_value` is treated as a URI.
      If `False`, it is treated as a string. Defaults to `False`.
    - filtering_condition (str): Optional filtering condition to apply to the
      search. For example, you can use SPARQL-like syntax to filter results based on
      specific criteria.
      Example:
      - `"?value > 10"` to filter nodes with values greater than 10.
      - `CONTAINS(STR(?value), "Temp")` to filter nodes with values  containing "Temp".

    Response:
    - A list of nodes that match the specified criteria.
    """
    try:
        return sindit_kg_connector.find_node_by_attribute(
            type_uri=type_uri,
            attribute_uri=attribute,
            attribute_value=attribute_value,
            is_value_uri=is_value_uri,
            filtering_condition=filtering_condition,
        )
    except Exception as e:
        logger.error(f"Error searching node: {e}")
        raise HTTPException(status_code=500, detail=str(e))

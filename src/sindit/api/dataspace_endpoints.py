from typing import List, Optional
from fastapi import HTTPException, Depends
from pydantic import BaseModel, Field
from sindit.initialize_kg_connectors import sindit_kg_connector
from sindit.api.authentication_endpoints import User, get_current_active_user
from sindit.dataspace.setup_dataspace import (
    dataspace_connectors,
    remove_dataspace_node,
    update_dataspace_node,
)
from sindit.common.semantic_knowledge_graph.rdf_model import URIRefNode

from sindit.knowledge_graph.dataspace_model import DataspaceManagement
from sindit.util.log import logger

from sindit.api.api import app


class DataspacePublishRequest(BaseModel):
    node_uris: List[str]


class DataspaceManagementInput(BaseModel):
    """Public request schema for ``POST /dataspace/management``.

    Mirrors the user-settable subset of :class:`DataspaceManagement` and
    intentionally excludes:

    - ``sinditServiceUser``: derived from the calling user's JWT so the
      EDC data plane cannot be made to impersonate an arbitrary user just
      by tweaking a request body.
    - ``isActive``: system-maintained status mirror of EDC reachability.
    - ``dataspaceAssets``: managed via ``/dataspace/publish`` and
      ``/dataspace/sync``.
    """

    uri: Optional[str] = Field(
        default=None,
        description=(
            "Stable URI of the DataspaceManagement node. Pass the same value "
            "on subsequent POSTs to update an existing node; omit to let the "
            "KG layer assign one."
        ),
    )
    endpoint: Optional[str] = Field(
        default=None,
        description="EDC Management API base URL, e.g. http://localhost:19193/management",
    )
    authenticationType: Optional[str] = Field(
        default=None, description="e.g. 'tokenbased'"
    )
    authenticationKeyPath: Optional[str] = Field(
        default=None,
        description="Vault path of the EDC Management API key used by SINDIT to call the EDC.",
    )
    dataspaceDescription: Optional[str] = None
    sinditApiBaseUrl: Optional[str] = Field(
        default=None,
        description=(
            "Public URL of the SINDIT API as seen from the EDC data plane "
            "(e.g. http://host.docker.internal:9017 when SINDIT runs on the "
            "docker host and the EDC runs in a container)."
        ),
    )

    def to_node(self, *, service_user: str) -> DataspaceManagement:
        """Materialize a :class:`DataspaceManagement` with server-set fields."""
        data = self.model_dump(exclude_none=True)
        # ``sinditServiceUser`` is *always* set by the server here; if a
        # client somehow submitted one in an extra field, Pydantic's
        # default ``ignore`` extra policy already discarded it.
        data["sinditServiceUser"] = service_user
        return DataspaceManagement(**data)


def _get_dataspace_node_or_404(uri: str) -> DataspaceManagement:
    # ``DataspaceManagement`` is not part of ``NodeURIClassMapping``
    # (which is what ``load_node_by_uri`` uses by default), so we go through
    # the dedicated dataspace loader that wires the right ``uri_class_mapping``.
    try:
        node = sindit_kg_connector.get_dataspace_node_by_uri(uri)
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"DataspaceManagement node {uri} not found: {e}",
        )
    if not isinstance(node, DataspaceManagement):
        raise HTTPException(
            status_code=404, detail=f"DataspaceManagement node {uri} not found"
        )
    return node


@app.get("/dataspace/types", tags=["Dataspace"])
async def get_all_dataspace_node_types(
    current_user: User = Depends(get_current_active_user),
) -> list:
    """
    Get all dataspace node types.
    """
    try:
        return sindit_kg_connector.get_all_dataspace_node_types()
    except Exception as e:
        logger.error(f"Error getting dataspace node types: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/dataspace", tags=["Dataspace"])
async def get_all_dataspace_nodes(
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 10,
) -> List[DataspaceManagement]:
    """
    Get all dataspace nodes.
    """
    try:
        return sindit_kg_connector.get_all_dataspace_nodes(skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error getting dataspace nodes: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/dataspace/management", tags=["Dataspace"])
async def create_dataspace_management(
    payload: DataspaceManagementInput,
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Create or update a DataspaceManagement node and (re)start its connector.

    The service user impersonated by the EDC data plane is **always** the
    caller's identity (``current_user.username``); it cannot be overridden
    via the request body. This guarantees:

    - the dataspace cannot be made to impersonate an arbitrary user simply
      by editing a JSON payload,
    - actions taken through the EDC are auditable back to the SINDIT user
      who created the dataspace.

    The EDC connector is started immediately and ``isActive`` is updated
    to reflect whether the EDC Management API is reachable. ``isActive``
    and ``dataspaceAssets`` are also system-managed and are not part of
    the request body (use ``/dataspace/publish`` to manage assets, and
    delete the node to disable a dataspace).
    """
    try:
        node = payload.to_node(service_user=current_user.username)
        result = sindit_kg_connector.save_node(node)
        if result:
            # Always (re)start the connector; isActive is a system-maintained
            # status reflecting EDC reachability, not user intent.
            update_dataspace_node(node, replace=True)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error creating dataspace management node: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/dataspace/management", tags=["Dataspace"])
async def delete_dataspace_management(
    uri: str,
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Delete a DataspaceManagement node.

    The deletion is done in three steps so resources don't dangle:

    1. Best-effort: clean up every SINDIT-published asset and contract
       definition currently registered in the corresponding EDC.
    2. Stop and forget the in-process ``DataspaceConnector``.
    3. Delete the ``DataspaceManagement`` node from the knowledge graph.

    EDC errors during step 1 are logged and ignored so the user can always
    remove a stale dataspace, even if its EDC is unreachable.
    """
    ds_node = _get_dataspace_node_or_404(uri)
    node_uri = str(ds_node.uri)

    # 1) Best-effort: drop every asset/contract we ever published to this EDC.
    connector = dataspace_connectors.get(node_uri)
    if connector is not None:
        try:
            for item in ds_node.dataspaceAssets or []:
                item_uri = str(getattr(item, "uri", item))
                if not item_uri:
                    continue
                try:
                    connector.unpublish_node(item_uri)
                except Exception as e:  # noqa: BLE001
                    logger.warning(
                        "Could not unpublish %s from %s during delete: %s",
                        item_uri,
                        node_uri,
                        e,
                    )
        except Exception as e:  # noqa: BLE001
            logger.warning("Catalog cleanup for dataspace %s failed: %s", node_uri, e)

    # 2) Stop the in-process connector and remove it from the registry.
    remove_dataspace_node(node_uri)

    # 3) Delete the KG node.
    try:
        result = sindit_kg_connector.delete_node(node_uri)
    except Exception as e:
        logger.error(f"Error deleting dataspace node {node_uri}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"result": result}


@app.post("/dataspace/test_connection", tags=["Dataspace"])
async def test_dataspace_connection(
    uri: str,
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Health-check the EDC Management API and persist the result onto isActive."""
    node = _get_dataspace_node_or_404(uri)
    try:
        connector = dataspace_connectors.get(str(node.uri))
        if connector is None:
            connector = update_dataspace_node(node, replace=False)
        if connector is None:
            return {"healthy": False, "reason": "connector not started"}
        healthy = connector.client.health_check()
        connector.update_connection_status(healthy)
        return {"healthy": healthy}
    except Exception as e:
        logger.error(f"Error testing dataspace {uri}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/dataspace/publish", tags=["Dataspace"])
async def publish_nodes_to_dataspace(
    uri: str,
    payload: DataspacePublishRequest,
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Add nodes to ``dataspaceAssets`` and push them to the EDC.

    The list is mutated and persisted *before* the EDC is contacted so a
    later call can sync the catalog from the KG, then we either reuse an
    existing connector or build a new one. ``update_dataspace_node`` runs
    an initial ``connector.sync(node)`` for freshly built connectors, which
    already publishes everything in ``dataspaceAssets``; we avoid
    re-publishing in that case to keep the response time predictable.
    """
    ds_node = _get_dataspace_node_or_404(uri)
    try:
        existing = list(ds_node.dataspaceAssets or [])
        existing_uris = {
            str(getattr(item, "uri", item)) for item in existing if item is not None
        }
        for node_uri in payload.node_uris:
            if node_uri not in existing_uris:
                existing.append(URIRefNode(uri=node_uri))
                existing_uris.add(node_uri)
        ds_node.dataspaceAssets = existing
        sindit_kg_connector.save_node(ds_node)

        connector = dataspace_connectors.get(str(ds_node.uri))
        connector_was_built_now = False
        if connector is None:
            connector = update_dataspace_node(ds_node, replace=False)
            connector_was_built_now = connector is not None

        published: list[str] = []
        if connector is not None and not connector_was_built_now:
            # Existing connector: explicitly publish the requested nodes.
            # For a freshly built connector update_dataspace_node has
            # already called connector.sync(ds_node), which iterates
            # dataspaceAssets and publishes them; doing it again here would
            # just be a no-op upsert.
            for node_uri in payload.node_uris:
                node = sindit_kg_connector.load_node_by_uri(node_uri)
                if node is None:
                    logger.warning("Node %s not found, skipping publish", node_uri)
                    continue
                connector.publish_node(node)
                published.append(node_uri)
        elif connector_was_built_now:
            published = list(payload.node_uris)
        return {"requested": payload.node_uris, "published": published}
    except Exception as e:
        logger.error(f"Error publishing to dataspace {uri}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/dataspace/publish", tags=["Dataspace"])
async def unpublish_nodes_from_dataspace(
    uri: str,
    payload: DataspacePublishRequest,
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Remove nodes from ``dataspaceAssets`` and unpublish from EDC."""
    ds_node = _get_dataspace_node_or_404(uri)
    try:
        remove_set = {str(u) for u in payload.node_uris}
        ds_node.dataspaceAssets = [
            item
            for item in (ds_node.dataspaceAssets or [])
            if str(getattr(item, "uri", item)) not in remove_set
        ]
        sindit_kg_connector.save_node(ds_node)

        connector = dataspace_connectors.get(str(ds_node.uri))
        unpublished: list[str] = []
        if connector is not None:
            for node_uri in payload.node_uris:
                if connector.unpublish_node(node_uri):
                    unpublished.append(node_uri)
        return {"requested": payload.node_uris, "unpublished": unpublished}
    except Exception as e:
        logger.error(f"Error unpublishing from dataspace {uri}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/dataspace/sync", tags=["Dataspace"])
async def sync_dataspace(
    uri: str,
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Reconcile the EDC catalog with this dataspace's ``dataspaceAssets``."""
    ds_node = _get_dataspace_node_or_404(uri)
    try:
        connector = dataspace_connectors.get(str(ds_node.uri))
        if connector is None:
            connector = update_dataspace_node(ds_node, replace=False)
        if connector is None:
            raise HTTPException(
                status_code=400, detail="Dataspace connector is not active"
            )
        return connector.sync(ds_node)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing dataspace {uri}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dataspace/catalog", tags=["Dataspace"])
async def get_dataspace_catalog(
    uri: str,
    current_user: User = Depends(get_current_active_user),
) -> list:
    """Return the SINDIT-published assets currently registered in the EDC."""
    ds_node = _get_dataspace_node_or_404(uri)
    connector = dataspace_connectors.get(str(ds_node.uri))
    if connector is None:
        connector = update_dataspace_node(ds_node, replace=False)
    if connector is None:
        raise HTTPException(status_code=400, detail="Dataspace connector is not active")
    try:
        assets = connector.client.list_assets()
        return [
            a
            for a in assets
            if isinstance(a, dict)
            and isinstance(a.get("@id"), str)
            and a["@id"].startswith("sindit-")
        ]
    except Exception as e:
        logger.error(f"Error listing catalog for {uri}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

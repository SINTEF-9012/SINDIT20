"""Lifecycle and registry for :class:`DataspaceConnector` instances.

Mirrors the shape of :mod:`sindit.connectors.setup_connectors` but only
handles ``DataspaceManagement`` KG nodes. Publishing of individual SINDIT
nodes is driven explicitly by the ``/dataspace/publish`` API and reconciled
by ``/dataspace/sync``; only :func:`unpublish_node_from_all_active_dataspaces`
is hooked into ``api/kg_endpoints.py`` (on DELETE) to avoid leaving dangling
EDC assets when their backing SINDIT node is removed.
"""

from __future__ import annotations

import threading

from sindit.dataspace.connector_dataspace import DataspaceConnector
from sindit.initialize_kg_connectors import sindit_kg_connector
from sindit.initialize_vault import get_vault_for_username
from sindit.knowledge_graph.dataspace_model import DataspaceManagement
from sindit.util.log import logger

# Active dataspace connectors keyed by ``"<workspace_uri>::<node_uri>"``.
# The composite key is required because different users / workspaces may create
# ``DataspaceManagement`` nodes that share the same URI (they live in separate
# named graphs, so the KG does not enforce global uniqueness).
dataspace_connectors: dict[str, DataspaceConnector] = {}

# Set of workspace URIs whose ``DataspaceManagement`` nodes have been loaded
# into the registry at least once. Used by ``load_dataspaces_for_current_graph``
# to skip redundant KG round-trips on every authenticated request.
_initialized_workspaces: set[str] = set()


def _connector_key(workspace_uri: str, node_uri: str) -> str:
    """Composite registry key: ``<workspace_uri>::<node_uri>``."""
    return f"{workspace_uri}::{node_uri}"


_lock = threading.Lock()


# --------------------------------------------------------------------- helpers


def _resolve_secret(path: str | None, username: str | None = None) -> str | None:
    if not path:
        return None
    try:
        vault = get_vault_for_username(username)
        return vault.resolveSecret(path)
    except Exception as e:  # noqa: BLE001 - vault impls raise various
        logger.warning("Failed to resolve vault secret '%s': %s", path, e)
        return None


def _build_connector_from_node(
    node: DataspaceManagement, username: str | None = None
) -> DataspaceConnector | None:
    """Instantiate a :class:`DataspaceConnector` from the KG node alone.

    All connection parameters live on the ``DataspaceManagement`` node itself
    so the same SINDIT instance can talk to multiple dataspaces with
    different EDC endpoints, service users and SINDIT base URLs.
    """
    if node is None or not getattr(node, "endpoint", None):
        return None

    sindit_api_base_url = (
        str(node.sinditApiBaseUrl) if getattr(node, "sinditApiBaseUrl", None) else None
    )
    if not sindit_api_base_url:
        logger.error(
            "Dataspace %s is missing sinditApiBaseUrl; cannot build connector",
            node.uri,
        )
        return None

    auth_key = _resolve_secret(getattr(node, "authenticationKeyPath", None), username)
    workspace_uri = (
        str(node.sinditWorkspaceUri)
        if getattr(node, "sinditWorkspaceUri", None)
        else None
    )
    callback_key = _resolve_secret(
        getattr(node, "sinditCallbackKeyPath", None), username
    )

    if not workspace_uri:
        logger.error(
            "Dataspace %s is missing sinditWorkspaceUri; cannot build connector",
            node.uri,
        )
        return None

    return DataspaceConnector(
        endpoint=str(node.endpoint),
        auth_type=str(node.authenticationType) if node.authenticationType else None,
        auth_key=auth_key,
        sindit_api_base_url=sindit_api_base_url,
        sindit_workspace_uri=workspace_uri,
        sindit_callback_key=callback_key,
        uri=str(node.uri),
        kg_connector=sindit_kg_connector,
    )


# --------------------------------------------------------------------- update


def update_dataspace_node(
    node: DataspaceManagement, replace: bool = True, username: str | None = None
) -> DataspaceConnector | None:
    """Create / refresh the connector for ``node`` and run an initial sync."""
    if node is None:
        return None
    node_uri = str(node.uri)
    workspace_uri = (
        str(node.sinditWorkspaceUri)
        if getattr(node, "sinditWorkspaceUri", None)
        else None
    )
    key = _connector_key(workspace_uri or "", node_uri)

    with _lock:
        existing = dataspace_connectors.get(key)
        if existing is not None and not replace:
            return existing

        if existing is not None:
            try:
                existing.stop(no_update_connection_status=True)
            except Exception:  # noqa: BLE001
                pass
            dataspace_connectors.pop(key, None)

        # ``isActive`` is system-maintained (set by ``start``/``stop`` and
        # health-check), so we always build & start the connector here. The
        # actual reachability of the EDC determines the persisted status.
        connector = _build_connector_from_node(node, username=username)
        if connector is None:
            return None

        try:
            connector.start()
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to start dataspace connector %s: %s", key, e)
            return None

        dataspace_connectors[key] = connector

    # Run an initial sync outside the lock to avoid blocking other updates.
    try:
        connector.sync(node)
    except Exception as e:  # noqa: BLE001
        logger.error("Initial sync of dataspace %s failed: %s", node_uri, e)

    return connector


def remove_dataspace_node(node_uri: str, workspace_uri: str | None = None) -> bool:
    """Stop the connector for ``node_uri`` and forget it.

    ``workspace_uri`` is required to build the composite registry key.  If
    omitted, falls back to a linear scan (supports callers that only have the
    node URI).
    """
    if workspace_uri is not None:
        key = _connector_key(workspace_uri, str(node_uri))
        with _lock:
            connector = dataspace_connectors.pop(key, None)
    else:
        # Fallback: scan for any connector whose underlying node URI matches.
        with _lock:
            key = next(
                (k for k, c in dataspace_connectors.items() if c.uri == str(node_uri)),
                None,
            )
            connector = dataspace_connectors.pop(key, None) if key else None
    if connector is None:
        return False
    try:
        connector.stop()
    except Exception as e:  # noqa: BLE001
        logger.warning("Error stopping dataspace connector %s: %s", node_uri, e)
    return True


# --------------------------------------------------------------------- init


def load_dataspaces_for_current_graph(
    force: bool = False, username: str | None = None
) -> None:
    """Load and (re)start all ``DataspaceManagement`` nodes from the currently
    active named graph (i.e. the caller's workspace).

    Skips the KG round-trip if this workspace has already been loaded, unless
    ``force=True`` (used after ``POST /dataspace/management`` to pick up a
    newly created node).

    Safe to call on every authenticated request — the ``_initialized_workspaces``
    guard makes subsequent calls for the same workspace a cheap set-lookup.
    """
    current_graph = sindit_kg_connector.get_graph_uri()
    with _lock:
        if not force and current_graph in _initialized_workspaces:
            return

    try:
        nodes = sindit_kg_connector.get_all_dataspace_nodes(skip=0, limit=1000) or []
    except Exception as e:  # noqa: BLE001
        logger.error("Failed to load dataspace nodes for current graph: %s", e)
        nodes = []

    for node in nodes:
        try:
            update_dataspace_node(node, replace=True, username=username)
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Failed to (re)start dataspace %s: %s", getattr(node, "uri", "?"), e
            )

    with _lock:
        _initialized_workspaces.add(current_graph)


# ----------------------------------------------------------------- KG hook API


def unpublish_node_from_all_active_dataspaces(node_uri: str) -> None:
    """Best-effort unpublish across every known dataspace connector.

    We don't filter by ``dataspaceAssets`` here because the node may already
    have been deleted from the KG; we just attempt to remove the corresponding
    EDC asset id from each known connector.
    """
    if not node_uri:
        return
    for connector in list(dataspace_connectors.values()):
        try:
            connector.unpublish_node(str(node_uri))
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Failed to unpublish node %s from dataspace %s: %s",
                node_uri,
                connector.uri,
                e,
            )

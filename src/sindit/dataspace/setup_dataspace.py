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
from sindit.dataspace.edc_mapping import SINDIT_BEARER_SECRET_NAME
from sindit.initialize_kg_connectors import sindit_kg_connector
from sindit.initialize_vault import secret_vault
from sindit.knowledge_graph.dataspace_model import DataspaceManagement
from sindit.util.log import logger

# Active dataspace connectors keyed by the URI of their ``DataspaceManagement``
# node.
dataspace_connectors: dict[str, DataspaceConnector] = {}
_lock = threading.Lock()

# How often the single background thread iterates every active dataspace
# connector to refresh its bearer and re-publish its assets. Default 25
# minutes, comfortably below the 30-minute SINDIT JWT TTL
# (``InMemoryAuthService.ACCESS_TOKEN_EXPIRE_MINUTES``) so consumers never
# see an expired token in published assets' ``authCode``.
_REFRESH_INTERVAL_SECONDS = 25 * 60

_refresh_thread: threading.Thread | None = None
_refresh_stop_event = threading.Event()


# --------------------------------------------------------------------- helpers


def _resolve_secret(path: str | None) -> str | None:
    if not path:
        return None
    try:
        return secret_vault.resolveSecret(path)
    except Exception as e:  # noqa: BLE001 - vault impls raise various
        logger.warning("Failed to resolve vault secret '%s': %s", path, e)
        return None


def _build_connector_from_node(node: DataspaceManagement) -> DataspaceConnector | None:
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

    auth_key = _resolve_secret(getattr(node, "authenticationKeyPath", None))
    service_user = (
        str(node.sinditServiceUser)
        if getattr(node, "sinditServiceUser", None)
        else None
    )
    service_user_password = _resolve_secret(
        getattr(node, "sinditServiceUserPasswordPath", None)
    )

    return DataspaceConnector(
        endpoint=str(node.endpoint),
        auth_type=str(node.authenticationType) if node.authenticationType else None,
        auth_key=auth_key,
        sindit_api_base_url=sindit_api_base_url,
        sindit_service_user=service_user,
        sindit_service_user_password=service_user_password,
        secret_name=SINDIT_BEARER_SECRET_NAME,
        uri=str(node.uri),
        kg_connector=sindit_kg_connector,
    )


# --------------------------------------------------------------------- update


def update_dataspace_node(
    node: DataspaceManagement, replace: bool = True
) -> DataspaceConnector | None:
    """Create / refresh the connector for ``node`` and run an initial sync."""
    if node is None:
        return None
    node_uri = str(node.uri)

    with _lock:
        existing = dataspace_connectors.get(node_uri)
        if existing is not None and not replace:
            return existing

        if existing is not None:
            try:
                existing.stop(no_update_connection_status=True)
            except Exception:  # noqa: BLE001
                pass
            dataspace_connectors.pop(node_uri, None)

        # ``isActive`` is system-maintained (set by ``start``/``stop`` and
        # health-check), so we always build & start the connector here. The
        # actual reachability of the EDC determines the persisted status.
        connector = _build_connector_from_node(node)
        if connector is None:
            return None

        try:
            connector.start()
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to start dataspace connector %s: %s", node_uri, e)
            return None

        dataspace_connectors[node_uri] = connector

    # Run an initial sync outside the lock to avoid blocking other updates.
    try:
        connector.sync(node)
    except Exception as e:  # noqa: BLE001
        logger.error("Initial sync of dataspace %s failed: %s", node_uri, e)

    return connector


def remove_dataspace_node(node_uri: str) -> bool:
    """Stop the connector for ``node_uri`` and forget it."""
    with _lock:
        connector = dataspace_connectors.pop(str(node_uri), None)
    if connector is None:
        return False
    try:
        connector.stop()
    except Exception as e:  # noqa: BLE001
        logger.warning("Error stopping dataspace connector %s: %s", node_uri, e)
    return True


# --------------------------------------------------------------------- init


def initialize_dataspaces() -> None:
    """Load all ``DataspaceManagement`` nodes from the KG and start active ones.

    Also starts the single shared background thread that periodically refreshes
    bearer tokens and re-publishes assets for every dataspace connector.
    """
    try:
        nodes = sindit_kg_connector.get_all_dataspace_nodes(skip=0, limit=1000) or []
    except Exception as e:  # noqa: BLE001
        logger.error("Failed to load dataspace nodes during init: %s", e)
        nodes = []

    for node in nodes:
        try:
            update_dataspace_node(node, replace=True)
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Failed to initialize dataspace %s: %s", getattr(node, "uri", "?"), e
            )

    # Always start the shared refresh loop, even if no dataspaces are active
    # yet; it will pick up any that get added later.
    start_refresh_thread()


# ----------------------------------------------------------- refresh loop


def _refresh_loop() -> None:
    """Single background loop that keeps every active dataspace fresh.

    On each tick the loop snapshots the current connector registry, then for
    every entry it reloads the corresponding ``DataspaceManagement`` node from
    the KG and calls ``connector.sync(node)``. ``sync`` itself refreshes the
    bearer and re-publishes every locally listed asset, propagating the
    rotated ``Authorization`` header into each EDC asset's ``authCode``.

    Errors are logged per connector so one failure does not stop the loop.
    """
    logger.info(
        "Dataspace refresh loop started (interval=%ss)", _REFRESH_INTERVAL_SECONDS
    )
    while not _refresh_stop_event.is_set():
        # Wait first so we don't double-refresh right after start() already
        # minted a token. ``Event.wait`` returns True if the event was set
        # while waiting -> loop exits cleanly on shutdown.
        if _refresh_stop_event.wait(_REFRESH_INTERVAL_SECONDS):
            break

        with _lock:
            snapshot = list(dataspace_connectors.items())

        if not snapshot:
            continue

        for node_uri, connector in snapshot:
            try:
                node = sindit_kg_connector.get_dataspace_node_by_uri(node_uri)
                if node is None:
                    logger.warning(
                        "Dataspace %s no longer in KG; skipping refresh", node_uri
                    )
                    continue
                connector.sync(node)
            except Exception as e:  # noqa: BLE001
                logger.error("Periodic refresh of dataspace %s failed: %s", node_uri, e)
    logger.info("Dataspace refresh loop stopped")


def start_refresh_thread() -> None:
    """Start the shared refresh loop if it is not already running."""
    global _refresh_thread
    if _refresh_thread is not None and _refresh_thread.is_alive():
        return
    _refresh_stop_event.clear()
    _refresh_thread = threading.Thread(
        target=_refresh_loop, name="dataspace_refresh", daemon=True
    )
    _refresh_thread.start()


def stop_refresh_thread() -> None:
    """Signal the shared refresh loop to exit (used by tests / shutdown)."""
    _refresh_stop_event.set()
    thread = _refresh_thread
    if thread is not None and thread.is_alive():
        thread.join(timeout=5.0)


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

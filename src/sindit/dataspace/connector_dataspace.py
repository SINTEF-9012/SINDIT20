"""Dataspace connector that publishes SINDIT KG nodes into an EDC.

This connector reuses the existing :class:`Connector` base class for
bookkeeping (uri, kg_connector, is_connected, observers_lock, ...) but the
"observer" semantics inherited from :class:`Connector` are unused: dataspace
publishing is outbound rather than inbound, so :meth:`notify` is never called.

The connector orchestrates three things:

1. Authenticates SINDIT against itself by calling ``POST /token`` with a
   configured service user, obtaining a JWT.
2. Pushes that JWT (as ``"Bearer <token>"``) into the EDC vault under the
   :data:`SINDIT_BEARER_SECRET_NAME` key via the EDC Management API.
3. Publishes / unpublishes / reconciles EDC HTTP assets that point back at
   ``GET /kg/node?node_uri=<uri>`` of the SINDIT API.
"""

from __future__ import annotations

from typing import Any, Iterable

from sindit.connectors.connector import Connector
from sindit.connectors.connector_factory import ObjectBuilder, connector_factory
from sindit.dataspace.edc_client import EDCManagementClient, EDCManagementClientError
from sindit.dataspace.edc_mapping import (
    DEFAULT_PUBLIC_POLICY_ID,
    SINDIT_BEARER_SECRET_NAME,
    build_contract_definition,
    build_default_public_policy,
    build_http_asset,
    contract_definition_id_for,
    sindit_uri_to_edc_asset_id,
)
from sindit.knowledge_graph.kg_connector import SINDITKGConnector
from sindit.util.log import logger


class DataspaceConnector(Connector):
    """EDC dataspace connector.

    Parameters:
        endpoint: EDC Management API base URL.
        auth_type: Auth type for the EDC Management API (``"tokenbased"``).
        auth_key: Resolved API key for the EDC Management API.
        sindit_api_base_url: Public URL where SINDIT's REST API is reachable
            from the EDC data plane.
        sindit_service_user: SINDIT username used to mint the long-lived
            bearer token consumed by EDC.
        sindit_service_user_password: Password for that user.
        secret_name: Vault key in EDC's vault that will hold the bearer.
        uri: Identifier for this connector instance (the URI of the
            ``DataspaceManagement`` KG node).
        kg_connector: SINDIT KG connector for status updates.
    """

    id: str = "dataspace"

    def __init__(
        self,
        endpoint: str,
        auth_type: str | None = "tokenbased",
        auth_key: str | None = None,
        sindit_api_base_url: str | None = None,
        sindit_workspace_uri: str | None = None,
        sindit_callback_key: str | None = None,
        secret_name: str = SINDIT_BEARER_SECRET_NAME,
        uri: str | None = None,
        kg_connector: SINDITKGConnector | None = None,
    ) -> None:
        super().__init__()
        if not endpoint:
            raise ValueError("endpoint is required for DataspaceConnector")
        if not sindit_api_base_url:
            raise ValueError("sindit_api_base_url is required for DataspaceConnector")
        self.uri = uri or endpoint
        self.kg_connector = kg_connector
        self.sindit_api_base_url = sindit_api_base_url.rstrip("/")
        # Named-graph URI for the workspace whose nodes are published here.
        # Stored on the connector so the callback endpoint can look it up
        # from the in-memory registry without touching the KG.
        self.sindit_workspace_uri = sindit_workspace_uri
        # Static API key sent by the EDC data plane as ``X-Api-Key``.
        self.__sindit_callback_key = sindit_callback_key
        self.secret_name = secret_name
        self.client = EDCManagementClient(
            endpoint=endpoint,
            auth_type=auth_type,
            auth_key=auth_key,
        )

    # ------------------------------------------------------------------ status

    def update_connection_status(self, is_connected: bool) -> None:
        """Persist health status onto ``DataspaceManagement.isActive``.

        Mirrors the base-class helper for ``Connection``/``isConnected``:
        load the full node, mutate the status field, and call ``save_node``.
        ``save_node`` deletes every triple for the subject (``?s ?p ?o``)
        before re-inserting the serialized graph, so any pre-existing
        duplicate ``isActive`` triples in the graph get collapsed back to a
        single value.

        ``DataspaceManagement`` is not part of ``NodeURIClassMapping``
        (which is what the base class' ``load_node_by_uri`` uses by default),
        so we go through :meth:`SINDITKGConnector.get_dataspace_node_by_uri`
        which wires the right ``DataspaceURIClassMapping``.
        """
        self.is_connected = is_connected
        try:
            node = self.kg_connector.get_dataspace_node_by_uri(self.uri)
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "Failed to load dataspace %s for status update: %s", self.uri, e
            )
            return
        if node is None:
            logger.warning(
                "Dataspace %s not found in KG; skipping isActive update", self.uri
            )
            return
        node.isActive = bool(is_connected)
        try:
            self.kg_connector.save_node(node)
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "Failed to persist isActive=%s on dataspace %s: %s",
                is_connected,
                self.uri,
                e,
            )

    # --------------------------------------------------------------- lifecycle

    def start(self, **kwargs) -> None:
        """Verify EDC reachability and ensure the public policy exists."""
        no_status = kwargs.get("no_update_connection_status", False)
        try:
            healthy = self.client.health_check()
            if not healthy:
                logger.error("Dataspace EDC %s is not reachable", self.uri)
                if not no_status:
                    self.update_connection_status(False)
                return

            self.client.create_policy_definition(build_default_public_policy())

            self.is_connected = True
            if not no_status:
                self.update_connection_status(True)
            logger.info("Dataspace connector %s started", self.uri)
        except EDCManagementClientError as e:
            logger.error("Failed to start dataspace connector %s: %s", self.uri, e)
            if not no_status:
                self.update_connection_status(False)

    def stop(self, **kwargs) -> None:
        no_status = kwargs.get("no_update_connection_status", False)
        self.is_connected = False
        if not no_status:
            self.update_connection_status(False)
        logger.info("Dataspace connector %s stopped", self.uri)

    # --------------------------------------------------------------- auth/token

    def validate_callback_key(self, key: str | None) -> bool:
        """Return True if ``key`` matches the configured callback API key.

        Uses a constant-time comparison to prevent timing attacks.
        Raises :class:`ValueError` if no callback key is configured.
        """
        import hmac

        if not self.__sindit_callback_key:
            raise ValueError(
                f"No sinditCallbackKeyPath configured for dataspace {self.uri}"
            )
        if not key:
            return False
        return hmac.compare_digest(self.__sindit_callback_key, key)

    # --------------------------------------------------------------- publish

    def publish_node(self, node: Any) -> str:
        """Upsert the asset and ensure its contract definition exists.

        The callback API key is inlined into the data address as ``authCode``
        so the EDC data plane can authenticate to the dedicated
        ``GET /dataspace/node`` callback endpoint.
        """
        asset_payload = build_http_asset(
            node,
            sindit_api_base_url=self.sindit_api_base_url,
            dataspace_uri=self.uri,
            callback_api_key=self.__sindit_callback_key,
        )
        asset_id = self.client.create_asset(asset_payload)
        self.client.create_contract_definition(
            build_contract_definition(asset_id, DEFAULT_PUBLIC_POLICY_ID)
        )
        logger.info(
            "Published SINDIT node %s as EDC asset %s on dataspace %s",
            getattr(node, "uri", node),
            asset_id,
            self.uri,
        )
        return asset_id

    def unpublish_node(self, node_uri: str) -> bool:
        asset_id = sindit_uri_to_edc_asset_id(node_uri)
        cd_id = contract_definition_id_for(asset_id)
        cd_deleted = self.client.delete_contract_definition(cd_id)
        asset_deleted = self.client.delete_asset(asset_id)
        logger.info(
            "Unpublished SINDIT node %s " "(asset=%s, cd_deleted=%s, asset_deleted=%s)",
            node_uri,
            asset_id,
            cd_deleted,
            asset_deleted,
        )
        return asset_deleted

    # ------------------------------------------------------------------- sync

    def _ensure_public_policy(self) -> None:
        """Idempotently (re)create the SINDIT public policy in the EDC.

        Contract definitions reference ``sindit-public-policy`` by id; if the
        policy is missing, EDC will silently drop the bound assets from
        catalog responses (point-to-point and federated alike). The launchers
        use in-memory EDC stores, so the policy does not survive an EDC
        restart - and ``sync`` is the path used by the periodic refresh loop
        and ``POST /dataspace/sync``, neither of which goes through
        ``start()``. Calling this here makes catalog visibility self-healing
        across EDC restarts.
        """
        try:
            self.client.create_policy_definition(build_default_public_policy())
        except EDCManagementClientError as e:
            logger.warning(
                "Failed to (re)create public policy on dataspace %s: %s",
                self.uri,
                e,
            )

    def sync(self, dataspace_node: Any) -> dict[str, int]:
        """Reconcile the EDC catalog with ``dataspace_node.dataspaceAssets``.

        - Re-asserts the public policy (in case the EDC was restarted and
          lost its in-memory store).
        - Re-publishes every locally listed node (the static API key never
          changes so this mainly serves to reconcile the EDC catalog).
        - Removes any SINDIT-prefixed asset in the EDC that isn't listed.
        Returns a small summary dict for logging / API responses.
        """
        self._ensure_public_policy()

        local_uris = _extract_node_uris(
            getattr(dataspace_node, "dataspaceAssets", None)
        )
        local_asset_ids = {sindit_uri_to_edc_asset_id(u): u for u in local_uris}

        # Inventory of what's currently in EDC under our prefix.
        try:
            remote_assets = self.client.list_assets()
        except EDCManagementClientError as e:
            logger.error("Failed to list assets during sync of %s: %s", self.uri, e)
            remote_assets = []
        remote_ids = {
            a.get("@id")
            for a in remote_assets
            if isinstance(a, dict)
            and isinstance(a.get("@id"), str)
            and a["@id"].startswith("sindit-")
        }

        # Always re-publish every locally listed node so the rotated bearer is
        # propagated. EDC's create-asset upsert (409 -> PUT) makes this safe.
        published = 0
        for asset_id, node_uri in local_asset_ids.items():
            try:
                node = (
                    self.kg_connector.load_node_by_uri(node_uri)
                    if self.kg_connector
                    else None
                )
                if node is None:
                    logger.warning(
                        "Skipping publish of %s: node not found in KG", node_uri
                    )
                    continue
                self.publish_node(node)
                published += 1
            except Exception as e:
                logger.error("Failed to publish %s during sync: %s", node_uri, e)

        removed = 0
        for asset_id in remote_ids - set(local_asset_ids.keys()):
            try:
                self.client.delete_contract_definition(
                    contract_definition_id_for(asset_id)
                )
                if self.client.delete_asset(asset_id):
                    removed += 1
            except EDCManagementClientError as e:
                logger.error("Failed to remove orphan asset %s: %s", asset_id, e)

        summary = {
            "local": len(local_asset_ids),
            "remote": len(remote_ids),
            "published": published,
            "removed": removed,
        }
        logger.info("Dataspace %s sync: %s", self.uri, summary)
        return summary


def _extract_node_uris(dataspace_assets: Iterable[Any] | None) -> list[str]:
    """Return the list of node URIs from a ``dataspaceAssets`` list."""
    if not dataspace_assets:
        return []
    uris: list[str] = []
    for item in dataspace_assets:
        uri = getattr(item, "uri", None) or item
        if uri is None:
            continue
        uri = str(uri)
        if uri:
            uris.append(uri)
    return uris


class DataspaceConnectorBuilder(ObjectBuilder):
    """Factory builder so DataspaceConnectors can be created via the registry."""

    def build(
        self,
        endpoint: str | None = None,
        auth_type: str | None = "tokenbased",
        auth_key: str | None = None,
        sindit_api_base_url: str | None = None,
        sindit_service_user: str | None = None,
        secret_name: str = SINDIT_BEARER_SECRET_NAME,
        uri: str | None = None,
        kg_connector: SINDITKGConnector | None = None,
        **_: Any,
    ) -> DataspaceConnector:
        return DataspaceConnector(
            endpoint=endpoint,
            auth_type=auth_type,
            auth_key=auth_key,
            sindit_api_base_url=sindit_api_base_url,
            sindit_service_user=sindit_service_user,
            secret_name=secret_name,
            uri=uri,
            kg_connector=kg_connector,
        )


connector_factory.register_builder(DataspaceConnector.id, DataspaceConnectorBuilder())

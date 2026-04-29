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
        sindit_service_user: str | None = None,
        sindit_service_user_password: str | None = None,
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
        self.__sindit_service_user = sindit_service_user
        self.__sindit_service_user_password = sindit_service_user_password
        # Kept for backward compatibility; current implementation inlines the
        # bearer as ``authCode`` and does not push to the EDC vault.
        self.secret_name = secret_name
        # Cached ``Authorization: Bearer <jwt>`` header value injected into
        # every published asset's data address. Refreshed via
        # ``refresh_backend_token`` and rotated by ``sync``.
        self._bearer_header: str | None = None
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
        """Verify EDC reachability, mint the SINDIT bearer, ensure policy."""
        no_status = kwargs.get("no_update_connection_status", False)
        try:
            healthy = self.client.health_check()
            if not healthy:
                logger.error("Dataspace EDC %s is not reachable", self.uri)
                if not no_status:
                    self.update_connection_status(False)
                return

            # Mint a fresh SINDIT bearer and cache it in memory; it will be
            # inlined into each asset's data address when published.
            self.refresh_backend_token()

            # Make sure the public policy exists.
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

    def _fetch_sindit_bearer(self) -> str | None:
        """Mint a SINDIT JWT for the configured service user, in-process.

        We deliberately avoid HTTP-calling SINDIT's own ``/token`` endpoint:
        SINDIT runs uvicorn with ``workers=1`` and this method is invoked from
        within a request handler, so a sync HTTP call back into ourselves
        would deadlock until the request times out. Instead we call the
        configured ``AuthService`` directly.

        Returns the full ``Authorization`` header value (``"Bearer <jwt>"``)
        ready to be stored in the EDC vault, or None if no service user is
        configured / authentication failed.
        """
        if not self.__sindit_service_user:
            logger.warning(
                "No SINDIT service user configured for dataspace %s; "
                "EDC will not be able to authenticate to SINDIT",
                self.uri,
            )
            return None
        try:
            # Imported lazily to avoid a circular import at module load.
            from sindit.initialize_authentication import authService

            token = authService.create_access_token(
                username=self.__sindit_service_user,
                password=self.__sindit_service_user_password or "",
            )
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Failed to mint SINDIT token for service user %s: %s",
                self.__sindit_service_user,
                e,
            )
            return None

        access_token = getattr(token, "access_token", None) or (
            token.get("access_token") if isinstance(token, dict) else None
        )
        if not access_token:
            logger.error("AuthService returned no access_token")
            return None
        return f"Bearer {access_token}"

    def refresh_backend_token(self) -> bool:
        """Mint a fresh SINDIT bearer and cache it on this connector.

        We deliberately do not push the value to the EDC vault: the optional
        ``secrets-api`` extension is not part of the default management API
        BOM and is absent from the SINTEF MVD build. The bearer is instead
        inlined into each asset's data address as ``authCode`` (see
        ``edc_mapping.build_http_asset``). Rotation is handled by ``sync``,
        which re-publishes all listed assets after refreshing the bearer.
        """
        header = self._fetch_sindit_bearer()
        if not header:
            return False
        self._bearer_header = header
        logger.info("Refreshed cached SINDIT bearer for dataspace %s", self.uri)
        return True

    # --------------------------------------------------------------- publish

    def publish_node(self, node: Any) -> str:
        """Upsert the asset and ensure its contract definition exists.

        The cached bearer (refreshed via ``refresh_backend_token``) is inlined
        into the data address as ``authCode`` so the EDC data plane can
        authenticate to SINDIT without requiring the EDC vault secrets API.

        If a SINDIT service user is configured but no bearer can be minted
        (for example because the password is missing or ``AuthService``
        rejects it) we refuse to publish: the resulting EDC asset would have
        no ``Authorization`` header in its data address and any consumer-side
        pull would be rejected by SINDIT's auth middleware, which is much
        harder to debug than a hard failure here.
        """
        if self._bearer_header is None:
            # Lazily mint on first publish in case start() didn't run yet.
            self.refresh_backend_token()
        if self._bearer_header is None and self.__sindit_service_user:
            raise EDCManagementClientError(
                f"Refusing to publish {getattr(node, 'uri', node)} to dataspace "
                f"{self.uri}: service user '{self.__sindit_service_user}' is "
                "configured but no SINDIT bearer could be minted (check the "
                "sinditServiceUserPasswordPath vault entry and AuthService logs)"
            )
        asset_payload = build_http_asset(
            node,
            sindit_api_base_url=self.sindit_api_base_url,
            bearer_header=self._bearer_header,
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
        - Refreshes the cached SINDIT bearer (token rotation).
        - Re-publishes every locally listed node so the freshly minted bearer
          is propagated into each asset's ``authCode`` value.
        - Removes any SINDIT-prefixed asset in the EDC that isn't listed.
        Returns a small summary dict for logging / API responses.
        """
        self._ensure_public_policy()
        self.refresh_backend_token()

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
        sindit_service_user_password: str | None = None,
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
            sindit_service_user_password=sindit_service_user_password,
            secret_name=secret_name,
            uri=uri,
            kg_connector=kg_connector,
        )


connector_factory.register_builder(DataspaceConnector.id, DataspaceConnectorBuilder())

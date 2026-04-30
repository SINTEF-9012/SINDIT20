"""HTTP client for the Eclipse Dataspace Connector (EDC) v0.17 Management API.

This client is intentionally small: it only covers the endpoints SINDIT needs
to publish HTTP assets (consumer-pull) with a single open public policy and a
contract definition per asset. Backend (SINDIT) credentials are stored in the
EDC vault and referenced from the asset's data address.

All HTTP traffic is routed through :class:`sindit.util.client_api.ClientAPI`
so that retry / logging behaviour stays consistent with the rest of SINDIT.
"""

from __future__ import annotations

from typing import Any

import requests

from sindit.util.client_api import ClientAPI
from sindit.util.log import logger


class EDCManagementClientError(Exception):
    """Raised on any unrecoverable interaction with the EDC Management API."""


class EDCManagementClient:
    """Thin sync wrapper around the EDC v0.17 Management API.

    Parameters:
        endpoint: Base URL of the EDC Management API (e.g.
            ``http://provider:19193/management``). The client appends versioned
            paths (``/v3/assets``, ``/v3/policydefinitions`` ...) to this base.
        auth_type: How the management API itself is authenticated. Currently
            only ``"tokenbased"`` is implemented (sets the ``X-Api-Key``
            header). Anything else falls back to no auth header.
        auth_key: The actual API key value for the EDC management endpoint
            (already resolved from the SINDIT vault by the caller).
        timeout: HTTP timeout in seconds for non-GET requests; GET uses
            :class:`ClientAPI`'s built-in long timeout.
    """

    EDC_NS = "https://w3id.org/edc/v0.0.1/ns/"
    DEFAULT_CONTEXT = {"@vocab": EDC_NS, "edc": EDC_NS}

    def __init__(
        self,
        endpoint: str,
        auth_type: str | None = "tokenbased",
        auth_key: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        if not endpoint:
            raise ValueError("EDC management endpoint must be provided")
        self.endpoint = endpoint.rstrip("/")
        self.auth_type = (auth_type or "").lower() or None
        self.__auth_key = auth_key
        self.timeout = timeout
        self._client = ClientAPI(self.endpoint)

    # ------------------------------------------------------------------ utils

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.auth_type == "tokenbased" and self.__auth_key:
            headers["X-Api-Key"] = self.__auth_key
        return headers

    def _request(
        self,
        method: str,
        path: str,
        json_body: Any | None = None,
        params: dict[str, Any] | None = None,
        ok_statuses: tuple[int, ...] = (200, 201, 204),
    ) -> requests.Response:
        method = method.upper()
        if not path.startswith("/"):
            path = "/" + path
        headers = self._headers()
        try:
            if method == "GET":
                response = self._client.get_raw(
                    path, retries=0, headers=headers, params=params
                )
            elif method == "POST":
                response = self._client.post(
                    path,
                    json=json_body,
                    retries=0,
                    headers=headers,
                    params=params,
                    timeout=self.timeout,
                )
            elif method == "PUT":
                response = self._client.put(
                    path,
                    json=json_body,
                    retries=0,
                    headers=headers,
                    params=params,
                    timeout=self.timeout,
                )
            elif method == "DELETE":
                response = self._client.delete(
                    path,
                    retries=0,
                    headers=headers,
                    params=params,
                    timeout=self.timeout,
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        except requests.RequestException as e:
            raise EDCManagementClientError(
                f"EDC request {method} {self.endpoint}{path} failed: {e}"
            ) from e

        if response is None:
            # ClientAPI swallows requests.RequestException and returns None on
            # exhausted retries; surface it as a hard failure here.
            raise EDCManagementClientError(
                f"EDC request {method} {self.endpoint}{path} returned no response"
            )

        if response.status_code not in ok_statuses:
            logger.debug(
                "EDC %s %s%s -> %s: %s",
                method,
                self.endpoint,
                path,
                response.status_code,
                response.text,
            )
        return response

    # ----------------------------------------------------------------- health

    def health_check(self) -> bool:
        """Return True if the management API answers a simple asset query."""
        try:
            response = self._request(
                "POST",
                "/v3/assets/request",
                json_body={
                    "@context": dict(self.DEFAULT_CONTEXT),
                    "@type": "QuerySpec",
                    "limit": 1,
                },
                ok_statuses=(200,),
            )
            return response.status_code == 200
        except EDCManagementClientError as e:
            logger.warning("EDC health check failed: %s", e)
            return False

    # ----------------------------------------------------------------- assets

    def list_assets(self, query: dict[str, Any] | None = None) -> list[dict]:
        body = {
            "@context": dict(self.DEFAULT_CONTEXT),
            "@type": "QuerySpec",
        }
        if query:
            body.update(query)
        response = self._request(
            "POST", "/v3/assets/request", json_body=body, ok_statuses=(200,)
        )
        if response.status_code != 200:
            raise EDCManagementClientError(
                f"Failed to list assets: {response.status_code} {response.text}"
            )
        data = response.json()
        if isinstance(data, list):
            return data
        return data.get("@graph", []) or []

    def get_asset(self, asset_id: str) -> dict | None:
        response = self._request(
            "GET", f"/v3/assets/{asset_id}", ok_statuses=(200, 404)
        )
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise EDCManagementClientError(
                f"Failed to get asset {asset_id}: "
                f"{response.status_code} {response.text}"
            )
        return response.json()

    def create_asset(self, asset_payload: dict) -> str:
        """Create an asset, falling back to update if it already exists.

        Returns the asset @id.
        """
        response = self._request(
            "POST", "/v3/assets", json_body=asset_payload, ok_statuses=(200, 201, 409)
        )
        if response.status_code in (200, 201):
            data = response.json()
            return data.get("@id") or asset_payload.get("@id")
        if response.status_code == 409:
            asset_id = asset_payload.get("@id")
            if not asset_id:
                raise EDCManagementClientError(
                    "Asset already exists but no @id provided for update"
                )
            self.update_asset(asset_id, asset_payload)
            return asset_id
        raise EDCManagementClientError(
            f"Failed to create asset: {response.status_code} {response.text}"
        )

    def update_asset(self, asset_id: str, asset_payload: dict) -> None:
        response = self._request(
            "PUT", "/v3/assets", json_body=asset_payload, ok_statuses=(200, 204)
        )
        if response.status_code not in (200, 204):
            raise EDCManagementClientError(
                f"Failed to update asset {asset_id}: "
                f"{response.status_code} {response.text}"
            )

    def delete_asset(self, asset_id: str) -> bool:
        response = self._request(
            "DELETE", f"/v3/assets/{asset_id}", ok_statuses=(200, 204, 404)
        )
        return response.status_code in (200, 204)

    # --------------------------------------------------------------- policies

    def create_policy_definition(self, payload: dict) -> str:
        response = self._request(
            "POST",
            "/v3/policydefinitions",
            json_body=payload,
            ok_statuses=(200, 201, 409),
        )
        if response.status_code in (200, 201):
            data = response.json()
            return data.get("@id") or payload.get("@id")
        if response.status_code == 409:
            return payload.get("@id")
        raise EDCManagementClientError(
            f"Failed to create policy definition: "
            f"{response.status_code} {response.text}"
        )

    def get_policy_definition(self, policy_id: str) -> dict | None:
        response = self._request(
            "GET",
            f"/v3/policydefinitions/{policy_id}",
            ok_statuses=(200, 404),
        )
        if response.status_code == 404:
            return None
        return response.json()

    # ----------------------------------------------------- contract definition

    def create_contract_definition(self, payload: dict) -> str:
        response = self._request(
            "POST",
            "/v3/contractdefinitions",
            json_body=payload,
            ok_statuses=(200, 201, 409),
        )
        if response.status_code in (200, 201):
            data = response.json()
            return data.get("@id") or payload.get("@id")
        if response.status_code == 409:
            return payload.get("@id")
        raise EDCManagementClientError(
            f"Failed to create contract definition: "
            f"{response.status_code} {response.text}"
        )

    def delete_contract_definition(self, contract_def_id: str) -> bool:
        response = self._request(
            "DELETE",
            f"/v3/contractdefinitions/{contract_def_id}",
            ok_statuses=(200, 204, 404),
        )
        return response.status_code in (200, 204)

    # ----------------------------------------------------------------- secret

    def put_secret(self, name: str, value: str) -> None:
        """Upsert a secret in the EDC vault via the Management API.

        EDC 0.17 exposes ``POST /v3/secrets`` to create and ``PUT /v3/secrets``
        to update. We treat 409 on create as an update.
        """
        payload = {
            "@context": dict(self.DEFAULT_CONTEXT),
            "@id": name,
            "value": value,
        }
        response = self._request(
            "POST", "/v3/secrets", json_body=payload, ok_statuses=(200, 201, 409)
        )
        if response.status_code in (200, 201):
            return
        if response.status_code == 409:
            response = self._request(
                "PUT", "/v3/secrets", json_body=payload, ok_statuses=(200, 204)
            )
            if response.status_code in (200, 204):
                return
        raise EDCManagementClientError(
            f"Failed to put secret {name}: " f"{response.status_code} {response.text}"
        )

    def delete_secret(self, name: str) -> bool:
        response = self._request(
            "DELETE", f"/v3/secrets/{name}", ok_statuses=(200, 204, 404)
        )
        return response.status_code in (200, 204)

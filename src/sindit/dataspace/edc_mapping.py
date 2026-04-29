"""Mapping helpers SINDIT KG node -> EDC 0.17 JSON-LD payloads.

The dataspace integration publishes one EDC HTTP asset per SINDIT KG node.
Each asset's data address points back at the SINDIT API
(``GET /kg/node?node_uri=<uri>``). The provider's data plane authenticates
to SINDIT using a bearer header **inlined into the data address** as
``authCode``. This avoids depending on the optional EDC ``secrets-api``
extension, which is not part of the default management API BOM and is not
present in the SINTEF MVD build. When the bearer rotates,
:class:`DataspaceConnector.sync` re-publishes the affected assets so they
pick up the fresh value.
"""

from __future__ import annotations

import hashlib
from typing import Any
from urllib.parse import quote

EDC_NS = "https://w3id.org/edc/v0.0.1/ns/"
# Mirror the canonical context used by the SINTEF MVD seed payloads
# (``deployment/requests/create-asset.json`` & friends): a single ``@vocab``
# entry pointing at the EDC namespace. Adding extra prefixes (``edc``,
# ``odrl``, ``sindit``, ``dct`` ...) here previously caused EDC 0.17's
# JSON-LD transformers to reject the payload with a 500 inside Jersey.
DEFAULT_CONTEXT: dict[str, Any] = {"@vocab": EDC_NS}

# Retained for backward compatibility with code that previously used the EDC
# vault secrets API. Current implementation inlines the bearer as
# ``authCode``; this constant is no longer referenced by ``build_http_asset``
# but kept exported so external imports do not break.
SINDIT_BEARER_SECRET_NAME = "sindit-kg-bearer"

# Fixed ids for the single public policy and the asset id prefix. Kept short
# because some EDC stores impose length limits.
DEFAULT_PUBLIC_POLICY_ID = "sindit-public-policy"
ASSET_ID_PREFIX = "sindit-"
CONTRACT_DEFINITION_ID_PREFIX = "sindit-cd-"


def sindit_uri_to_edc_asset_id(uri: str) -> str:
    """Deterministically derive a short, EDC-safe asset id from a SINDIT URI.

    SINDIT URIs are arbitrary IRIs (e.g. ``http://sindit.sintef.no/2.0#foo``).
    EDC accepts arbitrary string ids but length limits and special characters
    can cause issues, so we use a 16-char hex SHA-256 prefix.
    """
    digest = hashlib.sha256(str(uri).encode("utf-8")).hexdigest()
    return f"{ASSET_ID_PREFIX}{digest[:16]}"


def contract_definition_id_for(asset_id: str) -> str:
    return f"{CONTRACT_DEFINITION_ID_PREFIX}{asset_id}"


def build_http_asset(
    node: Any,
    sindit_api_base_url: str,
    bearer_header: str | None = None,
) -> dict:
    """Build the EDC 0.17 JSON-LD payload for an HTTP asset backed by SINDIT.

    Parameters:
        node: A SINDIT KG node (typically ``AbstractAsset`` or
            ``AbstractAssetProperty``). Only ``uri`` is required; class name
            and label are picked up if present.
        sindit_api_base_url: Public base URL where SINDIT's REST API is
            reachable from the EDC data plane (e.g. ``http://sindit:9017``).
        bearer_header: Full ``Authorization`` header value (e.g.
            ``"Bearer eyJ..."``) inlined into the data address as
            ``authCode``. Pass ``None`` to omit auth (useful only when SINDIT
            exposes an unauthenticated proxy route).
    """
    node_uri = str(getattr(node, "uri", node))
    asset_id = sindit_uri_to_edc_asset_id(node_uri)

    base_url = sindit_api_base_url.rstrip("/") + "/kg/node"
    query_params = f"node_uri={quote(node_uri, safe='')}&depth=1"

    # Plain, unprefixed property keys to match the canonical seed payload
    # (``deployment/requests/create-asset.json``). With ``@vocab=edc`` they
    # all resolve under the EDC namespace.
    properties: dict[str, Any] = {
        "name": node_uri,
        "contenttype": "application/json",
        "sinditUri": node_uri,
    }
    node_class = getattr(node.__class__, "CLASS_URI", None)
    if node_class is not None:
        properties["sinditType"] = str(node_class)
    label = getattr(node, "label", None)
    if label:
        properties["title"] = str(label)
    description = getattr(node, "assetDescription", None) or getattr(
        node, "propertyDescription", None
    )
    if description:
        properties["description"] = str(description)

    # Drop the explicit ``@type: DataAddress`` to match the seed payload;
    # EDC infers it from the ``dataAddress`` slot.
    data_address: dict[str, Any] = {
        "type": "HttpData",
        "name": asset_id,
        "baseUrl": base_url,
        "queryParams": query_params,
        "proxyQueryParams": "true",
        "proxyPath": "false",
        "proxyMethod": "false",
    }
    if bearer_header:
        data_address["authKey"] = "Authorization"
        data_address["authCode"] = bearer_header

    # No top-level ``@type: Asset`` either - matches the seed payload.
    #
    # We extend the default ``@context`` with explicit term definitions for
    # the SINDIT-specific property keys whose *values* are full IRIs
    # (``http://sindit.sintef.no/...`` or ``urn:samm:...``). Without this,
    # EDC's JSON-LD compactor warns ``IRI_CONFUSED_WITH_PREFIX`` because
    # those string values' leading ``http:`` / ``urn:`` segments look like
    # undeclared CURIE prefixes. Marking them as ``@type: "@id"`` (for the
    # IRI-valued ones) and leaving plain literals untyped keeps the
    # compactor quiet without changing the wire format.
    asset_context: dict[str, Any] = {
        **DEFAULT_CONTEXT,
        "sinditUri": {
            "@id": f"{EDC_NS}sinditUri",
            "@type": "@id",
        },
        "sinditType": {
            "@id": f"{EDC_NS}sinditType",
            "@type": "@id",
        },
    }
    return {
        "@context": asset_context,
        "@id": asset_id,
        "properties": properties,
        "dataAddress": data_address,
    }


def build_default_public_policy(
    policy_id: str = DEFAULT_PUBLIC_POLICY_ID,
) -> dict:
    """A permission-less ODRL policy: anyone may USE the bound assets.

    Mirrors the canonical payload used by the SINTEF MVD seed scripts
    (``deployment/requests/create-policy.json``): the outer envelope uses
    the EDC management vocabulary, while the inner ``policy`` block opts
    into the standard ODRL JSON-LD context so ``@type: "Set"`` and
    unprefixed ``permission``/``prohibition``/``obligation`` arrays
    resolve under the ODRL vocabulary. This avoids relying on a custom
    ``odrl:`` prefix and matches the form EDC 0.17's Management API
    accepts out of the box.
    """
    # Byte-for-byte mirror of ``deployment/requests/create-policy.json``
    # in the SINTEF MVD repo: that payload is known to be accepted by EDC
    # 0.17's policy-definition transformer. In particular, do *not* add a
    # top-level ``@type: PolicyDefinition`` - the management API infers it
    # from the route, and adding it triggers a JSON-LD validation error
    # that surfaces as a 500 inside Jersey's response pipeline.
    return {
        "@context": [
            "https://w3id.org/edc/connector/management/v0.0.1",
            {"@vocab": EDC_NS},
        ],
        "@id": policy_id,
        "policy": {
            "@context": "http://www.w3.org/ns/odrl.jsonld",
            "@type": "Set",
            "permission": [],
            "prohibition": [],
            "obligation": [],
        },
    }


def build_contract_definition(asset_id: str, policy_id: str) -> dict:
    """A contract definition that binds exactly one asset to ``policy_id``.

    Both the access and contract policies are set to the same public policy
    so the asset is freely discoverable in the catalog and freely contractable.

    Mirrors ``deployment/requests/create-contractdef.json`` from the MVD
    repo: no top-level ``@type: ContractDefinition`` (only the inner
    ``Criterion`` keeps its ``@type``).
    """
    return {
        "@context": dict(DEFAULT_CONTEXT),
        "@id": contract_definition_id_for(asset_id),
        "accessPolicyId": policy_id,
        "contractPolicyId": policy_id,
        "assetsSelector": [
            {
                "@type": "Criterion",
                "operandLeft": f"{EDC_NS}id",
                "operator": "=",
                "operandRight": asset_id,
            }
        ],
    }

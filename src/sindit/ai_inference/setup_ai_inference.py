"""Lifecycle management for AI inference invokers.

Mirrors the shape of ``connectors/setup_connectors.py`` without using the
connector factory (AI inference has no type-dispatcher; each deployment
node directly carries its endpoint config).

Runtime state
-------------
``ai_model_invokers``
    ``{ deployment_uri: AIModelInvoker }`` — one invoker per
    ``AIModelDeployment`` node that has a non-null ``endpointUrl``.
``ai_inference_properties``
    ``{ property_uri: AIInferencePropertyInvoker }`` — one invoker per
    ``AIInferenceProperty`` node.

Startup ordering
----------------
Deployments are initialised first so their invokers exist before
inference-property invokers try to attach to them — the same ordering
that ``initialize_connections_and_properties`` uses for connections and
properties.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

from sindit.ai_inference.ai_inference_property_invoker import (
    AIInferencePropertyInvoker,
)
from sindit.ai_inference.ai_model_invoker import AIModelInvoker
from sindit.common.semantic_knowledge_graph.rdf_model import URIRefNode
from sindit.initialize_kg_connectors import sindit_kg_connector
from sindit.initialize_vault import get_vault_for_username
from sindit.knowledge_graph.ai_deployment_model import AIModelDeployment
from sindit.knowledge_graph.ai_inference_model import AIInferenceProperty
from sindit.util.log import logger

# ---------------------------------------------------------------------------
# Runtime registries
# ---------------------------------------------------------------------------

ai_model_invokers: dict[str, AIModelInvoker] = {}
ai_inference_properties: dict[str, AIInferencePropertyInvoker] = {}

_pool = ThreadPoolExecutor(max_workers=10, thread_name_prefix="ai_inf_init")
_running_tasks: set[str] = set()
_tasks_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _iter_nodes_by_class(class_uri: str, batch_size: int = 50):
    """Yield all KG nodes of a given class, handling pagination."""
    skip = 0
    seen: set[str] = set()
    while True:
        batch = sindit_kg_connector.load_nodes_by_class(
            class_uri, skip=skip, limit=batch_size
        )
        if not batch:
            break
        for node in batch:
            node_uri = str(getattr(node, "uri", ""))
            if node_uri and node_uri not in seen:
                seen.add(node_uri)
                yield node
        if len(batch) < batch_size:
            break
        skip += len(batch)


def _deployment_uri_from_ref(ref) -> str | None:
    """Extract the URI string from an inferenceDeployment field value."""
    if ref is None:
        return None
    if isinstance(ref, URIRefNode):
        return str(ref.uri)
    if isinstance(ref, AIModelDeployment):
        return str(ref.uri)
    if hasattr(ref, "uri"):
        return str(ref.uri)
    return str(ref)


# ---------------------------------------------------------------------------
# Deployment invoker lifecycle
# ---------------------------------------------------------------------------


def update_deployment_invoker(
    node: AIModelDeployment,
    replace: bool = True,
    async_start: bool = False,
    username: str | None = None,
) -> AIModelInvoker | None:
    """Create or refresh an ``AIModelInvoker`` for the given deployment node.

    Returns ``None`` silently when ``node.endpointUrl`` is not set — safe to
    call unconditionally after saving any ``AIModelDeployment``.
    """
    if not node.endpointUrl:
        return None

    if async_start:
        _update_deployment_invoker_async(node, replace, username)
        return None
    return _update_deployment_invoker_sync(node, replace, username)


def _update_deployment_invoker_sync(
    node: AIModelDeployment,
    replace: bool = True,
    username: str | None = None,
) -> AIModelInvoker | None:
    node_uri = str(node.uri)

    if node_uri in ai_model_invokers and not replace:
        return ai_model_invokers[node_uri]

    # Resolve API key from vault (secret never stored/logged)
    api_key: str | None = None
    if node.apiKeyPath:
        try:
            vault = get_vault_for_username(username)
            api_key = vault.resolveSecret(str(node.apiKeyPath))
        except Exception as exc:
            logger.warning(
                "update_deployment_invoker: could not resolve apiKeyPath for %s: %s",
                node_uri,
                exc,
            )

    # Determine update_interval: prefer node value, fall back to 60 s
    update_interval = 60
    if node.updateInterval if hasattr(node, "updateInterval") else None:
        try:
            update_interval = int(node.updateInterval)  # type: ignore[arg-type]
        except Exception:
            pass

    # Stop the old invoker and collect its attached property invokers
    old_observers: dict = {}
    if node_uri in ai_model_invokers:
        old = ai_model_invokers[node_uri]
        old_observers = dict(old._observers)
        try:
            old.stop(no_update_connection_status=True)
        except Exception:
            pass

    invoker = AIModelInvoker(
        deployment_node=node,
        api_key=api_key,
        uri=node_uri,
        kg_connector=sindit_kg_connector,
        update_interval=update_interval,
    )

    # Re-attach property invokers that were on the old invoker
    for prop_invoker in old_observers.values():
        invoker.attach(prop_invoker)

    ai_model_invokers[node_uri] = invoker

    try:
        invoker.start()
    except Exception as exc:
        logger.error(
            "update_deployment_invoker: failed to start invoker for %s: %s",
            node_uri,
            exc,
        )
        try:
            node.isActive = False
            sindit_kg_connector.save_node(node)
        except Exception:
            pass

    return invoker


def _update_deployment_invoker_async(
    node: AIModelDeployment,
    replace: bool = True,
    username: str | None = None,
) -> None:
    node_uri = str(node.uri)

    with _tasks_lock:
        if node_uri in _running_tasks:
            logger.debug("update_deployment_invoker: already running for %s", node_uri)
            return
        _running_tasks.add(node_uri)

    def _run():
        try:
            _update_deployment_invoker_sync(node, replace, username)
        except Exception as exc:
            logger.error(
                "update_deployment_invoker (async): failed for %s: %s",
                node_uri,
                exc,
            )
        finally:
            with _tasks_lock:
                _running_tasks.discard(node_uri)

    _pool.submit(_run)


def remove_deployment_invoker(node_uri: str) -> bool:
    """Stop and remove the ``AIModelInvoker`` for the given deployment URI."""
    if node_uri not in ai_model_invokers:
        return False
    invoker = ai_model_invokers.pop(node_uri)
    # Detach and clean up all attached property invokers
    for prop_uri in list(invoker._observers.keys()):
        ai_inference_properties.pop(prop_uri, None)
    try:
        invoker.stop()
    except Exception:
        pass
    return True


# ---------------------------------------------------------------------------
# Inference property lifecycle
# ---------------------------------------------------------------------------


def update_inference_property_node(
    node: AIInferenceProperty,
    replace: bool = True,
    username: str | None = None,
) -> AIInferencePropertyInvoker | None:
    """Create or refresh an ``AIInferencePropertyInvoker`` for the given node."""
    node_uri = str(node.uri)

    if node_uri in ai_inference_properties and not replace:
        return ai_inference_properties[node_uri]

    # Resolve the referenced deployment
    deployment_uri = _deployment_uri_from_ref(node.inferenceDeployment)
    if not deployment_uri:
        logger.debug(
            "update_inference_property_node: %s has no inferenceDeployment, skipping",
            node_uri,
        )
        return None

    # Ensure a deployment invoker exists
    if deployment_uri not in ai_model_invokers:
        deployment_node = sindit_kg_connector.load_node_by_uri(deployment_uri)
        if not isinstance(deployment_node, AIModelDeployment):
            logger.warning(
                "update_inference_property_node: %s references deployment %s "
                "which was not found or has wrong type",
                node_uri,
                deployment_uri,
            )
            return None
        update_deployment_invoker(deployment_node, replace=False, username=username)

    invoker = ai_model_invokers.get(deployment_uri)
    if invoker is None:
        logger.warning(
            "update_inference_property_node: no active invoker for deployment %s",
            deployment_uri,
        )
        return None

    # Detach the old property invoker if present
    if node_uri in ai_inference_properties:
        old = ai_inference_properties[node_uri]
        if old.connector is not None:
            old.connector.detach(old)

    prop_invoker = AIInferencePropertyInvoker(
        uri=node_uri,
        kg_connector=sindit_kg_connector,
    )
    invoker.attach(prop_invoker)
    ai_inference_properties[node_uri] = prop_invoker
    return prop_invoker


def remove_inference_property_node(node_uri: str) -> bool:
    """Detach and remove the property invoker for the given URI."""
    if node_uri not in ai_inference_properties:
        return False
    prop_invoker = ai_inference_properties.pop(node_uri)
    if prop_invoker.connector is not None:
        prop_invoker.connector.detach(prop_invoker)
    return True


# ---------------------------------------------------------------------------
# Bulk initialisation
# ---------------------------------------------------------------------------


def initialize_ai_inference(
    replace: bool = True,
    batch_size: int = 50,
    async_start: bool = False,
    username: str | None = None,
) -> None:
    """Initialise all AI inference deployments and properties from the KG.

    Deployments with a non-null ``endpointUrl`` are initialised first so
    their invokers exist when inference-property invokers attach to them.
    """
    for node in _iter_nodes_by_class(str(AIModelDeployment.CLASS_URI), batch_size):
        if node.endpointUrl:
            update_deployment_invoker(
                node,
                replace=replace,
                async_start=async_start,
                username=username,
            )

    for node in _iter_nodes_by_class(str(AIInferenceProperty.CLASS_URI), batch_size):
        update_inference_property_node(node, replace=replace, username=username)


# ---------------------------------------------------------------------------
# On-demand inference
# ---------------------------------------------------------------------------


def invoke_and_update(property_uri: str, username: str | None = None) -> dict:
    """Run one inference step immediately for the given ``AIInferenceProperty``.

    Creates transient invokers on the fly when none exist yet.

    Returns
    -------
    dict
        ``{ "property_uri": ..., "value": ..., "timestamp": ... }``
    """
    node = sindit_kg_connector.load_node_by_uri(property_uri, depth=2)
    if not isinstance(node, AIInferenceProperty):
        raise ValueError(f"No AIInferenceProperty found at URI: {property_uri}")

    # Ensure property invoker exists
    prop_invoker = ai_inference_properties.get(property_uri)
    if prop_invoker is None:
        prop_invoker = update_inference_property_node(
            node, replace=False, username=username
        )
    if prop_invoker is None:
        raise RuntimeError(
            f"Could not create a property invoker for {property_uri}. "
            "Ensure the referenced AIModelDeployment has an endpointUrl."
        )

    # Resolve the deployment invoker
    deployment_uri = _deployment_uri_from_ref(node.inferenceDeployment)
    invoker = ai_model_invokers.get(deployment_uri)  # type: ignore[arg-type]
    if invoker is None:
        raise RuntimeError(f"No active AIModelInvoker for deployment {deployment_uri}")

    # Run inference synchronously
    prop_invoker.update_value(invoker)

    # Return the freshly written value
    updated = sindit_kg_connector.load_node_by_uri(property_uri)
    return {
        "property_uri": property_uri,
        "value": updated.propertyValue if updated else None,
        "timestamp": (
            str(updated.propertyValueTimestamp)
            if updated and updated.propertyValueTimestamp
            else None
        ),
    }

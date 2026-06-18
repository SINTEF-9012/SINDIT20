"""Runtime invoker for a single AIInferenceProperty.

When ``update_value()`` is called by ``AIModelInvoker.notify()``:

1. Load the ``AIInferenceProperty`` node from the KG.
2. Skip if ``isEnabled`` is ``False``.
3. For each ``(feature_name, property_uri)`` in ``inputMapping``, load
   the corresponding SINDIT property and read its current
   ``propertyValue``.
4. Call ``AIModelInvoker.invoke(input_data)`` with the assembled values.
5. Extract the prediction scalar using ``responseField`` (dot-path), or
   store the full JSON response when ``responseField`` is not set.
6. Write the result to this property's ``propertyValue`` /
   ``propertyValueTimestamp`` via ``update_property_value_to_kg()``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sindit.connectors.connector import Connector, Property
from sindit.knowledge_graph.kg_connector import SINDITKGConnector
from sindit.util.log import logger


def _extract_by_dotpath(response: dict | list, field_path: str):
    """Traverse a nested dict/list using a dot-separated path.

    Examples
    --------
    >>> _extract_by_dotpath({"predictions": [0.87]}, "predictions.0")
    0.87
    >>> _extract_by_dotpath({"result": {"score": 0.5}}, "result.score")
    0.5
    """
    value = response
    for part in field_path.split("."):
        try:
            if isinstance(value, list):
                value = value[int(part)]
            elif isinstance(value, dict):
                value = value[part]
            else:
                raise TypeError(
                    f"Cannot index into {type(value).__name__} with key '{part}'"
                )
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ValueError(
                f"responseField '{field_path}': cannot extract at '{part}': {exc}"
            ) from exc
    return value


class AIInferencePropertyInvoker(Property):
    """Observer that runs one inference step and writes the result to the KG.

    Parameters
    ----------
    uri:
        KG URI of the ``AIInferenceProperty`` this invoker manages.
    kg_connector:
        Used to load input properties and save the prediction result.
    """

    def __init__(self, uri: str, kg_connector: SINDITKGConnector):
        self.uri = str(uri)
        self.kg_connector = kg_connector
        self.value = None

    # ------------------------------------------------------------------
    # Property interface
    # ------------------------------------------------------------------

    def attach(self, connector: Connector) -> None:  # noqa: D401
        """Called by ``Connector.attach()``; no extra setup needed."""
        pass

    def update_value(self, connector: Connector, **kwargs) -> None:
        """Run one inference step triggered by the ``AIModelInvoker`` poll."""
        # Import here to avoid circular imports (invoker ↔ setup ↔ invoker).
        from sindit.ai_inference.ai_model_invoker import AIModelInvoker

        invoker: AIModelInvoker = connector  # type: ignore[assignment]

        # ── 1. Load the AIInferenceProperty node ─────────────────────
        try:
            node = self.kg_connector.load_node_by_uri(self.uri, depth=2)
        except Exception as exc:
            logger.error(
                "AIInferencePropertyInvoker %s: cannot load node: %s", self.uri, exc
            )
            return

        if node is None:
            logger.warning(
                "AIInferencePropertyInvoker %s: node not found in KG", self.uri
            )
            return

        # ── 2. Respect isEnabled flag ─────────────────────────────────
        if node.isEnabled is False:
            logger.debug(
                "AIInferencePropertyInvoker %s: isEnabled=False, skipping", self.uri
            )
            return

        # ── 3. Resolve inputMapping ───────────────────────────────────
        input_mapping = node.inputMapping or {}
        if isinstance(input_mapping, str):
            try:
                input_mapping = json.loads(input_mapping)
            except Exception as exc:
                logger.error(
                    "AIInferencePropertyInvoker %s: invalid inputMapping JSON: %s",
                    self.uri,
                    exc,
                )
                return

        input_data: dict = {}
        for feature_name, prop_uri in input_mapping.items():
            prop_uri_str = str(prop_uri).strip()  # strip accidental whitespace

            # Guard: reject obviously invalid URIs before hitting SPARQL
            if not prop_uri_str or not (
                prop_uri_str.startswith("http")
                or prop_uri_str.startswith("urn:")
            ):
                logger.error(
                    "AIInferencePropertyInvoker %s: inputMapping['%s'] = %r "
                    "is not a valid KG node URI (expected http:// or urn: prefix). "
                    "Update the AIInferenceProperty with the correct property URI.",
                    self.uri,
                    feature_name,
                    prop_uri_str,
                )
                return

            try:
                prop_node = self.kg_connector.load_node_by_uri(prop_uri_str)
                if prop_node is not None and hasattr(prop_node, "propertyValue"):
                    input_data[feature_name] = prop_node.propertyValue
                else:
                    logger.warning(
                        "AIInferencePropertyInvoker %s: input '%s' (%s) "
                        "has no propertyValue — using None",
                        self.uri,
                        feature_name,
                        prop_uri_str,
                    )
                    input_data[feature_name] = None
            except Exception as exc:
                logger.error(
                    "AIInferencePropertyInvoker %s: failed to load input '%s' "
                    "(URI: %s): %s",
                    self.uri,
                    feature_name,
                    prop_uri_str,
                    exc,
                )
                return

        # ── 4. Call the AI model endpoint ─────────────────────────────
        try:
            response = invoker.invoke(input_data)
        except Exception as exc:
            logger.error(
                "AIInferencePropertyInvoker %s: invoke failed: %s", self.uri, exc
            )
            return

        # ── 5. Extract result via responseField (or store full response) ──
        response_field = node.responseField
        if response_field:
            try:
                result = _extract_by_dotpath(response, str(response_field))
            except ValueError as exc:
                logger.error(
                    "AIInferencePropertyInvoker %s: %s", self.uri, exc
                )
                return
        else:
            result = response

        # ── 6. Persist result to KG ───────────────────────────────────
        timestamp = datetime.now(tz=timezone.utc)
        self.value = result
        self.update_property_value_to_kg(self.uri, result, timestamp)
        logger.debug(
            "AIInferencePropertyInvoker %s: updated propertyValue", self.uri
        )

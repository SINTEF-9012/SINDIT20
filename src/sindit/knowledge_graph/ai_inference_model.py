"""RDF model for AI inference properties.

An ``AIInferenceProperty`` is an ``AbstractAssetProperty`` whose
``propertyValue`` is produced by calling an external AI model prediction
API.  It behaves like any other SINDIT property: it can be attached to
assets, streamed via ``GET /kg/stream``, searched, and displayed.

The inference runtime (``AIModelInvoker`` + ``AIInferencePropertyInvoker``)
is responsible for periodically:

1. Reading the ``propertyValue`` of each URI listed in ``inputMapping``
   from the KG.
2. Assembling those values into a prediction request payload.
3. POSTing to the ``endpointUrl`` stored on the referenced
   ``AIModelDeployment`` node.
4. Extracting the result via ``responseField`` and writing it back to
   this property's ``propertyValue`` / ``propertyValueTimestamp``.
"""

from __future__ import annotations

from typing import ClassVar, Union

from rdflib import Literal, URIRef

from sindit.common.semantic_knowledge_graph.rdf_model import URIRefNode
from sindit.knowledge_graph.ai_deployment_model import AIModelDeployment
from sindit.knowledge_graph.graph_model import (
    GRAPH_MODEL,
    AbstractAssetProperty,
    NodeURIClassMapping,
)


class AIInferenceProperty(AbstractAssetProperty):
    """A property whose value is produced by calling an external AI model API.

    Inherits from ``AbstractAssetProperty`` so predictions are normal SINDIT
    data properties.  ``propertyConnection`` is intentionally left unset so
    the existing connector lifecycle (``setup_connectors.py``) ignores this
    class entirely.

    Fields
    ------
    inferenceDeployment
        URI reference to the ``AIModelDeployment`` node that holds the
        endpoint URL, type, and API-key vault path.
    inputMapping
        JSON dict mapping model feature names to SINDIT property URIs.
        Example: ``{"temperature": "urn:.../sensor_prop", "rpm": "urn:.../rpm_prop"}``
        The invoker reads the current ``propertyValue`` of each URI and
        assembles the request payload from those values.
    responseField
        Optional dot-path into the JSON response used to extract a scalar
        result.  Example: ``"predictions.0"`` extracts
        ``response["predictions"][0]``.  When omitted the full response
        JSON object is stored as ``propertyValue``.
    updateInterval
        Polling interval in seconds.  Defaults to 60 when not set.
    isEnabled
        Set to ``False`` to pause inference for this property without
        deleting it.  The invoker skips disabled properties.
    """

    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.AIInferenceProperty

    mapping: ClassVar[dict] = {
        **AbstractAssetProperty.mapping,
        "inferenceDeployment": GRAPH_MODEL.inferenceDeployment,
        "inputMapping": GRAPH_MODEL.inputMapping,
        "responseField": GRAPH_MODEL.responseField,
        "updateInterval": GRAPH_MODEL.updateInterval,
        "isEnabled": GRAPH_MODEL.isEnabled,
    }

    # Reference to the AIModelDeployment node (endpoint config)
    inferenceDeployment: Union[URIRefNode, AIModelDeployment] = None
    # JSON dict: { feature_name: sindit_property_uri, ... }
    inputMapping: Literal | dict = None
    # Dot-path to extract a scalar from the response JSON
    responseField: Literal | str = None
    # Polling interval in seconds (runtime default: 60)
    updateInterval: Literal | int = None
    # Set False to pause without deleting
    isEnabled: Literal | bool = None


# ---------------------------------------------------------------------------
# KG class-URI mapping and registration
# ---------------------------------------------------------------------------

AIInferenceURIClassMapping = {
    AIInferenceProperty.CLASS_URI: AIInferenceProperty,
}

# Register as a first-class KG node type so generic /kg/* endpoints work.
# AIModelDeployment is already registered via AIDeploymentURIClassMapping in
# ai_deployment_model.py; only the new class is added here.
NodeURIClassMapping.update(AIInferenceURIClassMapping)

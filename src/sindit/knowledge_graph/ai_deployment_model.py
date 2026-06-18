"""RDF model for AI model deployment metadata.

SINDIT is a *client* of externally deployed AI models, not a deployment
manager. ``AIModelDeployment`` stores the minimal information needed to
call an external model prediction API: a description, an optional link to
a twin asset, and the serving endpoint configuration.
"""

from __future__ import annotations

from typing import ClassVar

from rdflib import Literal, URIRef

from sindit.common.semantic_knowledge_graph.rdf_model import RDFModel, URIRefNode
from sindit.knowledge_graph.graph_model import GRAPH_MODEL, NodeURIClassMapping


class AIModelDeployment(RDFModel):
    """Root node describing an externally deployed AI model that SINDIT connects to.

    Combines identification/documentation fields from the AAS submodel
    (IDTA 02059-1-0) with SINDIT-specific serving-endpoint configuration
    fields so a single KG node represents both the semantic description and
    the runtime connection config.

    System-managed field
    --------------------
    ``isActive`` is set to ``True`` by ``AIModelInvoker.start()`` and
    ``False`` by ``AIModelInvoker.stop()``.  It defaults to ``None`` (not
    ``False``) for the same reason as ``Connection.isConnected`` and
    ``DataspaceManagement.isActive``: a ``False`` default would cause a
    phantom ``[False, <real_value>]`` list during deserialisation of nodes
    that only have a single ``:isActive`` triple.
    """

    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.AIModelDeployment

    mapping: ClassVar[dict] = {
        "deploymentDescription": GRAPH_MODEL.deploymentDescription,
        "deployedToAsset": GRAPH_MODEL.deployedToAsset,
        "endpointUrl": GRAPH_MODEL.endpointUrl,
        "endpointType": GRAPH_MODEL.endpointType,
        "apiKeyPath": GRAPH_MODEL.apiKeyPath,
        "isActive": GRAPH_MODEL.isActive,
    }

    deploymentDescription: Literal | str = None
    deployedToAsset: URIRefNode = None
    endpointUrl: Literal | str = None  # prediction REST URL
    endpointType: Literal | str = None  # "generic" | "mlflow" | "triton" | …
    apiKeyPath: Literal | str = None  # vault path for the API key
    isActive: Literal | bool = None  # runtime-managed; see class docstring


# ---------------------------------------------------------------------------
# KG class-URI mapping and registration
# ---------------------------------------------------------------------------

AIDeploymentURIClassMapping = {
    AIModelDeployment.CLASS_URI: AIModelDeployment,
}

# Register as first-class KG node types so generic /kg/* endpoints (load,
# list, search, delete) work without connector changes.
NodeURIClassMapping.update(AIDeploymentURIClassMapping)

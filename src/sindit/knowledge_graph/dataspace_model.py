from typing import ClassVar, List, Union

from sindit.common.semantic_knowledge_graph.rdf_model import RDFModel, URIRefNode
from rdflib import Literal, URIRef

from sindit.knowledge_graph.graph_model import (
    GRAPH_MODEL,
    AbstractAsset,
    AbstractAssetProperty,
)


class DataspaceManagement(RDFModel):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.DataspaceManagement

    mapping: ClassVar[dict] = {
        "endpoint": GRAPH_MODEL.endpoint,
        "authenticationType": GRAPH_MODEL.authenticationType,
        "authenticationKeyPath": GRAPH_MODEL.authenticationKeyPath,
        "isActive": GRAPH_MODEL.isActive,
        "dataspaceDescription": GRAPH_MODEL.dataspaceDescription,
        "sinditApiBaseUrl": GRAPH_MODEL.sinditApiBaseUrl,
        "sinditWorkspaceUri": GRAPH_MODEL.sinditWorkspaceUri,
        "sinditCallbackKeyPath": GRAPH_MODEL.sinditCallbackKeyPath,
        "dataspaceAssets": GRAPH_MODEL.dataspaceAssets,
    }

    endpoint: Literal | str = None
    authenticationType: Literal | str = None
    authenticationKeyPath: Literal | str = None
    # System-maintained status flag mirroring the ``isConnected`` pattern of
    # other connectors. Updated by ``DataspaceConnector`` after each
    # ``start``/``stop`` and health-check; not intended to be set by users.
    #
    # Default is ``None`` (not ``False``) deliberately, matching
    # ``Connection.isConnected``: the deserializer in :mod:`rdf_model`
    # appends each loaded triple's value to the existing field value when
    # that value is not ``None``. With a default of ``False``, every load
    # of a node with a single ``:isActive`` triple would surface as a
    # phantom ``[False, <real value>]`` list to callers.
    isActive: Literal | bool = None
    dataspaceDescription: Literal | str = None
    # Public URL of the SINDIT API as reachable from the EDC data plane.
    # Used to build the ``baseUrl`` of every published HTTP asset's data
    # address (e.g. ``http://sindit:9017``).
    sinditApiBaseUrl: Literal | str = None
    # Named-graph URI of the workspace whose KG nodes are published to this
    # dataspace (e.g. ``http://sindit.sintef.no/2.0#admin/default``).
    # **Optional on POST /dataspace/management**: if omitted or null, the
    # server automatically fills it from the calling user's current workspace.
    # Persisted in the KG so it survives SINDIT restarts.
    sinditWorkspaceUri: Literal | str = None
    # Vault path holding the static API key the EDC data plane must send as
    # ``X-Api-Key`` when calling back to ``GET /dataspace/node``.
    sinditCallbackKeyPath: Literal | str = None
    dataspaceAssets: List[
        Union[URIRefNode, AbstractAssetProperty, AbstractAsset]
    ] = None


DataspaceURIClassMapping = {
    DataspaceManagement.CLASS_URI: DataspaceManagement,
}

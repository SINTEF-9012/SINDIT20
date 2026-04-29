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
        "sinditServiceUser": GRAPH_MODEL.sinditServiceUser,
        "sinditServiceUserPasswordPath": GRAPH_MODEL.sinditServiceUserPasswordPath,
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
    # Service-user credentials used by this dataspace connector to mint a
    # bearer token via SINDIT's own ``POST /token`` endpoint. The bearer is
    # then stored in the EDC vault and referenced from each asset's
    # ``DataAddress`` via ``secretName``.
    sinditServiceUser: Literal | str = None
    sinditServiceUserPasswordPath: Literal | str = None
    dataspaceAssets: List[
        Union[URIRefNode, AbstractAssetProperty, AbstractAsset]
    ] = None


DataspaceURIClassMapping = {
    DataspaceManagement.CLASS_URI: DataspaceManagement,
}

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
    # SINDIT username the dataspace connector will impersonate when the EDC
    # data plane calls back into ``/kg/node``. A bearer JWT is minted
    # in-process via :meth:`AuthService.mint_service_token` and inlined into
    # each published asset's ``DataAddress`` as ``authCode``; no password is
    # stored on the node or in the vault. ``POST /dataspace/management``
    # auto-fills this with the calling user's username when omitted, so most
    # callers never need to set it explicitly.
    sinditServiceUser: Literal | str = None
    dataspaceAssets: List[
        Union[URIRefNode, AbstractAssetProperty, AbstractAsset]
    ] = None


DataspaceURIClassMapping = {
    DataspaceManagement.CLASS_URI: DataspaceManagement,
}

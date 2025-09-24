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
        "authenticationKey": GRAPH_MODEL.authenticationKey,
        "isActive": GRAPH_MODEL.isActive,
        "dataspaceDescription": GRAPH_MODEL.dataspaceDescription,
        "dataspaceName": GRAPH_MODEL.dataspaceName,
    }

    endpoint: Literal | str = None
    authenticationType: Literal | str = None
    authenticationKey: Literal | str = None
    isActive: Literal | bool = False
    dataspaceDescription: Literal | str = None
    dataspaceAssets: List[
        Union[URIRefNode, AbstractAssetProperty, AbstractAsset]
    ] = None


DataspaceURIClassMapping = {
    DataspaceManagement.CLASS_URI: DataspaceManagement,
}

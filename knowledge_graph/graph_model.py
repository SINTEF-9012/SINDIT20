from enum import Enum
from typing import ClassVar, List, Union

from common.semantic_knowledge_graph.rdf_model import RDFModel, URIRefNode
from rdflib import Literal, Namespace, URIRef


class GraphNamespace(Enum):
    """Enum for the namespaces used in the graph"""

    SINDIT = Namespace("urn:samm:sindit.sintef.no:1.0.0#")
    SINDIT_KG = Namespace("http://sindit.sintef.no/2.0#")
    SAMM_UNIT = Namespace("urn:samm:org.eclipse.esmf.samm:unit:2.1.0#")
    SAMM = Namespace("urn:samm:org.eclipse.esmf.samm:meta-model:2.1.0#")
    SAMM_CHARACTERISTIC = Namespace(
        "urn:samm:org.eclipse.esmf.samm:characteristic:2.1.0#"
    )


GRAPH_MODEL = GraphNamespace.SINDIT.value


class Connection(RDFModel):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.Connection

    mapping: ClassVar[dict] = {
        "tokenPath": GRAPH_MODEL.tokenPath,
        "type": GRAPH_MODEL.type,
        "passwordPath": GRAPH_MODEL.passwordPath,
        "port": GRAPH_MODEL.port,
        "host": GRAPH_MODEL.host,
        "isConnected": GRAPH_MODEL.isConnected,
        "username": GRAPH_MODEL.username,
        "connectionDescription": GRAPH_MODEL.connectionDescription,
    }

    type: Literal | str = None
    host: Literal | str = None
    port: Literal | int = None
    username: Literal | str = None
    passwordPath: Literal | str = None
    tokenPath: Literal | str = None
    isConnected: Literal | bool = None
    connectionDescription: Literal | str = None


class AbstractAssetProperty(RDFModel):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.AbstractAssetProperty

    mapping: ClassVar[dict] = {
        "propertyUnit": GRAPH_MODEL.propertyUnit,
        "propertySemanticID": GRAPH_MODEL.propertySemanticID,
        "propertyDescription": GRAPH_MODEL.propertyDescription,
        "propertyDataType": GRAPH_MODEL.propertyDataType,
        "propertyValue": GRAPH_MODEL.propertyValue,
        "propertyName": GRAPH_MODEL.propertyName,
        "propertyValueTimestamp": GRAPH_MODEL.propertyValueTimestamp,
    }

    propertyUnit: Union[URIRefNode, Literal, str] = None
    propertySemanticID: Literal | str = None
    propertyDescription: Literal | str = None
    propertyDataType: Union[URIRefNode, Literal, str] = None
    propertyValue: Literal | str = None
    propertyName: Literal | str = None
    propertyValueTimestamp: Literal | str = None


class DatabaseProperty(AbstractAssetProperty):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.DatabaseProperty

    databasePropertyConnection: Union[URIRefNode, Connection] = None
    query: Literal | str = None

    mapping: ClassVar[dict] = {
        **AbstractAssetProperty.mapping,
        "databasePropertyConnection": GRAPH_MODEL.databasePropertyConnection,
        "query": GRAPH_MODEL.query,
    }


class StreamingProperty(AbstractAssetProperty):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.StreamingProperty

    streamingPropertyConnection: Union[URIRefNode, Connection] = None
    streamingTopic: Literal | str = None
    streamingPath: Literal | str = None

    mapping: ClassVar[dict] = {
        **AbstractAssetProperty.mapping,
        "streamingPropertyConnection": GRAPH_MODEL.streamingPropertyConnection,
        "streamingTopic": GRAPH_MODEL.streamingTopic,
        "streamingPath": GRAPH_MODEL.streamingPath,
    }


class TimeseriesProperty(DatabaseProperty):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.TimeseriesProperty

    mapping: ClassVar[dict] = {
        **DatabaseProperty.mapping,
    }


class File(DatabaseProperty):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.File

    mapping: ClassVar[dict] = {
        **DatabaseProperty.mapping,
        "fileType": GRAPH_MODEL.fileType,
        "filePath": GRAPH_MODEL.filePath,
    }

    fileType: Literal | str = None
    filePath: Literal | str = None


class AbstractAsset(RDFModel):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.AbstractAsset

    mapping: ClassVar[dict] = {
        "assetProperties": GRAPH_MODEL.assetProperties,
        "assetDescription": GRAPH_MODEL.assetDescription,
    }

    assetProperties: List[
        Union[
            URIRefNode,
            AbstractAssetProperty,
            DatabaseProperty,
            StreamingProperty,
            TimeseriesProperty,
            File,
        ]
    ] = None

    assetDescription: Literal | str = None

    # def __init__(
    #     self,
    #     **kwargs,
    # ):
    #     super().__init__(**kwargs)

    #     if self.assetProperties is not None:
    #         for i in range(len(self.assetProperties)):
    #             if isinstance(self.assetProperties[i], str):
    #                 self.assetProperties[i] = URIRef(self.assetProperties[i])


class SINDITKG(RDFModel):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.SINDITKG

    mapping: ClassVar[dict] = {
        "assets": GRAPH_MODEL.assets,
        "dataConnections": GRAPH_MODEL.dataConnections,
    }

    assets: List[Union[URIRefNode, AbstractAsset]] = None
    dataConnections: List[Union[URIRefNode, Connection]] = None


URIClassMapping = {
    Connection.CLASS_URI: Connection,
    AbstractAssetProperty.CLASS_URI: AbstractAssetProperty,
    DatabaseProperty.CLASS_URI: DatabaseProperty,
    StreamingProperty.CLASS_URI: StreamingProperty,
    TimeseriesProperty.CLASS_URI: TimeseriesProperty,
    File.CLASS_URI: File,
    AbstractAsset.CLASS_URI: AbstractAsset,
    SINDITKG.CLASS_URI: SINDITKG,
}

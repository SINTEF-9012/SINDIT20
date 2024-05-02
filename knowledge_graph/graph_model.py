from enum import Enum
from typing import ClassVar, List, Union

from rdflib import Literal, Namespace, URIRef

from common.semantic_knowledge_graph.rdf_model import RDFModel


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
    class_uri: ClassVar[URIRef] = GRAPH_MODEL.Connection

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
    # uri: URIRef
    type: Literal | str = None
    host: Literal | str = None
    port: Literal | int = None
    username: Literal | str = None
    passwordPath: Literal | str = None
    tokenPath: Literal | str = None
    isConnected: Literal | bool = None
    connectionDescription: Literal | str = None

    # def __init__(
    #     self,
    #     uri: URIRef,
    #     label: Literal = None,
    #     type: Literal = None,
    #     host: Literal = None,
    #     port: Literal = None,
    #     username: Literal = None,
    #     passwordPath: Literal = None,
    #     tokenPath: Literal = None,
    #     isConnected: Literal = False,
    #     connectionDescription=None,
    # ):
    #     super().__init__()
    #     self.assign_constructor_vars(locals())

    # def __init__(
    #     self,
    #     **kwargs,
    # ):
    #     super().__init__(**kwargs)
    #     self.assign_constructor_vars(locals())


class AbstractAssetProperty(RDFModel):
    class_uri: ClassVar[URIRef] = GRAPH_MODEL.AbstractAssetProperty

    mapping: ClassVar[dict] = {
        "propertyUnit": GRAPH_MODEL.propertyUnit,
        "propertySemanticID": GRAPH_MODEL.propertySemanticID,
        "propertyDescription": GRAPH_MODEL.propertyDescription,
        "propertyDataType": GRAPH_MODEL.propertyDataType,
        "propertyValue": GRAPH_MODEL.propertyValue,
        "propertyName": GRAPH_MODEL.propertyName,
    }

    propertyUnit: URIRef | Literal | str = None
    propertySemanticID: Literal | str = None
    propertyDescription: Literal | str = None
    propertyDataType: Literal | str = None
    propertyValue: Literal | str = None
    propertyName: Literal | str = None

    # def __init__(
    #     self,
    #     uri: URIRef,
    #     label: Literal = None,
    #     propertyUnit: Literal = None,
    #     propertySemanticID: Literal = None,
    #     propertyDescription: Literal = None,
    #     propertyDataType: Literal = None,
    #     propertyValue: Literal = None,
    #     propertyName: Literal = None,
    # ):
    #     super().__init__()
    #     self.assign_constructor_vars(locals())


class DatabaseProperty(AbstractAssetProperty):
    class_uri: ClassVar[URIRef] = GRAPH_MODEL.DatabaseProperty

    databasePropertyConnection: Connection | URIRef = None
    query: Literal | str = None

    mapping: ClassVar[dict] = {
        **AbstractAssetProperty.mapping,
        "databasePropertyConnection": GRAPH_MODEL.databasePropertyConnection,
        "query": GRAPH_MODEL.query,
    }

    # def __init__(
    #     self,
    #     uri: URIRef,
    #     label: Literal = None,
    #     propertyUnit: Literal = None,
    #     propertySemanticID: Literal = None,
    #     propertyDescription: Literal = None,
    #     propertyDataType: Literal = None,
    #     propertyValue: Literal = None,
    #     propertyName: Literal = None,
    #     databasePropertyConnection: Connection = None,
    #     query: Literal = None,
    # ):
    #     super().__init__(uri)
    #     self.assign_constructor_vars(locals())


class StreamingProperty(AbstractAssetProperty):
    class_uri: ClassVar[URIRef] = GRAPH_MODEL.StreamingProperty

    streamingPropertyConnection: Connection | URIRef = None
    streamingTopic: Literal | str = None

    mapping: ClassVar[dict] = {
        **AbstractAssetProperty.mapping,
        "streamingPropertyConnection": GRAPH_MODEL.streamingPropertyConnection,
        "streamingTopic": GRAPH_MODEL.streamingTopic,
    }

    # def __init__(
    #     self,
    #     uri: URIRef,
    #     label: Literal = None,
    #     propertyUnit: Literal = None,
    #     propertySemanticID: Literal = None,
    #     propertyDescription: Literal = None,
    #     propertyDataType: Literal = None,
    #     propertyValue: Literal = None,
    #     propertyName: Literal = None,
    #     streamingPropertyConnection: Connection = None,
    #     streamingTopic: Literal = None,
    # ):
    #     super().__init__(uri)
    #     self.assign_constructor_vars(locals())


class TimeseriesProperty(DatabaseProperty):
    class_uri: ClassVar[URIRef] = GRAPH_MODEL.TimeseriesProperty

    mapping: ClassVar[dict] = {
        **DatabaseProperty.mapping,
    }

    # def __init__(
    #     self,
    #     uri: URIRef,
    #     label: Literal = None,
    #     propertyUnit: Literal = None,
    #     propertySemanticID: Literal = None,
    #     propertyDescription: Literal = None,
    #     propertyDataType: Literal = None,
    #     propertyValue: Literal = None,
    #     propertyName: Literal = None,
    #     databasePropertyConnection: Connection = None,
    #     query: Literal = None,
    # ):
    #     super().__init__(uri)
    #     self.assign_constructor_vars(locals())


class File(DatabaseProperty):
    class_uri: ClassVar[URIRef] = GRAPH_MODEL.File

    mapping: ClassVar[dict] = {
        **DatabaseProperty.mapping,
        "fileType": GRAPH_MODEL.fileType,
        "filePath": GRAPH_MODEL.filePath,
    }

    fileType: Literal | str = None
    filePath: Literal | str = None

    # def __init__(
    #     self,
    #     uri: URIRef,
    #     label: Literal = None,
    #     propertyUnit: Literal = None,
    #     propertySemanticID: Literal = None,
    #     propertyDescription: Literal = None,
    #     propertyDataType: Literal = None,
    #     propertyValue: Literal = None,
    #     propertyName: Literal = None,
    #     databasePropertyConnection: Connection = None,
    #     query: Literal = None,
    #     fileType: Literal = None,
    #     filePath: Literal = None,
    # ):
    #     super().__init__(uri)
    #     self.assign_constructor_vars(locals())


class AbstractAsset(RDFModel):
    class_uri: ClassVar[URIRef] = GRAPH_MODEL.AbstractAsset

    mapping: ClassVar[dict] = {
        "assetProperties": GRAPH_MODEL.assetProperties,
        "assetDescription": GRAPH_MODEL.assetDescription,
    }

    assetProperties: List[
        Union[
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
    #     uri: URIRef,
    #     label: Literal = None,
    #     assetProperties: List[
    #         Union[
    #             AbstractAssetProperty,
    #             DatabaseProperty,
    #             StreamingProperty,
    #             TimeseriesProperty,
    #             File,
    #         ]
    #     ] = None,
    #     assetDescription: Literal = None,
    # ):
    #     super().__init__()
    #     self.assign_constructor_vars(locals())


class SINDITKG(RDFModel):
    class_uri: ClassVar[URIRef] = GRAPH_MODEL.SINDITKG

    mapping: ClassVar[dict] = {
        "assets": GRAPH_MODEL.assets,
        "dataConnections": GRAPH_MODEL.dataConnections,
    }

    # :assets :dataConnections
    assets: List[AbstractAsset] = None
    dataConnections: List[Connection] = None

    # def __init__(
    #     self,
    #     uri: URIRef,
    #     label: Literal = None,
    #     assets: List[AbstractAsset] = None,
    #     dataConnections: List[Connection] = None,
    # ):
    #     super().__init__()
    #     self.assign_constructor_vars(locals())


URIClassMapping = {
    Connection.class_uri: Connection,
    AbstractAssetProperty.class_uri: AbstractAssetProperty,
    DatabaseProperty.class_uri: DatabaseProperty,
    StreamingProperty.class_uri: StreamingProperty,
    TimeseriesProperty.class_uri: TimeseriesProperty,
    File.class_uri: File,
    AbstractAsset.class_uri: AbstractAsset,
    SINDITKG.class_uri: SINDITKG,
}

from enum import Enum
from typing import List, Union

from semantic_knowledge_graph.rdf_orm.rdf_model import RDFModel, MapTo
from rdflib import Literal, URIRef, Namespace, Graph
from rdflib.namespace import OWL, RDFS, RDF

from util.environment_and_configuration import (
    get_environment_variable,
    get_environment_variable_int,
)


class GraphNamespace(Enum):
    """Enum for the namespaces used in the graph"""
    SINDIT = Namespace("urn:samm:sindit.sintef.no:1.0.0#")
    SINDIT_KG = Namespace("http://sindit.sintef.no/2.0#")
    SAMM_UNIT = Namespace("urn:samm:org.eclipse.esmf.samm:unit:2.1.0#")
    SAMM = Namespace("urn:samm:org.eclipse.esmf.samm:meta-model:2.1.0#")
    SAMM_CHARACTERISTIC = Namespace("urn:samm:org.eclipse.esmf.samm:characteristic:2.1.0#")


GRAPH_MODEL = GraphNamespace.SINDIT.value


class Connection(RDFModel):
    class_uri = GRAPH_MODEL.Connection

    mapping = {
        "token": GRAPH_MODEL.token,
        "type": GRAPH_MODEL.type,
        "password": GRAPH_MODEL.password,
        "port": GRAPH_MODEL.port,
        "host": GRAPH_MODEL.host,
        "isConnected": GRAPH_MODEL.isConnected,
        "username": GRAPH_MODEL.username,
        "connectionDescription": GRAPH_MODEL.connectionDescription,
    }
    # uri: URIRef
    type: Literal
    host: Literal
    port: Literal
    username: Literal
    password: Literal
    token: Literal
    isConnected: Literal
    connectionDescription: Literal

    def __init__(self,
                 uri: URIRef,
                 label: Literal = None,
                 type: Literal = None,
                 host: Literal = None,
                 port: Literal = None,
                 username: Literal = None,
                 password: Literal = None,
                 token: Literal = None,
                 isConnected: Literal = False,
                 connectionDescription=None
                 ):
        super().__init__()
        self.assign_constructor_vars(locals())


class AbstractAssetProperty(RDFModel):
    class_uri = GRAPH_MODEL.AbstractAssetProperty

    mapping = {
        "propertyUnit": GRAPH_MODEL.propertyUnit,
        "propertySemanticID": GRAPH_MODEL.propertySemanticID,
        "propertyDescription": GRAPH_MODEL.propertyDescription,
        "propertyDataType": GRAPH_MODEL.propertyDataType,
        "propertyValue": GRAPH_MODEL.propertyValue,
        "propertyName": GRAPH_MODEL.propertyName,
    }

    propertyUnit: Literal
    propertySemanticID: Literal
    propertyDescription: Literal
    propertyDataType: Literal
    propertyValue: Literal
    propertyName: Literal

    def __init__(self,
                 uri: URIRef,
                 label: Literal = None,
                 propertyUnit: Literal = None,
                 propertySemanticID: Literal = None,
                 propertyDescription: Literal = None,
                 propertyDataType: Literal = None,
                 propertyValue: Literal = None,
                 propertyName: Literal = None,

                 ):
        super().__init__()
        self.assign_constructor_vars(locals())


class DatabaseProperty(AbstractAssetProperty):
    class_uri = GRAPH_MODEL.DatabaseProperty

    databasePropertyConnection: Connection
    query: Literal

    mapping = {
        **AbstractAssetProperty.mapping,
        "databasePropertyConnection": GRAPH_MODEL.databasePropertyConnection,
        "query": GRAPH_MODEL.query,
    }

    def __init__(self,
                 uri: URIRef,
                 label: Literal = None,
                 propertyUnit: Literal = None,
                 propertySemanticID: Literal = None,
                 propertyDescription: Literal = None,
                 propertyDataType: Literal = None,
                 propertyValue: Literal = None,
                 propertyName: Literal = None,
                 databasePropertyConnection: Connection = None,
                 query: Literal = None,
                 ):
        super().__init__(uri)
        self.assign_constructor_vars(locals())


class StreamingProperty(AbstractAssetProperty):
    class_uri = GRAPH_MODEL.StreamingProperty

    streamingPropertyConnection: Connection
    streamingTopic: Literal

    mapping = {
        **AbstractAssetProperty.mapping,
        "streamingPropertyConnection": GRAPH_MODEL.streamingPropertyConnection,
        "streamingTopic": GRAPH_MODEL.streamingTopic,
    }

    def __init__(self,
                 uri: URIRef,
                 label: Literal = None,
                 propertyUnit: Literal = None,
                 propertySemanticID: Literal = None,
                 propertyDescription: Literal = None,
                 propertyDataType: Literal = None,
                 propertyValue: Literal = None,
                 propertyName: Literal = None,
                 streamingPropertyConnection: Connection = None,
                 streamingTopic: Literal = None,
                 ):
        super().__init__(uri)
        self.assign_constructor_vars(locals())


class TimeseriesProperty(DatabaseProperty):
    class_uri = GRAPH_MODEL.TimeseriesProperty

    mapping = {
        **DatabaseProperty.mapping,
    }

    def __init__(self,
                 uri: URIRef,
                 label: Literal = None,
                 propertyUnit: Literal = None,
                 propertySemanticID: Literal = None,
                 propertyDescription: Literal = None,
                 propertyDataType: Literal = None,
                 propertyValue: Literal = None,
                 propertyName: Literal = None,
                 databasePropertyConnection: Connection = None,
                 query: Literal = None,
                 ):
        super().__init__(uri)
        self.assign_constructor_vars(locals())


class File(DatabaseProperty):
    class_uri = GRAPH_MODEL.File

    mapping = {
        **DatabaseProperty.mapping,
        "fileType": GRAPH_MODEL.fileType,
        "filePath": GRAPH_MODEL.filePath,
    }

    fileType: Literal
    filePath: Literal

    def __init__(self,
                 uri: URIRef,
                 label: Literal = None,
                 propertyUnit: Literal = None,
                 propertySemanticID: Literal = None,
                 propertyDescription: Literal = None,
                 propertyDataType: Literal = None,
                 propertyValue: Literal = None,
                 propertyName: Literal = None,
                 databasePropertyConnection: Connection = None,
                 query: Literal = None,
                 fileType: Literal = None,
                 filePath: Literal = None,
                 ):
        super().__init__(uri)
        self.assign_constructor_vars(locals())


class AbstractAsset(RDFModel):
    class_uri = GRAPH_MODEL.AbstractAsset

    mapping = {
        "assetProperties": GRAPH_MODEL.assetProperties,
        "assetDescription": GRAPH_MODEL.assetDescription,

    }

    assetProperties: List[Union[AbstractAssetProperty,
                                DatabaseProperty, StreamingProperty, TimeseriesProperty, File]]
    assetDescription: Literal

    def __init__(self,
                 uri: URIRef,
                 label: Literal = None,
                 assetProperties: List[Union[AbstractAssetProperty, DatabaseProperty,
                                             StreamingProperty, TimeseriesProperty, File]] = None,
                 assetDescription: Literal = None,
                 ):
        super().__init__()
        self.assign_constructor_vars(locals())


class SINDITKG(RDFModel):
    class_uri = GRAPH_MODEL.SINDITKG

    mapping = {
        "assets": GRAPH_MODEL.assets,
        "dataConnections": GRAPH_MODEL.dataConnections,

    }

    # :assets :dataConnections
    assets: List[AbstractAsset]
    dataConnections: List[Connection]

    def __init__(self,
                 uri: URIRef,
                 label: Literal = None,
                 assets: List[AbstractAsset] = None,
                 dataConnections: List[Connection] = None,
                 ):
        super().__init__()
        self.assign_constructor_vars(locals())

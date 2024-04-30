from rdflib import XSD, Graph, URIRef

from common.semantic_knowledge_graph.GraphDBPersistenceService import (
    GraphDBPersistenceService,
)
from common.semantic_knowledge_graph.SemanticKGPersistenceService import (
    SemanticKGPersistenceService,
)
from knowledge_graph.graph_model import (
    AbstractAsset,
    Connection,
    GraphNamespace,
    StreamingProperty,
    TimeseriesProperty,
)
from knowledge_graph.kg_connector import SINDITKGConnector

if __name__ == "__main__":
    g = Graph()
    g.namespace_manager.bind("sindit", GraphNamespace.SINDIT.value)
    g.namespace_manager.bind("sindit_kg", GraphNamespace.SINDIT_KG.value)
    g.namespace_manager.bind("samm_unit", GraphNamespace.SAMM_UNIT.value)

    fluxdb_connection: Connection = Connection(
        URIRef("http://sindit.sintef.no/2.0#influxdb-connection"),
        type="INFLUXDB",
        host="localhost",
        port=8080,
        username="admin",
        passwordPath="admin",
        tokenPath="abcdef",
        label="InfluxDB Connection",
    )

    mqtt_connection = Connection(
        URIRef("http://sindit.sintef.no/2.0#mqtt-connection"),
        type="MQTT",
        host="localhost",
        port=1883,
        username="admin",
        passwordPath="admin",
        label="MQTT Connection",
    )

    temperature = StreamingProperty(
        URIRef("http://sindit.sintef.no/2.0#temperature"),
        label="Temperature",
        propertyDataType=XSD.float,
        streamingPropertyConnection=mqtt_connection,
        propertyDescription="Temperature data from the sensor",
        streamingTopic="topic/temp",
        propertyUnit=GraphNamespace.SAMM_UNIT.value.degreeCelsius,
    )

    humidity = TimeseriesProperty(
        URIRef("http://sindit.sintef.no/2.0#humidity"),
        label="Humidity",
        propertyDescription="Humidity data from the sensor",
        query="SELECT * FROM humidity",
        propertyUnit=GraphNamespace.SAMM_UNIT.value.percent,
        propertyDataType=XSD.float,
        databasePropertyConnection=fluxdb_connection,
    )

    asset = AbstractAsset(
        URIRef("http://sindit.sintef.no/2.0#factory-sensor"),
        label="Temperature Sensor",
        assetDescription="Sensor in the factory",
        assetProperties=[temperature, humidity],
    )

    # g += fluxdb_connection.g
    # g += temperature.g
    # g += humidity.g
    # g += asset.g

    # print(g.serialize(format="longturtle"))

    # ret = RDFModel.deserialize(
    #     AbstractAsset,
    #     g,
    #     URIRef("http://sindit.sintef.no/2.0#factory-sensor"),
    #     uri_class_mapping=URIClassMapping,
    # )

    # print(ret["http://sindit.sintef.no/2.0#factory-sensor"])

    kg_service: SemanticKGPersistenceService = GraphDBPersistenceService(
        "localhost", "7200", "SINDIT", "sindit20", "sindit20"
    )

    kg_connector = SINDITKGConnector(kg_service)
    # node = kg_connector.load_node("http://sindit.sintef.no/2.0#factory-sensor",
    # AbstractAsset, depth=1)
    # print(node)

    # fluxdb_connection.port = 888888
    # kg_connector.save_node(asset)

    # nodes = kg_connector.load_nodes_by_class(AbstractAsset.class_uri, depth=10)
    # for node in nodes:
    #    print(node)

    # kg_connector.delete_node("http://factory/ABC")

    xyz_connection = Connection(
        URIRef("http://sindit.sintef.no/2.0#xyz-connection"),
        type="MQTT",
        host="localhost",
        port=1883,
        username="admin",
        passwordPath="admin",
        label="MQTT Connection",
    )
    result = kg_connector.save_node(xyz_connection)
    print(result)

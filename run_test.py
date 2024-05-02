from rdflib import XSD, Graph, URIRef

from common.semantic_knowledge_graph.GraphDBPersistenceService import (
    GraphDBPersistenceService,
)
from common.semantic_knowledge_graph.rdf_model import RDFModel
from common.semantic_knowledge_graph.SemanticKGPersistenceService import (
    SemanticKGPersistenceService,
)
from knowledge_graph.graph_model import (
    AbstractAsset,
    Connection,
    GraphNamespace,
    StreamingProperty,
    TimeseriesProperty,
    URIClassMapping,
)

if __name__ == "__main__":
    g = Graph()
    g.namespace_manager.bind("sindit", GraphNamespace.SINDIT.value)
    g.namespace_manager.bind("sindit_kg", GraphNamespace.SINDIT_KG.value)
    g.namespace_manager.bind("samm_unit", GraphNamespace.SAMM_UNIT.value)

    fluxdb_connection: Connection = Connection(
        uri=URIRef("http://sindit.sintef.no/2.0#influxdb-connection"),
        type="INFLUXDB",
        host="localhost",
        port=8080,
        username="admin",
        passwordPath="admin",
        tokenPath="abcdef",
        label="InfluxDB Connection",
    )

    mqtt_connection = Connection(
        uri=URIRef("http://sindit.sintef.no/2.0#mqtt-connection"),
        type="MQTT",
        host="localhost",
        port=1883,
        username="admin",
        passwordPath="admin",
        label="MQTT Connection",
    )

    temperature = StreamingProperty(
        uri=URIRef("http://sindit.sintef.no/2.0#temperature"),
        label="Temperature",
        propertyDataType=XSD.float,
        streamingPropertyConnection=mqtt_connection,
        propertyDescription="Temperature data from the sensor",
        streamingTopic="topic/temp",
        propertyUnit=GraphNamespace.SAMM_UNIT.value.degreeCelsius,
    )

    humidity = TimeseriesProperty(
        uri=URIRef("http://sindit.sintef.no/2.0#humidity"),
        label="Humidity",
        propertyDescription="Humidity data from the sensor",
        query="SELECT * FROM humidity",
        propertyUnit=GraphNamespace.SAMM_UNIT.value.percent,
        propertyDataType=XSD.float,
        databasePropertyConnection=fluxdb_connection,
    )

    asset = AbstractAsset(
        uri=URIRef("http://sindit.sintef.no/2.0#factory-sensor"),
        label="Temperature Sensor",
        assetDescription="Sensor in the factory",
        assetProperties=[temperature, humidity],
    )

    # g += fluxdb_connection.g
    # g += temperature.g
    # g += humidity.g
    g += asset.g()

    # print(g.serialize(format="longturtle"))

    # print(asset)
    # print(asset.model_dump_json(exclude_none=True))

    ret = RDFModel.deserialize(
        g=g,
        node_class=AbstractAsset,
        node_uri=URIRef("http://sindit.sintef.no/2.0#factory-sensor"),
        uri_class_mapping=URIClassMapping,
    )

    # print(ret["http://sindit.sintef.no/2.0#factory-sensor"])

    kg_service: SemanticKGPersistenceService = GraphDBPersistenceService(
        "localhost", "7200", "SINDIT", "sindit20", "sindit20"
    )

    # kg_connector = SINDITKGConnector(kg_service)
    # node = kg_connector.load_node_by_uri(
    #     "http://sindit.sintef.no/2.0#factory-sensor", AbstractAsset, depth=1
    # )
    # node = kg_connector.load_node_by_uri(
    #     "http://sindit.sintef.no/2.0#factory-sensor", AbstractAsset, depth=2
    # )
    # node = kg_connector.load_node_by_uri(
    #     "http://sindit.sintef.no/2.0#factory-sensor", AbstractAsset, depth=3
    # )
    # print(node)

    # fluxdb_connection.port = 888888
    # kg_connector.save_node(asset)

    # nodes = kg_connector.load_nodes_by_class(AbstractAsset.class_uri, depth=10)
    # for node in nodes:
    #    print(node)

    # kg_connector.delete_node("http://factory/ABC")

    xyz_connection = Connection(
        uri=URIRef("http://sindit.sintef.no/2.0#xyz-connection"),
        type="MQTT",
        host="localhost",
        port=1883,
        username="admin",
        passwordPath="admin",
        label="MQTT Connection",
    )

    result = xyz_connection.model_dump_json(exclude_none=True, indent=4)
    # pretty_print(result)
    print(result)
    # result = kg_connector.save_node(xyz_connection)
    # print(result)

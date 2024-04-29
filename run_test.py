from rdflib import XSD, Graph, URIRef

from knowledge_graph.graph_model import (
    AbstractAsset,
    Connection,
    GraphNamespace,
    RDFModel,
    StreamingProperty,
    TimeseriesProperty,
    URIClassMapping,
)

if __name__ == "__main__":
    # kg_service:SemanticKGPersistenceService =
    # GraphDBPersistenceService(
    #   "localhost",
    #   "7200",
    #   "SINDIT",
    #   "sindit20",
    #   "sindit20"
    # )

    # query = "SELECT * WHERE { ?s ?p ?o } LIMIT 10"
    # update = "INSERT DATA {
    #   <http://example/book1>
    #   <http://example.org/pred1>
    #   'value1'
    # }"

    # print(kg_service.graph_update(update))
    g = Graph()
    g.namespace_manager.bind("sindit", GraphNamespace.SINDIT.value)
    g.namespace_manager.bind("sindit_kg", GraphNamespace.SINDIT_KG.value)
    g.namespace_manager.bind("samm_unit", GraphNamespace.SAMM_UNIT.value)

    fluxdb_connection = Connection(
        URIRef("http://sindit.sintef.no/2.0#influxdb-connection"),
        type="INFLUXDB",
        host="localhost",
        port=8080,
        username="admin",
        password="admin",
        token="abcdef",
        label="InfluxDB Connection",
    )

    mqtt_connection = Connection(
        URIRef("http://sindit.sintef.no/2.0#mqtt-connection"),
        type="MQTT",
        host="localhost",
        port=1883,
        username="admin",
        password="admin",
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

    g += fluxdb_connection.g
    g += temperature.g
    g += humidity.g
    g += asset.g

    # Print the global graph object.
    print(g.serialize(format="longturtle"))

    # print(connection.host)
    # print(connection.port)
    # print(connection.isConnected)

    ret = RDFModel.deserialize(
        AbstractAsset,
        g,
        URIRef("http://sindit.sintef.no/2.0#factory-sensor"),
        uri_class_mapping=URIClassMapping,
    )

    print(ret["http://sindit.sintef.no/2.0#factory-sensor"])

    # for key, value in ret.items():
    #    print(f"--------------")
    #    print(key)
    #    print(value)

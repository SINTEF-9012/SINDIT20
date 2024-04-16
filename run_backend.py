from rdflib import XSD, Graph, URIRef
from semantic_knowledge_graph.SemanticKGPersistenceService import SemanticKGPersistenceService
from semantic_knowledge_graph.GraphDBPersistenceService import GraphDBPersistenceService
from semantic_knowledge_graph.graph_model.graph_model import AbstractAsset, Connection, DatabaseProperty, TimeseriesProperty
from semantic_knowledge_graph.graph_model.graph_model import GraphNamespace

if __name__ == "__main__":

    # kg_service:SemanticKGPersistenceService  = GraphDBPersistenceService("localhost", "7200", "SINDIT", "sindit20", "sindit20")

    # query = "SELECT * WHERE { ?s ?p ?o } LIMIT 10"
    # update = "INSERT DATA { <http://example/book1> <http://example.org/pred1> 'value1' }"

    # print(kg_service.graph_update(update))
    g = Graph()
    g.namespace_manager.bind('sindit', GraphNamespace.SINDIT.value)
    g.namespace_manager.bind('sindit_kg', GraphNamespace.SINDIT_KG.value)

    connection = Connection(URIRef("http://sindit.sintef.no/2.0#influxdb-connection"),
                            type="INFLUXDB",
                            host="localhost",
                            port=8080,
                            username="admin",
                            password="admin",
                            # token = "abcdef",
                            label="InfluxDB Connection")

    dbproperty = DatabaseProperty(URIRef("http://sindit.sintef.no/2.0#temperature"),
                                  label="Temperature",
                                  propertyDataType=XSD.float,
                                  databasePropertyConnection=connection,
                                  propertyDescription="Temperature data from the sensor"
                                  )

    timeseries = TimeseriesProperty(URIRef("http://sindit.sintef.no/2.0#temperature-timeseries"),

                                           label="Temperature Timeseries",
                                           query="SELECT * FROM temperature", 
                                           propertyUnit="unit:degreeCelsius",)
    
    asset = AbstractAsset(URIRef("http://sindit.sintef.no/2.0#temperature-sensor"),
                            label="Temperature Sensor",
                            assetDescription="Temperature sensor in the living room",
                            assetProperties=[dbproperty, timeseries])

    dbproperty.query = "SELECT * FROM temperature"

    g += connection.g
    g += dbproperty.g
    g += timeseries.g
    g += asset.g

    # Print the global graph object.
    print(g.serialize(format='longturtle'))

    #print(connection.host)
    #print(connection.port)
    #print(connection.isConnected)

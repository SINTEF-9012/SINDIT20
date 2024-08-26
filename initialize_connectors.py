from knowledge_graph.graph_model import SINDITKG, AbstractAsset, AbstractAssetProperty, Connection, StreamingProperty, URIClassMapping
from common.semantic_knowledge_graph.rdf_model import RDFModel, URIRefNode

from initialize_vault import secret_vault
from initialize_kg_connectors import sindit_kg_connector

from connectors.connector_mqtt import MQTTConnector
from connectors.property_mqtt import MQTTProperty
from util.log import logger

connections = {}
properties = {}



def update_propery_node(node: AbstractAssetProperty):
    #Update only MQTT properties
    node_uri = str(node.uri)
    if node_uri not in properties:
        if isinstance(node, StreamingProperty):
            connection_node = node.streamingPropertyConnection
            if connection_node is not None:
                if isinstance(connection_node, URIRefNode):
                    connection_node = sindit_kg_connector.load_node_by_uri(str(connection_node.uri))
                
                if connection_node is not None and connection_node.type.lower() == "mqtt":
                    connection = update_connection_node(connection_node)
                    if connection is not None:
                        property = MQTTProperty(uri=node_uri, topic=node.streamingTopic, path_or_code=node.streamingPath)
                        property.attach(connection)
                        properties[node_uri] = property
    else:
        property = properties[node_uri]
        if isinstance(property, MQTTProperty):
            if property.topic != node.streamingTopic or property.path_or_code != node.streamingPath:
                property.topic = node.streamingTopic
                property.path_or_code = node.streamingPath
                #property.attach(connection)
                properties[node_uri] = property
    return properties[node_uri]


def update_connection_node(node: Connection):
    
    # Only update the connection if it is of type MQTT
    if str(node.type).lower() == "mqtt":
        try:
            password = secret_vault.get_secret(node.passwordPath)
        except:
            password = None
            
        node_uri = str(node.uri)
        
        try:
            if node_uri not in connections:
                    connection = MQTTConnector(host=node.host, port=node.port, username=node.username, password=password, uri = node_uri)
                    connection.start()
                    connections[node_uri] = connection
            else:
                connection = connections[node_uri]
                if str(connection.host) != str(node.host) or str(connection.port) != str(node.port):
                    connection.stop()
                    connection = MQTTConnector(host=node.host, port=node.port, username=node.username, password=password, uri = node_uri)
                    connection.start()
                    connections[node_uri] = connection
            
            return connection
        except Exception as e:
            logger.error(f"Error updating connection node {node_uri}: {e}")
            return None
    
    return None
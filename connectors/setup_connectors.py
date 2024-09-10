from knowledge_graph.graph_model import (
    AbstractAssetProperty,
    Connection,
    StreamingProperty,
)
from common.semantic_knowledge_graph.rdf_model import URIRefNode


from initialize_kg_connectors import sindit_kg_connector
from initialize_vault import secret_vault
from connectors.connector_mqtt import MQTTConnector
from connectors.property_mqtt import MQTTProperty
from util.log import logger

connections = {}
properties = {}


def update_propery_node(node: AbstractAssetProperty):
    # Update only MQTT properties
    # Warning: connection has to be created before the property.
    # Otherwise, the property will not be attached to the connection
    # or call intialize_connections_and_properties() again
    node_uri = str(node.uri)
    if node_uri not in properties:
        if isinstance(node, StreamingProperty):
            connection_node = node.streamingPropertyConnection
            if connection_node is not None:
                if isinstance(connection_node, URIRefNode):
                    connection_node = sindit_kg_connector.load_node_by_uri(
                        str(connection_node.uri)
                    )

                if (
                    connection_node is not None
                    and connection_node.type.lower() == "mqtt"
                ):
                    connection = update_connection_node(connection_node)
                    if connection is not None:
                        property = MQTTProperty(
                            uri=node_uri,
                            topic=node.streamingTopic,
                            path_or_code=node.streamingPath,
                        )
                        property.attach(connection)
                        properties[node_uri] = property

                        return properties[node_uri]
    else:
        # Warning: connection has to be created before the property.
        # Otherwise, the property will not be attached to the connection
        property = properties[node_uri]
        if isinstance(property, MQTTProperty):
            if (
                property.topic != node.streamingTopic
                or property.path_or_code != node.streamingPath
            ):
                property.topic = str(node.streamingTopic)
                property.path_or_code = str(node.streamingPath)
                # property.attach(connection)
                properties[node_uri] = property

                return properties[node_uri]

    return None


def remove_property_node(node: AbstractAssetProperty):
    node_uri = str(node.uri)
    if node_uri in properties:
        property = properties[node_uri]

        connection = property.connector
        if connection is not None:
            connection.detach(property)
        del properties[node_uri]
        return True
    return False


def remove_connection_node(node: Connection):
    node_uri = str(node.uri)
    if node_uri in connections:
        connection = connections[node_uri]
        for property in connection._observers.values():
            property.connector = None

        connection.stop()
        del connections[node_uri]
        return True
    return False


def update_connection_node(node: Connection):
    # Only update the connection if it is of type MQTT
    if str(node.type).lower() == "mqtt":
        try:
            password = secret_vault.get_secret(node.passwordPath)
        except Exception:
            password = None

        node_uri = str(node.uri)

        try:
            if node_uri not in connections:
                connection = MQTTConnector(
                    host=node.host,
                    port=node.port,
                    username=node.username,
                    password=password,
                    uri=node_uri,
                )
                connections[node_uri] = connection
                connection.start()
            else:
                connection = connections[node_uri]
                # Warning: updating the username and password
                # does not create a new connection
                if str(connection.host) != str(node.host) or str(
                    connection.port
                ) != str(node.port):
                    connection.stop()
                    connection = MQTTConnector(
                        host=node.host,
                        port=node.port,
                        username=node.username,
                        password=password,
                        uri=node_uri,
                    )
                    connections[node_uri] = connection

                    connection.start()
                elif (
                    node.isConnected is None
                    or not node.isConnected
                    or str(node.isConnected).lower() == "false"
                ):
                    connection.stop()
                    connection.start()

            return connection
        except Exception as e:
            logger.error(f"Error updating connection node {node_uri}: {e}")

            # Change the isConnected property to False
            if node is not None:
                node.isConnected = False
                sindit_kg_connector.save_node(node, update_value=True)
            return None

    return None


def initialize_connections_and_properties():
    for node in sindit_kg_connector.load_nodes_by_class(Connection.CLASS_URI):
        update_connection_node(node)

    for node in sindit_kg_connector.load_nodes_by_class(
        AbstractAssetProperty.CLASS_URI
    ):
        update_propery_node(node)

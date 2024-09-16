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
from connectors.connector_influxdb import InfluxDBConnector
from connectors.connector import Connector
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
            connection_node = node.propertyConnection
            if connection_node is not None:
                connection_uri = str(connection_node.uri)

                if isinstance(connection_node, URIRefNode):
                    connection_node = sindit_kg_connector.load_node_by_uri(
                        str(connection_uri)
                    )

                if (
                    connection_node is not None
                    and connection_node.type.lower() == MQTTConnector.id.lower()
                ):
                    if connection_uri not in connections:
                        connection = update_connection_node(connection_node)
                    else:
                        connection = connections[connection_uri]

                    if connection is not None:
                        new_property = MQTTProperty(
                            uri=node_uri,
                            topic=node.streamingTopic,
                            path_or_code=node.streamingPath,
                            kg_connector=sindit_kg_connector,
                        )

                        connection.attach(new_property)
                        # new_property.attach(connection)

                        properties[node_uri] = new_property

                        return properties[node_uri]
    else:
        # Warning: connection has to be created before the property.
        # Otherwise, the property will not be attached to the connection
        property = properties[node_uri]
        if isinstance(property, MQTTProperty) and (
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
        remove_property = properties[node_uri]

        connection = remove_property.connector
        if connection is not None:
            connection.detach(remove_property)
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


def replace_connector(new_connector: Connector, old_connector: Connector):
    if new_connector is not None and old_connector is not None:
        if old_connector._observers is not None:
            for property in old_connector._observers.values():
                new_connector.attach(property)


def create_connector(node: Connection) -> Connector:
    password = None
    token = None
    connector: Connector = None
    node_uri = None

    if node is not None:
        node_uri = str(node.uri)
        try:
            password = secret_vault.resolveSecret(node.passwordPath)
        except Exception:
            # logger.debug(f"Error getting password for {node_uri}: {e}")
            pass

        try:
            token = secret_vault.resolveSecret(node.tokenPath)
        except Exception:
            # logger.debug(f"Error getting token for {node_uri}: {e}")
            pass

        # TODO: Add support for other types of connections here
        if str(node.type).lower() == MQTTConnector.id.lower():
            connector = MQTTConnector(
                host=node.host,
                port=node.port,
                username=node.username,
                password=password,
                uri=node_uri,
                kg_connector=sindit_kg_connector,
            )
        elif str(node.type).lower() == InfluxDBConnector.id.lower():
            connector = InfluxDBConnector(
                host=node.host,
                port=node.port,
                token=token,
                uri=node_uri,
                kg_connector=sindit_kg_connector,
            )

    return connector


def update_connection_node(node: Connection):
    try:
        connector = create_connector(node)
        node_uri = str(node.uri)
        if connector is not None:
            if node_uri in connections:
                old_connector = connections[node_uri]

                try:
                    old_connector.stop()
                except Exception:
                    pass

                replace_connector(connector, old_connector)
                del old_connector

            connections[node_uri] = connector
            connector.start()

            return connector
    except Exception as e:
        logger.error(f"Error updating connection node {node.uri}: {e}")

        # Change the isConnected property to False
        if node is not None:
            node.isConnected = False
            sindit_kg_connector.save_node(node, update_value=True)

    return None


"""     if str(node.type).lower() == MQTTConnector.id:
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
                    kg_connector=sindit_kg_connector,
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
                        kg_connector=sindit_kg_connector,
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

    return None """


def initialize_connections_and_properties():
    for node in sindit_kg_connector.load_nodes_by_class(Connection.CLASS_URI):
        update_connection_node(node)

    for node in sindit_kg_connector.load_nodes_by_class(
        AbstractAssetProperty.CLASS_URI
    ):
        update_propery_node(node)

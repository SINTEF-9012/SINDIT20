from sindit.knowledge_graph.graph_model import (
    AbstractAssetProperty,
    Connection,
)
from sindit.common.semantic_knowledge_graph.rdf_model import URIRefNode
from sindit.initialize_kg_connectors import sindit_kg_connector
from sindit.initialize_vault import secret_vault
from sindit.connectors.connector import Connector
from sindit.connectors.connector import Property
from sindit.util.log import logger

from sindit.connectors.connector_factory import connector_factory, property_factory
from concurrent.futures import ThreadPoolExecutor

# TODO: This is a workaround to avoid circular imports
import sindit.connectors.connector_mqtt  # noqa: F401, E402
import sindit.connectors.connector_influxdb  # noqa: F401, E402
import sindit.connectors.connector_postgresql  # noqa: F401, E402
import sindit.connectors.connector_s3  # noqa: F401, E402
import sindit.connectors.property_mqtt  # noqa: F401, E402
import sindit.connectors.property_influxdb  # noqa: F401, E402
import sindit.connectors.property_postgresql  # noqa: F401, E402
import sindit.connectors.property_s3  # noqa: F401, E402


connections = {}
properties = {}

# Thread pool for async connection starts
_connection_pool = ThreadPoolExecutor(max_workers=10, thread_name_prefix="conn_init")


def update_propery_node(
    node: AbstractAssetProperty, replace: bool = True, async_start: bool = False
) -> Property:
    """
    Update or create a property node.

    Args:
        node: The property node to update
        replace: If True, replace existing property
        async_start: If True, start property operations asynchronously

    Returns:
        The property instance
    """
    if async_start:
        return _update_property_async(node, replace)
    else:
        return _update_property_sync(node, replace)


def _update_property_sync(
    node: AbstractAssetProperty, replace: bool = True
) -> Property:
    """
    Update property synchronously.
    """
    # Warning: connection has to be created before the property.
    # Otherwise, the property will not be attached to the connection
    # or call intialize_connections_and_properties() again
    node_uri = str(node.uri)
    new_property = None

    if replace or node_uri not in properties:
        # Remove the old property if it exists
        if node_uri in properties:
            old_property: Property = properties[node_uri]
            connection = old_property.connector
            if connection is not None:
                connection.detach(old_property)
            del properties[node_uri]
        # Create a new property
        new_property = create_property(node)
        if new_property is not None:
            properties[node_uri] = new_property
        return new_property
    else:
        # In case replace is False
        # Just refresh the connection
        old_property: Property = properties[node_uri]
        connection = old_property.connector
        if connection is None:
            new_property = create_property(node)
            if new_property is not None:
                properties[node_uri] = new_property
                del old_property
                return new_property

        return old_property


def _update_property_async(
    node: AbstractAssetProperty, replace: bool = True
) -> Property:
    """
    Update property asynchronously in a background thread.
    """

    def _update():
        try:
            logger.info(f"Updating property {node.uri} in background...")
            _update_property_sync(node, replace)
            logger.info(f"Property {node.uri} updated successfully")
        except Exception as e:
            logger.error(f"Error updating property {node.uri}: {e}")

    # Submit to the connection pool (reusing for properties too)
    _connection_pool.submit(_update)
    return None  # Async operations don't return the property immediately


def remove_property_node(node: AbstractAssetProperty):
    node_uri = str(node.uri)
    if node_uri in properties:
        remove_property: Property = properties[node_uri]

        connection = remove_property.connector
        if connection is not None:
            connection.detach(remove_property)
        del properties[node_uri]
        return True
    return False


def remove_connection_node(node: Connection):
    node_uri = str(node.uri)
    if node_uri in connections:
        connection: Connector = connections[node_uri]

        connection.observers_lock.acquire()
        try:
            for property in connection._observers.values():
                property.connector = None
        finally:
            connection.observers_lock.release()

        connection.stop()
        connection.cleanup()
        del connections[node_uri]
        return True
    return False


def replace_connector(new_connector: Connector, old_connector: Connector):
    if new_connector is not None and old_connector is not None:
        old_connector.observers_lock.acquire()
        try:
            if old_connector._observers is not None:
                for property in old_connector._observers.values():
                    new_connector.attach(property)
        finally:
            old_connector.observers_lock.release()


# TODO: Add support for other types of properties here
def create_property(node: AbstractAssetProperty) -> Property:
    new_property = None
    if node is not None:
        node_uri = str(node.uri)
        connection_node = node.propertyConnection
        if connection_node is not None:
            connection_uri = str(connection_node.uri)

            if isinstance(connection_node, URIRefNode):
                connection_node: Connection = sindit_kg_connector.load_node_by_uri(
                    connection_uri
                )

            if connection_node is not None:
                if connection_uri not in connections:
                    connection = update_connection_node(connection_node)
                else:
                    connection = connections[connection_uri]
                if connection is not None:
                    """if isinstance(node, StreamingProperty):
                        # Create an MQTT property
                        if connection_node.type.lower() == MQTTConnector.id.lower():
                            new_property = MQTTProperty(
                                uri=node_uri,
                                topic=node.streamingTopic,
                                path_or_code=node.streamingPath,
                                kg_connector=sindit_kg_connector,
                            )

                            connection.attach(new_property)
                    elif isinstance(node, TimeseriesProperty):
                        # Create an InfuxDB property
                        if connection_node.type.lower() == InfluxDBConnector.id.lower():
                            tags = node.timeseriesTags
                            identifiers = node.timeseriesIdentifiers
                            if identifiers is not None and isinstance(
                                identifiers, dict
                            ):
                                if "measurement" in identifiers:
                                    measurement = identifiers["measurement"]
                                if "field" in identifiers:
                                    field = identifiers["field"]
                                if "org" in identifiers:
                                    org = identifiers["org"]
                                if "bucket" in identifiers:
                                    bucket = identifiers["bucket"]

                                new_property = InfluxDBProperty(
                                    uri=node_uri,
                                    field=field,
                                    measurement=measurement,
                                    org=org,
                                    bucket=bucket,
                                    tags=tags,
                                    kg_connector=sindit_kg_connector,
                                )
                                connection.attach(new_property)"""
                    new_property = property_factory.create(
                        key=str(connection_node.type).lower(),
                        uri=node_uri,
                        kg_connector=sindit_kg_connector,
                        node=node,
                    )
                    if new_property is not None:
                        connection.attach(new_property)

    return new_property


# TODO: Add support for other types of connections here
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

        connector = connector_factory.create(
            key=str(node.type).lower(),
            host=node.host,
            port=node.port,
            username=node.username,
            password=password,
            uri=node_uri,
            kg_connector=sindit_kg_connector,
            token=token,
            configuration=node.configuration,
        )

        """ if str(node.type).lower() == MQTTConnector.id.lower():
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
            ) """

    return connector


def update_connection_node(
    node: Connection, replace: bool = True, async_start: bool = False
) -> Connector:
    """
    Update or create a connection node.

    Args:
        node: The connection node to update
        replace: If True, stop and replace existing connection
        async_start: If True, start the connector in a background thread

    Returns:
        The connector instance (may not be started yet if async_start=True)
    """
    try:
        node_uri = str(node.uri)

        # If the connection already exists and replace is False,
        # return the connection
        if node_uri in connections and not replace:
            connector: Connector = connections[node_uri]
            if connector is not None and not connector.is_connected:
                if async_start:
                    _start_connector_async(connector, node)
                else:
                    _start_connector_sync(connector, node)
            return connector

        connector = create_connector(node)
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

            if async_start:
                _start_connector_async(connector, node)
            else:
                _start_connector_sync(connector, node)

            return connector
    except Exception as e:
        logger.error(f"Error updating connection node {node.uri}: {e}")

        # Change the isConnected property to False
        if node is not None:
            node.isConnected = False
            sindit_kg_connector.save_node(node)

    return None


def _start_connector_sync(connector: Connector, node: Connection):
    """Start connector synchronously."""
    try:
        # Stop the connector first to ensure a fresh start
        try:
            connector.stop(no_update_connection_status=True)
        except Exception as e:
            logger.debug(
                f"Could not stop connector {connector.uri} " f"before starting: {e}"
            )

        connector.start()
    except Exception as e:
        logger.error(f"Error starting connector {connector.uri}: {e}")
        node.isConnected = False
        sindit_kg_connector.save_node(node)


def _start_connector_async(connector: Connector, node: Connection):
    """Start connector in a background thread."""

    def _start():
        try:
            logger.info(f"Starting connector {connector.uri} in background...")

            # Stop the connector first to ensure a fresh start
            try:
                connector.stop(no_update_connection_status=True)
            except Exception as e:
                logger.debug(
                    f"Could not stop connector {connector.uri} " f"before starting: {e}"
                )

            connector.start()
            logger.info(f"Connector {connector.uri} started successfully")
        except Exception as e:
            logger.error(f"Error starting connector {connector.uri}: {e}")
            try:
                node.isConnected = False
                sindit_kg_connector.save_node(node)
            except Exception:
                pass

    _connection_pool.submit(_start)


def _iter_nodes_by_class(class_uri: str, batch_size: int = 50):
    """Yield all nodes of a class by paging with skip/limit."""
    skip = 0
    seen = set()
    while True:
        batch = sindit_kg_connector.load_nodes_by_class(
            class_uri, skip=skip, limit=batch_size
        )
        if not batch:
            break

        for node in batch:
            node_uri = str(getattr(node, "uri", ""))
            if node_uri and node_uri not in seen:
                seen.add(node_uri)
                yield node

        got = len(batch)
        if got < batch_size:
            break
        skip += got


def initialize_connections_and_properties(
    replace: bool = True, batch_size: int = 50, async_start: bool = False
):
    """
    Initialize all connections and properties.

    Args:
        replace: If True, replace existing connections
        batch_size: Number of nodes to fetch per batch
        async_start: If True, start connections and properties asynchronously
    """
    # First initialize all connections
    for node in _iter_nodes_by_class(Connection.CLASS_URI, batch_size):
        update_connection_node(node, replace=replace, async_start=async_start)

    # Then initialize all properties
    for node in _iter_nodes_by_class(AbstractAssetProperty.CLASS_URI, batch_size):
        update_propery_node(node, replace=replace, async_start=async_start)

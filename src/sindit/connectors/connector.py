from __future__ import annotations
from abc import ABC, abstractmethod
import threading
from sindit.common.semantic_knowledge_graph.rdf_model import RDFModel, URIRefNode
from sindit.util.log import logger
from sindit.knowledge_graph.kg_connector import SINDITKGConnector


class Connector:
    id: str = None
    _observers: dict = None
    observers_lock = None
    uri: str = None
    kg_connector: SINDITKGConnector = None
    is_connected: bool = False

    def __init__(self):
        self._observers = {}
        self.observers_lock = threading.Lock()

    def attach(self, property: Property) -> None:
        """
        Attach a property to the connector.
        """
        """ if self._observers is None:
            self._observers = {}
        if self.observers_lock is None:
            self.observers_lock = threading.Lock() """

        logger.info(f"Attaching property {property.uri} to connector {self.uri}")
        self.observers_lock.acquire()
        try:
            if property.uri not in self._observers:
                self._observers[property.uri] = property
                property.connector = self
                property.attach(self)
        finally:
            self.observers_lock.release()

    def detach(self, property: Property) -> None:
        """
        Detach a property from the connector.
        """
        logger.info(f"Detaching {property.uri} from {self}")

        self.observers_lock.acquire()
        try:
            if self._observers is not None and property.uri in self._observers:
                del self._observers[property.uri]
        finally:
            self.observers_lock.release()

    def notify(self, **kwargs) -> None:
        """
        Notify all attached properties.
        """
        logger.debug(f"Node {self.uri} notifies all attached properties")
        self.observers_lock.acquire()

        try:
            if self._observers is not None:
                for observer in self._observers.values():
                    try:
                        observer.update_value(self, **kwargs)
                    except Exception as e:
                        logger.error(f"Failed to notify observer {observer.uri}: {e}")

        finally:
            self.observers_lock.release()

    @abstractmethod
    def start(self, **kwargs) -> any:
        """
        Start the connector.
        """
        pass

    @abstractmethod
    def stop(self, **kwargs) -> any:
        """
        Stop the connector.
        """
        pass

    def update_connection_status(self, is_connected: bool) -> None:
        """
        Update the connection status of the connector in the knowledge graph.
        """
        node = None
        try:
            node = self.kg_connector.load_node_by_uri(self.uri)
        except Exception:
            pass
        if node is not None:
            node.isConnected = is_connected
            self.is_connected = is_connected
            self.kg_connector.save_node(node)


class Property(ABC):
    connector: Connector = None
    uri: str = None
    kg_connector: SINDITKGConnector = None

    @abstractmethod
    def update_value(self, connector: Connector, **kwargs) -> None:
        """
        Receive update from connector
        """
        pass

    @abstractmethod
    def attach(self, connector: Connector) -> None:
        """
        Attach a property to the connector.
        """
        pass

    def update_property_value_to_kg(self, uri, value, timestamp):
        if self.kg_connector is not None:
            # Update the knowledge graph with the new value
            node = None
            try:
                node = self.kg_connector.load_node_by_uri(uri)
            except Exception:
                pass

            if node is not None:
                data_type = node.propertyDataType
                node_value = None

                if isinstance(data_type, URIRefNode):
                    data_type = data_type.uri

                if data_type is not None:
                    data_type = str(data_type)

                if isinstance(value, dict):
                    node_value = {}
                    for key, value in value.items():
                        node_value[key] = RDFModel.reverse_to_type(value, data_type)
                else:
                    node_value = RDFModel.reverse_to_type(value, data_type)

                value = node_value

                node.propertyValue = value
                node.propertyValueTimestamp = timestamp
                self.kg_connector.save_node(node)

            logger.debug(
                f"Property {uri} updated with value {value}, " f"timestamp {timestamp}"
            )

            self.value = value

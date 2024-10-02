from __future__ import annotations
from abc import ABC, abstractmethod
from common.semantic_knowledge_graph.rdf_model import RDFModel, URIRefNode
from util.log import logger
from knowledge_graph.kg_connector import SINDITKGConnector


class Connector:
    id: str = None
    _observers: dict = None
    uri: str = None
    kg_connector: SINDITKGConnector = None
    is_connected: bool = False

    def attach(self, property: Property) -> None:
        """
        Attach a property to the connector.
        """
        if self._observers is None:
            self._observers = {}

        logger.info(f"Attaching property {property.uri} to connector {self.uri}")
        if property.uri not in self._observers:
            self._observers[property.uri] = property
            property.connector = self
            property.attach(self)

    def detach(self, property: Property) -> None:
        """
        Detach a property from the connector.
        """
        logger.info(f"Detaching {property.uri} from {self}")

        if self._observers is not None and property.uri in self._observers:
            del self._observers[property.uri]

    def notify(self, **kwargs) -> None:
        """
        Notify all attached properties.
        """
        logger.debug(f"Node {self.uri} notifies all attached properties")
        if self._observers is not None:
            for observer in self._observers.values():
                observer.update_value(self, **kwargs)

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
            self.kg_connector.save_node(node, update_value=True)


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
                self.kg_connector.save_node(node, update_value=True)

            logger.debug(
                f"Property {uri} updated with value {value}, " f"timestamp {timestamp}"
            )

            self.value = value

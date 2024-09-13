from __future__ import annotations
from abc import ABC, abstractmethod
from util.log import logger


class Connector:
    _observers: dict = {}
    uri = None
    kg_connector = None

    def attach(self, property: Property) -> None:
        """
        Attach a property to the connector.
        """
        logger.info(f"Attaching property {property.uri} to connector {self.uri}")
        if property.uri not in self._observers:
            self._observers[property.uri] = property
            property.connector = self

    def detach(self, property: Property) -> None:
        """
        Detach a property from the connector.
        """
        logger.info(f"Detaching {property.uri} from {self}")
        if property.uri in self._observers:
            del self._observers[property.uri]

    def notify(self, **kwargs) -> None:
        """
        Notify all attached properties.
        """
        logger.debug("Notify all attached properties")
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
            self.kg_connector.save_node(node, update_value=True)


class Property(ABC):
    uri = None
    connector = None
    kg_connector = None

    @abstractmethod
    def update_value(self, connector: Connector, **kwargs) -> None:
        """
        Receive update from connector
        """
        pass

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from util.log import logger


class Connector:

    _observers: dict = {}
    uri = None

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
        logger.debug(f"Notify all attached properties")
        for observer in self._observers.values():
            observer.update_value(self, **kwargs)
    
    @abstractmethod        
    def start(self) -> any:
        """
        Start the connector.
        """
        pass
    
    @abstractmethod
    def stop(self) -> any:
        """
        Stop the connector.
        """
        pass


class Property(ABC):

    uri =  None
    connector = None
    
    @abstractmethod
    def update_value(self, connector: Connector, **kwargs) -> None:
        """
        Receive update from connector
        """
        pass
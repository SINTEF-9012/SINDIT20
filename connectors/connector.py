from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from util.log import logger


class Connector:

    _observers: List[Property] = []

    def attach(self, property: Property) -> None:
        """
        Attach a property to the connector.
        """
        logger.debug(f"Attaching {property.uri} to {self}")
        self._observers.append(property)

    def detach(self, property: Property) -> None:
        """
        Detach a property from the connector.
        """
        logger.debug(f"Detaching {property.uri} from {self}")
        self._observers.remove(property)

    def notify(self, **kwargs) -> None:
        """
        Notify all attached properties.
        """
        logger.debug(f"Notify all attached properties")
        for observer in self._observers:
            observer.update(self, **kwargs)


class Property(ABC):

    uri =  None
    
    @abstractmethod
    def update(self, connector: Connector, **kwargs) -> None:
        """
        Receive update from connector
        """
        pass
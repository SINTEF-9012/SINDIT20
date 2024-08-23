
from connectors.connector import Connector, Property
from connectors.connector_mqtt import MQTTConnector
from util.log import logger

class MQTTProperty(Property):
    
    def __init__(self, uri, topic):
        self.topic = topic
        self.uri = uri
        self.timestamp = None
        self.value = None
        
    
    def attach(self, connector: Connector) -> None:
        connector.attach(self)
        connector.subscribe(self.topic)
        logger.debug(f"Attaching {self.uri} to {connector}")
        
    
    def update(self, connector: Connector) -> None:
        mqttConnector: MQTTConnector = connector
        messages = mqttConnector.get_messages()
        if self.topic in messages:
            timestamp= messages[self.topic]["timestamp"]
            value = messages[self.topic]["payload"]
            if self.timestamp != timestamp:
                self.timestamp = timestamp
                self.value = value
                logger.debug(f"Property {self.uri} updated with value {self.value}")
                
                #TODO: Update the knowledge graph with the new value
                
            
            

    
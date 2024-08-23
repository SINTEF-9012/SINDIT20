
import json
from connectors.connector import Connector, Property
from connectors.connector_mqtt import MQTTConnector
from util.log import logger

class MQTTProperty(Property):
    
    def __init__(self, uri, topic, path_or_code):
        self.topic = topic
        self.uri = uri
        self.path_or_code = path_or_code
        self.timestamp = None
        self.value = None
        
        
    
    def attach(self, connector: Connector) -> None:
        connector.attach(self)
        connector.subscribe(self.topic)
        logger.debug(f"Attaching {self.uri} to {connector}")
        
    
    def update_value(self, connector: Connector) -> None:
        mqttConnector: MQTTConnector = connector
        messages = mqttConnector.get_messages()
        if self.topic in messages:
            timestamp= messages[self.topic]["timestamp"]
            value = messages[self.topic]["payload"]
            if self.timestamp != timestamp:
                self.timestamp = timestamp
                #self.value = value
                #logger.debug(f"Property {self.uri} updated with value {self.value}")
                #check if value is a number
                if isinstance(value, (int, float)):
                    self.value = value
                else:
                    extracted_value = self._extract_value_from_json(value, self.path_or_code)
                    if extracted_value is not None:
                        self.value = extracted_value
                        logger.debug(f"Property {self.uri} updated with value {self.value}")
                    else:
                        logger.error(f"Property {self.uri} could not extract value from {value}, using path_or_code {self.path_or_code}")
                #TODO: Update the knowledge graph with the new value
                
    def _extract_value_from_json(self, json_data, path_or_code):
        try:
            if isinstance(json_data, str):
                json_data = json.loads(json_data)
            # Check if the input is a JSON path (slash-separated string)
            if isinstance(path_or_code, str) and '/' in path_or_code:
                keys = path_or_code.split('/')
                value = json_data
                for key in keys:
                    if key in value:
                        value = value[key]
                    else:
                        return None
                return value
            elif path_or_code in json_data:
                return json_data[path_or_code]
            # Otherwise, assume it's a Python code string
            elif isinstance(path_or_code, str):
                # Evaluate the path code within the context
                value = eval(path_or_code, {}, {"data": json_data})
                return value

            else:
                return None
            
        except (KeyError, IndexError, TypeError, NameError) as e:
            # Return None or handle error if path is invalid
            return None
    
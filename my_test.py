from time import sleep
from connectors.connector_mqtt import MQTTConnector
from connectors.property_mqtt import MQTTProperty


if __name__ == "__main__":
    mqtt_connector = MQTTConnector(host="192.168.1.81", port=1883, topic="#")
    mqtt_connector.start()
    
    mqtt_property = MQTTProperty(uri="test_property", topic="i/bme680", path_or_code="data['p']")
    mqtt_property.attach(mqtt_connector)
    
    mqtt_property2 = MQTTProperty(uri="test_property2", topic="i/bme680", path_or_code="data['t']")
    mqtt_property2.attach(mqtt_connector)
    
    mqtt_connector.thread.join()
    
from time import sleep
from connectors.connector_mqtt import MQTTConnector
from connectors.property_mqtt import MQTTProperty
import threading

if __name__ == "__main__":
    mqtt_connector = MQTTConnector(host="192.168.1.81", port=1883, topic="#")
    mqtt_connector.start()
    
    mqtt_property = MQTTProperty(uri="test_property", topic="i/bme680")
    mqtt_property.attach(mqtt_connector)
    
    mqtt_connector.thread.join()
    
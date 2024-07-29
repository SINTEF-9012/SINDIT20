from connectors.connector_mqtt import MQTTConnector

# mock mqtt broker?
# https://stackoverflow.com/questions/73985389/is-there-a-mock-mqtt-broker-for-unit-testing


class TestMQTTConnector:
    def SetUp(self):
        self.mqtt = MQTTConnector()

    def test_mqtt_connector(self):
        assert self.mqtt is not None

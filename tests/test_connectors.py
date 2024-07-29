from connectors.connector_influxdb import InfluxDBConnector
from connectors.connector_mqtt import MQTTConnector

# mock mqtt broker?
# https://stackoverflow.com/questions/73985389/is-there-a-mock-mqtt-broker-for-unit-testing


class TestMQTTConnector:
    def setup_method(self):
        self.mqtt = MQTTConnector()

    def test_init(self):
        """Test default values of MQTTConnector."""
        assert self.mqtt.broker_address == "localhost"
        assert self.mqtt.port == 1883
        assert self.mqtt.topic == "#"
        assert self.mqtt.timeout == 60

    def test_start(self):
        self.mqtt.start()
        assert self.mqtt.thread.is_alive()
        self.mqtt.stop()

    # TODO: mock mqtt broker and test subscribe get_messages


class TestInfluxDBConnector:
    """Test the InfluxDBConnector class."""

    bucket = "test_bucket"

    def setup_method(self):
        self.influx = InfluxDBConnector(bucket=self.bucket)

    def test_init(self):
        """Test default values of InfluxDBConnector."""
        assert self.influx.host == "localhost"
        assert self.influx.port == str(8086)
        assert self.influx.org is None
        assert self.influx.bucket is self.bucket

    def test_set_token(self):
        """Test the set_token method of InfluxDBConnector."""
        token = "my_token"
        self.influx.set_token(token)
        assert self.influx._InfluxDBConnector__token == token

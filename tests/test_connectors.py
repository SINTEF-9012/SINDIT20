import pytest


from connectors.connector_influxdb import InfluxDBConnector
from connectors.connector_mqtt import MQTTConnector


@pytest.mark.gitlab_exempt(reason="not working in gitlab ci/cd pipeline")
class TestMQTTConnector:
    def setup_method(self):
        self.mqtt = MQTTConnector()

    def teardown_method(self):
        self.mqtt.stop()

    def test_init(self):
        """Test default values of MQTTConnector."""
        assert self.mqtt.host == "localhost"
        assert self.mqtt.port == 1883
        assert self.mqtt.topic == "#"
        assert self.mqtt.timeout == 60

    def test_start(self):
        self.mqtt.start()
        assert self.mqtt.thread.is_alive()
        self.mqtt.stop()

    # TODO: mock mqtt broker and test subscribe get_messages
    # I tried to use paho mqtt FakeBroker but it is not working


class TestInfluxDBConnector:
    """Test the InfluxDBConnector class."""

    def setup_method(self):
        self.influx = InfluxDBConnector()

    def test_init(self):
        """Test default values of InfluxDBConnector."""
        assert self.influx.host == "localhost"
        assert self.influx.port == str(8086)
        assert self.influx.org is None

    def test_set_token(self):
        """Test the set_token method of InfluxDBConnector."""
        token = "my_token"
        self.influx.set_token(token)
        assert self.influx._InfluxDBConnector__token == token

    def test_set_bucket(self):
        """Test the set_bucket method of InfluxDBConnector."""
        bucket = "new_bucket"
        self.influx.set_bucket(bucket)
        assert self.influx.bucket == bucket

    def test__check_if_bucket_name_is_set(self):
        """Test the _check_if_bucket_name_is_set method of InfluxDBConnector."""
        with pytest.raises(ValueError):
            self.influx._check_if_bucket_name_is_set()
        self.influx.set_bucket("new_bucket")
        assert self.influx._check_if_bucket_name_is_set()

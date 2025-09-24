import threading


import paho.mqtt.client as mqtt
from sindit.connectors.connector import Connector
from sindit.connectors.connector_factory import ObjectBuilder
from sindit.util.log import logger
from sindit.knowledge_graph.kg_connector import SINDITKGConnector
from sindit.util.datetime_util import (
    get_current_local_time,
)
from sindit.connectors.connector_factory import connector_factory


class MQTTConnector(Connector):
    """A class representing an MQTT connector.

    Args:
        host (str): The address of the MQTT broker.
            Default is "localhost".
        port (int): The port number of the MQTT broker. Default is 1883.
        topic (str): The topic to subscribe to. Default is "#".
        timeout (int): The timeout value for connecting to the MQTT broker.
            Default is 60 seconds.
        username (str): The username for connecting to the MQTT broker.
        password (str): The password for connecting to the MQTT broker.

    Attributes:
        client (mqtt.Client): The MQTT client instance.
        messages (dict): A dictionary to store subscribed messages.
        thread (threading.Thread): The thread for running the MQTT client loop.

    Methods:
        start(): Start the MQTT client and connect to the broker.
            The connection is started in a separate thread.
        stop(): Stop the MQTT client gracefully.
        subscribe(topic=None): Subscribe to a MQTT topic.
        get_messages(): Get the stored messages.

    """

    id: str = "mqtt"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 1883,
        topic: str = "#",
        timeout: int = 60,
        username: str = None,
        password: str = None,
        uri: str = None,
        kg_connector: SINDITKGConnector = None,
    ):
        super().__init__()

        self.host = host
        self.port = int(port)
        self.topic = topic
        self.timeout = timeout
        self.__username = username
        self.__password = password
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self.messages = {}  # Dict to store subscribed messages
        self.thread = None

        self.uri = f"mqtt://{host}:{port}/"
        if uri is not None:
            self.uri = uri

        self.kg_connector = kg_connector

    def start(self, **kwargs):
        """Start the MQTT client and connect to the broker
        in a separate thread."""
        if self.__username and self.__password:
            # set user and pwd if provided
            self.client.username_pw_set(self.__username, self.__password)
        self.client.connect(self.host, self.port, self.timeout)
        self.thread = threading.Thread(target=self.client.loop_forever)
        self.thread.start()

    def stop(self, **kwargs):
        """Stop the MQTT client gracefully."""
        self.client.loop_stop()
        self.client.disconnect()
        if self.thread is not None:
            self.thread.join()
        logger.info("Connector " + self.uri + " stopped")

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        logger.info(
            "Connector "
            + self.uri
            + " connected to "
            + self.host
            + ":"
            + str(self.port)
            + " with result code "
            + str(rc)
        )

        # Update the knowledge graph with the new value
        self.update_connection_status(True)

        # Subscribe to the topic again after reconnection
        self.observers_lock.acquire()
        try:
            if self._observers is not None:
                for property in self._observers.values():
                    self.subscribe(property.topic)
        finally:
            self.observers_lock.release()

    def _on_disconnect(self, client, userdata, disconnect_flags, rc, properties):
        logger.info(
            "Connector "
            + self.uri
            + " disconnected from "
            + self.host
            + ":"
            + str(self.port)
            + " with result code "
            + str(rc)
        )

        # Update the knowledge graph with the new value
        self.update_connection_status(False)

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode("utf-8")
        logger.debug(f"Received message on topic {topic}: {payload}")
        # if payload is number, convert it to float
        try:
            payload = float(payload)
        except ValueError:
            pass

        local_timestamp = get_current_local_time()

        self.messages[topic] = {"timestamp": local_timestamp, "payload": payload}

        # update the properties value
        self.notify()

    def subscribe(self, topic=None):
        """Subscribe to a topic."""
        if topic is None:
            topic = self.topic
        self.client.subscribe(topic)
        logger.debug(f"Subscribed to {topic}")

    def get_messages(self):
        """Get the stored messages.

        Returns:
            dict: A dictionary containing the subscribed messages.
        """
        return self.messages


class MQTTConnectorBuilder(ObjectBuilder):
    """A class for building an MQTT connector instance."""

    def build(
        self, host, port, username, password, uri, kg_connector, **kwargs
    ) -> MQTTConnector:
        connector = MQTTConnector(
            host=host,
            port=port,
            username=username,
            password=password,
            uri=uri,
            kg_connector=kg_connector,
        )
        return connector


connector_factory.register_builder(MQTTConnector.id, MQTTConnectorBuilder())

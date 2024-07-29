import threading
import time

import paho.mqtt.client as mqtt


class MQTTConnector:
    """A class representing an MQTT connector.

    Attributes:
        broker_address (str): The address of the MQTT broker.
            Default is "localhost".
        port (int): The port number of the MQTT broker. Default is 1883.
        topic (str): The topic to subscribe to. Default is "#".
        timeout (int): The timeout value for connecting to the MQTT broker.
            Default is 60 seconds.
        client (mqtt.Client): The MQTT client instance.
        messages (dict): A dictionary to store subscribed messages.
        thread (threading.Thread): The thread for running the MQTT client loop.

    Methods:
        start(): Start the MQTT client and connect to the broker.
            The connection is started in a separate thread.
        stop(): Stop the MQTT client gracefully.
        on_connect(client, userdata, flags, rc):
            Callback function for MQTT client on connect event.
        on_message(client, userdata, msg):
            Callback function for MQTT client on message event.
        subscribe(topic=None): Subscribe to a topic.
        get_messages(): Get the stored messages.

    """

    def __init__(
        self,
        broker_address: str = "localhost",
        port: int = 1883,
        topic: str = "#",
        timeout: int = 60,
    ):
        self.topic = topic
        self.timeout = timeout
        self.port = port
        self.broker_address = broker_address
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.messages = {}  # Dict to store subscribed messages
        self.thread = None

    def start(self):
        """Start the MQTT client and connect to the broker
        in a separate thread."""
        self.client.connect(self.broker_address, self.port, self.timeout)
        self.thread = threading.Thread(target=self.client.loop_forever)
        self.thread.start()

    def stop(self):
        """Stop the MQTT client gracefully."""
        self.client.loop_stop()
        self.client.disconnect()
        if self.thread is not None:
            self.thread.join()

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode("utf-8")
        print(f"Received message on topic {topic}: {payload}")
        if topic not in self.messages:
            self.messages[topic] = {"timestamp": [], "payload": []}
        # if payload is number, convert it to float
        try:
            payload = float(payload)
        except ValueError:
            pass
        self.messages[topic]["payload"].append(payload)
        self.messages[topic]["timestamp"].append(time.time())

    def subscribe(self, topic=None):
        """Subscribe to a topic."""
        if topic is None:
            topic = self.topic
        self.client.subscribe(topic)
        print(f"Subscribed to {topic}")

    def get_messages(self):
        """Get the stored messages.

        Returns:
            dict: A dictionary containing the subscribed messages.
        """
        return self.messages

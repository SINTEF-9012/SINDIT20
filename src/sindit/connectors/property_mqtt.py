import json
from sindit.connectors.connector import Connector, Property
from sindit.connectors.connector_mqtt import MQTTConnector
from sindit.knowledge_graph.graph_model import StreamingProperty

from sindit.util.log import logger
from sindit.knowledge_graph.kg_connector import SINDITKGConnector
from sindit.connectors.connector_factory import ObjectBuilder
from sindit.connectors.connector_factory import property_factory


class MQTTProperty(Property):
    def __init__(
        self, uri, topic, path_or_code, kg_connector: SINDITKGConnector = None
    ):
        self.topic = str(topic)
        self.uri = str(uri)
        self.path_or_code = str(path_or_code)
        self.timestamp = None
        self.value = None
        self.kg_connector = kg_connector

    def attach(self, connector: Connector) -> None:
        # self.connector = connector
        # connector.attach(self)
        connector.subscribe(str(self.topic))
        # logger.debug(f"Attaching property {self.uri} to connector {connector.uri}")

    def update_value(self, connector: Connector, **kwargs) -> None:
        mqtt_connector: MQTTConnector = connector
        messages = mqtt_connector.get_messages()
        if self.topic in messages:
            timestamp = messages[self.topic]["timestamp"]
            value = messages[self.topic]["payload"]
            if self.timestamp != timestamp:
                self.timestamp = timestamp
                # self.value = value
                # logger.debug(f"Property {self.uri} updated with value {self.value}")
                # check if value is a number
                if isinstance(value, (int, float)):
                    self.value = value
                else:
                    extracted_value = self._extract_value_from_json(
                        value, self.path_or_code
                    )
                    if extracted_value is not None:
                        self.value = extracted_value
                        """ logger.debug(
                            f"Property {self.uri} updated with value {self.value}"
                        ) """

                        # Update the knowledge graph with the new value
                        """ node = None
                        try:
                            node = self.kg_connector.load_node_by_uri(self.uri)
                        except Exception:
                            pass
                        if node is not None:
                            data_type = node.propertyDataType
                            node_value = self.value

                            if isinstance(data_type, URIRefNode):
                                data_type = data_type.uri
                            if data_type is not None:
                                data_type = str(data_type)

                                node_value = RDFModel.reverse_to_type(
                                    node_value, data_type
                                )

                            node.propertyValue = node_value
                            node.propertyValueTimestamp = self.timestamp
                            self.kg_connector.save_node(node, update_value=True)
                    else:
                        logger.error(
                            "Property "
                            + str(self.uri)
                            + " could not extract value from "
                            + str(value)
                            + ", using path_or_code "
                            + str(self.path_or_code)
                        ) """
                        self.update_property_value_to_kg(
                            self.uri, self.value, self.timestamp
                        )

    def _extract_value_from_json(self, json_data, path_or_code):
        try:
            if isinstance(json_data, str):
                json_data = json.loads(json_data)
            # Check if the input is a JSON path (slash-separated string)
            if isinstance(path_or_code, str) and "/" in path_or_code:
                keys = path_or_code.split("/")
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

        except (KeyError, IndexError, TypeError, NameError):
            # Return None or handle error if path is invalid
            return None


class MQTTPropertyBuilder(ObjectBuilder):
    def build(self, uri, kg_connector, node, **kwargs) -> MQTTProperty:
        if isinstance(node, StreamingProperty):
            topic = node.streamingTopic
            path_or_code = node.streamingPath

            new_property = MQTTProperty(
                uri=uri,
                topic=topic,
                path_or_code=path_or_code,
                kg_connector=kg_connector,
            )

            return new_property
        else:
            logger.error(
                f"Node {uri} is not a StreamingProperty, cannot create MQTTProperty"
            )
            return None


property_factory.register_builder(MQTTConnector.id, MQTTPropertyBuilder())

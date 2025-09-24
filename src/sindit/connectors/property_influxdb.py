from sindit.knowledge_graph.graph_model import TimeseriesProperty
from sindit.util.log import logger
from sindit.knowledge_graph.kg_connector import SINDITKGConnector
from sindit.connectors.connector import Connector, Property
from sindit.connectors.connector_influxdb import InfluxDBConnector
from datetime import datetime
from sindit.util.datetime_util import (
    convert_to_local_time,
    convert_string_to_local_time,
    get_current_local_time,
)
from sindit.connectors.connector_factory import ObjectBuilder
from sindit.connectors.connector_factory import property_factory


class InfluxDBProperty(Property):
    def __init__(
        self,
        uri,
        field: str | list = None,
        measurement: str = None,
        org: str = None,
        bucket: str = None,
        tags: dict = None,
        kg_connector: SINDITKGConnector = None,
    ):
        self.uri = str(uri)
        self.timestamp = None
        self.value = None
        self.kg_connector = kg_connector

        self.bucket = bucket
        self.org = org
        self.measurement = measurement
        self.field = field
        self.tags = tags

    def update_value(self, connector: Connector, **kwargs) -> None:
        """
        Receive update from connector
        """
        if self.connector is not None:
            influxdb_connector: InfluxDBConnector = connector
            df = influxdb_connector.query_field(
                field=self.field,
                measurement=self.measurement,
                org=self.org,
                bucket=self.bucket,
                tags=self.tags,
                latest=True,
                start=0,
                stop="now()",
            )
            if df is None or df.empty:
                logger.debug(f"No data found for property {self.uri}")
            else:
                if "_time" in df.columns:
                    self.timestamp = df["_time"].iloc[0]
                    self.timestamp = self.timestamp.to_pydatetime()
                else:
                    self.timestamp = get_current_local_time()

                try:
                    if isinstance(self.timestamp, datetime):
                        self.timestamp = convert_to_local_time(self.timestamp)
                    else:
                        self.timestamp = convert_string_to_local_time(
                            str(self.timestamp)
                        )
                except Exception as e:
                    self.timestamp = get_current_local_time()
                    logger.error(f"Error converting timestamp to datetime: {e}")

                self.value = None
                if self.field is not None:
                    if isinstance(self.field, list):
                        # set value to a dictionary of field values
                        self.value = {}
                        for field in self.field:
                            self.value[field] = df[field].values[0]

                    elif isinstance(self.field, str):
                        self.value = df[self.field].values[0]
                elif "_value" in df.columns:
                    self.value = df["_value"].values[0]

                # Update the knowledge graph with the new value
                """ node = None
                try:
                    node = self.kg_connector.load_node_by_uri(self.uri)
                except Exception:
                    pass

                if node is not None:
                    data_type = node.propertyDataType
                    node_value = None

                    if isinstance(data_type, URIRefNode):
                        data_type = data_type.uri

                    if data_type is not None:
                        data_type = str(data_type)

                    if isinstance(self.value, dict):
                        node_value = {}
                        for key, value in self.value.items():
                            node_value[key] = RDFModel.reverse_to_type(value, data_type)
                    else:
                        node_value = RDFModel.reverse_to_type(self.value, data_type)

                    self.value = node_value

                    node.propertyValue = self.value
                    node.propertyValueTimestamp = self.timestamp
                    self.kg_connector.save_node(node, update_value=True)

                logger.debug(
                    f"Property {self.uri} updated with value {self.value}, "
                    f"timestamp {self.timestamp}"
                ) """
                self.update_property_value_to_kg(self.uri, self.value, self.timestamp)

    def attach(self, connector: Connector) -> None:
        """
        Attach a property to the connector.
        """
        pass


class InfluxDBPropertyBuilder(ObjectBuilder):
    def build(self, uri, kg_connector, node, **kwargs) -> InfluxDBProperty:
        if isinstance(node, TimeseriesProperty):
            tags = node.timeseriesTags
            identifiers = node.timeseriesIdentifiers
            if identifiers is not None and isinstance(identifiers, dict):
                if "measurement" in identifiers:
                    measurement = identifiers["measurement"]
                if "field" in identifiers:
                    field = identifiers["field"]
                if "org" in identifiers:
                    org = identifiers["org"]
                if "bucket" in identifiers:
                    bucket = identifiers["bucket"]

                new_property = InfluxDBProperty(
                    uri=uri,
                    field=field,
                    measurement=measurement,
                    org=org,
                    bucket=bucket,
                    tags=tags,
                    kg_connector=kg_connector,
                )

                return new_property
        else:
            logger.error(
                (
                    f"Node {node.uri} is not a TimeseriesProperty, "
                    "cannot create InfluxDBProperty"
                )
            )
            return None


property_factory.register_builder(InfluxDBConnector.id, InfluxDBPropertyBuilder())

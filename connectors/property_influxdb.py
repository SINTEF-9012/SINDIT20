from util.log import logger
from knowledge_graph.kg_connector import SINDITKGConnector
from connectors.connector import Connector, Property
from connectors.connector_influxdb import InfluxDBConnector
from common.semantic_knowledge_graph.rdf_model import RDFModel, URIRefNode
from datetime import datetime


class InfluxDBProperty(Property):
    def __init__(
        self,
        uri, 
        field: str | list = None,
        measurement: str = None,
        org: str = None,
        bucket: str = None,
        tags: dict = None,
        kg_connector: SINDITKGConnector = None
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
            if df is not None and not df.empty:
                #set the timestamp (_time) 
                self.timestamp = df["_time"].values[0]
                #convert timestamp to datetime
                if not isinstance(self.timestamp, datetime):
                    try:
                        self.timestamp = datetime.fromisoformat(str(self.timestamp))
                    except Exception as e:
                        logger.error(f"Error converting timestamp to datetime: {e}")
                        pass

                self.value = None
                if self.field is not None:
                    if isinstance(self.field, list):
                        #set value to a dictionary of field values
                        self.value = {}
                        for field in self.field:
                            self.value[field] = df[field].values[0]
                            
                    elif isinstance(self.field, str):
                        self.value = df[self.field].values[0]
                elif "_value" in df.columns:
                    self.value = df["_value"].values[0]

                # Update the knowledge graph with the new value
                node = None
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
                            node_value[key] = RDFModel.reverse_to_type(
                                value, data_type
                            )
                    else:
                        node_value = RDFModel.reverse_to_type(
                            self.value, data_type
                        )

                    self.value = node_value

                    node.propertyValue = self.value
                    node.propertyValueTimestamp = self.timestamp
                    self.kg_connector.save_node(node, update_value=True)

                logger.debug(
                    f"Property {self.uri} updated with value {self.value}, "
                    f"timestamp {self.timestamp}"
                )


    def attach(self, connector: Connector) -> None:
        """
        Attach a property to the connector.
        """
        pass

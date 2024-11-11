from connectors.connector import Property
from connectors.connector_factory import ObjectBuilder
from connectors.connector_factory import property_factory
from knowledge_graph.kg_connector import SINDITKGConnector
from knowledge_graph.graph_model import S3ObjectProperty
from connectors.connector_s3 import S3Connector
from util.datetime_util import get_current_local_time, add_seconds_to_timestamp
from util.log import logger


class S3Property(Property):
    def __init__(
        self,
        uri: str,
        bucket: str,
        key: str,
        expiration: int = 3600,
        kg_conenctor: SINDITKGConnector = None,
    ):
        self.uri = str(uri)
        self.bucket = str(bucket)
        self.key = str(key)
        self.timestamp = None
        self.value = None
        self.kg_conenctor = kg_conenctor
        self.expiration = expiration

    def attach(self, connector: S3Connector) -> None:
        """Attach the property to S3Connector"""
        pass

    def _value_has_expired(self) -> bool:
        """
        Check if S3 value (presigned download url) has expired.
        If timestamp does not exist, the value has never been created before;
        then return True.
        If timestamp does exist. Check the expiration of the presigned url.
        """
        if self.timestamp is None:
            return True
        else:
            expiration_time = add_seconds_to_timestamp(
                timestamp=self.timestamp, seconds=self.expiration
            )
            if get_current_local_time() > expiration_time:
                return True
            else:
                return False

    def update_value(self, connector: S3Connector, **kwargs) -> None:
        """update the property value and timestamp"""
        if self.connector is not None:
            s3_connector: S3Connector = connector
            if self._value_has_expired():
                self.value = s3_connector.create_presigned_url_for_download_object(
                    bucket=self.bucket, key=self.key, expiration=self.expiration
                )
                timestamp = get_current_local_time()
                if self.timestamp != timestamp:
                    self.timestamp = timestamp
            self.update_property_value_to_kg(self.uri, self.value, self.timestamp)


class S3PropertyBuilder(ObjectBuilder):
    def build(self, uri, kg_connector, node, **kwargs) -> S3Property:
        if isinstance(node, S3ObjectProperty):
            bucket = node.bucket
            key = node.key
            expiration = node.expiration

            new_property = S3Property(
                uri=uri,
                bucket=bucket,
                key=key,
                expiration=expiration,
                kg_connector=kg_connector,
            )

            return new_property
        else:
            logger.error(
                f"Node {uri} is not a S3ObjectProperty, cannot create S3Property"
            )
            return None


property_factory.register_builder(S3Connector.id, S3PropertyBuilder())

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
        kg_connector: SINDITKGConnector = None,
    ):
        self.uri = str(uri)
        self.bucket = str(bucket)
        self.key = str(key)
        self.timestamp = None
        self.value = None
        self.kg_connector = kg_connector
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
            expiration_time = self._get_expiration_time()
            if get_current_local_time() > expiration_time:
                return True
            else:
                return False

    def _get_expiration_time(self) -> str:
        expiration_time = add_seconds_to_timestamp(
            timestamp=self.timestamp, seconds=self.expiration
        )
        return expiration_time

    def _bucket_exists(self, connector: S3Connector) -> bool:
        """Check if the bucket exists in the S3 storage"""
        if self.connector is not None:
            s3_connector: S3Connector = connector
            response = s3_connector.list_buckets()
            buckets = response["Buckets"]
            if len(buckets) > 0:
                if self.bucket in [x["Name"] for x in buckets]:
                    return True
                else:
                    return False
            else:
                return False

    def _key_exists(self, connector: S3Connector) -> bool:
        """Check if the key/object exists in the S3 storage"""
        if self.connector is not None:
            s3_connector: S3Connector = connector
            try:
                response = s3_connector.list_objects(bucket=self.bucket)
                try:
                    content = response["Contents"]
                    if self.key in [x["Key"] for x in content]:
                        return True
                except KeyError:
                    return False
            except Exception:
                logger.debug("Bucket does probably not exist")
                return False

    def update_value(self, connector: S3Connector, **kwargs) -> None:
        """update the property value and timestamp"""
        logger.debug(f"Updating S3 property value {self.uri}")
        if self.connector is None:
            logger.error("No connector attached to the property")
        else:
            s3_connector: S3Connector = connector
            if self.timestamp is None:
                # This is the first time the property is being created!
                # 1 Check if the bucket exists. If not, create it.
                # 2 Check if the key exists.
                #    If not, create and return presigned url for upload.
                #    If yes
                #          check if key/object/value presigned url has expired
                #               If yes
                #                   return presigned url for download.
                #               If no
                #                   existing presigned value is still valid. Do nothing.

                if not self._bucket_exists(s3_connector):
                    s3_connector.create_bucket(self.bucket)
                if not self._key_exists(s3_connector):
                    self.value = s3_connector.create_presigned_url_for_upload_object(
                        bucket=self.bucket, key=self.key, expiration=self.expiration
                    )
                    self.timestamp = get_current_local_time()
                else:
                    if self._value_has_expired():
                        self.value = s3_connector.create_presigned_url_for_download_object(  # noqa E501
                            bucket=self.bucket, key=self.key, expiration=self.expiration
                        )
                        timestamp = get_current_local_time()
                        if self.timestamp != timestamp:
                            self.timestamp = timestamp
                    else:
                        logger.debug(
                            f"""S3 property value has not expired.
                            Time: {self.timestamp}
                            Expires: {self._get_expiration_time()}"""
                        )
                        pass
            self.update_property_value_to_kg(self.uri, self.value, self.timestamp)


class S3PropertyBuilder(ObjectBuilder):
    def build(self, uri, kg_connector, node, **kwargs) -> S3Property:
        if isinstance(node, S3ObjectProperty):
            bucket = node.bucket
            key = node.key
            if node.expiration is None:
                expiration = 3600
            else:
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

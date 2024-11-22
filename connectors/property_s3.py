from connectors.connector import Property
from connectors.connector_factory import ObjectBuilder
from connectors.connector_factory import property_factory
from knowledge_graph.graph_model import S3ObjectProperty
from knowledge_graph.kg_connector import SINDITKGConnector
from connectors.connector_s3 import S3Connector
from util.datetime_util import get_current_local_time, add_seconds_to_timestamp
from util.log import logger
import threading
import time


class S3Property(Property):
    """
    S3 Property class to manage S3 object storage properties.

    Parameters:
        param: uri: str: URI of the property
        param: bucket: str: S3 bucket name
        param: key: str: S3 object key
        param: expiration: int: Expiration time in seconds for the presigned url
        param: kg_connector: SINDITKGConnector: Knowledge Graph connector
    """

    def __init__(
        self,
        uri: str,
        bucket: str,
        key: str,
        expiration: int = None,
        kg_connector: SINDITKGConnector = None,
    ):
        self.uri = str(uri)
        self.bucket = str(bucket)
        self.key = str(key)
        self.timestamp = None
        self.value = None
        self.kg_connector = kg_connector
        self.thread = None
        self._stop_thread_flag = threading.Event()
        self.create_download_url = None
        self.refresh_download_url = 5
        if expiration is not None:
            self.expiration = expiration
        else:
            self.expiration = 3600

    def __del__(self):
        self.stop_thread()

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
        """
        Check if the bucket exists in the S3 storage
        """
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
        """
        Check if the key/object exists in the S3 storage
        """
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

    def attach(self, connector: S3Connector) -> None:
        """
        Attach the property to S3Connector
        """
        # use the update_value method to set the value and timestamp
        if connector is not None:
            # This will overwrite the expiration with the connector expiration!
            self.expiration = connector.expiration

        logger.debug(
            f"""Attaching S3 property {self.uri} to
            S3 connector {connector.uri}"""
        )
        self.update_value(connector)

    def _update_value_upload_url(self, connector: S3Connector) -> None:
        """
        Update the upload url in a separate thread until it becomes a download url!
        """
        upload_url_expires = self.refresh_download_url * 60
        while self.create_download_url and not self._stop_thread_flag.is_set():
            # 1. Create the presigned url for upload
            logger.debug("Creating presigned url for upload")
            self.value = connector.create_presigned_url_for_upload_object(
                bucket=self.bucket, key=self.key, expiration=upload_url_expires
            )
            self.timestamp = get_current_local_time()
            # 2. update kg values accordingly
            self.update_property_value_to_kg(self.uri, self.value, self.timestamp)
            # 3. await for the refresh_download_url time
            time.sleep(self.refresh_download_url)
            # 4 Check if the key exists.
            if self._key_exists(connector):
                self.create_download_url = False
                logger.debug("Key exists. Break the loop")
                break
            else:
                logger.debug("Key does not exist. Continue refreshing presigned url")
                continue

        if self.create_download_url is False:
            logger.debug("Key exists. Update value to a download url")
            self._update_value_download_url(connector)

    def _stop_thread(self):
        """
        Stop the thread gracefully.
        """
        if self.thread is not None:
            self._stop_thread_flag.set()
            self.thread.join()
            self.thread = None

    def _update_value_download_url(self, connector: S3Connector) -> None:
        """
        Update the download url in the property
        """
        logger.debug(f"Updating S3 property download url {self.uri}")
        self.value = connector.create_presigned_url_for_download_object(
            bucket=self.bucket, key=self.key, expiration=self.expiration
        )
        self.timestamp = get_current_local_time()
        logger.debug(f"value: {self.value}")
        self.update_property_value_to_kg(self.uri, self.value, self.timestamp)

    def update_value(self, connector: S3Connector, **kwargs) -> None:
        """
        Update the property value and timestamp
        """
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
                    # TODO: create thread to update value until becomes a download url
                    self.create_download_url = True
                    self.thread = threading.Thread(
                        target=self._update_value_upload_url, args=(s3_connector,)
                    )
                    self.thread.daemon = True
                    self.thread.start()
                else:
                    if self._value_has_expired():
                        self._update_value_download_url(s3_connector)
                    else:
                        logger.debug(
                            f"""S3 property value has not expired.
                            Time: {self.timestamp}
                            Expires: {self._get_expiration_time()}"""
                        )


class S3PropertyBuilder(ObjectBuilder):
    def build(self, uri, kg_connector, node, **kwargs) -> S3Property:
        if isinstance(node, S3ObjectProperty):
            bucket = node.bucket
            key = node.key

            new_property = S3Property(
                uri=uri,
                bucket=bucket,
                key=key,
                kg_connector=kg_connector,
            )
            return new_property
        else:
            logger.error(
                f"Node {uri} is not a S3ObjectProperty, cannot create S3Property"
            )
            return None


property_factory.register_builder(S3Connector.id, S3PropertyBuilder())

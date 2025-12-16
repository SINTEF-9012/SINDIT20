from sindit.connectors.connector import Property
from sindit.connectors.connector_factory import ObjectBuilder
from sindit.connectors.connector_factory import property_factory
from sindit.knowledge_graph.graph_model import S3ObjectProperty
from sindit.knowledge_graph.kg_connector import SINDITKGConnector
from sindit.connectors.connector_s3 import S3Connector
from sindit.util.datetime_util import get_current_local_time
from sindit.util.log import logger
import threading


# Shared upload polling mechanism
class S3UploadPoller:
    """
    Singleton class to poll for S3 uploads across all S3 properties.
    Uses a single thread to check all properties waiting for uploads.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._properties = {}  # {uri: S3Property}
        self._thread = None
        self._stop_event = threading.Event()
        self._poll_interval = 10  # seconds

    def register(self, property_obj):
        """Register a property for upload polling."""
        with self._lock:
            self._properties[property_obj.uri] = property_obj
            if self._thread is None or not self._thread.is_alive():
                self._start_polling()

    def unregister(self, property_uri):
        """Unregister a property from upload polling."""
        with self._lock:
            if property_uri in self._properties:
                del self._properties[property_uri]
            # Stop thread if no properties to monitor
            if not self._properties and self._thread is not None:
                self._stop_event.set()

    def _start_polling(self):
        """Start the polling thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._poll_loop, name="s3_upload_poller", daemon=True
        )
        self._thread.start()
        logger.info("Started shared S3 upload polling thread")

    def _poll_loop(self):
        """Main polling loop."""
        while not self._stop_event.is_set():
            self._check_uploads()
            self._stop_event.wait(self._poll_interval)

    def _check_uploads(self):
        """Check all registered properties for upload completion."""
        with self._lock:
            properties_to_check = list(self._properties.values())

        if properties_to_check:
            logger.debug(
                f"Polling {len(properties_to_check)} S3 properties "
                f"for upload completion"
            )

        for prop in properties_to_check:
            try:
                if prop.connector is None:
                    continue

                logger.debug(f"Checking upload status for {prop.bucket}/{prop.key}")

                if prop._key_exists(prop.connector):
                    logger.info(
                        f"Upload detected for {prop.bucket}/{prop.key}, "
                        f"switching to download mode"
                    )
                    prop.create_download_url = False
                    prop._generate_download_url(prop.connector)
                    self.unregister(prop.uri)
            except Exception as e:
                logger.error(f"Error checking upload for {prop.uri}: {e}")


# Global poller instance
_upload_poller = S3UploadPoller()


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
        self.create_download_url = None
        if expiration is not None:
            self.expiration = expiration
        else:
            self.expiration = 3600

    def cleanup(self, delete_s3_object: bool = True):
        """
        Cleanup resources when property is detached.
        Unregisters from the upload poller.

        Args:
            delete_s3_object: If True, also delete the S3 object from storage
                            (default: True)
        """
        logger.debug(f"Cleaning up S3 property {self.uri}")
        _upload_poller.unregister(self.uri)
        self.create_download_url = False

        # Optionally delete the S3 object
        if delete_s3_object and self.connector is not None:
            try:
                logger.info(f"Deleting S3 object {self.bucket}/{self.key}")
                self.connector.delete_object(bucket=self.bucket, key=self.key)
            except Exception as e:
                logger.error(
                    f"Failed to delete S3 object {self.bucket}/{self.key}: {e}"
                )

    def __del__(self):
        """
        Destructor to cleanup resources during garbage collection.
        Only unregisters from poller - does NOT delete S3 object.
        S3 object deletion should be explicit via cleanup() or detach().
        """
        _upload_poller.unregister(self.uri)

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

    def _update_url_mode(self, mode: str) -> None:
        """
        Update the urlMode field in the knowledge graph.

        Args:
            mode: Either "upload" or "download"
        """
        if self.kg_connector is None:
            return

        try:
            node = self.kg_connector.load_node_by_uri(self.uri)
            if node is not None:
                node.urlMode = mode
                self.kg_connector.save_node(node)
                logger.debug(f"Updated urlMode to '{mode}' for {self.uri}")
        except Exception as e:
            logger.error(f"Failed to update urlMode for {self.uri}: {e}")

    def _generate_upload_url(self, connector: S3Connector) -> None:
        """
        Generate a presigned upload URL.
        Uses PUT method which is simpler than POST (no form fields policy issues).
        """
        logger.debug(f"Creating presigned upload URL for {self.uri}")

        # Use PUT method (use_post=False) for simpler uploads
        self.value = connector.create_presigned_url_for_upload_object(
            bucket=self.bucket,
            key=self.key,
            expiration=self.expiration,
            use_post=False,  # Use PUT instead of POST
        )
        self.timestamp = get_current_local_time()
        self.update_property_value_to_kg(self.uri, self.value, self.timestamp)
        self._update_url_mode("upload")

    def _generate_download_url(self, connector: S3Connector) -> None:
        """
        Generate a presigned download URL.
        """
        logger.debug(f"Creating presigned download URL for {self.uri}")
        self.value = connector.create_presigned_url_for_download_object(
            bucket=self.bucket, key=self.key, expiration=self.expiration
        )
        self.timestamp = get_current_local_time()
        self.update_property_value_to_kg(self.uri, self.value, self.timestamp)
        self._update_url_mode("download")

    def update_value(self, connector: S3Connector, **kwargs) -> None:
        """
        Update the property value and timestamp.

        This method is called periodically by the connector's notify().
        It generates fresh presigned URLs when needed.

        1) Checks if the bucket exists, if not creates it
        2) If key doesn't exist: generates upload URL and starts polling thread
        3) If key exists: generates download URL
        """
        logger.debug(f"Updating S3 property value {self.uri}")
        if self.connector is None:
            logger.error("No connector attached to the property")
            return

        s3_connector: S3Connector = connector

        # Check if client is ready (connector might still be starting)
        if not hasattr(s3_connector, "client") or s3_connector.client is None:
            logger.warning(
                f"S3 connector {s3_connector.uri} not ready yet, "
                f"skipping property update for {self.uri}"
            )
            return

        # Ensure bucket exists
        if not self._bucket_exists(s3_connector):
            logger.debug(f"Bucket does not exist, creating bucket for {self.uri}")
            s3_connector.create_bucket(self.bucket)

        # Check if file exists
        if not self._key_exists(s3_connector):
            # File not uploaded yet - generate upload URL
            logger.debug(f"Key does not exist, generating upload URL for {self.uri}")
            self._generate_upload_url(s3_connector)

            # Register with shared poller if not already registered
            if self.create_download_url is None:
                self.create_download_url = True
                _upload_poller.register(self)
                logger.debug(f"Registered {self.uri} with shared upload poller")
        else:
            # File exists - generate download URL
            logger.debug(f"Key exists, generating download URL for {self.uri}")
            self._generate_download_url(s3_connector)

            # Unregister from poller if registered
            if self.create_download_url:
                _upload_poller.unregister(self.uri)
                self.create_download_url = False
                logger.debug(f"Unregistered {self.uri} from upload poller")


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
                f"Node {uri} is not a S3ObjectProperty, " f"cannot create S3Property"
            )
            return None


property_factory.register_builder(S3Connector.id, S3PropertyBuilder())

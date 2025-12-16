from sindit.connectors.connector import Connector
from sindit.connectors.connector_factory import ObjectBuilder, connector_factory
from sindit.knowledge_graph.kg_connector import SINDITKGConnector
from sindit.util.log import logger
import boto3
from botocore.exceptions import ClientError
import threading


class S3Connector(Connector):
    """S3 Object Storage Connector.

    To use S3Connector as standalone class without a running backend;
    * make sure to pass argument "no_update_connection_status"
      to start and stop methods:
        s3.start(no_update_connection_status=True)
        s3.stop(no_update_connection_status=True)

    Parameters:
        host: str: S3 server hostname
        port: int: S3 server port
        access_key_id: str: S3 access key id
        secret_access_key: str: S3 secret access key
        region_name: str: S3 region name (optional)
        secure: bool: Use HTTPS if True, HTTP if False (default: False)
        expiration: int: Expiration time in seconds for the presigned url
        uri: str: URI of the connector (identifier for the connector instance)
    """

    id: str = "s3"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9000,
        access_key_id: str = "minioadmin",
        secret_access_key: str = "minioadmin",
        region_name: str = None,
        secure: bool = False,
        expiration: int = 3600,
        uri: str = None,
        kg_connector: SINDITKGConnector = None,
    ):
        super().__init__()
        self.thread = None
        self._stop_event = threading.Event()
        self.region_name = region_name
        self.secure = secure
        self.kg_connector = kg_connector
        # Convert port to int if it's a string
        if isinstance(port, str):
            try:
                port = int(port) if port else 0
            except ValueError:
                port = 0

        # if port is 443 set secure to True.
        secure = True if port == 443 else False
        # Construct endpoint URL with proper protocol scheme
        protocol = "https" if secure else "http"
        # Omit port if it's the default port for the protocol or 0/None
        default_port = 443 if secure else 80
        # Set the endpoint_url
        if port is None or port == 0 or port == default_port:
            self.endpoint_url = f"{protocol}://{host}"
        else:
            self.endpoint_url = f"{protocol}://{host}:{port}"
        # Set the s3 connection secrets
        if access_key_id is None:
            self.__access_key_id = "minioadmin"
        else:
            self.__access_key_id = access_key_id
        if secret_access_key is None:
            self.__secret_access_key = "minioadmin"
        else:
            self.__secret_access_key = secret_access_key
        # Set the URI of this instance of the connector
        if uri is not None:
            self.uri = uri
        else:
            self.uri = f"s3://{host}:{port}"
        # Set the S3 connection expiration time
        if expiration is not None:
            self.expiration = expiration
        else:
            self.expiration = 3600

    def _set_connection_status(self, connected: bool, **kwargs):
        """
        Set the connection status.
        """
        if kwargs.get("no_update_connection_status"):
            logger.debug("no update connection status")
            pass
        else:
            if connected:
                logger.info("connected to s3")
                self.update_connection_status(True)
            else:
                logger.error("could not connect to s3")
                self.update_connection_status(False)

    def start(self, **kwargs):
        """
        Start the S3 client.
        """
        logger.debug("Starting s3 connector client...")
        logger.debug(f"Endpoint URL: {self.endpoint_url}")
        logger.debug(f"Region: {self.region_name}")
        logger.debug(f"Secure: {self.secure}")

        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.__access_key_id,
            aws_secret_access_key=self.__secret_access_key,
            region_name=self.region_name,
            verify=True,  # SSL certificate verification
        )
        try:
            self.client.list_buckets()
            self._set_connection_status(True, **kwargs)
            self.thread = threading.Thread(
                target=self.update_property, name="connector_s3"
            )
            self.thread.daemon = True
            self.thread.start()
        except Exception as e:
            logger.error(f"error starting s3 connector client: {e}")
            self._set_connection_status(False, **kwargs)

    def stop(self, **kwargs):
        """
        Stop the S3 client.
        """
        if self.client is not None:
            self.client.close()
        self._set_connection_status(False, **kwargs)
        if self.thread is not None:
            self._stop_event.set()
            self.thread.join()
            self.thread = None
        logger.info(f"S3 connector {self.uri} stopped")

    def list_buckets(self):
        """
        List all buckets in the S3 storage.
        """
        response = self.client.list_buckets()
        return response

    def list_objects(self, bucket: str):
        """
        List all objects in a bucket.
        """
        response = self.client.list_objects_v2(Bucket=bucket)
        return response

    def get_object(self, bucket: str, key: str):
        """
        Get information about an object.
        """
        response = self.client.get_object(Bucket=bucket, Key=key)
        return response

    def put_object(self, bucket: str, key: str, data: bytes):
        """Put an object into a bucket.
        The data is the file data to upload.
            :param bucket: string
            :param key: string
            :param data: bytes
        bucket is the name of the bucket to upload the file to.
        The key is the path/filename of the object inside the bucket.
        For example key='random/path/to/file/image.jpg'.
        Example of usage:
        with open('test.jpg', 'rb') as data:
            s3.put_object(bucket='my-bucket', Key='test.jpg', Body=data)
        """
        response = self.client.put_object(Bucket=bucket, Key=key, Body=data)
        return response

    def delete_object(self, bucket: str, key: str):
        """
        Delete an object from a bucket.
        """
        response = self.client.delete_object(Bucket=bucket, Key=key)
        return response

    def create_bucket(self, bucket: str):
        """
        Create a bucket.
        """
        response = self.client.create_bucket(Bucket=bucket)
        return response

    def delete_bucket(self, bucket: str):
        """
        Delete a bucket.
        """
        response = self.client.delete_bucket(Bucket=bucket)
        return response

    def download_object(self, bucket: str, key: str, file_path: str) -> None:
        """Download an object from a bucket.
        bucket is the name of the bucket containing the object.
        key is the name of the object to download.
        file_path is the path in which save the object.
            :param bucket: string
            :param key: string
            :param file_path: string
        """
        self.client.download_file(bucket, key, file_path)

    def create_presigned_url_for_download_object(
        self, bucket: str, key: str, expiration: int = 3600
    ):
        """
        Generate a presigned URL to download an object.

        :param bucket: string
        :param key: string
        :param expiration: Time in seconds for the presigned URL to remain valid

        """
        response = self.client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expiration
        )
        return response

    def create_presigned_url_for_upload_object(
        self,
        bucket: str,
        key: str,
        expiration: int = 3600,
        use_post: bool = False,
        fields: dict = None,
        conditions: list = None,
    ):
        """Generate a presigned URL for uploading a file to S3 bucket

        :param bucket: string
        :param key: string
        :param expiration: Time in seconds for the presigned URL to remain valid
        :param use_post: If True, use POST (multipart), if False use PUT (simpler)
        :param fields: Dictionary of prefilled form fields (POST only)
        :param conditions: List of conditions to include in the policy (POST only)
        :return: For PUT: string URL. For POST: Dictionary with 'url' and 'fields'
        :return: None if error.
        """
        try:
            if use_post:
                # Use POST for multipart uploads (more complex)
                response = self.client.generate_presigned_post(
                    bucket,
                    key,
                    Fields=fields,
                    Conditions=conditions,
                    ExpiresIn=expiration,
                )
            else:
                # Use PUT for simple uploads (recommended)
                response = self.client.generate_presigned_url(
                    "put_object",
                    Params={"Bucket": bucket, "Key": key},
                    ExpiresIn=expiration,
                )
        except ClientError as e:
            logger.error(e)
            return None

        return response

    def update_property(self):
        """
        Notify all attached properties to update their values.
        """
        while not self._stop_event.is_set():
            try:
                logger.debug(f"S3 Connector node {self.uri} updating property")
                self.notify()
            except Exception as e:
                logger.error(f"Error updating property: {e}")
            self._stop_event.wait(self.expiration)


class S3ConnectorBuilder(ObjectBuilder):
    """
    A class representing an S3 connector builder.
    """

    def build(
        self,
        host: str,
        port: str,
        username: str,
        password: str,
        uri: str,
        kg_connector: SINDITKGConnector = None,
        configuration: dict = None,
        **kwargs,
    ) -> S3Connector:
        region_name = None
        secure = False
        expiration = 3600
        if configuration is not None:
            if "region_name" in configuration:
                region_name = configuration.get("region_name")
            if "secure" in configuration:
                secure = configuration.get("secure") in [True, "true", "True", "1", 1]
            if "expiration" in configuration:
                try:
                    expiration = int(configuration.get("expiration"))
                except ValueError:
                    pass

        connector = S3Connector(
            host=host,
            port=port,
            access_key_id=username,
            secret_access_key=password,
            region_name=region_name,
            secure=secure,
            expiration=expiration,
            uri=uri,
            kg_connector=kg_connector,
        )
        return connector


connector_factory.register_builder(S3Connector.id, S3ConnectorBuilder())

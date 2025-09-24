import threading
import time

from influxdb_client import InfluxDBClient
from sindit.connectors.connector import Connector
from sindit.knowledge_graph.kg_connector import SINDITKGConnector
from sindit.util.log import logger

from sindit.connectors.connector_factory import ObjectBuilder
from sindit.connectors.connector_factory import connector_factory


class InfluxDBConnector(Connector):
    """InfluxDB v2.0 connector class.

    This class provides methods to connect to and interact with an
        InfluxDB v2.0 instance.
    It supports querying data from the database and
        provides options to return the results
    as either a pandas DataFrame or an InfluxDB result.

    Args:
        host (str): The hostname or IP address of the InfluxDB server.
        port (int): The port number of the InfluxDB server.
        org (str): The organization name associated with the InfluxDB instance.
        bucket (str): Default name of the bucket in the InfluxDB database.
        token (str, optional):
            The authentication token for accessing the InfluxDB instance.
            Defaults to None.

    Attributes:
        host (str): The hostname or IP address of the InfluxDB server.
        port (str): The port number of the InfluxDB server.
        org (str): The organization name associated with the InfluxDB instance.
        bucket (str): The name of the bucket in the InfluxDB database.
        client (InfluxDBClient): The InfluxDB client instance.

    """

    id: str = "influxdb"

    def __init__(
        self,
        host: str = "http://localhost",
        port: int = 8086,
        org: str = None,
        bucket: str = None,
        token: str = None,
        uri: str = None,
        kg_connector: SINDITKGConnector = None,
        update_interval: int = 30,  # update every 30 seconds
    ):
        super().__init__()

        self.host = host
        # if host not start with http:// or https://, add http://
        if not host.startswith("http://") and not host.startswith("https://"):
            self.host = "http://" + host

        self.port = str(port)
        self.org = org
        self.bucket = bucket
        self.__token = token
        self.client = None

        self.uri = f"influxdb://{host}:{port}/"
        if uri is not None:
            self.uri = uri

        self.kg_connector = kg_connector

        self.thread = None
        self._stop_event = threading.Event()
        self.update_interval = update_interval

    def set_token(self, token):
        """Set the authentication token for the InfluxDB connection.

        Args:
            token (str): The authentication token to set.

        """
        self.__token = token

    def set_bucket(self, bucket):
        """Set the name of the bucket in the InfluxDB database.

        Args:
            bucket (str): The name of the bucket.

        """
        self.bucket = bucket

    def stop(self, **kwargs):
        """Disconnect from the InfluxDB server."""
        self.client.close()
        self.update_connection_status(False)

        # Stop the update thread
        if self.thread is not None:
            self._stop_event.set()
            self.thread.join()
            self.thread = None

        logger.info(f"Connector {self.uri} disconnected from InfluxDB")

    def start(self, **kwargs):
        """Instantiate a connection to the InfluxDB server.

        Raises:
            ValueError: If the token is not set.

        kwargs:
            Additional keyword arguments to pass to the InfluxDBClient.
            timeout (int): The timeout value for the connection.
            verify_ssl (bool):
                Set this to false to skip verifying SSL certificate
                when calling API from https server.
            See more at:
            https://github.com/influxdata/influxdb-client-python/blob/master/influxdb_client/client/influxdb_client.py

        """
        if self.__token is not None:
            client = InfluxDBClient(
                url=f"{self.host}:{self.port}",
                token=self.__token,
                org=self.org,
                **kwargs,
            )
            self.client = client
        else:
            raise ValueError("Token is required to connect to InfluxDB")

        if self.client.ping():
            logger.info(
                f"Connector {self.uri} successfully connected to "
                f"InfluxDB {self.host}:{self.port}"
            )
            self.update_connection_status(True)

            # Start the update thread
            self.thread = threading.Thread(target=self.update_property)
            self.thread.daemon = True
            self._stop_event.clear()
            self.thread.start()
        else:
            self.update_connection_status(False)
            raise ConnectionError("Failed to connect to InfluxDB")

    def _check_if_bucket_name_is_set(self, bucket: str = None) -> bool:
        """Check if bucket name is set.
        Returns true if bucket name is set, otherwise raises ValueError.
        """
        bucket_is_set = False
        if bucket is None:
            if self.bucket is None:
                raise ValueError("Bucket name is required.")
            else:
                bucket_is_set = True
        else:
            self.bucket = bucket
            bucket_is_set = True

        return bucket_is_set

    def query(self, query):
        """Execute a Flux query on the InfluxDB database.

        Args:
            query (str): The Flux query to execute.

        Returns:
            InfluxDB result: The query result.

        """
        # TODO: Evaluate if this is a security risk.
        # If it is, then the client should not be exposed either.
        return self.client.query_api().query_data_frame(query)

    def query_field(
        self,
        field: str | list = None,
        measurement: str = None,
        start: str = "-1h",
        stop: str = "now()",
        bucket: str = None,
        org: str = None,
        tags: dict = None,
        latest: bool = False,
        query_return_type: str = "pandas",
    ):
        """Query the specified field or measurement from the InfluxDB database.

        Args:
            field (str, optional): The name of the field to query.
            measurement (str, optional): The name of the measurement to
                query from.
            start (str, optional): The start time of the query range.
                Defaults to "-1h".
            stop (str, optional): The stop time of the query range.
                Defaults to "now()".
            query_return_type (str, optional):
                The type of the query result to return.
                Valid values are "pandas" and "flux".
                Defaults to "flux".

        Returns:
            pandas.DataFrame or InfluxDB result:
                The query result based on the specified return type.

        Raises:
            ValueError: If both `field` and `measurement` are `None` or if
            an invalid query return type is specified.
        """
        # Ensure either field or measurement is provided, but not both as None
        if field is None and measurement is None:
            raise ValueError(
                "Either `field` or `measurement` must be specified, "
                "but not both as None."
            )

        self._check_if_bucket_name_is_set(bucket)

        query = f"""
            from(bucket: "{self.bucket}")
            |> range(start: {start}, stop: {stop})
            """

        if measurement:
            query += f'|> filter(fn: (r) => r._measurement == "{measurement}")\n'

        if field:
            if isinstance(field, list):
                query += f'    |> filter(fn: (r) => r._field == "{field[0]}"'
                for i in range(1, len(field)):
                    query += f' or r._field == "{field[i]}"'
                query += ")\n"
            elif isinstance(field, str):
                query += f'    |> filter(fn: (r) => r._field == "{field}")\n'

        # tags value could be a list or a single value
        if tags:
            for key, value in tags.items():
                if isinstance(value, list):
                    query += f'    |> filter(fn: (r) => r.{key} == "{value[0]}"'
                    for i in range(1, len(value)):
                        query += f' or r.{key} == "{value[i]}"'
                    query += ")\n"
                else:
                    query += f'    |> filter(fn: (r) => r.{key} == "{value}")\n'
                # query += f'    |> filter(fn: (r) => r.{key} == "{value}")\n'

        if latest:
            query += "|> last()"

        if query_return_type == "pandas":
            query += (
                '|> pivot(rowKey:["_time"], '
                'columnKey: ["_field"], '
                'valueColumn: "_value") '
            )
            return self.client.query_api().query_data_frame(query, org=org)
        elif query_return_type == "flux":
            return self.client.query_api().query(query, org=org)
        else:
            raise ValueError(
                "Invalid query return type. Choose either 'pandas' or 'flux'."
            )

    def get_buckets(self):
        """Get list of buckets in the InfluxDB database.

        Returns:
            list: Buckets

        """
        return self.client.buckets_api().find_buckets().buckets

    def get_bucket_names(self):
        """Get list of bucket names in the InfluxDB database.

        Returns:
            list: Bucket names.

        """
        buckets = self.get_buckets()
        return [bucket.name for bucket in buckets]

    def extract_keys(self, result: list):
        keys = []
        for table in result:
            for record in table.records:
                keys.append(record["_value"])
        return keys

    def get_tags(self, bucket: str = None):
        """Get list of tags in the specified bucket.

        Args:
            bucket (str): The name of the bucket.

        Returns:
            list: Tags

        """
        self._check_if_bucket_name_is_set(bucket)
        tags_query = f"""
            import "influxdata/influxdb/schema"
            schema.tagKeys(bucket: "{self.bucket}")
            """
        result = self.client.query_api().query(tags_query)
        return self.extract_keys(result)

    def get_fields(self, bucket: str = None):
        """Get list of fields in the specified bucket.

        Args:
            bucket (str): The name of the bucket.

        Returns:
            list: Fields
        """
        self._check_if_bucket_name_is_set(bucket)
        fields_query = f"""
        import "influxdata/influxdb/schema"
        schema.fieldKeys(bucket: "{self.bucket}")
        """
        result = self.client.query_api().query(fields_query)
        return self.extract_keys(result)

    def get_data_async(self):
        """Get the data asynchronously as a stream."""
        # TODO: Implement this method?
        pass

    def update_property(self):
        while not self._stop_event.is_set():
            try:
                logger.debug(f"InfluxDB node {self.uri} updating property")
                self.notify()
            except Exception as e:
                logger.error(f"Error updating property: {e}")
            time.sleep(self.update_interval)


class InfluxDBConnectorBuilder(ObjectBuilder):
    def build(self, host, port, token, uri, kg_connector, **kwargs):
        connector = InfluxDBConnector(
            host=host,
            port=port,
            token=token,
            uri=uri,
            kg_connector=kg_connector,
        )
        return connector


connector_factory.register_builder(InfluxDBConnector.id, InfluxDBConnectorBuilder())

from influxdb_client import InfluxDBClient


class InfluxDBConnector:
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
        bucket (str): The name of the bucket in the InfluxDB database.
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

    def __init__(
        self,
        bucket: str,
        host: str = "localhost",
        port: int = 8086,
        org: str = None,
        token=None,
    ):
        self.host = host
        self.port = str(port)
        self.org = org
        self.bucket = bucket
        self.__token = token
        self.client = None

    def set_token(self, token):
        """Set the authentication token for the InfluxDB connection.

        Args:
            token (str): The authentication token to set.

        """
        self.__token = token

    def disconnect(self):
        """Disconnect from the InfluxDB server."""
        self.client.close()

    def connect(self):
        """Instantiate a connection to the InfluxDB server.

        Raises:
            ValueError: If the token is not provided.

        """
        if self.__token is not None:
            client = InfluxDBClient(
                url=f"http://{self.host}:{self.port}", token=self.__token, org=self.org
            )
            self.client = client
        else:
            raise ValueError("Token is required to connect to InfluxDB")

        if self.client.ping():
            print("Successfully connected to InfluxDB")
        else:
            raise ConnectionError("Failed to connect to InfluxDB")

    def query(self, query):
        """Execute a Flux query on the InfluxDB database.

        Args:
            query (str): The Flux query to execute.

        Returns:
            InfluxDB result: The query result.

        """
        result = self.client.query_api().query(query)
        return result.raw

    def query_field(
        self,
        field: str,
        start: str = "-1h",
        stop: str = "now()",
        query_return_type: str = "flux",
    ):
        """Query the specified field from the InfluxDB database.

        Args:
            field (str): The name of the field to query.
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
            ValueError: If an invalid query return type is specified.
        """
        query = f"""
            from(bucket: "{self.bucket}")
            |> range(start: {start}, stop: {stop})
            |> filter(fn: (r) => r._field == "{field}")
            """
        if query_return_type == "pandas":
            query += (
                '|> pivot(rowKey:["_time"], '
                'columnKey: ["_field"], '
                'valueColumn: "_value") '
            )
            return self.client.query_api().query_data_frame(query)
        elif query_return_type == "flux":
            return self.client.query_api().query(query)
        else:
            raise ValueError(
                ("Invalid query return type." 'Choose either "pandas" or "flux".')
            )

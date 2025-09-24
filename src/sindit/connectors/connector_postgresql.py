# from abc import ABC, abstractmethod
import threading
import psycopg2
from sindit.connectors.connector import Connector
from sindit.knowledge_graph.kg_connector import SINDITKGConnector
from sindit.util.log import logger
from sindit.connectors.connector_factory import ObjectBuilder, connector_factory


class PostgreSQLConnector(Connector):
    """PostgreSQL connector class.

    This class provides methods to connect to and interact with a
    PostgreSQL database. It supports querying data from the database
    and notifying attached properties of any changes.

    Args:
        host (str): The hostname or IP address of the PostgreSQL server.
        port (int): The port number of the PostgreSQL server.
        dbname (str): The name of the PostgreSQL database.
        user (str): The username for accessing the PostgreSQL database.
        password (str, optional): The password for accessing the database.
            Defaults to None.
    """

    id: str = "postgresql"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        dbname: str = None,
        user: str = None,
        password: str = None,
        uri: str = None,
        kg_connector: SINDITKGConnector = None,
        update_interval: int = 30,  # update every 30 seconds
    ):
        super().__init__()

        self.host = host
        self.port = str(port)
        self.dbname = dbname
        self.user = user
        self.password = password
        self.connection = None

        self.uri = f"postgresql://{host}:{port}/{dbname}"
        if uri is not None:
            self.uri = uri

        self.kg_connector = kg_connector

        self.thread = None
        self._stop_event = threading.Event()
        self.update_interval = update_interval

    def start(self, **kwargs):
        """Instantiate a connection to the PostgreSQL server."""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
            )
            self.connection.autocommit = True
            logger.info(f"Connector {self.uri} successfully connected to PostgreSQL")

            self.update_connection_status(True)
            self.thread = threading.Thread(target=self.update_property)
            self.thread.daemon = True
            self._stop_event.clear()
            self.thread.start()
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self.update_connection_status(False)

    def stop(self, **kwargs):
        """Disconnect from the PostgreSQL server."""
        if self.connection:
            self.connection.close()
        self.update_connection_status(False)

        if self.thread is not None:
            self._stop_event.set()
            self.thread.join()
            self.thread = None

        logger.info(f"Connector {self.uri} disconnected from PostgreSQL")

    def query(self, query_str):
        """Execute an SQL query on the PostgreSQL database.

        Args:
            query_str (str): The SQL query to execute.

        Returns:
            list: Query result as a list of rows.

        """
        if not self.connection:
            raise ConnectionError("PostgreSQL connection is not active.")

        cursor = self.connection.cursor()
        cursor.execute(query_str)
        result = cursor.fetchall()
        cursor.close()
        return result

    def update_property(self):
        while not self._stop_event.is_set():
            try:
                logger.debug(f"PostgreSQL node {self.uri} updating property")
                self.notify()
            except Exception as e:
                logger.error(f"Error updating property: {e}")
            threading.Event().wait(self.update_interval)


class PostgreSQLConnectorBuilder(ObjectBuilder):
    def build(
        self, host, port, username, password, uri, kg_connector, configuration, **kwargs
    ):
        dbname = None
        if configuration is not None:
            if "dbname" in configuration:
                dbname = configuration.get("dbname")
        if dbname is None:
            raise ValueError("PostgreSQL database name is required.")

        connector = PostgreSQLConnector(
            host=host,
            port=port,
            dbname=dbname,
            user=username,
            password=password,
            uri=uri,
            kg_connector=kg_connector,
        )
        return connector


connector_factory.register_builder(PostgreSQLConnector.id, PostgreSQLConnectorBuilder())

# from abc import ABC, abstractmethod
from sindit.connectors.connector import Connector, Property
from datetime import datetime
from sindit.knowledge_graph.kg_connector import SINDITKGConnector
from sindit.knowledge_graph.graph_model import DatabaseProperty
from sindit.util.log import logger
from sindit.connectors.connector_postgresql import PostgreSQLConnector
from sindit.connectors.connector_factory import ObjectBuilder, property_factory


class PostgreSQLProperty(Property):
    def __init__(
        self,
        uri: str,
        table: str = None,
        field: str = None,
        conditions: dict = None,
        kg_connector: SINDITKGConnector = None,
    ):
        self.uri = str(uri)
        self.table = table
        self.field = field
        self.conditions = conditions
        self.kg_connector = kg_connector
        self.timestamp = None
        self.value = None

    def update_value(self, connector: Connector, **kwargs) -> None:
        """
        Receive update from the PostgreSQL connector
        and query the database for the property value.
        """
        if self.connector is not None:
            postgresql_connector: PostgreSQLConnector = connector

            # Build query based on table, field, and conditions
            if isinstance(self.field, list):
                fields_str = ", ".join(self.field)  # Join fields for multiple selection
            else:
                fields_str = self.field  # Single field

            query = f"SELECT {fields_str} FROM {self.table}"

            # Adding conditions to the query if they exist
            if self.conditions:
                condition_str = " AND ".join(
                    [f"{k}='{v}'" for k, v in self.conditions.items()]
                )
                query += f" WHERE {condition_str}"

            # query += " ORDER BY id DESC LIMIT 1;"
            # Assuming 'id' or primary key exists to get the latest entry

            # Execute the query
            result = postgresql_connector.query(query)

            if result:
                result_row = result[0]  # Fetch the first row of the result
                self.timestamp = datetime.now()

                # Check if the field is a list or a single value
                if isinstance(self.field, list):
                    # Create a dictionary with field names
                    # as keys and their respective values
                    self.value = {
                        self.field[i]: result_row[i] for i in range(len(self.field))
                    }
                else:
                    # Single field case, just return the scalar value
                    self.value = result_row[0]

                # Log and update value in the knowledge graph
                logger.debug(
                    (
                        f"Property {self.uri} updated with value {self.value}, "
                        f"timestamp {self.timestamp}"
                    )
                )

                self.update_property_value_to_kg(self.uri, self.value, self.timestamp)
            else:
                logger.debug(f"No data found for property {self.uri}")

    def attach(self, connector: Connector) -> None:
        """
        Attach the property to the PostgreSQL connector.
        """
        pass


class PostgreSQLPropertyBuilder(ObjectBuilder):
    def build(self, uri, kg_connector, node, **kwargs) -> PostgreSQLProperty:
        """
        Build a PostgreSQLProperty instance.
        """
        if isinstance(node, DatabaseProperty):
            table = None
            field = None
            conditions = None
            property_identifiers = node.propertyIdentifiers
            if "table" in property_identifiers:
                table = property_identifiers["table"]
            if "field" in property_identifiers:
                field = property_identifiers["field"]
            if "conditions" in property_identifiers:
                conditions = property_identifiers["conditions"]

            if table is None or field is None:
                logger.error(
                    f"Node {uri} is missing table or field identifiers, "
                    "cannot create PostgreSQLProperty."
                )
                return None

            new_property = PostgreSQLProperty(
                uri=uri,
                table=table,
                field=field,
                conditions=conditions,
                kg_connector=kg_connector,
            )

            return new_property
        else:
            logger.error(
                f"Node {uri} is not an instance of DatabaseProperty, "
                "cannot create PostgreSQLProperty."
            )
            return None


property_factory.register_builder(PostgreSQLConnector.id, PostgreSQLPropertyBuilder())

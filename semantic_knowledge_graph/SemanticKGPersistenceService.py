class SemanticKGPersistenceService:
    """
    Interface for the Semantic Knowledge Graph Persistence Service
    """

    def is_connected(self) -> bool:
        """
        Check if the service is connected to the database.
        :return: True if connected, False otherwise

        """
        pass

    def graph_query(self, query: str, accept_content: str) -> any:
        """
        Execute a query on the graph database, including SELECT, CONSTRUCT,
        ASK, DESCRIBE queries.
        :param query: The query to be executed
        :param accept_content: The content type of the response. Accepted values:
            application/sparql-results+json, application/sparql-results+xml, text/csv
        :return: The result of the query, None if the query was unsuccessful.
        """
        pass

    def graph_update(self, update: str) -> any:
        """
        Execute an update query on the graph database, including INSERT, DELETE queries.
        :param update: The update query to be executed
        :return: True if the update was successful, False otherwise
        """
        pass

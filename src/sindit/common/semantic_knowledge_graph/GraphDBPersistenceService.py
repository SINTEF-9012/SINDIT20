import time

import requests
from sindit.common.semantic_knowledge_graph.SemanticKGPersistenceService import (
    SemanticKGPersistenceService,
)
from sindit.util.client_api import ClientAPI
from sindit.util.log import logger


class GraphDBPersistenceService(SemanticKGPersistenceService):
    def __init__(
        self,
        host: str,
        port: str,
        repository: str,
        username: str = "",
        password: str = "",
    ):
        # self.__api_endpoint = f"http://{host}:{port}"
        self.__sparql_endpoint = f"http://{host}:{port}/repositories/{repository}"
        self.__repository = repository
        self.__username = username
        self.__password = password
        self.__connected = False
        self._connect()

        self.__client_api = ClientAPI(self.__sparql_endpoint)

    def _connect(self):
        self.__health_check_uri = f"{self.__sparql_endpoint}/health"

        while not self.__connected:
            try:
                logger.info("Connecting to GraphDB...")
                logger.debug(f"Trying to connect to uri {self.__health_check_uri}.")

                response = requests.get(
                    self.__health_check_uri,
                    timeout=5,
                    auth=(self.__username, self.__password),
                )
                if not response.ok:
                    raise Exception(
                        "Failed to connect to "
                        + f"{self.__health_check_uri}. "
                        + f"Response: {response.content}"
                    )

                self.__connected = True

                logger.info("Connected to GraphDB.")
            except Exception as e:
                logger.error(
                    "GraphDB unavailable or Authentication invalid!. "
                    + f"Reason: {e}. Trying again in 10 seconds..."
                )
                time.sleep(10)

    def is_connected(self) -> bool:
        return self.__connected

    def graph_query(self, query: str, accept_content: str) -> any:
        params = {
            "query": query,
        }
        headers = {"Accept": accept_content}
        response = self.__client_api.get_str(
            "",
            params=params,
            headers=headers,
            retries=5,
            auth=(self.__username, self.__password),
        )
        return response

    def graph_update_old(self, update: str) -> bool:
        params = {
            "update": update,
        }
        response = self.__client_api.post(
            "/statements",
            params=params,
            retries=5,
            auth=(self.__username, self.__password),
        )

        return response

    def graph_update(self, update: str) -> bool:
        data = {
            "update": update,
        }
        response = self.__client_api.post(
            "/statements",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            # headers={"Content-Type": "application/sparql-update"},
            retries=5,
            auth=(self.__username, self.__password),
        )

        return response

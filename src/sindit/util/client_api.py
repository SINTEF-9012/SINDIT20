import json
import time
from typing import Dict

import requests
from requests.exceptions import RequestException as ReqExc
from sindit.util.log import logger

# FAST_API_HOST = get_environment_variable("FAST_API_HOST")
# FAST_API_PORT = get_environment_variable_int("FAST_API_PORT")
# API_URI = f"http://{FAST_API_HOST}:{FAST_API_PORT}"


class ClientAPI:
    def __init__(self, api_uri: str):
        self.api_uri = api_uri

    def _handle_request_exception(self, retry_number: int = 0):
        logger.info("API not available!")
        logger.info(f"Tried to connect to {self.api_uri}")

        sleep_time = 5 * (2**retry_number)

        logger.info(f"Retrying in {sleep_time} seconds...")
        time.sleep(sleep_time)

    def get_json(
        self,
        relative_path: str,
        retries: int = -1,
        timeout: int = 30,
        result_class=None,
        **kwargs,
    ):
        """
        Get request to the specified api endpoint
        :param relative_path:
        :param retries: how often to retry if the call failed.
            Negative numbers mean (about) unlimited.
        :return: the response json as dict
        """
        range_limit = retries + 1 if retries >= 0 else 9 * 10**23
        for i in range(range_limit):
            try:
                resp_dict = requests.get(
                    self.api_uri + relative_path, timeout=timeout, **kwargs
                ).json()

                if result_class is not None:
                    resp_dict = result_class.from_json(str(resp_dict))

                elif isinstance(resp_dict, str):
                    # Sometimes, the json is still represented as string
                    # instead of dict
                    resp_dict = json.loads(resp_dict)

                return resp_dict
            except ReqExc as e:
                logger.error(
                    "Failed to execute "
                    + self.api_uri
                    + relative_path
                    + " with args "
                    + str(kwargs)
                )
                logger.error(e)
                if i < retries:
                    self._handle_request_exception(i)

    def get_raw(self, relative_path: str, retries: int = -1, **kwargs):
        """
        Get request to the specified api endpoint
        :param relative_path:
        :param retries: how often to retry if the call failed.
            Negative numbers mean (about) unlimited.
        :return: Complete response object
        """
        range_limit = retries + 1 if retries >= 0 else 9 * 10**23
        for i in range(range_limit):
            try:
                return requests.get(self.api_uri + relative_path, timeout=300, **kwargs)
            except ReqExc:
                self._handle_request_exception(i)

    def get_str(self, relative_path: str, retries: int = -1, **kwargs):
        """
        Get request to the specified api endpoint
        :param relative_path:
        :return: the response as string
        """
        range_limit = retries + 1 if retries >= 0 else 9 * 10**23
        for i in range(range_limit):
            try:
                return requests.get(
                    self.api_uri + relative_path, timeout=30, **kwargs
                ).text
            except ReqExc:
                self._handle_request_exception(i)

    def get_int(self, relative_path: str, retries: int = -1, **kwargs):
        """
        Get request to the specified api endpoint
        :param relative_path:
        :param retries: how often to retry if the call failed.
            Negative numbers mean (about) unlimited.
        :return: the response as int number
        """
        range_limit = retries + 1 if retries >= 0 else 9 * 10**23
        for i in range(range_limit):
            try:
                return int(
                    requests.get(
                        self.api_uri + relative_path, timeout=30, **kwargs
                    ).text
                )
            except ReqExc:
                self._handle_request_exception(i)

    def get_float(self, relative_path: str, retries: int = -1, **kwargs):
        """
        Get request to the specified api endpoint
        :param relative_path:
        :param retries: how often to retry if the call failed.
            Negative numbers mean (about) unlimited.
        :return: the response as float number
        """
        range_limit = retries + 1 if retries >= 0 else 9 * 10**23
        for i in range(range_limit):
            try:
                return float(
                    requests.get(
                        self.api_uri + relative_path, timeout=30, **kwargs
                    ).text
                )
            except ReqExc:
                self._handle_request_exception(i)

    def patch(self, relative_path: str, retries: int = -1, **kwargs):
        range_limit = retries + 1 if retries >= 0 else 9 * 10**23
        for i in range(range_limit):
            try:
                return requests.patch(self.api_uri + relative_path, **kwargs)
            except ReqExc:
                self._handle_request_exception(i)

    def post(
        self,
        relative_path: str,
        data: Dict = None,
        json: Dict = None,
        retries: int = -1,
        **kwargs,
    ):
        """Post request. Returns the response body text

        Args:
        relative_path (str): _description_
        retries: how often to retry if the call failed.
            Negative numbners mean (about) unlimited.
            data (Dict, optional): _description_. Defaults to None.
            json (Dict, optional): _description_. Defaults to None.

        Returns: Complete response object
        """
        range_limit = retries + 1 if retries >= 0 else 9 * 10**23
        for i in range(range_limit):
            try:
                response = requests.post(
                    self.api_uri + relative_path, data=data, json=json, **kwargs
                )
                # text = response.text
                # print(response.status_code)
                # if text[0] == '"' and text[-1] == '"':
                #    text = text[1:-1]S
                return response
            except ReqExc:
                self._handle_request_exception(i)

    def delete(self, relative_path: str, retries: int = -1, **kwargs):
        """Delete request. Returns the response body text

        Args:
        relative_path (str): _description_
        retries: how often to retry if the call failed.
            Negative numbners mean (about) unlimited.


        Returns: Complete response object
        """
        range_limit = retries + 1 if retries >= 0 else 9 * 10**23
        for i in range(range_limit):
            try:
                response = requests.delete(self.api_uri + relative_path, **kwargs)
                # text = response.text
                # if text[0] == '"' and text[-1] == '"':
                #    text = text[1:-1]
                return response
            except ReqExc:
                self._handle_request_exception(i)

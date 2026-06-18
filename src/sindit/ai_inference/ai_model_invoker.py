"""Runtime invoker for an external AI model prediction endpoint.

``AIModelInvoker`` extends ``Connector`` so it can use the existing
observer pattern: attached ``AIInferencePropertyInvoker`` objects
(``Property`` subclasses) receive ``update_value()`` calls on each poll.

Supported endpoint types
------------------------
``generic`` (default)
    ``{"inputs": [input_dict]}`` — works with most custom FastAPI/Flask
    servers.
``mlflow``
    ``{"dataframe_records": [input_dict]}`` — MLflow Model Server
    ``POST /invocations``.
``triton``
    NVIDIA Triton HTTP v2: each key/value becomes a named FP32 tensor.
``huggingface``
    ``{"inputs": input_dict}`` — HF Inference API
    (``POST https://api-inference.huggingface.co/models/<model-id>``).
    Also works with locally served HF pipelines.
``tensorflow-serving``
    ``{"instances": [input_dict]}`` — TensorFlow Serving REST API
    ``POST /v1/models/<model>:predict``.
``torchserve``
    Raw ``input_dict`` body — TorchServe ``POST /predictions/<model>``.
    The custom handler receives the dict directly.
``bentoml``
    Raw ``input_dict`` body — BentoML Service endpoint.
    The service's input schema deserialises the JSON body directly.
``seldon``
    ``{"data": {"names": [...], "ndarray": [[...]]}}`` — Seldon Core
    ``POST /api/v1.0/predictions``.

New endpoint types can be added by extending ``_build_payload`` without
changing the observer or lifecycle machinery.
"""

import json
import threading

import requests

from sindit.connectors.connector import Connector
from sindit.knowledge_graph.kg_connector import SINDITKGConnector
from sindit.util.log import logger


class AIModelInvoker(Connector):
    """Connector that periodically notifies attached AI inference properties.

    Parameters
    ----------
    deployment_node:
        The ``AIModelDeployment`` KG node supplying ``endpointUrl``,
        ``endpointType``, and ``isActive``.
    api_key:
        Resolved secret value (retrieved from the vault by the setup layer).
        Never logged or persisted.
    uri:
        KG URI of the deployment node, used as the invoker's identity key.
    kg_connector:
        Used to persist ``isActive`` back to the KG.
    update_interval:
        Poll interval in seconds.  Defaults to 60.
    """

    def __init__(
        self,
        deployment_node,
        api_key: str | None = None,
        uri: str | None = None,
        kg_connector: SINDITKGConnector | None = None,
        update_interval: int = 60,
    ):
        super().__init__()
        self.deployment_node = deployment_node
        self._api_key = api_key
        self.uri = uri or str(deployment_node.uri)
        self.kg_connector = kg_connector
        self.update_interval = update_interval

        self.thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Connector lifecycle
    # ------------------------------------------------------------------

    def start(self, **kwargs) -> None:
        """Start background polling and mark the deployment as active."""
        self._stop_event.clear()
        self._persist_is_active(True)

        self.thread = threading.Thread(
            target=self._poll_loop,
            name=f"ai-invoker-{self.uri}",
            daemon=True,
        )
        self.thread.start()
        logger.info("AIModelInvoker started for deployment %s", self.uri)

    def stop(self, **kwargs) -> None:
        """Stop background polling and mark the deployment as inactive."""
        if self.thread is not None:
            self._stop_event.set()
            self.thread.join(timeout=5)
            self.thread = None

        no_update = kwargs.get("no_update_connection_status", False)
        if not no_update:
            self._persist_is_active(False)

        logger.info("AIModelInvoker stopped for deployment %s", self.uri)

    def _poll_loop(self) -> None:
        """Background thread: call notify() every ``update_interval`` seconds."""
        while not self._stop_event.is_set():
            try:
                logger.debug("AIModelInvoker %s: notifying observers", self.uri)
                self.notify()
            except Exception as exc:
                logger.error("AIModelInvoker %s: poll error: %s", self.uri, exc)
            self._stop_event.wait(self.update_interval)

    # ------------------------------------------------------------------
    # Prediction request
    # ------------------------------------------------------------------

    def invoke(self, input_data: dict) -> dict:
        """POST ``input_data`` to the model endpoint and return the JSON response.

        Parameters
        ----------
        input_data:
            Feature name → value dict assembled from input SINDIT properties.

        Returns
        -------
        dict
            Parsed JSON response from the model server.

        Raises
        ------
        ValueError
            When the deployment node has no ``endpointUrl``.
        requests.HTTPError
            When the model server returns a non-2xx status.
        """
        endpoint_url = str(getattr(self.deployment_node, "endpointUrl", "") or "")
        if not endpoint_url:
            raise ValueError(
                f"AIModelDeployment {self.uri} has no endpointUrl configured"
            )

        endpoint_type = str(
            getattr(self.deployment_node, "endpointType", None) or "generic"
        ).lower()

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = self._build_payload(endpoint_type, input_data)

        logger.debug("AIModelInvoker %s: POST %s", self.uri, endpoint_url)
        response = requests.post(
            endpoint_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _build_payload(endpoint_type: str, input_data: dict) -> dict:
        """Format ``input_data`` for the given endpoint protocol."""

        if endpoint_type == "mlflow":
            # MLflow Model Server: POST /invocations
            # https://mlflow.org/docs/latest/deployment/deploy-model-locally.html
            return {"dataframe_records": [input_data]}

        if endpoint_type == "triton":
            # NVIDIA Triton Inference Server HTTP v2 API (simplified)
            # Each feature becomes a named scalar FP32 tensor.
            # https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/protocol/extension_binary_data.html
            inputs = [
                {
                    "name": key,
                    "shape": [1, 1],
                    "datatype": "FP32",
                    "data": [[value]],
                }
                for key, value in input_data.items()
            ]
            return {"inputs": inputs}

        if endpoint_type == "huggingface":
            # Hugging Face Inference API
            # POST https://api-inference.huggingface.co/models/<model-id>
            # Also works with locally served HF pipelines.
            # https://huggingface.co/docs/api-inference/index
            #
            # Single-input mapping (most text/image/audio models):
            #   inputMapping = {"inputs": "urn:...text_prop"}
            #   → {"inputs": "the text value"}
            #
            # Multi-input mapping (tabular models):
            #   inputMapping = {"temperature": "urn:...t", "rpm": "urn:...r"}
            #   → {"inputs": {"temperature": 42.3, "rpm": 1200}}
            if len(input_data) == 1:
                return {"inputs": list(input_data.values())[0]}
            return {"inputs": input_data}

        if endpoint_type == "tensorflow-serving":
            # TensorFlow Serving REST API
            # POST /v1/models/<model>:predict
            # https://www.tensorflow.org/tfx/serving/api_rest
            return {"instances": [input_data]}

        if endpoint_type == "torchserve":
            # TorchServe Management/Inference API
            # POST /predictions/<model>
            # The custom handler receives the raw JSON body; no standard wrapper.
            # https://pytorch.org/serve/inference_api.html
            return input_data

        if endpoint_type == "bentoml":
            # BentoML Service endpoint
            # The service's input schema deserialises the JSON body directly.
            # https://docs.bentoml.com/en/latest/
            return input_data

        if endpoint_type == "seldon":
            # Seldon Core V1 prediction protocol
            # POST /api/v1.0/predictions
            # https://docs.seldon.io/projects/seldon-core/en/latest/reference/apis/index.html
            names = list(input_data.keys())
            values = [list(input_data.values())]
            return {"data": {"names": names, "ndarray": values}}

        # generic (default): works with most custom FastAPI/Flask servers
        return {"inputs": [input_data]}

    # ------------------------------------------------------------------
    # Connection-status persistence
    # ------------------------------------------------------------------

    def update_connection_status(self, is_connected: bool) -> None:
        """Persist ``isActive`` on the deployment node in the KG."""
        self._persist_is_active(is_connected)

    def _persist_is_active(self, is_active: bool) -> None:
        self.is_connected = is_active
        if self.kg_connector is None:
            return
        try:
            node = self.kg_connector.load_node_by_uri(self.uri)
            if node is not None:
                node.isActive = is_active
                self.kg_connector.save_node(node)
        except Exception as exc:
            logger.warning(
                "AIModelInvoker %s: could not persist isActive=%s: %s",
                self.uri,
                is_active,
                exc,
            )

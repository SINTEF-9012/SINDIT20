"""FastAPI endpoints for the AI inference feature.

Importing this module triggers import of ``ai_inference_model``, which
registers ``AIInferenceProperty`` into ``NodeURIClassMapping`` so the
generic ``/kg/*`` endpoints also work on inference properties.

``AIModelDeployment`` CRUD is handled by ``/ai_deployment/deployment*``.
Saving a deployment via that endpoint also calls
``update_deployment_invoker()`` so the runtime invoker is kept in sync.

Routes
------
POST   /ai_inference/property      — create / replace an AIInferenceProperty
GET    /ai_inference/property      — load one by URI
GET    /ai_inference/properties    — list all (paginated)
POST   /ai_inference/invoke        — run inference on demand
POST   /ai_inference/refresh       — reinitialise all invokers in background
"""

from typing import List

from fastapi import BackgroundTasks, Depends, HTTPException

from sindit.ai_inference.setup_ai_inference import (
    initialize_ai_inference,
    invoke_and_update,
    update_inference_property_node,
)
from sindit.api.api import app
from sindit.api.authentication_endpoints import User, get_current_active_user
from sindit.initialize_kg_connectors import sindit_kg_connector
from sindit.knowledge_graph.ai_inference_model import AIInferenceProperty  # noqa: F401
from sindit.util.log import logger

_DEFAULT_DEPTH = 2


@app.post("/ai_inference/property", tags=["AI"])
async def create_ai_inference_property(
    node: AIInferenceProperty,
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Create or replace an ``AIInferenceProperty`` and attach its runtime invoker.

    The invoker is started immediately after the node is saved so
    predictions begin polling on the next ``updateInterval`` tick.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        if result:
            update_inference_property_node(
                node, replace=True, username=current_user.username
            )
        return {"result": result}
    except Exception as exc:
        logger.error("Error saving AIInferenceProperty %s: %s", node.uri, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get(
    "/ai_inference/property",
    tags=["AI"],
    response_model_exclude_none=True,
    response_model=AIInferenceProperty,
    summary="Get AI Inference Property",
)
async def get_ai_inference_property(
    node_uri: str,
    depth: int = _DEFAULT_DEPTH,
    current_user: User = Depends(get_current_active_user),
):
    """Load a single ``AIInferenceProperty`` by URI."""
    try:
        node = sindit_kg_connector.load_node_by_uri(node_uri, depth=depth)
        if not isinstance(node, AIInferenceProperty):
            raise HTTPException(
                status_code=404,
                detail=f"AIInferenceProperty {node_uri} not found",
            )
        return node
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error loading AIInferenceProperty %s: %s", node_uri, exc)
        raise HTTPException(status_code=404, detail=str(exc))


@app.get(
    "/ai_inference/properties",
    tags=["AI"],
    response_model_exclude_none=True,
    response_model=List[AIInferenceProperty],
    summary="Get all AI Inference Properties",
)
async def list_ai_inference_properties(
    depth: int = _DEFAULT_DEPTH,
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
) -> list:
    """List all ``AIInferenceProperty`` nodes (paginated)."""
    try:
        return sindit_kg_connector.load_nodes_by_class(
            str(AIInferenceProperty.CLASS_URI),
            depth=depth,
            skip=skip,
            limit=limit,
        )
    except Exception as exc:
        logger.error("Error listing AIInferenceProperty nodes: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ai_inference/invoke", tags=["AI"])
async def invoke_inference(
    property_uri: str,
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Immediately run one inference step and return the updated value.

    Uses the current ``propertyValue`` of each input property in
    ``inputMapping`` as the request payload, then writes the prediction
    result back to this property's ``propertyValue``.
    """
    try:
        return invoke_and_update(property_uri, username=current_user.username)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Error invoking inference for %s: %s", property_uri, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ai_inference/refresh", tags=["AI"])
async def refresh_ai_inference(
    replace: bool = False,
    current_user: User = Depends(get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> dict:
    """Reinitialise all AI inference deployments and properties in the background.

    Parameters
    ----------
    replace:
        When ``True``, existing invokers are stopped and recreated.
        When ``False`` (default), only new nodes are initialised.
    """

    def _run():
        try:
            logger.info("AI inference refresh started (replace=%s)", replace)
            initialize_ai_inference(
                replace=replace,
                async_start=True,
                username=current_user.username,
            )
            logger.info("AI inference refresh completed")
        except Exception as exc:
            logger.error("AI inference refresh failed: %s", exc)

    background_tasks.add_task(_run)
    return {"message": "AI inference refresh started", "replace": replace}

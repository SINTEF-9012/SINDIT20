"""FastAPI endpoints for AI model deployment metadata.

These endpoints let clients register and query AI model deployment metadata
in the SINDIT knowledge graph (see
``sindit.knowledge_graph.ai_deployment_model``). SINDIT acts as a semantic
control plane: it persists the metadata in GraphDB but does not serve or run
the models.

Importing this module also imports the AI deployment model module, which
registers the AI deployment classes into ``NodeURIClassMapping``. As a result
the generic ``/kg/*`` endpoints (get by URI, delete, advanced search, patch)
work on AI deployment nodes as well; the routes here add a typed,
deployment-centric surface for the most common operations.
"""

from fastapi import Depends, HTTPException

from sindit.ai_inference.setup_ai_inference import update_deployment_invoker
from sindit.api.api import app
from sindit.api.authentication_endpoints import User, get_current_active_user
from sindit.initialize_kg_connectors import sindit_kg_connector
from sindit.knowledge_graph.ai_deployment_model import AIModelDeployment
from sindit.util.log import logger

# Depth 2 is enough to load the nested ModelInput / ModelOutput helpers
# in a single request; the model no longer has deeper nesting.
DEFAULT_AI_DEPLOYMENT_DEPTH = 2


@app.post("/ai_deployment/deployment", tags=["AI"])
async def create_ai_deployment(
    node: AIModelDeployment,
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Create or save an AI model deployment node to the knowledge graph.

    Nested collections (storage, input/output, requirements, performance
    information, live monitoring) may be supplied inline; give nested nodes an
    explicit ``uri`` to keep them individually addressable in the graph.

    **Important**: All existing information related to this node will be
    completely removed before adding the new node.

    If you want to update a node without removing all its old information,
    use the `POST /kg/node` update endpoint instead.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        if result:
            # (Re)start the runtime invoker whenever the deployment is saved,
            # mirroring how POST /dataspace/management restarts its connector.
            update_deployment_invoker(
                node, replace=True, username=current_user.username
            )
        return {"result": result}
    except Exception as e:
        logger.error(f"Error saving AI deployment node {node}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/ai_deployment/deployment",
    tags=["AI"],
    response_model_exclude_none=True,
    response_model=AIModelDeployment,
    summary="Get AI Deployment",
)
async def get_ai_deployment(
    node_uri: str,
    depth: int = DEFAULT_AI_DEPLOYMENT_DEPTH,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get an AI model deployment node from the knowledge graph by its URI.

    The default `depth` is high enough to return the nested deployment
    collections (storage, performance information, live monitoring, ...) in a
    single request.
    """
    try:
        return sindit_kg_connector.load_node_by_uri(node_uri, depth=depth)
    except Exception as e:
        logger.error(f"Error getting AI deployment node {node_uri}: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@app.get(
    "/ai_deployment/deployments",
    tags=["AI"],
    response_model_exclude_none=True,
    response_model=list[AIModelDeployment],
    summary="Get all AI Deployments",
)
async def get_all_ai_deployments(
    depth: int = DEFAULT_AI_DEPLOYMENT_DEPTH,
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
) -> list:
    """
    Get all AI model deployment nodes from the knowledge graph (paginated).
    """
    try:
        return sindit_kg_connector.load_nodes_by_class(
            str(AIModelDeployment.CLASS_URI),
            depth=depth,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Error getting AI deployment nodes: {e}")
        raise HTTPException(status_code=404, detail=str(e))

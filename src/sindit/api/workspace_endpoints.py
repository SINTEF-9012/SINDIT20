from fastapi import HTTPException, Depends
from sindit.initialize_kg_connectors import sindit_kg_connector
from sindit.api.authentication_endpoints import User, get_current_active_user

from sindit.util.log import logger

from sindit.api.api import app


@app.get(
    "/ws/get",
    tags=["Workspace"],
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "workspace_uri": "new-graph-uri",
                    }
                }
            },
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to get workspace: error message"}
                }
            },
        },
    },
)
async def get_workspace(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the name (uri) of the current workspace.
    """
    try:
        return {"workspace_uri": sindit_kg_connector.get_graph_uri()}
    except Exception as e:
        logger.error(f"Error getting workspace: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@app.get(
    "/ws/list",
    tags=["Workspace"],
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": [
                        "workspace1",
                        "workspace2",
                        "workspace3",
                    ]
                }
            },
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to get workspaces: error message"}
                }
            },
        },
    },
)
async def get_workspaces(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a list of all available workspaces.
    """
    try:
        return sindit_kg_connector.get_graph_uris()
    except Exception as e:
        logger.error(f"Error getting workspaces: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@app.post(
    "/ws/switch",
    tags=["Workspace"],
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "workspace_uri": "new-graph-uri",
                    }
                }
            },
        },
        400: {
            "description": "Bad request",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to switch workspace: error message"}
                }
            },
        },
    },
)
async def switch_workspace(
    workspace_uri: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Switch to a new workspace.
    """
    try:
        graph_uri = sindit_kg_connector.set_graph_uri(workspace_uri.strip())
        return {"workspace_uri": graph_uri}

        # TODO: switching to a new workspace should also
        # stop/clean up all connections and properties

    except Exception as e:
        logger.error(f"Error setting workspace: {e}")
        raise HTTPException(status_code=400, detail=str(e))

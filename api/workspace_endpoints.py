from fastapi import HTTPException
from initialize_kg_connectors import sindit_kg_connector

from util.log import logger

from api.api import app


@app.get(
    "/ws/get",
    tags=["Workspace"],
)
async def get_workspace():
    """
    Get the name (uri) of the current workspace.
    """
    try:
        return {"workspace_uri": sindit_kg_connector.get_graph_uri()} 
    except Exception as e:
        logger.error(f"Error getting workspace: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    
    
@app.post(
    "/ws/switch",
    tags=["Workspace"],
)
async def switch_workspace(
    workspace_uri: str,
):
    """
    Switch to a new workspace.
    """
    try:
        graph_uri = sindit_kg_connector.set_graph_uri(workspace_uri)
        return {"workspace_uri": graph_uri}
    
        #TODO: switching to a new workspace should also stop/clean up all connections and properties
        
    except Exception as e:
        logger.error(f"Error setting workspace: {e}")
        raise HTTPException(status_code=400, detail=str(e))
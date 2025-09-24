from typing import List
from fastapi import HTTPException, Depends
from sindit.initialize_kg_connectors import sindit_kg_connector
from sindit.api.authentication_endpoints import User, get_current_active_user

from sindit.knowledge_graph.dataspace_model import DataspaceManagement
from sindit.util.log import logger

from sindit.api.api import app


@app.get("/dataspace/types", tags=["Dataspace"])
async def get_all_dataspace_node_types(
    current_user: User = Depends(get_current_active_user),
) -> list:
    """
    Get all dataspace node types.
    """
    try:
        return sindit_kg_connector.get_all_dataspace_node_types()
    except Exception as e:
        logger.error(f"Error getting dataspace node types: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/dataspace", tags=["Dataspace"])
async def get_all_dataspace_nodes(
    current_user: User = Depends(get_current_active_user),
) -> List[DataspaceManagement]:
    """
    Get all dataspace nodes.
    """
    try:
        return sindit_kg_connector.get_all_dataspace_nodes()
    except Exception as e:
        logger.error(f"Error getting dataspace nodes: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/dataspace/management", tags=["Dataspace"])
async def create_dataspace_management(
    node: DataspaceManagement,
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Create a dataspace management node.
    """
    try:
        result = sindit_kg_connector.save_node(node)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error creating dataspace management node: {e}")
        raise HTTPException(status_code=404, detail=str(e))

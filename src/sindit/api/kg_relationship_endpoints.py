from typing import List, Union
from fastapi import HTTPException, Depends
from sindit.initialize_kg_connectors import sindit_kg_connector
from sindit.api.authentication_endpoints import User, get_current_active_user

from sindit.knowledge_graph.relationship_model import (
    AbstractRelationship,
    ConsistOfRelationship,
    PartOfRelationship,
    ConnectedToRelationship,
    DependsOnRelationship,
    DerivedFromRelationship,
    MonitorsRelationship,
    ControlsRelationship,
    SimulatesRelationship,
    UsesRelationship,
    CommunicatesWithRelationship,
    IsTypeOfRelationship,
)
from sindit.util.log import logger

from sindit.api.api import app


@app.get("/kg/relationship_types", tags=["Knowledge Graph"])
async def get_all_relationship_types(
    current_user: User = Depends(get_current_active_user),
) -> list:
    """
    Get all relationship types.
    """
    try:
        return sindit_kg_connector.get_all_relationship_types()
    except Exception as e:
        logger.error(f"Error getting relationship types: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/kg/relationship", tags=["Knowledge Graph"])
async def create_relationship(
    relationship: Union[
        ConsistOfRelationship,
        PartOfRelationship,
        ConnectedToRelationship,
        DependsOnRelationship,
        DerivedFromRelationship,
        MonitorsRelationship,
        ControlsRelationship,
        SimulatesRelationship,
        UsesRelationship,
        CommunicatesWithRelationship,
        AbstractRelationship,
        IsTypeOfRelationship,
    ],
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a relationship between two assets.
    """
    try:
        result = sindit_kg_connector.save_node(relationship)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error creating relationship {relationship}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/kg/relationship_by_node",
    tags=["Knowledge Graph"],
    response_model_exclude_none=True,
    response_model=List[
        Union[
            ConsistOfRelationship,
            PartOfRelationship,
            ConnectedToRelationship,
            DependsOnRelationship,
            DerivedFromRelationship,
            MonitorsRelationship,
            ControlsRelationship,
            SimulatesRelationship,
            UsesRelationship,
            CommunicatesWithRelationship,
            AbstractRelationship,
            IsTypeOfRelationship,
        ]
    ],
)
async def get_relationship_by_node(
    node_uri: str, current_user: User = Depends(get_current_active_user)
):
    """
    Get a relationship by URI of either the source or target node.
    This will return all relationships that are connected to the node.
    """
    try:
        return sindit_kg_connector.get_relationships_by_node(node_uri)
    except Exception as e:
        logger.error(f"Error getting relationship by URI: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@app.get(
    "/kg/relationship",
    tags=["Knowledge Graph"],
    response_model_exclude_none=True,
    response_model=List[
        Union[
            ConsistOfRelationship,
            PartOfRelationship,
            ConnectedToRelationship,
            DependsOnRelationship,
            DerivedFromRelationship,
            MonitorsRelationship,
            ControlsRelationship,
            SimulatesRelationship,
            UsesRelationship,
            CommunicatesWithRelationship,
            AbstractRelationship,
            IsTypeOfRelationship,
        ]
    ],
)
async def get_all_relationships(current_user: User = Depends(get_current_active_user)):
    """
    Get all relationships.
    """
    try:
        return sindit_kg_connector.get_all_relationships()
    except Exception as e:
        logger.error(f"Error getting all relationships: {e}")
        raise HTTPException(status_code=404, detail=str(e))

from typing import List, Union
from fastapi import HTTPException
from initialize_kg_connectors import sindit_kg_connector

from knowledge_graph.relationship_model import (
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
)
from util.log import logger

from api.api import app


@app.get("/kg/relationship_types", tags=["Knowledge Graph"])
async def get_all_relationship_types():
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
    relationship: Union[AbstractRelationship, ConsistOfRelationship]
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
        ]
    ],
)
async def get_relationship_by_node(node_uri: str):
    """
    Get a relationship by its URI.
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
        ]
    ],
)
async def get_all_relationships():
    """
    Get all relationships.
    """
    try:
        return sindit_kg_connector.get_all_relationships()
    except Exception as e:
        logger.error(f"Error getting all relationships: {e}")
        raise HTTPException(status_code=404, detail=str(e))

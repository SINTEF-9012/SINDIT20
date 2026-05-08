from typing import Annotated, Any, ClassVar, Union

from pydantic import Discriminator, Tag
from sindit.common.semantic_knowledge_graph.rdf_model import RDFModel, URIRefNode
from rdflib import Literal, URIRef

from sindit.knowledge_graph.graph_model import GRAPH_MODEL, AbstractAsset


class AbstractRelationship(RDFModel):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.AbstractRelationship

    mapping: ClassVar[dict] = {
        "relationshipDescription": GRAPH_MODEL.relationshipDescription,
        "relationshipType": GRAPH_MODEL.relationshipType,
        "relationshipSemanticID": GRAPH_MODEL.relationshipSemanticID,
        "relationshipValue": GRAPH_MODEL.relationshipValue,
        "relationshipUnit": GRAPH_MODEL.relationshipUnit,
        "relationshipSource": GRAPH_MODEL.relationshipSource,
        "relationshipTarget": GRAPH_MODEL.relationshipTarget,
    }

    relationshipDescription: Literal | str = None
    relationshipType: Literal | str = None
    relationshipSemanticID: Union[URIRefNode, Literal, str] = None
    relationshipValue: Literal | dict | Any = None
    relationshipUnit: Union[URIRefNode, Literal, str] = None
    relationshipSource: Union[URIRefNode, AbstractAsset] = None
    relationshipTarget: Union[URIRefNode, AbstractAsset] = None


class ConsistOfRelationship(AbstractRelationship):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.ConsistOfRelationship

    mapping: ClassVar[dict] = {
        **AbstractRelationship.mapping,
    }

    relationshipType: Literal | str = "consistsOf"


class PartOfRelationship(AbstractRelationship):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.PartOfRelationship

    mapping: ClassVar[dict] = {
        **AbstractRelationship.mapping,
    }

    relationshipType: Literal | str = "partOf"


# ConnectedToRelationship
class ConnectedToRelationship(AbstractRelationship):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.ConnectedToRelationship

    mapping: ClassVar[dict] = {
        **AbstractRelationship.mapping,
    }

    relationshipType: Literal | str = "connectedTo"


# DependsOnRelationship
class DependsOnRelationship(AbstractRelationship):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.DependsOnRelationship

    mapping: ClassVar[dict] = {
        **AbstractRelationship.mapping,
    }

    relationshipType: Literal | str = "dependsOn"


# DerivedFromRelationship
class DerivedFromRelationship(AbstractRelationship):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.DerivedFromRelationship

    mapping: ClassVar[dict] = {
        **AbstractRelationship.mapping,
    }

    relationshipType: Literal | str = "derivedFrom"


# MonitorsRelationship
class MonitorsRelationship(AbstractRelationship):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.MonitorsRelationship

    mapping: ClassVar[dict] = {
        **AbstractRelationship.mapping,
    }

    relationshipType: Literal | str = "monitors"


# ControlsRelationship
class ControlsRelationship(AbstractRelationship):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.ControlsRelationship

    mapping: ClassVar[dict] = {
        **AbstractRelationship.mapping,
    }

    relationshipType: Literal | str = "controls"


# SimulatesRelationship
class SimulatesRelationship(AbstractRelationship):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.SimulatesRelationship

    mapping: ClassVar[dict] = {
        **AbstractRelationship.mapping,
    }

    relationshipType: Literal | str = "simulates"


# UsesRelationship
class UsesRelationship(AbstractRelationship):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.UsesRelationship

    mapping: ClassVar[dict] = {
        **AbstractRelationship.mapping,
    }

    relationshipType: Literal | str = "uses"


# CommunicatesWithRelationship
class CommunicatesWithRelationship(AbstractRelationship):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.CommunicatesWithRelationship

    mapping: ClassVar[dict] = {
        **AbstractRelationship.mapping,
    }

    relationshipType: Literal | str = "communicatesWith"


# IsTypeOfRelationship
class IsTypeOfRelationship(AbstractRelationship):
    CLASS_URI: ClassVar[URIRef] = GRAPH_MODEL.IsTypeOfRelationship

    mapping: ClassVar[dict] = {
        **AbstractRelationship.mapping,
    }

    relationshipType: Literal | str = "isTypeOf"


RelationshipURIClassMapping = {
    AbstractRelationship.CLASS_URI: AbstractRelationship,
    ConsistOfRelationship.CLASS_URI: ConsistOfRelationship,
    PartOfRelationship.CLASS_URI: PartOfRelationship,
    ConnectedToRelationship.CLASS_URI: ConnectedToRelationship,
    DependsOnRelationship.CLASS_URI: DependsOnRelationship,
    DerivedFromRelationship.CLASS_URI: DerivedFromRelationship,
    MonitorsRelationship.CLASS_URI: MonitorsRelationship,
    ControlsRelationship.CLASS_URI: ControlsRelationship,
    SimulatesRelationship.CLASS_URI: SimulatesRelationship,
    UsesRelationship.CLASS_URI: UsesRelationship,
    CommunicatesWithRelationship.CLASS_URI: CommunicatesWithRelationship,
    IsTypeOfRelationship.CLASS_URI: IsTypeOfRelationship,
}

_KNOWN_RELATIONSHIP_TYPES = {
    "consistsOf",
    "partOf",
    "connectedTo",
    "dependsOn",
    "derivedFrom",
    "monitors",
    "controls",
    "simulates",
    "uses",
    "communicatesWith",
    "isTypeOf",
}


def _relationship_discriminator(v) -> str:
    if isinstance(v, dict):
        rel_type = v.get("relationshipType")
    else:
        rel_type = getattr(v, "relationshipType", None)
        if isinstance(rel_type, list):
            rel_type = rel_type[0] if rel_type else None
    if rel_type and str(rel_type) in _KNOWN_RELATIONSHIP_TYPES:
        return str(rel_type)
    return "abstract"


RelationshipUnion = Annotated[
    Union[
        Annotated[ConsistOfRelationship, Tag("consistsOf")],
        Annotated[PartOfRelationship, Tag("partOf")],
        Annotated[ConnectedToRelationship, Tag("connectedTo")],
        Annotated[DependsOnRelationship, Tag("dependsOn")],
        Annotated[DerivedFromRelationship, Tag("derivedFrom")],
        Annotated[MonitorsRelationship, Tag("monitors")],
        Annotated[ControlsRelationship, Tag("controls")],
        Annotated[SimulatesRelationship, Tag("simulates")],
        Annotated[UsesRelationship, Tag("uses")],
        Annotated[CommunicatesWithRelationship, Tag("communicatesWith")],
        Annotated[IsTypeOfRelationship, Tag("isTypeOf")],
        Annotated[AbstractRelationship, Tag("abstract")],
    ],
    Discriminator(_relationship_discriminator),
]

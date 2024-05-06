from typing import Any, ClassVar, List, Union, get_type_hints
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator
from rdflib import RDF, RDFS, XSD, Graph, URIRef
from rdflib.term import BNode, Literal, Node
from typing_extensions import Annotated


class PropertyNotSetException(Exception):
    """Required property of RDFModel is not set."""

    pass


class MapTo:
    """Class to represent bidirectional relationships between individuals"""

    def __init__(self, value: Node, inverse: Node = None):
        self.value = value
        self.inverse = inverse


class URIRefNode(BaseModel):
    uri: Annotated[Union[URIRef, str], Field(validate_default=True)]

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    @field_validator("uri", mode="before")
    @classmethod
    def uri_validator(cls, v):
        if isinstance(v, str):
            return URIRef(v)
        return v

    def __str__(self):
        return f"uri: {self.uri}"


class RDFModel(BaseModel):
    """RDF Model"""

    CLASS_URI: ClassVar[URIRef] = None

    class_uri: Annotated[Union[URIRef, str], Field(validate_default=True)] = CLASS_URI

    mapping: ClassVar[dict] = None

    uri: Annotated[Union[URIRef, BNode], Field(validate_default=True)] = None
    label: Literal | str = None

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    @field_validator("uri", mode="before")
    @classmethod
    def uri_validator(cls, v):
        if v is None:
            return BNode(str(uuid4()))
        elif isinstance(v, str):
            return URIRef(v)
        return v

    @field_validator("class_uri", mode="before")
    @classmethod
    def class_uri_validator(cls, v):
        # if v is none or empty, set it to cls.CLASS_URI
        if v is None or v == "":
            v = cls.CLASS_URI
        elif isinstance(v, str):
            v = URIRef(v)

        # if v is not the same as cls.CLASS_URI, raise error
        if v != cls.CLASS_URI:
            raise ValueError(f"class_uri must be the same as {cls.__name__}.CLASS_URI")

        return v

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.CLASS_URI is None:
            raise PropertyNotSetException(
                f"class_uri in {self.__class__.__name__} class is not defined."
            )
        if self.mapping is None:
            raise PropertyNotSetException(
                f"mapping in {self.__class__.__name__} class is not defined."
            )

        if hasattr(self, "label"):
            self.mapping["label"] = RDFS.label

    """ def assign_constructor_vars(self, local_vars: locals):
        for key, val in local_vars.items():
            if key != "self" and key != "kwargs" and key != "__class__":
                # if isinstance(val, URIRef)
                #   or isinstance(val, BNode)
                #   or isinstance(val, Literal):
                #     new_val = val
                # elif isinstance(val, str):
                #     new_val = Literal(val, datatype=XSD.string)
                # elif isinstance(val, int):
                #     new_val = Literal(val, datatype=XSD.integer)
                # elif isinstance(val, float):
                #     new_val = Literal(val, datatype=XSD.float)
                # elif isinstance(val, bool):
                #     new_val = Literal(val, datatype=XSD.boolean)
                # else:
                #     new_val = val

                # setattr(self, key, new_val)

                self.__setattr__(key, val)

        # Generate a blank node if self.uri is not set.
        if not hasattr(self, "uri"):
            self.uri = BNode(str(uuid4()))

        if hasattr(self, "label"):
            self.mapping["label"] = RDFS.label """

    """def __str__(self):
        if hasattr(self, 'label'):
            return f'<{self.label}>'
        else:
            return f'<{self.uri}>' """

    def __str__(self):
        ret_str = f"uri: {self.uri}\n"
        for key, rdf_property in self.mapping.items():
            value = getattr(self, key, None)
            if value is not None:
                # if value is an object of RDFModel, add newline before value
                if isinstance(value, RDFModel):
                    ret_str += f"{key}:\n"
                    ret_str += f"{value}\n"
                elif isinstance(value, list) or isinstance(value, tuple):
                    ret_str += f"{key}:\n"
                    for item in value:
                        if isinstance(item, RDFModel):
                            ret_str += f"{item}\n"
                        else:
                            ret_str += f"\t{item}\n"
                else:
                    ret_str += f"{key}: {value}\n"

        # indent the string
        ret_str = "\n".join(["\t" + line for line in ret_str.split("\n")])
        return f"<{self.__class__.__name__}:\n{ret_str}\n>"

    """ def __setattr__(self, name: str, value: Any) -> None:
        if (
            isinstance(value, URIRef)
            or isinstance(value, BNode)
            or isinstance(value, Literal)
        ):
            new_val = value
        elif isinstance(value, str):
            new_val = Literal(value, datatype=XSD.string)
        elif isinstance(value, int):
            new_val = Literal(value, datatype=XSD.integer)
        elif isinstance(value, float):
            new_val = Literal(value, datatype=XSD.float)
        elif isinstance(value, bool):
            new_val = Literal(value, datatype=XSD.boolean)
        else:
            new_val = value

        super().__setattr__(name, new_val) """

    def _process_attr(self, value: Any) -> None:
        if isinstance(value, URIRefNode):
            new_val = value.uri
        elif (
            isinstance(value, URIRef)
            or isinstance(value, BNode)
            or isinstance(value, Literal)
        ):
            new_val = value
        elif isinstance(value, str):
            new_val = Literal(value, datatype=XSD.string)
        elif isinstance(value, int):
            new_val = Literal(value, datatype=XSD.integer)
        elif isinstance(value, float):
            new_val = Literal(value, datatype=XSD.float)
        elif isinstance(value, bool):
            new_val = Literal(value, datatype=XSD.boolean)
        else:
            new_val = value

        return new_val

    def g(self) -> Graph:
        """Lazy load the rdflib.Graph object."""
        self.rdf()
        return self._g

    def _add(self, s: Node, p: Node, o: Node):
        if isinstance(p, URIRef):
            self._g.add((s, p, o))
        elif isinstance(p, MapTo):
            self._g.add((s, p.value, o))
            self._g.add((o, p.inverse, s))
        else:
            raise TypeError(f"Unexpected type {type(p)} for value {p}")

    def rdf(self, format: str = "turtle") -> str:
        # Set/reset g
        self._g = Graph()

        # if it is the basemodel, return empty graph
        if self.class_uri == RDFModel.CLASS_URI:
            return self._g.serialize(format=format)

        self._g.add((self.uri, RDF.type, self.class_uri))
        for key, rdf_property in self.mapping.items():
            value = getattr(self, key, None)
            value = self._process_attr(value)
            # Check for optional values and skip if they are None.
            if value is not None:
                if isinstance(value, RDFModel):
                    self._add(self.uri, rdf_property, value.uri)
                    # if type(value.uri) == BNode:
                    #     self._g += value.g
                    self._g += value.g()
                elif isinstance(value, list) or isinstance(value, tuple):
                    for item in value:
                        item = self._process_attr(item)
                        if isinstance(item, RDFModel):
                            self._add(self.uri, rdf_property, item.uri)
                            # if type(item.uri) == BNode:
                            #     self._g += item.g
                            self._g += item.g()
                        elif isinstance(item, URIRef):
                            self._add(self.uri, rdf_property, item)
                        else:
                            raise TypeError(
                                f"Unexpected type {type(item)} for value {item}"
                            )
                elif isinstance(value, Literal) or isinstance(value, URIRef):
                    self._add(self.uri, rdf_property, value)
                else:
                    raise TypeError(f"Unexpected type {type(value)} for value {value}")
        return self._g.serialize(format=format)

    # @computed_field
    # @property
    # def rdf(self) -> str:
    #     return self._compute_rdf()

    def deserialize(
        g: Graph,
        node_class=None,
        node_uri: URIRef = None,
        class_uri: URIRef = None,
        created_individuals: dict = {},
        uri_class_mapping: dict = {},
    ):
        # if len(g) <= 0:
        #    raise ValueError("Graph is empty.")

        # for rdf triple in g
        return_individuals = created_individuals
        if return_individuals is None or return_individuals == {}:
            return_individuals = {}

        if node_uri is None and class_uri is None:
            raise ValueError("node_uri or class_uri must be set")

        if node_uri is not None:
            individuals = [node_uri]
            # get class_uri from the graph
            if node_class is None:
                class_uri = g.value(subject=node_uri, predicate=RDF.type)
                node_class = uri_class_mapping.get(class_uri)

        elif class_uri is not None:
            individuals = [ind for ind, _, _ in g.triples((None, RDF.type, class_uri))]
            if node_class is None:
                node_class = uri_class_mapping.get(class_uri)

        if node_class is None:
            raise ValueError(
                "Cannot determine node_class from class_uri "
                "or node_uri. "
                "Either the class_uri is not defined in the model "
                "or the node does not exist "
                "in the knowledge graph"
            )

        for ind in individuals:
            # for ind, _, _ in g.triples(None, RDF.type, class_uri):
            if str(ind) not in return_individuals:
                new_ind = node_class(uri=ind)
                return_individuals[str(ind)] = new_ind

                for att_name, att_uri in node_class.mapping.items():
                    if isinstance(att_uri, MapTo):
                        att_uri = att_uri.value
                    # att_value = g.value(subject=ind, predicate=att_uri)
                    att_value = [
                        value for _, _, value in g.triples((ind, att_uri, None))
                    ]

                    if att_value is not None:
                        return_individuals = RDFModel._set_att_from_graph(
                            new_ind,
                            g,
                            ind,
                            att_name,
                            att_value,
                            return_individuals,
                            uri_class_mapping,
                        )

        return return_individuals

    def _set_obj_att(ind_obj, att_name, att_value):
        att_type_hint = get_type_hints(ind_obj.__class__).get(att_name)
        if att_type_hint is not None:
            # if the type hint is a list
            # if(str(att_type_hint).startswith('typing.List') ):
            # print(att_type_hint)
            # print(type(att_type_hint))

            if "__origin__" in dir(att_type_hint) and (
                att_type_hint.__origin__ == list or att_type_hint.__origin__ == List
            ):
                # get the exising value
                existing_value = getattr(ind_obj, att_name, None)
                # if the existing value is not None
                if existing_value is not None:
                    # append the new value to the existing value
                    setattr(ind_obj, att_name, existing_value + [att_value])
                # if the existing value is None
                else:
                    # set the value as a list
                    setattr(ind_obj, att_name, [att_value])
            else:
                setattr(ind_obj, att_name, att_value)
        else:
            setattr(ind_obj, att_name, att_value)

    def _set_att_from_graph(
        ind_obj,
        g: Graph,
        ind: URIRef,
        att_name: str,
        att_value: Any,
        created_individuals: dict = {},
        uri_class_mapping: dict = {},
    ):
        return_individuals = created_individuals

        # value = g.value(subject=ind, predicate=att_uri)

        # if value is not None:
        value = att_value
        if isinstance(value, Literal):
            RDFModel._set_obj_att(ind_obj, att_name, value)
        elif isinstance(value, URIRef) or isinstance(value, BNode):
            if str(value) in return_individuals:
                RDFModel._set_obj_att(ind_obj, att_name, return_individuals[str(value)])
            else:
                new_node_uri = value
                new_node_class_uri = g.value(subject=value, predicate=RDF.type)
                if (
                    new_node_class_uri is not None
                    and new_node_class_uri in uri_class_mapping
                ):
                    new_node_class = uri_class_mapping.get(new_node_class_uri)
                    new_node_class_uri = URIRef(new_node_class_uri)
                    return_individuals = RDFModel.deserialize(
                        g,
                        new_node_class,
                        new_node_uri,
                        new_node_class_uri,
                        return_individuals,
                        uri_class_mapping,
                    )
                    if str(value) in return_individuals:
                        RDFModel._set_obj_att(
                            ind_obj, att_name, return_individuals[str(value)]
                        )
                    else:
                        raise ValueError(
                            "Could not create object for {value} with class "
                            "{new_node_class_uri}"
                        )
                else:
                    # Instead of setting value to URIRef, create a URIRefNode
                    value = URIRefNode(uri=value)
                    RDFModel._set_obj_att(ind_obj, att_name, value)

        elif isinstance(value, list):
            for item in value:
                return_individuals = RDFModel._set_att_from_graph(
                    ind_obj,
                    g,
                    ind,
                    att_name,
                    item,
                    return_individuals,
                    uri_class_mapping,
                )
        else:
            raise TypeError(f"Unexpected type {type(value)} for value {value}")

        return return_individuals

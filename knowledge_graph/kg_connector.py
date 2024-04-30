from io import StringIO

import pandas as pd
from rdflib import Graph, URIRef

from common.semantic_knowledge_graph.rdf_model import RDFModel
from common.semantic_knowledge_graph.SemanticKGPersistenceService import (
    SemanticKGPersistenceService,
)
from knowledge_graph.graph_model import URIClassMapping

load_node_query_file = "knowledge_graph/queries/load_node.sparql"
load_nodes_query_file = "knowledge_graph/queries/load_nodes.sparql"
delete_node_query_file = "knowledge_graph/queries/delete_node.sparql"
delete_nodes_query_file = "knowledge_graph/queries/delete_nodes.sparql"
insert_data_query_file = "knowledge_graph/queries/insert_data.sparql"
get_uris_by_class_uri_query_file = (
    "knowledge_graph/queries/get_uris_by_class_uri.sparql"
)


class SINDITKGConnector:
    def __init__(self, kg_service: SemanticKGPersistenceService):
        self.__kg_service = kg_service

    def load_node_by_uri(
        self, node_uri: str, node_class, depth: int = 1, created_individuals: dict = {}
    ) -> RDFModel:
        # read the sparql query from the file
        with open(load_node_query_file, "r") as f:
            query_template = f.read()

        loop = depth
        full_graph = Graph()

        nodes = [URIRef(node_uri)]
        visited = set()
        while loop > 0:
            loop -= 1
            children = []
            while len(nodes) > 0:
                current_node_uri = nodes.pop()
                if current_node_uri in visited:
                    continue
                visited.add(current_node_uri)
                query = query_template.replace("[node_uri]", str(current_node_uri))
                query_result = self.__kg_service.graph_query(
                    query, "application/x-trig"
                )
                g = Graph()
                g.parse(data=query_result, format="trig")
                if len(g) > 0 and loop > 0:
                    for _, _, o in g.triples((current_node_uri, None, None)):
                        if isinstance(o, URIRef):
                            children.append(o)

                full_graph += g

            nodes = children
            if len(nodes) == 0:
                break

        # print(f"Lenght of g: {len(full_graph)}")

        ret = RDFModel.deserialize(
            node_class,
            full_graph,
            URIRef(node_uri),
            created_individuals=created_individuals,
            uri_class_mapping=URIClassMapping,
        )
        created_individuals.update(ret)
        node = ret[node_uri]

        # print(node)
        return node

    def load_nodes_by_class(self, class_uri, depth: int = 1) -> list:
        with open(get_uris_by_class_uri_query_file, "r") as f:
            query_template = f.read()

        query = query_template.replace("[class_uri]", class_uri)
        query_result = self.__kg_service.graph_query(query, "text/csv")
        df = pd.read_csv(StringIO(query_result), sep=",")
        created_individuals = {}
        nodes = []
        for uri in df["node"]:
            ret = self.load_node_by_uri(
                uri,
                URIClassMapping[class_uri],
                depth,
                created_individuals=created_individuals,
            )
            nodes.append(ret)

        # print(created_individuals)
        # print(nodes)
        return nodes

    def delete_node(self, node_uri: str) -> bool:
        """Delete a node from the knowledge graph."""
        with open(delete_node_query_file, "r") as f:
            query_template = f.read()

        query = query_template.replace("[node_uri]", node_uri)
        query_result = self.__kg_service.graph_update(query)

        return query_result

    def save_node(
        self,
        node: RDFModel,
    ) -> bool:
        """Save a node to the knowledge graph. Create a new node if it
        does not exist, update it otherwise.
        This method also update the children nodes if they are serialized in
        the subgraph of the root node.
        Warning: This method will delete attributes of the nodes that are not
        serialized in the subgraph.
        """

        g = node.g
        # get the list of subject in g
        subjects = set([s for s, _, _ in g])
        # concat the subject as a string, each surrounded by < and >,
        # separated by a space
        subjects = " ".join([f"<{str(s)}>" for s in subjects])
        with open(delete_nodes_query_file, "r") as f:
            query_template = f.read()

        query = query_template.replace("[nodes_uri]", subjects)
        query_result = self.__kg_service.graph_update(query)

        with open(insert_data_query_file, "r") as f:
            query_template = f.read()

        graph_data = str(g.serialize(format="longturtle"))
        # extract the line starting with PREFIX or prefix,
        # and the data without the prefixes
        prefixes = ""
        data = ""
        for line in graph_data.split("\n"):
            if line.startswith("PREFIX") or line.startswith("prefix"):
                prefixes += line + "\n"
            else:
                data += line + "\n"

        query = query_template.replace("[prefixes]", prefixes)

        query = query.replace("[data]", data)
        query_result = self.__kg_service.graph_update(query)
        # print(f"inserted: {query_result}")

        return query_result

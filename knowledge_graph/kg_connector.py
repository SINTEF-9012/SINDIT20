from io import StringIO

import pandas as pd
from common.semantic_knowledge_graph.rdf_model import RDFModel
from common.semantic_knowledge_graph.SemanticKGPersistenceService import (
    SemanticKGPersistenceService,
)
from knowledge_graph.graph_model import (
    KG_NS,
    NodeURIClassMapping,
)
from knowledge_graph.relationship_model import RelationshipURIClassMapping
from rdflib import RDF, XSD, Graph, URIRef
from rdflib.term import _is_valid_uri

# from initialize_connectors import update_connection_node, update_propery_node


load_node_query_file = "knowledge_graph/queries/load_node.sparql"
load_nodes_query_file = "knowledge_graph/queries/load_nodes.sparql"
delete_node_query_file = "knowledge_graph/queries/delete_node.sparql"
delete_nodes_query_file = "knowledge_graph/queries/delete_nodes.sparql"
insert_data_query_file = "knowledge_graph/queries/insert_data.sparql"
insert_delete_query_file = "knowledge_graph/queries/insert_delete.sparql"
insert_delete_data_query_file = "knowledge_graph/queries/insert_delete_data.sparql"
get_uris_by_class_uri_query_file = (
    "knowledge_graph/queries/get_uris_by_class_uri.sparql"
)
get_class_uri_by_uri_query_file = "knowledge_graph/queries/get_class_uri_by_uri.sparql"
list_named_graphs_query_file = "knowledge_graph/queries/list_named_graphs.sparql"
search_unit_query_file = "knowledge_graph/queries/find_unit.sparql"
get_all_units_query_file = "knowledge_graph/queries/get_all_units.sparql"
search_unit_by_uri_query_file = "knowledge_graph/queries/find_unit_by_uri.sparql"
get_all_relationship_types_query_file = (
    "knowledge_graph/queries/get_all_relationship_types.sparql"
)

get_relationships_by_node_query_file = (
    "knowledge_graph/queries/get_relationships_by_node.sparql"
)


class SINDITKGConnector:
    def __init__(self, kg_service: SemanticKGPersistenceService):
        self.__kg_service = kg_service
        self.__graph_uri = KG_NS.DefaultGraph

    def get_graph_uri(self):
        return str(self.__graph_uri)

    def set_graph_uri(self, uri: str):
        try:
            # check if uri is valid, otherwise concat it with the default graph uri
            if not uri.startswith("http"):
                uri = str(KG_NS) + uri
            if not _is_valid_uri(uri):
                raise Exception(f"Invalid uri: {uri}")
            self.__graph_uri = URIRef(uri)
            return str(self.__graph_uri)
        except Exception as e:
            raise Exception(f"Failed to set the graph uri. Reason: {e}")

    def get_graph_uris(self):
        with open(list_named_graphs_query_file, "r") as f:
            try:
                query = f.read()
                query_result = self.__kg_service.graph_query(query, "text/csv")
                df = pd.read_csv(StringIO(query_result), sep=",")
                return df["g"].to_list()
            except Exception as e:
                raise Exception(f"Failed to get the graph uris. Reason: {e}")

    def search_unit(self, search_term: str):
        with open(search_unit_query_file, "r") as f:
            try:
                query_template = f.read()
                query = query_template.replace("[search_term]", search_term)
                query_result = self.__kg_service.graph_query(query, "text/csv")
                df = pd.read_csv(StringIO(query_result), sep=",")

                if not df.empty:
                    # rename the columns unit to uri
                    df.rename(columns={"unit": "uri"}, inplace=True)
                    # convert the dataframe to a list of dictionaries, ignore nan values
                    # replace nan with None
                    df_dict = df.apply(lambda x: x.dropna().to_dict(), axis=1).tolist()

                    return df_dict

                return []

            except Exception as e:
                raise Exception(f"Failed to search for the unit. Reason: {e}")

    def get_unit_by_uri(self, uri: str):
        with open(search_unit_by_uri_query_file, "r") as f:
            try:
                query_template = f.read()
                query = query_template.replace("[unit_uri]", uri)
                query_result = self.__kg_service.graph_query(query, "text/csv")
                df = pd.read_csv(StringIO(query_result), sep=",")

                if not df.empty:
                    # rename the columns unit to uri
                    df.rename(columns={"unit": "uri"}, inplace=True)
                    # convert the dataframe to a list of dictionaries, ignore nan values
                    # replace nan with None
                    df_dict = df.apply(lambda x: x.dropna().to_dict(), axis=1).tolist()

                    return df_dict

                return []

            except Exception as e:
                raise Exception(f"Failed to search for the unit. Reason: {e}")

    def get_all_units(self):
        with open(get_all_units_query_file, "r") as f:
            try:
                query = f.read()
                query_result = self.__kg_service.graph_query(query, "text/csv")
                df = pd.read_csv(StringIO(query_result), sep=",")

                if not df.empty:
                    # rename the columns unit to uri
                    df.rename(columns={"unit": "uri"}, inplace=True)
                    # convert the dataframe to a list of dictionaries, ignore nan values
                    # replace nan with None
                    df_dict = df.apply(lambda x: x.dropna().to_dict(), axis=1).tolist()

                    return df_dict

                return []

            except Exception as e:
                raise Exception(f"Failed to get all units. Reason {e}")

    def get_all_data_types(self):
        list_data_types = []
        list_data_types.append({"uri": XSD.string, "label": "string"})
        list_data_types.append({"uri": XSD.integer, "label": "integer"})
        list_data_types.append({"uri": XSD.float, "label": "float"})
        list_data_types.append({"uri": XSD.boolean, "label": "boolean"})
        list_data_types.append(
            {"uri": XSD.dateTimeStamp, "label": "dateTime | dateTimeStamp"}
        )
        return list_data_types

    def load_node_by_uri(
        self,
        node_uri: str,
        node_class=None,
        depth: int = 1,
    ) -> RDFModel:
        ret = self._load_node(node_uri, node_class, depth)
        node = ret[node_uri]

        # print(f"node uri: {node_uri}, depth: {depth}")
        # print(node)
        return node

    def _load_node(
        self,
        node_uri: str,
        node_class=None,
        depth: int = 1,
        created_individuals: dict = {},
        uri_class_mapping: dict = NodeURIClassMapping,
    ) -> RDFModel:
        # read the sparql query from the file
        with open(load_node_query_file, "r") as f:
            query_template = f.read()
            if "[graph_uri]" in query_template:
                query_template = query_template.replace(
                    "[graph_uri]", str(self.__graph_uri)
                )

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
            full_graph,
            node_class,
            URIRef(node_uri),
            created_individuals=created_individuals,
            uri_class_mapping=uri_class_mapping,
        )

        return ret

    def load_nodes_by_class(
        self,
        class_uri: str,
        depth: int = 1,
        uri_class_mapping: dict = NodeURIClassMapping,
    ) -> list:
        with open(get_uris_by_class_uri_query_file, "r") as f:
            query_template = f.read()
            if "[graph_uri]" in query_template:
                query_template = query_template.replace(
                    "[graph_uri]", str(self.__graph_uri)
                )

        query = query_template.replace("[class_uri]", class_uri)
        query_result = self.__kg_service.graph_query(query, "text/csv")
        df = pd.read_csv(StringIO(query_result), sep=",")
        created_individuals = {}
        nodes = []
        for uri in df["node"]:
            ret = self._load_node(
                uri,
                None,
                depth,
                created_individuals=created_individuals,
                uri_class_mapping=uri_class_mapping,
            )
            created_individuals.update(ret)
            node = ret[uri]
            nodes.append(node)

        # print(created_individuals)
        # print(nodes)
        return nodes

    def load_all_nodes(
        self,
        uri_class_mapping: dict = NodeURIClassMapping,
    ) -> list:
        nodes = []
        for class_uri in uri_class_mapping.keys():
            nodes += self.load_nodes_by_class(class_uri, depth=1)

        node_uris = []
        return_nodes = []
        for node in nodes:
            if node.uri not in node_uris:
                return_nodes.append(node)
                node_uris.append(node.uri)
        return return_nodes

    def delete_node(self, node_uri: str) -> bool:
        """Delete a node from the knowledge graph."""
        with open(delete_node_query_file, "r") as f:
            query_template = f.read()
            if "[graph_uri]" in query_template:
                query_template = query_template.replace(
                    "[graph_uri]", str(self.__graph_uri)
                )

        query = query_template.replace("[node_uri]", node_uri)
        query_result = self.__kg_service.graph_update(query)

        if not query_result.ok:
            raise Exception(
                "Failed to delete the node. Reason: " + query_result.content
            )

        return query_result.ok

    def update_node(
        self,
        node_dict: dict,  # to accept any types of node
        overwrite: bool = True,  # otherwise, keep both old and new data
        uri_class_mapping: dict = NodeURIClassMapping,
    ) -> bool:
        """
        Update a node in the knowledge graph. If overwrite is True, the old data
        will be deleted and replaced with the new data. Otherwise, the old data
        will be kept and the new data will be added.
        """

        if "uri" not in node_dict:
            raise Exception("Node uri is required")

        # Remove class_uri from the node_dict
        if "class_uri" in node_dict:
            del node_dict["class_uri"]

        node_uri = node_dict["uri"]

        # g: Graph = node.g()
        # get the list of subject in g
        subjects = set()
        subjects.add(URIRef(node_uri))
        # Check the type of the subjects in the exising graph,
        # if different return error
        with open(get_class_uri_by_uri_query_file, "r") as f:
            query_template = f.read()
            if "[graph_uri]" in query_template:
                query_template = query_template.replace(
                    "[graph_uri]", str(self.__graph_uri)
                )

        node = None
        query = query_template.replace("[node_uri]", node_uri)
        query_result = self.__kg_service.graph_query(query, "text/csv")
        df = pd.read_csv(StringIO(query_result), sep=",")
        if len(df) > 0:
            class_uri = df["class"][0]
            node_class = uri_class_mapping.get(URIRef(class_uri))
            if node_class is not None:
                try:
                    node = node_class(**node_dict)
                    g = node.g()
                except Exception as e:
                    raise Exception(
                        f"Failed to update the node {node_uri}. Reason: {e}"
                    )

        if node is None:
            raise Exception(
                f"Cannnot find the class of the node {node_uri}. "
                "Try to save the node first if it is a new node."
            )

        subjects_str = " ".join([f"<{str(s)}>" for s in subjects])

        # Load the old data
        with open(load_nodes_query_file, "r") as f:
            query_template = f.read()

            if "[graph_uri]" in query_template:
                query_template = query_template.replace(
                    "[graph_uri]", str(self.__graph_uri)
                )

        query = query_template.replace("[nodes_uri]", subjects_str)
        query_result_old = self.__kg_service.graph_query(query, "application/x-trig")

        g_old = Graph()
        g_old.parse(data=query_result_old, format="trig")

        # Get the data to be removed
        g_remove = Graph()

        if overwrite:
            # Find triples in g_old that match the subject and predicate from g
            for s, p, _ in g:
                for s_old, p_old, o_old in g_old.triples((s, p, None)):
                    # Add the matching triples to the new graph
                    g_remove.add((s_old, p_old, o_old))
        else:
            # Find triples in g_old that match the triples from g
            for s, p, o in g:
                for s_old, p_old, o_old in g_old.triples((s, p, o)):
                    # Add the matching triples to the new graph
                    g_remove.add((s_old, p_old, o_old))

        try:
            with open(insert_delete_data_query_file, "r") as f:
                query_template = f.read()
                if "[graph_uri]" in query_template:
                    query_template = query_template.replace(
                        "[graph_uri]", str(self.__graph_uri)
                    )

            # For delete the old data
            query_template = query_template.replace("[nodes_uri]", subjects_str)

            graph_data = str(g.serialize(format="longturtle"))
            graph_remove_data = str(g_remove.serialize(format="longturtle"))
            # extract the line starting with PREFIX or prefix,
            # and the data without the prefixes
            prefixes = ""
            old_prefixes = ""
            insert_data = ""
            for line in graph_data.split("\n"):
                if line.startswith("PREFIX") or line.startswith("prefix"):
                    prefixes += line + "\n"
                else:
                    insert_data += line + "\n"

            delete_data = ""
            for line in graph_remove_data.split("\n"):
                if line.startswith("PREFIX") or line.startswith("prefix"):
                    old_prefixes += line + "\n"
                else:
                    delete_data += line + "\n"

            query = query_template.replace("[prefixes]", prefixes)
            query = query.replace("[insert_data]", insert_data)
            query = query.replace("[delete_data]", delete_data)

            query_result = self.__kg_service.graph_update(query)

            if not query_result.ok:
                raise Exception(f"{query_result.content}")

        except Exception as e:
            # self._restore_graph(g_old)
            raise Exception(f"Failed to update the node. Reason: {e}")

        return query_result.ok

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

        g = node.g()
        # get the list of subject in g
        subjects = set([s for s, _, _ in g])
        # Check the type of the subjects in the exising graph,
        # if different return error
        with open(get_class_uri_by_uri_query_file, "r") as f:
            query_template = f.read()
            if "[graph_uri]" in query_template:
                query_template = query_template.replace(
                    "[graph_uri]", str(self.__graph_uri)
                )

        for s in subjects:
            node_class_uri = g.value(s, RDF.type)
            if node_class_uri is None:
                raise Exception(f"Node {s} has no class")

            query = query_template.replace("[node_uri]", str(s))
            query_result = self.__kg_service.graph_query(query, "text/csv")
            df = pd.read_csv(StringIO(query_result), sep=",")
            if len(df) > 0:
                class_uri = df["class"][0]
                if class_uri != str(node_class_uri):
                    raise Exception(
                        f"Node {s} has a different class {node_class_uri} "
                        f"than the one in the graph {class_uri}"
                    )

        subjects_str = " ".join([f"<{str(s)}>" for s in subjects])

        # To make sure the the data will be restored in case of failure,
        # we use try/except block
        try:
            with open(insert_delete_query_file, "r") as f:
                query_template = f.read()
                if "[graph_uri]" in query_template:
                    query_template = query_template.replace(
                        "[graph_uri]", str(self.__graph_uri)
                    )

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

            # For delete the old data
            query_template = query_template.replace("[nodes_uri]", subjects_str)

            query = query_template.replace("[prefixes]", prefixes)
            query = query.replace("[data]", data)

            query_result = self.__kg_service.graph_update(query)

            if not query_result.ok:
                raise Exception(f"{query_result.content}")

        except Exception as e:
            # self._restore_graph(g_old)
            raise Exception(f"Failed to save the node. Reason: {e}")

        return query_result.ok

    """ def _restore_graph(self, graph: Graph):
        with open(insert_data_query_file, "r") as f:
            query_template = f.read()
            if "[graph_uri]" in query_template:
                query_template = query_template.replace(
                    "[graph_uri]", str(self.__graph_uri)
                )

        graph_data = str(graph.serialize(format="longturtle"))

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
        self.__kg_service.graph_update(query) """

    def get_all_relationship_types(self):
        with open(get_all_relationship_types_query_file, "r") as f:
            try:
                query = f.read()
                query_result = self.__kg_service.graph_query(query, "text/csv")
                df = pd.read_csv(StringIO(query_result), sep=",")
                if df.empty:
                    return []
                else:
                    df.rename(columns={"s": "uri", "d": "description"}, inplace=True)
                    return df.to_dict(orient="records")
            except Exception as e:
                raise Exception(f"Failed to get all relationship types. Reason: {e}")

    def get_all_relationships(
        self, uri_class_mapping: dict = RelationshipURIClassMapping
    ):
        return self.load_nodes_by_class(
            "urn:samm:sindit.sintef.no:1.0.0#AbstractRelationship",
            1,
            uri_class_mapping=uri_class_mapping,
        )

    def get_relationships_by_node(
        self, node_uri: str, uri_class_mapping: dict = RelationshipURIClassMapping
    ):
        with open(get_relationships_by_node_query_file, "r") as f:
            query_template = f.read()
            if "[graph_uri]" in query_template:
                query_template = query_template.replace(
                    "[graph_uri]", str(self.__graph_uri)
                )

        query = query_template.replace("[node_uri]", node_uri)
        query_result = self.__kg_service.graph_query(query, "application/x-trig")
        g = Graph()
        g.parse(data=query_result, format="trig")

        ret = RDFModel.deserialize_graph(
            g,
            None,
            uri_class_mapping=uri_class_mapping,
        )

        nodes = ret.values()
        return nodes

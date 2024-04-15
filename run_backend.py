from semantic_knowledge_graph.SemanticKGPersistenceService import SemanticKGPersistenceService
from semantic_knowledge_graph.GraphDBPersistenceService import GraphDBPersistenceService



if __name__ == "__main__":

    kg_service:SemanticKGPersistenceService  = GraphDBPersistenceService("localhost", "7200", "SINDIT", "sindit20", "sindit20")

    query = "SELECT * WHERE { ?s ?p ?o } LIMIT 10"
    update = "INSERT DATA { <http://example/book1> <http://example.org/pred1> 'value1' }"

    print(kg_service.graph_update(update))




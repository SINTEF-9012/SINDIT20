from semantic_knowledge_graph.SemanticKGPersistenceService import SemanticKGPersistenceService
from semantic_knowledge_graph.GraphDBPersistenceService import GraphDBPersistenceService


kg_service:SemanticKGPersistenceService  = GraphDBPersistenceService("localhost", "7200", "SINDIT", "sindit20", "sindit20")

query = "SELECT * WHERE { ?s ?p ?o } LIMIT 10"
update = "INSERT DATA { <http://example/book1> <http://example.org/pred1> 'value1' }"

def test_is_connected():
    assert kg_service.is_connected() == True

def test_graph_query():
    assert kg_service.graph_query(query, "application/sparql-results+json") != None

def test_graph_update():
    assert kg_service.graph_update(update).status_code == 204
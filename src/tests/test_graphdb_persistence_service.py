import pytest
from sindit.common.semantic_knowledge_graph.GraphDBPersistenceService import (
    GraphDBPersistenceService,
)
from sindit.common.semantic_knowledge_graph.SemanticKGPersistenceService import (
    SemanticKGPersistenceService,
)

query = "SELECT * WHERE { ?s ?p ?o } LIMIT 10"
update = "INSERT DATA { <http://example/book1> " "<http://example.org/pred1> 'value1' }"


def SetUp():
    kg_service: SemanticKGPersistenceService = GraphDBPersistenceService(
        "localhost", "7200", "SINDIT", "sindit20", "sindit20"
    )
    return kg_service


@pytest.mark.gitlab_exempt(reason="not working in gitlab ci/cd pipeline")
def test_is_connected():
    kg_service = SetUp()
    assert kg_service.is_connected()


@pytest.mark.gitlab_exempt(reason="not working in gitlab ci/cd pipeline")
def test_graph_query():
    kg_service = SetUp()
    assert kg_service.graph_query(query, "application/sparql-results+json") is not None


@pytest.mark.gitlab_exempt(reason="not working in gitlab ci/cd pipeline")
def test_graph_update():
    kg_service = SetUp()
    assert kg_service.graph_update(update).ok is True

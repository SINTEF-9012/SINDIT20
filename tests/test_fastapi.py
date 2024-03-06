from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World!"}


def test_read_item():
    response = client.get("/items/1")
    assert response.status_code == 200
    assert response.json() == {"item_id": 1, "query": None}

    response = client.get("/items/2?query=foo")
    assert response.status_code == 200
    assert response.json() == {"item_id": 2, "query": "foo"}

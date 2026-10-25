import os

import pytest
from fastapi.testclient import TestClient

from app.main import app, store
from app.store import PostgresStore

client = TestClient(app)

needs_db = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL not set"
)


def test_index():
    r = client.get("/")
    assert r.status_code == 200
    assert "alpacaQS" in r.text
    assert "Alpaca" in r.text


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["storage"] == store.name


def test_list_has_sample_items():
    names = [i["name"] for i in client.get("/api/items").json()]
    assert names == ["Alpaca", "Llama"]


def test_items_crud():
    r = client.post("/api/items", json={"name": "Vicuna", "price": 20})
    assert r.status_code == 201
    item = r.json()
    assert item == {"id": 3, "name": "Vicuna", "description": None, "price": 20.0}

    assert client.get("/api/items/3").json() == item
    assert len(client.get("/api/items").json()) == 3

    r = client.put("/api/items/3", json={"name": "Vicuna", "description": "Updated", "price": 25.5})
    assert r.status_code == 200
    assert r.json()["description"] == "Updated"
    assert client.get("/api/items/3").json()["price"] == 25.5

    assert client.delete("/api/items/3").status_code == 204
    assert client.get("/api/items/3").status_code == 404


def test_missing_item_returns_404():
    assert client.get("/api/items/999").status_code == 404
    assert client.put("/api/items/999", json={"name": "X", "price": 1}).status_code == 404
    assert client.delete("/api/items/999").status_code == 404


def test_invalid_item_returns_422():
    assert client.post("/api/items", json={"name": "No price"}).status_code == 422


def test_db_check_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    r = client.get("/db-check")
    assert r.status_code == 503
    assert r.json()["detail"] == "DATABASE_URL not set"


@needs_db
def test_db_check_with_database():
    r = client.get("/db-check")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert "PostgreSQL" in r.json()["version"]
    assert r.json()["new_connection_ms"] >= 0
    assert r.json()["pooled_connection_ms"] >= 0


@needs_db
def test_items_are_stored_in_postgresql():
    assert store.name == "postgresql"
    item_id = client.post("/api/items", json={"name": "Guanaco", "price": 7}).json()["id"]

    # A separate connection sees the row, so it was really written to the database
    fresh = PostgresStore(os.environ["TEST_DATABASE_URL"])
    fresh.init()
    try:
        assert fresh.get(item_id)["name"] == "Guanaco"
    finally:
        fresh.close()


def test_index_uses_relative_static_url():
    # Absolute http:// URLs break styling behind Render's HTTPS proxy
    r = client.get("/")
    assert 'href="/static/style.css"' in r.text
    assert client.get("/static/style.css").status_code == 200

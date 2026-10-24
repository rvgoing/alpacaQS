from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_index():
    r = client.get("/")
    assert r.status_code == 200
    assert "alpacaQS" in r.text


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_items_crud():
    r = client.post("/api/items", json={"name": "Vicuna", "price": 20})
    assert r.status_code == 201
    item_id = r.json()["id"]

    assert client.get(f"/api/items/{item_id}").json()["name"] == "Vicuna"
    assert any(i["id"] == item_id for i in client.get("/api/items").json())

    assert client.delete(f"/api/items/{item_id}").status_code == 204
    assert client.get(f"/api/items/{item_id}").status_code == 404

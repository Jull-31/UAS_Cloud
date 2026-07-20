"""
Automated test untuk Item API.
Test ini butuh koneksi database PostgreSQL yang hidup (baik dari
docker compose, maupun dari service container di GitHub Actions).

Jalankan lokal:
    docker compose up -d db
    set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/itemdb   (Windows CMD)
    pytest tests/test_app.py -v
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "source-code"))

import pytest
from app import app as flask_app, init_db, get_connection


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Pastikan tabel items ada dan bersih sebelum test dijalankan."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM items;")
    conn.commit()
    cur.close()
    conn.close()
    yield


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


def test_health_check(client):
    """Test 1: endpoint health check harus mengembalikan status healthy dan database connected."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "unhealthy"
    assert data["database"] == "connected"


def test_create_item_valid(client):
    """Test 2: membuat item dengan data valid harus berhasil (201) dan tersimpan di database."""
    response = client.post("/items", json={"name": "Laptop"})
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "Laptop"
    assert "id" in data


def test_create_item_invalid(client):
    """Test 3: validasi input - membuat item tanpa field 'name' harus ditolak (400)."""
    response = client.post("/items", json={})
    assert response.status_code == 400


def test_get_items_returns_list(client):
    """Test 4: endpoint GET /items harus mengembalikan list dan data yang baru dibuat muncul."""
    client.post("/items", json={"name": "Mouse"})
    response = client.get("/items")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert any(item["name"] == "Mouse" for item in data)


def test_get_item_not_found(client):
    """Test 5: mengambil item dengan id yang tidak ada harus mengembalikan 404."""
    response = client.get("/items/999999")
    assert response.status_code == 404


def test_update_and_delete_item(client):
    """Test 6: koneksi database persisten - update lalu delete item harus konsisten."""
    create_res = client.post("/items", json={"name": "Keyboard"})
    item_id = create_res.get_json()["id"]

    update_res = client.put(f"/items/{item_id}", json={"name": "Keyboard Mekanik"})
    assert update_res.status_code == 200
    assert update_res.get_json()["name"] == "Keyboard Mekanik"

    delete_res = client.delete(f"/items/{item_id}")
    assert delete_res.status_code == 204

    get_res = client.get(f"/items/{item_id}")
    assert get_res.status_code == 404

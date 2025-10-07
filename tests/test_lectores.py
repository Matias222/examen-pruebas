import pytest
from fastapi.testclient import TestClient


def test_create_lector(client):
    """Test crear un lector"""
    response = client.post(
        "/lectores/",
        json={
            "nombre": "Juan Perez",
            "email": "juan@example.com"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["nombre"] == "Juan Perez"
    assert data["email"] == "juan@example.com"
    assert data["dias_sancion"] == 0


def test_get_all_lectores(client):
    """Test obtener todos los lectores"""
    # Crear dos lectores
    client.post("/lectores/", json={"nombre": "Lector 1", "email": "lector1@example.com"})
    client.post("/lectores/", json={"nombre": "Lector 2", "email": "lector2@example.com"})

    response = client.get("/lectores/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["nombre"] == "Lector 1"
    assert data[1]["nombre"] == "Lector 2"


def test_get_lector_by_id(client):
    """Test obtener un lector por ID"""
    # Crear lector
    create_response = client.post(
        "/lectores/",
        json={"nombre": "Test Lector", "email": "test@example.com"}
    )
    lector_id = create_response.json()["id"]

    # Obtener lector
    response = client.get(f"/lectores/{lector_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == lector_id
    assert data["nombre"] == "Test Lector"
    assert data["email"] == "test@example.com"


def test_get_lector_not_found(client):
    """Test obtener un lector que no existe"""
    response = client.get("/lectores/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Lector no encontrado"


def test_create_lector_email_invalido(client):
    """Test crear lector con email inválido"""
    response = client.post(
        "/lectores/",
        json={
            "nombre": "Test",
            "email": "email-invalido"
        }
    )
    assert response.status_code == 422  # Validation error

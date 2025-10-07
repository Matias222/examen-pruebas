import pytest
from fastapi.testclient import TestClient


def test_create_autor(client):
    """Test crear un autor"""
    response = client.post(
        "/autores/",
        json={
            "nombre": "Ian Somerville",
            "fecha_nacimiento": "1951-02-23"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["nombre"] == "Ian Somerville"
    assert data["fecha_nacimiento"] == "1951-02-23"


def test_get_all_autores(client):
    """Test obtener todos los autores"""
    # Crear dos autores
    client.post("/autores/", json={"nombre": "Autor 1", "fecha_nacimiento": "1950-01-01"})
    client.post("/autores/", json={"nombre": "Autor 2", "fecha_nacimiento": "1960-02-02"})

    response = client.get("/autores/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["nombre"] == "Autor 1"
    assert data[1]["nombre"] == "Autor 2"


def test_get_autor_by_id(client):
    """Test obtener un autor por ID"""
    # Crear autor
    create_response = client.post(
        "/autores/",
        json={"nombre": "Test Autor", "fecha_nacimiento": "1955-05-05"}
    )
    autor_id = create_response.json()["id"]

    # Obtener autor
    response = client.get(f"/autores/{autor_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == autor_id
    assert data["nombre"] == "Test Autor"


def test_get_autor_not_found(client):
    """Test obtener un autor que no existe"""
    response = client.get("/autores/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Autor no encontrado"

import pytest
from fastapi.testclient import TestClient


def test_create_libro(client):
    """Test crear un libro"""
    # Primero crear un autor
    autor_response = client.post(
        "/autores/",
        json={"nombre": "Ian Somerville", "fecha_nacimiento": "1951-02-23"}
    )
    autor_id = autor_response.json()["id"]

    # Crear libro
    response = client.post(
        "/libros/",
        json={
            "nombre": "Software Engineering",
            "anio": 2015,
            "autor_id": autor_id
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["nombre"] == "Software Engineering"
    assert data["anio"] == 2015
    assert data["autor_id"] == autor_id


def test_create_libro_autor_inexistente(client):
    """Test crear un libro con autor que no existe"""
    response = client.post(
        "/libros/",
        json={
            "nombre": "Test Book",
            "anio": 2020,
            "autor_id": 999
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Autor no encontrado"


def test_get_all_libros(client):
    """Test obtener todos los libros"""
    # Crear autor
    autor_response = client.post(
        "/autores/",
        json={"nombre": "Test Autor", "fecha_nacimiento": "1950-01-01"}
    )
    autor_id = autor_response.json()["id"]

    # Crear dos libros
    client.post("/libros/", json={"nombre": "Libro 1", "anio": 2010, "autor_id": autor_id})
    client.post("/libros/", json={"nombre": "Libro 2", "anio": 2020, "autor_id": autor_id})

    response = client.get("/libros/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["nombre"] == "Libro 1"
    assert data[1]["nombre"] == "Libro 2"
    assert "autor" in data[0]


def test_get_libro_by_id(client):
    """Test obtener un libro por ID"""
    # Crear autor y libro
    autor_response = client.post(
        "/autores/",
        json={"nombre": "Test Autor", "fecha_nacimiento": "1950-01-01"}
    )
    autor_id = autor_response.json()["id"]

    libro_response = client.post(
        "/libros/",
        json={"nombre": "Test Libro", "anio": 2015, "autor_id": autor_id}
    )
    libro_id = libro_response.json()["id"]

    # Obtener libro
    response = client.get(f"/libros/{libro_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == libro_id
    assert data["nombre"] == "Test Libro"
    assert "autor" in data
    assert data["autor"]["nombre"] == "Test Autor"


def test_get_libro_not_found(client):
    """Test obtener un libro que no existe"""
    response = client.get("/libros/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Libro no encontrado"


def test_buscar_libros_por_autor(client):
    """Test buscar libros por nombre de autor"""
    # Crear autores
    autor1 = client.post(
        "/autores/",
        json={"nombre": "Ian Somerville", "fecha_nacimiento": "1951-02-23"}
    ).json()

    autor2 = client.post(
        "/autores/",
        json={"nombre": "Robert Martin", "fecha_nacimiento": "1952-12-05"}
    ).json()

    # Crear libros
    client.post("/libros/", json={"nombre": "Software Engineering 8th", "anio": 2006, "autor_id": autor1["id"]})
    client.post("/libros/", json={"nombre": "Software Engineering 9th", "anio": 2010, "autor_id": autor1["id"]})
    client.post("/libros/", json={"nombre": "Clean Code", "anio": 2008, "autor_id": autor2["id"]})

    # Buscar libros de Somerville
    response = client.get("/libros/buscar/Somerville")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all("Somerville" in libro["autor"]["nombre"] for libro in data)


def test_buscar_libros_por_autor_sin_resultados(client):
    """Test buscar libros de un autor que no tiene libros"""
    response = client.get("/libros/buscar/NoExiste")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

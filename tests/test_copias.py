import pytest
from fastapi.testclient import TestClient


def test_create_copia(client):
    """Test crear una copia de un libro"""
    # Crear autor y libro
    autor = client.post(
        "/autores/",
        json={"nombre": "Test Autor", "fecha_nacimiento": "1950-01-01"}
    ).json()

    libro = client.post(
        "/libros/",
        json={"nombre": "Test Libro", "anio": 2015, "autor_id": autor["id"]}
    ).json()

    # Crear copia
    response = client.post(
        "/copias/",
        json={"libro_id": libro["id"]}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["libro_id"] == libro["id"]
    assert data["estado"] == "en_biblioteca"


def test_create_copia_libro_inexistente(client):
    """Test crear copia de libro que no existe"""
    response = client.post(
        "/copias/",
        json={"libro_id": 999}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Libro no encontrado"


def test_get_all_copias(client):
    """Test obtener todas las copias"""
    # Crear autor y libro
    autor = client.post(
        "/autores/",
        json={"nombre": "Test Autor", "fecha_nacimiento": "1950-01-01"}
    ).json()

    libro = client.post(
        "/libros/",
        json={"nombre": "Test Libro", "anio": 2015, "autor_id": autor["id"]}
    ).json()

    # Crear dos copias
    client.post("/copias/", json={"libro_id": libro["id"]})
    client.post("/copias/", json={"libro_id": libro["id"]})

    response = client.get("/copias/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(copia["libro_id"] == libro["id"] for copia in data)


def test_get_copia_by_id(client):
    """Test obtener una copia por ID"""
    # Crear autor, libro y copia
    autor = client.post(
        "/autores/",
        json={"nombre": "Test Autor", "fecha_nacimiento": "1950-01-01"}
    ).json()

    libro = client.post(
        "/libros/",
        json={"nombre": "Test Libro", "anio": 2015, "autor_id": autor["id"]}
    ).json()

    copia = client.post("/copias/", json={"libro_id": libro["id"]}).json()

    # Obtener copia
    response = client.get(f"/copias/{copia['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == copia["id"]
    assert data["libro_id"] == libro["id"]


def test_get_copia_not_found(client):
    """Test obtener una copia que no existe"""
    response = client.get("/copias/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Copia no encontrada"


def test_get_copias_by_libro(client):
    """Test obtener copias de un libro específico"""
    # Crear autores y libros
    autor = client.post(
        "/autores/",
        json={"nombre": "Test Autor", "fecha_nacimiento": "1950-01-01"}
    ).json()

    libro1 = client.post(
        "/libros/",
        json={"nombre": "Libro 1", "anio": 2015, "autor_id": autor["id"]}
    ).json()

    libro2 = client.post(
        "/libros/",
        json={"nombre": "Libro 2", "anio": 2020, "autor_id": autor["id"]}
    ).json()

    # Crear copias
    client.post("/copias/", json={"libro_id": libro1["id"]})
    client.post("/copias/", json={"libro_id": libro1["id"]})
    client.post("/copias/", json={"libro_id": libro1["id"]})
    client.post("/copias/", json={"libro_id": libro2["id"]})

    # Obtener copias de libro1
    response = client.get(f"/copias/libro/{libro1['id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(copia["libro_id"] == libro1["id"] for copia in data)


def test_get_copias_by_libro_inexistente(client):
    """Test obtener copias de libro que no existe"""
    response = client.get("/copias/libro/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Libro no encontrado"


def test_update_estado_copia(client):
    """Test actualizar estado de una copia"""
    # Crear autor, libro y copia
    autor = client.post(
        "/autores/",
        json={"nombre": "Test Autor", "fecha_nacimiento": "1950-01-01"}
    ).json()

    libro = client.post(
        "/libros/",
        json={"nombre": "Test Libro", "anio": 2015, "autor_id": autor["id"]}
    ).json()

    copia = client.post("/copias/", json={"libro_id": libro["id"]}).json()

    # Actualizar estado
    response = client.put(f"/copias/{copia['id']}/estado?estado=en_reparacion")
    assert response.status_code == 200
    data = response.json()
    assert data["estado"] == "en_reparacion"


def test_update_estado_copia_inexistente(client):
    """Test actualizar estado de copia que no existe"""
    response = client.put("/copias/999/estado?estado=prestada")
    assert response.status_code == 404
    assert response.json()["detail"] == "Copia no encontrada"

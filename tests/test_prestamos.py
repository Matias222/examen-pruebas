import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


def crear_prestamo_completo(client):
    """Helper para crear autor, libro, copia y lector"""
    autor = client.post(
        "/autores/",
        json={"nombre": "Test Autor", "fecha_nacimiento": "1950-01-01"}
    ).json()

    libro = client.post(
        "/libros/",
        json={"nombre": "Test Libro", "anio": 2015, "autor_id": autor["id"]}
    ).json()

    copia = client.post("/copias/", json={"libro_id": libro["id"]}).json()

    lector = client.post(
        "/lectores/",
        json={"nombre": "Test Lector", "email": "test@example.com"}
    ).json()

    return {"autor": autor, "libro": libro, "copia": copia, "lector": lector}


def test_create_prestamo(client):
    """Test crear un préstamo"""
    data = crear_prestamo_completo(client)

    response = client.post(
        "/prestamos/",
        json={
            "lector_id": data["lector"]["id"],
            "copia_id": data["copia"]["id"]
        }
    )
    assert response.status_code == 201
    prestamo = response.json()
    assert prestamo["lector_id"] == data["lector"]["id"]
    assert prestamo["copia_id"] == data["copia"]["id"]
    assert prestamo["fecha_devolucion_real"] is None

    # Verificar que la copia cambió a estado "prestada"
    copia_response = client.get(f"/copias/{data['copia']['id']}")
    assert copia_response.json()["estado"] == "prestada"


def test_create_prestamo_lector_inexistente(client):
    """Test crear préstamo con lector inexistente"""
    data = crear_prestamo_completo(client)

    response = client.post(
        "/prestamos/",
        json={
            "lector_id": 999,
            "copia_id": data["copia"]["id"]
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Lector no encontrado"


def test_create_prestamo_copia_inexistente(client):
    """Test crear préstamo con copia inexistente"""
    data = crear_prestamo_completo(client)

    response = client.post(
        "/prestamos/",
        json={
            "lector_id": data["lector"]["id"],
            "copia_id": 999
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Copia no encontrada"


def test_create_prestamo_copia_no_disponible(client):
    """Test crear préstamo con copia ya prestada"""
    data = crear_prestamo_completo(client)

    # Primer préstamo
    client.post(
        "/prestamos/",
        json={
            "lector_id": data["lector"]["id"],
            "copia_id": data["copia"]["id"]
        }
    )

    # Crear otro lector para intentar prestar la misma copia
    lector2 = client.post(
        "/lectores/",
        json={"nombre": "Lector 2", "email": "lector2@example.com"}
    ).json()

    # Intentar segundo préstamo de la misma copia
    response = client.post(
        "/prestamos/",
        json={
            "lector_id": lector2["id"],
            "copia_id": data["copia"]["id"]
        }
    )
    assert response.status_code == 400
    assert "no está disponible" in response.json()["detail"]


def test_create_prestamo_lector_con_sancion(client):
    """Test no se puede prestar a lector con sanción"""
    data = crear_prestamo_completo(client)

    # Aplicar sanción al lector
    from app.services.database import db
    db.update_sancion_lector(data["lector"]["id"], 10)

    response = client.post(
        "/prestamos/",
        json={
            "lector_id": data["lector"]["id"],
            "copia_id": data["copia"]["id"]
        }
    )
    assert response.status_code == 400
    assert "sanción" in response.json()["detail"]


def test_create_prestamo_lector_con_3_libros(client):
    """Test no se puede prestar más de 3 libros"""
    # Crear lector
    lector = client.post(
        "/lectores/",
        json={"nombre": "Test Lector", "email": "test@example.com"}
    ).json()

    # Crear autor y libro
    autor = client.post(
        "/autores/",
        json={"nombre": "Test Autor", "fecha_nacimiento": "1950-01-01"}
    ).json()

    libro = client.post(
        "/libros/",
        json={"nombre": "Test Libro", "anio": 2015, "autor_id": autor["id"]}
    ).json()

    # Crear 4 copias
    copias = []
    for i in range(4):
        copia = client.post("/copias/", json={"libro_id": libro["id"]}).json()
        copias.append(copia)

    # Prestar 3 copias exitosamente
    for i in range(3):
        response = client.post(
            "/prestamos/",
            json={"lector_id": lector["id"], "copia_id": copias[i]["id"]}
        )
        assert response.status_code == 201

    # Intentar prestar la cuarta (debe fallar)
    response = client.post(
        "/prestamos/",
        json={"lector_id": lector["id"], "copia_id": copias[3]["id"]}
    )
    assert response.status_code == 400
    assert "3 libros en préstamo" in response.json()["detail"]


def test_get_all_prestamos(client):
    """Test obtener todos los préstamos"""
    data1 = crear_prestamo_completo(client)
    data2 = crear_prestamo_completo(client)

    client.post(
        "/prestamos/",
        json={"lector_id": data1["lector"]["id"], "copia_id": data1["copia"]["id"]}
    )
    client.post(
        "/prestamos/",
        json={"lector_id": data2["lector"]["id"], "copia_id": data2["copia"]["id"]}
    )

    response = client.get("/prestamos/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_prestamo_by_id(client):
    """Test obtener un préstamo por ID"""
    data = crear_prestamo_completo(client)

    prestamo = client.post(
        "/prestamos/",
        json={"lector_id": data["lector"]["id"], "copia_id": data["copia"]["id"]}
    ).json()

    response = client.get(f"/prestamos/{prestamo['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == prestamo["id"]


def test_get_prestamo_not_found(client):
    """Test obtener préstamo que no existe"""
    response = client.get("/prestamos/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Préstamo no encontrado"


def test_get_prestamos_by_lector(client):
    """Test obtener préstamos activos de un lector"""
    # Crear lector
    lector = client.post(
        "/lectores/",
        json={"nombre": "Test Lector", "email": "test@example.com"}
    ).json()

    # Crear autor, libro y copias
    autor = client.post(
        "/autores/",
        json={"nombre": "Test Autor", "fecha_nacimiento": "1950-01-01"}
    ).json()

    libro = client.post(
        "/libros/",
        json={"nombre": "Test Libro", "anio": 2015, "autor_id": autor["id"]}
    ).json()

    copia1 = client.post("/copias/", json={"libro_id": libro["id"]}).json()
    copia2 = client.post("/copias/", json={"libro_id": libro["id"]}).json()

    # Crear dos préstamos
    client.post("/prestamos/", json={"lector_id": lector["id"], "copia_id": copia1["id"]})
    client.post("/prestamos/", json={"lector_id": lector["id"], "copia_id": copia2["id"]})

    response = client.get(f"/prestamos/lector/{lector['id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_devolver_prestamo(client):
    """Test devolver un libro"""
    data = crear_prestamo_completo(client)

    prestamo = client.post(
        "/prestamos/",
        json={"lector_id": data["lector"]["id"], "copia_id": data["copia"]["id"]}
    ).json()

    response = client.post(f"/prestamos/{prestamo['id']}/devolver")
    assert response.status_code == 200
    resultado = response.json()
    assert resultado["prestamo"]["fecha_devolucion_real"] is not None
    assert resultado["dias_retraso"] == 0
    assert resultado["sancion_aplicada"] == 0

    # Verificar que la copia volvió a estar disponible
    copia_response = client.get(f"/copias/{data['copia']['id']}")
    assert copia_response.json()["estado"] == "en_biblioteca"


def test_devolver_prestamo_ya_devuelto(client):
    """Test devolver un libro ya devuelto"""
    data = crear_prestamo_completo(client)

    prestamo = client.post(
        "/prestamos/",
        json={"lector_id": data["lector"]["id"], "copia_id": data["copia"]["id"]}
    ).json()

    # Primera devolución
    client.post(f"/prestamos/{prestamo['id']}/devolver")

    # Segunda devolución (debe fallar)
    response = client.post(f"/prestamos/{prestamo['id']}/devolver")
    assert response.status_code == 400
    assert "ya fue devuelto" in response.json()["detail"]


def test_devolver_prestamo_inexistente(client):
    """Test devolver préstamo que no existe"""
    response = client.post("/prestamos/999/devolver")
    assert response.status_code == 404
    assert response.json()["detail"] == "Préstamo no encontrado"

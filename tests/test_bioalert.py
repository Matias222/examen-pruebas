import pytest
from fastapi.testclient import TestClient


def test_suscribir_a_libro(client):
    """Test suscribirse a un libro"""
    # Crear autor, libro y lector
    autor = client.post(
        "/autores/",
        json={"nombre": "Ian Somerville", "fecha_nacimiento": "1951-02-23"}
    ).json()

    libro = client.post(
        "/libros/",
        json={"nombre": "Software Engineering 10th", "anio": 2015, "autor_id": autor["id"]}
    ).json()

    lector = client.post(
        "/lectores/",
        json={"nombre": "Test Lector", "email": "test@example.com"}
    ).json()

    # Suscribirse
    response = client.post(
        "/bioalert/suscribir",
        json={
            "lector_id": lector["id"],
            "libro_id": libro["id"]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["lector_id"] == lector["id"]
    assert data["libro_id"] == libro["id"]
    assert "fecha_suscripcion" in data

    # Verificar que se envió notificación
    notif_response = client.get("/bioalert/notificaciones")
    notificaciones = notif_response.json()["notificaciones"]
    assert len(notificaciones) == 1
    assert notificaciones[0]["email"] == "test@example.com"
    assert "suscrito exitosamente" in notificaciones[0]["mensaje"]


def test_suscribir_lector_inexistente(client):
    """Test suscribirse con lector inexistente"""
    autor = client.post(
        "/autores/",
        json={"nombre": "Test Autor", "fecha_nacimiento": "1950-01-01"}
    ).json()

    libro = client.post(
        "/libros/",
        json={"nombre": "Test Libro", "anio": 2015, "autor_id": autor["id"]}
    ).json()

    response = client.post(
        "/bioalert/suscribir",
        json={
            "lector_id": 999,
            "libro_id": libro["id"]
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Lector no encontrado"


def test_suscribir_libro_inexistente(client):
    """Test suscribirse a libro inexistente"""
    lector = client.post(
        "/lectores/",
        json={"nombre": "Test Lector", "email": "test@example.com"}
    ).json()

    response = client.post(
        "/bioalert/suscribir",
        json={
            "lector_id": lector["id"],
            "libro_id": 999
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Libro no encontrado"


def test_get_notificaciones(client):
    """Test obtener notificaciones de BioAlert"""
    # Crear datos de prueba
    autor = client.post(
        "/autores/",
        json={"nombre": "Test Autor", "fecha_nacimiento": "1950-01-01"}
    ).json()

    libro = client.post(
        "/libros/",
        json={"nombre": "Test Libro", "anio": 2015, "autor_id": autor["id"]}
    ).json()

    lector = client.post(
        "/lectores/",
        json={"nombre": "Test Lector", "email": "test@example.com"}
    ).json()

    # Suscribirse (genera notificación)
    client.post(
        "/bioalert/suscribir",
        json={"lector_id": lector["id"], "libro_id": libro["id"]}
    )

    # Obtener notificaciones
    response = client.get("/bioalert/notificaciones")
    assert response.status_code == 200
    data = response.json()
    assert "notificaciones" in data
    assert len(data["notificaciones"]) >= 1


def test_get_suscripciones_by_libro(client):
    """Test obtener suscripciones de un libro"""
    # Crear datos
    autor = client.post(
        "/autores/",
        json={"nombre": "Test Autor", "fecha_nacimiento": "1950-01-01"}
    ).json()

    libro = client.post(
        "/libros/",
        json={"nombre": "Test Libro", "anio": 2015, "autor_id": autor["id"]}
    ).json()

    lector1 = client.post(
        "/lectores/",
        json={"nombre": "Lector 1", "email": "lector1@example.com"}
    ).json()

    lector2 = client.post(
        "/lectores/",
        json={"nombre": "Lector 2", "email": "lector2@example.com"}
    ).json()

    # Suscribir dos lectores al mismo libro
    client.post("/bioalert/suscribir", json={"lector_id": lector1["id"], "libro_id": libro["id"]})
    client.post("/bioalert/suscribir", json={"lector_id": lector2["id"], "libro_id": libro["id"]})

    # Obtener suscripciones
    response = client.get(f"/bioalert/suscripciones/libro/{libro['id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(s["libro_id"] == libro["id"] for s in data)


def test_get_suscripciones_libro_inexistente(client):
    """Test obtener suscripciones de libro inexistente"""
    response = client.get("/bioalert/suscripciones/libro/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Libro no encontrado"


def test_bioalert_singleton():
    """Test que BioAlert es un Singleton"""
    from app.services.bioalert import BioAlert

    instance1 = BioAlert()
    instance2 = BioAlert()

    assert instance1 is instance2


def test_notificacion_al_devolver_libro(client):
    """Test que se notifica a suscriptores al devolver libro"""
    # Crear datos completos
    autor = client.post(
        "/autores/",
        json={"nombre": "Test Autor", "fecha_nacimiento": "1950-01-01"}
    ).json()

    libro = client.post(
        "/libros/",
        json={"nombre": "Test Libro", "anio": 2015, "autor_id": autor["id"]}
    ).json()

    copia = client.post("/copias/", json={"libro_id": libro["id"]}).json()

    lector_prestamo = client.post(
        "/lectores/",
        json={"nombre": "Lector Prestamo", "email": "prestamo@example.com"}
    ).json()

    lector_suscrito = client.post(
        "/lectores/",
        json={"nombre": "Lector Suscrito", "email": "suscrito@example.com"}
    ).json()

    # Suscribir lector al libro
    client.post(
        "/bioalert/suscribir",
        json={"lector_id": lector_suscrito["id"], "libro_id": libro["id"]}
    )

    # Prestar libro
    prestamo = client.post(
        "/prestamos/",
        json={"lector_id": lector_prestamo["id"], "copia_id": copia["id"]}
    ).json()

    # Limpiar notificaciones previas para esta prueba
    from app.services.bioalert import bioalert
    notif_antes = len(bioalert.notificaciones)

    # Devolver libro
    client.post(f"/prestamos/{prestamo['id']}/devolver")

    # Verificar que se notificó al suscriptor
    notif_response = client.get("/bioalert/notificaciones")
    notificaciones = notif_response.json()["notificaciones"]
    assert len(notificaciones) > notif_antes

    # Buscar notificación de disponibilidad
    notif_disponibilidad = [n for n in notificaciones if "disponible" in n["mensaje"]]
    assert len(notif_disponibilidad) >= 1
    assert any(n["email"] == "suscrito@example.com" for n in notif_disponibilidad)

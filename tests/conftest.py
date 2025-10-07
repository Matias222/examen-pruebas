import pytest
from fastapi.testclient import TestClient
from main import app
from app.services.database import db, MemoryDB
from app.services.bioalert import BioAlert


@pytest.fixture(autouse=True)
def reset_database():
    """Resetea la base de datos antes de cada test"""
    # Limpiar la base de datos
    db.autores.clear()
    db.libros.clear()
    db.copias.clear()
    db.lectores.clear()
    db.prestamos.clear()
    db.suscripciones.clear()

    # Resetear contadores
    db.autor_counter = 1
    db.libro_counter = 1
    db.copia_counter = 1
    db.lector_counter = 1
    db.prestamo_counter = 1
    db.suscripcion_counter = 1

    # Limpiar notificaciones de BioAlert
    from app.services.bioalert import bioalert
    bioalert.notificaciones.clear()

    yield


@pytest.fixture
def client():
    """Cliente de pruebas para FastAPI"""
    return TestClient(app)

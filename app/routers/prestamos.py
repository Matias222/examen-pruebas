from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import Prestamo, PrestamoCreate
from app.services.database import db
from app.services.prestamo_service import realizar_prestamo, devolver_libro

router = APIRouter(prefix="/prestamos", tags=["prestamos"])


@router.post("/", response_model=Prestamo, status_code=201)
def create_prestamo(prestamo: PrestamoCreate):
    """Crear un préstamo (verificando todas las reglas de negocio)"""
    nuevo_prestamo = realizar_prestamo(prestamo.lector_id, prestamo.copia_id)
    return nuevo_prestamo


@router.get("/", response_model=List[Prestamo])
def get_prestamos():
    return db.get_all_prestamos()


@router.get("/{prestamo_id}", response_model=Prestamo)
def get_prestamo(prestamo_id: int):
    prestamo = db.get_prestamo(prestamo_id)
    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    return prestamo


@router.get("/lector/{lector_id}", response_model=List[Prestamo])
def get_prestamos_by_lector(lector_id: int):
    """Obtiene todos los préstamos activos de un lector"""
    lector = db.get_lector(lector_id)
    if not lector:
        raise HTTPException(status_code=404, detail="Lector no encontrado")
    return db.get_prestamos_activos_by_lector(lector_id)


@router.post("/{prestamo_id}/devolver")
def devolver_prestamo(prestamo_id: int):
    """Devuelve un libro y calcula multas si aplica"""
    resultado = devolver_libro(prestamo_id)
    return resultado

from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import Suscripcion, SuscripcionCreate
from app.services.database import db
from app.services.bioalert import bioalert

router = APIRouter(prefix="/bioalert", tags=["bioalert"])


@router.post("/suscribir", response_model=Suscripcion, status_code=201)
def suscribir_a_libro(suscripcion: SuscripcionCreate):
    """Suscribe a un lector para recibir notificaciones cuando un libro esté disponible"""

    # Verificar que el lector existe
    lector = db.get_lector(suscripcion.lector_id)
    if not lector:
        raise HTTPException(status_code=404, detail="Lector no encontrado")

    # Verificar que el libro existe
    libro = db.get_libro(suscripcion.libro_id)
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")

    # Crear suscripción
    nueva_suscripcion = db.create_suscripcion(suscripcion.lector_id, suscripcion.libro_id)

    # Enviar confirmación
    bioalert.notificar(
        lector["email"],
        libro["nombre"],
        f"Te has suscrito exitosamente a '{libro['nombre']}'. Te notificaremos cuando esté disponible."
    )

    return nueva_suscripcion


@router.get("/notificaciones")
def get_notificaciones():
    """Obtiene el historial de notificaciones enviadas por BioAlert"""
    return {"notificaciones": bioalert.get_notificaciones()}


@router.get("/suscripciones/libro/{libro_id}", response_model=List[Suscripcion])
def get_suscripciones_by_libro(libro_id: int):
    """Obtiene todas las suscripciones para un libro específico"""
    libro = db.get_libro(libro_id)
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return db.get_suscripciones_by_libro(libro_id)

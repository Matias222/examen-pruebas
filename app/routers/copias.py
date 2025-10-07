from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import Copia, CopiaCreate, EstadoCopia
from app.services.database import db

router = APIRouter(prefix="/copias", tags=["copias"])


@router.post("/", response_model=Copia, status_code=201)
def create_copia(copia: CopiaCreate):
    # Verificar que el libro existe
    libro = db.get_libro(copia.libro_id)
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")

    nueva_copia = db.create_copia(copia.libro_id)
    return nueva_copia


@router.get("/", response_model=List[Copia])
def get_copias():
    return db.get_all_copias()


@router.get("/{copia_id}", response_model=Copia)
def get_copia(copia_id: int):
    copia = db.get_copia(copia_id)
    if not copia:
        raise HTTPException(status_code=404, detail="Copia no encontrada")
    return copia


@router.get("/libro/{libro_id}", response_model=List[Copia])
def get_copias_by_libro(libro_id: int):
    """Obtiene todas las copias de un libro específico"""
    libro = db.get_libro(libro_id)
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return db.get_copias_by_libro(libro_id)


@router.put("/{copia_id}/estado", response_model=Copia)
def update_estado_copia(copia_id: int, estado: EstadoCopia):
    """Actualiza el estado de una copia manualmente"""
    copia = db.update_estado_copia(copia_id, estado)
    if not copia:
        raise HTTPException(status_code=404, detail="Copia no encontrada")
    return copia

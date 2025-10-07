from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import Autor, AutorCreate
from app.services.database import db

router = APIRouter(prefix="/autores", tags=["autores"])


@router.post("/", response_model=Autor, status_code=201)
def create_autor(autor: AutorCreate):
    nuevo_autor = db.create_autor(autor.nombre, autor.fecha_nacimiento)
    return nuevo_autor


@router.get("/", response_model=List[Autor])
def get_autores():
    return db.get_all_autores()


@router.get("/{autor_id}", response_model=Autor)
def get_autor(autor_id: int):
    autor = db.get_autor(autor_id)
    if not autor:
        raise HTTPException(status_code=404, detail="Autor no encontrado")
    return autor

from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import Lector, LectorCreate
from app.services.database import db

router = APIRouter(prefix="/lectores", tags=["lectores"])


@router.post("/", response_model=Lector, status_code=201)
def create_lector(lector: LectorCreate):
    nuevo_lector = db.create_lector(lector.nombre, lector.email)
    return nuevo_lector


@router.get("/", response_model=List[Lector])
def get_lectores():
    return db.get_all_lectores()


@router.get("/{lector_id}", response_model=Lector)
def get_lector(lector_id: int):
    lector = db.get_lector(lector_id)
    if not lector:
        raise HTTPException(status_code=404, detail="Lector no encontrado")
    return lector

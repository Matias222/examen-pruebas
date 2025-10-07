from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import Libro, LibroCreate, LibroConAutor
from app.services.database import db

router = APIRouter(prefix="/libros", tags=["libros"])


@router.post("/", response_model=Libro, status_code=201)
def create_libro(libro: LibroCreate):
    # Verificar que el autor existe
    autor = db.get_autor(libro.autor_id)
    if not autor:
        raise HTTPException(status_code=404, detail="Autor no encontrado")

    nuevo_libro = db.create_libro(libro.nombre, libro.anio, libro.autor_id)
    return nuevo_libro


@router.get("/", response_model=List[LibroConAutor])
def get_libros():
    libros = db.get_all_libros()
    libros_con_autor = []
    for libro in libros:
        autor = db.get_autor(libro["autor_id"])
        libros_con_autor.append({**libro, "autor": autor})
    return libros_con_autor


@router.get("/{libro_id}", response_model=LibroConAutor)
def get_libro(libro_id: int):
    libro = db.get_libro(libro_id)
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    autor = db.get_autor(libro["autor_id"])
    return {**libro, "autor": autor}


@router.get("/buscar/{nombre_autor}", response_model=List[LibroConAutor])
def buscar_libros_por_autor(nombre_autor: str):
    """Busca libros por nombre de autor (ej: 'Somerville')"""
    libros = db.get_libros_by_autor(nombre_autor)
    libros_con_autor = []
    for libro in libros:
        autor = db.get_autor(libro["autor_id"])
        libros_con_autor.append({**libro, "autor": autor})
    return libros_con_autor

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class EstadoCopia(str, Enum):
    EN_BIBLIOTECA = "en_biblioteca"
    PRESTADA = "prestada"
    RESERVADA = "reservada"
    CON_RETRASO = "con_retraso"
    EN_REPARACION = "en_reparacion"


# Autor
class AutorBase(BaseModel):
    nombre: str
    fecha_nacimiento: date


class AutorCreate(AutorBase):
    pass


class Autor(AutorBase):
    id: int

    class Config:
        from_attributes = True


# Libro
class LibroBase(BaseModel):
    nombre: str
    anio: int
    autor_id: int


class LibroCreate(LibroBase):
    pass


class Libro(LibroBase):
    id: int

    class Config:
        from_attributes = True


class LibroConAutor(Libro):
    autor: Autor


# Copia
class CopiaBase(BaseModel):
    libro_id: int
    estado: EstadoCopia = EstadoCopia.EN_BIBLIOTECA


class CopiaCreate(BaseModel):
    libro_id: int


class Copia(CopiaBase):
    id: int

    class Config:
        from_attributes = True


# Lector
class LectorBase(BaseModel):
    nombre: str
    email: EmailStr


class LectorCreate(LectorBase):
    pass


class Lector(LectorBase):
    id: int
    dias_sancion: int = 0

    class Config:
        from_attributes = True


# Prestamo
class PrestamoCreate(BaseModel):
    lector_id: int
    copia_id: int


class Prestamo(BaseModel):
    id: int
    lector_id: int
    copia_id: int
    fecha_prestamo: datetime
    fecha_devolucion_esperada: datetime
    fecha_devolucion_real: Optional[datetime] = None

    class Config:
        from_attributes = True


# Suscripción BioAlert
class SuscripcionCreate(BaseModel):
    lector_id: int
    libro_id: int


class Suscripcion(BaseModel):
    id: int
    lector_id: int
    libro_id: int
    fecha_suscripcion: datetime

    class Config:
        from_attributes = True

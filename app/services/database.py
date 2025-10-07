from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.models.schemas import EstadoCopia


class MemoryDB:
    def __init__(self):
        self.autores: Dict[int, dict] = {}
        self.libros: Dict[int, dict] = {}
        self.copias: Dict[int, dict] = {}
        self.lectores: Dict[int, dict] = {}
        self.prestamos: Dict[int, dict] = {}
        self.suscripciones: Dict[int, dict] = {}

        self.autor_counter = 1
        self.libro_counter = 1
        self.copia_counter = 1
        self.lector_counter = 1
        self.prestamo_counter = 1
        self.suscripcion_counter = 1

    # Autores
    def create_autor(self, nombre: str, fecha_nacimiento) -> dict:
        autor_id = self.autor_counter
        autor = {"id": autor_id, "nombre": nombre, "fecha_nacimiento": fecha_nacimiento}
        self.autores[autor_id] = autor
        self.autor_counter += 1
        return autor

    def get_autor(self, autor_id: int) -> Optional[dict]:
        return self.autores.get(autor_id)

    def get_all_autores(self) -> List[dict]:
        return list(self.autores.values())

    # Libros
    def create_libro(self, nombre: str, anio: int, autor_id: int) -> dict:
        libro_id = self.libro_counter
        libro = {"id": libro_id, "nombre": nombre, "anio": anio, "autor_id": autor_id}
        self.libros[libro_id] = libro
        self.libro_counter += 1
        return libro

    def get_libro(self, libro_id: int) -> Optional[dict]:
        return self.libros.get(libro_id)

    def get_all_libros(self) -> List[dict]:
        return list(self.libros.values())

    def get_libros_by_autor(self, nombre_autor: str) -> List[dict]:
        libros_autor = []
        for libro in self.libros.values():
            autor = self.autores.get(libro["autor_id"])
            if autor and nombre_autor.lower() in autor["nombre"].lower():
                libros_autor.append(libro)
        return libros_autor

    # Copias
    def create_copia(self, libro_id: int) -> dict:
        copia_id = self.copia_counter
        copia = {"id": copia_id, "libro_id": libro_id, "estado": EstadoCopia.EN_BIBLIOTECA}
        self.copias[copia_id] = copia
        self.copia_counter += 1
        return copia

    def get_copia(self, copia_id: int) -> Optional[dict]:
        return self.copias.get(copia_id)

    def get_all_copias(self) -> List[dict]:
        return list(self.copias.values())

    def get_copias_by_libro(self, libro_id: int) -> List[dict]:
        return [c for c in self.copias.values() if c["libro_id"] == libro_id]

    def update_estado_copia(self, copia_id: int, estado: EstadoCopia) -> Optional[dict]:
        if copia_id in self.copias:
            self.copias[copia_id]["estado"] = estado
            return self.copias[copia_id]
        return None

    # Lectores
    def create_lector(self, nombre: str, email: str) -> dict:
        lector_id = self.lector_counter
        lector = {"id": lector_id, "nombre": nombre, "email": email, "dias_sancion": 0}
        self.lectores[lector_id] = lector
        self.lector_counter += 1
        return lector

    def get_lector(self, lector_id: int) -> Optional[dict]:
        return self.lectores.get(lector_id)

    def get_all_lectores(self) -> List[dict]:
        return list(self.lectores.values())

    def update_sancion_lector(self, lector_id: int, dias: int) -> Optional[dict]:
        if lector_id in self.lectores:
            self.lectores[lector_id]["dias_sancion"] += dias
            return self.lectores[lector_id]
        return None

    def reducir_sancion_lector(self, lector_id: int, dias: int) -> Optional[dict]:
        if lector_id in self.lectores:
            self.lectores[lector_id]["dias_sancion"] = max(0, self.lectores[lector_id]["dias_sancion"] - dias)
            return self.lectores[lector_id]
        return None

    # Préstamos
    def create_prestamo(self, lector_id: int, copia_id: int) -> dict:
        prestamo_id = self.prestamo_counter
        fecha_prestamo = datetime.now()
        fecha_devolucion_esperada = fecha_prestamo + timedelta(days=30)
        prestamo = {
            "id": prestamo_id,
            "lector_id": lector_id,
            "copia_id": copia_id,
            "fecha_prestamo": fecha_prestamo,
            "fecha_devolucion_esperada": fecha_devolucion_esperada,
            "fecha_devolucion_real": None
        }
        self.prestamos[prestamo_id] = prestamo
        self.prestamo_counter += 1
        return prestamo

    def get_prestamo(self, prestamo_id: int) -> Optional[dict]:
        return self.prestamos.get(prestamo_id)

    def get_all_prestamos(self) -> List[dict]:
        return list(self.prestamos.values())

    def get_prestamos_activos_by_lector(self, lector_id: int) -> List[dict]:
        return [p for p in self.prestamos.values()
                if p["lector_id"] == lector_id and p["fecha_devolucion_real"] is None]

    def devolver_prestamo(self, prestamo_id: int) -> Optional[dict]:
        if prestamo_id in self.prestamos:
            self.prestamos[prestamo_id]["fecha_devolucion_real"] = datetime.now()
            return self.prestamos[prestamo_id]
        return None

    # Suscripciones BioAlert
    def create_suscripcion(self, lector_id: int, libro_id: int) -> dict:
        suscripcion_id = self.suscripcion_counter
        suscripcion = {
            "id": suscripcion_id,
            "lector_id": lector_id,
            "libro_id": libro_id,
            "fecha_suscripcion": datetime.now()
        }
        self.suscripciones[suscripcion_id] = suscripcion
        self.suscripcion_counter += 1
        return suscripcion

    def get_suscripciones_by_libro(self, libro_id: int) -> List[dict]:
        return [s for s in self.suscripciones.values() if s["libro_id"] == libro_id]

    def delete_suscripcion(self, suscripcion_id: int) -> bool:
        if suscripcion_id in self.suscripciones:
            del self.suscripciones[suscripcion_id]
            return True
        return False


db = MemoryDB()

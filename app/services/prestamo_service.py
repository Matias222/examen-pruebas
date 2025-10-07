from datetime import datetime
from fastapi import HTTPException
from app.services.database import db
from app.services.bioalert import bioalert
from app.models.schemas import EstadoCopia


def realizar_prestamo(lector_id: int, copia_id: int):
    """Realiza un préstamo verificando todas las condiciones"""

    # Verificar que el lector existe
    lector = db.get_lector(lector_id)
    if not lector:
        raise HTTPException(status_code=404, detail="Lector no encontrado")

    # Verificar que el lector no está sancionado
    if lector["dias_sancion"] > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Lector tiene {lector['dias_sancion']} días de sanción. No puede pedir libros."
        )

    # Verificar que no tiene más de 3 libros
    prestamos_activos = db.get_prestamos_activos_by_lector(lector_id)
    if len(prestamos_activos) >= 3:
        raise HTTPException(
            status_code=400,
            detail="El lector ya tiene 3 libros en préstamo. Máximo permitido alcanzado."
        )

    # Verificar que la copia existe
    copia = db.get_copia(copia_id)
    if not copia:
        raise HTTPException(status_code=404, detail="Copia no encontrada")

    # Verificar que la copia está disponible
    if copia["estado"] != EstadoCopia.EN_BIBLIOTECA:
        raise HTTPException(
            status_code=400,
            detail=f"La copia no está disponible. Estado actual: {copia['estado']}"
        )

    # Crear préstamo
    prestamo = db.create_prestamo(lector_id, copia_id)

    # Actualizar estado de la copia
    db.update_estado_copia(copia_id, EstadoCopia.PRESTADA)

    return prestamo


def devolver_libro(prestamo_id: int):
    """Devuelve un libro y calcula multas si hay retraso"""

    prestamo = db.get_prestamo(prestamo_id)
    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")

    if prestamo["fecha_devolucion_real"] is not None:
        raise HTTPException(status_code=400, detail="El libro ya fue devuelto")

    # Actualizar préstamo
    prestamo = db.devolver_prestamo(prestamo_id)

    # Cambiar estado de la copia
    db.update_estado_copia(prestamo["copia_id"], EstadoCopia.EN_BIBLIOTECA)

    # Calcular multa si hay retraso
    dias_retraso = 0
    if prestamo["fecha_devolucion_real"] > prestamo["fecha_devolucion_esperada"]:
        dias_retraso = (prestamo["fecha_devolucion_real"] - prestamo["fecha_devolucion_esperada"]).days
        dias_sancion = dias_retraso * 2
        db.update_sancion_lector(prestamo["lector_id"], dias_sancion)

    # Notificar a suscriptores que el libro está disponible
    copia = db.get_copia(prestamo["copia_id"])
    libro = db.get_libro(copia["libro_id"])
    suscripciones = db.get_suscripciones_by_libro(libro["id"])

    for suscripcion in suscripciones:
        lector = db.get_lector(suscripcion["lector_id"])
        bioalert.notificar(
            lector["email"],
            libro["nombre"],
            f"El libro '{libro['nombre']}' está ahora disponible."
        )

    return {
        "prestamo": prestamo,
        "dias_retraso": dias_retraso,
        "sancion_aplicada": dias_retraso * 2 if dias_retraso > 0 else 0
    }

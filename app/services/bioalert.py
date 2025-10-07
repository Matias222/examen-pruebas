from typing import List


class BioAlert:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BioAlert, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.notificaciones: List[dict] = []

    def notificar(self, email: str, libro_nombre: str, mensaje: str):
        """Simula envío de notificación por email"""
        notificacion = {
            "email": email,
            "libro": libro_nombre,
            "mensaje": mensaje
        }
        self.notificaciones.append(notificacion)
        print(f"📧 BioAlert: Email enviado a {email} sobre '{libro_nombre}': {mensaje}")

    def get_notificaciones(self) -> List[dict]:
        """Obtiene historial de notificaciones"""
        return self.notificaciones


# Instancia global singleton
bioalert = BioAlert()

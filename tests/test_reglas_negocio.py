import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.services.database import db


def crear_datos_base(client):
    """Helper para crear datos básicos de prueba"""
    autor = client.post(
        "/autores/",
        json={"nombre": "Ian Somerville", "fecha_nacimiento": "1951-02-23"}
    ).json()

    libro = client.post(
        "/libros/",
        json={"nombre": "Software Engineering", "anio": 2015, "autor_id": autor["id"]}
    ).json()

    lector = client.post(
        "/lectores/",
        json={"nombre": "Juan Estudiante", "email": "juan@example.com"}
    ).json()

    return {"autor": autor, "libro": libro, "lector": lector}


class TestLimite3Libros:
    """Tests para regla: máximo 3 libros por lector"""

    def test_prestar_3_libros_exitoso(self, client):
        """Test: Un lector puede tener exactamente 3 libros prestados"""
        data = crear_datos_base(client)

        # Crear 3 copias
        copias = []
        for i in range(3):
            copia = client.post("/copias/", json={"libro_id": data["libro"]["id"]}).json()
            copias.append(copia)

        # Prestar 3 libros
        for i in range(3):
            response = client.post(
                "/prestamos/",
                json={"lector_id": data["lector"]["id"], "copia_id": copias[i]["id"]}
            )
            assert response.status_code == 201

        # Verificar que el lector tiene 3 préstamos activos
        prestamos = client.get(f"/prestamos/lector/{data['lector']['id']}").json()
        assert len(prestamos) == 3

    def test_no_puede_prestar_mas_de_3_libros(self, client):
        """Test: No se puede prestar un 4to libro cuando ya tienes 3"""
        data = crear_datos_base(client)

        # Crear 4 copias
        copias = []
        for i in range(4):
            copia = client.post("/copias/", json={"libro_id": data["libro"]["id"]}).json()
            copias.append(copia)

        # Prestar 3 libros exitosamente
        for i in range(3):
            response = client.post(
                "/prestamos/",
                json={"lector_id": data["lector"]["id"], "copia_id": copias[i]["id"]}
            )
            assert response.status_code == 201

        # Intentar prestar el 4to libro - debe fallar
        response = client.post(
            "/prestamos/",
            json={"lector_id": data["lector"]["id"], "copia_id": copias[3]["id"]}
        )
        assert response.status_code == 400
        assert "3 libros en préstamo" in response.json()["detail"]
        assert "Máximo permitido alcanzado" in response.json()["detail"]

    def test_despues_de_devolver_puede_pedir_otro(self, client):
        """Test: Después de devolver un libro, puede pedir otro"""
        data = crear_datos_base(client)

        # Crear 4 copias
        copias = []
        for i in range(4):
            copia = client.post("/copias/", json={"libro_id": data["libro"]["id"]}).json()
            copias.append(copia)

        # Prestar 3 libros
        prestamos = []
        for i in range(3):
            prestamo = client.post(
                "/prestamos/",
                json={"lector_id": data["lector"]["id"], "copia_id": copias[i]["id"]}
            ).json()
            prestamos.append(prestamo)

        # Devolver uno
        client.post(f"/prestamos/{prestamos[0]['id']}/devolver")

        # Ahora debe poder pedir el 4to libro
        response = client.post(
            "/prestamos/",
            json={"lector_id": data["lector"]["id"], "copia_id": copias[3]["id"]}
        )
        assert response.status_code == 201

        # Verificar que tiene 3 préstamos activos (2 antiguos + 1 nuevo)
        prestamos_activos = client.get(f"/prestamos/lector/{data['lector']['id']}").json()
        assert len(prestamos_activos) == 3


class TestSistemaMultas:
    """Tests para sistema de multas y sanciones"""

    def test_devolucion_en_tiempo_sin_multa(self, client):
        """Test: Devolver en tiempo no genera multa"""
        data = crear_datos_base(client)
        copia = client.post("/copias/", json={"libro_id": data["libro"]["id"]}).json()

        # Crear préstamo
        prestamo = client.post(
            "/prestamos/",
            json={"lector_id": data["lector"]["id"], "copia_id": copia["id"]}
        ).json()

        # Devolver inmediatamente (sin retraso)
        response = client.post(f"/prestamos/{prestamo['id']}/devolver")
        resultado = response.json()

        assert resultado["dias_retraso"] == 0
        assert resultado["sancion_aplicada"] == 0

        # Verificar que el lector no tiene sanción
        lector = client.get(f"/lectores/{data['lector']['id']}").json()
        assert lector["dias_sancion"] == 0

    def test_devolucion_con_retraso_genera_multa_2x(self, client):
        """Test: 1 día de retraso = 2 días de sanción (multa 2x)"""
        data = crear_datos_base(client)
        copia = client.post("/copias/", json={"libro_id": data["libro"]["id"]}).json()

        # Crear préstamo
        prestamo = client.post(
            "/prestamos/",
            json={"lector_id": data["lector"]["id"], "copia_id": copia["id"]}
        ).json()

        # Simular retraso modificando la fecha esperada de devolución
        # Hacer que la fecha esperada sea 5 días en el pasado
        db.prestamos[prestamo["id"]]["fecha_devolucion_esperada"] = datetime.now() - timedelta(days=5)

        # Devolver con retraso
        response = client.post(f"/prestamos/{prestamo['id']}/devolver")
        resultado = response.json()

        assert resultado["dias_retraso"] == 5
        assert resultado["sancion_aplicada"] == 10  # 5 días * 2 = 10 días de sanción

        # Verificar que el lector tiene la sanción aplicada
        lector = client.get(f"/lectores/{data['lector']['id']}").json()
        assert lector["dias_sancion"] == 10

    def test_lector_con_sancion_no_puede_pedir_libros(self, client):
        """Test: Un lector con sanción activa no puede pedir libros"""
        data = crear_datos_base(client)
        copia1 = client.post("/copias/", json={"libro_id": data["libro"]["id"]}).json()
        copia2 = client.post("/copias/", json={"libro_id": data["libro"]["id"]}).json()

        # Crear préstamo con retraso para generar sanción
        prestamo1 = client.post(
            "/prestamos/",
            json={"lector_id": data["lector"]["id"], "copia_id": copia1["id"]}
        ).json()
        db.prestamos[prestamo1["id"]]["fecha_devolucion_esperada"] = datetime.now() - timedelta(days=10)
        client.post(f"/prestamos/{prestamo1['id']}/devolver")

        # Verificar que tiene sanción
        lector = client.get(f"/lectores/{data['lector']['id']}").json()
        assert lector["dias_sancion"] == 20  # 10 días * 2

        # Intentar pedir otro libro - debe fallar
        response = client.post(
            "/prestamos/",
            json={"lector_id": data["lector"]["id"], "copia_id": copia2["id"]}
        )
        assert response.status_code == 400
        assert "sanción" in response.json()["detail"]
        assert "20 días de sanción" in response.json()["detail"]
        assert "No puede pedir libros" in response.json()["detail"]


class TestBioAlertNotificaciones:
    """Tests para sistema BioAlert de notificaciones"""

    def test_suscripcion_genera_notificacion_confirmacion(self, client):
        """Test: Al suscribirse se envía notificación de confirmación"""
        data = crear_datos_base(client)

        response = client.post(
            "/bioalert/suscribir",
            json={"lector_id": data["lector"]["id"], "libro_id": data["libro"]["id"]}
        )
        assert response.status_code == 201

        # Verificar notificación de confirmación
        notif = client.get("/bioalert/notificaciones").json()["notificaciones"]
        assert len(notif) >= 1
        assert any("suscrito exitosamente" in n["mensaje"] for n in notif)

    def test_devolver_libro_notifica_suscriptores(self, client):
        """Test: Al devolver un libro se notifica a todos los suscriptores"""
        data = crear_datos_base(client)

        # Crear 3 lectores adicionales
        lectores_suscritos = []
        for i in range(3):
            lector = client.post(
                "/lectores/",
                json={"nombre": f"Lector {i}", "email": f"lector{i}@example.com"}
            ).json()
            lectores_suscritos.append(lector)

        # Todos se suscriben al mismo libro
        for lector in lectores_suscritos:
            client.post(
                "/bioalert/suscribir",
                json={"lector_id": lector["id"], "libro_id": data["libro"]["id"]}
            )

        # Crear copia y prestarla
        copia = client.post("/copias/", json={"libro_id": data["libro"]["id"]}).json()
        prestamo = client.post(
            "/prestamos/",
            json={"lector_id": data["lector"]["id"], "copia_id": copia["id"]}
        ).json()

        # Contar notificaciones antes de devolver
        notif_antes = len(client.get("/bioalert/notificaciones").json()["notificaciones"])

        # Devolver el libro
        client.post(f"/prestamos/{prestamo['id']}/devolver")

        # Verificar que se notificó a todos los suscriptores
        notif_despues = client.get("/bioalert/notificaciones").json()["notificaciones"]
        assert len(notif_despues) > notif_antes

        # Verificar que los 3 lectores recibieron notificación de disponibilidad
        notif_disponibilidad = [n for n in notif_despues if "disponible" in n["mensaje"]]
        emails_notificados = [n["email"] for n in notif_disponibilidad]

        for lector in lectores_suscritos:
            assert lector["email"] in emails_notificados

    def test_libro_sin_suscriptores_no_genera_notificaciones(self, client):
        """Test: Devolver libro sin suscriptores no genera notificaciones adicionales"""
        data = crear_datos_base(client)
        copia = client.post("/copias/", json={"libro_id": data["libro"]["id"]}).json()

        # Crear préstamo
        prestamo = client.post(
            "/prestamos/",
            json={"lector_id": data["lector"]["id"], "copia_id": copia["id"]}
        ).json()

        # Contar notificaciones antes
        notif_antes = len(client.get("/bioalert/notificaciones").json()["notificaciones"])

        # Devolver sin suscriptores
        client.post(f"/prestamos/{prestamo['id']}/devolver")

        # No debe haber nuevas notificaciones de disponibilidad
        notif_despues = client.get("/bioalert/notificaciones").json()["notificaciones"]
        notif_nuevas = [n for n in notif_despues[notif_antes:] if "disponible" in n["mensaje"]]
        assert len(notif_nuevas) == 0


class TestCopiaEstados:
    """Tests para estados de copias"""

    def test_copia_nueva_estado_en_biblioteca(self, client):
        """Test: Copia nueva tiene estado 'en_biblioteca'"""
        data = crear_datos_base(client)
        copia = client.post("/copias/", json={"libro_id": data["libro"]["id"]}).json()

        assert copia["estado"] == "en_biblioteca"

    def test_prestar_cambia_estado_a_prestada(self, client):
        """Test: Al prestar, el estado cambia a 'prestada'"""
        data = crear_datos_base(client)
        copia = client.post("/copias/", json={"libro_id": data["libro"]["id"]}).json()

        # Prestar
        client.post(
            "/prestamos/",
            json={"lector_id": data["lector"]["id"], "copia_id": copia["id"]}
        )

        # Verificar estado
        copia_actualizada = client.get(f"/copias/{copia['id']}").json()
        assert copia_actualizada["estado"] == "prestada"

    def test_devolver_cambia_estado_a_en_biblioteca(self, client):
        """Test: Al devolver, el estado vuelve a 'en_biblioteca'"""
        data = crear_datos_base(client)
        copia = client.post("/copias/", json={"libro_id": data["libro"]["id"]}).json()

        # Prestar
        prestamo = client.post(
            "/prestamos/",
            json={"lector_id": data["lector"]["id"], "copia_id": copia["id"]}
        ).json()

        # Devolver
        client.post(f"/prestamos/{prestamo['id']}/devolver")

        # Verificar que volvió a estar disponible
        copia_actualizada = client.get(f"/copias/{copia['id']}").json()
        assert copia_actualizada["estado"] == "en_biblioteca"

    def test_no_puede_prestar_copia_no_disponible(self, client):
        """Test: No se puede prestar una copia que no está en biblioteca"""
        data = crear_datos_base(client)
        copia = client.post("/copias/", json={"libro_id": data["libro"]["id"]}).json()

        # Cambiar estado manualmente a "en_reparacion"
        client.put(f"/copias/{copia['id']}/estado?estado=en_reparacion")

        # Intentar prestar - debe fallar
        response = client.post(
            "/prestamos/",
            json={"lector_id": data["lector"]["id"], "copia_id": copia["id"]}
        )
        assert response.status_code == 400
        assert "no está disponible" in response.json()["detail"]


class TestBusquedaLibrosPorAutor:
    """Tests para búsqueda de libros por autor (caso de Somerville)"""

    def test_buscar_libros_somerville(self, client):
        """Test: Buscar todos los libros de Somerville (caso del diálogo)"""
        # Crear autor Somerville
        somerville = client.post(
            "/autores/",
            json={"nombre": "Ian Somerville", "fecha_nacimiento": "1951-02-23"}
        ).json()

        # Crear varios libros de Somerville (diferentes ediciones)
        libros = [
            {"nombre": "Software Engineering 8th Edition", "anio": 2006},
            {"nombre": "Software Engineering 9th Edition", "anio": 2010},
            {"nombre": "Software Engineering 10th Edition", "anio": 2015},
            {"nombre": "Software Engineering (Spanish)", "anio": 2012},
        ]

        for libro_data in libros:
            client.post(
                "/libros/",
                json={**libro_data, "autor_id": somerville["id"]}
            )

        # Buscar libros de Somerville
        response = client.get("/libros/buscar/Somerville")
        assert response.status_code == 200
        libros_encontrados = response.json()

        assert len(libros_encontrados) == 4
        assert all("Somerville" in libro["autor"]["nombre"] for libro in libros_encontrados)
        assert all("Software Engineering" in libro["nombre"] for libro in libros_encontrados)

    def test_contar_copias_de_libro_somerville(self, client):
        """Test: ¿Cuántos libros de Somerville tienen? (cuenta las copias)"""
        # Crear autor y libro
        somerville = client.post(
            "/autores/",
            json={"nombre": "Ian Somerville", "fecha_nacimiento": "1951-02-23"}
        ).json()

        libro = client.post(
            "/libros/",
            json={"nombre": "Software Engineering", "anio": 2015, "autor_id": somerville["id"]}
        ).json()

        # Crear 15 copias (como en el diálogo: "quince")
        for i in range(15):
            client.post("/copias/", json={"libro_id": libro["id"]})

        # Verificar cantidad de copias
        copias = client.get(f"/copias/libro/{libro['id']}").json()
        assert len(copias) == 15


class TestPrestamoLibroSinCopias:
    """Tests para el caso de libros nuevos sin copias (caso del diálogo)"""

    def test_libro_nuevo_sin_copias(self, client):
        """Test: Libro nuevo no tiene copias disponibles"""
        somerville = client.post(
            "/autores/",
            json={"nombre": "Ian Somerville", "fecha_nacimiento": "1951-02-23"}
        ).json()

        libro_nuevo = client.post(
            "/libros/",
            json={"nombre": "Software Engineering 10th Edition", "anio": 2015, "autor_id": somerville["id"]}
        ).json()

        # Verificar que no tiene copias
        copias = client.get(f"/copias/libro/{libro_nuevo['id']}").json()
        assert len(copias) == 0

    def test_suscribirse_a_libro_sin_copias(self, client):
        """Test: Estudiante se suscribe para obtener libro cuando esté disponible"""
        somerville = client.post(
            "/autores/",
            json={"nombre": "Ian Somerville", "fecha_nacimiento": "1951-02-23"}
        ).json()

        libro_nuevo = client.post(
            "/libros/",
            json={"nombre": "Software Engineering 10th Edition", "anio": 2015, "autor_id": somerville["id"]}
        ).json()

        estudiante = client.post(
            "/lectores/",
            json={"nombre": "Estudiante", "email": "estudiante@utec.edu.pe"}
        ).json()

        # Suscribirse al libro
        response = client.post(
            "/bioalert/suscribir",
            json={"lector_id": estudiante["id"], "libro_id": libro_nuevo["id"]}
        )
        assert response.status_code == 201

        # Verificar que la suscripción existe
        suscripciones = client.get(f"/bioalert/suscripciones/libro/{libro_nuevo['id']}").json()
        assert len(suscripciones) == 1
        assert suscripciones[0]["lector_id"] == estudiante["id"]

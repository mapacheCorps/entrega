from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db.conexion import conectar
from app.integraciones.almacenamiento import ErrorAlmacenamiento
from app.main import create_app
from tests.conftest import datos_aporte


class AlmacenamientoQueFalla:
    def guardar(self, archivo, aporte_id, version_id):
        raise ErrorAlmacenamiento("Fallo simulado del almacenamiento.")

    def eliminar(self, referencia):
        return None


def _contar(ruta_db, tabla: str) -> int:
    conexion = conectar(ruta_db)
    try:
        return conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
    finally:
        conexion.close()


def _estado_aporte(ruta_db, aporte_id: int) -> str:
    conexion = conectar(ruta_db)
    try:
        return conexion.execute(
            "SELECT estado FROM aportes WHERE id = ?", (aporte_id,)
        ).fetchone()["estado"]
    finally:
        conexion.close()


def test_inicio_y_formulario_disponibles(cliente, catalogos):
    inicio = cliente.get("/")
    assert inicio.status_code == 200
    assert "Torpedos universitarios" in inicio.text

    formulario = cliente.get("/aportes/nuevo")
    assert formulario.status_code == 200
    assert "Ingeniería Civil Informática" in formulario.text
    assert "Cálculo I" in formulario.text
    assert "2026" in formulario.text
    assert "Límites y continuidad" in formulario.text


def test_selector_de_rol_cambia_el_perfil(cliente):
    respuesta = cliente.post(
        "/demo/rol", data={"rol": "Moderador"}, follow_redirects=False
    )
    assert respuesta.status_code == 303
    assert cliente.cookies.get("demo_role") == "Moderador"

    inicio = cliente.get("/")
    assert "Moderador" in inicio.text
    assert "Comunidad Estudiantil" in inicio.text
    assert "cambia al perfil" in inicio.text

    formulario = cliente.get("/aportes/nuevo")
    assert "Solo el perfil" in formulario.text
    assert "Estudiante" in formulario.text


def test_selector_solo_ofrece_estudiante_y_moderador(cliente):
    inicio = cliente.get("/")
    assert '<option value="Estudiante"' in inicio.text
    assert '<option value="Moderador"' in inicio.text
    assert '<option value="Ayudante"' not in inicio.text
    assert '<option value="Coordinador"' not in inicio.text


def test_rol_no_valido_es_rechazado(cliente):
    for rol in ("Administrador", "Ayudante", "Coordinador"):
        respuesta = cliente.post("/demo/rol", data={"rol": rol})
        assert respuesta.status_code == 400


def test_rol_no_estudiante_no_puede_crear_aportes(
    cliente, catalogos, ruta_db
):
    cliente.post("/demo/rol", data={"rol": "Moderador"})
    respuesta = cliente.post(
        "/aportes",
        data=datos_aporte(catalogos),
        files={"archivo": ("apunte.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert respuesta.status_code == 403
    assert "Solo el perfil de demostración Estudiante" in respuesta.text
    assert _contar(ruta_db, "aportes") == 0


def test_envio_valido_redirige_al_detalle(cliente, catalogos, ruta_db):
    respuesta = cliente.post(
        "/aportes",
        data=datos_aporte(catalogos),
        files={"archivo": ("apunte.pdf", b"%PDF-1.4 apunte", "application/pdf")},
        follow_redirects=False,
    )

    assert respuesta.status_code == 303
    assert respuesta.headers["location"].startswith("/aportes/")

    detalle = cliente.get(respuesta.headers["location"])
    assert detalle.status_code == 200
    assert "Pendiente de asignación" in detalle.text
    assert "Pendiente de revisión" in detalle.text
    assert "aún no se publica" in detalle.text
    assert "número 1" in detalle.text
    assert "SHA-256" not in detalle.text
    assert "Referencia de almacenamiento" not in detalle.text
    assert "Tipo MIME" not in detalle.text
    assert "Creada" not in detalle.text
    assert _contar(ruta_db, "aportes") == 1
    assert _contar(ruta_db, "versiones_apunte") == 1


def test_datos_faltantes_vuelven_al_formulario(cliente, catalogos, ruta_db):
    datos = datos_aporte(catalogos, procedencia="")
    respuesta = cliente.post(
        "/aportes",
        data=datos,
        files={"archivo": ("apunte.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert respuesta.status_code == 400
    assert "Declara la procedencia del apunte." in respuesta.text
    assert _contar(ruta_db, "aportes") == 0


def test_sin_archivo_no_se_crea_nada(cliente, catalogos, ruta_db):
    respuesta = cliente.post("/aportes", data=datos_aporte(catalogos))

    assert respuesta.status_code == 400
    assert "Adjunta el archivo del apunte." in respuesta.text
    assert _contar(ruta_db, "aportes") == 0


def test_archivo_invalido_muestra_requiere_correccion(cliente, catalogos, ruta_db):
    respuesta = cliente.post(
        "/aportes",
        data=datos_aporte(catalogos),
        files={"archivo": ("apunte.exe", b"contenido", "application/octet-stream")},
    )

    assert respuesta.status_code == 400
    assert "Requiere corrección" in respuesta.text
    assert "Subir un archivo corregido" in respuesta.text
    assert _contar(ruta_db, "aportes") == 1
    assert _estado_aporte(ruta_db, 1) == "RequiereCorreccion"


def test_correccion_de_extremo_a_extremo(cliente, catalogos, ruta_db):
    inicial = cliente.post(
        "/aportes",
        data=datos_aporte(catalogos),
        files={"archivo": ("apunte.pdf", b"", "application/pdf")},
    )
    assert inicial.status_code == 400
    aporte_id = 1

    formulario = cliente.get(f"/aportes/{aporte_id}/corregir")
    assert formulario.status_code == 200
    assert "Corregir el aporte" in formulario.text

    correccion = cliente.post(
        f"/aportes/{aporte_id}/correcciones",
        files={"archivo": ("apunte.pdf", b"contenido corregido", "application/pdf")},
        follow_redirects=False,
    )
    assert correccion.status_code == 303

    detalle = cliente.get(correccion.headers["location"])
    assert "Pendiente de asignación" in detalle.text
    assert "Pendiente de revisión" in detalle.text
    assert "número 2" in detalle.text

    conexion = conectar(ruta_db)
    try:
        versiones = conexion.execute(
            "SELECT numero, estado FROM versiones_apunte ORDER BY numero"
        ).fetchall()
    finally:
        conexion.close()
    assert [(fila["numero"], fila["estado"]) for fila in versiones] == [
        (1, "Final"),
        (2, "PendienteRevision"),
    ]


def test_duplicado_exacto_muestra_la_coincidencia(cliente, catalogos, ruta_db):
    archivo = ("apunte.pdf", b"%PDF-1.4 mismo archivo", "application/pdf")
    primero = cliente.post(
        "/aportes",
        data=datos_aporte(catalogos),
        files={"archivo": archivo},
        follow_redirects=False,
    )
    assert primero.status_code == 303

    segundo = cliente.post(
        "/aportes",
        data=datos_aporte(catalogos),
        files={"archivo": ("copia.pdf", b"%PDF-1.4 mismo archivo", "application/pdf")},
    )

    assert segundo.status_code == 409
    assert "Ya existe un archivo idéntico registrado" in segundo.text
    assert "no es una aprobación académica" in segundo.text
    assert _contar(ruta_db, "aportes") == 1


def test_fallo_de_almacenamiento_muestra_error_y_no_registra(
    ruta_db, catalogos
):
    app = create_app(db_path=ruta_db, almacenamiento=AlmacenamientoQueFalla())
    with TestClient(app) as cliente:
        respuesta = cliente.post(
            "/aportes",
            data=datos_aporte(catalogos),
            files={"archivo": ("apunte.pdf", b"%PDF-1.4", "application/pdf")},
        )

    assert respuesta.status_code == 502
    assert "Fallo simulado del almacenamiento." in respuesta.text
    assert _contar(ruta_db, "aportes") == 0


def test_detalle_inexistente_devuelve_404(cliente):
    respuesta = cliente.get("/aportes/999")
    assert respuesta.status_code == 404
    assert "Aporte no encontrado" in respuesta.text


def test_rol_no_estudiante_no_puede_corregir(cliente, catalogos):
    cliente.post(
        "/aportes",
        data=datos_aporte(catalogos),
        files={"archivo": ("apunte.pdf", b"", "application/pdf")},
    )
    cliente.post("/demo/rol", data={"rol": "Moderador"})

    respuesta = cliente.get("/aportes/1/corregir")
    assert respuesta.status_code == 403

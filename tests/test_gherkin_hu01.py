"""Escenarios Gherkin de HU-01, uno por prueba."""

from __future__ import annotations

from app.db.conexion import conectar
from tests.conftest import datos_aporte


def _consultar(ruta_db, sql: str, parametros=()):
    conexion = conectar(ruta_db)
    try:
        return conexion.execute(sql, parametros).fetchall()
    finally:
        conexion.close()


def test_escenario_registro_de_aporte_completo(cliente, catalogos, ruta_db):
    # Dado un estudiante autor que aporta un archivo no vacío
    # Y el archivo cumple formato/tamaño y se declara la clasificación completa
    respuesta = cliente.post(
        "/aportes",
        data=datos_aporte(catalogos),
        files={"archivo": ("apunte.pdf", b"%PDF-1.4 apunte completo", "application/pdf")},
        follow_redirects=False,
    )

    # Cuando el autor presenta el aporte
    assert respuesta.status_code == 303

    # Entonces el sistema registra el aporte y su primera versión
    aportes = _consultar(ruta_db, "SELECT * FROM aportes")
    versiones = _consultar(ruta_db, "SELECT * FROM versiones_apunte")
    assert len(aportes) == 1
    assert len(versiones) == 1
    assert versiones[0]["numero"] == 1

    # Y la versión queda pendiente de asignación o revisión, sin publicarse
    assert aportes[0]["estado"] == "PendienteAsignacion"
    assert versiones[0]["estado"] == "PendienteRevision"
    assert versiones[0]["referencia_archivo"]

    detalle = cliente.get(respuesta.headers["location"])
    assert "aún no se publica" in detalle.text


def test_escenario_datos_de_aporte_invalidos(cliente, catalogos, ruta_db):
    # Dado el autor presenta un aporte con datos obligatorios faltantes
    faltantes = cliente.post(
        "/aportes",
        data=datos_aporte(catalogos, ramo_id="", tema_id=""),
        files={"archivo": ("apunte.pdf", b"%PDF-1.4", "application/pdf")},
    )

    # Cuando el autor presenta el aporte
    # Entonces se identifica la causa del incumplimiento
    assert faltantes.status_code == 400
    assert "Selecciona un ramo." in faltantes.text
    assert "Selecciona un tema." in faltantes.text

    # Y no se remite la versión a revisión hasta corregirla
    assert _consultar(ruta_db, "SELECT * FROM aportes") == []
    assert _consultar(ruta_db, "SELECT * FROM versiones_apunte") == []

    # Caso con datos completos y archivo inválido
    invalido = cliente.post(
        "/aportes",
        data=datos_aporte(catalogos),
        files={"archivo": ("apunte.exe", b"contenido", "application/octet-stream")},
    )
    assert invalido.status_code == 400
    assert "no está permitido" in invalido.text

    aportes = _consultar(ruta_db, "SELECT * FROM aportes")
    versiones = _consultar(ruta_db, "SELECT * FROM versiones_apunte")
    assert len(aportes) == 1
    assert len(versiones) == 1
    assert versiones[0]["estado"] == "RequiereCorreccion"
    assert versiones[0]["estado"] != "PendienteRevision"


def test_escenario_archivo_duplicado_exacto(cliente, catalogos, ruta_db):
    # Dado existe un archivo idéntico ya registrado
    contenido = b"%PDF-1.4 archivo repetido"
    primero = cliente.post(
        "/aportes",
        data=datos_aporte(catalogos),
        files={"archivo": ("original.pdf", contenido, "application/pdf")},
        follow_redirects=False,
    )
    assert primero.status_code == 303

    # Cuando el autor presenta el aporte
    segundo = cliente.post(
        "/aportes",
        data=datos_aporte(catalogos),
        files={"archivo": ("copia.pdf", contenido, "application/pdf")},
    )

    # Entonces se informa la coincidencia exacta
    assert segundo.status_code == 409
    assert "Ya existe un archivo idéntico registrado" in segundo.text

    # Y la coincidencia no se interpreta como aprobación académica
    assert "no es una aprobación académica" in segundo.text
    assert len(_consultar(ruta_db, "SELECT * FROM aportes")) == 1
    assert len(_consultar(ruta_db, "SELECT * FROM versiones_apunte")) == 1

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db.conexion import aplicar_migraciones, conectar
from app.db.seed import sembrar
from app.integraciones.almacenamiento import AlmacenamientoLocal
from app.main import create_app
from app.servicios.validacion import ArchivoSubido


def obtener_catalogos(ruta) -> dict[str, int]:
    conexion = conectar(ruta)
    try:
        carrera_ici = conexion.execute(
            "SELECT id FROM carreras WHERE codigo = 'ICI'"
        ).fetchone()["id"]
        carrera_ico = conexion.execute(
            "SELECT id FROM carreras WHERE codigo = 'ICO'"
        ).fetchone()["id"]
        ramo_req = conexion.execute("SELECT id FROM ramos WHERE codigo = 'REQ'").fetchone()[
            "id"
        ]
        ramo_cal = conexion.execute("SELECT id FROM ramos WHERE codigo = 'CAL1'").fetchone()[
            "id"
        ]
        ramo_mic = conexion.execute("SELECT id FROM ramos WHERE codigo = 'MIC'").fetchone()[
            "id"
        ]
        periodo = conexion.execute(
            "SELECT id FROM periodos_academicos WHERE anio = 2026 AND semestre = 1"
        ).fetchone()["id"]
        tema_req = conexion.execute(
            "SELECT id FROM temas_unidad WHERE ramo_id = ? AND numero = 1", (ramo_req,)
        ).fetchone()["id"]
        tema_cal = conexion.execute(
            "SELECT id FROM temas_unidad WHERE ramo_id = ? AND numero = 1", (ramo_cal,)
        ).fetchone()["id"]
        return {
            "carrera_id": carrera_ici,
            "otra_carrera_id": carrera_ico,
            "ramo_id": ramo_req,
            "otro_ramo_id": ramo_cal,
            "ramo_otra_carrera_id": ramo_mic,
            "periodo_id": periodo,
            "tema_id": tema_req,
            "tema_otro_ramo_id": tema_cal,
        }
    finally:
        conexion.close()


def datos_aporte(catalogos: dict[str, int], **cambios: object) -> dict[str, str]:
    datos = {
        "procedencia": "Apuntes de la clase de requisitos",
        "carrera_id": str(catalogos["carrera_id"]),
        "ramo_id": str(catalogos["ramo_id"]),
        "periodo_id": str(catalogos["periodo_id"]),
        "tema_id": str(catalogos["tema_id"]),
    }
    datos.update({clave: str(valor) for clave, valor in cambios.items()})
    return datos


def archivo_pdf(contenido: bytes = b"%PDF-1.4 apunte de prueba") -> ArchivoSubido:
    return ArchivoSubido(
        nombre="apunte.pdf", contenido=contenido, tipo_mime="application/pdf"
    )


@pytest.fixture
def ruta_db(tmp_path):
    ruta = tmp_path / "app.db"
    conexion = conectar(ruta)
    try:
        aplicar_migraciones(conexion)
        sembrar(conexion)
    finally:
        conexion.close()
    return ruta


@pytest.fixture
def almacenamiento(tmp_path):
    return AlmacenamientoLocal(tmp_path / "archivos")


@pytest.fixture
def app(ruta_db, almacenamiento):
    return create_app(db_path=ruta_db, almacenamiento=almacenamiento)


@pytest.fixture
def cliente(app):
    with TestClient(app) as cliente_prueba:
        yield cliente_prueba


@pytest.fixture
def catalogos(ruta_db):
    return obtener_catalogos(ruta_db)

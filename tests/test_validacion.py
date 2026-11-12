from __future__ import annotations

import pytest

from app.db.conexion import conectar
from app.servicios.validacion import (
    MAX_BYTES,
    ArchivoSubido,
    calcular_hash,
    validar_archivo,
    validar_datos,
)
from tests.conftest import datos_aporte


@pytest.fixture
def conexion(ruta_db):
    conexion = conectar(ruta_db)
    yield conexion
    conexion.close()


def test_datos_completos_no_tienen_errores(conexion, catalogos):
    assert (
        validar_datos(
            conexion, datos_aporte(catalogos), archivo_presente=True
        )
        == {}
    )


@pytest.mark.parametrize(
    ("campo", "valor", "clave"),
    [
        ("procedencia", "", "procedencia"),
        ("carrera_id", "", "carrera_id"),
        ("ramo_id", "", "ramo_id"),
        ("periodo_id", "", "periodo_id"),
        ("tema_id", "", "tema_id"),
    ],
)
def test_cada_campo_obligatorio_se_valida(conexion, catalogos, campo, valor, clave):
    datos = datos_aporte(catalogos, **{campo: valor})
    errores = validar_datos(conexion, datos, archivo_presente=True)
    assert clave in errores


def test_archivo_es_obligatorio(conexion, catalogos):
    errores = validar_datos(
        conexion, datos_aporte(catalogos), archivo_presente=False
    )
    assert "archivo" in errores


def test_ramo_debe_pertenecer_a_la_carrera(conexion, catalogos):
    datos = datos_aporte(catalogos, carrera_id=catalogos["otra_carrera_id"])
    errores = validar_datos(conexion, datos, archivo_presente=True)
    assert "ramo_id" in errores


def test_tema_debe_pertenecer_al_ramo(conexion, catalogos):
    datos = datos_aporte(catalogos, tema_id=catalogos["tema_otro_ramo_id"])
    errores = validar_datos(conexion, datos, archivo_presente=True)
    assert "tema_id" in errores


def test_identificadores_inexistentes_se_rechazan(conexion, catalogos):
    datos = datos_aporte(catalogos, ramo_id=9999, tema_id=9999, periodo_id=9999)
    errores = validar_datos(conexion, datos, archivo_presente=True)
    assert "ramo_id" in errores
    assert "tema_id" in errores
    assert "periodo_id" in errores


def test_archivo_valido():
    assert validar_archivo(ArchivoSubido("apunte.pdf", b"contenido")) == []
    assert validar_archivo(ArchivoSubido("apunte.docx", b"contenido")) == []
    assert validar_archivo(ArchivoSubido("apunte.pptx", b"contenido")) == []
    assert validar_archivo(ArchivoSubido("apunte.png", b"contenido")) == []
    assert validar_archivo(ArchivoSubido("apunte.jpg", b"contenido")) == []


def test_archivo_ausente_o_vacio():
    assert validar_archivo(None) == ["Adjunta el archivo del apunte."]
    errores = validar_archivo(ArchivoSubido("apunte.pdf", b""))
    assert "El archivo está vacío." in errores


def test_archivo_con_extension_no_permitida():
    errores = validar_archivo(ArchivoSubido("apunte.exe", b"contenido"))
    assert any("formato" in error for error in errores)
    assert all(".pdf" in error for error in errores if "formato" in error)


def test_archivo_de_10_mb_es_valido_y_uno_mas_grande_no():
    contenido = b"a" * MAX_BYTES
    assert validar_archivo(ArchivoSubido("apunte.pdf", contenido)) == []
    errores = validar_archivo(ArchivoSubido("apunte.pdf", contenido + b"a"))
    assert "El archivo supera el tamaño máximo de 10 MB." in errores


def test_hash_es_estable_y_distingue_contenidos():
    assert calcular_hash(b"mismo contenido") == calcular_hash(b"mismo contenido")
    assert calcular_hash(b"contenido A") != calcular_hash(b"contenido B")
    assert len(calcular_hash(b"x")) == 64

from __future__ import annotations

import pytest

from app.integraciones.almacenamiento import (
    AlmacenamientoLocal,
    ErrorAlmacenamiento,
    nombre_seguro,
)
from app.servicios.validacion import ArchivoSubido


def test_guardar_archivo_y_devolver_referencia(tmp_path):
    almacenamiento = AlmacenamientoLocal(tmp_path / "archivos")
    archivo = ArchivoSubido("apunte.pdf", b"contenido del apunte", "application/pdf")

    referencia = almacenamiento.guardar(archivo, aporte_id=7, version_id=3)

    assert referencia == "7/3_apunte.pdf"
    destino = tmp_path / "archivos" / referencia
    assert destino.read_bytes() == b"contenido del apunte"


def test_nombre_seguro_elimina_rutas_y_caracteres_peligrosos():
    assert nombre_seguro("../../evil.pdf") == "evil.pdf"
    assert nombre_seguro("..\\..\\evil.pdf") == "evil.pdf"
    assert nombre_seguro("apunte con espacios.pdf") == "apunte_con_espacios.pdf"
    assert nombre_seguro("...") == "archivo"


def test_guardar_sanea_el_nombre(tmp_path):
    almacenamiento = AlmacenamientoLocal(tmp_path / "archivos")
    archivo = ArchivoSubido("../../apunte final.pdf", b"contenido")

    referencia = almacenamiento.guardar(archivo, aporte_id=1, version_id=1)

    assert referencia == "1/1_apunte_final.pdf"
    assert (tmp_path / "archivos" / referencia).exists()
    assert not (tmp_path / "apunte final.pdf").exists()


def test_eliminar_archivo_y_carpeta_vacia(tmp_path):
    almacenamiento = AlmacenamientoLocal(tmp_path / "archivos")
    archivo = ArchivoSubido("apunte.pdf", b"contenido")
    referencia = almacenamiento.guardar(archivo, aporte_id=2, version_id=1)

    almacenamiento.eliminar(referencia)

    assert not (tmp_path / "archivos" / referencia).exists()
    assert not (tmp_path / "archivos" / "2").exists()


def test_eliminar_referencia_fuera_de_la_base_es_ignorada(tmp_path):
    almacenamiento = AlmacenamientoLocal(tmp_path / "archivos")
    externo = tmp_path / "externo.txt"
    externo.write_text("no borrar", encoding="utf-8")

    almacenamiento.eliminar("../externo.txt")

    assert externo.exists()


def test_guardar_falla_si_la_base_es_un_archivo(tmp_path):
    bloqueante = tmp_path / "bloqueante"
    bloqueante.write_text("archivo", encoding="utf-8")
    almacenamiento = AlmacenamientoLocal(bloqueante)

    with pytest.raises(ErrorAlmacenamiento):
        almacenamiento.guardar(ArchivoSubido("apunte.pdf", b"contenido"), 1, 1)

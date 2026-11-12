from __future__ import annotations

import pytest

from app.db.conexion import conectar
from app.integraciones.almacenamiento import ErrorAlmacenamiento
from app.servicios.aportes import ServicioAportes, TipoResultado
from app.servicios.validacion import ArchivoSubido
from tests.conftest import archivo_pdf, datos_aporte


class AlmacenamientoQueFalla:
    def __init__(self):
        self.eliminados: list[str] = []

    def guardar(self, archivo, aporte_id, version_id):
        raise ErrorAlmacenamiento("Fallo simulado del almacenamiento.")

    def eliminar(self, referencia):
        self.eliminados.append(referencia)


@pytest.fixture
def conexion(ruta_db):
    conexion = conectar(ruta_db)
    yield conexion
    conexion.close()


@pytest.fixture
def servicio(conexion, almacenamiento):
    return ServicioAportes(conexion, almacenamiento)


def _contar(conexion, tabla: str) -> int:
    return conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]


def test_envio_valido_registra_aporte_y_primera_version(
    conexion, almacenamiento, catalogos, servicio
):
    resultado = servicio.enviar(datos_aporte(catalogos), archivo_pdf())

    assert resultado.tipo is TipoResultado.REGISTRADO
    aporte = conexion.execute("SELECT * FROM aportes").fetchone()
    version = conexion.execute("SELECT * FROM versiones_apunte").fetchone()
    assert aporte["estado"] == "PendienteAsignacion"
    assert version["numero"] == 1
    assert version["estado"] == "PendienteRevision"
    assert version["referencia_archivo"]
    assert version["hash_archivo"]
    assert (almacenamiento.base_dir / version["referencia_archivo"]).exists()


def test_envio_sin_datos_obligatorios_no_escribe(conexion, catalogos, servicio):
    resultado = servicio.enviar(
        datos_aporte(catalogos, procedencia=""), archivo_pdf()
    )

    assert resultado.tipo is TipoResultado.DATOS_INVALIDOS
    assert "procedencia" in resultado.errores
    assert _contar(conexion, "aportes") == 0
    assert _contar(conexion, "versiones_apunte") == 0


def test_archivo_invalido_con_datos_completos_crea_requiere_correccion(
    conexion, almacenamiento, catalogos, servicio
):
    archivo = ArchivoSubido("apunte.exe", b"contenido no permitido")
    resultado = servicio.enviar(datos_aporte(catalogos), archivo)

    assert resultado.tipo is TipoResultado.ARCHIVO_INVALIDO
    aporte = conexion.execute("SELECT * FROM aportes").fetchone()
    version = conexion.execute("SELECT * FROM versiones_apunte").fetchone()
    assert aporte["estado"] == "RequiereCorreccion"
    assert version["estado"] == "RequiereCorreccion"
    assert version["referencia_archivo"] is None
    assert version["hash_archivo"] is None
    assert not almacenamiento.base_dir.exists()


def test_duplicado_exacto_no_crea_un_segundo_aporte(conexion, catalogos, servicio):
    primero = servicio.enviar(datos_aporte(catalogos), archivo_pdf())
    assert primero.tipo is TipoResultado.REGISTRADO

    segundo = servicio.enviar(
        datos_aporte(catalogos),
        ArchivoSubido("copia.pdf", b"%PDF-1.4 apunte de prueba", "application/pdf"),
    )

    assert segundo.tipo is TipoResultado.DUPLICADO
    assert segundo.duplicado["aporte_id"] == primero.aporte_id
    assert "no es una aprobación académica" in (segundo.mensaje or "")
    assert _contar(conexion, "aportes") == 1
    assert _contar(conexion, "versiones_apunte") == 1


def test_correccion_valida_crea_nueva_version_y_cierra_la_anterior(
    conexion, almacenamiento, catalogos, servicio
):
    inicial = servicio.enviar(
        datos_aporte(catalogos), ArchivoSubido("apunte.pdf", b"")
    )
    assert inicial.tipo is TipoResultado.ARCHIVO_INVALIDO

    resultado = servicio.corregir(
        inicial.aporte_id, archivo_pdf(b"contenido corregido")
    )

    assert resultado.tipo is TipoResultado.REGISTRADO
    versiones = conexion.execute(
        "SELECT numero, estado, referencia_archivo FROM versiones_apunte ORDER BY numero"
    ).fetchall()
    assert [(fila["numero"], fila["estado"]) for fila in versiones] == [
        (1, "Final"),
        (2, "PendienteRevision"),
    ]
    assert conexion.execute("SELECT estado FROM aportes").fetchone()["estado"] == (
        "PendienteAsignacion"
    )
    assert (almacenamiento.base_dir / versiones[1]["referencia_archivo"]).exists()


def test_correccion_invalida_repite_el_ciclo(conexion, catalogos, servicio):
    inicial = servicio.enviar(
        datos_aporte(catalogos), ArchivoSubido("apunte.pdf", b"")
    )
    assert inicial.tipo is TipoResultado.ARCHIVO_INVALIDO

    resultado = servicio.corregir(
        inicial.aporte_id, ArchivoSubido("apunte.exe", b"contenido")
    )

    assert resultado.tipo is TipoResultado.ARCHIVO_INVALIDO
    versiones = conexion.execute(
        "SELECT numero, estado FROM versiones_apunte ORDER BY numero"
    ).fetchall()
    assert [(fila["numero"], fila["estado"]) for fila in versiones] == [
        (1, "Final"),
        (2, "RequiereCorreccion"),
    ]
    assert conexion.execute("SELECT estado FROM aportes").fetchone()["estado"] == (
        "RequiereCorreccion"
    )


def test_fallo_de_almacenamiento_no_confirma_el_registro(conexion, catalogos):
    almacenamiento = AlmacenamientoQueFalla()
    servicio = ServicioAportes(conexion, almacenamiento)

    resultado = servicio.enviar(datos_aporte(catalogos), archivo_pdf())

    assert resultado.tipo is TipoResultado.ERROR_ALMACENAMIENTO
    assert "Fallo simulado" in (resultado.mensaje or "")
    assert _contar(conexion, "aportes") == 0
    assert _contar(conexion, "versiones_apunte") == 0


def test_fallo_de_almacenamiento_en_correccion_no_cambia_la_version(
    conexion, catalogos, servicio
):
    inicial = servicio.enviar(
        datos_aporte(catalogos), ArchivoSubido("apunte.pdf", b"")
    )
    servicio_con_fallo = ServicioAportes(conexion, AlmacenamientoQueFalla())

    resultado = servicio_con_fallo.corregir(
        inicial.aporte_id, archivo_pdf(b"contenido corregido")
    )

    assert resultado.tipo is TipoResultado.ERROR_ALMACENAMIENTO
    version = conexion.execute("SELECT * FROM versiones_apunte").fetchone()
    assert version["estado"] == "RequiereCorreccion"
    assert version["numero"] == 1
    assert conexion.execute("SELECT estado FROM aportes").fetchone()["estado"] == (
        "RequiereCorreccion"
    )


def test_compensacion_elimina_el_archivo_si_falla_la_insercion(
    conexion, almacenamiento, catalogos, servicio, monkeypatch
):
    def fallar_al_insertar(**_kwargs):
        raise RuntimeError("Fallo simulado de inserción")

    monkeypatch.setattr(
        servicio.repo, "crear_aporte_con_version", fallar_al_insertar
    )

    resultado = servicio.enviar(datos_aporte(catalogos), archivo_pdf())

    assert resultado.tipo is TipoResultado.ERROR_ALMACENAMIENTO
    assert _contar(conexion, "aportes") == 0
    assert _contar(conexion, "versiones_apunte") == 0
    archivos = list(almacenamiento.base_dir.rglob("*")) if almacenamiento.base_dir.exists() else []
    assert archivos == []


def test_corregir_aporte_inexistente_o_que_no_lo_requiere(conexion, catalogos, servicio):
    assert servicio.corregir(999, archivo_pdf()).tipo is TipoResultado.NO_ENCONTRADO

    valido = servicio.enviar(datos_aporte(catalogos), archivo_pdf())
    resultado = servicio.corregir(valido.aporte_id, archivo_pdf(b"otro contenido"))
    assert resultado.tipo is TipoResultado.NO_CORREGIBLE


def test_duplicado_al_corregir_no_modifica_el_aporte(
    conexion, catalogos, servicio
):
    primero = servicio.enviar(datos_aporte(catalogos), archivo_pdf(b"contenido original"))
    assert primero.tipo is TipoResultado.REGISTRADO

    segundo = servicio.enviar(
        datos_aporte(catalogos), ArchivoSubido("apunte.pdf", b"")
    )
    assert segundo.tipo is TipoResultado.ARCHIVO_INVALIDO

    resultado = servicio.corregir(
        segundo.aporte_id, archivo_pdf(b"contenido original")
    )

    assert resultado.tipo is TipoResultado.DUPLICADO
    versiones = conexion.execute(
        "SELECT numero, estado FROM versiones_apunte WHERE aporte_id = ?",
        (segundo.aporte_id,),
    ).fetchall()
    assert [(fila["numero"], fila["estado"]) for fila in versiones] == [
        (1, "RequiereCorreccion")
    ]

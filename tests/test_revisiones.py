from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import sqlite3
from threading import Barrier

import pytest

from app.db.conexion import conectar
from app.dominio.revisiones import RevisionAcademicaRepositorio
from app.servicios.aportes import ServicioAportes
from app.servicios.revisiones import DatosRevisionInvalidos, ErrorRevision, MotivoRevision, ServicioRevisiones
from tests.conftest import archivo_pdf, datos_aporte


@pytest.fixture
def pendiente(ruta_db, almacenamiento, catalogos):
    with closing(conectar(ruta_db)) as conexion:
        aporte_id = ServicioAportes(conexion, almacenamiento).enviar(
            datos_aporte(catalogos), archivo_pdf()
        ).aporte_id
        moderador = conexion.execute(
            "SELECT * FROM estudiantes WHERE rol = 'Moderador'"
        ).fetchone()
        version_id = conexion.execute(
            "SELECT id FROM versiones_apunte WHERE aporte_id = ?", (aporte_id,)
        ).fetchone()[0]
    return aporte_id, version_id, moderador


def test_consulta_muestra_la_ultima_version(ruta_db, pendiente):
    aporte_id, version_id, _ = pendiente
    with closing(conectar(ruta_db)) as conexion:
        repo = RevisionAcademicaRepositorio(conexion)
        revision, = repo.listar_pendientes()
        assert revision["version_id"] == version_id
        with conexion:
            conexion.execute(
                """
                INSERT INTO versiones_apunte (aporte_id, numero, nombre_archivo, estado, fecha_creacion)
                VALUES (?, 2, 'nueva.pdf', 'PendienteRevision', '2026-11-18')
                """,
                (aporte_id,),
            )
        assert repo.obtener_contexto(aporte_id)["version_id"] != version_id
        with pytest.raises(ErrorRevision) as error:
            ServicioRevisiones(conexion).consultar(aporte_id, version_id)
        assert error.value.motivo is MotivoRevision.ESTADO_INCOMPATIBLE


@pytest.mark.parametrize(
    ("decision", "estado_version", "estado_aporte"),
    [
        ("Aprobacion", "Publicada", "Publicado"),
        ("Rechazo", "Rechazada", "Rechazado"),
        ("SolicitudCorreccion", "RequiereCorreccion", "CorreccionSolicitada"),
    ],
)
def test_decision_actualiza_version_y_aporte(ruta_db, pendiente, decision, estado_version, estado_aporte):
    with closing(conectar(ruta_db)) as conexion:
        servicio = ServicioRevisiones(conexion)
        with pytest.raises(DatosRevisionInvalidos) as invalidos:
            servicio.decidir(*pendiente, decision, " ", "")
        assert invalidos.value.errores.keys() == {"alcance", "observaciones"}
        assert conexion.execute("SELECT count(*) FROM revisiones_academicas").fetchone()[0] == 0
        assert conexion.execute("SELECT estado FROM versiones_apunte").fetchone()[0] == "PendienteRevision"

        servicio.decidir(*pendiente, decision, " Capítulo ", " Observaciones ")

        assert conexion.execute("SELECT estado FROM versiones_apunte").fetchone()[0] == estado_version
        assert conexion.execute("SELECT estado FROM aportes").fetchone()[0] == estado_aporte
        revision = conexion.execute("SELECT * FROM revisiones_academicas").fetchone()
        assert revision["version_id"] == pendiente[1]
        assert revision["revisor_id"] == pendiente[2]["id"]
        assert revision["comunidad_id"] == pendiente[2]["comunidad_id"]
        assert revision["decision"] == decision
        assert revision["alcance"] == "Capítulo"
        assert revision["observaciones"] == "Observaciones"


def test_fallo_en_el_cierre_revierte_decision_y_estados(ruta_db, pendiente):
    with closing(conectar(ruta_db)) as conexion:
        servicio = ServicioRevisiones(conexion)
        conexion.execute("""
            CREATE TEMP TRIGGER fallo_cierre BEFORE UPDATE ON aportes
            BEGIN
                SELECT RAISE(ABORT, 'fallo simulado');
            END
            """)
        with pytest.raises(sqlite3.IntegrityError, match="fallo simulado"):
            servicio.decidir(*pendiente, "Aprobacion", "Capítulo", "Observaciones")
        assert conexion.execute("SELECT count(*) FROM revisiones_academicas").fetchone()[0] == 0
        assert conexion.execute("SELECT estado FROM versiones_apunte").fetchone()[0] == "PendienteRevision"
        assert conexion.execute("SELECT estado FROM aportes").fetchone()[0] == "PendienteRevision"


def test_decisiones_simultaneas_conservan_un_solo_resultado(ruta_db, pendiente):
    inicio = Barrier(2, timeout=5)

    def decidir():
        with closing(conectar(ruta_db)) as conexion:
            inicio.wait()
            try:
                return ServicioRevisiones(conexion).decidir(
                    *pendiente, "Aprobacion", "Capítulo", "Observaciones"
                )
            except ErrorRevision as exc:
                return exc.motivo

    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        resultados = [ejecutor.submit(decidir), ejecutor.submit(decidir)]
        assert {resultado.result() for resultado in resultados} == {
            "Aprobacion", MotivoRevision.YA_RESUELTA,
        }
    with closing(conectar(ruta_db)) as conexion:
        assert conexion.execute("SELECT count(*) FROM revisiones_academicas").fetchone()[0] == 1
        assert conexion.execute("SELECT estado FROM versiones_apunte").fetchone()[0] == "Publicada"

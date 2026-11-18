from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import sqlite3
from threading import Barrier

import pytest

from app.db.conexion import conectar
from app.dominio.revisiones import RevisionAcademicaRepositorio
from app.servicios.aportes import ServicioAportes
from app.servicios.asignaciones import ServicioAsignaciones, TipoAsignacion
from app.servicios.revisiones import DatosRevisionInvalidos, ErrorRevision, MotivoRevision, ServicioRevisiones
from tests.conftest import archivo_pdf, datos_aporte


@pytest.fixture
def asignada(ruta_db, almacenamiento, catalogos):
    with closing(conectar(ruta_db)) as conexion:
        aporte_id = ServicioAportes(conexion, almacenamiento).enviar(
            datos_aporte(catalogos), archivo_pdf()
        ).aporte_id
        comunidad_id = conexion.execute(
            "SELECT comunidad_id FROM estudiantes WHERE rol = 'Moderador'"
        ).fetchone()[0]
        resultado = ServicioAsignaciones(conexion).asignar(aporte_id, comunidad_id)
        assert resultado.tipo is TipoAsignacion.ASIGNADO
        version_id = conexion.execute(
            "SELECT id FROM versiones_apunte WHERE aporte_id = ?", (aporte_id,)
        ).fetchone()[0]
    return aporte_id, version_id, comunidad_id


def test_consulta_filtra_por_comunidad_y_mantiene_revisor_de_la_ultima_version(ruta_db, asignada):
    aporte_id, version_id, comunidad_id = asignada
    with closing(conectar(ruta_db)) as conexion:
        repo = RevisionAcademicaRepositorio(conexion)
        assert repo.listar_asignadas(comunidad_id + 1) == []
        revision, = repo.listar_asignadas(comunidad_id)
        assert revision["version_id"] == version_id
        assert revision["revisor"] == "Revisor Demo 1"
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
            ServicioRevisiones(conexion).iniciar(*asignada)
        assert error.value.motivo is MotivoRevision.ESTADO_INCOMPATIBLE


@pytest.mark.parametrize(
    ("decision", "estado_version", "estado_aporte"),
    [
        ("Aprobacion", "Publicada", "Publicado"),
        ("Rechazo", "Rechazada", "Rechazado"),
        ("SolicitudCorreccion", "RequiereCorreccion", "CorreccionSolicitada"),
    ],
)
def test_decision_actualiza_version_aporte_y_asignacion(
    ruta_db, asignada, decision, estado_version, estado_aporte
):
    with closing(conectar(ruta_db)) as conexion:
        servicio = ServicioRevisiones(conexion)
        with pytest.raises(ErrorRevision) as error:
            servicio.decidir(*asignada, decision, "Capítulo", "Observaciones")
        assert error.value.motivo is MotivoRevision.ESTADO_INCOMPATIBLE
        servicio.iniciar(*asignada)
        with pytest.raises(DatosRevisionInvalidos) as invalidos:
            servicio.decidir(*asignada, decision, " ", "")
        assert invalidos.value.errores.keys() == {"alcance", "observaciones"}
        assert conexion.execute("SELECT count(*) FROM revisiones_academicas").fetchone()[0] == 0
        assert conexion.execute("SELECT estado FROM versiones_apunte").fetchone()[0] == "EnRevision"

        servicio.decidir(*asignada, decision, " Capítulo ", " Observaciones ")

        assert conexion.execute("SELECT estado FROM versiones_apunte").fetchone()[0] == estado_version
        assert conexion.execute("SELECT estado FROM aportes").fetchone()[0] == estado_aporte
        asignacion = conexion.execute("SELECT * FROM asignaciones_revision").fetchone()
        revision = conexion.execute("SELECT * FROM revisiones_academicas").fetchone()
        assert asignacion["estado"] == "Finalizada"
        assert revision["version_id"] == asignada[1]
        assert revision["revisor_id"] == asignacion["revisor_id"]
        assert revision["comunidad_id"] == asignada[2]
        assert revision["decision"] == decision
        assert revision["alcance"] == "Capítulo"
        assert revision["observaciones"] == "Observaciones"


def test_fallo_en_el_cierre_revierte_decision_y_estados(ruta_db, asignada):
    with closing(conectar(ruta_db)) as conexion:
        servicio = ServicioRevisiones(conexion)
        servicio.iniciar(*asignada)
        conexion.execute("""
            CREATE TEMP TRIGGER fallo_cierre BEFORE UPDATE ON asignaciones_revision
            BEGIN
                SELECT RAISE(ABORT, 'fallo simulado');
            END
            """)
        with pytest.raises(sqlite3.IntegrityError, match="fallo simulado"):
            servicio.decidir(*asignada, "Aprobacion", "Capítulo", "Observaciones")
        assert conexion.execute("SELECT count(*) FROM revisiones_academicas").fetchone()[0] == 0
        assert conexion.execute("SELECT estado FROM versiones_apunte").fetchone()[0] == "EnRevision"
        assert conexion.execute("SELECT estado FROM aportes").fetchone()[0] == "Asignado"
        assert conexion.execute("SELECT estado FROM asignaciones_revision").fetchone()[0] == "Asignada"


def test_decisiones_simultaneas_conservan_un_solo_resultado(ruta_db, asignada):
    with closing(conectar(ruta_db)) as conexion:
        ServicioRevisiones(conexion).iniciar(*asignada)
    inicio = Barrier(2, timeout=5)

    def decidir():
        with closing(conectar(ruta_db)) as conexion:
            inicio.wait()
            try:
                return ServicioRevisiones(conexion).decidir(
                    *asignada, "Aprobacion", "Capítulo", "Observaciones"
                )
            except ErrorRevision as exc:
                return exc.motivo

    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        resultados = [ejecutor.submit(decidir), ejecutor.submit(decidir)]
        assert {resultado.result() for resultado in resultados} == {
            "Aprobacion", MotivoRevision.ESTADO_INCOMPATIBLE,
        }
    with closing(conectar(ruta_db)) as conexion:
        assert conexion.execute("SELECT count(*) FROM revisiones_academicas").fetchone()[0] == 1
        assert conexion.execute("SELECT estado FROM versiones_apunte").fetchone()[0] == "Publicada"

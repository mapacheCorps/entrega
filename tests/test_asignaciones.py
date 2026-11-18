from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import sqlite3
from threading import Barrier

import pytest

from app.db.conexion import conectar
from app.dominio.repositorios import AsignacionRevisionRepositorio
from app.servicios.aportes import ServicioAportes
from app.servicios.asignaciones import ServicioAsignaciones, TipoAsignacion
from tests.conftest import archivo_pdf, datos_aporte


def _comunidad(conexion):
    return conexion.execute(
        "SELECT comunidad_id FROM estudiantes WHERE rol = 'Moderador'"
    ).fetchone()[0]


def _crear_aporte(conexion, almacenamiento, catalogos, contenido=b"%PDF HU-02"):
    resultado = ServicioAportes(conexion, almacenamiento).enviar(
        datos_aporte(catalogos), archivo_pdf(contenido)
    )
    assert resultado.aporte_id is not None
    return resultado.aporte_id


def test_elegir_revisor_prioriza_carga_activa_y_desempata_por_identificador(
    ruta_db, almacenamiento, catalogos
):
    with closing(conectar(ruta_db)) as conexion:
        aporte_id = _crear_aporte(conexion, almacenamiento, catalogos)
        comunidad_id = _comunidad(conexion)
        ramo_id = catalogos["ramo_id"]
        autor_id = conexion.execute(
            "SELECT autor_id FROM aportes WHERE id = ?", (aporte_id,)
        ).fetchone()[0]
        repo = AsignacionRevisionRepositorio(conexion)
        candidatos = conexion.execute(
            "SELECT id FROM estudiantes WHERE rol IS NULL ORDER BY id"
        ).fetchall()
        primero, segundo = (fila["id"] for fila in candidatos)

        assert repo.elegir_revisor(comunidad_id, ramo_id, autor_id)["id"] == primero
        with conexion:
            repo.registrar(aporte_id, primero, comunidad_id, "2026-11-18T12:00:00+00:00")
        assert repo.elegir_revisor(comunidad_id, ramo_id, autor_id)["id"] == segundo
        with conexion:
            conexion.execute("UPDATE asignaciones_revision SET estado = 'Finalizada'")
        assert repo.elegir_revisor(comunidad_id, ramo_id, autor_id)["id"] == primero


def test_elegir_revisor_excluye_autor_otra_comunidad_no_disponible_y_no_habilitado(
    ruta_db, catalogos
):
    with closing(conectar(ruta_db)) as conexion:
        comunidad_id = _comunidad(conexion)
        ramo_id = catalogos["ramo_id"]
        autor_id = conexion.execute(
            "SELECT id FROM estudiantes WHERE rol = 'Estudiante'"
        ).fetchone()[0]
        with conexion:
            otra_comunidad = conexion.execute(
                "INSERT INTO comunidades_estudiantiles (nombre) VALUES ('Otra comunidad')"
            ).lastrowid
            conexion.execute(
                "UPDATE estudiantes SET comunidad_id = ?, disponible = 1 WHERE id = ?",
                (comunidad_id, autor_id),
            )
            conexion.execute(
                "UPDATE estudiantes SET comunidad_id = ? WHERE correo = 'revisor1@demo.cl'",
                (otra_comunidad,),
            )
            conexion.execute(
                "UPDATE estudiantes SET disponible = 0 WHERE correo = 'revisor2@demo.cl'"
            )
            conexion.execute(
                """
                INSERT INTO estudiantes (nombre, correo, comunidad_id, disponible)
                VALUES ('Sin habilitación', 'sin-habilitacion@demo.cl', ?, 1)
                """,
                (comunidad_id,),
            )
            conexion.execute(
                "INSERT INTO estudiantes_ramos_habilitados VALUES (?, ?)",
                (autor_id, ramo_id),
            )
        assert AsignacionRevisionRepositorio(conexion).elegir_revisor(
            comunidad_id, ramo_id, autor_id
        ) is None


def test_solicitar_asignacion_dos_veces_concurrentemente_conserva_un_responsable(
    ruta_db, almacenamiento, catalogos
):
    with closing(conectar(ruta_db)) as conexion:
        aporte_id = _crear_aporte(conexion, almacenamiento, catalogos)
        comunidad_id = _comunidad(conexion)

    inicio = Barrier(2, timeout=5)

    def asignar():
        with closing(conectar(ruta_db)) as conexion:
            inicio.wait()
            return ServicioAsignaciones(conexion).asignar(aporte_id, comunidad_id)

    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        primero = ejecutor.submit(asignar)
        segundo = ejecutor.submit(asignar)
        resultados = [primero.result(), segundo.result()]

    assert {resultado.tipo for resultado in resultados} == {
        TipoAsignacion.ASIGNADO, TipoAsignacion.YA_ASIGNADO
    }
    assert resultados[0].asignacion["id"] == resultados[1].asignacion["id"]
    with closing(conectar(ruta_db)) as conexion:
        assert conexion.execute("SELECT count(*) FROM asignaciones_revision").fetchone()[0] == 1


def test_asignacion_revierte_el_registro_si_falla_el_cambio_de_estado(
    ruta_db, almacenamiento, catalogos
):
    with closing(conectar(ruta_db)) as conexion:
        aporte_id = _crear_aporte(conexion, almacenamiento, catalogos)
        comunidad_id = _comunidad(conexion)
        conexion.execute(
            """
            CREATE TEMP TRIGGER fallo_actualizacion BEFORE UPDATE ON aportes
            WHEN NEW.estado = 'Asignado'
            BEGIN
                SELECT RAISE(ABORT, 'fallo simulado');
            END
            """
        )
        with pytest.raises(sqlite3.IntegrityError, match="fallo simulado"):
            ServicioAsignaciones(conexion).asignar(aporte_id, comunidad_id)
        assert AsignacionRevisionRepositorio(conexion).buscar_vigente(aporte_id) is None
        assert conexion.execute(
            "SELECT estado FROM aportes WHERE id = ?", (aporte_id,)
        ).fetchone()[0] == "PendienteAsignacion"

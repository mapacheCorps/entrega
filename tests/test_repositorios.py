from __future__ import annotations

import sqlite3

import pytest

from app.db.conexion import conectar
from app.dominio.repositorios import AporteRepositorio, CatalogoRepositorio


@pytest.fixture
def conexion(ruta_db):
    conexion = conectar(ruta_db)
    yield conexion
    conexion.close()


def test_catalogos_sembrados(conexion):
    repo = CatalogoRepositorio(conexion)
    assert len(repo.listar_carreras()) == 3
    assert len(repo.listar_ramos()) == 5
    assert len(repo.listar_periodos()) == 2
    assert len(repo.listar_temas()) == 8
    assert repo.obtener_estudiante_por_rol("Estudiante")["nombre"] == "Estudiante Demo"
    assert repo.obtener_estudiante_por_rol("Moderador")["nombre"] == "Comunidad Estudiantil"
    assert repo.obtener_estudiante_por_rol("Ayudante") is None
    assert repo.obtener_estudiante_por_rol("Coordinador") is None


def test_crear_aporte_con_version_y_consultar_detalle(conexion, catalogos):
    repo = AporteRepositorio(conexion)
    aporte_id = repo.crear_aporte_con_version(
        aporte_id=repo.siguiente_id("aportes"),
        autor_id=1,
        ramo_id=catalogos["ramo_id"],
        periodo_id=catalogos["periodo_id"],
        tema_id=catalogos["tema_id"],
        procedencia="Apuntes de clase",
        fecha_envio="2026-11-05T10:00:00",
        estado_aporte="PendienteAsignacion",
        version_id=repo.siguiente_id("versiones_apunte"),
        nombre_archivo="apunte.pdf",
        referencia_archivo="1/1_apunte.pdf",
        hash_archivo="hash-apunte",
        tamano_bytes=100,
        tipo_mime="application/pdf",
        estado_version="PendienteRevision",
        fecha_creacion="2026-11-05T10:00:00",
    )

    detalle = repo.obtener_detalle(aporte_id)
    assert detalle["estado_aporte"] == "PendienteAsignacion"
    assert detalle["estado_version"] == "PendienteRevision"
    assert detalle["numero"] == 1
    assert detalle["hash_archivo"] == "hash-apunte"
    assert repo.buscar_version_por_hash("hash-apunte")["aporte_id"] == aporte_id
    assert repo.contar_aportes() == 1


def test_creacion_de_aporte_es_transaccional(conexion, catalogos):
    repo = AporteRepositorio(conexion)
    with pytest.raises(sqlite3.IntegrityError):
        repo.crear_aporte_con_version(
            aporte_id=repo.siguiente_id("aportes"),
            autor_id=1,
            ramo_id=catalogos["ramo_id"],
            periodo_id=catalogos["periodo_id"],
            tema_id=catalogos["tema_id"],
            procedencia="Apuntes de clase",
            fecha_envio="2026-11-05T10:00:00",
            estado_aporte="PendienteAsignacion",
            version_id=repo.siguiente_id("versiones_apunte"),
            nombre_archivo="apunte.pdf",
            referencia_archivo="1/1_apunte.pdf",
            hash_archivo="hash-apunte",
            tamano_bytes=100,
            tipo_mime="application/pdf",
            estado_version="EstadoInvalido",
            fecha_creacion="2026-11-05T10:00:00",
        )

    assert repo.contar_aportes() == 0
    assert conexion.execute("SELECT COUNT(*) FROM versiones_apunte").fetchone()[0] == 0


def test_correccion_es_transaccional(conexion, catalogos):
    repo = AporteRepositorio(conexion)
    aporte_id = repo.crear_aporte_con_version(
        aporte_id=repo.siguiente_id("aportes"),
        autor_id=1,
        ramo_id=catalogos["ramo_id"],
        periodo_id=catalogos["periodo_id"],
        tema_id=catalogos["tema_id"],
        procedencia="Apuntes de clase",
        fecha_envio="2026-11-05T10:00:00",
        estado_aporte="RequiereCorreccion",
        version_id=repo.siguiente_id("versiones_apunte"),
        nombre_archivo="apunte.invalido",
        referencia_archivo=None,
        hash_archivo=None,
        tamano_bytes=0,
        tipo_mime="application/octet-stream",
        estado_version="RequiereCorreccion",
        fecha_creacion="2026-11-05T10:00:00",
    )
    version_anterior = repo.obtener_ultima_version(aporte_id)

    with pytest.raises(sqlite3.IntegrityError):
        repo.crear_version_corregida(
            aporte_id=aporte_id,
            version_anterior_id=version_anterior["id"],
            nueva_version_id=repo.siguiente_id("versiones_apunte"),
            numero=2,
            nombre_archivo="apunte.pdf",
            referencia_archivo="1/2_apunte.pdf",
            hash_archivo="hash-corregido",
            tamano_bytes=100,
            tipo_mime="application/pdf",
            estado_version="EstadoInvalido",
            estado_aporte="PendienteAsignacion",
            fecha_creacion="2026-11-05T10:05:00",
        )

    assert repo.obtener_ultima_version(aporte_id)["estado"] == "RequiereCorreccion"
    assert repo.obtener_aporte(aporte_id)["estado"] == "RequiereCorreccion"

    repo.crear_version_corregida(
        aporte_id=aporte_id,
        version_anterior_id=version_anterior["id"],
        nueva_version_id=repo.siguiente_id("versiones_apunte"),
        numero=2,
        nombre_archivo="apunte.pdf",
        referencia_archivo="1/2_apunte.pdf",
        hash_archivo="hash-corregido",
        tamano_bytes=100,
        tipo_mime="application/pdf",
        estado_version="PendienteRevision",
        estado_aporte="PendienteAsignacion",
        fecha_creacion="2026-11-05T10:05:00",
    )

    versiones = conexion.execute(
        "SELECT numero, estado FROM versiones_apunte WHERE aporte_id = ? ORDER BY numero",
        (aporte_id,),
    ).fetchall()
    assert [(fila["numero"], fila["estado"]) for fila in versiones] == [
        (1, "Final"),
        (2, "PendienteRevision"),
    ]
    assert repo.obtener_aporte(aporte_id)["estado"] == "PendienteAsignacion"

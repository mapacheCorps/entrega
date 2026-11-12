from __future__ import annotations

import sqlite3

import pytest

from app.db.conexion import aplicar_migraciones, conectar
from app.db.seed import sembrar


def test_migracion_se_aplica_una_sola_vez(tmp_path):
    ruta = tmp_path / "app.db"
    conexion = conectar(ruta)
    try:
        primeras = aplicar_migraciones(conexion)
        segundas = aplicar_migraciones(conexion)
        filas = conexion.execute("SELECT version FROM schema_migrations").fetchall()
    finally:
        conexion.close()

    assert primeras == ["001_inicial.sql"]
    assert segundas == []
    assert [fila["version"] for fila in filas] == ["001_inicial.sql"]


def _insertar_aporte(conexion, catalogos, aporte_id: int) -> None:
    conexion.execute(
        """
        INSERT INTO aportes
            (id, autor_id, ramo_id, periodo_id, tema_id, procedencia, fecha_envio, estado)
        VALUES (?, 1, ?, ?, ?, 'Procedencia de prueba', '2026-11-05T10:00:00', 'PendienteAsignacion')
        """,
        (
            aporte_id,
            catalogos["ramo_id"],
            catalogos["periodo_id"],
            catalogos["tema_id"],
        ),
    )
    conexion.commit()


def _insertar_version(
    conexion,
    *,
    version_id: int,
    aporte_id: int,
    numero: int,
    hash_archivo: str | None = None,
) -> None:
    referencia = f"archivo-{version_id}" if hash_archivo else None
    conexion.execute(
        """
        INSERT INTO versiones_apunte
            (id, aporte_id, numero, nombre_archivo, referencia_archivo, hash_archivo,
             tamano_bytes, tipo_mime, estado, fecha_creacion)
        VALUES (?, ?, ?, 'apunte.pdf', ?, ?, 10, 'application/pdf', 'PendienteRevision',
                '2026-11-05T10:00:00')
        """,
        (version_id, aporte_id, numero, referencia, hash_archivo),
    )
    conexion.commit()


@pytest.fixture
def db_sembrada(tmp_path):
    ruta = tmp_path / "app.db"
    conexion = conectar(ruta)
    aplicar_migraciones(conexion)
    sembrar(conexion)
    from tests.conftest import obtener_catalogos

    catalogos = obtener_catalogos(ruta)
    yield conexion, catalogos
    conexion.close()


def test_aporte_sin_ramo_es_rechazado(db_sembrada):
    conexion, catalogos = db_sembrada
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            """
            INSERT INTO aportes
                (autor_id, ramo_id, periodo_id, tema_id, procedencia, fecha_envio, estado)
            VALUES (1, NULL, ?, ?, 'Procedencia', '2026-11-05T10:00:00', 'PendienteAsignacion')
            """,
            (catalogos["periodo_id"], catalogos["tema_id"]),
        )
    conexion.rollback()


def test_version_con_numero_repetido_es_rechazada(db_sembrada):
    conexion, catalogos = db_sembrada
    _insertar_aporte(conexion, catalogos, aporte_id=100)
    _insertar_version(
        conexion, version_id=100, aporte_id=100, numero=1, hash_archivo="hash-1"
    )
    with pytest.raises(sqlite3.IntegrityError):
        _insertar_version(
            conexion, version_id=101, aporte_id=100, numero=1, hash_archivo="hash-2"
        )


def test_hash_duplicado_es_rechazado(db_sembrada):
    conexion, catalogos = db_sembrada
    _insertar_aporte(conexion, catalogos, aporte_id=100)
    _insertar_aporte(conexion, catalogos, aporte_id=101)
    _insertar_version(
        conexion, version_id=100, aporte_id=100, numero=1, hash_archivo="hash-repetido"
    )
    with pytest.raises(sqlite3.IntegrityError):
        _insertar_version(
            conexion,
            version_id=101,
            aporte_id=101,
            numero=1,
            hash_archivo="hash-repetido",
        )

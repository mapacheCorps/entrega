from __future__ import annotations

import sqlite3

import pytest

from app.db.conexion import MIGRACIONES_DIR, aplicar_migraciones, conectar
from app.db.seed import sembrar


def test_migracion_se_aplica_una_sola_vez(tmp_path):
    ruta = tmp_path / "app.db"
    conexion = conectar(ruta)
    try:
        primeras = aplicar_migraciones(conexion)
        segundas = aplicar_migraciones(conexion)
        filas = conexion.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
    finally:
        conexion.close()

    assert primeras == [
        "001_inicial.sql", "002_asignacion_revision.sql", "003_revision_comunitaria.sql", "004_revision_directa.sql"
    ]
    assert segundas == []
    assert [fila["version"] for fila in filas] == primeras


def _insertar_aporte(conexion, catalogos, aporte_id: int, estado="PendienteRevision") -> None:
    conexion.execute(
        """
        INSERT INTO aportes
            (id, autor_id, ramo_id, periodo_id, tema_id, procedencia, fecha_envio, estado)
        VALUES (?, 1, ?, ?, ?, 'Procedencia de prueba', '2026-11-05T10:00:00', ?)
        """,
        (
            aporte_id,
            catalogos["ramo_id"],
            catalogos["periodo_id"],
            catalogos["tema_id"],
            estado,
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


def test_migracion_hu02_conserva_un_aporte_corregido_y_su_historial(tmp_path):
    ruta = tmp_path / "app.db"
    migraciones_hu01 = tmp_path / "hu01"
    migraciones_hu01.mkdir()
    inicial = "001_inicial.sql"
    (migraciones_hu01 / inicial).write_bytes((MIGRACIONES_DIR / inicial).read_bytes())
    conexion = conectar(ruta)
    try:
        aplicar_migraciones(conexion, migraciones_hu01)
        with conexion:
            conexion.executescript("""
                INSERT INTO estudiantes VALUES (1, 'Autor', 'autor@demo.cl', 'Estudiante');
                INSERT INTO carreras VALUES (1, 'ICI', 'Informática');
                INSERT INTO ramos VALUES (1, 'REQ', 'Requisitos', 1);
                INSERT INTO periodos_academicos VALUES (1, 2026, 1);
                INSERT INTO temas_unidad VALUES (1, 1, 1, 'Elicitación');
                """)
        catalogos = {"ramo_id": 1, "periodo_id": 1, "tema_id": 1}
        _insertar_aporte(conexion, catalogos, aporte_id=42, estado="PendienteAsignacion")
        _insertar_version(conexion, version_id=10, aporte_id=42, numero=1)
        _insertar_version(
            conexion, version_id=11, aporte_id=42, numero=2, hash_archivo="corregido"
        )
        with conexion:
            conexion.execute("UPDATE versiones_apunte SET estado = 'Final' WHERE id = 10")

        assert aplicar_migraciones(conexion) == [
            "002_asignacion_revision.sql", "003_revision_comunitaria.sql", "004_revision_directa.sql"
        ]
        assert conexion.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert conexion.execute("PRAGMA foreign_key_check").fetchall() == []
        aporte = conexion.execute("SELECT id, autor_id, estado FROM aportes").fetchone()
        assert tuple(aporte) == (42, 1, "PendienteRevision")
        versiones = conexion.execute(
            "SELECT id, numero, estado, hash_archivo FROM versiones_apunte ORDER BY numero"
        ).fetchall()
        assert list(map(tuple, versiones)) == [
            (10, 1, "Final", None),
            (11, 2, "PendienteRevision", "corregido"),
        ]
    finally:
        conexion.close()


def test_revision_directa_migra_un_aporte_asignado_y_conserva_su_historial(tmp_path):
    migraciones_hu03 = tmp_path / "hu03"
    migraciones_hu03.mkdir()
    for nombre in ("001_inicial.sql", "002_asignacion_revision.sql", "003_revision_comunitaria.sql"):
        (migraciones_hu03 / nombre).write_bytes((MIGRACIONES_DIR / nombre).read_bytes())

    conexion = conectar(tmp_path / "app.db")
    try:
        aplicar_migraciones(conexion, migraciones_hu03)
        sembrar(conexion)
        from tests.conftest import obtener_catalogos

        catalogos = obtener_catalogos(tmp_path / "app.db")
        _insertar_aporte(conexion, catalogos, aporte_id=42, estado="PendienteAsignacion")
        _insertar_version(
            conexion, version_id=11, aporte_id=42, numero=1, hash_archivo="vigente"
        )
        with conexion:
            conexion.execute("UPDATE aportes SET estado = 'Asignado' WHERE id = 42")
            conexion.execute("UPDATE versiones_apunte SET estado = 'EnRevision' WHERE id = 11")
            conexion.execute("""
                INSERT INTO asignaciones_revision (aporte_id, revisor_id, comunidad_id, fecha_asignacion, estado)
                SELECT 42, id, comunidad_id, '2026-11-18', 'Asignada'
                FROM estudiantes WHERE correo = 'revisor1@demo.cl'
                """)
        asignacion = conexion.execute("SELECT * FROM asignaciones_revision").fetchone()
        assert aplicar_migraciones(conexion) == ["004_revision_directa.sql"]
        assert conexion.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conexion.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert conexion.execute("SELECT * FROM asignaciones_revision").fetchone() == asignacion
        assert conexion.execute("SELECT estado FROM aportes WHERE id = 42").fetchone()[0] == "PendienteRevision"
        assert tuple(conexion.execute(
            "SELECT id, aporte_id, hash_archivo, estado FROM versiones_apunte"
        ).fetchone()) == (11, 42, "vigente", "PendienteRevision")
        indices = {fila["name"] for fila in conexion.execute("PRAGMA index_list('versiones_apunte')")}
        assert {"idx_versiones_hash_unico", "idx_versiones_aporte"} <= indices
        with conexion:
            conexion.execute("UPDATE versiones_apunte SET estado = 'EnRevision' WHERE id = 11")
            conexion.execute("UPDATE aportes SET estado = 'CorreccionSolicitada' WHERE id = 42")
    finally:
        conexion.close()


def test_migracion_fallida_revierte_los_cambios_y_restaura_claves_foraneas(tmp_path):
    migraciones = tmp_path / "migrations"
    migraciones.mkdir()
    (migraciones / "001_prueba.sql").write_text(
        "CREATE TABLE padre (id INTEGER PRIMARY KEY);\n"
        "CREATE TABLE hijo (padre_id INTEGER REFERENCES padre(id));\n"
        "INSERT INTO hijo VALUES (1);", encoding="utf-8"
    )
    conexion = conectar(tmp_path / "app.db")
    try:
        with pytest.raises(sqlite3.IntegrityError, match="clave foránea inválida en hijo"):
            aplicar_migraciones(conexion, migraciones)
        assert conexion.execute("SELECT version FROM schema_migrations").fetchall() == []
        assert conexion.execute("SELECT name FROM sqlite_master WHERE name = 'padre'").fetchone() is None
        assert conexion.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        conexion.close()


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


def test_seed_conserva_perfiles_y_revisores_al_repetirlo(db_sembrada):
    conexion, catalogos = db_sembrada
    antes = conexion.execute("SELECT * FROM estudiantes ORDER BY id").fetchall()
    sembrar(conexion)
    despues = conexion.execute("SELECT * FROM estudiantes ORDER BY id").fetchall()
    assert despues == antes
    perfiles = {fila["rol"]: fila for fila in despues if fila["rol"]}
    assert set(perfiles) == {"Estudiante", "Moderador"}
    comunidad = perfiles["Moderador"]["comunidad_id"]
    ramos_habilitados = conexion.execute(
        """
        SELECT h.ramo_id FROM estudiantes_ramos_habilitados h
        JOIN estudiantes e ON e.id = h.estudiante_id
        WHERE e.comunidad_id = ? AND e.disponible = 1
        """,
        (comunidad,),
    ).fetchall()
    assert [fila[0] for fila in ramos_habilitados].count(catalogos["ramo_id"]) == 2
    assert catalogos["otro_ramo_id"] not in {fila[0] for fila in ramos_habilitados}
    assert conexion.execute("SELECT count(*) FROM comunidades_estudiantiles").fetchone()[0] == 1


def test_aporte_sin_ramo_es_rechazado(db_sembrada):
    conexion, catalogos = db_sembrada
    with pytest.raises(sqlite3.IntegrityError):
        conexion.execute(
            """
            INSERT INTO aportes
                (autor_id, ramo_id, periodo_id, tema_id, procedencia, fecha_envio, estado)
            VALUES (1, NULL, ?, ?, 'Procedencia', '2026-11-05T10:00:00', 'PendienteRevision')
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

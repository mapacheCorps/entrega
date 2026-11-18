"""Conexión a SQLite y aplicación de migraciones."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from fastapi import Request

BASE_DIR = Path(__file__).resolve().parents[2]
MIGRACIONES_DIR = Path(__file__).resolve().parent / "migrations"
RUTA_DB_POR_DEFECTO = BASE_DIR / "data" / "app.db"


def ruta_db_por_defecto() -> Path:
    """Ruta de la base, configurable con APP_DB_PATH (útil en pruebas)."""
    return Path(os.environ.get("APP_DB_PATH", RUTA_DB_POR_DEFECTO))


def conectar(ruta: str | Path | None = None) -> sqlite3.Connection:
    destino = Path(ruta) if ruta is not None else ruta_db_por_defecto()
    destino.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(destino, check_same_thread=False)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def aplicar_migraciones(
    conexion: sqlite3.Connection, directorio: Path | None = None
) -> list[str]:
    """Aplica las migraciones pendientes y devuelve sus nombres."""
    directorio = directorio or MIGRACIONES_DIR
    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            aplicada_en TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conexion.commit()

    nuevas: list[str] = []

    claves_foraneas = conexion.execute("PRAGMA foreign_keys").fetchone()[0]
    # La reconstrucción de tablas padre debe conservar sus filas dependientes.
    conexion.execute("PRAGMA foreign_keys = OFF")
    try:
        for archivo in sorted(directorio.glob("*.sql")):
            with conexion:
                conexion.execute("BEGIN IMMEDIATE")
                aplicada = conexion.execute(
                    "SELECT 1 FROM schema_migrations WHERE version = ?", (archivo.name,)
                ).fetchone()
                if aplicada:
                    continue

                _ejecutar_sql_migracion(conexion, archivo.read_text(encoding="utf-8"))
                violacion = conexion.execute("PRAGMA foreign_key_check").fetchone()
                if violacion:
                    raise sqlite3.IntegrityError(
                        f"{archivo.name}: clave foránea inválida en {violacion[0]}"
                    )
                conexion.execute(
                    "INSERT INTO schema_migrations (version) VALUES (?)", (archivo.name,)
                )
            nuevas.append(archivo.name)
    finally:
        if claves_foraneas:
            conexion.execute("PRAGMA foreign_keys = ON")

    return nuevas


def _ejecutar_sql_migracion(conexion: sqlite3.Connection, sql: str) -> None:
    """Ejecuta el script sin el commit implícito de executescript."""
    inicio = 0
    for indice, caracter in enumerate(sql):
        if caracter == ";" and sqlite3.complete_statement(sql[inicio : indice + 1]):
            conexion.execute(sql[inicio : indice + 1])
            inicio = indice + 1
    if sql[inicio:].strip():
        conexion.execute(sql[inicio:])


def obtener_conexion(request: Request):
    """Dependencia de FastAPI: una conexión por solicitud."""
    conexion = conectar(request.app.state.db_path)
    try:
        yield conexion
    finally:
        conexion.close()

"""Datos de ejemplo idempotentes para la aplicación."""

from __future__ import annotations

import sqlite3

from app.db.conexion import aplicar_migraciones, conectar, ruta_db_por_defecto

CARRERAS = [
    ("ICI", "Ingeniería Civil Informática"),
    ("ICO", "Ingeniería Comercial"),
    ("DER", "Derecho"),
]

RAMOS = [
    ("ICI", "CAL1", "Cálculo I"),
    ("ICI", "EDD", "Estructuras de Datos"),
    ("ICI", "REQ", "Ingeniería de Requisitos"),
    ("ICO", "MIC", "Microeconomía"),
    ("DER", "DCIV", "Derecho Civil"),
]

PERIODOS = [(2025, 2), (2026, 1)]

TEMAS = {
    ("ICI", "CAL1"): [(1, "Límites y continuidad"), (2, "Derivadas")],
    ("ICI", "EDD"): [(1, "Listas enlazadas"), (2, "Árboles")],
    ("ICI", "REQ"): [(1, "Elicitación de requisitos"), (2, "Especificación")],
    ("ICO", "MIC"): [(1, "Oferta y demanda")],
    ("DER", "DCIV"): [(1, "Obligaciones civiles")],
}

PERFILES = [
    ("Estudiante Demo", "estudiante@demo.cl", "Estudiante"),
    ("Comunidad Estudiantil", "comunidad@demo.cl", "Moderador"),
]


def sembrar(conexion: sqlite3.Connection) -> None:
    """Inserta catálogos y perfiles sin duplicar filas si se ejecuta otra vez."""
    with conexion:
        for codigo, nombre in CARRERAS:
            conexion.execute(
                """
                INSERT INTO carreras (codigo, nombre) VALUES (?, ?)
                ON CONFLICT(codigo) DO UPDATE SET nombre = excluded.nombre
                """,
                (codigo, nombre),
            )

        for carrera_codigo, codigo, nombre in RAMOS:
            carrera = conexion.execute(
                "SELECT id FROM carreras WHERE codigo = ?", (carrera_codigo,)
            ).fetchone()
            if carrera is None:
                raise RuntimeError(f"Falta la carrera {carrera_codigo}")
            conexion.execute(
                """
                INSERT INTO ramos (codigo, nombre, carrera_id) VALUES (?, ?, ?)
                ON CONFLICT(carrera_id, codigo) DO UPDATE SET nombre = excluded.nombre
                """,
                (codigo, nombre, carrera["id"]),
            )

        for anio, semestre in PERIODOS:
            conexion.execute(
                """
                INSERT INTO periodos_academicos (anio, semestre) VALUES (?, ?)
                ON CONFLICT(anio, semestre) DO NOTHING
                """,
                (anio, semestre),
            )

        for (carrera_codigo, ramo_codigo), temas in TEMAS.items():
            ramo = conexion.execute(
                """
                SELECT r.id FROM ramos r
                JOIN carreras c ON c.id = r.carrera_id
                WHERE c.codigo = ? AND r.codigo = ?
                """,
                (carrera_codigo, ramo_codigo),
            ).fetchone()
            if ramo is None:
                raise RuntimeError(f"Falta el ramo {carrera_codigo}/{ramo_codigo}")
            for numero, nombre in temas:
                conexion.execute(
                    """
                    INSERT INTO temas_unidad (ramo_id, numero, nombre) VALUES (?, ?, ?)
                    ON CONFLICT(ramo_id, numero) DO UPDATE SET nombre = excluded.nombre
                    """,
                    (ramo["id"], numero, nombre),
                )

        # Limpia perfiles de versiones anteriores que ya no se usan y que no
        # tengan aportes asociados. Así el seed sigue siendo idempotente.
        conexion.execute(
            """
            DELETE FROM estudiantes
            WHERE rol NOT IN ('Estudiante', 'Moderador')
              AND id NOT IN (SELECT autor_id FROM aportes)
            """
        )

        for nombre, correo, rol in PERFILES:
            conexion.execute(
                """
                INSERT INTO estudiantes (nombre, correo, rol) VALUES (?, ?, ?)
                ON CONFLICT(correo) DO UPDATE
                    SET nombre = excluded.nombre, rol = excluded.rol
                """,
                (nombre, correo, rol),
            )


def main() -> None:
    ruta = ruta_db_por_defecto()
    conexion = conectar(ruta)
    try:
        nuevas = aplicar_migraciones(conexion)
        sembrar(conexion)
        totales = {
            tabla: conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
            for tabla in (
                "carreras",
                "ramos",
                "periodos_academicos",
                "temas_unidad",
                "estudiantes",
            )
        }
    finally:
        conexion.close()

    print(f"Base de datos: {ruta}")
    print(f"Migraciones aplicadas: {', '.join(nuevas) if nuevas else 'ninguna'}")
    print("Datos de ejemplo:")
    for tabla, total in totales.items():
        print(f"  {tabla}: {total}")


if __name__ == "__main__":
    main()

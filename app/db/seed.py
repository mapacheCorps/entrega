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

COMUNIDAD_DEMO = "Comunidad Estudiantil"
REVISORES = [
    ("Revisor Demo 1", "revisor1@demo.cl", ("REQ", "EDD")),
    ("Revisor Demo 2", "revisor2@demo.cl", ("REQ",)),
]

EXPERTOS = [
    ("Dr. Juan Pérez", "juan.perez@experto.cl", "Física Cuántica"),
    ("Dra. María González", "maria.gonzalez@experto.cl", "Cálculo Avanzado"),
    ("Dr. Carlos Rodríguez", "carlos.rodriguez@experto.cl", "Estructuras de Datos"),
]


def sembrar(conexion: sqlite3.Connection) -> None:
    """Inserta catálogos, perfiles y revisores sin duplicarlos."""
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

        conexion.execute(
            "INSERT INTO comunidades_estudiantiles (nombre) VALUES (?) "
            "ON CONFLICT(nombre) DO NOTHING",
            (COMUNIDAD_DEMO,),
        )
        comunidad_id = conexion.execute(
            "SELECT id FROM comunidades_estudiantiles WHERE nombre = ?",
            (COMUNIDAD_DEMO,),
        ).fetchone()["id"]

        for nombre, correo, rol in PERFILES:
            conexion.execute(
                """
                INSERT INTO estudiantes (nombre, correo, rol, comunidad_id)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(correo) DO UPDATE
                    SET nombre = excluded.nombre, rol = excluded.rol,
                        comunidad_id = COALESCE(excluded.comunidad_id, estudiantes.comunidad_id)
                """,
                (nombre, correo, rol, comunidad_id if rol == "Moderador" else None),
            )

        for nombre, correo, codigos_ramo in REVISORES:
            conexion.execute(
                """
                INSERT INTO estudiantes (nombre, correo, comunidad_id, disponible)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(correo) DO UPDATE
                    SET nombre = excluded.nombre, comunidad_id = excluded.comunidad_id
                """,
                (nombre, correo, comunidad_id),
            )
            for codigo_ramo in codigos_ramo:
                conexion.execute(
                    """
                    INSERT INTO estudiantes_ramos_habilitados (estudiante_id, ramo_id)
                    SELECT e.id, r.id FROM estudiantes e
                    JOIN ramos r ON r.codigo = ?
                    JOIN carreras c ON c.id = r.carrera_id AND c.codigo = 'ICI'
                    WHERE e.correo = ?
                    ON CONFLICT(estudiante_id, ramo_id) DO NOTHING
                    """,
                    (codigo_ramo, correo),
                )

        for nombre, correo, especialidad in EXPERTOS:
            conexion.execute(
                """
                INSERT INTO expertos (nombre, correo, especialidad)
                VALUES (?, ?, ?)
                ON CONFLICT(correo) DO UPDATE
                    SET nombre = excluded.nombre, especialidad = excluded.especialidad
                """,
                (nombre, correo, especialidad),
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
                "comunidades_estudiantiles",
                "estudiantes_ramos_habilitados",
                "expertos",
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

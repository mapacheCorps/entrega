"""Repositorios SQLite para aportes, versiones y catálogos."""

from __future__ import annotations

import sqlite3
from contextlib import nullcontext
from typing import Any

TABLAS_CON_ID = {"aportes", "versiones_apunte"}


class CatalogoRepositorio:
    def __init__(self, conexion: sqlite3.Connection):
        self.conexion = conexion

    def listar_carreras(self) -> list[sqlite3.Row]:
        return list(
            self.conexion.execute(
                "SELECT id, codigo, nombre FROM carreras ORDER BY nombre"
            )
        )

    def listar_ramos(self) -> list[sqlite3.Row]:
        return list(
            self.conexion.execute(
                """
                SELECT r.id, r.codigo, r.nombre, r.carrera_id, c.nombre AS carrera_nombre
                FROM ramos r
                JOIN carreras c ON c.id = r.carrera_id
                ORDER BY c.nombre, r.nombre
                """
            )
        )

    def listar_periodos(self) -> list[sqlite3.Row]:
        return list(
            self.conexion.execute(
                """
                SELECT id, anio, semestre
                FROM periodos_academicos
                ORDER BY anio DESC, semestre DESC
                """
            )
        )

    def listar_temas(self) -> list[sqlite3.Row]:
        return list(
            self.conexion.execute(
                """
                SELECT t.id, t.numero, t.nombre, t.ramo_id, r.nombre AS ramo_nombre
                FROM temas_unidad t
                JOIN ramos r ON r.id = t.ramo_id
                ORDER BY r.nombre, t.numero
                """
            )
        )

    def obtener_carrera(self, carrera_id: int) -> sqlite3.Row | None:
        return self.conexion.execute(
            "SELECT id, codigo, nombre FROM carreras WHERE id = ?", (carrera_id,)
        ).fetchone()

    def obtener_ramo(self, ramo_id: int) -> sqlite3.Row | None:
        return self.conexion.execute(
            "SELECT id, codigo, nombre, carrera_id FROM ramos WHERE id = ?", (ramo_id,)
        ).fetchone()

    def obtener_periodo(self, periodo_id: int) -> sqlite3.Row | None:
        return self.conexion.execute(
            "SELECT id, anio, semestre FROM periodos_academicos WHERE id = ?",
            (periodo_id,),
        ).fetchone()

    def obtener_tema(self, tema_id: int) -> sqlite3.Row | None:
        return self.conexion.execute(
            "SELECT id, numero, nombre, ramo_id FROM temas_unidad WHERE id = ?",
            (tema_id,),
        ).fetchone()

    def obtener_estudiante_por_rol(self, rol: str) -> sqlite3.Row | None:
        return self.conexion.execute(
            "SELECT id, nombre, correo, rol, comunidad_id FROM estudiantes WHERE rol = ?",
            (rol,),
        ).fetchone()


class AporteRepositorio:
    def __init__(self, conexion: sqlite3.Connection):
        self.conexion = conexion

    def siguiente_id(self, tabla: str) -> int:
        if tabla not in TABLAS_CON_ID:
            raise ValueError(f"Tabla no permitida: {tabla}")
        fila = self.conexion.execute(
            f"SELECT COALESCE(MAX(id), 0) + 1 AS siguiente FROM {tabla}"
        ).fetchone()
        return int(fila["siguiente"])

    def crear_aporte_con_version(
        self,
        *,
        aporte_id: int,
        autor_id: int,
        ramo_id: int,
        periodo_id: int,
        tema_id: int,
        procedencia: str,
        fecha_envio: str,
        estado_aporte: str,
        version_id: int,
        nombre_archivo: str,
        referencia_archivo: str | None,
        hash_archivo: str | None,
        tamano_bytes: int | None,
        tipo_mime: str | None,
        estado_version: str,
        fecha_creacion: str,
    ) -> int:
        with self.conexion:
            self.conexion.execute(
                """
                INSERT INTO aportes
                    (id, autor_id, ramo_id, periodo_id, tema_id, procedencia, fecha_envio, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    aporte_id,
                    autor_id,
                    ramo_id,
                    periodo_id,
                    tema_id,
                    procedencia,
                    fecha_envio,
                    estado_aporte,
                ),
            )
            # La versión nace en Recibida y la validación la deja en su estado final,
            # tal como indica EST-01. Ambos pasos ocurren en la misma transacción.
            self.conexion.execute(
                """
                INSERT INTO versiones_apunte
                    (id, aporte_id, numero, nombre_archivo, referencia_archivo, hash_archivo,
                     tamano_bytes, tipo_mime, estado, fecha_creacion)
                VALUES (?, ?, 1, ?, ?, ?, ?, ?, 'Recibida', ?)
                """,
                (
                    version_id,
                    aporte_id,
                    nombre_archivo,
                    referencia_archivo,
                    hash_archivo,
                    tamano_bytes,
                    tipo_mime,
                    fecha_creacion,
                ),
            )
            self.conexion.execute(
                "UPDATE versiones_apunte SET estado = ? WHERE id = ?",
                (estado_version, version_id),
            )
        return aporte_id

    def crear_version_corregida(
        self,
        *,
        aporte_id: int,
        version_anterior_id: int,
        nueva_version_id: int,
        numero: int,
        nombre_archivo: str,
        referencia_archivo: str | None,
        hash_archivo: str | None,
        tamano_bytes: int | None,
        tipo_mime: str | None,
        estado_version: str,
        estado_aporte: str,
        fecha_creacion: str,
        confirmar: bool = True,
    ) -> int:
        with self.conexion if confirmar else nullcontext():
            self.conexion.execute(
                "UPDATE versiones_apunte SET estado = 'Final' WHERE id = ?",
                (version_anterior_id,),
            )
            self.conexion.execute(
                """
                INSERT INTO versiones_apunte
                    (id, aporte_id, numero, nombre_archivo, referencia_archivo, hash_archivo,
                     tamano_bytes, tipo_mime, estado, fecha_creacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Recibida', ?)
                """,
                (
                    nueva_version_id,
                    aporte_id,
                    numero,
                    nombre_archivo,
                    referencia_archivo,
                    hash_archivo,
                    tamano_bytes,
                    tipo_mime,
                    fecha_creacion,
                ),
            )
            self.conexion.execute(
                "UPDATE versiones_apunte SET estado = ? WHERE id = ?",
                (estado_version, nueva_version_id),
            )
            self.conexion.execute(
                "UPDATE aportes SET estado = ? WHERE id = ?",
                (estado_aporte, aporte_id),
            )
        return nueva_version_id

    def obtener_aporte(self, aporte_id: int) -> sqlite3.Row | None:
        return self.conexion.execute(
            "SELECT * FROM aportes WHERE id = ?", (aporte_id,)
        ).fetchone()

    def obtener_detalle(self, aporte_id: int) -> sqlite3.Row | None:
        return self.conexion.execute(
            """
            SELECT a.id, a.fecha_envio, a.estado AS estado_aporte, a.procedencia,
                   e.nombre AS autor, e.correo AS autor_correo,
                   c.nombre AS carrera, r.nombre AS ramo,
                   p.anio, p.semestre, t.nombre AS tema,
                   v.id AS version_id, v.numero, v.nombre_archivo, v.referencia_archivo,
                   v.hash_archivo, v.tamano_bytes, v.tipo_mime,
                   v.estado AS estado_version, v.fecha_creacion
            FROM aportes a
            JOIN estudiantes e ON e.id = a.autor_id
            JOIN ramos r ON r.id = a.ramo_id
            JOIN carreras c ON c.id = r.carrera_id
            JOIN periodos_academicos p ON p.id = a.periodo_id
            JOIN temas_unidad t ON t.id = a.tema_id
            JOIN versiones_apunte v ON v.aporte_id = a.id
            WHERE a.id = ?
            ORDER BY v.numero DESC
            LIMIT 1
            """,
            (aporte_id,),
        ).fetchone()

    def obtener_ultima_version(self, aporte_id: int) -> sqlite3.Row | None:
        return self.conexion.execute(
            """
            SELECT * FROM versiones_apunte
            WHERE aporte_id = ?
            ORDER BY numero DESC
            LIMIT 1
            """,
            (aporte_id,),
        ).fetchone()

    def buscar_version_por_hash(self, hash_archivo: str) -> sqlite3.Row | None:
        return self.conexion.execute(
            """
            SELECT v.id AS version_id, v.numero, v.nombre_archivo,
                   v.estado AS estado_version,
                   a.id AS aporte_id, a.fecha_envio, a.estado AS estado_aporte,
                   e.nombre AS autor, r.nombre AS ramo, t.nombre AS tema
            FROM versiones_apunte v
            JOIN aportes a ON a.id = v.aporte_id
            JOIN estudiantes e ON e.id = a.autor_id
            JOIN ramos r ON r.id = a.ramo_id
            JOIN temas_unidad t ON t.id = a.tema_id
            WHERE v.hash_archivo = ?
            LIMIT 1
            """,
            (hash_archivo,),
        ).fetchone()

    def contar_aportes(self) -> int:
        fila = self.conexion.execute("SELECT COUNT(*) AS total FROM aportes").fetchone()
        return int(fila["total"])

    def actualizar_estado_aporte(self, aporte_id: int, estado: str) -> None:
        with self.conexion:
            self.conexion.execute(
                "UPDATE aportes SET estado = ? WHERE id = ?", (estado, aporte_id)
            )

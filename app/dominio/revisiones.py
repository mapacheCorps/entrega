"""Consultas y persistencia de revisión académica y publicación."""

from __future__ import annotations

import sqlite3

from app.dominio.entidades import DecisionRevision, EstadoAporte, EstadoVersion


class RevisionAcademicaRepositorio:
    def __init__(self, conexion: sqlite3.Connection):
        self.conexion = conexion

    def listar_asignadas(self, comunidad_id: int) -> list[sqlite3.Row]:
        return self.conexion.execute(
            """
            SELECT a.id AS aporte_id, v.id AS version_id, v.numero,
                   v.estado AS estado_version, v.nombre_archivo, e.nombre AS revisor
            FROM asignaciones_revision ar
            JOIN aportes a ON a.id = ar.aporte_id
            JOIN estudiantes e ON e.id = ar.revisor_id
            JOIN versiones_apunte v ON v.id = (
                SELECT id FROM versiones_apunte
                WHERE aporte_id = a.id ORDER BY numero DESC LIMIT 1
            )
            WHERE ar.comunidad_id = ? AND ar.estado = 'Asignada' AND a.estado = 'Asignado'
              AND v.estado IN ('PendienteRevision', 'EnRevision')
            ORDER BY ar.fecha_asignacion, a.id
            """,
            (comunidad_id,),
        ).fetchall()

    def obtener_contexto(self, aporte_id: int) -> sqlite3.Row | None:
        return self.conexion.execute(
            """
            SELECT a.id AS aporte_id, a.estado AS estado_aporte,
                   v.id AS version_id, v.numero, v.nombre_archivo, v.referencia_archivo,
                   v.estado AS estado_version, ar.id AS asignacion_id, ar.revisor_id,
                   COALESCE(ar.comunidad_id, ra.comunidad_id) AS comunidad_id,
                   e.nombre AS revisor
            FROM aportes a
            JOIN versiones_apunte v ON v.id = (
                SELECT id FROM versiones_apunte
                WHERE aporte_id = a.id ORDER BY numero DESC LIMIT 1
            )
            LEFT JOIN asignaciones_revision ar ON ar.aporte_id = a.id AND ar.estado = 'Asignada'
            LEFT JOIN estudiantes e ON e.id = ar.revisor_id
            LEFT JOIN revisiones_academicas ra ON ra.version_id = v.id
            WHERE a.id = ?
            """,
            (aporte_id,),
        ).fetchone()

    def cambiar_estado_version(self, version_id: int, estado: EstadoVersion) -> None:
        self.conexion.execute(
            "UPDATE versiones_apunte SET estado = ? WHERE id = ?", (estado, version_id)
        )

    def registrar(
        self,
        revision: sqlite3.Row,
        fecha: str,
        decision: DecisionRevision,
        alcance: str,
        observaciones: str,
    ) -> None:
        self.conexion.execute(
            """
            INSERT INTO revisiones_academicas
                (version_id, revisor_id, comunidad_id, fecha, decision, alcance, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                revision["version_id"], revision["revisor_id"], revision["comunidad_id"],
                fecha, decision, alcance, observaciones,
            ),
        )

    def cerrar_asignacion(
        self, revision: sqlite3.Row, estado_aporte: EstadoAporte
    ) -> None:
        self.conexion.execute(
            "UPDATE aportes SET estado = ? WHERE id = ?",
            (estado_aporte, revision["aporte_id"]),
        )
        self.conexion.execute(
            "UPDATE asignaciones_revision SET estado = 'Finalizada' WHERE id = ?",
            (revision["asignacion_id"],),
        )

    def listar_publicadas(self) -> list[sqlite3.Row]:
        return self.conexion.execute(
            """
            SELECT v.id AS version_id, v.numero, v.nombre_archivo,
                   c.nombre AS carrera, r.nombre AS ramo, t.nombre AS tema, p.anio, p.semestre
            FROM versiones_apunte v
            JOIN revisiones_academicas ra ON ra.version_id = v.id AND ra.decision = 'Aprobacion'
            JOIN aportes a ON a.id = v.aporte_id
            JOIN ramos r ON r.id = a.ramo_id
            JOIN carreras c ON c.id = r.carrera_id
            JOIN temas_unidad t ON t.id = a.tema_id
            JOIN periodos_academicos p ON p.id = a.periodo_id
            WHERE v.estado = 'Publicada'
            ORDER BY ra.fecha DESC, v.id DESC
            """
        ).fetchall()

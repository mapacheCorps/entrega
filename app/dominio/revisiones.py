"""Consultas y persistencia de revisión académica y publicación."""

from __future__ import annotations

import sqlite3

from app.dominio.entidades import DecisionRevision, EstadoAporte, EstadoVersion, TipoRevisor


class RevisionAcademicaRepositorio:
    def __init__(self, conexion: sqlite3.Connection):
        self.conexion = conexion

    def listar_feedback_autor(self, aporte_id: int, autor_id: int) -> list[sqlite3.Row]:
        return self.conexion.execute(
            """
            SELECT v.id AS version_id, v.numero, ra.decision, ra.alcance, ra.observaciones
            FROM revisiones_academicas ra
            JOIN versiones_apunte v ON v.id = ra.version_id
            JOIN aportes a ON a.id = v.aporte_id
            WHERE a.id = ? AND a.autor_id = ?
              AND ra.decision IN ('Rechazo', 'SolicitudCorreccion')
            ORDER BY v.numero DESC
            """,
            (aporte_id, autor_id),
        ).fetchall()

    def obtener_decision(self, version_id: int) -> str | None:
        fila = self.conexion.execute(
            "SELECT decision FROM revisiones_academicas WHERE version_id = ?", (version_id,)
        ).fetchone()
        return fila["decision"] if fila is not None else None

    def listar_pendientes(self) -> list[sqlite3.Row]:
        return self.conexion.execute(
            """
            SELECT a.id AS aporte_id, v.id AS version_id, v.numero,
                   v.nombre_archivo, r.nombre AS ramo, t.nombre AS tema, p.anio, p.semestre
            FROM aportes a
            JOIN ramos r ON r.id = a.ramo_id
            JOIN temas_unidad t ON t.id = a.tema_id
            JOIN periodos_academicos p ON p.id = a.periodo_id
            JOIN versiones_apunte v ON v.id = (
                SELECT id FROM versiones_apunte
                WHERE aporte_id = a.id ORDER BY numero DESC LIMIT 1
            )
            WHERE a.estado = 'PendienteRevision' AND v.estado = 'PendienteRevision'
            ORDER BY v.fecha_creacion, a.id
            """
        ).fetchall()

    def listar_para_experto(self) -> list[sqlite3.Row]:
        """Versiones en estado EnRevisionExperto para el panel de experto."""
        return self.conexion.execute(
            """
            SELECT a.id AS aporte_id, v.id AS version_id, v.numero,
                   v.nombre_archivo, r.nombre AS ramo, t.nombre AS tema, p.anio, p.semestre,
                   ra.especialidad_registrada
            FROM aportes a
            JOIN ramos r ON r.id = a.ramo_id
            JOIN temas_unidad t ON t.id = a.tema_id
            JOIN periodos_academicos p ON p.id = a.periodo_id
            JOIN versiones_apunte v ON v.id = (
                SELECT id FROM versiones_apunte
                WHERE aporte_id = a.id ORDER BY numero DESC LIMIT 1
            )
            JOIN revisiones_academicas ra ON ra.version_id = v.id
            WHERE a.estado = 'PendienteRevision' AND v.estado = 'EnRevisionExperto'
            ORDER BY v.fecha_creacion, a.id
            """
        ).fetchall()

    def obtener_contexto(self, aporte_id: int) -> sqlite3.Row | None:
        return self.conexion.execute(
            """
            SELECT a.id AS aporte_id, a.estado AS estado_aporte,
                   v.id AS version_id, v.numero, v.nombre_archivo, v.referencia_archivo,
                   v.estado AS estado_version, ra.id AS decision_id,
                   ra.tipo_revisor, ra.experto_id, ra.especialidad_registrada
            FROM aportes a
            JOIN versiones_apunte v ON v.id = (
                SELECT id FROM versiones_apunte
                WHERE aporte_id = a.id ORDER BY numero DESC LIMIT 1
            )
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
        tipo_revisor: TipoRevisor,
        revisor_id: int | None,
        experto_id: int | None,
        comunidad_id: int,
        fecha: str,
        decision: DecisionRevision,
        alcance: str,
        observaciones: str,
        especialidad_registrada: str | None = None,
    ) -> None:
        self.conexion.execute(
            """
            INSERT INTO revisiones_academicas
                (version_id, tipo_revisor, revisor_id, experto_id, comunidad_id, fecha, decision, alcance, observaciones, especialidad_registrada)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                revision["version_id"], tipo_revisor, revisor_id, experto_id, comunidad_id,
                fecha, decision, alcance, observaciones, especialidad_registrada,
            ),
        )

    def actualizar_estado_aporte(
        self, revision: sqlite3.Row, estado_aporte: EstadoAporte
    ) -> None:
        self.conexion.execute(
            "UPDATE aportes SET estado = ? WHERE id = ?",
            (estado_aporte, revision["aporte_id"]),
        )

    def listar_publicadas(self) -> list[sqlite3.Row]:
        return self.conexion.execute(self._publicadas + " ORDER BY ra.fecha DESC, v.id DESC").fetchall()

    def obtener_publicada(self, version_id: int) -> sqlite3.Row | None:
        return self.conexion.execute(self._publicadas + " AND v.id = ?", (version_id,)).fetchone()

    _publicadas = """
            SELECT v.id AS version_id, v.numero, v.nombre_archivo, v.referencia_archivo,
                   c.nombre AS carrera, r.nombre AS ramo, t.nombre AS tema, p.anio, p.semestre,
                   a.procedencia, ra.fecha, ra.alcance, e.nombre AS revisor
            FROM versiones_apunte v
            JOIN revisiones_academicas ra ON ra.version_id = v.id AND ra.decision = 'Aprobacion'
            JOIN estudiantes e ON e.id = COALESCE(ra.revisor_id, ra.experto_id)
            JOIN aportes a ON a.id = v.aporte_id
            JOIN ramos r ON r.id = a.ramo_id
            JOIN carreras c ON c.id = r.carrera_id
            JOIN temas_unidad t ON t.id = a.tema_id
            JOIN periodos_academicos p ON p.id = a.periodo_id
            WHERE v.estado = 'Publicada'
            """
"""Inicio y resolución de la revisión comunitaria (HU-03)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from enum import Enum

from app.dominio.entidades import DecisionRevision, EstadoAporte, EstadoVersion
from app.dominio.revisiones import RevisionAcademicaRepositorio


class MotivoRevision(Enum):
    NO_ENCONTRADA = "no_encontrada"
    COMUNIDAD_NO_AUTORIZADA = "comunidad_no_autorizada"
    ESTADO_INCOMPATIBLE = "estado_incompatible"


class ErrorRevision(Exception):
    def __init__(self, motivo: MotivoRevision):
        super().__init__(motivo.value)
        self.motivo = motivo


class DatosRevisionInvalidos(Exception):
    def __init__(self, errores: dict[str, str]):
        super().__init__("Completa los datos de la decisión.")
        self.errores = errores


RESULTADOS = {
    DecisionRevision.APROBACION: (EstadoVersion.PUBLICADA, EstadoAporte.PUBLICADO),
    DecisionRevision.RECHAZO: (EstadoVersion.RECHAZADA, EstadoAporte.RECHAZADO),
    DecisionRevision.SOLICITUD_CORRECCION: (
        EstadoVersion.REQUIERE_CORRECCION, EstadoAporte.CORRECCION_SOLICITADA,
    ),
}


class ServicioRevisiones:
    def __init__(self, conexion: sqlite3.Connection):
        self.conexion = conexion
        self.repo = RevisionAcademicaRepositorio(conexion)

    def consultar(self, aporte_id: int, version_id: int, comunidad_id: int) -> sqlite3.Row:
        revision = self.repo.obtener_contexto(aporte_id)
        if revision is None:
            raise ErrorRevision(MotivoRevision.NO_ENCONTRADA)
        if revision["comunidad_id"] != comunidad_id:
            raise ErrorRevision(MotivoRevision.COMUNIDAD_NO_AUTORIZADA)
        if (
            revision["version_id"] != version_id
            or revision["asignacion_id"] is None
            or revision["estado_aporte"] != EstadoAporte.ASIGNADO
            or revision["estado_version"] not in (
                EstadoVersion.PENDIENTE_REVISION, EstadoVersion.EN_REVISION,
            )
        ):
            raise ErrorRevision(MotivoRevision.ESTADO_INCOMPATIBLE)
        return revision

    def iniciar(self, aporte_id: int, version_id: int, comunidad_id: int) -> None:
        with self.conexion:
            self.conexion.execute("BEGIN IMMEDIATE")
            revision = self.consultar(aporte_id, version_id, comunidad_id)
            if revision["estado_version"] == EstadoVersion.PENDIENTE_REVISION:
                self.repo.cambiar_estado_version(version_id, EstadoVersion.EN_REVISION)

    def decidir(
        self,
        aporte_id: int,
        version_id: int,
        comunidad_id: int,
        decision: str,
        alcance: str,
        observaciones: str,
    ) -> DecisionRevision:
        with self.conexion:
            self.conexion.execute("BEGIN IMMEDIATE")
            revision = self.consultar(aporte_id, version_id, comunidad_id)
            if revision["estado_version"] != EstadoVersion.EN_REVISION:
                raise ErrorRevision(MotivoRevision.ESTADO_INCOMPATIBLE)
            decision_valida = _validar_datos(decision, alcance, observaciones)
            estado_version, estado_aporte = RESULTADOS[decision_valida]
            fecha = datetime.now(timezone.utc).isoformat(timespec="seconds")
            self.repo.registrar(
                revision, fecha, decision_valida, alcance.strip(), observaciones.strip()
            )
            if decision_valida is DecisionRevision.APROBACION:
                self.repo.cambiar_estado_version(version_id, EstadoVersion.APROBADA)
            self.repo.cambiar_estado_version(version_id, estado_version)
            self.repo.cerrar_asignacion(revision, estado_aporte)
            return decision_valida


def _validar_datos(decision: str, alcance: str, observaciones: str) -> DecisionRevision:
    errores: dict[str, str] = {}
    decisiones = {opcion.value: opcion for opcion in DecisionRevision}
    if decision not in decisiones:
        errores["decision"] = "Selecciona una decisión."
    if not alcance.strip():
        errores["alcance"] = "Indica qué parte del contenido revisaste."
    if not observaciones.strip():
        errores["observaciones"] = "Escribe las observaciones que fundamentan la decisión."
    if errores:
        raise DatosRevisionInvalidos(errores)
    return decisiones[decision]

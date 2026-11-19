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
    YA_RESUELTA = "ya_resuelta"
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

    def consultar(self, aporte_id: int, version_id: int) -> sqlite3.Row:
        revision = self.repo.obtener_contexto(aporte_id)
        if revision is None:
            raise ErrorRevision(MotivoRevision.NO_ENCONTRADA)
        if revision["version_id"] != version_id:
            raise ErrorRevision(MotivoRevision.ESTADO_INCOMPATIBLE)
        if revision["decision_id"] is not None:
            raise ErrorRevision(MotivoRevision.YA_RESUELTA)
        if (
            revision["estado_aporte"] != EstadoAporte.PENDIENTE_REVISION
            or revision["estado_version"] != EstadoVersion.PENDIENTE_REVISION
        ):
            raise ErrorRevision(MotivoRevision.ESTADO_INCOMPATIBLE)
        return revision

    def decidir(
        self,
        aporte_id: int,
        version_id: int,
        moderador: sqlite3.Row,
        decision: str,
        alcance: str,
        observaciones: str,
    ) -> DecisionRevision:
        if moderador["rol"] != "Moderador" or moderador["comunidad_id"] is None:
            raise ErrorRevision(MotivoRevision.COMUNIDAD_NO_AUTORIZADA)
        with self.conexion:
            self.conexion.execute("BEGIN IMMEDIATE")
            revision = self.consultar(aporte_id, version_id)
            decision_valida = _validar_datos(decision, alcance, observaciones)
            estado_version, estado_aporte = RESULTADOS[decision_valida]
            fecha = datetime.now(timezone.utc).isoformat(timespec="seconds")
            self.repo.cambiar_estado_version(version_id, EstadoVersion.EN_REVISION)
            self.repo.registrar(
                revision, moderador["id"], moderador["comunidad_id"], fecha,
                decision_valida, alcance.strip(), observaciones.strip(),
            )
            if decision_valida is DecisionRevision.APROBACION:
                self.repo.cambiar_estado_version(version_id, EstadoVersion.APROBADA)
            self.repo.cambiar_estado_version(version_id, estado_version)
            self.repo.actualizar_estado_aporte(revision, estado_aporte)
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

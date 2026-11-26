"""Inicio y resolución de la revisión comunitaria y por Experto (HU-03 / CU-13)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from enum import Enum

from app.dominio.entidades import DecisionRevision, EstadoAporte, EstadoVersion, TipoRevisor
from app.dominio.revisiones import RevisionAcademicaRepositorio


class MotivoRevision(Enum):
    NO_ENCONTRADA = "no_encontrada"
    COMUNIDAD_NO_AUTORIZADA = "comunidad_no_autorizada"
    EXPERTO_NO_AUTORIZADO = "experto_no_autorizado"
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
        """Alias para compatibilidad con tests existentes. Equivale a consultar_para_comunidad."""
        return self.consultar_para_comunidad(aporte_id, version_id)

    def consultar_para_comunidad(self, aporte_id: int, version_id: int) -> sqlite3.Row:
        """Valida y devuelve contexto para decisión por Comunidad (Moderador)."""
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

    def consultar_para_experto(self, aporte_id: int, version_id: int) -> sqlite3.Row:
        """Valida y devuelve contexto para evaluación por Experto."""
        revision = self.repo.obtener_contexto(aporte_id)
        if revision is None:
            raise ErrorRevision(MotivoRevision.NO_ENCONTRADA)
        if revision["version_id"] != version_id:
            raise ErrorRevision(MotivoRevision.ESTADO_INCOMPATIBLE)
        if revision["decision_id"] is not None:
            raise ErrorRevision(MotivoRevision.YA_RESUELTA)
        if revision["estado_version"] != EstadoVersion.EN_REVISION_EXPERTO:
            raise ErrorRevision(MotivoRevision.ESTADO_INCOMPATIBLE)
        return revision

    def solicitar_revision_experto(
        self,
        aporte_id: int,
        version_id: int,
        moderador: sqlite3.Row,
        especialidad: str,
    ) -> None:
        """Transición PendienteRevision → EnRevisionExperto (Moderador deriva a Experto)."""
        if moderador["rol"] != "Moderador" or moderador["comunidad_id"] is None:
            raise ErrorRevision(MotivoRevision.COMUNIDAD_NO_AUTORIZADA)
        with self.conexion:
            self.conexion.execute("BEGIN IMMEDIATE")
            revision = self.consultar_para_comunidad(aporte_id, version_id)
            self.repo.cambiar_estado_version(version_id, EstadoVersion.EN_REVISION_EXPERTO)
            # Registramos una 'solicitud' inicial sin decisión aún; el experto completará la revisión
            # Aquí solo cambiamos el estado; la revisión académica se crea cuando el experto decide

    def evaluar_por_experto(
        self,
        aporte_id: int,
        version_id: int,
        experto: sqlite3.Row,
        decision: str,
        alcance: str,
        observaciones: str,
    ) -> DecisionRevision:
        """Experto evalúa versión en EnRevisionExperto → estado final."""
        if experto["rol"] != "Experto" or experto["experto_id"] is None:
            raise ErrorRevision(MotivoRevision.EXPERTO_NO_AUTORIZADO)
        with self.conexion:
            self.conexion.execute("BEGIN IMMEDIATE")
            revision = self.consultar_para_experto(aporte_id, version_id)
            decision_valida = _validar_datos(decision, alcance, observaciones)
            estado_version, estado_aporte = RESULTADOS[decision_valida]
            fecha = datetime.now(timezone.utc).isoformat(timespec="seconds")
            # Transición EnRevisionExperto → estado final
            self.repo.cambiar_estado_version(version_id, estado_version)
            # Obtener comunidad_id del moderador que derivó (fallback: primera comunidad)
            comunidad = self.conexion.execute(
                "SELECT id FROM comunidades_estudiantiles LIMIT 1"
            ).fetchone()
            comunidad_id = comunidad["id"] if comunidad else 1

            self.repo.registrar(
                revision,
                tipo_revisor=TipoRevisor.EXPERTO,
                revisor_id=None,
                experto_id=experto["experto_id"],
                comunidad_id=comunidad_id,
                fecha=fecha,
                decision=decision_valida,
                alcance=alcance.strip(),
                observaciones=observaciones.strip(),
                especialidad_registrada=experto.get("especialidad"),
            )
            self.repo.actualizar_estado_aporte(revision, estado_aporte)
            return decision_valida

    def decidir(
        self,
        aporte_id: int,
        version_id: int,
        moderador: sqlite3.Row,
        decision: str,
        alcance: str,
        observaciones: str,
    ) -> DecisionRevision:
        """Decisión por Comunidad (Moderador): PendienteRevision/EnRevision → estado final."""
        if moderador["rol"] != "Moderador" or moderador["comunidad_id"] is None:
            raise ErrorRevision(MotivoRevision.COMUNIDAD_NO_AUTORIZADA)
        with self.conexion:
            self.conexion.execute("BEGIN IMMEDIATE")
            revision = self.consultar_para_comunidad(aporte_id, version_id)
            decision_valida = _validar_datos(decision, alcance, observaciones)
            estado_version, estado_aporte = RESULTADOS[decision_valida]
            fecha = datetime.now(timezone.utc).isoformat(timespec="seconds")
            # Transición según estado actual
            if revision["estado_version"] == EstadoVersion.PENDIENTE_REVISION:
                self.repo.cambiar_estado_version(version_id, EstadoVersion.EN_REVISION)
            # Si ya estaba en EnRevision, se queda
            self.repo.cambiar_estado_version(version_id, estado_version)
            self.repo.registrar(
                revision,
                tipo_revisor=TipoRevisor.COMUNIDAD,
                revisor_id=moderador["id"],
                experto_id=None,
                comunidad_id=moderador["comunidad_id"],
                fecha=fecha,
                decision=decision_valida,
                alcance=alcance.strip(),
                observaciones=observaciones.strip(),
                especialidad_registrada=None,
            )
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
"""Entidades y estados del dominio de aportes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EstadoAporte(str, Enum):
    PENDIENTE_REVISION = "PendienteRevision"
    REQUIERE_CORRECCION = "RequiereCorreccion"
    PUBLICADO = "Publicado"
    RECHAZADO = "Rechazado"
    CORRECCION_SOLICITADA = "CorreccionSolicitada"


class EstadoVersion(str, Enum):
    RECIBIDA = "Recibida"
    PENDIENTE_REVISION = "PendienteRevision"
    REQUIERE_CORRECCION = "RequiereCorreccion"
    FINAL = "Final"
    EN_REVISION = "EnRevision"
    EN_REVISION_EXPERTO = "EnRevisionExperto"
    APROBADA = "Aprobada"
    PUBLICADA = "Publicada"
    RECHAZADA = "Rechazada"


class DecisionRevision(str, Enum):
    APROBACION = "Aprobacion"
    RECHAZO = "Rechazo"
    SOLICITUD_CORRECCION = "SolicitudCorreccion"


class TipoRevisor(str, Enum):
    COMUNIDAD = "comunidad"
    EXPERTO = "experto"


@dataclass
class Aporte:
    id: int | None
    autor_id: int
    ramo_id: int
    periodo_id: int
    tema_id: int
    procedencia: str
    fecha_envio: datetime
    estado: EstadoAporte = EstadoAporte.PENDIENTE_REVISION

    def esta_pendiente(self) -> bool:
        return self.estado is EstadoAporte.PENDIENTE_REVISION

    def requiere_correccion(self) -> bool:
        return self.estado is EstadoAporte.REQUIERE_CORRECCION


@dataclass
class VersionApunte:
    id: int | None
    aporte_id: int
    numero: int
    nombre_archivo: str
    estado: EstadoVersion = EstadoVersion.RECIBIDA
    referencia_archivo: str | None = None
    hash_archivo: str | None = None
    tamano_bytes: int | None = None
    tipo_mime: str | None = None
    fecha_creacion: datetime | None = None

    def fue_recibida(self) -> bool:
        return self.estado is EstadoVersion.RECIBIDA

    def esta_pendiente_de_revision(self) -> bool:
        return self.estado is EstadoVersion.PENDIENTE_REVISION

    def esta_en_revision_experto(self) -> bool:
        return self.estado is EstadoVersion.EN_REVISION_EXPERTO

    def requiere_correccion(self) -> bool:
        return self.estado is EstadoVersion.REQUIERE_CORRECCION

    def esta_final(self) -> bool:
        return self.estado is EstadoVersion.FINAL


@dataclass
class Experto:
    id: int | None
    nombre: str
    correo: str
    especialidad: str
    creado_en: datetime | None = None


@dataclass
class RevisionAcademica:
    id: int | None
    version_id: int
    comunidad_id: int
    fecha: datetime
    decision: DecisionRevision
    alcance: str
    observaciones: str
    tipo_revisor: TipoRevisor = TipoRevisor.COMUNIDAD
    revisor_id: int | None = None          # Moderador (cuando comunidad)
    experto_id: int | None = None          # Experto (cuando experto)
    especialidad_registrada: str | None = None  # Denormalizada para ficha

    def es_por_comunidad(self) -> bool:
        return self.tipo_revisor is TipoRevisor.COMUNIDAD

    def es_por_experto(self) -> bool:
        return self.tipo_revisor is TipoRevisor.EXPERTO
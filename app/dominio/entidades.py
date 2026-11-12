"""Entidades y estados del dominio usados por HU-01."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EstadoAporte(str, Enum):
    PENDIENTE_ASIGNACION = "PendienteAsignacion"
    REQUIERE_CORRECCION = "RequiereCorreccion"


class EstadoVersion(str, Enum):
    RECIBIDA = "Recibida"
    PENDIENTE_REVISION = "PendienteRevision"
    REQUIERE_CORRECCION = "RequiereCorreccion"
    FINAL = "Final"


@dataclass
class Aporte:
    id: int | None
    autor_id: int
    ramo_id: int
    periodo_id: int
    tema_id: int
    procedencia: str
    fecha_envio: datetime
    estado: EstadoAporte = EstadoAporte.PENDIENTE_ASIGNACION

    def esta_pendiente(self) -> bool:
        return self.estado is EstadoAporte.PENDIENTE_ASIGNACION

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

    def requiere_correccion(self) -> bool:
        return self.estado is EstadoVersion.REQUIERE_CORRECCION

    def esta_final(self) -> bool:
        return self.estado is EstadoVersion.FINAL

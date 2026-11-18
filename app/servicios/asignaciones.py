"""Organización de revisiones de aportes (HU-02, P05)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from app.dominio.entidades import EstadoAporte, EstadoVersion
from app.dominio.repositorios import AporteRepositorio, AsignacionRevisionRepositorio


class TipoAsignacion(Enum):
    ASIGNADO = "asignado"
    YA_ASIGNADO = "ya_asignado"
    SIN_REVISOR = "sin_revisor"
    NO_ENCONTRADO = "no_encontrado"
    NO_ASIGNABLE = "no_asignable"


@dataclass(frozen=True)
class ResultadoAsignacion:
    tipo: TipoAsignacion
    asignacion: sqlite3.Row | None = None


class ServicioAsignaciones:
    def __init__(self, conexion: sqlite3.Connection):
        self.conexion = conexion
        self.aportes = AporteRepositorio(conexion)
        self.asignaciones = AsignacionRevisionRepositorio(conexion)

    def asignar(self, aporte_id: int, comunidad_id: int) -> ResultadoAsignacion:
        with self.conexion:
            self.conexion.execute("BEGIN IMMEDIATE")
            aporte = self.aportes.obtener_aporte(aporte_id)
            if aporte is None:
                return ResultadoAsignacion(TipoAsignacion.NO_ENCONTRADO)

            vigente = self.asignaciones.buscar_vigente(aporte_id)
            if vigente is not None:
                return ResultadoAsignacion(TipoAsignacion.YA_ASIGNADO, vigente)

            version = self.aportes.obtener_ultima_version(aporte_id)
            if (
                aporte["estado"] != EstadoAporte.PENDIENTE_ASIGNACION
                or version is None
                or version["estado"] != EstadoVersion.PENDIENTE_REVISION
            ):
                return ResultadoAsignacion(TipoAsignacion.NO_ASIGNABLE)

            revisor = self.asignaciones.elegir_revisor(
                comunidad_id, aporte["ramo_id"], aporte["autor_id"]
            )
            if revisor is None:
                return ResultadoAsignacion(TipoAsignacion.SIN_REVISOR)

            fecha = datetime.now(timezone.utc).isoformat(timespec="seconds")
            self.asignaciones.registrar(aporte_id, revisor["id"], comunidad_id, fecha)
            return ResultadoAsignacion(
                TipoAsignacion.ASIGNADO, self.asignaciones.buscar_vigente(aporte_id)
            )

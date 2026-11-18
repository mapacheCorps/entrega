"""Panel de la comunidad para organizar revisiones (HU-02, CU-02)."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request

from app.db.conexion import obtener_conexion
from app.dominio.repositorios import AsignacionRevisionRepositorio, CatalogoRepositorio
from app.rutas.demo import rol_actual
from app.rutas.paginas import contexto_base, pagina_error, templates
from app.servicios.asignaciones import ResultadoAsignacion, ServicioAsignaciones, TipoAsignacion

router = APIRouter(prefix="/moderacion")


def _acceso_denegado(request: Request):
    return pagina_error(
        request,
        403,
        "Acción no disponible para este rol",
        "Solo el perfil Moderador puede organizar las revisiones.",
    )


def _panel(
    request: Request,
    conexion: sqlite3.Connection,
    aporte_id: int | None = None,
    resultado: ResultadoAsignacion | None = None,
):
    contexto = contexto_base(request)
    contexto.update(
        aportes=AsignacionRevisionRepositorio(conexion).listar_aportes_pendientes(),
        aporte_id=aporte_id,
        asignacion=resultado.asignacion if resultado else None,
        ya_asignado=bool(resultado and resultado.tipo is TipoAsignacion.YA_ASIGNADO),
        sin_revisor=bool(resultado and resultado.tipo is TipoAsignacion.SIN_REVISOR),
    )
    return templates.TemplateResponse(request, "moderacion_aportes.html", contexto)


@router.get("/aportes")
def panel_moderacion(
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    if rol_actual(request) != "Moderador":
        return _acceso_denegado(request)
    return _panel(request, conexion)


@router.post("/aportes/{aporte_id}/asignar")
def asignar_revision(
    aporte_id: Annotated[int, Path(ge=1, le=2**63 - 1)],
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    if rol_actual(request) != "Moderador":
        return _acceso_denegado(request)

    moderador = CatalogoRepositorio(conexion).obtener_estudiante_por_rol("Moderador")
    if moderador is None or moderador["comunidad_id"] is None:
        return pagina_error(
            request,
            503,
            "Comunidad de demostración sin configurar",
            "Carga los datos de ejemplo para organizar revisiones.",
        )

    resultado = ServicioAsignaciones(conexion).asignar(aporte_id, moderador["comunidad_id"])
    if resultado.tipo is TipoAsignacion.NO_ENCONTRADO:
        return pagina_error(
            request, 404, "Aporte no encontrado",
            "No existe un aporte con el identificador solicitado.",
        )
    if resultado.tipo is TipoAsignacion.NO_ASIGNABLE:
        return pagina_error(
            request, 409, "Aporte no disponible para asignación",
            "Solo se pueden asignar aportes pendientes cuya última versión está validada.",
        )
    return _panel(request, conexion, aporte_id, resultado)

"""Cola compartida de revisión comunitaria (HU-02 y HU-03)."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Path, Request
from fastapi.responses import Response

from app.db.conexion import obtener_conexion
from app.dominio.entidades import DecisionRevision
from app.dominio.repositorios import CatalogoRepositorio
from app.dominio.revisiones import RevisionAcademicaRepositorio
from app.integraciones.almacenamiento import ErrorAlmacenamiento, nombre_seguro
from app.rutas.demo import rol_actual
from app.rutas.paginas import contexto_base, pagina_error, templates
from app.servicios.revisiones import (
    DatosRevisionInvalidos,
    ErrorRevision,
    MotivoRevision,
    ServicioRevisiones,
)

router = APIRouter(prefix="/moderacion")
Identificador = Annotated[int, Path(ge=1, le=2**63 - 1)]
BASE_REVISION = "/aportes/{aporte_id}/versiones/{version_id}"
DECISIONES = {
    DecisionRevision.APROBACION: "Aprobar y publicar",
    DecisionRevision.RECHAZO: "Rechazar",
    DecisionRevision.SOLICITUD_CORRECCION: "Solicitar corrección",
}
CONFIRMACIONES = {
    DecisionRevision.APROBACION: "La versión fue aprobada y publicada.",
    DecisionRevision.RECHAZO: "El rechazo quedó registrado. La versión sigue fuera del catálogo.",
    DecisionRevision.SOLICITUD_CORRECCION: (
        "La solicitud de corrección quedó registrada. La versión sigue fuera del catálogo."
    ),
}


def _moderador_autorizado(
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
) -> sqlite3.Row:
    if rol_actual(request) != "Moderador":
        raise ErrorRevision(MotivoRevision.COMUNIDAD_NO_AUTORIZADA)
    moderador = CatalogoRepositorio(conexion).obtener_estudiante_por_rol("Moderador")
    if moderador is None or moderador["comunidad_id"] is None:
        raise ErrorRevision(MotivoRevision.COMUNIDAD_NO_AUTORIZADA)
    return moderador


async def mostrar_error_revision(request: Request, error: ErrorRevision):
    if error.motivo is MotivoRevision.COMUNIDAD_NO_AUTORIZADA:
        return pagina_error(
            request, 403, "Revisión no autorizada",
            "Solo el perfil Moderador puede revisar aportes.",
        )
    if error.motivo is MotivoRevision.NO_ENCONTRADA:
        return pagina_error(
            request, 404, "Versión no encontrada", "El aporte no tiene una versión disponible."
        )
    if error.motivo is MotivoRevision.YA_RESUELTA:
        return pagina_error(
            request, 409, "Versión ya resuelta", "Otro moderador ya registró una decisión para esta versión."
        )
    return pagina_error(
        request, 409, "La acción no está disponible",
        "Comprueba que sea la versión vigente y que siga pendiente de revisión.",
    )


def _formulario_revision(
    request: Request,
    revision: sqlite3.Row,
    valores: dict[str, str] | None = None,
    errores: dict[str, str] | None = None,
):
    contexto = contexto_base(request)
    contexto.update(
        revision=revision, decisiones=DECISIONES, valores=valores or {}, errores=errores or {},
    )
    return templates.TemplateResponse(
        request, "revision_comunitaria.html", contexto, status_code=400 if errores else 200,
    )


@router.get("/aportes")
def panel_moderacion(
    request: Request,
    moderador: sqlite3.Row = Depends(_moderador_autorizado),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    contexto = contexto_base(request)
    contexto["revisiones"] = RevisionAcademicaRepositorio(conexion).listar_pendientes()
    return templates.TemplateResponse(request, "moderacion_aportes.html", contexto)


@router.get(BASE_REVISION + "/revision")
def detalle_revision(
    aporte_id: Identificador,
    version_id: Identificador,
    request: Request,
    moderador: sqlite3.Row = Depends(_moderador_autorizado),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    revision = ServicioRevisiones(conexion).consultar(aporte_id, version_id)
    return _formulario_revision(request, revision)


@router.get(BASE_REVISION + "/archivo")
def archivo_revision(
    aporte_id: Identificador,
    version_id: Identificador,
    request: Request,
    moderador: sqlite3.Row = Depends(_moderador_autorizado),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    revision = ServicioRevisiones(conexion).consultar(aporte_id, version_id)
    try:
        archivo = request.app.state.almacenamiento.leer(revision["referencia_archivo"] or "")
    except ErrorAlmacenamiento:
        return pagina_error(
            request, 404, "Archivo no disponible", "No se encontró el archivo de esta versión."
        )
    nombre = nombre_seguro(revision["nombre_archivo"])
    return Response(
        archivo,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )


@router.post(BASE_REVISION + "/revision/decision")
def decidir_revision(
    aporte_id: Identificador,
    version_id: Identificador,
    request: Request,
    decision: str = Form(""),
    alcance: str = Form(""),
    observaciones: str = Form(""),
    moderador: sqlite3.Row = Depends(_moderador_autorizado),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    servicio = ServicioRevisiones(conexion)
    try:
        resultado = servicio.decidir(
            aporte_id, version_id, moderador, decision, alcance, observaciones
        )
    except DatosRevisionInvalidos as error:
        revision = servicio.consultar(aporte_id, version_id)
        valores = {"decision": decision, "alcance": alcance, "observaciones": observaciones}
        return _formulario_revision(request, revision, valores, error.errores)

    contexto = contexto_base(request)
    contexto.update(
        mensaje=CONFIRMACIONES[resultado],
        publicada=resultado is DecisionRevision.APROBACION,
    )
    return templates.TemplateResponse(request, "revision_resultado.html", contexto)

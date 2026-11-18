"""Panel de asignación y revisión comunitaria (HU-02 y HU-03)."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Path, Request
from fastapi.responses import RedirectResponse, Response

from app.db.conexion import obtener_conexion
from app.dominio.entidades import DecisionRevision
from app.dominio.repositorios import AsignacionRevisionRepositorio, CatalogoRepositorio
from app.dominio.revisiones import RevisionAcademicaRepositorio
from app.integraciones.almacenamiento import ErrorAlmacenamiento, nombre_seguro
from app.rutas.demo import rol_actual
from app.rutas.paginas import contexto_base, pagina_error, templates
from app.servicios.asignaciones import ResultadoAsignacion, ServicioAsignaciones, TipoAsignacion
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
    comunidad_id = _comunidad_moderador(conexion)
    revisiones = (
        RevisionAcademicaRepositorio(conexion).listar_asignadas(comunidad_id)
        if comunidad_id is not None else []
    )
    contexto.update(
        aportes=AsignacionRevisionRepositorio(conexion).listar_aportes_pendientes(),
        revisiones=revisiones,
        aporte_id=aporte_id,
        asignacion=resultado.asignacion if resultado else None,
        ya_asignado=bool(resultado and resultado.tipo is TipoAsignacion.YA_ASIGNADO),
        sin_revisor=bool(resultado and resultado.tipo is TipoAsignacion.SIN_REVISOR),
    )
    return templates.TemplateResponse(request, "moderacion_aportes.html", contexto)


def _comunidad_moderador(conexion: sqlite3.Connection) -> int | None:
    moderador = CatalogoRepositorio(conexion).obtener_estudiante_por_rol("Moderador")
    return moderador["comunidad_id"] if moderador is not None else None


def _comunidad_autorizada(
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
) -> int:
    if rol_actual(request) != "Moderador":
        raise ErrorRevision(MotivoRevision.COMUNIDAD_NO_AUTORIZADA)
    comunidad_id = _comunidad_moderador(conexion)
    if comunidad_id is None:
        raise ErrorRevision(MotivoRevision.COMUNIDAD_NO_AUTORIZADA)
    return comunidad_id


async def mostrar_error_revision(request: Request, error: ErrorRevision):
    if error.motivo is MotivoRevision.COMUNIDAD_NO_AUTORIZADA:
        return pagina_error(
            request, 403, "Revisión no autorizada",
            "Solo el perfil Moderador de la comunidad responsable puede gestionar esta revisión.",
        )
    if error.motivo is MotivoRevision.NO_ENCONTRADA:
        return pagina_error(
            request, 404, "Versión no encontrada", "El aporte no tiene una versión disponible."
        )
    return pagina_error(
        request, 409, "La acción no está disponible",
        "Comprueba que sea la versión actual, con asignación vigente y en el estado requerido.",
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
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    if rol_actual(request) != "Moderador":
        return _acceso_denegado(request)
    return _panel(request, conexion)


@router.post("/aportes/{aporte_id}/asignar")
def asignar_revision(
    aporte_id: Identificador,
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    if rol_actual(request) != "Moderador":
        return _acceso_denegado(request)

    comunidad_id = _comunidad_moderador(conexion)
    if comunidad_id is None:
        return pagina_error(
            request,
            503,
            "Comunidad de demostración sin configurar",
            "Carga los datos de ejemplo para organizar revisiones.",
        )

    resultado = ServicioAsignaciones(conexion).asignar(aporte_id, comunidad_id)
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


@router.get(BASE_REVISION + "/revision")
def detalle_revision(
    aporte_id: Identificador,
    version_id: Identificador,
    request: Request,
    comunidad_id: int = Depends(_comunidad_autorizada),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    revision = ServicioRevisiones(conexion).consultar(aporte_id, version_id, comunidad_id)
    return _formulario_revision(request, revision)


@router.get(BASE_REVISION + "/archivo")
def archivo_revision(
    aporte_id: Identificador,
    version_id: Identificador,
    request: Request,
    comunidad_id: int = Depends(_comunidad_autorizada),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    revision = ServicioRevisiones(conexion).consultar(aporte_id, version_id, comunidad_id)
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


@router.post(BASE_REVISION + "/revision/iniciar")
def iniciar_revision(
    aporte_id: Identificador,
    version_id: Identificador,
    request: Request,
    comunidad_id: int = Depends(_comunidad_autorizada),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    ServicioRevisiones(conexion).iniciar(aporte_id, version_id, comunidad_id)
    return RedirectResponse(
        request.url_for("detalle_revision", aporte_id=aporte_id, version_id=version_id),
        status_code=303,
    )


@router.post(BASE_REVISION + "/revision/decision")
def decidir_revision(
    aporte_id: Identificador,
    version_id: Identificador,
    request: Request,
    decision: str = Form(""),
    alcance: str = Form(""),
    observaciones: str = Form(""),
    comunidad_id: int = Depends(_comunidad_autorizada),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    servicio = ServicioRevisiones(conexion)
    try:
        resultado = servicio.decidir(
            aporte_id, version_id, comunidad_id, decision, alcance, observaciones
        )
    except DatosRevisionInvalidos as error:
        revision = servicio.consultar(aporte_id, version_id, comunidad_id)
        valores = {"decision": decision, "alcance": alcance, "observaciones": observaciones}
        return _formulario_revision(request, revision, valores, error.errores)

    contexto = contexto_base(request)
    contexto.update(
        mensaje=CONFIRMACIONES[resultado],
        publicada=resultado is DecisionRevision.APROBACION,
    )
    return templates.TemplateResponse(request, "revision_resultado.html", contexto)

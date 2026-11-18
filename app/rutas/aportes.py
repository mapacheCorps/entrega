"""Rutas HTTP para aportes, catálogo y reenvío académico."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Path, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import RedirectResponse

from app.db.conexion import obtener_conexion
from app.dominio.repositorios import AporteRepositorio, CatalogoRepositorio
from app.dominio.revisiones import RevisionAcademicaRepositorio
from app.rutas.demo import rol_actual
from app.rutas.paginas import contexto_base as _contexto_base
from app.rutas.paginas import pagina_error as _error
from app.rutas.paginas import templates
from app.servicios.aportes import Resultado, ServicioAportes, TipoResultado
from app.servicios.validacion import ArchivoSubido

ESTADOS_APORTE = {
    "PendienteAsignacion": "Pendiente de asignación",
    "RequiereCorreccion": "Requiere corrección",
    "Asignado": "Asignado",
    "Publicado": "Publicado",
    "Rechazado": "Rechazado",
    "CorreccionSolicitada": "Corrección solicitada",
}
ESTADOS_VERSION = {
    "Recibida": "Recibida",
    "PendienteRevision": "Pendiente de revisión",
    "RequiereCorreccion": "Requiere corrección",
    "Final": "Final",
    "EnRevision": "En revisión",
    "Aprobada": "Aprobada",
    "Publicada": "Publicada",
    "Rechazada": "Rechazada",
}

router = APIRouter()
Identificador = Annotated[int, Path(ge=1, le=2**63 - 1)]
RUTA_REENVIO = "/aportes/{aporte_id}/versiones/{version_id}/reenviar"


def _catalogos(conexion: sqlite3.Connection) -> dict[str, object]:
    repo = CatalogoRepositorio(conexion)
    return {
        "carreras": [dict(fila) for fila in repo.listar_carreras()],
        "ramos": [dict(fila) for fila in repo.listar_ramos()],
        "periodos": [dict(fila) for fila in repo.listar_periodos()],
        "temas": [dict(fila) for fila in repo.listar_temas()],
    }


def _fecha_legible(valor: str | None) -> str:
    if not valor:
        return "—"
    return valor.replace("T", " ").replace("+00:00", " UTC")


def _detalle(conexion: sqlite3.Connection, aporte_id: int) -> dict[str, object] | None:
    fila = AporteRepositorio(conexion).obtener_detalle(aporte_id)
    if fila is None:
        return None
    datos = dict(fila)
    datos["fecha_envio_legible"] = _fecha_legible(datos.get("fecha_envio"))
    datos["estado_aporte_legible"] = ESTADOS_APORTE.get(
        str(datos.get("estado_aporte")), str(datos.get("estado_aporte"))
    )
    datos["estado_version_legible"] = ESTADOS_VERSION.get(
        str(datos.get("estado_version")), str(datos.get("estado_version"))
    )
    return datos


async def _leer_archivo(archivo: UploadFile | None) -> ArchivoSubido | None:
    if archivo is None or not (archivo.filename or "").strip():
        return None
    contenido = await archivo.read()
    return ArchivoSubido(
        nombre=archivo.filename or "archivo",
        contenido=contenido,
        tipo_mime=archivo.content_type or "application/octet-stream",
    )


def _datos_formulario(
    procedencia: str,
    carrera_id: str,
    ramo_id: str,
    periodo_id: str,
    tema_id: str,
) -> dict[str, str]:
    return {
        "procedencia": procedencia,
        "carrera_id": carrera_id,
        "ramo_id": ramo_id,
        "periodo_id": periodo_id,
        "tema_id": tema_id,
    }


@router.get("/")
def inicio(
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    contexto = _contexto_base(request)
    contexto["total_aportes"] = AporteRepositorio(conexion).contar_aportes()
    return templates.TemplateResponse(request, "inicio.html", contexto)


@router.get("/aportes/nuevo")
def formulario_aporte(
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    contexto = _contexto_base(request)
    contexto.update(_catalogos(conexion))
    contexto.update(
        {
            "valores": {},
            "errores": {},
            "puede_crear": contexto["es_estudiante"],
        }
    )
    return templates.TemplateResponse(request, "aporte_form.html", contexto)


@router.get("/catalogo")
def catalogo(
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    contexto = _contexto_base(request)
    contexto["versiones"] = RevisionAcademicaRepositorio(conexion).listar_publicadas()
    return templates.TemplateResponse(request, "catalogo.html", contexto)


@router.post("/aportes")
async def crear_aporte(
    request: Request,
    procedencia: str = Form(""),
    carrera_id: str = Form(""),
    ramo_id: str = Form(""),
    periodo_id: str = Form(""),
    tema_id: str = Form(""),
    archivo: UploadFile | None = File(None),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    if rol_actual(request) != "Estudiante":
        return _error(
            request,
            403,
            "Acción no disponible para este rol",
            "Solo el perfil de demostración Estudiante puede enviar aportes en esta historia.",
        )

    archivo_subido = await _leer_archivo(archivo)
    datos = _datos_formulario(
        procedencia, carrera_id, ramo_id, periodo_id, tema_id
    )
    servicio = ServicioAportes(conexion, request.app.state.almacenamiento)
    resultado = servicio.enviar(datos, archivo_subido)
    return _responder_envio(request, conexion, datos, resultado)


def _responder_envio(
    request: Request,
    conexion: sqlite3.Connection,
    datos: dict[str, str],
    resultado: Resultado,
):
    if resultado.tipo is TipoResultado.REGISTRADO:
        return RedirectResponse(
            url=f"/aportes/{resultado.aporte_id}", status_code=303
        )

    if resultado.tipo is TipoResultado.DATOS_INVALIDOS:
        contexto = _contexto_base(request)
        contexto.update(_catalogos(conexion))
        contexto.update(
            {
                "valores": datos,
                "errores": resultado.errores,
                "puede_crear": True,
            }
        )
        return templates.TemplateResponse(
            request, "aporte_form.html", contexto, status_code=400
        )

    if resultado.tipo is TipoResultado.ARCHIVO_INVALIDO:
        contexto = _contexto_base(request)
        contexto.update(
            {
                "aporte": _detalle(conexion, resultado.aporte_id or 0),
                "errores_archivo": resultado.errores_archivo,
                "aviso": (
                    "El aporte quedó registrado en RequiereCorreccion. "
                    "Sube un archivo corregido para continuar."
                ),
                "es_duplicado": False,
            }
        )
        return templates.TemplateResponse(
            request, "aporte_detalle.html", contexto, status_code=400
        )

    if resultado.tipo is TipoResultado.DUPLICADO:
        contexto = _contexto_base(request)
        contexto.update(
            {
                "duplicado": resultado.duplicado,
                "mensaje": resultado.mensaje,
            }
        )
        return templates.TemplateResponse(
            request, "duplicado.html", contexto, status_code=409
        )

    contexto = _contexto_base(request)
    contexto.update(_catalogos(conexion))
    contexto.update(
        {
            "valores": datos,
            "errores": {},
            "error_general": resultado.mensaje
            or "No fue posible resguardar el archivo. Intenta nuevamente.",
            "puede_crear": True,
        }
    )
    return templates.TemplateResponse(
        request, "aporte_form.html", contexto, status_code=502
    )


@router.get("/aportes/{aporte_id}")
def detalle_aporte(
    aporte_id: int,
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    aporte = _detalle(conexion, aporte_id)
    if aporte is None:
        return _error(
            request,
            404,
            "Aporte no encontrado",
            "No existe un aporte con el identificador solicitado.",
        )
    contexto = _contexto_base(request)
    contexto.update(
        {
            "aporte": aporte,
            "errores_archivo": [],
            "aviso": None,
            "es_duplicado": False,
        }
    )
    if contexto["es_estudiante"]:
        estudiante = CatalogoRepositorio(conexion).obtener_estudiante_por_rol("Estudiante")
        if estudiante is not None:
            feedback = RevisionAcademicaRepositorio(conexion).listar_feedback_autor(
                aporte_id, estudiante["id"]
            )
            contexto["feedback_academico"] = feedback
            if any(revision["version_id"] == aporte["version_id"] for revision in feedback):
                servicio = ServicioAportes(conexion, request.app.state.almacenamiento)
                contexto["puede_reenviar"] = not isinstance(
                    servicio.consultar_reenvio(aporte_id, aporte["version_id"]), Resultado
                )
    return templates.TemplateResponse(request, "aporte_detalle.html", contexto)


@router.get("/aportes/{aporte_id}/corregir")
def formulario_correccion(
    aporte_id: int,
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    if rol_actual(request) != "Estudiante":
        return _error(
            request,
            403,
            "Acción no disponible para este rol",
            "Solo el perfil de demostración Estudiante puede corregir sus aportes.",
        )

    aporte = _detalle(conexion, aporte_id)
    if aporte is None:
        return _error(
            request,
            404,
            "Aporte no encontrado",
            "No existe un aporte con el identificador solicitado.",
        )

    if aporte["estado_aporte"] != "RequiereCorreccion":
        contexto = _contexto_base(request)
        contexto.update(
            {
                "aporte": aporte,
                "errores_archivo": [],
                "aviso": "Este aporte no está en estado RequiereCorreccion.",
                "es_duplicado": False,
            }
        )
        return templates.TemplateResponse(
            request, "aporte_detalle.html", contexto, status_code=400
        )

    contexto = _contexto_base(request)
    contexto.update(
        {
            "aporte": aporte,
            "errores": {},
            "errores_archivo": [],
            "error_general": None,
        }
    )
    return templates.TemplateResponse(request, "aporte_corregir.html", contexto)


@router.post("/aportes/{aporte_id}/correcciones")
async def corregir_aporte(
    aporte_id: int,
    request: Request,
    archivo: UploadFile | None = File(None),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    if rol_actual(request) != "Estudiante":
        return _error(
            request,
            403,
            "Acción no disponible para este rol",
            "Solo el perfil de demostración Estudiante puede corregir sus aportes.",
        )

    archivo_subido = await _leer_archivo(archivo)
    servicio = ServicioAportes(conexion, request.app.state.almacenamiento)
    resultado = servicio.corregir(aporte_id, archivo_subido)

    if resultado.tipo is TipoResultado.REGISTRADO:
        return RedirectResponse(url=f"/aportes/{aporte_id}", status_code=303)

    if resultado.tipo is TipoResultado.NO_ENCONTRADO:
        return _error(
            request,
            404,
            "Aporte no encontrado",
            "No existe un aporte con el identificador solicitado.",
        )

    if resultado.tipo is TipoResultado.DUPLICADO:
        contexto = _contexto_base(request)
        contexto.update(
            {
                "duplicado": resultado.duplicado,
                "mensaje": resultado.mensaje,
            }
        )
        return templates.TemplateResponse(
            request, "duplicado.html", contexto, status_code=409
        )

    aporte = _detalle(conexion, aporte_id)

    if resultado.tipo is TipoResultado.NO_CORREGIBLE:
        contexto = _contexto_base(request)
        contexto.update(
            {
                "aporte": aporte,
                "errores_archivo": [],
                "aviso": resultado.mensaje,
                "es_duplicado": False,
            }
        )
        return templates.TemplateResponse(
            request, "aporte_detalle.html", contexto, status_code=400
        )

    if resultado.tipo is TipoResultado.ARCHIVO_INVALIDO:
        contexto = _contexto_base(request)
        contexto.update(
            {
                "aporte": aporte,
                "errores_archivo": resultado.errores_archivo,
                "aviso": (
                    "La nueva versión sigue en RequiereCorreccion. "
                    "Puedes intentarlo otra vez."
                ),
                "es_duplicado": False,
            }
        )
        return templates.TemplateResponse(
            request, "aporte_detalle.html", contexto, status_code=400
        )

    if resultado.tipo is TipoResultado.DATOS_INVALIDOS:
        contexto = _contexto_base(request)
        contexto.update(
            {
                "aporte": aporte,
                "errores": resultado.errores,
                "errores_archivo": [],
                "error_general": None,
            }
        )
        return templates.TemplateResponse(
            request, "aporte_corregir.html", contexto, status_code=400
        )

    contexto = _contexto_base(request)
    contexto.update(
        {
            "aporte": aporte,
            "errores": {},
            "errores_archivo": [],
            "error_general": resultado.mensaje
            or "No fue posible resguardar el archivo. Intenta nuevamente.",
        }
    )
    return templates.TemplateResponse(
        request, "aporte_corregir.html", contexto, status_code=502
    )


def _reenvio_no_autorizado(request: Request):
    return _error(
        request, 403, "Reenvío no autorizado",
        "Solo el autor del aporte puede reenviar una versión corregida.",
    )


def _reenvio_no_disponible(request: Request, resultado: Resultado):
    if resultado.tipo is TipoResultado.NO_AUTORIZADO:
        return _reenvio_no_autorizado(request)
    if resultado.tipo is TipoResultado.NO_ENCONTRADO:
        return _error(
            request, 404, "Aporte no encontrado", "No existe un aporte con ese identificador."
        )
    return _error(
        request, 409, "Versión no disponible para reenviar",
        "Abre el detalle del aporte para consultar la versión vigente.",
    )


def _formulario_reenvio(
    request: Request,
    servicio: ServicioAportes,
    aporte_id: int,
    version_id: int,
    resultado: Resultado | None = None,
):
    version = servicio.consultar_reenvio(aporte_id, version_id)
    if isinstance(version, Resultado):
        return _reenvio_no_disponible(request, version)

    feedback = RevisionAcademicaRepositorio(servicio.conexion).listar_feedback_autor(
        aporte_id, servicio.autor["id"]
    )
    contexto = _contexto_base(request)
    contexto.update(
        aporte_id=aporte_id,
        version=version,
        revision=next((fila for fila in feedback if fila["version_id"] == version_id), None),
        resultado=resultado,
    )
    codigos = {
        TipoResultado.ARCHIVO_INVALIDO: 400,
        TipoResultado.DUPLICADO: 409,
        TipoResultado.ERROR_ALMACENAMIENTO: 502,
    }
    codigo = codigos[resultado.tipo] if resultado else 200
    return templates.TemplateResponse(
        request, "aporte_reenviar.html", contexto, status_code=codigo
    )


@router.get(RUTA_REENVIO)
def formulario_reenvio(
    aporte_id: Identificador,
    version_id: Identificador,
    request: Request,
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    if rol_actual(request) != "Estudiante":
        return _reenvio_no_autorizado(request)
    servicio = ServicioAportes(conexion, request.app.state.almacenamiento)
    return _formulario_reenvio(request, servicio, aporte_id, version_id)


@router.post(RUTA_REENVIO)
async def reenviar_aporte(
    aporte_id: Identificador,
    version_id: Identificador,
    request: Request,
    archivo: UploadFile | None = File(None),
    conexion: sqlite3.Connection = Depends(obtener_conexion),
):
    if rol_actual(request) != "Estudiante":
        return _reenvio_no_autorizado(request)
    servicio = ServicioAportes(conexion, request.app.state.almacenamiento)
    archivo_subido = await _leer_archivo(archivo)
    resultado = await run_in_threadpool(servicio.reenviar, aporte_id, version_id, archivo_subido)
    if resultado.tipo is TipoResultado.REGISTRADO:
        return RedirectResponse(url=f"/aportes/{aporte_id}", status_code=303)
    if resultado.tipo in (
        TipoResultado.NO_AUTORIZADO, TipoResultado.NO_ENCONTRADO, TipoResultado.NO_CORREGIBLE,
    ):
        return _reenvio_no_disponible(request, resultado)
    return _formulario_reenvio(request, servicio, aporte_id, version_id, resultado)

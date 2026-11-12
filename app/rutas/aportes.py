"""Rutas HTTP de HU-01: enviar y clasificar un aporte."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db.conexion import obtener_conexion
from app.dominio.repositorios import AporteRepositorio, CatalogoRepositorio
from app.rutas.demo import ROLES_DEMO, rol_actual
from app.servicios.aportes import Resultado, ServicioAportes, TipoResultado
from app.servicios.validacion import ArchivoSubido

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=BASE_DIR / "templates")

ESTADOS_APORTE = {
    "PendienteAsignacion": "Pendiente de asignación",
    "RequiereCorreccion": "Requiere corrección",
}
ESTADOS_VERSION = {
    "Recibida": "Recibida",
    "PendienteRevision": "Pendiente de revisión",
    "RequiereCorreccion": "Requiere corrección",
    "Final": "Final",
}

router = APIRouter()


def _contexto_base(request: Request) -> dict[str, object]:
    rol = rol_actual(request)
    return {
        "request": request,
        "rol_actual": rol,
        "roles_demo": ROLES_DEMO,
        "es_estudiante": rol == "Estudiante",
    }


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


def _tamano_legible(valor: int | None) -> str:
    if valor is None:
        return "—"
    if valor < 1024:
        return f"{valor} B"
    if valor < 1024 * 1024:
        return f"{valor / 1024:.1f} KB"
    return f"{valor / (1024 * 1024):.1f} MB"


def _detalle(conexion: sqlite3.Connection, aporte_id: int) -> dict[str, object] | None:
    fila = AporteRepositorio(conexion).obtener_detalle(aporte_id)
    if fila is None:
        return None
    datos = dict(fila)
    datos["fecha_envio_legible"] = _fecha_legible(datos.get("fecha_envio"))
    datos["fecha_creacion_legible"] = _fecha_legible(datos.get("fecha_creacion"))
    datos["tamano_legible"] = _tamano_legible(datos.get("tamano_bytes"))
    datos["estado_aporte_legible"] = ESTADOS_APORTE.get(
        str(datos.get("estado_aporte")), str(datos.get("estado_aporte"))
    )
    datos["estado_version_legible"] = ESTADOS_VERSION.get(
        str(datos.get("estado_version")), str(datos.get("estado_version"))
    )
    return datos


def _error(
    request: Request,
    codigo: int,
    titulo: str,
    mensaje: str,
):
    contexto = _contexto_base(request)
    contexto.update({"codigo": codigo, "titulo": titulo, "mensaje": mensaje})
    return templates.TemplateResponse(
        request, "error.html", contexto, status_code=codigo
    )


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

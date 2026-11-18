"""Contexto compartido para las páginas de la aplicación."""

from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.rutas.demo import ROLES_DEMO, rol_actual

templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")


def contexto_base(request: Request) -> dict[str, object]:
    rol = rol_actual(request)
    return {
        "request": request,
        "rol_actual": rol,
        "roles_demo": ROLES_DEMO,
        "es_estudiante": rol == "Estudiante",
    }


def pagina_error(request: Request, codigo: int, titulo: str, mensaje: str):
    contexto = contexto_base(request)
    contexto.update({"codigo": codigo, "titulo": titulo, "mensaje": mensaje})
    return templates.TemplateResponse(
        request, "error.html", contexto, status_code=codigo
    )

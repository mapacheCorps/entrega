"""Selector de rol de demostración, sin autenticación real."""

from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

ROLES_DEMO = ["Estudiante", "Moderador"]
COOKIE_ROL = "demo_role"
ROL_POR_DEFECTO = "Estudiante"

router = APIRouter()


def rol_actual(request: Request) -> str:
    rol = request.cookies.get(COOKIE_ROL)
    return rol if rol in ROLES_DEMO else ROL_POR_DEFECTO


@router.post("/demo/rol")
def cambiar_rol(rol: str = Form(...)):
    if rol not in ROLES_DEMO:
        raise HTTPException(status_code=400, detail="Rol de demostración no válido")
    respuesta = RedirectResponse(url="/", status_code=303)
    respuesta.set_cookie(
        COOKIE_ROL,
        rol,
        max_age=8 * 60 * 60,
        httponly=True,
        samesite="lax",
    )
    return respuesta

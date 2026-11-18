"""Punto de entrada de la aplicación FastAPI."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db.conexion import aplicar_migraciones, conectar, ruta_db_por_defecto
from app.integraciones.almacenamiento import (
    AlmacenamientoArchivos,
    AlmacenamientoConFallo,
    AlmacenamientoLocal,
)
from app.rutas import aportes, demo, moderacion

BASE_DIR = Path(__file__).resolve().parent


def create_app(
    db_path: str | Path | None = None,
    almacenamiento: AlmacenamientoArchivos | None = None,
) -> FastAPI:
    ruta = Path(db_path) if db_path is not None else ruta_db_por_defecto()

    conexion = conectar(ruta)
    try:
        aplicar_migraciones(conexion)
    finally:
        conexion.close()

    aplicacion = FastAPI(title="Torpedos universitarios")
    aplicacion.state.db_path = str(ruta)
    if almacenamiento is not None:
        aplicacion.state.almacenamiento = almacenamiento
    elif os.environ.get("APP_SIMULAR_FALLO_ALMACENAMIENTO") == "1":
        aplicacion.state.almacenamiento = AlmacenamientoConFallo(
            ruta.parent / "archivos"
        )
    else:
        aplicacion.state.almacenamiento = AlmacenamientoLocal(ruta.parent / "archivos")

    aplicacion.mount(
        "/static", StaticFiles(directory=BASE_DIR / "static"), name="static"
    )
    aplicacion.include_router(demo.router)
    aplicacion.include_router(aportes.router)
    aplicacion.include_router(moderacion.router)
    return aplicacion


app = create_app()

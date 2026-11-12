"""Adaptador simulado del servicio externo de almacenamiento."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

from app.servicios.validacion import ArchivoSubido


class ErrorAlmacenamiento(Exception):
    """El servicio de almacenamiento no pudo resguardar o eliminar el archivo."""


class AlmacenamientoArchivos(Protocol):
    def guardar(
        self, archivo: ArchivoSubido, aporte_id: int, version_id: int
    ) -> str: ...

    def eliminar(self, referencia: str) -> None: ...


def nombre_seguro(nombre: str) -> str:
    """Reduce el nombre a un archivo simple, sin rutas ni caracteres peligrosos."""
    base = Path(nombre).name.strip().replace("\\", "_")
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
    base = base.strip("._-")
    return base or "archivo"


class AlmacenamientoLocal:
    """Simulación local del servicio de almacenamiento."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)

    def guardar(
        self, archivo: ArchivoSubido, aporte_id: int, version_id: int
    ) -> str:
        try:
            carpeta = self.base_dir / str(aporte_id)
            carpeta.mkdir(parents=True, exist_ok=True)
            destino = carpeta / f"{version_id}_{nombre_seguro(archivo.nombre)}"
            destino.write_bytes(archivo.contenido)
            return destino.relative_to(self.base_dir).as_posix()
        except OSError as exc:
            raise ErrorAlmacenamiento(
                "El servicio de almacenamiento no pudo resguardar el archivo."
            ) from exc

    def eliminar(self, referencia: str) -> None:
        try:
            base = self.base_dir.resolve()
            ruta = (base / referencia).resolve()
            if base not in ruta.parents:
                return
            ruta.unlink(missing_ok=True)
            carpeta = ruta.parent
            if carpeta != base and not any(carpeta.iterdir()):
                carpeta.rmdir()
        except OSError as exc:
            raise ErrorAlmacenamiento(
                "El servicio de almacenamiento no pudo eliminar el archivo."
            ) from exc


class AlmacenamientoConFallo(AlmacenamientoLocal):
    """Variante de demostración que siempre falla al guardar.

    Se activa con APP_SIMULAR_FALLO_ALMACENAMIENTO=1 para recorrer el camino
    de error de DSS-01 sin integrar un proveedor real.
    """

    def guardar(
        self, archivo: ArchivoSubido, aporte_id: int, version_id: int
    ) -> str:
        raise ErrorAlmacenamiento(
            "Fallo simulado del almacenamiento. No se confirmó el registro."
        )

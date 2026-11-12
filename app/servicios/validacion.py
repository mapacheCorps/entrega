"""Reglas de validación de datos y archivos de un aporte."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path

MAX_BYTES = 10 * 1024 * 1024
EXTENSIONES_PERMITIDAS = {".pdf", ".docx", ".pptx", ".png", ".jpg"}
EXTENSIONES_TEXTO = ", ".join(sorted(EXTENSIONES_PERMITIDAS))


@dataclass(frozen=True)
class ArchivoSubido:
    nombre: str
    contenido: bytes
    tipo_mime: str = "application/octet-stream"


def entero(valor: object) -> int | None:
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        return None


def validar_datos(
    conexion: sqlite3.Connection,
    datos: dict[str, object],
    *,
    archivo_presente: bool,
) -> dict[str, str]:
    """Devuelve un error por cada campo obligatorio o relación incoherente."""
    errores: dict[str, str] = {}

    procedencia = str(datos.get("procedencia") or "").strip()
    if not procedencia:
        errores["procedencia"] = "Declara la procedencia del apunte."
    elif len(procedencia) > 500:
        errores["procedencia"] = "La procedencia no puede superar los 500 caracteres."

    carrera_id = entero(datos.get("carrera_id"))
    ramo_id = entero(datos.get("ramo_id"))
    periodo_id = entero(datos.get("periodo_id"))
    tema_id = entero(datos.get("tema_id"))

    if carrera_id is None:
        errores["carrera_id"] = "Selecciona una carrera."
    if ramo_id is None:
        errores["ramo_id"] = "Selecciona un ramo."
    if periodo_id is None:
        errores["periodo_id"] = "Selecciona un período académico."
    if tema_id is None:
        errores["tema_id"] = "Selecciona un tema."
    if not archivo_presente:
        errores["archivo"] = "Adjunta el archivo del apunte."

    carrera = None
    ramo = None
    tema = None

    if carrera_id is not None:
        carrera = conexion.execute(
            "SELECT id FROM carreras WHERE id = ?", (carrera_id,)
        ).fetchone()
        if carrera is None:
            errores["carrera_id"] = "La carrera seleccionada no existe."

    if ramo_id is not None:
        ramo = conexion.execute(
            "SELECT id, carrera_id FROM ramos WHERE id = ?", (ramo_id,)
        ).fetchone()
        if ramo is None:
            errores["ramo_id"] = "El ramo seleccionado no existe."
        elif carrera_id is not None and ramo["carrera_id"] != carrera_id:
            errores["ramo_id"] = "El ramo no pertenece a la carrera seleccionada."

    if periodo_id is not None:
        periodo = conexion.execute(
            "SELECT id FROM periodos_academicos WHERE id = ?", (periodo_id,)
        ).fetchone()
        if periodo is None:
            errores["periodo_id"] = "El período académico seleccionado no existe."

    if tema_id is not None:
        tema = conexion.execute(
            "SELECT id, ramo_id FROM temas_unidad WHERE id = ?", (tema_id,)
        ).fetchone()
        if tema is None:
            errores["tema_id"] = "El tema seleccionado no existe."
        elif ramo_id is not None and tema["ramo_id"] != ramo_id:
            errores["tema_id"] = "El tema no pertenece al ramo seleccionado."

    return errores


def validar_archivo(archivo: ArchivoSubido | None) -> list[str]:
    """Devuelve las observaciones del archivo; lista vacía si cumple las reglas."""
    if archivo is None:
        return ["Adjunta el archivo del apunte."]

    errores: list[str] = []
    if not archivo.nombre.strip():
        errores.append("El archivo no tiene un nombre válido.")

    if not archivo.contenido:
        errores.append("El archivo está vacío.")

    extension = Path(archivo.nombre).suffix.lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        errores.append(
            f"El formato del archivo no está permitido. Usa {EXTENSIONES_TEXTO}."
        )

    if len(archivo.contenido) > MAX_BYTES:
        errores.append("El archivo supera el tamaño máximo de 10 MB.")

    return errores


def calcular_hash(contenido: bytes) -> str:
    return hashlib.sha256(contenido).hexdigest()

"""Envío de aportes y sus correcciones (HU-01 y HU-04)."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from app.dominio.entidades import DecisionRevision, EstadoAporte, EstadoVersion
from app.dominio.repositorios import AporteRepositorio, CatalogoRepositorio
from app.dominio.revisiones import RevisionAcademicaRepositorio
from app.integraciones.almacenamiento import (
    AlmacenamientoArchivos,
    ErrorAlmacenamiento,
)
from app.servicios.validacion import (
    ArchivoSubido,
    calcular_hash,
    entero,
    validar_archivo,
    validar_datos,
)

logger = logging.getLogger(__name__)


class TipoResultado(str, Enum):
    REGISTRADO = "registrado"
    DATOS_INVALIDOS = "datos_invalidos"
    ARCHIVO_INVALIDO = "archivo_invalido"
    DUPLICADO = "duplicado"
    ERROR_ALMACENAMIENTO = "error_almacenamiento"
    NO_ENCONTRADO = "no_encontrado"
    NO_CORREGIBLE = "no_corregible"
    NO_AUTORIZADO = "no_autorizado"


DECISIONES_REENVIABLES = {
    EstadoAporte.RECHAZADO: (EstadoVersion.RECHAZADA, DecisionRevision.RECHAZO),
    EstadoAporte.CORRECCION_SOLICITADA: (
        EstadoVersion.REQUIERE_CORRECCION, DecisionRevision.SOLICITUD_CORRECCION,
    ),
}


@dataclass
class Resultado:
    tipo: TipoResultado
    aporte_id: int | None = None
    errores: dict[str, str] = field(default_factory=dict)
    errores_archivo: list[str] = field(default_factory=list)
    duplicado: dict[str, object] | None = None
    mensaje: str | None = None


def _ahora() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class ServicioAportes:
    def __init__(
        self,
        conexion: sqlite3.Connection,
        almacenamiento: AlmacenamientoArchivos,
        *,
        rol_autor: str = "Estudiante",
    ):
        self.conexion = conexion
        self.almacenamiento = almacenamiento
        self.catalogos = CatalogoRepositorio(conexion)
        self.repo = AporteRepositorio(conexion)
        self.autor = self.catalogos.obtener_estudiante_por_rol(rol_autor)
        if self.autor is None:
            raise RuntimeError(
                f"No existe el perfil de demostración «{rol_autor}». Ejecuta el seed."
            )

    # ------------------------------------------------------------------
    # Envío inicial
    # ------------------------------------------------------------------

    def enviar(
        self, datos: dict[str, object], archivo: ArchivoSubido | None
    ) -> Resultado:
        errores = validar_datos(
            self.conexion, datos, archivo_presente=archivo is not None
        )
        if errores:
            return Resultado(TipoResultado.DATOS_INVALIDOS, errores=errores)

        errores_archivo = validar_archivo(archivo)
        if errores_archivo:
            aporte_id = self._crear_aporte_invalido(datos, archivo)  # type: ignore[arg-type]
            return Resultado(
                TipoResultado.ARCHIVO_INVALIDO,
                aporte_id=aporte_id,
                errores_archivo=errores_archivo,
            )

        assert archivo is not None
        hash_archivo = calcular_hash(archivo.contenido)
        existente = self.repo.buscar_version_por_hash(hash_archivo)
        if existente is not None:
            return Resultado(
                TipoResultado.DUPLICADO,
                duplicado=dict(existente),
                mensaje=(
                    "Ya existe un archivo idéntico registrado. La coincidencia "
                    "no es una aprobación académica."
                ),
            )

        aporte_id = self.repo.siguiente_id("aportes")
        version_id = self.repo.siguiente_id("versiones_apunte")
        try:
            referencia = self.almacenamiento.guardar(archivo, aporte_id, version_id)
        except ErrorAlmacenamiento as exc:
            return Resultado(
                TipoResultado.ERROR_ALMACENAMIENTO,
                mensaje=str(exc),
            )

        try:
            self.repo.crear_aporte_con_version(
                aporte_id=aporte_id,
                autor_id=int(self.autor["id"]),
                ramo_id=entero(datos.get("ramo_id")) or 0,
                periodo_id=entero(datos.get("periodo_id")) or 0,
                tema_id=entero(datos.get("tema_id")) or 0,
                procedencia=str(datos.get("procedencia") or "").strip(),
                fecha_envio=_ahora(),
                estado_aporte=EstadoAporte.PENDIENTE_ASIGNACION.value,
                version_id=version_id,
                nombre_archivo=archivo.nombre,
                referencia_archivo=referencia,
                hash_archivo=hash_archivo,
                tamano_bytes=len(archivo.contenido),
                tipo_mime=archivo.tipo_mime,
                estado_version=EstadoVersion.PENDIENTE_REVISION.value,
                fecha_creacion=_ahora(),
            )
        except Exception:
            logger.exception("Falló el registro del aporte; se compensa el archivo")
            self._eliminar_sin_fallar(referencia)
            return Resultado(
                TipoResultado.ERROR_ALMACENAMIENTO,
                mensaje=(
                    "No fue posible confirmar el registro del aporte. "
                    "Intenta enviarlo nuevamente."
                ),
            )

        return Resultado(TipoResultado.REGISTRADO, aporte_id=aporte_id)

    def _crear_aporte_invalido(
        self, datos: dict[str, object], archivo: ArchivoSubido
    ) -> int:
        aporte_id = self.repo.siguiente_id("aportes")
        version_id = self.repo.siguiente_id("versiones_apunte")
        self.repo.crear_aporte_con_version(
            aporte_id=aporte_id,
            autor_id=int(self.autor["id"]),
            ramo_id=entero(datos.get("ramo_id")) or 0,
            periodo_id=entero(datos.get("periodo_id")) or 0,
            tema_id=entero(datos.get("tema_id")) or 0,
            procedencia=str(datos.get("procedencia") or "").strip(),
            fecha_envio=_ahora(),
            estado_aporte=EstadoAporte.REQUIERE_CORRECCION.value,
            version_id=version_id,
            nombre_archivo=archivo.nombre or "archivo",
            referencia_archivo=None,
            hash_archivo=None,
            tamano_bytes=len(archivo.contenido),
            tipo_mime=archivo.tipo_mime,
            estado_version=EstadoVersion.REQUIERE_CORRECCION.value,
            fecha_creacion=_ahora(),
        )
        return aporte_id

    # ------------------------------------------------------------------
    # Corrección de un archivo inválido
    # ------------------------------------------------------------------

    def corregir(
        self, aporte_id: int, archivo: ArchivoSubido | None
    ) -> Resultado:
        aporte = self.repo.obtener_aporte(aporte_id)
        if aporte is None:
            return Resultado(TipoResultado.NO_ENCONTRADO)

        if aporte["estado"] != EstadoAporte.REQUIERE_CORRECCION.value:
            return Resultado(
                TipoResultado.NO_CORREGIBLE,
                aporte_id=aporte_id,
                mensaje="El aporte no está en estado RequiereCorreccion.",
            )

        version_anterior = self.repo.obtener_ultima_version(aporte_id)
        if version_anterior is None:
            return Resultado(TipoResultado.NO_CORREGIBLE, aporte_id=aporte_id)

        if archivo is None:
            return Resultado(
                TipoResultado.DATOS_INVALIDOS,
                aporte_id=aporte_id,
                errores={"archivo": "Adjunta un archivo corregido."},
            )

        numero = int(version_anterior["numero"]) + 1
        errores_archivo = validar_archivo(archivo)
        if errores_archivo:
            self._registrar_correccion(
                aporte_id=aporte_id,
                version_anterior_id=int(version_anterior["id"]),
                numero=numero,
                archivo=archivo,
                referencia=None,
                hash_archivo=None,
                estado_version=EstadoVersion.REQUIERE_CORRECCION.value,
                estado_aporte=EstadoAporte.REQUIERE_CORRECCION.value,
            )
            return Resultado(
                TipoResultado.ARCHIVO_INVALIDO,
                aporte_id=aporte_id,
                errores_archivo=errores_archivo,
            )

        hash_archivo = calcular_hash(archivo.contenido)
        existente = self.repo.buscar_version_por_hash(hash_archivo)
        if existente is not None:
            return Resultado(
                TipoResultado.DUPLICADO,
                aporte_id=aporte_id,
                duplicado=dict(existente),
                mensaje=(
                    "Ya existe un archivo idéntico registrado. La coincidencia "
                    "no es una aprobación académica."
                ),
            )

        nueva_version_id = self.repo.siguiente_id("versiones_apunte")
        try:
            referencia = self.almacenamiento.guardar(
                archivo, aporte_id, nueva_version_id
            )
        except ErrorAlmacenamiento as exc:
            return Resultado(
                TipoResultado.ERROR_ALMACENAMIENTO,
                aporte_id=aporte_id,
                mensaje=str(exc),
            )

        try:
            self._registrar_correccion(
                aporte_id=aporte_id,
                version_anterior_id=int(version_anterior["id"]),
                numero=numero,
                archivo=archivo,
                referencia=referencia,
                hash_archivo=hash_archivo,
                estado_version=EstadoVersion.PENDIENTE_REVISION.value,
                estado_aporte=EstadoAporte.PENDIENTE_ASIGNACION.value,
                nueva_version_id=nueva_version_id,
            )
        except Exception:
            logger.exception(
                "Falló el registro de la versión corregida; se compensa el archivo"
            )
            self._eliminar_sin_fallar(referencia)
            return Resultado(
                TipoResultado.ERROR_ALMACENAMIENTO,
                aporte_id=aporte_id,
                mensaje=(
                    "No fue posible confirmar la corrección del aporte. "
                    "Intenta enviarla nuevamente."
                ),
            )

        return Resultado(TipoResultado.REGISTRADO, aporte_id=aporte_id)

    def consultar_reenvio(
        self, aporte_id: int, version_id: int
    ) -> sqlite3.Row | Resultado:
        aporte = self.repo.obtener_aporte(aporte_id)
        if aporte is None:
            return Resultado(TipoResultado.NO_ENCONTRADO, aporte_id=aporte_id)
        if self.autor["rol"] != "Estudiante" or aporte["autor_id"] != self.autor["id"]:
            return Resultado(TipoResultado.NO_AUTORIZADO, aporte_id=aporte_id)

        version = self.repo.obtener_ultima_version(aporte_id)
        requerida = DECISIONES_REENVIABLES.get(aporte["estado"])
        if (
            version is None or version["id"] != version_id
            or requerida is None or version["estado"] != requerida[0]
            or RevisionAcademicaRepositorio(self.conexion).obtener_decision(version_id)
            != requerida[1]
        ):
            return Resultado(
                TipoResultado.NO_CORREGIBLE,
                aporte_id=aporte_id,
                mensaje="Esta versión ya no está disponible para reenviar.",
            )
        return version

    def reenviar(
        self, aporte_id: int, version_id: int, archivo: ArchivoSubido | None
    ) -> Resultado:
        errores = validar_archivo(archivo)
        try:
            with self.conexion:
                self.conexion.execute("BEGIN IMMEDIATE")
                version = self.consultar_reenvio(aporte_id, version_id)
                if isinstance(version, Resultado):
                    return version
                if errores:
                    return Resultado(
                        TipoResultado.ARCHIVO_INVALIDO,
                        aporte_id=aporte_id,
                        errores_archivo=errores,
                    )

                assert archivo is not None
                huella = calcular_hash(archivo.contenido)
                if self.repo.buscar_version_por_hash(huella) is not None:
                    return Resultado(
                        TipoResultado.DUPLICADO,
                        aporte_id=aporte_id,
                        mensaje="Ya existe un archivo idéntico registrado. Adjunta una versión corregida.",
                    )

                nueva_version_id = self.repo.siguiente_id("versiones_apunte")
                referencia = self.almacenamiento.guardar(archivo, aporte_id, nueva_version_id)
                try:
                    self._registrar_correccion(
                        aporte_id=aporte_id,
                        version_anterior_id=version_id,
                        numero=version["numero"] + 1,
                        archivo=archivo,
                        referencia=referencia,
                        hash_archivo=huella,
                        estado_version=EstadoVersion.PENDIENTE_REVISION.value,
                        estado_aporte=EstadoAporte.PENDIENTE_ASIGNACION.value,
                        nueva_version_id=nueva_version_id,
                        confirmar=False,
                    )
                    self.conexion.commit()
                except Exception:
                    self._eliminar_sin_fallar(referencia)
                    raise
        except ErrorAlmacenamiento as exc:
            return Resultado(
                TipoResultado.ERROR_ALMACENAMIENTO, aporte_id=aporte_id, mensaje=str(exc)
            )
        except sqlite3.Error:
            logger.exception("Falló el registro del reenvío académico")
            return Resultado(
                TipoResultado.ERROR_ALMACENAMIENTO,
                aporte_id=aporte_id,
                mensaje="No fue posible confirmar el reenvío. Intenta nuevamente.",
            )
        return Resultado(TipoResultado.REGISTRADO, aporte_id=aporte_id)

    def _registrar_correccion(
        self,
        *,
        aporte_id: int,
        version_anterior_id: int,
        numero: int,
        archivo: ArchivoSubido,
        referencia: str | None,
        hash_archivo: str | None,
        estado_version: str,
        estado_aporte: str,
        nueva_version_id: int | None = None,
        confirmar: bool = True,
    ) -> None:
        if nueva_version_id is None:
            nueva_version_id = self.repo.siguiente_id("versiones_apunte")
        self.repo.crear_version_corregida(
            aporte_id=aporte_id,
            version_anterior_id=version_anterior_id,
            nueva_version_id=nueva_version_id,
            numero=numero,
            nombre_archivo=archivo.nombre or "archivo",
            referencia_archivo=referencia,
            hash_archivo=hash_archivo,
            tamano_bytes=len(archivo.contenido),
            tipo_mime=archivo.tipo_mime,
            estado_version=estado_version,
            estado_aporte=estado_aporte,
            fecha_creacion=_ahora(),
            confirmar=confirmar,
        )

    def _eliminar_sin_fallar(self, referencia: str) -> None:
        try:
            self.almacenamiento.eliminar(referencia)
        except ErrorAlmacenamiento:
            logger.exception("No se pudo eliminar el archivo huérfano %s", referencia)

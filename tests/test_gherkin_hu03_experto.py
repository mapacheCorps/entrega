"""Pruebas Gherkin para HU-03: revisión por Experto (cuatro nuevos escenarios)."""

from __future__ import annotations

from contextlib import closing
import sqlite3

import pytest

from app.db.conexion import conectar
from app.dominio.entidades import DecisionRevision, EstadoAporte, EstadoVersion, TipoRevisor
from app.servicios.aportes import ServicioAportes
from app.servicios.revisiones import (
    DatosRevisionInvalidos,
    ErrorRevision,
    MotivoRevision,
    ServicioRevisiones,
)
from tests.conftest import archivo_pdf, datos_aporte


@pytest.fixture
def version_para_experto(ruta_db, almacenamiento, catalogos):
    """Crea un aporte con versión en PendienteRevision para derivar a experto."""
    with closing(conectar(ruta_db)) as conexion:
        aporte_id = ServicioAportes(conexion, almacenamiento).enviar(
            datos_aporte(catalogos), archivo_pdf()
        ).aporte_id
        version_id = conexion.execute(
            "SELECT id FROM versiones_apunte WHERE aporte_id = ?", (aporte_id,)
        ).fetchone()[0]
        # Buscar experto de prueba y adaptar a la estructura que espera el servicio
        experto_row = conexion.execute(
            "SELECT * FROM expertos ORDER BY id LIMIT 1"
        ).fetchone()
        if experto_row:
            # Adaptar a la estructura que espera el servicio (rol, experto_id)
            experto = dict(experto_row)
            experto["rol"] = "Experto"
            experto["experto_id"] = experto["id"]
        else:
            experto = None
    return aporte_id, version_id, experto


def test_solicitud_experto(ruta_db, almacenamiento, catalogos):
    """Escenario: Solicitud de revisión por Experto para materia especializada."""
    with closing(conectar(ruta_db)) as conexion:
        aporte_id = ServicioAportes(conexion, almacenamiento).enviar(
            datos_aporte(catalogos), archivo_pdf()
        ).aporte_id
        version_id = conexion.execute(
            "SELECT id FROM versiones_apunte WHERE aporte_id = ?", (aporte_id,)
        ).fetchone()[0]

        moderador = conexion.execute(
            "SELECT * FROM estudiantes WHERE rol = 'Moderador'"
        ).fetchone()
        servicio = ServicioRevisiones(conexion)
        servicio.solicitar_revision_experto(aporte_id, version_id, moderador, "Física Cuántica")

        # Verificar transición a EnRevisionExperto
        estado = conexion.execute(
            "SELECT estado FROM versiones_apunte WHERE id = ?", (version_id,)
        ).fetchone()[0]
        assert estado == "EnRevisionExperto"

        # Verificar que no se creó revisión académica aún (solo cambia estado)
        rev = conexion.execute(
            "SELECT * FROM revisiones_academicas WHERE version_id = ?", (version_id,)
        ).fetchone()
        assert rev is None


def test_aprobacion_experto(ruta_db, version_para_experto):
    """Escenario: Aprobación de versión revisada por Experto."""
    aporte_id, version_id, experto = version_para_experto

    with closing(conectar(ruta_db)) as conexion:
        moderador = conexion.execute(
            "SELECT * FROM estudiantes WHERE rol = 'Moderador'"
        ).fetchone()
        servicio = ServicioRevisiones(conexion)

        # Primero derivar a experto
        servicio.solicitar_revision_experto(aporte_id, version_id, moderador, "Física Cuántica")

        # Experto evalúa y aprueba
        resultado = servicio.evaluar_por_experto(
            aporte_id, version_id, experto,
            "Aprobacion", "Contenido correcto y completo", "Aprobado sin observaciones"
        )

    assert resultado == DecisionRevision.APROBACION

    with closing(conectar(ruta_db)) as conexion:
        # Verificar versión pública
        estado_version = conexion.execute(
            "SELECT estado FROM versiones_apunte WHERE id = ?", (version_id,)
        ).fetchone()[0]
        assert estado_version == "Publicada"

        estado_aporte = conexion.execute(
            "SELECT estado FROM aportes WHERE id = ?", (aporte_id,)
        ).fetchone()[0]
        assert estado_aporte == "Publicado"

        # Verificar revisión académica con tipo_revisor = experto
        rev = conexion.execute(
            "SELECT * FROM revisiones_academicas WHERE version_id = ?", (version_id,)
        ).fetchone()
        assert rev is not None
        assert rev["tipo_revisor"] == "experto"
        assert rev["experto_id"] is not None
        assert rev["decision"] == "Aprobacion"
        assert rev["especialidad_registrada"] is not None


def test_rechazo_experto(ruta_db, version_para_experto):
    """Escenario: Rechazo por Experto."""
    aporte_id, version_id, experto = version_para_experto

    with closing(conectar(ruta_db)) as conexion:
        moderador = conexion.execute(
            "SELECT * FROM estudiantes WHERE rol = 'Moderador'"
        ).fetchone()
        servicio = ServicioRevisiones(conexion)
        servicio.solicitar_revision_experto(aporte_id, version_id, moderador, "Cálculo Avanzado")

        resultado = servicio.evaluar_por_experto(
            aporte_id, version_id, experto,
            "Rechazo", "Contenido con errores conceptuales", "Error en la demostración del teorema"
        )

    assert resultado == DecisionRevision.RECHAZO

    with closing(conectar(ruta_db)) as conexion:
        estado_version = conexion.execute(
            "SELECT estado FROM versiones_apunte WHERE id = ?", (version_id,)
        ).fetchone()[0]
        assert estado_version == "Rechazada"

        estado_aporte = conexion.execute(
            "SELECT estado FROM aportes WHERE id = ?", (aporte_id,)
        ).fetchone()[0]
        assert estado_aporte == "Rechazado"

        rev = conexion.execute(
            "SELECT * FROM revisiones_academicas WHERE version_id = ?", (version_id,)
        ).fetchone()
        assert rev["tipo_revisor"] == "experto"
        assert rev["decision"] == "Rechazo"


def test_correccion_experto(ruta_db, version_para_experto):
    """Escenario: Solicitud de corrección por Experto."""
    aporte_id, version_id, experto = version_para_experto

    with closing(conectar(ruta_db)) as conexion:
        moderador = conexion.execute(
            "SELECT * FROM estudiantes WHERE rol = 'Moderador'"
        ).fetchone()
        servicio = ServicioRevisiones(conexion)
        servicio.solicitar_revision_experto(aporte_id, version_id, moderador, "Estructuras de Datos")

        resultado = servicio.evaluar_por_experto(
            aporte_id, version_id, experto,
            "SolicitudCorreccion", "Falta explicación del algoritmo", "Añadir complejidad temporal"
        )

    assert resultado == DecisionRevision.SOLICITUD_CORRECCION

    with closing(conectar(ruta_db)) as conexion:
        estado_version = conexion.execute(
            "SELECT estado FROM versiones_apunte WHERE id = ?", (version_id,)
        ).fetchone()[0]
        assert estado_version == "RequiereCorreccion"

        estado_aporte = conexion.execute(
            "SELECT estado FROM aportes WHERE id = ?", (aporte_id,)
        ).fetchone()[0]
        assert estado_aporte == "CorreccionSolicitada"

        rev = conexion.execute(
            "SELECT * FROM revisiones_academicas WHERE version_id = ?", (version_id,)
        ).fetchone()
        assert rev["tipo_revisor"] == "experto"
        assert rev["decision"] == "SolicitudCorreccion"


def test_intento_no_autorizado_experto(ruta_db, version_para_experto):
    """Escenario: Intento no autorizado (incluye Experto)."""
    aporte_id, version_id, experto = version_para_experto

    with closing(conectar(ruta_db)) as conexion:
        moderador = conexion.execute(
            "SELECT * FROM estudiantes WHERE rol = 'Moderador'"
        ).fetchone()
        servicio = ServicioRevisiones(conexion)
        servicio.solicitar_revision_experto(aporte_id, version_id, moderador, "Física Cuántica")

        # Estudiante sin rol intenta evaluar como experto
        estudiante = conexion.execute(
            "SELECT * FROM estudiantes WHERE rol = 'Estudiante'"
        ).fetchone()
        # Forzar rol experto sin experto_id
        estudiante_fake = dict(estudiante)
        estudiante_fake["rol"] = "Experto"
        estudiante_fake["experto_id"] = None

        with pytest.raises(ErrorRevision) as error:
            servicio.evaluar_por_experto(
                aporte_id, version_id, estudiante_fake,
                "Aprobacion", "test", "test"
            )
        assert error.value.motivo is MotivoRevision.EXPERTO_NO_AUTORIZADO


def test_decisiones_simultaneas_comunidad_experto(ruta_db, version_para_experto):
    """Escenario: Decisiones simultáneas Comunidad + Experto (primera gana)."""
    aporte_id, version_id, experto = version_para_experto

    with closing(conectar(ruta_db)) as conexion:
        moderador = conexion.execute(
            "SELECT * FROM estudiantes WHERE rol = 'Moderador'"
        ).fetchone()
        servicio = ServicioRevisiones(conexion)
        servicio.solicitar_revision_experto(aporte_id, version_id, moderador, "Física Cuántica")

    # Primera decisión: Experto aprueba
    with closing(conectar(ruta_db)) as conexion:
        servicio = ServicioRevisiones(conexion)
        resultado1 = servicio.evaluar_por_experto(
            aporte_id, version_id, experto,
            "Aprobacion", "test", "test"
        )
    assert resultado1 == DecisionRevision.APROBACION

    # Segunda decisión: Comunidad intenta decidir sobre versión ya resuelta
    with closing(conectar(ruta_db)) as conexion:
        moderador = conexion.execute(
            "SELECT * FROM estudiantes WHERE rol = 'Moderador'"
        ).fetchone()
        servicio = ServicioRevisiones(conexion)
        with pytest.raises(ErrorRevision) as error:
            servicio.decidir(aporte_id, version_id, moderador,
                           "Rechazo", "test", "test")
        assert error.value.motivo is MotivoRevision.YA_RESUELTA
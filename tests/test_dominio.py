from __future__ import annotations

from datetime import datetime, timezone

from app.dominio.entidades import (
    Aporte,
    EstadoAporte,
    EstadoVersion,
    VersionApunte,
)


def test_aporte_nuevo_queda_pendiente_de_asignacion():
    aporte = Aporte(
        id=None,
        autor_id=1,
        ramo_id=1,
        periodo_id=1,
        tema_id=1,
        procedencia="Apuntes propios",
        fecha_envio=datetime.now(timezone.utc),
    )
    assert aporte.estado is EstadoAporte.PENDIENTE_ASIGNACION
    assert aporte.esta_pendiente()
    assert not aporte.requiere_correccion()


def test_aporte_puede_pasar_a_requiere_correccion():
    aporte = Aporte(
        id=1,
        autor_id=1,
        ramo_id=1,
        periodo_id=1,
        tema_id=1,
        procedencia="Apuntes propios",
        fecha_envio=datetime.now(timezone.utc),
        estado=EstadoAporte.REQUIERE_CORRECCION,
    )
    assert aporte.requiere_correccion()
    assert not aporte.esta_pendiente()


def test_version_apunte_recorre_sus_estados():
    version = VersionApunte(
        id=None,
        aporte_id=1,
        numero=1,
        nombre_archivo="apunte.pdf",
    )
    assert version.estado is EstadoVersion.RECIBIDA
    assert version.fue_recibida()

    version.estado = EstadoVersion.PENDIENTE_REVISION
    assert version.esta_pendiente_de_revision()

    version.estado = EstadoVersion.REQUIERE_CORRECCION
    assert version.requiere_correccion()

    version.estado = EstadoVersion.FINAL
    assert version.esta_final()

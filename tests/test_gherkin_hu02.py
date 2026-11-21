from contextlib import closing

import pytest

from app.db.conexion import conectar
from tests.conftest import datos_aporte


@pytest.fixture
def aporte_pendiente(cliente, catalogos):
    envio = cliente.post(
        "/aportes",
        data=datos_aporte(catalogos),
        files={"archivo": ("apunte.pdf", b"%PDF-1.4", "application/pdf")},
        follow_redirects=False,
    )
    assert envio.status_code == 303


def test_acceso_a_la_cola_desde_el_perfil_estudiante(cliente, aporte_pendiente):
    """HU-02 · Acceso a la cola desde el perfil Estudiante."""
    assert cliente.get("/moderacion/aportes").status_code == 403


def test_cola_compartida_ofrece_version_validada_sin_reserva(cliente, ruta_db, aporte_pendiente):
    """HU-02 · Consultar un aporte pendiente."""
    cliente.post("/demo/rol", data={"rol": "Moderador"})
    with closing(conectar(ruta_db)) as conexion:
        version = conexion.execute("SELECT id, aporte_id FROM versiones_apunte").fetchone()
        ruta = f"/moderacion/aportes/{version['aporte_id']}/versiones/{version['id']}/revision"
        panel = cliente.get("/moderacion/aportes")
        assert ruta in panel.text
        assert "Asignar revisor" not in panel.text
        assert "Registrar decisión" in cliente.get(ruta).text
        assert ruta in cliente.get("/moderacion/aportes").text
        assert conexion.execute("SELECT estado FROM versiones_apunte").fetchone()[0] == "PendienteRevision"
        assert conexion.execute("SELECT count(*) FROM asignaciones_revision").fetchone()[0] == 0

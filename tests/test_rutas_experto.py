"""Verificación del flujo HU-03-CA4 desde los formularios de la demo."""

import re
from contextlib import closing

import pytest

from app.db.conexion import conectar
from tests.conftest import datos_aporte


@pytest.mark.parametrize(
    ("decision", "estado", "estado_catalogo"),
    [
        ("Aprobacion", "Publicada", 200),
        ("Rechazo", "Rechazada", 404),
        ("SolicitudCorreccion", "RequiereCorreccion", 404),
    ],
)
def test_hu03_ca4_flujo_http_experto(
    cliente, catalogos, ruta_db, decision, estado, estado_catalogo
):
    archivo = b"%PDF-1.4 contenido para revision experta"
    aporte = cliente.post(
        "/aportes", data=datos_aporte(catalogos),
        files={"archivo": ("apunte.pdf", archivo, "application/pdf")},
        follow_redirects=False,
    )
    assert aporte.status_code == 303
    with closing(conectar(ruta_db)) as conexion:
        ids = conexion.execute("SELECT aporte_id, id FROM versiones_apunte").fetchone()
        nombre_experto, especialidad_experto = conexion.execute(
            "SELECT nombre, especialidad FROM expertos ORDER BY id LIMIT 1"
        ).fetchone()
    aporte_id, version_id = ids
    base = f"/moderacion/aportes/{aporte_id}/versiones/{version_id}"
    evaluar = f"/moderacion/experto/aportes/{aporte_id}/versiones/{version_id}/evaluar"
    dictamen = {"decision": decision, "alcance": "Unidad 1", "observaciones": "Revisión experta"}

    assert cliente.post(evaluar, data=dictamen).status_code == 403
    assert cliente.post(
        base + "/revision/derivar-experto", data={"especialidad": "Física Cuántica"}
    ).status_code == 403
    cliente.post("/demo/rol", data={"rol": "Moderador"})
    assert cliente.post(base + "/revision/derivar-experto", data={"especialidad": " "}).status_code == 400
    derivacion = cliente.post(
        base + "/revision/derivar-experto", data={"especialidad": "Física Cuántica"}
    )
    assert derivacion.status_code == 200
    assert cliente.get(base + "/experto/archivo").status_code == 403

    cliente.post("/demo/rol", data={"rol": "Experto"})
    bandeja = cliente.get("/moderacion/experto/aportes")
    assert bandeja.status_code == 200
    assert f"Aporte #{aporte_id}" in bandeja.text
    assert "Física Cuántica" in bandeja.text
    formulario = cliente.get(base + "/experto/evaluar")
    assert formulario.status_code == 200
    opciones = re.findall(r'name="decision" value="([^"]+)"', formulario.text)
    assert opciones == ["Aprobacion", "Rechazo", "SolicitudCorreccion"]
    dictamen["decision"] = opciones[opciones.index(decision)]
    assert cliente.get(base + "/experto/archivo").content == archivo
    assert cliente.post(evaluar, data=dictamen).status_code == 200
    assert cliente.post(evaluar, data=dictamen).status_code == 409
    cliente.post("/demo/rol", data={"rol": "Moderador"})
    assert cliente.post(
        base + "/revision/derivar-experto", data={"especialidad": "Física Cuántica"}
    ).status_code == 409

    with closing(conectar(ruta_db)) as conexion:
        version = conexion.execute("SELECT estado FROM versiones_apunte WHERE id = ?", (version_id,))
        assert version.fetchone()["estado"] == estado
    ficha = cliente.get(f"/catalogo/{version_id}")
    assert ficha.status_code == estado_catalogo
    catalogo = cliente.get("/catalogo")
    assert catalogo.status_code == 200
    assert (f'/catalogo/{version_id}"' in catalogo.text) == (estado_catalogo == 200)
    if estado_catalogo == 200:
        assert nombre_experto in ficha.text
        assert especialidad_experto in ficha.text
    else:
        cliente.post("/demo/rol", data={"rol": "Estudiante"})
        detalle = cliente.get(aporte.headers["location"])
        assert detalle.status_code == 200
        assert nombre_experto in detalle.text
        assert dictamen["observaciones"] in detalle.text

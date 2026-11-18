from contextlib import closing

from app.db.conexion import conectar
from tests.conftest import datos_aporte

PANEL = "/moderacion/aportes"


def _enviar_aporte(cliente, datos, contenido=b"%PDF HU-02"):
    return cliente.post(
        "/aportes",
        data=datos,
        files={"archivo": ("apunte.pdf", contenido, "application/pdf")},
        follow_redirects=False,
    )


def _crear_aporte_pendiente(cliente, datos):
    respuesta = _enviar_aporte(cliente, datos)
    assert respuesta.status_code == 303
    return int(respuesta.headers["location"].rsplit("/", 1)[-1])


def _elegir_moderador(cliente):
    inicio = cliente.post("/demo/rol", data={"rol": "Moderador"})
    assert inicio.status_code == 200
    assert 'href="http://testserver/moderacion/aportes"' in inicio.text


def _ruta_asignar(aporte_id):
    return f"{PANEL}/{aporte_id}/asignar"


def test_estudiante_de_la_comunidad_disponible(cliente, ruta_db, catalogos):
    """HU-02 · Estudiante de la comunidad disponible."""
    aporte_id = _crear_aporte_pendiente(cliente, datos_aporte(catalogos))
    _elegir_moderador(cliente)
    panel = cliente.get(PANEL)
    assert panel.status_code == 200
    assert _ruta_asignar(aporte_id) in panel.text
    assert "Ingeniería de Requisitos" in panel.text
    assert "Elicitación de requisitos" in panel.text
    assert "2026 · semestre 1" in panel.text

    respuesta = cliente.post(_ruta_asignar(aporte_id))

    assert respuesta.status_code == 200
    assert f"Aporte #{aporte_id} asignado." in respuesta.text
    assert "Revisor Demo 1" in respuesta.text
    assert _ruta_asignar(aporte_id) not in respuesta.text
    with closing(conectar(ruta_db)) as conexion:
        asignacion = conexion.execute(
            """
            SELECT ar.estado, ar.fecha_asignacion, a.estado AS aporte,
                   v.estado AS version, e.correo, c.nombre AS comunidad
            FROM asignaciones_revision ar
            JOIN aportes a ON a.id = ar.aporte_id
            JOIN versiones_apunte v ON v.aporte_id = a.id
            JOIN estudiantes e ON e.id = ar.revisor_id
            JOIN comunidades_estudiantiles c ON c.id = ar.comunidad_id
            WHERE a.id = ?
            """,
            (aporte_id,),
        ).fetchone()
        assert asignacion["estado"] == "Asignada"
        assert asignacion["fecha_asignacion"]
        assert asignacion["aporte"] == "Asignado"
        assert asignacion["version"] == "PendienteRevision"
        assert asignacion["correo"] == "revisor1@demo.cl"
        assert asignacion["comunidad"] == "Comunidad Estudiantil"

    detalle = cliente.get(f"/aportes/{aporte_id}")
    assert "Ya tiene un responsable y sigue pendiente de revisión" in detalle.text


def test_sin_estudiantes_revisores_disponibles(cliente, ruta_db, catalogos):
    """HU-02 · Sin estudiantes revisores disponibles."""
    datos = datos_aporte(
        catalogos, ramo_id=catalogos["otro_ramo_id"], tema_id=catalogos["tema_otro_ramo_id"]
    )
    aporte_id = _crear_aporte_pendiente(cliente, datos)
    _elegir_moderador(cliente)

    respuesta = cliente.post(_ruta_asignar(aporte_id))

    assert respuesta.status_code == 200
    assert "Sin revisor disponible para este ramo" in respuesta.text
    assert "El material sigue sin aprobarse ni publicarse." in respuesta.text
    assert _ruta_asignar(aporte_id) in respuesta.text
    assert _ruta_asignar(aporte_id) in cliente.get(PANEL).text
    with closing(conectar(ruta_db)) as conexion:
        assert conexion.execute("SELECT count(*) FROM asignaciones_revision").fetchone()[0] == 0
        estados = conexion.execute(
            """
            SELECT a.estado, v.estado FROM aportes a
            JOIN versiones_apunte v ON v.aporte_id = a.id
            WHERE a.id = ?
            """,
            (aporte_id,),
        ).fetchone()
        assert tuple(estados) == ("PendienteAsignacion", "PendienteRevision")


def test_estudiante_no_puede_abrir_panel_ni_asignar(cliente, ruta_db, catalogos):
    aporte_id = _crear_aporte_pendiente(cliente, datos_aporte(catalogos))
    assert cliente.get(PANEL).status_code == 403
    assert cliente.post(_ruta_asignar(aporte_id)).status_code == 403
    with closing(conectar(ruta_db)) as conexion:
        assert conexion.execute("SELECT count(*) FROM asignaciones_revision").fetchone()[0] == 0
        assert conexion.execute("SELECT estado FROM aportes").fetchone()[0] == "PendienteAsignacion"


def test_no_se_ofrece_aporte_que_requiere_correccion(cliente, catalogos):
    envio = _enviar_aporte(cliente, datos_aporte(catalogos), contenido=b"")
    assert envio.status_code == 400
    _elegir_moderador(cliente)
    assert _ruta_asignar(1) not in cliente.get(PANEL).text
    assert cliente.post(_ruta_asignar(1)).status_code == 409
    assert cliente.post(_ruta_asignar(900)).status_code == 404


def test_no_se_asigna_si_la_ultima_version_no_esta_validada(cliente, ruta_db, catalogos):
    aporte_id = _crear_aporte_pendiente(cliente, datos_aporte(catalogos))
    with closing(conectar(ruta_db)) as conexion, conexion:
        conexion.execute(
            """
            INSERT INTO versiones_apunte (aporte_id, numero, nombre_archivo, estado, fecha_creacion)
            VALUES (?, 2, 'corregir.pdf', 'RequiereCorreccion', '2026-11-18T12:00:00+00:00')
            """,
            (aporte_id,),
        )
    _elegir_moderador(cliente)
    assert _ruta_asignar(aporte_id) not in cliente.get(PANEL).text
    assert cliente.post(_ruta_asignar(aporte_id)).status_code == 409


def test_el_reintento_muestra_el_responsable_vigente(cliente, ruta_db, catalogos):
    aporte_id = _crear_aporte_pendiente(cliente, datos_aporte(catalogos))
    _elegir_moderador(cliente)
    assert cliente.post(_ruta_asignar(aporte_id)).status_code == 200

    respuesta = cliente.post(_ruta_asignar(aporte_id))

    assert respuesta.status_code == 200
    assert "ya tiene un revisor asignado" in respuesta.text
    assert "Revisor Demo 1" in respuesta.text
    with closing(conectar(ruta_db)) as conexion:
        assert conexion.execute("SELECT count(*) FROM asignaciones_revision").fetchone()[0] == 1

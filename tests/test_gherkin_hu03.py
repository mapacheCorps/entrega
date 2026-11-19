from contextlib import closing

import pytest

from app.db.conexion import conectar
from tests.conftest import datos_aporte

PANEL = "/moderacion/aportes"
DECISION = {
    "decision": "Aprobacion",
    "alcance": "Unidad de elicitación",
    "observaciones": "Las definiciones y ejemplos coinciden con lo visto en clase.",
}


def _perfil(cliente, rol):
    assert cliente.post("/demo/rol", data={"rol": rol}).status_code == 200


def _enviar(cliente, catalogos, archivo):
    contenido = f"%PDF-1.4 HU-03 {archivo}".encode()
    envio = cliente.post(
        "/aportes",
        data=datos_aporte(catalogos),
        files={"archivo": (archivo, contenido, "application/pdf")},
        follow_redirects=False,
    )
    assert envio.status_code == 303
    return int(envio.headers["location"].rsplit("/", 1)[-1])


@pytest.fixture
def aporte_pendiente(cliente, ruta_db, catalogos):
    aporte_id = _enviar(cliente, catalogos, "contenido-revisado.pdf")
    _perfil(cliente, "Moderador")
    with closing(conectar(ruta_db)) as conexion:
        version_id = conexion.execute(
            "SELECT id FROM versiones_apunte WHERE aporte_id = ?", (aporte_id,),
        ).fetchone()[0]
    return aporte_id, f"{PANEL}/{aporte_id}/versiones/{version_id}"


def _estado(ruta_db, aporte_id):
    with closing(conectar(ruta_db)) as conexion:
        fila = conexion.execute(
            """
            SELECT a.estado AS aporte, v.estado AS version,
                   (SELECT id FROM estudiantes WHERE rol = 'Moderador') AS moderador_id,
                   (SELECT comunidad_id FROM estudiantes WHERE rol = 'Moderador') AS comunidad_actual,
                   ra.revisor_id, ra.comunidad_id, ra.fecha, ra.decision, ra.alcance, ra.observaciones
            FROM aportes a
            JOIN versiones_apunte v ON v.aporte_id = a.id
            LEFT JOIN revisiones_academicas ra ON ra.version_id = v.id
            WHERE a.id = ? ORDER BY v.numero DESC LIMIT 1
            """,
            (aporte_id,),
        ).fetchone()
        return dict(fila)


def _abrir(cliente, base):
    respuesta = cliente.get(base + "/revision")
    assert respuesta.status_code == 200
    assert "Pendiente de revisión" in respuesta.text
    assert "Registrar decisión" in respuesta.text


def test_aprobacion_de_version_revisada(cliente, ruta_db, aporte_pendiente):
    """HU-03 · Aprobación de versión revisada."""
    aporte_id, base = aporte_pendiente
    assert base + "/revision" in cliente.get(PANEL).text
    archivo = cliente.get(base + "/archivo")
    assert archivo.status_code == 200
    assert archivo.content == b"%PDF-1.4 HU-03 contenido-revisado.pdf"
    assert archivo.headers["content-disposition"].startswith("attachment;")
    assert "contenido-revisado.pdf" not in cliente.get("/catalogo").text
    _abrir(cliente, base)

    respuesta = cliente.post(base + "/revision/decision", data=DECISION)

    assert respuesta.status_code == 200
    assert "La versión fue aprobada y publicada." in respuesta.text
    estado = _estado(ruta_db, aporte_id)
    assert (estado["aporte"], estado["version"]) == (
        "Publicado", "Publicada",
    )
    assert estado["decision"] == "Aprobacion"
    assert estado["revisor_id"] == estado["moderador_id"]
    assert estado["comunidad_id"] == estado["comunidad_actual"]
    assert estado["fecha"] and estado["alcance"] == DECISION["alcance"]
    assert estado["observaciones"] == DECISION["observaciones"]
    assert base + "/revision" not in cliente.get(PANEL).text
    assert "Esta versión está publicada" in cliente.get(f"/aportes/{aporte_id}").text
    assert cliente.post(base + "/revision/decision", data=DECISION).status_code == 409
    assert _estado(ruta_db, aporte_id) == estado
    _perfil(cliente, "Estudiante")
    assert "contenido-revisado.pdf" in cliente.get("/catalogo").text


def test_ficha_vista_previa_y_descarga_revalidan_la_version(
    cliente, ruta_db, almacenamiento, aporte_pendiente
):
    _, base = aporte_pendiente
    version_id = int(base.rsplit("/", 1)[-1])
    ficha = f"/catalogo/{version_id}"
    assert cliente.get(ficha + "/descargar").status_code == 404
    assert cliente.post(base + "/revision/decision", data=DECISION).status_code == 200
    assert ficha in cliente.get("/catalogo").text
    pagina = cliente.get(ficha)
    assert DECISION["alcance"] in pagina.text and "Vista previa" in pagina.text
    vista = cliente.get(ficha + "/vista-previa")
    descarga = cliente.get(ficha + "/descargar")
    assert vista.headers["content-type"] == "application/pdf"
    assert vista.headers["content-disposition"].startswith("inline;")
    assert descarga.headers["content-disposition"].startswith("attachment;")
    assert vista.content == descarga.content == b"%PDF-1.4 HU-03 contenido-revisado.pdf"

    with closing(conectar(ruta_db)) as conexion, conexion:
        referencia = conexion.execute(
            "SELECT referencia_archivo FROM versiones_apunte WHERE id = ?", (version_id,),
        ).fetchone()[0]
        almacenamiento.eliminar(referencia)
    assert "Versión no disponible" in cliente.get(ficha + "/descargar").text
    assert cliente.get(ficha).status_code == 404
    with closing(conectar(ruta_db)) as conexion, conexion:
        conexion.execute("UPDATE versiones_apunte SET estado = 'Final' WHERE id = ?", (version_id,))
    assert cliente.get(ficha).status_code == 404
    assert cliente.get(ficha + "/vista-previa").status_code == 404


@pytest.mark.parametrize(
    ("extension", "contenido", "tipo_vista"),
    [
        ("png", b"\x89PNG\r\n\x1a\n", "image/png"),
        ("jpg", b"\xff\xd8\xff", "image/jpeg"),
        ("docx", b"PK Office demo", None),
        ("pptx", b"PK presentacion demo", None),
        ("pdf", b"<html>no es un PDF", None),
    ],
)
def test_solo_formatos_compatibles_se_sirven_en_linea(
    cliente, ruta_db, catalogos, extension, contenido, tipo_vista
):
    envio = cliente.post(
        "/aportes", data=datos_aporte(catalogos),
        files={"archivo": (f"apunte.{extension}", contenido, "text/html")},
        follow_redirects=False,
    )
    assert envio.status_code == 303
    with closing(conectar(ruta_db)) as conexion:
        version, aporte = conexion.execute("SELECT id, aporte_id FROM versiones_apunte").fetchone()
    _perfil(cliente, "Moderador")
    decision = f"{PANEL}/{aporte}/versiones/{version}/revision/decision"
    assert cliente.post(decision, data=DECISION).status_code == 200
    ficha = f"/catalogo/{version}"
    vista = cliente.get(ficha + "/vista-previa")
    descarga = cliente.get(ficha + "/descargar")
    assert descarga.content == contenido
    assert descarga.headers["content-type"] == "application/octet-stream"
    if tipo_vista is None:
        assert vista.status_code == 415
    else:
        assert vista.headers["content-type"] == tipo_vista
        assert vista.content == contenido
    if extension in {"docx", "pptx"}:
        assert "Descarga el archivo para abrirlo" in cliente.get(ficha).text


def test_rechazo_o_solicitud_de_correccion(cliente, ruta_db, aporte_pendiente):
    """HU-03 · Rechazo o solicitud de corrección."""
    aporte_id, base = aporte_pendiente
    _abrir(cliente, base)
    observaciones = "El apunte atribuye mal la técnica al autor de la fuente."

    respuesta = cliente.post(
        base + "/revision/decision",
        data={**DECISION, "decision": "Rechazo", "observaciones": observaciones},
    )

    assert respuesta.status_code == 200
    assert "El rechazo quedó registrado." in respuesta.text
    estado = _estado(ruta_db, aporte_id)
    assert (estado["aporte"], estado["version"]) == (
        "Rechazado", "Rechazada",
    )
    assert estado["observaciones"] == observaciones
    assert "contenido-revisado.pdf" not in cliente.get("/catalogo").text


def test_intento_no_autorizado(cliente, ruta_db, aporte_pendiente):
    """HU-03 · Intento no autorizado."""
    aporte_id, base = aporte_pendiente
    estado = _estado(ruta_db, aporte_id)
    assert estado["version"] == "PendienteRevision"
    _perfil(cliente, "Estudiante")

    respuesta = cliente.post(base + "/revision/decision", data=DECISION)

    assert respuesta.status_code == 403
    assert "Revisión no autorizada" in respuesta.text
    assert cliente.get(base + "/archivo").status_code == 403
    assert _estado(ruta_db, aporte_id) == estado
    assert "contenido-revisado.pdf" not in cliente.get("/catalogo").text


def test_solicitud_de_correccion_academica(cliente, ruta_db, aporte_pendiente):
    aporte_id, base = aporte_pendiente
    _abrir(cliente, base)
    observaciones = "Agrega la referencia del ejemplo de entrevista."

    respuesta = cliente.post(
        base + "/revision/decision",
        data={**DECISION, "decision": "SolicitudCorreccion", "observaciones": observaciones},
    )

    assert respuesta.status_code == 200
    assert "La solicitud de corrección quedó registrada." in respuesta.text
    estado = _estado(ruta_db, aporte_id)
    assert (estado["aporte"], estado["version"]) == (
        "CorreccionSolicitada", "RequiereCorreccion",
    )
    assert estado["observaciones"] == observaciones
    _perfil(cliente, "Estudiante")
    assert cliente.get(f"/aportes/{aporte_id}/corregir").status_code == 400
    assert "Subir un archivo corregido" not in cliente.get(f"/aportes/{aporte_id}").text
    assert "contenido-revisado.pdf" not in cliente.get("/catalogo").text


def test_muestra_campos_invalidos_y_conserva_los_datos_ya_ingresados(
    cliente, ruta_db, aporte_pendiente
):
    aporte_id, base = aporte_pendiente
    _abrir(cliente, base)
    respuesta = cliente.post(
        base + "/revision/decision", data={**DECISION, "observaciones": " "},
    )
    assert respuesta.status_code == 400
    assert "Escribe las observaciones que fundamentan la decisión" in respuesta.text
    assert DECISION["alcance"] in respuesta.text
    assert 'aria-describedby="error-observaciones"' in respuesta.text
    assert _estado(ruta_db, aporte_id)["decision"] is None


def test_catalogo_exige_aprobacion_de_la_misma_version(cliente, ruta_db, aporte_pendiente):
    aporte_id, base = aporte_pendiente
    _abrir(cliente, base)
    assert cliente.post(base + "/revision/decision", data=DECISION).status_code == 200
    with closing(conectar(ruta_db)) as conexion, conexion:
        conexion.execute("""
            INSERT INTO versiones_apunte (aporte_id, numero, nombre_archivo, estado, fecha_creacion)
            VALUES (?, 2, 'otra-version.pdf', 'Publicada', '2026-11-18')
            """, (aporte_id,))
    respuesta = cliente.get("/catalogo")
    assert "contenido-revisado.pdf" in respuesta.text
    assert "otra-version.pdf" not in respuesta.text

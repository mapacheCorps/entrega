from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import dataclass
from threading import Barrier

import pytest

from app.db.conexion import conectar
from app.integraciones.almacenamiento import AlmacenamientoConFallo
from app.servicios.aportes import ServicioAportes, TipoResultado
from tests.conftest import archivo_pdf, datos_aporte

PANEL = "/moderacion/aportes"
OBSERVACIONES = "Distingue los objetivos de la entrevista de las preguntas."
ALCANCE = "Unidad de elicitación"
ORIGINAL = ("original.pdf", b"Archivo original HU-04", "application/pdf")
CORREGIDO = ("corregido.pdf", b"Archivo corregido HU-04", "application/pdf")


@dataclass(frozen=True)
class AporteRevisado:
    id: int
    version_id: int

    @property
    def detalle(self):
        return f"/aportes/{self.id}"

    @property
    def reenvio(self):
        return f"{self.detalle}/versiones/{self.version_id}/reenviar"


def _perfil(cliente, rol):
    assert cliente.post("/demo/rol", data={"rol": rol}).status_code == 200


@pytest.fixture
def revisado(cliente, ruta_db, catalogos, request):
    envio = cliente.post(
        "/aportes", data=datos_aporte(catalogos), files={"archivo": ORIGINAL},
        follow_redirects=False,
    )
    assert envio.status_code == 303
    aporte_id = int(envio.headers["location"].rsplit("/", 1)[-1])
    with closing(conectar(ruta_db)) as conexion:
        version_id = conexion.execute(
            "SELECT id FROM versiones_apunte WHERE aporte_id = ?", (aporte_id,)
        ).fetchone()[0]

    base = f"{PANEL}/{aporte_id}/versiones/{version_id}/revision"
    _perfil(cliente, "Moderador")
    assert cliente.post(f"{PANEL}/{aporte_id}/asignar").status_code == 200
    assert cliente.post(base + "/iniciar").status_code == 200
    decision = getattr(request, "param", "Rechazo")
    respuesta = cliente.post(
        base + "/decision",
        data={"decision": decision, "alcance": ALCANCE, "observaciones": OBSERVACIONES},
    )
    assert respuesta.status_code == 200
    _perfil(cliente, "Estudiante")
    return AporteRevisado(aporte_id, version_id)


def _historial(ruta_db, aporte_id):
    with closing(conectar(ruta_db)) as conexion:
        aporte = conexion.execute("SELECT * FROM aportes WHERE id = ?", (aporte_id,)).fetchone()
        versiones = conexion.execute(
            """
            SELECT v.*, ra.decision, ra.alcance, ra.observaciones
            FROM versiones_apunte v
            LEFT JOIN revisiones_academicas ra ON ra.version_id = v.id
            WHERE v.aporte_id = ? ORDER BY v.numero
            """,
            (aporte_id,),
        ).fetchall()
        asignaciones = conexion.execute(
            "SELECT * FROM asignaciones_revision WHERE aporte_id = ? ORDER BY id", (aporte_id,)
        ).fetchall()
    return dict(aporte), [dict(v) for v in versiones], [dict(a) for a in asignaciones]


def test_nueva_version_del_mismo_aporte(cliente, ruta_db, almacenamiento, revisado):
    """HU-04 · Nueva versión del mismo aporte."""
    antes = _historial(ruta_db, revisado.id)
    detalle = cliente.get(revisado.detalle)
    assert OBSERVACIONES in detalle.text and ALCANCE in detalle.text
    assert revisado.reenvio in detalle.text
    formulario = cliente.get(revisado.reenvio)
    assert formulario.status_code == 200
    assert "original.pdf" in formulario.text and OBSERVACIONES in formulario.text

    respuesta = cliente.post(revisado.reenvio, files={"archivo": CORREGIDO})

    assert respuesta.status_code == 200
    assert respuesta.url.path == revisado.detalle
    assert "número 2" in respuesta.text and OBSERVACIONES in respuesta.text
    assert revisado.reenvio not in respuesta.text
    aporte, (anterior, nueva), asignaciones = _historial(ruta_db, revisado.id)
    assert aporte == {**antes[0], "estado": "PendienteAsignacion"}
    assert anterior == {**antes[1][0], "estado": "Final"}
    assert almacenamiento.leer(anterior["referencia_archivo"]) == ORIGINAL[1]
    assert almacenamiento.leer(nueva["referencia_archivo"]) == CORREGIDO[1]
    assert nueva["id"] != revisado.version_id and nueva["numero"] == 2
    assert nueva["estado"] == "PendienteRevision" and nueva["decision"] is None
    assert asignaciones == antes[2] and asignaciones[0]["estado"] == "Finalizada"
    assert "corregido.pdf" not in cliente.get("/catalogo").text
    assert cliente.post(revisado.reenvio, files={"archivo": CORREGIDO}).status_code == 409

    _perfil(cliente, "Moderador")
    assert f"{PANEL}/{revisado.id}/asignar" in cliente.get(PANEL).text
    assert cliente.post(f"{PANEL}/{revisado.id}/asignar").status_code == 200
    assert _historial(ruta_db, revisado.id)[2][-1]["estado"] == "Asignada"


def test_correccion_invalida(cliente, ruta_db, revisado):
    """HU-04 · Corrección inválida."""
    antes = _historial(ruta_db, revisado.id)

    respuesta = cliente.post(
        revisado.reenvio, files={"archivo": ("archivo.txt", b"texto", "text/plain")}
    )

    assert respuesta.status_code == 400
    assert "El formato del archivo no está permitido" in respuesta.text
    assert OBSERVACIONES in respuesta.text and "Enviar versión corregida" in respuesta.text
    assert _historial(ruta_db, revisado.id) == antes
    _perfil(cliente, "Moderador")
    assert f"{PANEL}/{revisado.id}/asignar" not in cliente.get(PANEL).text


@pytest.mark.parametrize("revisado", ["SolicitudCorreccion"], indirect=True)
def test_reenvio_tras_solicitud_de_correccion(cliente, ruta_db, revisado):
    assert "Solicitud de corrección" in cliente.get(revisado.detalle).text
    respuesta = cliente.post(revisado.reenvio, files={"archivo": CORREGIDO})
    assert respuesta.status_code == 200
    aporte, (anterior, nueva), _ = _historial(ruta_db, revisado.id)
    assert aporte["estado"] == "PendienteAsignacion"
    assert anterior["decision"] == "SolicitudCorreccion" and anterior["estado"] == "Final"
    assert nueva["decision"] is None and nueva["estado"] == "PendienteRevision"


def test_archivo_ausente_y_duplicado_permiten_reintentar(cliente, ruta_db, revisado):
    antes = _historial(ruta_db, revisado.id)
    sin_archivo = cliente.post(revisado.reenvio)
    assert sin_archivo.status_code == 400
    assert "Adjunta el archivo" in sin_archivo.text
    duplicado = cliente.post(revisado.reenvio, files={"archivo": ORIGINAL})
    assert duplicado.status_code == 409
    assert "Ya existe un archivo idéntico registrado" in duplicado.text
    assert OBSERVACIONES in duplicado.text
    assert _historial(ruta_db, revisado.id) == antes


def test_feedback_y_reenvio_pertenecen_al_autor(cliente, ruta_db, revisado):
    _perfil(cliente, "Moderador")
    assert OBSERVACIONES not in cliente.get(revisado.detalle).text
    assert cliente.get(revisado.reenvio).status_code == 403
    assert cliente.post(revisado.reenvio, files={"archivo": CORREGIDO}).status_code == 403

    with closing(conectar(ruta_db)) as conexion, conexion:
        otro_estudiante = conexion.execute(
            "INSERT INTO estudiantes (nombre, correo) VALUES ('Otro autor', 'otro@demo.cl')"
        ).lastrowid
        conexion.execute("UPDATE aportes SET autor_id = ? WHERE id = ?", (otro_estudiante, revisado.id))
    antes = _historial(ruta_db, revisado.id)
    _perfil(cliente, "Estudiante")
    detalle = cliente.get(revisado.detalle)
    assert OBSERVACIONES not in detalle.text and revisado.reenvio not in detalle.text
    assert cliente.get(revisado.reenvio).status_code == 403
    assert cliente.post(revisado.reenvio, files={"archivo": CORREGIDO}).status_code == 403
    assert _historial(ruta_db, revisado.id) == antes


def test_el_reenvio_exige_version_vigente_y_decision_coherente(cliente, ruta_db, revisado):
    otra_version = f"{revisado.detalle}/versiones/{revisado.version_id + 1}/reenviar"
    assert cliente.get(otra_version).status_code == 409
    with closing(conectar(ruta_db)) as conexion, conexion:
        conexion.execute(
            "UPDATE revisiones_academicas SET decision = 'Aprobacion' WHERE version_id = ?",
            (revisado.version_id,),
        )
    assert cliente.get(revisado.reenvio).status_code == 409
    with closing(conectar(ruta_db)) as conexion, conexion:
        conexion.execute("UPDATE aportes SET estado = 'Asignado' WHERE id = ?", (revisado.id,))
    assert cliente.post(revisado.reenvio, files={"archivo": CORREGIDO}).status_code == 409


def test_fallo_de_almacenamiento_conserva_el_aporte(cliente, ruta_db, almacenamiento, revisado):
    antes = _historial(ruta_db, revisado.id)
    cliente.app.state.almacenamiento = AlmacenamientoConFallo(almacenamiento.base_dir)
    respuesta = cliente.post(revisado.reenvio, files={"archivo": CORREGIDO})
    assert respuesta.status_code == 502
    assert "Fallo simulado del almacenamiento" in respuesta.text
    assert OBSERVACIONES in respuesta.text
    assert _historial(ruta_db, revisado.id) == antes
    assert len(list((almacenamiento.base_dir / str(revisado.id)).iterdir())) == 1


def test_fallo_de_registro_revierte_el_reenvio_y_retira_solo_el_archivo_nuevo(
    cliente, ruta_db, almacenamiento, revisado
):
    antes = _historial(ruta_db, revisado.id)
    with closing(conectar(ruta_db)) as conexion, conexion:
        conexion.execute("""
            CREATE TRIGGER fallo_confirmacion BEFORE UPDATE ON aportes
            WHEN NEW.estado = 'PendienteAsignacion'
            BEGIN
                SELECT RAISE(ABORT, 'fallo simulado');
            END
            """)
    respuesta = cliente.post(revisado.reenvio, files={"archivo": CORREGIDO})
    assert respuesta.status_code == 502
    assert "No fue posible confirmar el reenvío" in respuesta.text
    assert _historial(ruta_db, revisado.id) == antes
    assert len(list((almacenamiento.base_dir / str(revisado.id)).iterdir())) == 1
    assert almacenamiento.leer(antes[1][0]["referencia_archivo"]) == ORIGINAL[1]

    with closing(conectar(ruta_db)) as conexion, conexion:
        conexion.execute("DROP TRIGGER fallo_confirmacion")
    assert cliente.post(revisado.reenvio, files={"archivo": CORREGIDO}).status_code == 200


def test_dos_reenvios_concurrentes_generan_una_sola_version(ruta_db, almacenamiento, revisado):
    inicio = Barrier(2, timeout=5)

    def reenviar(contenido):
        with closing(conectar(ruta_db)) as conexion:
            servicio = ServicioAportes(conexion, almacenamiento)
            inicio.wait()
            return servicio.reenviar(revisado.id, revisado.version_id, archivo_pdf(contenido))

    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        resultados = [ejecutor.submit(reenviar, b"Una"), ejecutor.submit(reenviar, b"Otra")]
        assert {tarea.result().tipo for tarea in resultados} == {
            TipoResultado.REGISTRADO, TipoResultado.NO_CORREGIBLE,
        }
    _, versiones, _ = _historial(ruta_db, revisado.id)
    assert [version["numero"] for version in versiones] == [1, 2]
    assert almacenamiento.leer(versiones[-1]["referencia_archivo"]) in (b"Una", b"Otra")

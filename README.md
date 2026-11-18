# Torpedos universitarios

Documentación de Ingeniería de Requisitos, CIN324.
- [Entrega 1](./IngReq-Entrega%201.md)
- [Entrega 2](./IngReq-Entrega%202.md)

## Integrantes
- Ignacio Rivera
- Nicolas Lazcano
- Sebastian Rojas
- Rodrigo Sances
- Benjamín Isasmendi

## Aplicación web

Aplicación de demostración construida con **Python + FastAPI + Jinja2 + SQLite**.
Implementa el envío de un apunte con su clasificación, la validación del archivo,
la detección de duplicados exactos y la corrección de un archivo inválido (HU-01).
También permite que la comunidad estudiantil asigne un revisor a un aporte
validado (HU-02), registre la decisión académica y publique la versión aprobada
en un catálogo básico (HU-03).

### Requisitos

- Python 3.11 o superior. En Windows se usa el lanzador `py`.
- Git (opcional, para clonar el repositorio).

### Instalación

```powershell
py -m venv .venv
. .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

En macOS o Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Crear la base y los datos de ejemplo

```powershell
python -m app.db.seed
```

El comando crea `data/app.db`, aplica las migraciones pendientes y carga carreras,
ramos, períodos, temas, los dos perfiles de demostración y los revisores con
sus habilitaciones. Ejecuta el mismo comando si ya tenías la base de HU-01.
Puedes volver a ejecutarlo sin duplicar filas.

### Ejecutar la aplicación

```powershell
python -m uvicorn app.main:app --reload
```

Abre <http://localhost:8000>.

### Probar

```powershell
python -m pytest
```

Las pruebas usan una base SQLite temporal por prueba y no dependen de `data/app.db`.

### Selector de rol de demostración

El selector superior guarda el perfil activo en la cookie `demo_role`. Los perfiles
son **Estudiante** y **Moderador**. El Moderador representa a la **Comunidad
Estudiantil** del modelo de dominio. Estudiante puede enviar aportes y corregir un
archivo inválido. Moderador puede abrir **Organizar revisiones**, asignar un revisor
e iniciar y resolver la revisión en su nombre. El selector sirve para recorrer la
demostración.

### Probar HU-02 en el navegador

Con el perfil **Estudiante**, envía dos archivos válidos distintos y completa
todos los campos de clasificación. Usa la carrera **Ingeniería Civil Informática**
para ambos aportes. Luego cambia a **Moderador**, abre **Organizar revisiones** y
pulsa **Asignar revisor** en el aporte de cada ramo.

| Escenario | Clasificación sugerida | Qué deberías ver |
|---|---|---|
| Estudiante de la comunidad disponible | Ingeniería de Requisitos, Elicitación de requisitos, 2026 · semestre 1 | Se muestra el nombre e identificador del revisor. El aporte pasa a **Asignado** y sale del listado de pendientes. Su versión sigue **Pendiente de revisión**. |
| Sin estudiantes revisores disponibles | Cálculo I, Límites y continuidad, 2026 · semestre 1 | Se muestra **Sin revisor disponible para este ramo**. El aporte sigue en el panel, pendiente de asignación, sin aprobarse ni publicarse. |

### Probar HU-03 en el navegador

Con el entorno virtual activo, ejecuta `python -m app.db.seed` y
`python -m uvicorn app.main:app --reload`. Abre <http://localhost:8000>.
Para cada recorrido, envía un archivo válido distinto como **Estudiante**. Usa
**Ingeniería Civil Informática → Ingeniería de Requisitos → Elicitación de
requisitos** y completa el período y la procedencia. Cambia a **Moderador**, abre
**Organizar revisiones**, pulsa **Asignar revisor** y abre **Revisar versión**.
La pantalla identifica al revisor designado y permite abrir el archivo adjunto.
Pulsa **Iniciar revisión** para abrir el formulario de decisión.

| Escenario | Qué hacer | Qué deberías ver |
|---|---|---|
| Aprobación de versión revisada | Selecciona **Aprobar y publicar**. Indica el alcance revisado y las observaciones. | La pantalla confirma la publicación y la misma versión aparece en **Ver catálogo de apuntes**. |
| Rechazo o solicitud de corrección | Selecciona **Rechazar**. Indica el alcance y explica el motivo. | Se confirma el rechazo. El archivo no aparece en el catálogo. |
| Solicitud de corrección de RP-04 | Selecciona **Solicitar corrección**. Indica el alcance y qué debe corregirse. | Se confirma la solicitud y la versión sigue fuera del catálogo. El detalle indica **Corrección solicitada**. |
| Intento no autorizado | Deja el formulario abierto. En otra pestaña del mismo navegador, abre el inicio y cambia a **Estudiante**. Vuelve a la primera pestaña e intenta registrar una aprobación. | Se muestra **Revisión no autorizada**. La versión sigue fuera del catálogo y conserva su estado. |

Las decisiones válidas finalizan la asignación. Para ejecutar toda la suite usa
`python -m pytest`. Para ejecutar los recorridos HTTP de HU-03 usa
`python -m pytest tests/test_gherkin_hu03.py`.

### Almacenamiento simulado

Los archivos se guardan en `data/archivos/{aporte_id}/`. El servicio de
almacenamiento es un adaptador local; no se integra un proveedor externo.
Para recorrer el camino de error de DSS-01, inicia el servidor con:

```powershell
$env:APP_SIMULAR_FALLO_ALMACENAMIENTO = "1"
python -m uvicorn app.main:app --reload
```

Con esa variable activa, el envío de un archivo válido responde con un error y no
confirma el registro.

### Alcance de esta entrega

- Se implementan el envío y la corrección de archivos inválidos (HU-01), la
  asignación de revisores (HU-02) y la revisión y publicación (HU-03).
- La entrega de observaciones al autor y el reenvío académico quedan para HU-04.
  Los avisos, la búsqueda, la ficha, la descarga pública, los reportes y el retiro
  de versiones se desarrollan en las historias siguientes.
- Los requisitos no funcionales se documentan, pero no se implementan como pruebas de
  rendimiento o usabilidad.

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
validado (HU-02).

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
archivo inválido. Moderador puede abrir **Organizar revisiones** y solicitar la asignación.

### Probar HU-02 en el navegador

Con el perfil **Estudiante**, envía dos archivos válidos distintos y completa
todos los campos de clasificación. Usa la carrera **Ingeniería Civil Informática**
para ambos aportes. Luego cambia a **Moderador**, abre **Organizar revisiones** y
pulsa **Asignar revisor** en el aporte de cada ramo.

| Escenario | Clasificación sugerida | Qué deberías ver |
|---|---|---|
| Estudiante de la comunidad disponible | Ingeniería de Requisitos, Elicitación de requisitos, 2026 · semestre 1 | Se muestra el nombre e identificador del revisor. El aporte pasa a **Asignado** y sale del listado de pendientes. Su versión sigue **Pendiente de revisión**. |
| Sin estudiantes revisores disponibles | Cálculo I, Límites y continuidad, 2026 · semestre 1 | Se muestra **Sin revisor disponible para este ramo**. El aporte sigue en el panel, pendiente de asignación, sin aprobarse ni publicarse. |

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

- Se implementan el envío y la corrección de archivos inválidos (HU-01) y la asignación de revisores (HU-02).
- La revisión, la publicación y los demás recorridos corresponden a historias posteriores.
- Los requisitos no funcionales se documentan, pero no se implementan como pruebas de
  rendimiento o usabilidad.

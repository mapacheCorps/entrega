# Torpedos universitarios

Documentación de Ingeniería de Requisitos, CIN324, Entrega 1.
- [Documentación de la entrega](./IngReq-Entrega%201.md)

## Integrantes
- Ignacio Rivera
- Nicolas Lazcano
- Sebastian Rojas
- Rodrigo Sances
- Benjamín Isasmendi

## Aplicación web — HU-01 Enviar y clasificar un aporte

Aplicación de demostración construida con **Python + FastAPI + Jinja2 + SQLite**.
Implementa el envío de un apunte con su clasificación, la validación del archivo,
la detección de duplicados exactos y la corrección de un archivo inválido.
No incluye autenticación real ni publicación automática.

### Requisitos

- Python 3.11 o superior. En Windows se usa el lanzador `py`.
- Git (opcional, para clonar el repositorio).

### Instalación

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

En macOS o Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Crear la base y los datos de ejemplo

```powershell
py -m app.db.seed
```

El comando crea `data/app.db`, aplica las migraciones pendientes y carga carreras,
ramos, períodos, temas y los dos perfiles de demostración. Es idempotente: se
puede ejecutar varias veces sin duplicar filas.

### Ejecutar la aplicación

```powershell
uvicorn app.main:app --reload
```

Abre <http://localhost:8000>.

### Probar

```powershell
pytest
```

Las pruebas usan una base SQLite temporal por prueba y no dependen de `data/app.db`.

### Selector de rol de demostración

El selector superior guarda el perfil activo en la cookie `demo_role`. Los perfiles
son **Estudiante** y **Moderador**. El Moderador representa a la **Comunidad
Estudiantil** del modelo de dominio. En HU-01 solo el perfil Estudiante puede enviar
y corregir aportes; el Moderador ve las pantallas sin habilitación. No es
autenticación real: es una herramienta para recorrer la demostración.

### Almacenamiento simulado

Los archivos se guardan en `data/archivos/{aporte_id}/`. El servicio de
almacenamiento es un adaptador local; no se integra un proveedor externo.
Para recorrer el camino de error de DSS-01, inicia el servidor con:

```powershell
$env:APP_SIMULAR_FALLO_ALMACENAMIENTO = "1"
uvicorn app.main:app --reload
```

Con esa variable activa, el envío de un archivo válido responde con un error y no
confirma el registro.

### Alcance de esta entrega

- Se implementan P01–P04 y P07 del TO-BE; P13–P14 se usan para corregir un archivo inválido.
- Quedan fuera: asignación de revisores (HU-02), revisión (HU-03), corrección tras un
  rechazo (HU-04), notificaciones, búsqueda, ficha, descarga, reportes y retiro de versiones.
- Los requisitos no funcionales se documentan, pero no se implementan como pruebas de
  rendimiento o usabilidad.

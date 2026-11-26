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

### Requisitos

- Python 3.11 o superior. En Windows se usa el lanzador `py`.
- Git (opcional, para clonar el repositorio).

### Ejecutar
```
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.db.seed
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Abre <http://127.0.0.1:8000>. El sistema usa SQLite y ofrece los perfiles de
demostración **Estudiante** y **Moderador**. El acceso institucional de HU-12
corresponde a una etapa futura.

### Demostración de la Entrega 3

1. Como **Estudiante**, envía un archivo válido y guarda la URL de su detalle.
2. Como **Moderador**, abre **Revisar aportes**, selecciona la versión y solicita
   una corrección. Escribe el alcance y las observaciones.
3. Vuelve a **Estudiante**, abre el detalle y reenvía un archivo corregido con
   contenido distinto. Comprueba que el aporte conserva su ID y suma una versión.
4. Como **Moderador**, aprueba la versión corregida. Comprueba en el catálogo
   que aparece la versión aprobada. Su ficha permite abrir una vista previa
   para PDF, PNG y JPG y descargar el archivo exacto.

### Flujo Experto (HU-03 / CU-13) — Evaluación 2

1. Como **Estudiante**, envía un aporte de materia especializada (ej. "Física Cuántica").
2. Como **Moderador**, abre **Revisar aportes**, verás un botón **"Derivar a Experto"**.
   Ingresa la especialidad requerida (ej. "Física Cuántica") y confirma.
3. Cambia el rol a **Experto** en el selector superior. Verás **Panel de Experto**
   con las versiones derivadas. Selecciona "Evaluar", elige decisión
   (Aprobar/Rechazar/Solicitar corrección), escribe alcance y observaciones.
4. Vuelve a **Moderador** o **Estudiante**: la decisión del Experto aparece en
   la ficha del aporte con su nombre y especialidad. Si aprobó, la versión
   está publicada en el catálogo.

Desde la raíz del repositorio, ejecuta `.\.venv\Scripts\python.exe -m pytest`.
La [matriz de trazabilidad](./12-trazabilidad.md#código-y-pruebas-de-la-entrega-3)
enlaza las historias con su código y pruebas.

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

### Requisitos previos

- **Python 3.11+** (en Windows se usa el lanzador `py`)
- **Git** (para clonar el repositorio)
- **Node.js 20.19+** (solo si vas a instalar OpenSpec CLI para desarrollo con skills)

### Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/mapacheCorps/entrega.git
cd entrega

# 2. Crear y activar entorno virtual
py -m venv .venv
.\.venv\Scripts\activate

# 3. Instalar dependencias de la aplicación
pip install -r requirements.txt

# 4. Inicializar base de datos (migraciones + datos de ejemplo)
py -m app.db.seed

# 5. (Opcional) Instalar OpenSpec CLI para desarrollo con skills
npm install -g @fission-ai/openspec@latest
# Luego en la carpeta del repo: openspec init --tools opencode
```

### Ejecutar la aplicación

```
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.db.seed
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Abre <http://127.0.0.1:8000>. El sistema usa SQLite y ofrece los perfiles de
demostración **Estudiante**, **Moderador** y **Experto**. El acceso institucional de HU-12
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

### Evaluación 2 — Cambio de requerimientos (Martes 24/11 → Jueves 26/11)

**Cambio implementado:** Incorporación de la figura de **Experto** para revisión de materias especializadas.

| Etiqueta Git | Descripción |
|--------------|-------------|
| `base-eval2` | 4 HU base implementadas (HU-01 a HU-04, HU-07, HU-08) |
| `cambio-validado` | Especificación sin IA (martes 24/11): EVALUACION2.md + artefactos actualizados |
| `entrega-eval2` | Implementación con skills (entre sesiones): cambio `ajuste-hu-03-experto-revision` |

**Artefactos de la Evaluación 2:**
- [`eval2/CAMBIOS.md`](./eval2/CAMBIOS.md) — Registro de cambios por artefacto (requerido por rúbrica)
- [`eval2/Presentacion_Evaluacion2_mapacheCorps.pptx`](./eval2/Presentacion_Evaluacion2_mapacheCorps.pptx) — Presentación 5 min (mapa de impacto + reflexión por artefacto)
- [`openspec/changes/ajuste-hu-03-experto-revision/`](./openspec/changes/ajuste-hu-03-experto-revision/) — Propuesta, specs, design, tasks de OpenSpec

### Pruebas

Desde la raíz del repositorio:
```
.\.venv\Scripts\python.exe -m pytest
```
**103 tests pasan** (97 originales + 6 nuevos: `test_gherkin_hu03_experto.py`)

La [matriz de trazabilidad](./12-trazabilidad.md#código-y-pruebas-de-la-entrega-3)
enlaza las historias con su código y pruebas.

### Estructura del proyecto

```
├── 01-proceso-as-is.md              # BPMN AS-IS
├── 02-rediseno-to-be.md             # BPMN TO-BE
├── 03-requisitos.md                 # Requisitos RP-01 a RP-20
├── 04-historias-usuario.md          # HU-01 a HU-12
├── 07-criterios-aceptacion.md       # Gherkin (27+ escenarios)
├── 08-modelo-dominio.md             # Modelo de dominio (3 vistas UML)
├── 09-casos-de-uso.md               # 13 CU (incluye CU-13 Experto)
├── 10-diagramas-secuencia.md        # DSS-01, DSS-02
├── 11-diagramas-estado.md           # EST-01, EST-02
├── 12-trazabilidad.md               # Matriz RP ↔ HU ↔ CU ↔ DSS ↔ EST
├── diagramas/                       # Fuentes .puml + PNG/SVG exportados
├── app/                             # Código FastAPI + SQLite
│   ├── db/migrations/               # 001..005 (005 = Experto)
│   ├── templates/                   # Jinja2 (incluye experto_evaluacion.html)
│   └── ...
├── openspec/                        # Especificaciones OpenSpec
│   ├── changes/ajuste-hu-03-experto-revision/
│   └── specs/gestion-aportes/
├── tests/                           # 103 tests (pytest)
│   └── test_gherkin_hu03_experto.py # 6 tests nuevos flujo Experto
└── eval2/                           # Entregables Evaluación 2
    ├── CAMBIOS.md
    └── Presentacion_Evaluacion2_mapacheCorps.pptx
```
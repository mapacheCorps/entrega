# Torpedos universitarios

Documentación de Ingeniería de Requisitos, CIN324.
- [Entrega 1](./IngReq-Entrega%201.md)
- [Entrega 2](./IngReq-Entrega%202.md)

## Integrantes y responsables por artefacto (Evaluación 2)

| Integrante | Artefactos responsables (Evaluación 2) |
|------------|----------------------------------------|
| **Ignacio Rivera** | Casos de uso (CU-13, Actor Experto) |
| **Nicolás Lázcano** | HU y Gherkin (HU-03-CA4, 7 escenarios Experto), Implementación frontend (Templates Experto/Moderador/Feedback, selector rol) |
| **Sebastián Rojas** | Modelo de dominio y pruebas del flujo Experto |
| **Rodrigo Sances** | Diagramas de secuencia y matriz de trazabilidad |
| **Benjamín Isasmendi** | Implementación backend (ServicioRevisiones, endpoints, migración 005), Diagramas de estado (EST-01 EnRevisionExperto) |

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
3. Cambia el rol a **Experto** en el selector superior. En **Panel de Experto**,
   abre la versión derivada y descarga el apunte. Elige decisión
   (Aprobar/Rechazar/Solicitar corrección), escribe alcance y observaciones.
4. Si aprueba, abre la ficha del catálogo y verifica la versión publicada y quién la revisó.
   Si rechaza o pide corrección, cambia a **Estudiante** y consulta el detalle
   del aporte para ver las observaciones. La versión sigue fuera del catálogo.
5. Para mostrar la transición inválida, vuelve a la URL del formulario de evaluación
   después de decidir. El sistema informa que la versión ya fue resuelta.

La demo usa un Experto precargado. La especialidad requerida queda registrada en la
derivación. El correo automático de HU-05 y la autenticación institucional siguen previstos.

### Evaluación 2 — Cambio de requerimientos (Martes 24/11 → Jueves 26/11)

**Cambio implementado:** Incorporación de la figura de **Experto** para revisión de materias especializadas.

| Etiqueta Git | Descripción |
|--------------|-------------|
| `base-eval2` | Base de Entrega 3. HU-01 a HU-04, con HU-07 y HU-08 para consultar el catálogo. |
| `cambio-validado` | Referencia agregada al cierre sobre `c5871e4`, el corte del martes registrado por el curso. |
| `entrega-eval2` | Versión final con la demo, las pruebas, los artefactos actualizados y el cambio archivado. |

**Artefactos de la Evaluación 2:**
- [`eval2/CAMBIOS.md`](./eval2/CAMBIOS.md) — Registro de cambios por artefacto (requerido por rúbrica)
- [`eval2/Presentacion_Evaluacion2_mapacheCorps.pptx`](./eval2/Presentacion_Evaluacion2_mapacheCorps.pptx) — Presentación 5 min (mapa de impacto + reflexión por artefacto)
- [Cambio archivado en OpenSpec](./openspec/changes/archive/2026-11-26-ajuste-hu-03-experto-revision/) — Propuesta, diseño, especificación y tareas

### Pruebas

Desde la raíz del repositorio:
```
.\.venv\Scripts\python.exe -m pytest
```
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
│   ├── db/migrations/               # 001..006 (005 y 006 = flujo Experto)
│   ├── templates/                   # Jinja2 (incluye experto_evaluacion.html)
│   └── ...
├── openspec/                        # Especificaciones OpenSpec
│   ├── changes/archive/
│   └── specs/gestion-aportes/
├── tests/                           # Servicio, HTTP y regresión
│   └── test_rutas_experto.py        # Tres decisiones del Experto por HTTP
└── eval2/                           # Entregables Evaluación 2
    ├── CAMBIOS.md
    └── Presentacion_Evaluacion2_mapacheCorps.pptx
```

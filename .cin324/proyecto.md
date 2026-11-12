# Estado del proyecto — generación de la aplicación

## Proyecto
- Nombre: Torpedos universitarios
- Repositorio de documentación: esta carpeta
- Última auditoría: 2026-11-05 — resultado: con supuestos

## Mapa de artefactos (rutas detectadas)
| Artefacto | Ruta(s) | Estado |
|-----------|---------|--------|
| BPMN AS-IS | `01-proceso-as-is.md`; `diagramas/as-is-publicacion.bpmn` y `as-is-busqueda.bpmn` (+ PNG) | completo |
| BPMN TO-BE | `02-rediseno-to-be.md`; `diagramas/to-be-publicacion.bpmn`, `to-be-busqueda.bpmn`, `to-be-reportes.bpmn` (+ PNG) | completo |
| Historias de usuario | `04-historias-usuario.md` (HU-01 a HU-11) | completo |
| Criterios Gherkin | `07-criterios-aceptacion.md` (27 escenarios) | completo |
| Modelo de dominio | `08-modelo-dominio.md`; `diagramas/modelo-dominio.puml`, `modelo-dominio-gestion.puml`, `modelo-dominio-clasificacion.puml` (+ PNG) | completo, con huecos registrados como supuestos |
| Casos de uso | `09-casos-de-uso.md`; `diagramas/casos-de-uso.png` | completo; fuentes `.puml`/`.svg` desactualizadas (evidencia histórica) |
| Diagramas de estado | `11-diagramas-estado.md`; `diagramas/est-01.puml`, `est-02.puml` (+ PNG) | completo |
| Diagramas de secuencia | `10-diagramas-secuencia.md`; `diagramas/dss-01.puml`, `dss-02.puml`, `secuencia-hu-01-envio-aporte.puml`, `secuencia-hu-05-notificacion.puml` (+ PNG) | completo |
| Requisitos y atributos de calidad | `03-requisitos.md`; `06-atributos-calidad.md` | completo |

## Supuestos acordados (por elementos faltantes o dudosos)
- 2026-11-05 — Confirmado por el estudiante al responder «continuamos»:
  - **Casos de uso:** `09-casos-de-uso.md` y `diagramas/casos-de-uso.png` son la fuente de verdad. `08-diagramas-casos-uso-secuencia.md`, `casos-de-uso.puml` y `casos-de-uso.svg` quedan como evidencia histórica y no se usan para generar.
  - **Roles:** selector de rol de demostración con dos perfiles: **Estudiante** (autor) y **Moderador** (representa a la `ComunidadEstudiantil` del modelo). Sin autenticación real. Ayudante y Coordinador no se incluyen por ahora; se incorporarán cuando sus historias los requieran.
  - **Huecos del modelo:** se implementan como atributos y estados de base de datos: `Estudiante.disponible`, `Estudiante.ramosHabilitados`, `RevisionAcademica.alcance`, `ReporteError.resultado`, `ReporteError.accionTomada`, `ReporteError.fechaResolucion`; estados de `Aporte` y `ReporteError`. Si se desea, se actualizarán los documentos del curso mediante `cin324-validar-sistema`.
  - **Archivos:** se aceptan `.pdf`, `.docx`, `.pptx`, `.png`, `.jpg`; máximo 10 MB; el archivo no puede estar vacío; duplicado exacto por SHA-256.
  - **Plazo de 48 horas:** se evalúa al abrir el panel de coordinación o al pulsar «Evaluar plazos»; no hay proceso en segundo plano.
  - **Servicios externos:** almacenamiento de archivos y correo se simulan. Los archivos se guardan localmente y las notificaciones quedan en una bandeja/registro visible.
  - **Requisitos no funcionales:** RP-15, RP-16 y RP-17 se leen pero no se implementan como pruebas de rendimiento o usabilidad. RP-18 se cubre funcionalmente con el selector de rol y los escenarios de intento no autorizado.

## Stack (se define una sola vez)
- Lenguaje y framework: Python 3.14 + FastAPI + Jinja2
- Base de datos: SQLite — archivo `data/app.db`; migraciones SQL en `app/db/migrations/`
- Pruebas: pytest + `TestClient` de FastAPI
- Cómo instalar: `py -m venv .venv`; `.venv\Scripts\activate`; `pip install -r requirements.txt`
- Cómo ejecutar: `py -m app.db.seed`; `uvicorn app.main:app --reload` — URL: http://localhost:8000
- Cómo probar: `pytest`
- Stack confirmado por el estudiante: 2026-11-05

## Historias
| Historia | Estado | Cambio de OpenSpec | Fecha | Observaciones |
|----------|--------|--------------------|-------|----------------|
| HU-01 | hecha · validada y archivada | `openspec/changes/archive/2026-11-12-hu-01-enviar-clasificar-aporte` | 2026-11-12 | Código ajustado y 62 pruebas aprobadas. Selección dependiente y confirmación útil verificadas en navegador. Especificaciones sincronizadas a `openspec/specs/gestion-aportes/spec.md`. |
| HU-02 | pendiente | — | — | Requiere aportes registrados (HU-01). |
| HU-03 | pendiente | — | — | Requiere asignación/revisión (HU-02) y versiones. |
| HU-04 | pendiente | — | — | Requiere una revisión con corrección (HU-03). |
| HU-05 | pendiente | — | — | Requiere decisiones de revisión (HU-03). |
| HU-06 | pendiente | — | — | Requiere versiones publicadas (HU-03). |
| HU-07 | pendiente | — | — | Requiere versiones publicadas y revisión (HU-03). |
| HU-08 | pendiente | — | — | Requiere versiones publicadas (HU-03). |
| HU-09 | pendiente | — | — | Requiere versiones publicadas (HU-03). |
| HU-10 | pendiente | — | — | Requiere asignaciones y revisiones en curso (HU-02/HU-03). |
| HU-11 | pendiente | — | — | Requiere reportes confirmados (HU-09). |

## Validaciones
| Historia | Informe | Estado | Fecha |
|----------|---------|--------|-------|
| HU-01 | `.cin324/validaciones/VAL-HU-01-1.md` | validada por el estudiante; ajustes implementados y verificados | 2026-11-12 |

## Cambios posteriores
| Cambio | Historia afectada | Motivo | Fecha |
|--------|-------------------|--------|-------|
| Ajuste OBS-1/OBS-2 | HU-01 | Filtrar ramos por carrera y temas por ramo; mostrar solo información útil en la confirmación | 2026-11-12 |

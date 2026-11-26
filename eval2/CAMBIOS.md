# Cambios por el cambio de requerimientos — Evaluación 2

**Fecha:** 2026-11-24 (Martes)  
**Equipo:** mapacheCorps  
**Cambio solicitado:** Incorporar la figura de **Experto** para la revisión de apuntes de materias especializadas (según EVALUACION2.md)

---

## Resumen del cambio

El cambio requiere que, cuando un aporte corresponde a una materia especializada, la comunidad estudiantil pueda convocar a un **Experto** (persona con conocimiento especializado, puede ser un profesor externo) para que realice la revisión académica en lugar de o además de la comunidad.

---

## Artefactos afectados

| Artefacto | Qué cambió (antes → después) | Por qué el cambio lo exige | Responsable |
|-----------|------------------------------|----------------------------|-------------|
| **04-historias-usuario.md** (HU y Gherkin) | HU-03: Agregado criterio de aceptación **HU-03-CA4** — "Si el aporte presentado es de una materia específica tengo la opción de llamar a un experto para hacer la revisión." | El cambio pide explícitamente que exista la opción de llamar a un experto para revisar materias especializadas. | **Nicolás Lázcano** |
| **07-criterios-aceptacion.md** (Gherkin) | HU-03: Agregados 3 nuevos escenarios Gherkin: (1) Solicitud de revisión por Experto, (2) Aprobación por Experto, (3) Rechazo/corrección por Experto. | Cada regla del cambio debe tener su escenario Gherkin equivalente para trazabilidad y pruebas. | **Nicolás Lázcano** |
| **08-modelo-dominio.md** + **diagramas/modelo-dominio.puml** + **diagramas/modelo-dominio-gestion.puml** | Modelo de dominio: Nueva clase **Experto** (identificador, nombre, correo, especialidad). Relación `Experto "0..1" -- "0..*" RevisionAcademica : revisa como Experto`. Actualizada tabla de clases y relaciones. Decisiones de modelado incluyen al Experto como rol especializado. | El cambio crea una nueva entidad "Experto" que participa en la revisión académica. El modelo de dominio debe reflejar esta entidad y sus relaciones. | **Ignacio Rivera** |
| **09-casos-de-uso.md** + **diagramas/casos-de-uso.puml** | Nuevo actor **Experto en la materia**. Nuevo caso de uso **CU-13 Revisar aporte como Experto** (origen HU-03). Actor asociado a CU-13. Moderador también asociado a CU-13 (solicita la revisión). Reglas principales: agregada regla 6 sobre revisión por Experto. Notas: agregada CU-13. | El cambio introduce un nuevo actor externo y un nuevo caso de uso para la revisión por experto. | **Ignacio Rivera** |
| **10-diagramas-secuencia.md** + **diagramas/dss-02.puml** | DSS-02: Nuevo fragmento `alt Materia especializada - se requiere Experto` con actor `Experto en la materia`. Flujo: Comunidad solicita revisión → Sistema pide evaluación al Experto → Experto entrega evaluación → Sistema informa decisión → Correo notifica. Documentación actualizada con variante Experto. | El diagrama de secuencia del sistema debe mostrar cómo la comunidad deriva la revisión a un Experto y cómo este interactúa con el sistema. | **Rodrigo Sances** |
| **diagramas/secuencia-hu-05-notificacion.puml** | HU-05: Grupo "Decisión de revisión (HU-03)" con `alt Revisión por Comunidad` / `else Revisión por Experto`. Incluye mensajes `solicitarRevisionExperto`, `solicitarEvaluacion`, `entregarEvaluacion`, `registrarDecisionFinal` con datos del experto. Notificación cubre 3 decisiones: aprobada, rechazada, solicitud de corrección. | El flujo de notificación debe cubrir ambos orígenes de decisión (Comunidad y Experto). | **Rodrigo Sances** |
| **11-diagramas-estado.md** + **diagramas/est-01.puml** | EST-01: Nuevo estado **EnRevisionExperto**. Transiciones: `PendienteRevision --> EnRevisionExperto : solicitarRevisionExperto [materia especializada]`, `EnRevisionExperto --> Aprobada : evaluacionExperto [experto aprueba]`, `EnRevisionExperto --> Rechazada : evaluacionExperto [experto rechaza] / guardarFeedback`, `EnRevisionExperto --> RequiereCorreccion : evaluacionExperto [experto solicita correccion] / guardarFeedback`. Tabla de transiciones actualizada. | El diagrama de estados debe modelar el nuevo flujo de revisión por Experto como camino alternativo desde PendienteRevision. | **Benjamín Isasmendi** |
| **12-trazabilidad.md** | Matriz actualizada: RP-04, RP-06, RP-18, RP-20 incluyen ahora `Experto` y `CU-13` en columnas Caso de uso y Clases del dominio. Coherencia TO-BE actualizada para C03/C05 y RP-20. | La trazabilidad debe reflejar que el Experto y CU-13 participan en los requisitos de revisión, decisión y publicación. | **Rodrigo Sances** |
| **tests/test_gherkin_hu03_experto.py** (Tests) | 6 nuevos tests: solicitud Experto, aprobación Experto, rechazo Experto, corrección Experto, no autorizado Experto, simultáneas Comunidad+Experto. Total 103 tests pasan. | El cambio exige validar el flujo Experto con pruebas automáticas por cada escenario Gherkin nuevo. | **Sebastián Rojas** |

---

## Artefactos SIN cambios (y por qué)

| Artefacto | Justificación |
|-----------|---------------|
| **01-proceso-as-is.md** | El proceso AS-IS refleja el estado actual sin el cambio; no se modifica. |
| **02-rediseno-to-be.md** | El TO-BE ya describe actividades de revisión; el cambio es una especialización de P06/P09-P10, no una actividad nueva. |
| **03-requisitos.md** | Los requisitos RP-01 a RP-20 no cambian; el cambio afecta *cómo* se cumple RP-04/RP-06/RP-18, no los requisitos en sí. |
| **05-elicitacion.md** | Técnicas de elicitación no cambian. |
| **06-atributos-calidad.md** | Atributos de calidad no cambian. |
| **07-trazabilidad.md** | Corresponde a Entrega 1; se mantiene intacto. |
| **08-diagramas-casos-uso-secuencia.md** | Documento de apoyo; la info autoritativa está en 09, 10, 11. |
| **diagramas/modelo-dominio-clasificacion.puml** | Clasificación académica (Carrera, Ramo, Tema, Periodo) no se ve afectada por el rol Experto. |
| **diagramas/dss-01.puml** | DSS-01 cubre presentación de aporte (HU-01); el Experto interviene solo en revisión (HU-03/HU-05). |
| **diagramas/est-02.puml** | EST-02 cubre ciclo de vida de Notificación; no cambia por el origen de la decisión. |
| **diagramas/secuencia-hu-01-envio-aporte.puml** | HU-01 no involucra revisión por Experto. |
| **app/** (código) | La implementación se hará entre sesiones con `/cin324-generar-app`. |

---

## Validación del profesor (martes 24/11)

- [ ] Equipo explicó el cambio con sus palabras al profesor
- [ ] Profesor validó que el equipo entendió el cambio
- [ ] Commits realizados durante la sesión con autores responsables declarados:
  - HU y Gherkin: **Nicolás Lázcano**
  - Modelo de dominio: **Ignacio Rivera**
  - Casos de uso: **Ignacio Rivera**
  - Diagramas de secuencia: **Rodrigo Sances**
  - Diagramas de estado: **Benjamín Isasmendi**
  - Trazabilidad: **Rodrigo Sances**
  - Tests: **Sebastián Rojas**
- [ ] Sin asistentes de IA ni OpenCode abiertos durante la especificación

---

## Próximos pasos (entre sesiones)

1. Crear cambio `ajuste-experto-revision` en OpenSpec con `/cin324-generar-app`
2. Generar código y pruebas para CU-13 y flujo Experto en HU-03/HU-05
3. Ejecutar suite completa (pruebas nuevas + regresión)
4. Corregir artefactos si la implementación revela insuficiencias (commits posteriores a cambio-validado)
5. Preparar demostración y reflexión para jueves 26/11
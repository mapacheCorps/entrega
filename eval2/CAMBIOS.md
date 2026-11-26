# Cambios de la Evaluación 2

**Grupo 6 · Torpedos universitarios**

El Moderador puede derivar la versión vigente de un apunte especializado a un Experto. El Experto consulta la bandeja, descarga la versión y registra una decisión fundamentada. La aprobación publica esa versión. El rechazo y la solicitud de corrección dejan observaciones para el autor.

## Versiones de referencia

| Versión | Evidencia |
|---|---|
| `base-eval2` | Base de la Entrega 3. |
| [`c5871e4`](https://github.com/mapacheCorps/entrega-1/tree/c5871e4) | Corte del martes 24/11 en el [seguimiento del curso](https://shimmering-sprite-afb4dd.netlify.app/). Se registró el cambio en `EVALUACION2.md`, se añadió HU-03-CA4 y se actualizó el material de dominio y estado, incluido el [boceto de EST-01](../diagramas/est1-01-ev3.png). La etiqueta `cambio-validado` se añadió posteriormente sobre este commit. |
| [`b784aff`](https://github.com/mapacheCorps/entrega-1/tree/b784aff) | Versión publicada que se compara en el PPT. Contenía los modelos detallados del Experto y la implementación inicial. En el ensayo HTTP, la versión derivada no aparecía en la bandeja y enviar la evaluación devolvía 500. |
| `entrega-eval2` | Versión de entrega con las correcciones posteriores, pruebas HTTP, exportaciones UML y cambio OpenSpec archivado. |

## Cambios por artefacto

| Artefacto | Antes y después | Por qué | Responsable |
|---|---|---|---|
| [HU y Gherkin](../07-criterios-aceptacion.md) | El martes HU-03-CA4 introdujo la opción de llamar a un Experto. Los escenarios posteriores detallan derivación, aprobación, rechazo, corrección y autorización. | Cada decisión tiene un resultado verificable para la versión y su autor. | Nicolás Lázcano |
| [Modelo de dominio](../08-modelo-dominio.md) | La propuesta del martes introduce al Experto. Las fuentes finales muestran su relación con `RevisionAcademica`, un único revisor por decisión y la especialidad requerida en `VersionApunte`. | Distingue quién solicitó la revisión, qué especialidad pidió y quién decidió. | Sebastián Rojas |
| [Casos de uso](../09-casos-de-uso.md) | CU-03 conserva la revisión comunitaria. CU-13 agrega la solicitud del Moderador y la evaluación del Experto. | Derivar y evaluar son operaciones con responsabilidades y permisos distintos. | Ignacio Rivera |
| [Diagramas de secuencia](../10-diagramas-secuencia.md) | DSS-02 del martes muestra revisión comunitaria. El final agrega derivación, consulta de bandeja, descarga, evaluación y rechazo de una segunda decisión. | El Experto necesita acceder a la versión exacta y registrar su propia decisión. | Rodrigo Sances |
| [Diagramas de estado](../11-diagramas-estado.md) | El boceto anotaba una excepción de revisión experta y una referencia a 24 horas. EST-01 formaliza `PendienteRevision` → `EnRevisionExperto` y sus tres resultados. EST-02 conserva los estados del aviso propuesto. | La bandeja y la validación de una decisión dependen del estado de la versión. El límite del boceto no está en el alcance implementado. | Benjamín Isasmendi |
| [Trazabilidad](../12-trazabilidad.md) | RP-04, RP-06, RP-18 y RP-20 incorporan CU-13 y Experto. La fila HU-03-CA4 enlaza las rutas y pruebas HTTP. | Permite seguir el cambio hasta su implementación y su verificación. | Rodrigo Sances |

El AS-IS, la clasificación académica, DSS-01 y EST-02 mantienen el alcance original. El cambio añade una vía de revisión en el TO-BE existente. La identidad del Experto se simula en el selector de la demo. La autenticación institucional y el correo real continúan como funcionalidades previstas.

## Correcciones posteriores y evidencia

- La bandeja consulta versiones en `EnRevisionExperto`, aunque todavía no tengan un dictamen. La migración 006 guarda la especialidad solicitada y la comunidad que derivó.
- La ruta de evaluación recibe el identificador del Experto y aplica el guardado de la decisión sobre la versión vigente. La ficha pública muestra el revisor correcto. El detalle del autor muestra el feedback experto cuando corresponde.
- Las [pruebas HTTP de HU-03-CA4](../tests/test_rutas_experto.py) cubren derivación, autorización, archivo exacto, las tres decisiones y el bloqueo de una segunda decisión. La suite completa pasó **106 pruebas**.
- Se regeneraron las exportaciones de dominio, casos de uso, DSS-02, EST-01 y la secuencia de HU-05 a partir de sus fuentes. El [cambio de OpenSpec](../openspec/changes/archive/2026-11-26-ajuste-hu-03-experto-revision/) se validó y sincronizó antes de archivarlo.
- La [presentación del grupo](./Presentacion_Evaluacion2_mapacheCorps.pptx) contiene las comparaciones visuales de `c5871e4` y `b784aff`. Las notas incluyen los hallazgos de la verificación posterior.

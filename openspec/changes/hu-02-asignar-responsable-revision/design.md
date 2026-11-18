# Diseño de la asignación de revisiones

## Contexto

HU-01 ya deja el `Aporte` en `PendienteAsignacion` y su última `VersionApunte` en `PendienteRevision` tras la validación. SQLite limita actualmente `aportes.estado` a dos valores y exige un rol de demostración único por fila de `estudiantes`. La ficha confirmada de HU-02 completa el flujo de CU-02 a partir de P05 y de los dos escenarios Gherkin porque el caso de uso carece de un DSS propio.

## Objetivos y alcance técnico

- Incorporar las relaciones de comunidad, elegibilidad y asignación en SQLite, preservando los identificadores, los aportes y el historial de versiones existentes.
- Reutilizar el selector de perfiles y el catálogo académico. La asignación usa los datos locales y carece de llamadas a almacenamiento, correo u otros servicios externos.
- EST-01 reserva la transición a `EnRevision` para el inicio de la revisión comunitaria. En HU-02 la versión permanece en `PendienteRevision`. La transición de `AsignacionRevision` a `Finalizada` se implementará con HU-03.

## Decisiones

### Persistencia y perfiles

La nueva migración numerada `002_asignacion_revision.sql` amplía el esquema de HU-01. La siguiente estructura deriva de las clases y asociaciones del modelo de dominio y de las decisiones de la ficha.

| Tabla | Cambio |
|---|---|
| `comunidades_estudiantiles` | Identificador y nombre de la comunidad organizadora. |
| `estudiantes` | Agregar `comunidad_id` y `disponible`, con disponibilidad inicialmente desactivada. Mantener la unicidad de los dos perfiles de demostración y permitir un rol nulo para los revisores que no aparecen en el selector. El perfil Moderador sigue representando a la comunidad. |
| `estudiantes_ramos_habilitados` | Clave compuesta por estudiante y ramo para registrar habilitaciones. |
| `aportes` | Ampliar la restricción de estado para admitir `Asignado`, conservando los estados de HU-01. |
| `asignaciones_revision` | Identificador, fecha, estado y referencias obligatorias a aporte, revisor y comunidad. Un índice único parcial por aporte para el estado `Asignada` garantiza una única asignación vigente y permite conservar el historial. |

El seed identifica por claves estables la comunidad y los revisores de ejemplo, conserva los perfiles existentes y reemplaza la limpieza legada de roles por una lógica compatible con revisores sin perfil. Habrá ramos con revisor disponible y al menos uno sin revisor. El Moderador se vincula a la comunidad organizadora mediante los datos de ejemplo y el selector sigue mostrando Estudiante y Moderador.

### Asignación y consistencia

El servicio obtiene un bloqueo de escritura de SQLite antes de consultar la asignación vigente, los estados y la carga de los candidatos. La última versión se determina por el mayor número de versión del aporte. La consulta filtra por comunidad organizadora, habilitación, disponibilidad e identidad distinta del autor. Ordena por número de asignaciones en estado `Asignada` y luego por identificador ascendente.

Si existe una asignación vigente, el servicio devuelve ese registro. Para un aporte elegible con candidato crea la asignación y actualiza el aporte a `Asignado` en una sola transacción. Con cero candidatos devuelve el resultado «sin revisor» sin escribir. Un fallo revierte toda la operación, y los reintentos consultan la asignación vigente antes de intentar otra.

### Panel y rutas propuestas

| Interacción de CU-02 reconstruida en la ficha | Ruta |
|---|---|
| Abrir el panel y consultar aportes por asignar | `GET /moderacion/aportes` |
| Organizar la revisión del aporte elegido | `POST /moderacion/aportes/{aporte_id}/asignar` |

Las rutas validan el perfil con el selector actual. La lista muestra ramo, tema y período de cada aporte elegible. Tras la operación, el Moderador ve la identificación del responsable y el estado del aporte, o el mensaje de falta de revisor con el aporte todavía visible. Una solicitud directa para un aporte inexistente responde 404 y para uno que requiere corrección se informa que no está disponible para asignación. El selector es de demostración.

## Riesgos y migración

- Los cambios en las restricciones de `estudiantes` y `aportes` requieren reconstruir las tablas padre. La migración conserva las claves primarias, los índices y las referencias de `versiones_apunte`. Si se desactivan claves foráneas para la reconstrucción, hacerlo fuera de la transacción, registrar la migración dentro de la misma transacción de escritura, verificar `foreign_key_check` antes de confirmar y reactivar la comprobación al terminar.
- Verificar la migración sobre una base nueva y sobre una base con datos de HU-01, incluyendo un aporte corregido con su historial. Si la validación de integridad falla, revertir la migración antes de registrar su aplicación.
- Las solicitudes concurrentes pueden intentar asignar el mismo aporte. La transacción serializa la selección y la actualización, y el índice único parcial protege la asignación vigente.

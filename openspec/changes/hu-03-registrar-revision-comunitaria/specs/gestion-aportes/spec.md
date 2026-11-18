# Revisión comunitaria y publicación

## ADDED Requirements

### Requirement: Inicio de la revisión de la versión asignada

El sistema DEBE permitir al Moderador de la comunidad responsable consultar la versión actual y su archivo, ver al revisor designado e iniciar la revisión si existe una asignación vigente. El inicio cambia la versión de `PendienteRevision` a `EnRevision`.

#### Scenario: Inicio de revisión comunitaria

- **GIVEN** existe un aporte asignado a la comunidad del Moderador y su última versión está en `PendienteRevision`
- **WHEN** el Moderador abre el aporte e inicia la revisión
- **THEN** puede consultar el archivo de esa versión y la identidad del estudiante designado
- **AND** la versión queda en `EnRevision` con su asignación vigente

### Requirement: Aprobación y publicación de la versión revisada

El sistema DEBE registrar la aprobación de la versión actual en revisión, con fecha, alcance, observaciones, revisor y comunidad. DEBE publicar esa misma versión, actualizar el aporte a `Publicado` y finalizar la asignación.

#### Scenario: Aprobación de versión revisada

- **GIVEN** existe una versión `EnRevision` con revisión realizada y un estudiante designado por la comunidad
- **WHEN** el Moderador de esa comunidad registra la aprobación con alcance y observaciones
- **THEN** la decisión queda asociada a esa versión, a la fecha, al revisor designado y a su comunidad
- **AND** esa versión pasa a `Aprobada` y luego a `Publicada` y aparece en el catálogo básico
- **AND** el aporte queda `Publicado` y la asignación queda `Finalizada`

### Requirement: Rechazo fundamentado de la versión revisada

El sistema DEBE registrar el rechazo de la versión actual en revisión con alcance y retroalimentación concreta. DEBE dejar el aporte en `Rechazado`, finalizar la asignación y mantener la versión fuera del catálogo.

#### Scenario: Rechazo o solicitud de corrección

- **GIVEN** existe una versión `EnRevision` y el estudiante designado representa a la comunidad
- **WHEN** el Moderador de esa comunidad registra el rechazo con alcance y retroalimentación concreta
- **THEN** queda guardada la decisión sobre esa versión con la fecha, el alcance, el revisor, la comunidad y el feedback
- **AND** la versión queda `Rechazada` y sigue fuera del catálogo
- **AND** la asignación queda `Finalizada`

### Requirement: Solicitud de corrección académica

El sistema DEBE registrar la solicitud de corrección como una decisión con alcance y retroalimentación concreta. La versión queda en `RequiereCorreccion`, el aporte en `CorreccionSolicitada` y la asignación en `Finalizada`. La versión sigue fuera del catálogo.

#### Scenario: Solicitud de corrección con observaciones

- **GIVEN** existe una versión actual `EnRevision` con una asignación vigente
- **WHEN** el Moderador de la comunidad responsable registra una solicitud de corrección con alcance y observaciones
- **THEN** la solicitud queda guardada para la versión exacta, con la fecha, el revisor, la comunidad, el alcance y las observaciones
- **AND** la versión queda en `RequiereCorreccion`, el aporte en `CorreccionSolicitada` y la asignación en `Finalizada`
- **AND** la versión sigue fuera del catálogo y el aporte queda fuera del formulario de corrección de archivos inválidos de HU-01

### Requirement: Autorización de la revisión comunitaria

El sistema DEBE limitar la consulta de archivos para revisión, el inicio y el registro de decisiones al Moderador de la comunidad con una asignación vigente sobre el aporte. DEBE usar la identidad del estudiante designado en la asignación.

#### Scenario: Intento no autorizado

- **GIVEN** existe una versión pendiente de revisión o en revisión y el interesado no actúa como Moderador de la comunidad responsable
- **WHEN** el interesado intenta registrar aprobación
- **THEN** el sistema deniega la decisión y conserva el estado de la versión, del aporte y de la asignación
- **AND** no se crea una revisión ni cambia la publicación

### Requirement: Consistencia del registro de la decisión académica

El sistema DEBE exigir alcance y observaciones y solo admitir una decisión de HU-03 sobre la versión actual en `EnRevision`. DEBE guardar juntos la decisión, los estados resultantes y el cierre de la asignación.

#### Scenario: Decisión sin información obligatoria

- **GIVEN** el Moderador de la comunidad responsable está revisando una versión con asignación vigente
- **WHEN** intenta registrar una decisión sin indicar alcance u observaciones
- **THEN** el sistema indica qué debe completar y conserva la revisión en curso sin registrar la decisión

#### Scenario: Decisión repetida o sobre una versión anterior

- **GIVEN** la versión ya tiene una decisión registrada o dejó de ser la versión actual del aporte
- **WHEN** el Moderador intenta registrar otra decisión sobre esa versión
- **THEN** el sistema rechaza la operación y conserva la decisión, la asignación y la publicación existentes

### Requirement: Catálogo de versiones publicadas

El sistema DEBE mostrar en el catálogo básico únicamente las versiones en `Publicada` con una revisión aprobatoria asociada a esa misma versión.

#### Scenario: Consulta de versiones publicadas

- **GIVEN** existen versiones pendientes, aprobadas y publicadas, rechazadas y con corrección solicitada
- **WHEN** se abre el catálogo básico
- **THEN** solo se muestran las versiones publicadas que cuentan con aprobación propia

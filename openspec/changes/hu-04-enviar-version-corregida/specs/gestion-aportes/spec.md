# Reenvío tras la revisión académica

## ADDED Requirements

### Requirement: Consulta del feedback por el autor

El sistema DEBE mostrar al autor la decisión, el alcance y las observaciones de cada rechazo o solicitud de corrección en el detalle del aporte. Cada registro DEBE identificar la versión revisada y seguir visible tras un reenvío.

#### Scenario: El autor consulta la revisión de una versión anterior

- **GIVEN** una versión del aporte recibió una decisión de rechazo o corrección con observaciones
- **WHEN** el autor abre el detalle del aporte antes o después de reenviar
- **THEN** ve la decisión y las observaciones asociadas al número de la versión revisada

### Requirement: Nueva versión del mismo aporte tras una decisión académica

El sistema DEBE permitir que el autor reenvíe un archivo para la versión vigente de un aporte en `Rechazado` o `CorreccionSolicitada`. Un reenvío válido DEBE conservar el identificador, la clasificación y la procedencia del aporte y crear la versión siguiente con una revisión independiente.

#### Scenario: Nueva versión del mismo aporte

- **GIVEN** la versión vigente fue rechazada y su autor puede consultar las observaciones
- **WHEN** el autor envía un archivo corregido que supera la validación y el resguardo
- **THEN** se crea una versión con un número nuevo, asociada al mismo aporte
- **AND** la versión anterior pasa a `Final` y conserva su decisión y su archivo
- **AND** la nueva versión queda en `PendienteRevision` sin heredar una decisión
- **AND** el aporte pasa a `PendienteAsignacion` y el autor ve la nueva versión

#### Scenario: Reenvío después de una solicitud de corrección

- **GIVEN** el aporte está en `CorreccionSolicitada` y su versión vigente conserva el feedback académico
- **WHEN** su autor reenvía un archivo válido y se confirma el resguardo
- **THEN** se registra la versión siguiente del mismo aporte y vuelve a asignación
- **AND** la versión anterior queda en `Final` con su revisión intacta

### Requirement: Validación del archivo reenviado

El sistema DEBE aplicar la validación de archivos y duplicados exactos de HU-01. Si falta el archivo, es inválido o es un duplicado exacto, DEBE informar la causa y conservar el aporte, su versión vigente y su revisión para que el autor pueda reintentar.

#### Scenario: Corrección inválida

- **GIVEN** existe un aporte rechazado con retroalimentación y el archivo corregido incumple una regla de validación
- **WHEN** el autor presenta el archivo
- **THEN** se muestran los incumplimientos y el aporte sigue en su estado anterior
- **AND** no se crea una versión ni se envía el archivo inválido a revisión

#### Scenario: Reenvío duplicado

- **GIVEN** el archivo que el autor adjunta ya está registrado con el mismo contenido
- **WHEN** intenta reenviarlo
- **THEN** se informa la coincidencia exacta sin tratarla como aprobación
- **AND** se conserva la versión vigente y su feedback

### Requirement: Consistencia del reenvío académico

El sistema DEBE confirmar juntos el cierre de la versión anterior, el registro de la nueva y el retorno a asignación. Si falla el resguardo o el registro, DEBE informar el error y conservar el estado previo. Un reenvío para una versión que dejó de ser la vigente DEBE rechazarse.

#### Scenario: Fallo al resguardar o registrar la corrección

- **GIVEN** el autor presenta un archivo corregido válido para la versión vigente
- **WHEN** falla su resguardo o la confirmación del registro
- **THEN** se informa que el reenvío no se pudo confirmar
- **AND** la versión anterior sigue vigente con su revisión y el autor puede reintentar

#### Scenario: Segundo envío sobre una versión reemplazada

- **GIVEN** un reenvío válido ya reemplazó la versión que indica el formulario
- **WHEN** se envía otra corrección desde ese formulario
- **THEN** se informa que la versión dejó de estar disponible para reenviar
- **AND** no se crea otra versión ni se modifica la ya confirmada

### Requirement: Acceso al feedback y reenvío del propio aporte

El sistema DEBE verificar que el perfil Estudiante corresponda al autor registrado en el aporte antes de mostrar el feedback académico o permitir el reenvío.

#### Scenario: Consulta o reenvío por una persona distinta del autor

- **GIVEN** existe un aporte con rechazo o con una solicitud de corrección
- **WHEN** una persona que no actúa como su autor intenta consultar su feedback o enviar otra versión
- **THEN** el sistema no muestra esas observaciones ni modifica el aporte o su historial

# Cambio HU-03 / CU-13

## ADDED Requirements

### Requirement: Solicitud de revisión por Experto para materia especializada

El sistema DEBE (MUST) permitir al Moderador derivar la versión vigente pendiente, conservar la especialidad solicitada y mostrar el archivo en la bandeja del Experto de demostración.

#### Scenario: HU-03-CA4 Derivación válida

- **WHEN** el Moderador deriva una versión vigente pendiente e indica la especialidad
- **THEN** la versión pasa a `EnRevisionExperto`, sale de la cola comunitaria y aparece en la bandeja experta con la especialidad solicitada
- **AND** el Experto puede descargar esa versión antes de decidir

#### Scenario: HU-03-CA4 Derivación inválida

- **WHEN** se intenta derivar una versión ya resuelta o se omite la especialidad
- **THEN** se rechaza la solicitud y se conserva el estado

#### Scenario: HU-03-CA4 Operación sin permiso

- **WHEN** un perfil distinto del Moderador intenta derivar, o uno distinto del Experto intenta evaluar o descargar desde la bandeja
- **THEN** se deniega el acceso sin cambiar el estado

## MODIFIED Requirements

### Requirement: Una decisión por versión y autoría de moderación

El sistema DEBE (MUST) guardar en una transacción la primera decisión válida de la versión vigente, con la identidad del Moderador o Experto, su tipo de revisor, comunidad, fecha, alcance y observaciones. La revisión experta conserva además la especialidad del revisor.

#### Scenario: Decisiones sobre la misma versión

- **WHEN** un Moderador o Experto intenta resolver una versión que ya tiene decisión
- **THEN** se informa que la versión ya fue resuelta y se conserva la primera decisión

### Requirement: Aprobación y publicación de la versión revisada

El sistema DEBE (MUST) registrar la aprobación y publicar esa misma versión en una operación, tanto en la vía comunitaria como en la experta.

#### Scenario: Aprobación de versión revisada

- **WHEN** el revisor autorizado aprueba una versión vigente en su vía de revisión
- **THEN** la decisión se asocia a la versión exacta con fecha, identidad, alcance y observaciones
- **AND** la versión queda `Publicada` y el aporte `Publicado`
- **AND** la ficha del catálogo muestra la identidad del revisor y su especialidad si corresponde

### Requirement: Rechazo fundamentado de la versión revisada

El sistema DEBE (MUST) registrar el rechazo de la versión con alcance y retroalimentación concreta, identificar al revisor y mantener la versión fuera del catálogo.

#### Scenario: Rechazo o solicitud de corrección

- **WHEN** el revisor autorizado registra un rechazo con su fundamento
- **THEN** la versión queda `Rechazada` y el autor puede consultar el feedback de esa versión

### Requirement: Solicitud de corrección académica

El sistema DEBE (MUST) registrar la corrección académica como decisión con alcance y observaciones. Mantiene la versión fuera del catálogo y separada de la corrección de archivos inválidos de HU-01.

#### Scenario: Solicitud de corrección con observaciones

- **WHEN** el Moderador o Experto registra una solicitud de corrección de la versión vigente en revisión
- **THEN** la versión queda `RequiereCorreccion`, el aporte queda `CorreccionSolicitada` y el autor puede consultar las observaciones de esa versión

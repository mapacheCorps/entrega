# Cola compartida de revisión

## ADDED Requirements

### Requirement: Acceso directo al aporte pendiente

El sistema DEBE permitir a cualquier Moderador consultar la versión vigente y validada del aporte y resolverla desde la cola compartida. Abrirla no cambia su estado ni la reserva.

#### Scenario: Aporte disponible en la cola compartida

- **WHEN** un Moderador abre un aporte pendiente
- **THEN** accede a la versión y al formulario sin asignación previa
- **AND** otro Moderador puede abrir esa misma versión mientras siga pendiente

#### Scenario: Perfil sin autorización

- **WHEN** un Estudiante intenta abrir la cola o decidir sobre el aporte
- **THEN** el sistema deniega el acceso sin cambiar la versión

### Requirement: Una decisión por versión y autoría de moderación

El sistema DEBE persistir la primera decisión válida sobre la versión vigente en una transacción y conservar el Moderador que la registró, la fecha, el alcance y las observaciones.

#### Scenario: Decisiones sobre la misma versión

- **WHEN** dos Moderadores intentan resolver la misma versión pendiente
- **THEN** se registra solo la primera decisión válida y el segundo recibe un aviso

### Requirement: Retorno de la versión corregida a la cola

El sistema DEBE dejar la versión corregida válida pendiente de revisión en la cola compartida y conservar las decisiones de versiones anteriores.

#### Scenario: Reenvío válido

- **WHEN** el autor reenvía una versión corregida válida
- **THEN** la nueva versión queda disponible para revisión directa sin heredar la decisión previa

## MODIFIED Requirements

### Requirement: Registro de un aporte válido

El sistema DEBE registrar un `Aporte` y su primera `VersionApunte` cuando el autor adjunta un archivo no vacío, declara procedencia, carrera, ramo, período académico y tema, y el archivo cumple el formato y tamaño permitidos. El `Aporte` queda en estado `PendienteRevision` y la versión en `PendienteRevision`; ninguno se publica.

#### Scenario: Registro de aporte completo

- **GIVEN** existe un estudiante autor que aporta un archivo no vacío
- **AND** el archivo cumple el formato y tamaño configurados y se declara carrera, ramo, período académico, tema y procedencia
- **WHEN** el autor presenta el aporte
- **THEN** el sistema registra el aporte y su primera versión
- **AND** la versión queda disponible para cualquier Moderador en la cola de revisión, sin publicarse

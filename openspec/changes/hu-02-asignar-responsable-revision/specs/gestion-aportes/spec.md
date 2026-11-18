# Asignación de responsables de revisión

## ADDED Requirements

### Requirement: Asignación de un revisor elegible

El sistema DEBE asignar el aporte validado a un estudiante de la comunidad disponible, habilitado para su ramo y distinto del autor. DEBE conservar la identificación del responsable y de la comunidad organizadora. Entre los elegibles, prioriza al estudiante con menos asignaciones activas (estado `Asignada`) y, en empate, al de menor identificador.

#### Scenario: Estudiante de la comunidad disponible

- **GIVEN** existe un aporte en `PendienteAsignacion` cuya última versión está en `PendienteRevision`
- **AND** existe un estudiante de la comunidad habilitado para el ramo, disponible y distinto del autor
- **WHEN** la comunidad organiza la revisión mediante el perfil Moderador
- **THEN** el sistema registra una `AsignacionRevision` en estado `Asignada`, con fecha e identificación del responsable y de la comunidad organizadora
- **AND** el aporte queda en `Asignado` y la interfaz muestra el estado y el responsable
- **AND** la última versión sigue en `PendienteRevision`

### Requirement: Continuidad del aporte sin revisor

El sistema DEBE mantener el aporte visible y en `PendienteAsignacion` si no hay un estudiante elegible y DEBE informar la falta de revisor a la comunidad. El intento no crea una asignación ni aprueba o publica el material.

#### Scenario: Sin estudiantes revisores disponibles

- **GIVEN** existe un aporte en `PendienteAsignacion` cuya última versión está en `PendienteRevision`
- **AND** no hay un estudiante elegible para revisar ese ramo
- **WHEN** la comunidad organiza la revisión mediante el perfil Moderador
- **THEN** el aporte sigue pendiente y visible en el panel
- **AND** el sistema muestra «Sin revisor disponible para este ramo» y aclara que el material sigue sin aprobarse ni publicarse
- **AND** el sistema no registra una asignación ni modifica la versión

### Requirement: Acceso y alcance de la organización de revisiones

El sistema DEBE reservar el panel y la operación de asignación al perfil Moderador. El panel DEBE listar los aportes en `PendienteAsignacion` cuya última versión esté en `PendienteRevision` y mostrar su ramo, tema y período académico. La operación DEBE comprobar los mismos estados al recibir la solicitud, salvo para mostrar una asignación vigente del aporte.

#### Scenario: Aporte que requiere corrección

- **GIVEN** existe un aporte en `RequiereCorreccion`
- **WHEN** el Moderador consulta los aportes pendientes o intenta asignar ese aporte directamente
- **THEN** el panel no ofrece el aporte y la solicitud directa no genera una asignación

#### Scenario: Acceso desde el perfil Estudiante

- **GIVEN** el perfil de demostración activo es Estudiante
- **WHEN** se intenta abrir el panel o solicitar una asignación
- **THEN** el sistema deniega el acceso y no modifica el aporte ni registra una asignación

### Requirement: Asignación vigente única por aporte

El sistema DEBE registrar la asignación y el nuevo estado del aporte como una operación indivisible. Si el aporte ya cuenta con una asignación vigente, el sistema DEBE mostrarla sin crear otra ni sustituir al responsable.

#### Scenario: Reintento sobre un aporte asignado

- **GIVEN** existe un aporte en `Asignado` con una asignación en estado `Asignada`
- **WHEN** el Moderador vuelve a solicitar la asignación
- **THEN** el sistema muestra la asignación existente y su responsable
- **AND** sigue existiendo una sola asignación vigente para el aporte

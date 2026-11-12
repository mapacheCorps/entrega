# Spec Delta — gestion-aportes

## Purpose

Permite que un estudiante autor entregue un apunte con su clasificación académica y que el sistema valide la entrada antes de remitirla a la revisión comunitaria, conservando la primera versión y el historial de correcciones.

## ADDED Requirements

### Requirement: Registro de un aporte válido

El sistema DEBE registrar un `Aporte` y su primera `VersionApunte` cuando el autor adjunta un archivo no vacío, declara procedencia, carrera, ramo, período académico y tema, y el archivo cumple el formato y tamaño permitidos. El `Aporte` queda en estado `PendienteAsignacion` y la versión en `PendienteRevision`; ninguno se publica.

#### Scenario: Registro de aporte completo

- **GIVEN** existe un estudiante autor que aporta un archivo no vacío
- **AND** el archivo cumple el formato y tamaño configurados y se declara carrera, ramo, período académico, tema y procedencia
- **WHEN** el autor presenta el aporte
- **THEN** el sistema registra el aporte y su primera versión
- **AND** la versión queda pendiente de asignación o revisión, sin publicarse

### Requirement: Clasificación académica dependiente

El sistema DEBE ofrecer en el formulario solo los ramos de la carrera seleccionada y solo los temas del ramo seleccionado. El período académico DEBE elegirse con independencia del ramo. La validación del servidor DEBE rechazar combinaciones incoherentes aunque se manipule la solicitud.

#### Scenario: Clasificación académica dependiente

- **GIVEN** el autor selecciona una carrera
- **WHEN** el sistema muestra los ramos disponibles
- **THEN** solo aparecen los ramos de esa carrera
- **AND** al seleccionar un ramo, solo aparecen sus temas o unidades
- **AND** el período académico se puede elegir con independencia del ramo

### Requirement: Confirmación con información útil para el autor

El sistema DEBE mostrar en la confirmación los identificadores del aporte y de la versión, la clasificación, el estado y la aclaración de que el aporte no se publica. NO DEBE mostrar el hash SHA-256, la referencia de almacenamiento, el tipo MIME ni la fecha de creación de la versión.

#### Scenario: Confirmación con información útil para el autor

- **GIVEN** el autor presenta un aporte válido
- **WHEN** el sistema confirma el registro
- **THEN** muestra los identificadores del aporte y de la versión, la clasificación, el estado y la aclaración de que aún no se publica
- **AND** no muestra el hash SHA-256, la referencia de almacenamiento, el tipo MIME ni la fecha de creación de la versión

### Requirement: Validación de datos y archivo

El sistema DEBE identificar la causa cuando faltan datos obligatorios o el archivo es inválido. Si faltan datos, no DEBE crear el aporte ni la versión. Si los datos están completos y el archivo es inválido, DEBE crear el `Aporte` y la `VersionApunte` en estado `RequiereCorreccion`, con `referenciaArchivo` nula, sin remitirlos a revisión. La corrección DEBE crear una versión nueva y cerrar la anterior como `Final`.

#### Scenario: Datos de aporte inválidos

- **GIVEN** el autor presenta un aporte con datos obligatorios faltantes o archivo inválido
- **WHEN** el autor presenta el aporte
- **THEN** se identifica la causa del incumplimiento
- **AND** no se remite la versión a revisión hasta corregirla

#### Scenario: Datos obligatorios faltantes no crean el aporte

- **GIVEN** el autor envía un aporte al que le falta procedencia, carrera, ramo, período, tema o archivo
- **WHEN** el autor presenta el aporte
- **THEN** el sistema muestra los campos o el archivo que deben corregirse
- **AND** no crea ningún `Aporte` ni `VersionApunte`

#### Scenario: Archivo inválido con datos completos queda en RequiereCorreccion

- **GIVEN** el autor declaró todos los datos de clasificación
- **AND** el archivo está vacío, supera los 10 MB o no tiene una extensión permitida
- **WHEN** el autor presenta el aporte
- **THEN** el sistema crea el `Aporte` y la `VersionApunte` en estado `RequiereCorreccion`
- **AND** deja `referenciaArchivo` nula
- **AND** no remite la versión a revisión

#### Scenario: La corrección de un archivo inválido crea una nueva versión

- **GIVEN** existe un `Aporte` con una `VersionApunte` en estado `RequiereCorreccion`
- **WHEN** el autor sube un archivo corregido y lo presenta
- **THEN** el sistema crea la versión siguiente
- **AND** la versión anterior pasa a estado `Final`
- **AND** la nueva versión se valida antes de remitirse a revisión

### Requirement: Detección de duplicado exacto

El sistema DEBE calcular el SHA-256 del archivo y compararlo con las versiones ya registradas. Si encuentra una coincidencia exacta, DEBE informar el aporte existente, no DEBE registrar el nuevo aporte y NO DEBE presentar la coincidencia como aprobación académica.

#### Scenario: Archivo duplicado exacto

- **GIVEN** existe un archivo idéntico ya registrado
- **WHEN** el autor presenta el aporte
- **THEN** se informa la coincidencia exacta
- **AND** la coincidencia no se interpreta como aprobación académica

### Requirement: Manejo del fallo del almacenamiento

El sistema DEBE informar un error y NO DEBE confirmar el registro del aporte cuando el servicio de almacenamiento simulado no puede resguardar el archivo. El autor DEBE poder reintentar el envío.

#### Scenario: Fallo del servicio de almacenamiento

- **GIVEN** el autor presenta un aporte con datos y archivo válidos
- **AND** el servicio de almacenamiento simulado falla
- **WHEN** el sistema intenta resguardar el archivo
- **THEN** el sistema informa el error
- **AND** no confirma el registro del aporte
- **AND** permite reintentar el envío

### Requirement: Reglas de archivo aceptadas

El sistema DEBE aceptar archivos `.pdf`, `.docx`, `.pptx`, `.png` y `.jpg`, con un tamaño máximo de 10 MB, y DEBE rechazar archivos vacíos o de otros formatos.

#### Scenario: Archivo de formato o tamaño no permitido

- **GIVEN** el autor adjunta un archivo vacío, de otro formato o de más de 10 MB
- **WHEN** el autor presenta el aporte
- **THEN** el sistema informa que el archivo no cumple las reglas configuradas
- **AND** no lo remite a revisión

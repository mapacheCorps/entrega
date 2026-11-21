# gestion-aportes Specification

## Purpose

Permite que un estudiante autor entregue un apunte con su clasificación académica y que el sistema valide la entrada antes de remitirla a la revisión comunitaria, conservando la primera versión y el historial de correcciones.

## Requirements

### Requirement: Registro de un aporte válido

El sistema DEBE registrar un `Aporte` y su primera `VersionApunte` cuando el autor adjunta un archivo no vacío, declara procedencia, carrera, ramo, período académico y tema, y el archivo cumple el formato y tamaño permitidos. El `Aporte` queda en estado `PendienteRevision` y la versión en `PendienteRevision`; ninguno se publica.

#### Scenario: Registro de aporte completo

- **GIVEN** existe un estudiante autor que aporta un archivo no vacío
- **AND** el archivo cumple el formato y tamaño configurados y se declara carrera, ramo, período académico, tema y procedencia
- **WHEN** el autor presenta el aporte
- **THEN** el sistema registra el aporte y su primera versión
- **AND** la versión queda disponible para cualquier Moderador en la cola de revisión, sin publicarse

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

### Requirement: Ficha de la misma versión publicada

El sistema DEBE mostrar la ficha de la versión seleccionada con procedencia, clasificación y evidencia de revisión de esa versión.

#### Scenario: Consultar versión desde el catálogo

- **WHEN** un estudiante abre una versión publicada desde el catálogo
- **THEN** la ficha muestra los antecedentes de esa versión y ofrece descargar su archivo

### Requirement: Vista previa o descarga del archivo exacto

El sistema DEBE revalidar que la versión siga publicada y que el archivo esté disponible para cada solicitud. Ofrece vista previa para PDF, PNG y JPG y descarga para los formatos admitidos.

#### Scenario: Archivo publicado disponible

- **WHEN** el estudiante solicita una vista previa admitida o una descarga
- **THEN** recibe el archivo de la misma versión seleccionada

#### Scenario: Versión retirada o archivo ausente

- **WHEN** el estudiante solicita una versión cuya publicación o archivo ya no está disponible
- **THEN** recibe un aviso y puede volver al catálogo

### Requirement: Aprobación y publicación de la versión revisada

El sistema DEBE registrar la aprobación de la versión actual pendiente de revisión, con fecha, alcance, observaciones, moderador y comunidad. DEBE publicar esa misma versión y actualizar el aporte a `Publicado`.

#### Scenario: Aprobación de versión revisada

- **GIVEN** existe una versión pendiente y un Moderador de una comunidad habilitada
- **WHEN** el Moderador registra la aprobación con alcance y observaciones
- **THEN** la decisión queda asociada a esa versión, a la fecha, al Moderador que la registró y a su comunidad
- **AND** esa versión pasa a `Aprobada` y luego a `Publicada` y aparece en el catálogo básico
- **AND** el aporte queda `Publicado`

### Requirement: Rechazo fundamentado de la versión revisada

El sistema DEBE registrar el rechazo de la versión actual pendiente de revisión con alcance y retroalimentación concreta. DEBE dejar el aporte en `Rechazado` y mantener la versión fuera del catálogo.

#### Scenario: Rechazo o solicitud de corrección

- **GIVEN** existe una versión pendiente y un Moderador puede registrar su decisión
- **WHEN** el Moderador registra el rechazo con alcance y retroalimentación concreta
- **THEN** queda guardada la decisión sobre esa versión con la fecha, el alcance, el revisor, la comunidad y el feedback
- **AND** la versión queda `Rechazada` y sigue fuera del catálogo

### Requirement: Solicitud de corrección académica

El sistema DEBE registrar la solicitud de corrección como una decisión con alcance y retroalimentación concreta. La versión queda en `RequiereCorreccion`, el aporte en `CorreccionSolicitada`. La versión sigue fuera del catálogo.

#### Scenario: Solicitud de corrección con observaciones

- **GIVEN** existe una versión actual pendiente y un Moderador de una comunidad habilitada
- **WHEN** el Moderador registra una solicitud de corrección con alcance y observaciones
- **THEN** la solicitud queda guardada para la versión exacta, con la fecha, el revisor, la comunidad, el alcance y las observaciones
- **AND** la versión queda en `RequiereCorreccion`, el aporte en `CorreccionSolicitada`
- **AND** la versión sigue fuera del catálogo y el aporte queda fuera del formulario de corrección de archivos inválidos de HU-01

### Requirement: Consulta del feedback por el autor

El sistema DEBE mostrar al autor la decisión, el alcance y las observaciones de cada rechazo o solicitud de corrección en el detalle del aporte. Cada registro DEBE identificar la versión revisada y seguir visible tras un reenvío.

#### Scenario: El autor consulta la revisión de una versión anterior

- **GIVEN** una versión del aporte recibió una decisión de rechazo o corrección con observaciones
- **WHEN** el autor abre el detalle del aporte antes o después de reenviar
- **THEN** ve la decisión y las observaciones asociadas al número de la versión revisada

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

### Requirement: Acceso al feedback y reenvío del propio aporte

El sistema DEBE verificar que el perfil Estudiante corresponda al autor registrado en el aporte antes de mostrar el feedback académico o permitir el reenvío.

#### Scenario: Consulta o reenvío por una persona distinta del autor

- **GIVEN** existe un aporte con rechazo o con una solicitud de corrección
- **WHEN** una persona que no actúa como su autor intenta consultar su feedback o enviar otra versión
- **THEN** el sistema no muestra esas observaciones ni modifica el aporte o su historial

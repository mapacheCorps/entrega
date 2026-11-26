# Spec Delta

## MODIFIED Requirements

### Requirement: Una decisión por versión y autoría de moderación
El sistema DEBE persistir la primera decisión válida sobre la versión vigente en una transacción y conservar **quién la registró** (Moderador de la Comunidad Estudiantil **o** Experto en la materia), la fecha, el alcance y las observaciones. La decisión incluye `tipo_revisor` (`comunidad` | `experto`) y `experto_id` (cuando aplica). Solo se confirma la primera decisión; intentos posteriores informan que la versión ya fue resuelta.

#### Scenario: Decisiones sobre la misma versión
- **WHEN** dos Moderadores intentan resolver la misma versión pendiente
- **THEN** se registra solo la primera decisión válida y el segundo recibe un aviso

#### Scenario: Primera decisión válida por Comunidad
- **WHEN** un Moderador registra decisión (aprobación/rechazo/corrección) sobre versión en `PendienteRevision` o `EnRevision`
- **THEN** se crea `RevisionAcademica` con `tipo_revisor = comunidad`, `moderador_id` del Moderador, fecha, alcance, observaciones
- **THEN** la versión transiciona a `EnRevision` y luego a `Aprobada`/`Rechazada`/`RequiereCorreccion` según decisión

#### Scenario: Primera decisión válida por Experto
- **WHEN** un Experto registra decisión (aprobación/rechazo/corrección) sobre versión en `EnRevisionExperto`
- **THEN** se crea `RevisionAcademica` con `tipo_revisor = experto`, `experto_id` del Experto, fecha, alcance, observaciones, especialidad
- **THEN** la versión transiciona a `Aprobada`/`Rechazada`/`RequiereCorreccion` según decisión

#### Scenario: Intento de decisión cuando ya existe una
- **WHEN** cualquier actor (Moderador o Experto) intenta registrar decisión sobre versión que ya tiene `RevisionAcademica`
- **THEN** el sistema rechaza la operación e informa que la versión ya fue resuelta
- **THEN** no se modifica la decisión existente ni el estado de la versión

---

### Requirement: Aprobación y publicación de la versión revisada
El sistema DEBE registrar la aprobación de la versión actual pendiente de revisión, con fecha, alcance, observaciones, **tipo de revisor** (Comunidad u Experto) e identidad del decisor. DEBE publicar esa misma versión y actualizar el aporte a `Publicado`.

#### Scenario: Aprobación de versión revisada
- **GIVEN** existe una versión pendiente y un Moderador de una comunidad habilitada
- **WHEN** el Moderador registra la aprobación con alcance y observaciones
- **THEN** la decisión queda asociada a esa versión, a la fecha, al Moderador que la registró y a su comunidad
- **AND** esa versión pasa a `Aprobada` y luego a `Publicada` y aparece en el catálogo básico
- **AND** el aporte queda `Publicado`

#### Scenario: Aprobación por Comunidad y publicación
- **WHEN** la Comunidad registra aprobación con observaciones sobre versión en `EnRevision`
- **THEN** se crea `RevisionAcademica` con `decision = aprobada`, `tipo_revisor = comunidad`
- **THEN** la versión pasa a `Aprobada` → `Publicada`
- **THEN** el aporte se marca como `Publicado`
- **THEN** se dispara notificación (HU-05) con enlace de publicación

#### Scenario: Aprobación por Experto y publicación
- **WHEN** el Experto registra aprobación con observaciones sobre versión en `EnRevisionExperto`
- **THEN** se crea `RevisionAcademica` con `decision = aprobada`, `tipo_revisor = experto`, `experto_id`, `especialidad`
- **THEN** la versión pasa a `Aprobada` → `Publicada`
- **THEN** el aporte se marca como `Publicado`
- **THEN** se dispara notificación (HU-05) con enlace de publicación

---

### Requirement: Rechazo fundamentado de la versión revisada
El sistema DEBE registrar el rechazo de la versión actual pendiente de revisión con alcance y retroalimentación concreta, **indicando si el rechazo provino de la Comunidad o del Experto**. DEBE dejar el aporte en `Rechazado` y mantener la versión fuera del catálogo.

#### Scenario: Rechazo o solicitud de corrección
- **GIVEN** existe una versión pendiente y un Moderador puede registrar su decisión
- **WHEN** el Moderador registra el rechazo con alcance y retroalimentación concreta
- **THEN** queda guardada la decisión sobre esa versión con la fecha, el alcance, el revisor, la comunidad y el feedback
- **AND** la versión queda `Rechazada` y sigue fuera del catálogo

#### Scenario: Rechazo por Comunidad
- **WHEN** la Comunidad registra rechazo con retroalimentación sobre versión en `EnRevision`
- **THEN** se crea `RevisionAcademica` con `decision = rechazada`, `tipo_revisor = comunidad`, feedback obligatorio
- **THEN** la versión pasa a `Rechazada`
- **THEN** el aporte queda en `Rechazado`
- **THEN** se dispara notificación (HU-05) con motivo de rechazo

#### Scenario: Rechazo por Experto
- **WHEN** el Experto registra rechazo con retroalimentación sobre versión en `EnRevisionExperto`
- **THEN** se crea `RevisionAcademica` con `decision = rechazada`, `tipo_revisor = experto`, `experto_id`, `especialidad`, feedback obligatorio
- **THEN** la versión pasa a `Rechazada`
- **THEN** el aporte queda en `Rechazado`
- **THEN** se dispara notificación (HU-05) con motivo de rechazo

---

### Requirement: Solicitud de corrección académica
El sistema DEBE registrar la solicitud de corrección como una decisión con alcance y retroalimentación concreta, **indicando si la solicitud provino de la Comunidad o del Experto**. La versión queda en `RequiereCorreccion`, el aporte en `CorreccionSolicitada`. La versión sigue fuera del catálogo.

#### Scenario: Solicitud de corrección con observaciones
- **GIVEN** existe una versión actual pendiente y un Moderador de una comunidad habilitada
- **WHEN** el Moderador registra una solicitud de corrección con alcance y observaciones
- **THEN** la solicitud queda guardada para la versión exacta, con la fecha, el revisor, la comunidad, el alcance y las observaciones
- **AND** la versión queda en `RequiereCorreccion`, el aporte en `CorreccionSolicitada`
- **AND** la versión sigue fuera del catálogo y el aporte queda fuera del formulario de corrección de archivos inválidos de HU-01

#### Scenario: Solicitud de corrección por Comunidad
- **WHEN** la Comunidad registra solicitud de corrección con observaciones sobre versión en `EnRevision`
- **THEN** se crea `RevisionAcademica` con `decision = correccion`, `tipo_revisor = comunidad`, observaciones obligatorias
- **THEN** la versión pasa a `RequiereCorreccion`
- **THEN** el aporte queda en `CorreccionSolicitada`
- **THEN** se dispara notificación (HU-05) con observaciones de corrección

#### Scenario: Solicitud de corrección por Experto
- **WHEN** el Experto registra solicitud de corrección con observaciones sobre versión en `EnRevisionExperto`
- **THEN** se crea `RevisionAcademica` con `decision = correccion`, `tipo_revisor = experto`, `experto_id`, `especialidad`, observaciones obligatorias
- **THEN** la versión pasa a `RequiereCorreccion`
- **THEN** el aporte queda en `CorreccionSolicitada`
- **THEN** se dispara notificación (HU-05) con observaciones de corrección

---

## ADDED Requirements

### Requirement: Registro de Experto para revisión especializada
El sistema DEBE permitir registrar la identidad y especialidad del Experto que evalúa una versión, asociándola a la `RevisionAcademica` correspondiente.

#### Scenario: Registro de datos del Experto en la revisión
- **WHEN** el Experto entrega su evaluación (aprobación/rechazo/corrección)
- **THEN** la `RevisionAcademica` incluye `experto_id`, `nombre_experto`, `correo_experto`, `especialidad_experto`
- **THEN** estos datos quedan consultables en la ficha del aporte y en el historial de revisiones

---

### Requirement: Transición a revisión por Experto desde estado pendiente
El sistema DEBE ofrecer la transición `PendienteRevision` → `EnRevisionExperto` mediante el evento `solicitarRevisionExperto` con guarda "materia especializada".

#### Scenario: Transición válida a EnRevisionExperto
- **WHEN** versión en `PendienteRevision` sin decisión previa
- **WHEN** Moderador solicita revisión por Experto indicando especialidad
- **THEN** versión pasa a `EnRevisionExperto`
- **THEN** se registra `especialidad_requerida` en la versión o en la solicitud

#### Scenario: Transición inválida (versión ya decidida)
- **WHEN** versión ya tiene `RevisionAcademica` registrada
- **WHEN** se intenta solicitar revisión por Experto
- **THEN** se rechaza la operación
- **THEN** la versión conserva su estado actual

---

### Requirement: Solicitud de revisión por Experto para materia especializada
El sistema DEBE permitir a la Comunidad derivar una versión pendiente de revisión a un Experto cuando la materia lo requiera. La versión transiciona a `EnRevisionExperto` y se registra la especialidad requerida.

#### Scenario: Derivación a Experto desde cola de moderación
- **WHEN** un Moderador identifica que la versión corresponde a materia especializada y solicita revisión por Experto
- **WHEN** el sistema valida que la versión está en `PendienteRevision` y no tiene decisión previa
- **THEN** la versión transiciona a `EnRevisionExperto`
- **THEN** se registra la solicitud con la `especialidad` requerida
- **THEN** el sistema notifica al Experto (simulado) para que evalúe la versión

#### Scenario: Transición inválida (versión ya decidida)
- **WHEN** versión ya tiene `RevisionAcademica` registrada
- **WHEN** se intenta solicitar revisión por Experto
- **THEN** se rechaza la operación
- **THEN** la versión conserva su estado actual

---

### Requirement: Evaluación del Experto y transición a estado final
El sistema DEBE procesar la evaluación del Experto (`evaluacionExperto`) con tres guardas: aprueba, rechaza, solicita corrección; cada una transiciona al estado final correspondiente (`Aprobada`, `Rechazada`, `RequiereCorreccion`).

#### Scenario: Experto aprueba → Aprobada
- **WHEN** versión en `EnRevisionExperto`
- **WHEN** Experto entrega evaluación con decisión = aprobada
- **THEN** versión pasa a `Aprobada` → `Publicada`
- **THEN** se crea `RevisionAcademica` con `tipo_revisor = experto`, decisión aprobada

#### Scenario: Experto rechaza → Rechazada
- **WHEN** versión en `EnRevisionExperto`
- **WHEN** Experto entrega evaluación con decisión = rechazada y feedback obligatorio
- **THEN** versión pasa a `Rechazada`
- **THEN** se crea `RevisionAcademica` con `tipo_revisor = experto`, decisión rechazada, feedback

#### Scenario: Experto solicita corrección → RequiereCorreccion
- **WHEN** versión en `EnRevisionExperto`
- **WHEN** Experto entrega evaluación con decisión = correccion y observaciones obligatorias
- **THEN** versión pasa a `RequiereCorreccion`
- **THEN** se crea `RevisionAcademica` con `tipo_revisor = experto`, decisión correccion, observaciones
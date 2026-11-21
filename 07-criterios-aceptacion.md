# Criterios de aceptación (Gherkin)

Se especifican las doce historias existentes en [Entrega 1](./04-historias-usuario.md). Los escenarios describen comportamientos del dominio; no prueban que el software esté implementado. Los servicios externos de almacenamiento/correo son propuestas de diseño.

## HU-01 : Enviar y clasificar un aporte
**Historia:** Como usuario que aporta material, quiero adjuntar y clasificar mi apunte, para que la comunidad lo reciba con la información necesaria.

**Origen:** [HU-01 en Entrega 1](./04-historias-usuario.md#hu-01).

```gherkin
Característica: Recepción de aporte

  Escenario: Registro de aporte completo
    Dado existe un autor que aporta un archivo no vacío
    Y el archivo cumple el formato y tamaño configurados y se declara carrera, ramo, período académico, tema y procedencia
    Cuando el autor presenta el aporte
    Entonces el sistema registra el aporte y su primera versión
    Y la versión queda pendiente de revisión en la cola compartida, sin publicarse

  Escenario: Datos de aporte inválidos
    Dado el autor presenta un aporte con datos obligatorios faltantes o archivo inválido
    Cuando el autor presenta el aporte
    Entonces se identifica la causa del incumplimiento
    Y no se publica ni se remite a revisión hasta corregirla

  Escenario: Archivo duplicado exacto
    Dado existe un archivo idéntico ya registrado
    Cuando el autor presenta el aporte
    Entonces se informa la coincidencia exacta
    Y la coincidencia no se interpreta como aprobación académica

  Escenario: Clasificación académica dependiente
    Dado el autor selecciona una carrera
    Cuando el sistema muestra los ramos disponibles
    Entonces solo aparecen los ramos de esa carrera
    Y al seleccionar un ramo, solo aparecen sus temas o unidades
    Y el período académico se puede elegir con independencia del ramo

  Escenario: Confirmación con información útil para el autor
    Dado un autor presenta un aporte válido
    Cuando el sistema confirma el registro
    Entonces muestra los identificadores del aporte y de la versión, la clasificación, el estado y la aclaración de que aún no se publica
    Y no muestra el hash SHA-256, la referencia de almacenamiento, el tipo MIME ni la fecha de creación de la versión

```

## HU-02 : Consultar aportes pendientes de revisión
**Historia:** Como Moderador, quiero abrir cualquier aporte pendiente desde una cola compartida, para revisar directamente su versión vigente.

**Origen:** [HU-02 en Entrega 1](./04-historias-usuario.md#hu-02).

```gherkin
Característica: Cola compartida de revisión

  Escenario: Consultar un aporte pendiente
    Dado existe un aporte validado cuya versión vigente está pendiente de revisión
    Cuando un Moderador abre la cola y selecciona el aporte
    Entonces puede abrir la versión y registrar una decisión sin asignación previa
    Y otro Moderador puede consultar el mismo aporte mientras siga pendiente

  Escenario: Acceso a la cola desde el perfil Estudiante
    Dado existe una versión pendiente
    Cuando un Estudiante intenta entrar a la cola de moderación
    Entonces el sistema deniega el acceso

```

## HU-03 : Registrar revisión comunitaria
**Historia:** Como integrante de la comunidad estudiantil, quiero registrar una decisión fundamentada sobre una versión, para aprobarla y publicarla o rechazarla con feedback.

**Origen:** [HU-03 en Entrega 1](./04-historias-usuario.md#hu-03).

```gherkin
Característica: Decisión de revisión académica

  Escenario: Aprobación de versión revisada
    Dado existe una versión pendiente de decisión con revisión realizada
    Y el Moderador que revisa puede tomar una decisión sobre esa versión
    Cuando la comunidad registra la aprobación con observaciones
    Entonces queda asociada a la versión la fecha y la identidad del revisor
    Y esa versión aprobada se publica

  Escenario: Rechazo o solicitud de corrección
    Dado existe una versión pendiente de decisión
    Y el Moderador que revisa puede tomar una decisión sobre esa versión
    Cuando la comunidad registra rechazo con retroalimentación concreta para el autor
    Entonces queda documentada la decisión sobre la versión
    Y la versión rechazada no se publica

  Escenario: Intento no autorizado
    Dado existe una versión pendiente de revisión
    Y el interesado no tiene el perfil Moderador
    Cuando el interesado intenta registrar aprobación
    Entonces se rechaza la decisión por falta de autorización
    Y no cambia el estado de publicación

  Escenario: Decisiones simultáneas
    Dado dos moderadores abrieron la misma versión pendiente
    Cuando ambos registran una decisión válida
    Entonces se confirma solo la primera decisión y se identifica al Moderador que la registró
    Y el segundo recibe un aviso de que la versión ya fue resuelta

```

## HU-04 : Enviar una versión corregida
**Historia:** Como autor de un aporte, quiero recibir observaciones y enviar una versión corregida, para resolver problemas sin perder el historial.

**Origen:** [HU-04 en Entrega 1](./04-historias-usuario.md#hu-04).

```gherkin
Característica: Corrección del aporte

  Escenario: Nueva versión del mismo aporte
    Dado existe un aporte cuya versión fue rechazada con retroalimentación
    Y el autor puede consultar el motivo y las observaciones
    Cuando el autor envía una nueva versión corregida
    Entonces se crea una nueva versión ligada al identificador del aporte
    Y la nueva versión vuelve a la cola compartida tras validarse sin heredar aprobaciones

  Escenario: Corrección inválida
    Dado existe un aporte con rechazo y retroalimentación
    Y el archivo corregido no cumple una regla de validación
    Cuando el autor presenta la nueva versión
    Entonces se informan los incumplimientos
    Y no se deriva a revisión el archivo inválido

```

## HU-05 : Conocer resolución del aporte
**Historia:** Como autor de un aporte, quiero conocer la resolución de mi envío, para saber si se publicó o por qué fue rechazado.

**Origen:** [HU-05 en Entrega 1](./04-historias-usuario.md#hu-05).

```gherkin
Característica: Comunicación de la resolución

  Escenario: Resolución aprobada
    Dado existe una decisión final aprobatoria de una versión concreta
    Y la versión aprobada fue publicada
    Cuando se registra la resolución final
    Entonces el autor puede conocer la aprobación y el enlace de publicación
    Y el aviso identifica el aporte y la versión

  Escenario: Resolución rechazada
    Dado existe una decisión final de rechazo con fundamento
    Cuando se registra la resolución final
    Entonces el autor puede conocer el rechazo y el feedback registrado por la comunidad
    Y el aviso identifica el aporte y la versión
    Y la versión rechazada permanece sin publicar

  Escenario: Servicio externo de avisos no disponible
    Dado existe una resolución final registrada
    Y el servicio externo de correo no puede aceptar el aviso
    Cuando se intenta comunicar la resolución
    Entonces la decisión final se conserva sin alteración
    Y el envío pendiente o fallido queda identificado para su seguimiento

```

## HU-06 : Buscar apuntes publicados
**Historia:** Como estudiante que busca material, quiero filtrar los apuntes publicados por ramo, período y tema, para encontrar material pertinente.

**Origen:** [HU-06 en Entrega 1](./04-historias-usuario.md#hu-06).

```gherkin
Característica: Búsqueda de material

  Escenario: Coincidencias pertinentes
    Dado existen versiones publicadas clasificadas por carrera, ramo, período y tema
    Cuando el estudiante solicita una búsqueda con filtros
    Entonces el sistema informa solo las versiones publicadas que cumplen los filtros
    Y los resultados permiten distinguir los apuntes

  Escenario: Búsqueda sin coincidencias
    Dado no existen versiones publicadas que cumplan los filtros solicitados
    Cuando el estudiante solicita una búsqueda con filtros
    Entonces el sistema informa que no hay coincidencias
    Y el estudiante puede reformular la búsqueda

```

## HU-07 : Consultar ficha de revisión
**Historia:** Como estudiante que consulta un apunte, quiero ver su procedencia y la revisión de la versión disponible, para valorar su pertinencia y confiabilidad.

**Origen:** [HU-07 en Entrega 1](./04-historias-usuario.md#hu-07).

```gherkin
Característica: Consulta de ficha de apunte

  Escenario: Información de revisión consistente
    Dado existe una versión publicada con revisión académica registrada
    Cuando el estudiante consulta la información del apunte
    Entonces se informa procedencia, período, número de versión, fecha, responsable y alcance de revisión
    Y la información corresponde a la versión ofrecida

  Escenario: Previsualización del archivo publicado
    Dado el estudiante abre una versión publicada y disponible con archivo PDF, PNG o JPG
    Cuando consulta la ficha del apunte
    Entonces puede ver una previsualización de esa versión o descargarla

  Escenario: Archivo de Office
    Dado el estudiante abre una versión publicada con archivo DOCX o PPTX
    Cuando consulta la ficha
    Entonces se ofrece la descarga de esa versión

  Escenario: Ausencia de certificación académica
    Dado existe un archivo que superó controles técnicos sin revisión académica
    Cuando el estudiante consulta la información del material
    Entonces el sistema no lo presenta como versión académicamente aprobada
    Y el control técnico no se afirma como garantía de corrección

```

## HU-08 : Obtener apunte
**Historia:** Como estudiante que consulta material, quiero obtener el archivo que seleccioné, para utilizarlo para estudiar.

**Origen:** [HU-08 en Entrega 1](./04-historias-usuario.md#hu-08).

```gherkin
Característica: Obtención de una versión

  Escenario: Versión publicada y disponible
    Dado existe una versión seleccionada que sigue publicada
    Y su archivo está disponible
    Cuando el estudiante solicita descargar esa versión
    Entonces se entrega el archivo que corresponde exactamente a la versión seleccionada
    Y no se sustituye silenciosamente por otra versión

  Escenario: Versión retirada o ausente
    Dado el estudiante seleccionó una versión no disponible o retirada
    Cuando el estudiante solicita abrir o descargar el archivo
    Entonces se informa la indisponibilidad de la versión
    Y el estudiante puede volver al catálogo

```

## HU-09 : Reportar posible error
**Historia:** Como estudiante que detecta un posible error, quiero reportarlo y conocer su resolución, para ayudar a mantener la calidad del material.

**Origen:** [HU-09 en Entrega 1](./04-historias-usuario.md#hu-09).

```gherkin
Característica: Reporte de errores

  Escenario: Registro de reporte completo
    Dado existe una versión de apunte identificable
    Y el estudiante describe un posible error de esa versión
    Cuando el estudiante presenta el reporte
    Entonces se registra el reporte vinculado a la versión
    Y el reporte queda disponible para revisión de la comunidad estudiantil sin considerar confirmado el error

  Escenario: Reporte incompleto
    Dado el estudiante omite identificar la versión o la descripción del error
    Cuando el estudiante presenta el reporte
    Entonces se informa qué dato imprescindible falta
    Y no se registra un reporte incompleto

  Escenario: Resolución de un reporte investigado
    Dado existe un reporte vinculado a una versión y con investigación concluida
    Y la comunidad estudiantil ha registrado si el error se confirmó o descartó
    Cuando se registra la resolución del reporte
    Entonces el estudiante que lo presentó puede conocer el resultado de la investigación
    Y se informa la acción tomada si el error fue confirmado

```

## HU-10 : Recibir alerta de demora
**Historia:** Como integrante de la comunidad estudiantil, quiero conocer revisiones demoradas, para organizar el trabajo pendiente.

**Origen:** [HU-10 en Entrega 1](./04-historias-usuario.md#hu-10).

```gherkin
Característica: Seguimiento de revisiones

  Escenario: Revisión supera el plazo
    Dado existe una versión pendiente cuyo ingreso a la cola fue hace más de 48 horas
    Cuando vence el plazo de seguimiento configurado
    Entonces se alerta a la comunidad estudiantil
    Y la versión sigue pendiente sin aprobación ni rechazo automáticos

  Escenario: Revisión aún dentro del plazo
    Dado existe una versión pendiente sin plazo excedido
    Cuando se evalúa el plazo de seguimiento
    Entonces no se genera una alerta de demora por ese evento
    Y el estado de revisión se conserva

```

## HU-11 : Corregir o retirar versión con error
**Historia:** Como integrante de la comunidad estudiantil, quiero coordinar la corrección o retirada de una versión con errores confirmados, para evitar distribuir material defectuoso.

**Origen:** [HU-11 en Entrega 1](./04-historias-usuario.md#hu-11).

```gherkin
Característica: Mantenimiento de versiones

  Escenario: Error confirmado corregible
    Dado existe una versión con error confirmado
    Y la comunidad estudiantil dispone de contenido corregido
    Cuando la comunidad gestiona la corrección
    Entonces se crea una versión distinta y se revisa antes de publicarse
    Y la versión afectada mantiene su historial

  Escenario: Error confirmado no corregible
    Dado existe una versión con error confirmado que no puede corregirse
    Cuando la comunidad estudiantil decide su retiro
    Entonces la versión queda retirada y se registra el motivo
    Y se informa la resolución sin seguir ofreciéndola como publicada

  Escenario: Intento de retiro no autorizado
    Dado existe una versión publicada
    Y una persona no pertenece a la comunidad responsable de retirarla
    Cuando la persona intenta retirar la versión
    Entonces el sistema rechaza la operación
    Y la versión conserva su estado

```

## HU-12 : Iniciar sesión con cuenta institucional
**Historia:** Como integrante de la comunidad universitaria, quiero iniciar sesión con mi cuenta institucional, para acceder al sistema con el tipo de cuenta que me corresponde.

**Origen:** [HU-12 en Entrega 1](./04-historias-usuario.md#hu-12).

```gherkin
Característica: Acceso con cuenta institucional

  Escenario: Inicio de sesión con dominio permitido
    Dado un correo @uv.cl o @estudiantes.uv.cl con credenciales válidas
    Cuando la persona inicia sesión
    Entonces se crea la sesión
    Y el sistema identifica si la cuenta es de estudiante o académica

  Escenario: Dominio no permitido
    Dado un correo con un dominio distinto de @uv.cl y @estudiantes.uv.cl
    Cuando la persona intenta iniciar sesión
    Entonces se rechaza el acceso
    Y no se crea la sesión

  Escenario: Acceso sin sesión
    Dado que no hay una sesión iniciada
    Cuando la persona intenta enviar un aporte
    Entonces el sistema rechaza la operación
    Y solicita iniciar sesión

```

## Verificación pendiente de requisitos de calidad asociados

Los siguientes umbrales proceden de `03-requisitos.md` de la Entrega 1. Son **pruebas propuestas**, no resultados obtenidos ni evidencia de implementación. Los escenarios Gherkin anteriores cubren el comportamiento del negocio; estos criterios numéricos se verificarían por separado.

| Requisito | Historias vinculadas | Verificación exigida |
|---|---|---|
| RP-15 | HU-06 | Obtener exactamente los identificadores esperados en el **100 % de 30 consultas** sobre catálogo controlado, incluyendo filtros combinados, ausencia de resultados y exclusión de no publicados. |
| RP-16 | HU-01, HU-06, HU-08 | Con **10 estudiantes nuevos**, completar al menos **16 de 20 tareas** (enviar un aporte completo y obtener un apunte) sin ayuda en **120 segundos o menos por tarea**. |
| RP-17 | HU-06 | Con **1.000 apuntes**, **10 personas buscando simultáneamente** y al menos **200 búsquedas**, entregar resultados en **2 segundos o menos en al menos el 95 %**; documentar equipo y configuración, sin incluir descarga. |
| RP-18 | HU-03, HU-11 | Impedir el **100 % de 20 intentos no autorizados** de aprobar, rechazar, publicar o retirar material, conservando intacto el estado. |

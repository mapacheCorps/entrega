# Diagramas de estado

Los estados representan condiciones de las entidades del dominio. Los eventos indican cuándo una versión o notificación cambia de estado.

## EST-01: Ciclo de vida de VersionApunte

- Clase: [`VersionApunte`](./08-modelo-dominio.md)
- Secuencias relacionadas: [`DSS-01`, `DSS-02`](./10-diagramas-secuencia.md)

![EST-01: estados de una versión](./diagramas/est-01.png)

Fuente editable: [`est-01.puml`](./diagramas/est-01.puml)

### Tabla de transiciones

| Estado origen | Evento | Guarda | Acción | Estado destino |
|---|---|---|---|---|
| Inicio | registrarVersion | No aplica | Registrar versión | Recibida |
| Recibida | validarAporte | Archivo y clasificación válidos | Ingresar en la cola compartida | PendienteRevision |
| Recibida | validarAporte | Archivo o clasificación inválidos | Informar observaciones | RequiereCorreccion |
| PendienteRevision | registrarDecision | La versión vigente sigue pendiente y el Moderador envía una decisión válida | Iniciar la resolución en la misma transacción | EnRevision |
| PendienteRevision | solicitarRevisionExperto | La versión corresponde a una materia especializada | Derivar a Experto | EnRevisionExperto |
| EnRevision | registrarDecision | Comunidad aprueba | Registrar evaluación | Aprobada |
| EnRevision | registrarDecision | Comunidad rechaza | Guardar feedback obligatorio | Rechazada |
| EnRevision | registrarDecision | Comunidad solicita corrección | Guardar observaciones | RequiereCorreccion |
| EnRevisionExperto | evaluacionExperto | Experto aprueba | Registrar evaluación del Experto | Aprobada |
| EnRevisionExperto | evaluacionExperto | Experto rechaza | Guardar feedback obligatorio del Experto | Rechazada |
| EnRevisionExperto | evaluacionExperto | Experto solicita corrección | Guardar observaciones del Experto | RequiereCorreccion |
| Aprobada | publicarVersion | No aplica | Publicar la versión aprobada | Publicada |
| Publicada | confirmarReporteDeError | Reporte confirmado | Conservar antecedente | BajoInvestigacion |
| BajoInvestigacion | retirarVersion | Error no corregible | Dejar de publicar | Retirada |
| BajoInvestigacion | publicarVersionCorregida | Nueva versión aprobada | Reemplazar versión pública | Sustituida |
| RequiereCorreccion | reemplazarPorNuevaVersion | No aplica | Mantener trazabilidad | Final |
| Rechazada | cerrarVersionConFeedback | No aplica | Conservar rechazo y feedback | Final |
| Retirada | cerrarVersion | No aplica | Conservar historial | Final |
| Sustituida | cerrarVersion | No aplica | Conservar historial | Final |

Una versión rechazada no cambia a publicada. El estudiante puede crear otra versión corregida del mismo aporte, que vuelve a quedar pendiente de revisión. Para materias especializadas, la versión puede derivarse a un Experto desde PendienteRevision.

En la demo, la aprobación y la publicación se confirman en una misma transacción. El estado persistido al finalizar es `Publicada`. La guarda de derivación exige un Moderador y una versión vigente pendiente. Una segunda decisión se rechaza.

## EST-02: Ciclo de vida de Notificacion

- Clase: [`Notificacion`](./08-modelo-dominio.md)
- Secuencia relacionada: [`DSS-02`](./10-diagramas-secuencia.md)

![EST-02: estados de una notificación](./diagramas/est-02.png)

Fuente editable: [`est-02.puml`](./diagramas/est-02.puml)

### Tabla de transiciones

| Estado origen | Evento | Guarda | Acción | Estado destino |
|---|---|---|---|---|
| Inicio | registrarResultado | No aplica | Guardar aviso | Pendiente |
| Pendiente | solicitarEntrega | No aplica | Pedir entrega al correo externo | EnEnvio |
| EnEnvio | confirmarAceptacionServicio | El correo acepta el aviso | Guardar respuesta del servicio | AceptadaPorServicio |
| EnEnvio | informarFalloEntrega | El correo no acepta el aviso | Registrar el fallo | Fallida |
| Fallida | reintentar | Hay reintentos disponibles | Solicitar otro intento | EnEnvio |
| Fallida | cerrarIntentos | No hay reintentos disponibles | Registrar problema | Agotada |
| AceptadaPorServicio | archivarConstancia | No aplica | Guardar constancia | Final |
| Agotada | registrarIncidencia | No aplica | Conservar incidencia | Final |

La aceptación por el servicio externo no demuestra que el autor haya leído el mensaje. La decisión de la comunidad permanece guardada aunque falle el correo.

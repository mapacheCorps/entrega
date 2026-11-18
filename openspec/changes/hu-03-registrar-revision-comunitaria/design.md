# Diseño de la revisión comunitaria

## Contexto

HU-02 deja el aporte en `Asignado` y la versión validada en `PendienteRevision`. La asignación vigente ya identifica al estudiante responsable y a su comunidad. DSS-02 describe la decisión y sus resultados. El inicio de revisión se deriva de EST-01 y la solicitud de corrección de RP-04 y de la ficha aprobada.

## Objetivos y alcance técnico

- Reutilizar el panel de Moderador, el selector de perfiles y la base SQLite existentes.
- Vincular la evidencia de revisión, el cambio de estados y la publicación a una versión exacta.
- Permitir consultar el archivo resguardado desde moderación. La lectura pública del archivo y el tramo de notificación de DSS-02 se implementarán en otras historias.

## Decisiones

### Persistencia y estados

La migración `003_revision_comunitaria.sql` usa el ejecutor transaccional de HU-02. Crea `revisiones_academicas` con identificador, fecha, decisión, alcance, observaciones y referencias obligatorias a versión, revisor y comunidad. Una restricción de unicidad de la decisión inicial por versión evita registrar dos resoluciones de HU-03. Cuando una historia futura requiera revisiones de otro tipo, deberá conservar esa garantía para la decisión inicial.

Se amplían las restricciones de estados de `versiones_apunte` y `aportes`, conservando los identificadores, índices, restricciones de archivos y referencias existentes. La asignación reutiliza `Asignada` y `Finalizada` de HU-02.

| Operación | Estado de la versión resultante | Estado del aporte resultante | Estado de la asignación |
|---|---|---|---|
| Iniciar revisión | `PendienteRevision` → `EnRevision` | `Asignado` | `Asignada` |
| Aprobar | `EnRevision` → `Aprobada` → `Publicada` | `Publicado` | `Finalizada` |
| Rechazar | `EnRevision` → `Rechazada` | `Rechazado` | `Finalizada` |
| Solicitar corrección | `EnRevision` → `RequiereCorreccion` | `CorreccionSolicitada` | `Finalizada` |

El estado `CorreccionSolicitada` del aporte evita que un resultado académico habilite el formulario de corrección de archivo inválido de HU-01. Se ajustan los textos de estado existentes para mostrar el resultado real del aporte, preservando los recorridos de HU-01 y HU-02.

### Transacciones y autorización

En cada operación de moderación, el servidor comprueba el perfil activo y la comunidad organizadora. Para iniciar o resolver, abre una transacción de escritura y vuelve a consultar la asignación vigente, la versión actual y su estado. La versión indicada por la solicitud debe coincidir con la que se está evaluando. El revisor y la comunidad provienen de la asignación. El formulario envía la decisión, el alcance y las observaciones.

La decisión académica se persiste antes de ejecutar la transición resultante. Cuando la decisión aprueba, el paso por `Aprobada` y la publicación ocurren en la misma transacción que guarda la revisión, cambia el aporte y finaliza la asignación. Así no queda una aprobación confirmada a medias. Para una decisión repetida o una solicitud sobre una versión anterior, el servidor informa el conflicto y conserva el resultado previo.

### Vistas y rutas propuestas

| Interacción | Ruta | Comportamiento |
|---|---|---|
| Seleccionar aporte asignado | `GET /moderacion/aportes` | Extiende el panel con las revisiones asignadas a la comunidad y en curso. |
| Consultar revisión concreta | `GET /moderacion/aportes/{aporte_id}/versiones/{version_id}/revision` | Muestra la versión, el estudiante designado y las acciones permitidas. |
| Leer el archivo para evaluar | `GET /moderacion/aportes/{aporte_id}/versiones/{version_id}/archivo` | Comprueba el perfil, la comunidad, la asignación y la versión antes de entregar el archivo desde el adaptador local. |
| Iniciar revisión | `POST /moderacion/aportes/{aporte_id}/versiones/{version_id}/revision/iniciar` | Aplica la transición de EST-01. |
| Registrar decisión | `POST /moderacion/aportes/{aporte_id}/versiones/{version_id}/revision/decision` | Procesa el formulario y muestra la confirmación o los errores. |
| Consultar material publicado | `GET /catalogo` | Lista las versiones publicadas con aprobación propia. |

El catálogo muestra el nombre del archivo, su número de versión y su clasificación académica. La consulta usa el identificador de la versión aprobada, sin inferir que otra versión del mismo aporte comparte su aprobación. No incorpora filtros, ficha pública detallada ni un enlace de descarga pública.

### Almacenamiento de demostración

El adaptador local incorpora una operación de lectura que usa la referencia persistida para la versión autorizada. La ruta evita exponer ubicaciones del disco y devuelve el archivo como adjunto para que el revisor pueda abrirlo. Si falta el archivo, informa que no está disponible y la consulta no cambia estados. El correo externo queda para HU-05.

## Riesgos y migración

- La reconstrucción de las tablas con nuevos estados debe conservar las asignaciones de HU-02, el historial de versiones, sus índices, referencias y los identificadores. El ejecutor existente permite verificar las claves foráneas antes de confirmar.
- Las dos solicitudes de decisión sobre la misma versión se serializan al escribir. La guarda de estado y la restricción de unicidad impiden que una solicitud tardía cambie el resultado.
- Para probar el proceso se reutilizan la comunidad y los revisores de ejemplo de HU-02, creando los aportes desde HU-01 y asignándolos desde HU-02. No se necesitan nuevas identidades de demostración.

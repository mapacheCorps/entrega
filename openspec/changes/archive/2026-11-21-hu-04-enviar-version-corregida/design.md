# Diseño del reenvío de una versión corregida

## Contexto

HU-03 registra las observaciones por versión y deja el aporte en `Rechazado` o `CorreccionSolicitada`. HU-01 ya valida, detecta duplicados, resguarda archivos y registra versiones corregidas. HU-02 recibe aportes en `PendienteAsignacion` cuya última versión está en `PendienteRevision`.

## Objetivos y alcance técnico

- Reutilizar las tablas de aportes, versiones y revisiones. El cambio se puede aplicar sobre los datos existentes de HU-03 sin migración ni seed nuevo.
- Vincular el feedback al número de versión que le corresponde y conservar los archivos y decisiones previos al reenvío.
- Usar el almacenamiento local de HU-01 para el nuevo archivo. Los avisos de resolución se desarrollan en HU-05.

## Decisiones

### Lectura y acceso

El detalle del aporte consulta las decisiones de rechazo o corrección junto con los números de las versiones que las recibieron. Esta consulta se usa solo si el perfil activo es Estudiante y su identificador coincide con `aportes.autor_id`. El enlace al reenvío se muestra bajo la misma condición y cuando la versión vigente tiene la decisión académica que corresponde al estado del aporte.

Las rutas de reenvío verifican el rol y la identidad del autor en el servidor, incluso si se invocan directamente. Comprueban que la versión indicada pertenezca al aporte, sea la vigente y tenga una revisión coherente con el estado: rechazo con `Rechazada` o solicitud académica con `RequiereCorreccion`. Se devuelve un mensaje de conflicto si el formulario apunta a una versión anterior o el aporte ya cambió de estado.

### Validación y escritura

Usar las mismas funciones de archivo, huella SHA-256 y consulta de duplicados de HU-01. La operación valida el archivo y conserva el contexto del formulario ante errores para que se puedan leer las observaciones y reintentar.

Para un reenvío válido, adquirir el bloqueo de escritura de SQLite antes de volver a comprobar la versión vigente, la autorización y la unicidad de la huella. Reservar un solo identificador de versión y usarlo para el resguardo y el registro. Reutilizar la escritura de una versión corregida de HU-01 de modo que el servicio controle la transacción completa sin un commit intermedio. Mantener el comportamiento actual de HU-01 cuando su propio formulario recibe un archivo inválido.

Guardar la nueva versión como `Recibida`, aplicar la transición a `PendienteRevision`, cerrar la anterior como `Final` y dejar el aporte en `PendienteAsignacion` en la misma transacción. Conservar la clasificación, la procedencia, la asignación finalizada y la revisión previa. Las consultas de HU-02 ya incorporan el aporte reingresado, que podrá recibir una nueva asignación.

Si una escritura falla, revertir el registro y eliminar el archivo nuevo si ya fue resguardado. El adaptador debe evitar dejar escrituras parciales en la ubicación definitiva cuando el guardado falla. No se elimina ni se sobrescribe el archivo de una versión anterior.

### Pantallas y rutas propuestas

| Interacción reconstruida de CU-04 | Ruta |
|---|---|
| Consultar la versión actual y sus antecedentes | `GET /aportes/{aporte_id}` |
| Abrir el formulario de reenvío académico | `GET /aportes/{aporte_id}/versiones/{version_id}/reenviar` |
| Enviar el archivo corregido | `POST /aportes/{aporte_id}/versiones/{version_id}/reenviar` |

El formulario muestra el archivo anterior, las observaciones, el número previsto de la nueva versión y las reglas de archivo. Tras el éxito, el autor vuelve al detalle, donde ve el número y el estado de la nueva versión y conserva acceso al feedback de la anterior.

## Riesgos y verificación

- Una solicitud atrasada o concurrente podría intentar cerrar la misma versión dos veces. El identificador de versión en la ruta y la revalidación dentro de la transacción solo permiten confirmar un reenvío para esa versión.
- La base de datos y el almacenamiento local son recursos distintos. Una prueba debe simular un fallo de registro después de resguardar el archivo y verificar el retroceso y la limpieza.
- Los estados `RequiereCorreccion` de HU-01 y de la versión para HU-04 tienen orígenes distintos. La guarda del estado del aporte y de la decisión asociada asegura que el intento siga las reglas del formulario correcto.

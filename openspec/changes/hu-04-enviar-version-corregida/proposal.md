# HU-04 Enviar una versión corregida

## Por qué

HU-03 conserva el rechazo o la solicitud de corrección de una versión. HU-04 permite al autor consultar las observaciones y devolver el mismo aporte al flujo de revisión con un archivo corregido. El cambio se deriva de CU-04, RP-05 y RP-14, y cubre P07, P08, P13 y P14 del TO-BE dentro de C04.

## Qué cambia

- El autor consulta en el detalle las decisiones de rechazo o solicitud de corrección y las observaciones asociadas a cada versión.
- Tras cualquiera de esos dos resultados, el autor puede presentar otro archivo. Se conservan el identificador del aporte, la clasificación y la procedencia.
- Si la validación y el resguardo tienen éxito, se registra la siguiente versión, se cierra la anterior y el aporte vuelve a asignación. La revisión anterior permanece asociada a la versión que la recibió.
- Si falta el archivo, es inválido o idéntico a uno registrado, o falla el resguardo, se informa la causa y el autor puede reintentar con la misma versión vigente.

La edición de datos académicos, los avisos de HU-05 y la publicación automática quedan fuera del alcance.

## Capacidades

### Capacidades nuevas

### Capacidades modificadas

- `gestion-aportes` incorpora el reenvío tras una decisión académica y la consulta del feedback por el autor. La corrección de archivos inválidos de HU-01 mantiene su propio recorrido.

## Impacto

Se amplían el detalle del aporte y los servicios de reenvío con las entidades y tablas existentes. Se reutilizan la validación de archivos de HU-01, el almacenamiento local y la cola de asignación de HU-02. No se requieren migraciones.

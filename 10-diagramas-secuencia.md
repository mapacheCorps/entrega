# Diagramas de secuencia de sistema

En ambos diagramas, **Torpedos universitarios** aparece como una única caja negra. Las actividades internas de frontend, backend y base de datos no forman parte de estos diagramas. Los servicios de archivos y correo son integraciones propuestas para la especificación.

## DSS-01: Presentar un aporte y decidir su publicación

- Caso de uso: [CU-01](./09-casos-de-uso.md) y [CU-12](./09-casos-de-uso.md)
- Historia: [HU-01](./04-historias-usuario.md#hu-01) y [HU-12](./04-historias-usuario.md#hu-12)
- Requisitos: [RP-01, RP-02, RP-19, RP-20](./03-requisitos.md)
- Integración: servicio externo de almacenamiento de archivos (propuesto).

![DSS-01: Presentar aporte](./diagramas/dss-01.png)

Fuente editable: [`dss-01.puml`](./diagramas/dss-01.puml)

**Escenario principal:** el usuario institucional inicia sesión con una cuenta válida y presenta un apunte válido; el servicio externo confirma el resguardo. Con cuenta `@uv.cl` la versión se publica; con cuenta `@estudiantes.uv.cl` queda pendiente de revisión comunitaria.

**Opciones de clasificación:** el selector de ramo ofrece solo los ramos de la carrera seleccionada y el de tema solo los temas del ramo seleccionado; el período académico se elige con independencia del ramo. La validación del servidor rechaza combinaciones incoherentes.

**Confirmación al autor:** la respuesta exitosa muestra los identificadores del aporte y de la versión, la clasificación, el estado y la aclaración de que no se publica cuando la cuenta es `@estudiantes.uv.cl`, o de que la versión quedó publicada cuando es `@uv.cl`; no expone hash SHA-256, referencia de almacenamiento, tipo MIME ni fecha de creación de la versión.

**Variantes `alt`:** dominio no permitido, datos de aporte inválidos, imposibilidad de resguardar el archivo y ruta de publicación según el tipo de cuenta. En todos los casos se informa el motivo o el resultado al autor.

## DSS-02: Registrar la decisión y comunicar el feedback

- Caso de uso principal: [CU-05](./09-casos-de-uso.md)
- Caso relacionado: [CU-03](./09-casos-de-uso.md)
- Historia principal: [HU-05](./04-historias-usuario.md#hu-05)
- Historia relacionada: [HU-03](./04-historias-usuario.md#hu-03)
- Requisitos: [RP-04, RP-06, RP-07](./03-requisitos.md)
- Integración: servicio externo de correo (propuesto).

![DSS-02: Resolución comunitaria](./diagramas/dss-02.png)

Fuente editable: [`dss-02.puml`](./diagramas/dss-02.puml)

**Escenario principal:** la comunidad estudiantil registra su decisión. Una aprobación habilita la publicación de esa versión; un rechazo impide la publicación y debe ir acompañado de retroalimentación que el autor pueda consultar.

**Variantes `alt`:** aprobación o rechazo fundamentado; servicio de correo acepta el aviso o registra un fallo. La falla del correo no modifica la decisión guardada.

## Consistencia del proceso

`Usuario institucional inicia sesión` -> `Presenta apunte` -> `Si es @uv.cl: publica tras validar` **o** `Si es @estudiantes.uv.cl: pendiente de revisión` -> `Comunidad estudiantil revisa` -> `Aprobación y publicación` **o** `Rechazo con feedback` -> `Nueva versión corregida y nueva revisión, si el autor decide reenviar`.

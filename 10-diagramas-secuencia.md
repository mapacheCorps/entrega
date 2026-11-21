# Diagramas de secuencia de sistema

En ambos diagramas, **Torpedos universitarios** aparece como una única caja negra. Las actividades internas de frontend, backend y base de datos no forman parte de estos diagramas. Los servicios de archivos y correo son integraciones propuestas para la especificación.

## DSS-01: Presentar un aporte

- Caso de uso: [CU-01](./09-casos-de-uso.md)
- Historia: [HU-01](./04-historias-usuario.md#hu-01)
- Requisitos: [RP-01, RP-02, RP-20](./03-requisitos.md)
- Integración: servicio externo de almacenamiento de archivos (propuesto).

![DSS-01: Presentar aporte](./diagramas/dss-01.png)

Fuente editable: [`dss-01.puml`](./diagramas/dss-01.puml)

**Escenario principal:** el autor presenta un apunte válido. El almacenamiento confirma el resguardo y la versión queda en la cola de revisión comunitaria.

**Opciones de clasificación:** el selector de ramo ofrece solo los ramos de la carrera seleccionada y el de tema solo los temas del ramo seleccionado; el período académico se elige con independencia del ramo. La validación del servidor rechaza combinaciones incoherentes.

**Confirmación al autor:** la respuesta exitosa muestra los identificadores del aporte y de la versión, la clasificación, el estado y la aclaración de que aún no se publica; no expone hash SHA-256, referencia de almacenamiento, tipo MIME ni fecha de creación de la versión.

**Variantes `alt`:** datos o archivo inválidos y fallo de almacenamiento. El sistema informa el motivo y no remite la versión a revisión.

## DSS-02: Registrar la decisión y comunicar el feedback

- Caso de uso principal: [CU-05](./09-casos-de-uso.md)
- Caso relacionado: [CU-03](./09-casos-de-uso.md)
- Historia principal: [HU-05](./04-historias-usuario.md#hu-05)
- Historia relacionada: [HU-03](./04-historias-usuario.md#hu-03)
- Requisitos: [RP-04, RP-06, RP-07](./03-requisitos.md)
- Integración: servicio externo de correo (propuesto).

![DSS-02: Resolución comunitaria](./diagramas/dss-02.png)

Fuente editable: [`dss-02.puml`](./diagramas/dss-02.puml)

**Escenario principal:** cualquier Moderador abre una versión pendiente, revisa el archivo y registra la decisión. Se guarda su identidad y solo se confirma la primera decisión válida. Una aprobación habilita la publicación de esa versión; un rechazo impide la publicación y debe ir acompañado de retroalimentación que el autor pueda consultar.

**Variantes `alt`:** aprobación o rechazo fundamentado; servicio de correo acepta el aviso o registra un fallo. La falla del correo no modifica la decisión guardada.

## Consistencia del proceso

El autor presenta el apunte, el sistema lo valida, la comunidad revisa la versión y solo una aprobación permite publicarla.

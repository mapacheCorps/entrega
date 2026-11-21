# Tareas de HU-03

## 1. Persistencia y estados

 - [x] 1.1 Crear la migración numerada para `RevisionAcademica` y ampliar los estados de `Aporte` y `VersionApunte`. Probar la migración en una base nueva y desde HU-02, preservando versiones, asignaciones, índices y claves foráneas.
 - [x] 1.2 Incorporar los estados y las consultas de revisión por versión y comunidad. Verificar que se reconoce la última versión de un aporte, solo se ofrecen asignaciones vigentes de la comunidad y se mantiene íntegra la identidad del revisor.

## 2. Inicio, decisión y lectura del archivo

 - [x] 2.1 Implementar las guardas y transiciones de EST-01 para iniciar y decidir. Cubrir las tres decisiones, el vínculo con la versión, el cierre de la asignación, la falta de datos y el rechazo de estados inválidos o versiones anteriores.
 - [x] 2.2 Verificar con pruebas que una decisión repetida o concurrente conserva un solo resultado y que un fallo al guardar revierte la revisión, el cambio de estados y el cierre de la asignación.
 - [x] 2.3 Incorporar lectura al adaptador de almacenamiento local. Probar la lectura de un archivo resguardado y el tratamiento de referencias inválidas o archivos ausentes.

## 3. Panel de moderación y catálogo

 - [x] 3.1 Extender el panel con aportes asignados y en revisión, y agregar el detalle de versión con acceso al archivo y acciones de inicio y decisión. Verificar con TestClient la identidad visible del responsable, las guardas de perfil y comunidad, los mensajes de validación y las confirmaciones.
 - [x] 3.2 Crear el catálogo básico y enlazarlo desde el inicio. Ajustar los mensajes de estado existentes. Probar que solo aparecen versiones publicadas con aprobación propia y que la corrección académica no activa el formulario de archivo inválido de HU-01.
 - [x] 3.3 Ejecutar una prueba HTTP por cada escenario Gherkin original: «Aprobación de versión revisada», «Rechazo o solicitud de corrección» e «Intento no autorizado». Añadir una prueba independiente para la solicitud de corrección de RP-04.

## 4. Verificación integrada y guía

 - [x] 4.1 Reutilizar el seed de HU-02 y comprobar el recorrido envío → asignación → inicio → decisión → catálogo, con las ramas de aprobación, rechazo, corrección y acceso denegado. Ejecutar `python -m pytest` con las regresiones de HU-01 y HU-02.
 - [x] 4.2 Actualizar `README.md` con instalación, seed, arranque y pasos reproducibles para verificar los tres escenarios Gherkin y la solicitud de corrección.

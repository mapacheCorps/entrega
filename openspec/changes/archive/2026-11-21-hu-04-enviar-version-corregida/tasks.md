# Tareas de HU-04

## 1. Feedback y elegibilidad

 - [x] 1.1 Consultar las decisiones de rechazo y corrección por versión y validar que el estudiante de demostración sea el autor. Probar el historial por número de versión y la exclusión de observaciones al consultar como otro estudiante o Moderador.
 - [x] 1.2 Comprobar que la versión vigente pertenezca al aporte y tenga la decisión académica que corresponde a su estado. Probar rechazo, solicitud de corrección, una versión anterior y un aporte fuera de ambos estados.

## 2. Validación y registro

 - [x] 2.1 Implementar el reenvío académico reutilizando la validación de archivo y duplicados de HU-01. Probar que los archivos ausentes, inválidos o duplicados conservan intacto el historial y que se informa la causa.
 - [x] 2.2 Reutilizar la escritura de versiones corregidas dentro de una transacción que confirme la nueva versión, el cierre de la anterior y el retorno a asignación. Probar que conserva metadatos, archivos, revisión y asignación previa y que dos reenvíos concurrentes crean como máximo una versión.
 - [x] 2.3 Verificar que una falla de almacenamiento o del registro deja la versión anterior vigente y permite reintentar. Simular ambos fallos y comprobar que no queda un archivo nuevo o parcial confirmado.

## 3. Recorrido del autor

 - [x] 3.1 Mostrar el feedback por versión y el enlace de reenvío en el detalle. Agregar las rutas del formulario académico y verificar que una solicitud directa de alguien distinto al autor no expone observaciones ni modifica el historial.
 - [x] 3.2 Agregar una prueba HTTP por escenario Gherkin. Verificar que «Nueva versión del mismo aporte» muestra el nuevo número y que «Corrección inválida» muestra el motivo sin registrar o remitir el archivo.

## 4. Verificación integrada

 - [x] 4.1 Con los perfiles y datos de HU-02, verificar los recorridos rechazo → reenvío y solicitud de corrección → reenvío. Comprobar que la nueva versión entra en la cola, admite una nueva asignación y no hereda la decisión anterior. Ejecutar `python -m pytest` con las regresiones de HU-01 a HU-03.
 - [x] 4.2 Actualizar `README.md` con instalación, seed, arranque y pasos reproducibles para los escenarios válido e inválido, incluyendo cómo encontrar el feedback.

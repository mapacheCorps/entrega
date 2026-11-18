# Tareas de HU-02

## 1. Persistencia y datos de demostración

 - [x] 1.1 Crear la migración numerada de comunidad, disponibilidad, habilitaciones, asignaciones y estado `Asignado`. Ajustar el ejecutor para aplicar la reconstrucción y registrar la migración atómicamente. Probar la ejecución única en una base nueva y la actualización de una base HU-01 con aportes y versiones existentes, incluyendo la comprobación de claves foráneas.
 - [x] 1.2 Extender el seed con la comunidad, su vínculo con el perfil Moderador, revisores y habilitaciones. Verificar que sembrar dos veces preserva los dos perfiles y deja datos estables, con al menos un ramo asignable y otro sin revisor.

## 2. Selección y registro de la asignación

 - [x] 2.1 Incorporar los estados de HU-02 y las consultas para la lista de aportes elegibles, su última versión, la asignación vigente y el revisor por carga activa. Probar que se excluyen el autor, los estudiantes de otra comunidad, los no habilitados y los no disponibles, y que el desempate usa el identificador.
 - [x] 2.2 Implementar la operación transaccional de P05. Probar el retroceso ante un fallo entre el registro y el cambio de estado, y verificar que dos solicitudes sobre el mismo aporte conservan una única asignación vigente.

## 3. Panel del Moderador y escenarios de aceptación

 - [x] 3.1 Agregar el enlace, el panel y las rutas de CU-02 con las guardas del perfil Moderador. Verificar con TestClient la clasificación visible, el rechazo de accesos desde Estudiante y el tratamiento de aportes inexistentes, inválidos o con asignación vigente.
 - [x] 3.2 Agregar una prueba de integración por escenario Gherkin de HU-02. Verificar que «Estudiante de la comunidad disponible» conserva el responsable, la comunidad y el estado de la versión, y que «Sin estudiantes revisores disponibles» deja el aporte visible, pendiente y sin asignación ni publicación.

## 4. Verificación integrada

 - [x] 4.1 Ejecutar `pytest` completo y verificar los recorridos de HU-01 y los dos resultados de HU-02 con los perfiles de demostración.
 - [x] 4.2 Actualizar `README.md` con los pasos de instalación, seed, arranque y pruebas, y comprobar que sus instrucciones permiten recorrer ambos escenarios de HU-02.

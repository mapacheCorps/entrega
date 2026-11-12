# Tasks — HU-01 Enviar y clasificar un aporte

## 1. Estructura del proyecto y dependencias

- [x] 1.1 Crear la estructura base (`app/`, `app/db/migrations/`, `app/dominio/`, `app/servicios/`, `app/integraciones/`, `app/rutas/`, `app/templates/`, `tests/`) y verificar que existan los archivos `__init__.py` correspondientes.
- [x] 1.2 Crear `requirements.txt` con FastAPI, Uvicorn, Jinja2, python-multipart, pytest y httpx; instalar en el entorno virtual y verificar que `pip install -r requirements.txt` termine sin errores.
- [x] 1.3 Crear `pytest.ini` o `pyproject.toml` con la configuración de pytest y una prueba mínima de arranque de la aplicación; verificar que `pytest` recoja y pase esa prueba.
- [x] 1.4 Crear `.gitignore` para `.venv/`, `__pycache__/`, `data/app.db`, `data/archivos/` y `.pytest_cache/`, y verificar que `git status` no muestre archivos generados.

## 2. Base de datos, migraciones y datos de ejemplo

- [x] 2.1 Crear `app/db/conexion.py` con la conexión SQLite por solicitud, `PRAGMA foreign_keys = ON` y el registro de migraciones en `schema_migrations`; verificar con una prueba que una base temporal se crea y que la migración queda registrada una sola vez.
- [x] 2.2 Crear `app/db/migrations/001_inicial.sql` con las tablas `estudiantes`, `carreras`, `ramos`, `periodos_academicos`, `temas_unidad`, `aportes` y `versiones_apunte`, sus claves foráneas, restricciones `CHECK` de estados, unicidad `(aporte_id, numero)` e índice único parcial de `hash_archivo`; verificar aplicando la migración sobre una base temporal y consultando `schema_migrations`.
- [x] 2.3 Crear `app/db/seed.py` idempotente con carreras, ramos, períodos, temas y los dos perfiles de demostración (Estudiante y Moderador, que representa a la Comunidad Estudiantil); verificar ejecutándolo dos veces y comprobando que no duplica filas.
- [x] 2.4 Agregar una prueba de las restricciones de la base que confirme el rechazo de un `aporte` sin ramo o período, de una versión con número repetido y de dos versiones con el mismo `hash_archivo` no nulo; verificar que `pytest` la apruebe.

## 3. Dominio y repositorios

- [x] 3.1 Crear en `app/dominio/` las entidades y enumeraciones de `Aporte` y `VersionApunte`, con los estados `PendienteAsignacion`/`RequiereCorreccion` y `Recibida`/`PendienteRevision`/`RequiereCorreccion`/`Final`; verificar con pruebas unitarias de creación y comparación de estados.
- [x] 3.2 Crear los repositorios SQLite de aportes, versiones y catálogos (carreras, ramos, períodos, temas) con operaciones de lectura por identificador, listado de catálogos y búsqueda de versión por hash; verificar con pruebas sobre una base temporal sembrada.
- [x] 3.3 Implementar la creación transaccional de `Aporte` más primera `VersionApunte` y la de versión corregida más cierre de la anterior; verificar con pruebas que un fallo intermedio no deja filas parciales.

## 4. Validación y servicio de aportes

- [x] 4.1 Implementar la validación de campos obligatorios (procedencia, carrera, ramo, período, tema y archivo) y la coherencia ramo–carrera y tema–ramo; verificar con pruebas unitarias de cada campo faltante y de cada combinación incoherente.
- [x] 4.2 Implementar la validación del archivo (no vacío, extensiones `.pdf`, `.docx`, `.pptx`, `.png`, `.jpg` y máximo 10 MB); verificar con pruebas unitarias de archivo vacío, extensión no permitida, archivo de 10 MB y archivo de más de 10 MB.
- [x] 4.3 Implementar el cálculo de SHA-256 y la detección de duplicado exacto antes de registrar; verificar con una prueba que dos archivos idénticos producen el mismo hash y que el segundo envío no crea filas.
- [x] 4.4 Implementar el flujo de registro válido: validar, detectar duplicado, resguardar y crear `Aporte` en `PendienteAsignacion` con `VersionApunte` número 1 en `PendienteRevision`; verificar con la prueba del escenario Gherkin «Registro de aporte completo».
- [x] 4.5 Implementar la rama de datos faltantes sin escritura en la base y la rama B1 de archivo inválido con datos completos (`RequiereCorreccion`, `referencia_archivo` y `hash_archivo` nulos); verificar con las pruebas de los escenarios «Datos obligatorios faltantes no crean el aporte» y «Archivo inválido con datos completos queda en RequiereCorreccion».
- [x] 4.6 Implementar la corrección de un archivo inválido: nueva versión, versión anterior en `Final` y actualización del aporte a `PendienteAsignacion` si la nueva versión es válida; verificar con la prueba del escenario «La corrección de un archivo inválido crea una nueva versión».
- [x] 4.7 Implementar los errores de duplicado exacto y de fallo del almacenamiento sin confirmar el registro, con posibilidad de reintento; verificar con las pruebas de los escenarios «Archivo duplicado exacto» y «Fallo del servicio de almacenamiento».

## 5. Almacenamiento simulado

- [x] 5.1 Crear `app/integraciones/almacenamiento.py` con la interfaz `AlmacenamientoArchivos` y el adaptador `AlmacenamientoLocal` que guarda en `data/archivos/{aporte_id}/{version_id}_{nombre_seguro}`, sanea el nombre y devuelve la ruta relativa; verificar con pruebas de guardado, saneamiento y eliminación.
- [x] 5.2 Agregar la compensación para eliminar el archivo guardado si la inserción en la base falla después del resguardo; verificar con una prueba que fuerza el fallo de inserción y comprueba que no queda archivo ni fila.

## 6. Rutas, plantillas y selector de rol

- [x] 6.1 Crear `app/main.py` con el arranque, las migraciones, el montaje de estáticos y el registro de rutas; verificar que la aplicación responde `200` en `/` con una base temporal.
- [x] 6.2 Implementar el selector de rol de demostración con cookie `demo_role` y los dos perfiles (Estudiante y Moderador); verificar con pruebas que el rol activo se muestra y que solo Estudiante habilita la creación de aportes.
- [x] 6.3 Implementar `GET /aportes/nuevo` con el formulario y los catálogos cargados desde la base; verificar con una prueba que la página lista carreras, ramos, períodos y temas sembrados.
- [x] 6.4 Implementar `POST /aportes` conectado al servicio, con re-render del formulario y errores por campo cuando la validación falla; verificar con pruebas de envío válido, datos faltantes y archivo inválido.
- [x] 6.5 Implementar `GET /aportes/{id}` como confirmación con identificadores, estados y la aclaración de que el aporte no se publica; verificar con una prueba que la página muestra los datos del aporte registrado.
- [x] 6.6 Implementar `GET /aportes/{id}/corregir` y `POST /aportes/{id}/correcciones` para subir el archivo corregido y mostrar el resultado; verificar con la prueba de corrección de extremo a extremo.
- [x] 6.7 Crear las plantillas Jinja2 del layout, inicio, formulario, confirmación y corrección, en español y con etiquetas accesibles; verificar manualmente que las cinco páginas se renderizan sin errores de plantilla.
- [x] 6.8 Implementar la selección en cascada del formulario: ramo según carrera y tema según ramo, con el período académico independiente; verificar que las opciones incoherentes se oculten y que el servidor siga rechazando combinaciones manipuladas.
- [x] 6.9 Ajustar la confirmación para mostrar identificadores del aporte y de la versión, clasificación, estado y aclaración de no publicación, sin hash SHA-256, referencia de almacenamiento, tipo MIME ni fecha de creación; verificar con una prueba de la página de detalle.

## 7. Pruebas de los escenarios Gherkin

- [x] 7.1 Implementar la prueba del escenario «Registro de aporte completo» con `TestClient` y base temporal, comprobando los estados `PendienteAsignacion` y `PendienteRevision`, la referencia del archivo y la ausencia de publicación; verificar que `pytest` la apruebe.
- [x] 7.2 Implementar la prueba del escenario «Datos de aporte inválidos», comprobando que se identifica la causa y que la versión no se remite a revisión; verificar que `pytest` la apruebe.
- [x] 7.3 Implementar la prueba del escenario «Archivo duplicado exacto», comprobando que se informa la coincidencia, que no se crea un nuevo aporte y que el mensaje no la presenta como aprobación académica; verificar que `pytest` la apruebe.
- [x] 7.4 Ejecutar la suite completa con una base temporal limpia y verificar que todas las pruebas pasan y que ninguna depende de `data/app.db`.
- [x] 7.5 Implementar la prueba del escenario «Clasificación académica dependiente», comprobando las opciones dependientes y el rechazo del servidor ante una combinación incoherente; verificar que `pytest` la apruebe.
- [x] 7.6 Implementar la prueba del escenario «Confirmación con información útil para el autor», comprobando los identificadores y la ausencia de datos técnicos; verificar que `pytest` la apruebe.

## 8. Integración final y documentación

- [x] 8.1 Ejecutar la aplicación desde cero (`py -m app.db.seed` y `uvicorn app.main:app --reload`), recorrer el flujo completo en `http://localhost:8000` y verificar los cinco caminos: válido, datos faltantes, archivo inválido con corrección, duplicado y fallo de almacenamiento simulado.
- [x] 8.2 Actualizar `README.md` con los comandos de instalación, creación de la base, ejecución y pruebas, la descripción del selector de rol y la advertencia de que el almacenamiento es simulado; verificar ejecutando cada comando tal como está documentado.

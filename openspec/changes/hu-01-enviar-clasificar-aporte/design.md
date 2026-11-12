# Design — HU-01 Enviar y clasificar un aporte

## Context

La aplicación parte de un repositorio de documentación y de la ficha confirmada `.cin324/historias/HU-01.md`. No existe código de aplicación todavía. El stack elegido es Python 3.14 + FastAPI + Jinja2 + SQLite + pytest. La historia se apoya en DSS-01 (`presentar apunte`, validar, resguardar y confirmar) y en EST-01 (`VersionApunte`). El modelo de dominio se usa con las correcciones acordadas: `Aporte 0..* – 1 TemaUnidad` y los atributos `hashArchivo`, `tamanoBytes` y `tipoMime` de `VersionApunte`.

## Goals / Non-Goals

**Goals:**

- Recibir un aporte con archivo y clasificación en una sola pantalla.
- Validar datos, archivo y duplicado exacto antes de registrar.
- Crear `Aporte` y `VersionApunte` con los estados acordados.
- Permitir la corrección de un archivo inválido creando una nueva versión.
- Simular el servicio de almacenamiento y dejar el proyecto ejecutable y probado.

**Non-Goals:**

- Asignar revisores, revisar contenido, publicar, notificar, buscar o descargar.
- Autenticación real; solo hay un selector de rol de demostración.
- Implementar requisitos no funcionales de usabilidad o rendimiento.
- Integrar un proveedor real de almacenamiento.

## Decisions

### 1. Arquitectura

Una sola aplicación FastAPI con renderizado en el servidor mediante Jinja2. No se usa SPA ni API separada. Las rutas de la historia llaman a un servicio de aplicación, que usa repositorios SQLite y el adaptador de almacenamiento.

- `app/main.py`: crea la aplicación, registra rutas y aplica migraciones al arrancar.
- `app/db/`: conexión, migraciones y datos de ejemplo.
- `app/dominio/`: tipos y repositorios de `Aporte`, `VersionApunte` y catálogos.
- `app/servicios/aportes.py`: validación, transiciones y transacciones.
- `app/integraciones/almacenamiento.py`: interfaz y adaptador local simulado.
- `app/rutas/aportes.py`: rutas HTTP.
- `app/templates/`: plantillas Jinja2.
- `tests/`: pruebas por escenario Gherkin.

**Alternativa considerada:** API JSON + frontend separado. Se descarta porque el curso pide una aplicación web sencilla y el renderizado en servidor reduce piezas y pruebas.

### 2. Tablas derivadas del modelo de dominio

| Clase del dominio | Tabla | Columnas principales |
|---|---|---|
| `Estudiante` | `estudiantes` | `id`, `nombre`, `correo` |
| `Carrera` | `carreras` | `id`, `codigo`, `nombre` |
| `Ramo` | `ramos` | `id`, `codigo`, `nombre`, `carrera_id` |
| `PeriodoAcademico` | `periodos_academicos` | `id`, `anio`, `semestre` |
| `TemaUnidad` | `temas_unidad` | `id`, `ramo_id`, `numero`, `nombre` |
| `Aporte` | `aportes` | `id`, `autor_id`, `ramo_id`, `periodo_id`, `tema_id`, `procedencia`, `fecha_envio`, `estado` |
| `VersionApunte` | `versiones_apunte` | `id`, `aporte_id`, `numero`, `nombre_archivo`, `referencia_archivo`, `hash_archivo`, `tamano_bytes`, `tipo_mime`, `estado`, `fecha_creacion` |

- `aportes` tiene claves foráneas no nulas a `estudiantes`, `ramos`, `periodos_academicos` y `temas_unidad`. La clasificación completa es requisito para crear el aporte; por eso no se guardan borradores con datos faltantes.
- `versiones_apunte.referencia_archivo` y `versiones_apunte.hash_archivo` son nulas cuando el archivo es inválido. `numero` es consecutivo por aporte y hay una restricción única `(aporte_id, numero)`.
- Se agrega un índice único parcial sobre `hash_archivo` cuando no es nulo, para impedir duplicados exactos incluso ante dos envíos simultáneos.
- Los estados se validan con `CHECK` y también en el servicio: `Aporte` usa `PendienteAsignacion` y `RequiereCorreccion`; `VersionApunte` usa `Recibida`, `PendienteRevision`, `RequiereCorreccion` y `Final`.
- `ComunidadEstudiantil`, `AsignacionRevision`, `RevisionAcademica`, `Notificacion` y `ReporteError` no se crean en esta historia: pertenecen a historias posteriores.
- `Carrera` no se guarda en `aportes`: se obtiene mediante `ramos.carrera_id`, tal como en el modelo.

**Alternativa considerada:** guardar un borrador con claves foráneas nulas. Se descarta porque el modelo exige `Ramo` y `PeriodoAcademico` para un `Aporte`, y la opción B1 acordada solo persiste cuando la clasificación está completa.

### 3. Transiciones de estado

`VersionApunte`:

1. Al crear: `Recibida`.
2. Archivo y clasificación válidos: `Recibida → PendienteRevision`.
3. Datos completos y archivo inválido: `Recibida → RequiereCorreccion`, con `referencia_archivo = NULL` y `hash_archivo = NULL`.
4. Corrección de archivo: se crea una versión nueva y la anterior pasa a `Final` (`RequiereCorreccion → Final`); la nueva empieza en `Recibida` y se valida.
5. Versión válida corregida: `Recibida → PendienteRevision`.

`Aporte`:

1. Envío válido: `PendienteAsignacion`.
2. Archivo inválido con datos completos: `RequiereCorreccion`.
3. Corrección válida: `RequiereCorreccion → PendienteAsignacion`.

`Aporte` no tiene EST en el curso; estos estados se registran como decisión de implementación coherente con HU-02 y EST-01.

### 4. Rutas y flujo HTTP

| Ruta | Método | Uso | Mensaje de DSS-01 |
|---|---|---|---|
| `/` | GET | Inicio y acceso al formulario | — |
| `/demo/rol` | POST | Cambiar el rol de demostración en una cookie | — |
| `/aportes/nuevo` | GET | Formulario de aporte | Presentar apunte y clasificación |
| `/aportes` | POST | Validar y registrar el aporte | Validar / solicitar resguardo / confirmar |
| `/aportes/{id}` | GET | Confirmación y detalle del aporte | Aporte recibido, pendiente de revisión |
| `/aportes/{id}/corregir` | GET | Formulario de corrección de archivo inválido | Informar motivo y solicitar corrección |
| `/aportes/{id}/correcciones` | POST | Crear la versión corregida | Reenviar versión corregida |

El formulario carga carreras, ramos, períodos y temas desde la base. La selección se ofrece en cascada: el selector de ramo solo muestra los ramos de la carrera elegida y el de tema solo los temas del ramo elegido; el período académico se elige con independencia del ramo. La relación `ramo → carrera` y `tema → ramo` se valida también en el servidor, de modo que una solicitud manipulada se rechaza aunque se omita la ayuda de JavaScript. La respuesta exitosa muestra los identificadores del aporte y de la versión, la clasificación, el estado y la aclaración de que el aporte no se publica; no expone hash SHA-256, referencia de almacenamiento, tipo MIME ni fecha de creación.

El selector de rol vive en el layout y guarda una cookie `demo_role`. Tiene dos perfiles: **Estudiante** (autor de los aportes) y **Moderador** (representa a la `ComunidadEstudiantil` del modelo). Para HU-01 solo el rol **Estudiante** puede crear y corregir aportes; el Moderador ve las pantallas sin habilitación. No es autenticación real: la cookie es una herramienta de demostración y se documenta como tal.

### 5. Validación y transacción

1. Normalizar y validar campos obligatorios: procedencia, carrera, ramo, período, tema y archivo.
2. Validar el archivo: no vacío, extensión `.pdf`, `.docx`, `.pptx`, `.png` o `.jpg`, tamaño máximo 10 MB.
3. Si faltan datos: re-renderizar el formulario con errores; no se escribe en la base.
4. Si los datos están completos y el archivo es inválido: insertar `Aporte` y `VersionApunte` en una transacción, en estado `RequiereCorreccion`, con referencia y hash nulos. No se llama al almacenamiento.
5. Si el archivo es válido: calcular SHA-256 y buscar una versión con el mismo hash. Si existe, mostrar el aporte coincidente y no insertar nada.
6. Si no hay duplicado: llamar al almacenamiento simulado. Si falla, mostrar el error y no escribir en la base.
7. Si el almacenamiento confirma: insertar `Aporte` y `VersionApunte` en una transacción, con estado `PendienteAsignacion` y `PendienteRevision`. Si la inserción falla después del almacenamiento, eliminar el archivo guardado como compensación.

Las operaciones que crean aporte y versión, o que crean la versión corregida y cierran la anterior, usan una transacción SQLite.

### 6. Almacenamiento simulado

Se define la interfaz `AlmacenamientoArchivos` con `guardar(archivo, aporte_id, version_id) -> referencia` y `eliminar(referencia)`. La implementación `AlmacenamientoLocal` guarda en `data/archivos/{aporte_id}/{version_id}_{nombre_seguro}` y devuelve la ruta relativa. El nombre se sanea para evitar traversal. El fallo se simula con una implementación falsa en las pruebas o con una variable de entorno de desarrollo; la aplicación muestra el mismo mensaje de error en ambos casos.

No se integra un proveedor externo real. La interfaz permite sustituir el adaptador en el futuro sin cambiar el servicio.

### 7. Duplicado exacto

El hash se calcula sobre los bytes del archivo. La consulta busca en `versiones_apunte` por `hash_archivo` no nulo. Si encuentra una coincidencia, se muestra el `Aporte` y la `VersionApunte` existentes, se indica que la coincidencia no es aprobación académica y no se crea un nuevo registro. El índice único parcial protege la regla ante condiciones de carrera.

### 8. Pruebas

Se usa pytest con `TestClient` de FastAPI y una base SQLite temporal por prueba. Las pruebas cubren:

- Los escenarios Gherkin de HU-01, incluidos la clasificación dependiente y la confirmación con información útil.
- Datos obligatorios faltantes: no se crea nada.
- Archivo inválido con datos completos: se crea `RequiereCorreccion`.
- Corrección: nueva versión y anterior en `Final`.
- Duplicado exacto: no se crea un nuevo aporte.
- Fallo del almacenamiento: no se confirma el registro.
- Reglas de formato y tamaño.

### 9. Migraciones y datos de ejemplo

- `app/db/migrations/001_inicial.sql`: crea las tablas, claves foráneas, índices y restricciones.
- `app/db/conexion.py`: aplica las migraciones pendientes al arrancar y registra en `schema_migrations`.
- `app/db/seed.py`: inserta de forma idempotente carreras, ramos, períodos, temas y los dos perfiles de demostración: Estudiante y Moderador (que representa a la Comunidad Estudiantil). Para HU-01 se usa el perfil Estudiante como autor.
- `README.md`: comandos de instalación, creación de la base, ejecución y pruebas.

## Risks / Trade-offs

- **Cookie de rol falsificable** → es una demostración, no autenticación; se documenta y no se usa para datos sensibles.
- **Archivo huérfano si falla la inserción después de guardar** → compensación con `eliminar(referencia)` y transacción; se prueba el camino.
- **Consumo de memoria al leer el archivo** → se limita a 10 MB y se valida antes de procesar.
- **Condición de carrera en duplicados** → índice único parcial sobre `hash_archivo` y transacción.
- **SQLite con solicitudes concurrentes** → conexión por solicitud, `PRAGMA foreign_keys = ON` y transacciones cortas; el volumen del curso es pequeño.
- **Estados de `Aporte` no modelados en EST-01** → se registran en la ficha y en este diseño; se mantienen consistentes con HU-02.

## Migration Plan

1. Crear la estructura del proyecto, `requirements.txt` y la configuración de pytest.
2. Crear y aplicar `001_inicial.sql`; cargar los datos de ejemplo.
3. Implementar el adaptador de almacenamiento y el servicio de aportes.
4. Implementar las rutas y plantillas.
5. Ejecutar las pruebas y corregir.
6. Documentar en `README.md` cómo instalar, ejecutar y probar.

Rollback de desarrollo: detener el servidor, eliminar `data/app.db` y `data/archivos`, y volver a ejecutar la migración y el seed. No hay datos de producción.

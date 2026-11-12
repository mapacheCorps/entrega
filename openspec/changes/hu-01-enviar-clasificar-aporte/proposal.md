# Proposal — HU-01 Enviar y clasificar un aporte

## Why

En el proceso AS-IS el material se comparte por chats y contactos, sin una clasificación común ni una validación previa. La comunidad recibe archivos dispersos y el estudiante que aporta no tiene forma de asegurar que su envío llegue con la información mínima. HU-01 resuelve esa entrada al proceso TO-BE: recibe el archivo y su clasificación en una sola solicitud, valida los datos y deja el aporte listo para la revisión comunitaria, sin publicarlo.

## What Changes

- Se agrega una pantalla para que un estudiante autor adjunte un apunte y declare procedencia, carrera, ramo, período académico y tema.
- La clasificación se elige en cascada: el selector de ramo ofrece solo los ramos de la carrera seleccionada y el de tema solo los temas del ramo seleccionado. El período académico se mantiene independiente. El servidor rechaza combinaciones incoherentes aunque se manipule la solicitud.
- La confirmación muestra solo información útil para el autor: identificadores del aporte y de la versión, clasificación, estado y la aclaración de que no se publica. No expone hash SHA-256, referencia de almacenamiento, tipo MIME ni fecha de creación.
- El sistema valida los campos obligatorios y el archivo: no vacío, extensión permitida (`.pdf`, `.docx`, `.pptx`, `.png`, `.jpg`) y tamaño máximo de 10 MB.
- Se detectan duplicados exactos mediante SHA-256. Si existe una coincidencia, se informa el aporte ya registrado y no se presenta la coincidencia como aprobación académica.
- Un envío válido crea un `Aporte` en estado `PendienteAsignacion` y su `VersionApunte` número 1 en estado `PendienteRevision`. El aporte no se publica.
- Si faltan datos obligatorios, se muestran las causas y no se registra nada.
- Si los datos están completos pero el archivo es inválido, se crea el aporte y la versión en `RequiereCorreccion` con `referenciaArchivo = null`. La corrección sube un archivo nuevo, crea una versión siguiente y cierra la anterior como `Final`.
- El almacenamiento externo se simula con un adaptador local; no se integra un proveedor real.
- Se usa un selector de rol de demostración. Para esta historia, el perfil activo es **Estudiante**; no hay autenticación real.
- **Fuera de alcance:** asignación de revisores (HU-02), revisión y decisión (HU-03), corrección posterior a un rechazo (HU-04), notificaciones (HU-05), búsqueda (HU-06), ficha (HU-07), descarga (HU-08), reportes (HU-09), alertas de demora (HU-10), retiro de versiones (HU-11), autenticación real y requisitos no funcionales.

## Capabilities

### New Capabilities

- `gestion-aportes`: recepción de un aporte con archivo y clasificación, validación de entrada, detección de duplicado exacto, creación de la primera versión y corrección de archivos inválidos antes de la revisión.

### Modified Capabilities

- Ninguna. El proyecto no tiene capacidades previas en `openspec/specs/`.

## Impact

- **Aplicación:** se crea la estructura inicial de la aplicación FastAPI con plantillas Jinja2 y SQLite.
- **Datos:** tablas para `estudiantes`, `carreras`, `ramos`, `periodos_academicos`, `temas_unidad`, `aportes` y `versiones_apunte`, con migraciones numeradas y datos de ejemplo.
- **Dominio:** se usan `Aporte`, `VersionApunte`, `Estudiante`, `Carrera`, `Ramo`, `PeriodoAcademico` y `TemaUnidad`. Se incorporan la asociación `Aporte 0..* – 1 TemaUnidad` y los atributos `hashArchivo`, `tamanoBytes` y `tipoMime` de `VersionApunte`, acordados en la ficha de HU-01.
- **Integraciones:** adaptador simulado de almacenamiento de archivos; no se integra un servicio externo real.
- **Pruebas:** una prueba automática por cada escenario Gherkin de HU-01.
- **Documentación del curso:** no se modifica. La fuente es `.cin324/historias/HU-01.md`.

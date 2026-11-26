# Design

## Context

Ver `proposal.md` — Why y What Changes. El sistema actual (cambio archivado `2026-11-21-hu-03-registrar-revision-comunitaria`) implementa revisión solo por Comunidad (Moderador). El modelo de dominio ya incluye la entidad `Experto` y el estado `EnRevisionExperto` en EST-01. La base de datos tiene tabla `revision_academica` sin distinguir tipo de revisor.

Stack: Python 3.14 + FastAPI + Jinja2 + SQLite. Migraciones en `app/db/migrations/`. Perfiles demo: Estudiante (autor) y Moderador (Comunidad). **No hay autenticación real**; el Experto se simula como actor externo invocado desde el panel de moderación.

## Goals / Non-Goals

**Goals:**
- Añadir tabla `experto` y extender `revision_academica` con `tipo_revisor` y `experto_id`
- Implementar transición `PendienteRevision` → `EnRevisionExperto` en el servicio de revisiones
- Permitir al Moderador derivar a Experto desde la cola de moderación (nuevo botón/acción)
- Pantalla simple para que el Experto (simulado) entregue evaluación
- Notificación (HU-05) cubre ambos orígenes de decisión
- Migración SQL idempotente y seed con datos de ejemplo de Expertos
- Pruebas para 4 nuevos escenarios Gherkin + regresión

**Non-Goals:**
- Autenticación/autorización real de Experto (cuenta institucional, login, tokens)
- Catálogo de Expertos con búsqueda, alta/baja, asignación de materias
- Notificación real por correo al Experto (se simula en bandeja)
- Proceso en segundo plano para derivar automáticamente por materia
- Historial de versiones del Experto (solo se registra en la revisión actual)

## Decisions

### 1. Modelo de datos: tabla `experto` + campos en `revision_academica`

**Opción elegida:** Nueva tabla `experto` (id, nombre, correo, especialidad, creado_en) + en `revision_academica` añadir `tipo_revisor` TEXT CHECK IN ('comunidad','experto') DEFAULT 'comunidad', `experto_id` INTEGER REFERENCES experto(id) NULL, `especialidad_registrada` TEXT NULL.

**Rationale:**
- `Experto` es entidad del dominio (08-modelo-dominio.md) → merece tabla propia
- `tipo_revisor` permite consultar fácilmente "todas las revisiones por Experto" sin JOIN complejo
- `experto_id` FK nula mantiene compatibilidad con revisiones existentes (comunidad)
- `especialidad_registrada` denormalizada en la revisión para mostrar en ficha sin JOIN

**Alternativas consideradas:**
- Solo `revisor_tipo` + `revisor_id` polimórfico: más flexible pero requiere lógica de aplicación para resolver; rechazado por simplicidad en SQLite
- Extender tabla `estudiante` con rol experto: incorrecto semánticamente (Experto no es estudiante ni tiene cuenta @uv.cl)

### 2. Transición de estado: `EnRevisionExperto` como estado propio

**Opción elegida:** Estado distinto `EnRevisionExperto` en `VersionApunte.estado` (enum/texto), con transiciones propias desde `PendienteRevision` y hacia `Aprobada`/`Rechazada`/`RequiereCorreccion`.

**Rationale:**
- Coincide exactamente con EST-01 (diagrama de estado aprobado)
- Permite queries simples: "versiones en revisión por experto" = `WHERE estado = 'EnRevisionExperto'`
- Diferencia clara en UI: panel de moderación muestra cola comunidad; panel experto muestra cola experto

**Alternativas consideradas:**
- Sub-estado dentro de `EnRevision` (campo `revisor_tipo`): más simple en BD pero rompe correspondencia 1:1 con diagrama de estados; rechazado

### 3. API: un solo endpoint de decisión con `tipo_revisor`

**Opción elegida:** `POST /moderacion/aportes/{aporte_id}/versiones/{version_id}/revision/decision` acepta body con `tipo_revisor` ('comunidad'|'experto'), `decision` ('aprobada'|'rechazada'|'correccion'), `alcance`, `observaciones`, `experto_id` (requerido si tipo_revisor=experto).

**Rationale:**
- Evita duplicar lógica de validación/transición en dos endpoints
- El servicio `revisiones.py` ya centraliza la lógica; añadir branching por `tipo_revisor` es limpio
- Coincide con DSS-02: ambos caminos convergen en "Registrar decisión"

**Alternativas consideradas:**
- Endpoints separados `/revision/comunidad` y `/revision/experto`: más REST pero duplica código de transición y notificación

### 4. UI: selector de rol extendido + panel Experto simulado

**Opción elegida:** Selector de rol actual (Estudiante/Moderador) se extiende con "Experto (demo)". Al elegir Experto, se muestra lista de versiones en `EnRevisionExperto` con botón "Evaluar". El Moderador ve en la cola un botón "Derivar a Experto" para versiones en `PendienteRevision`.

**Rationale:**
- Consistencia con arquitectura actual (selector de rol demo)
- Sin autenticación real → Experto "elige" su identidad de una lista precargada (seed)
- Mínimo cambio en templates existentes

### 5. Migración SQL: versión 005

**Archivo:** `app/db/migrations/005_experto_revision.sql`
- `CREATE TABLE experto (...)`
- `ALTER TABLE revision_academica ADD COLUMN tipo_revisor TEXT DEFAULT 'comunidad' CHECK (...)`
- `ALTER TABLE revision_academica ADD COLUMN experto_id INTEGER REFERENCES experto(id)`
- `ALTER TABLE revision_academica ADD COLUMN especialidad_registrada TEXT`
- `CREATE INDEX idx_revision_academica_tipo_revisor ON revision_academica(tipo_revisor)`
- Seed: 3 Expertos de ejemplo (especialidades: "Física Cuántica", "Cálculo Avanzado", "Estructuras de Datos")

### 6. Notificación (HU-05): un flujo, dos orígenes

**Opción elegida:** Servicio `notificaciones.py` (o dentro de `revisiones.py`) construye el mensaje según `tipo_revisor` de la `RevisionAcademica` recién creada. No hay cambio en el endpoint de notificación ni en el adaptador de correo simulado.

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|------------|
| **Inconsistencia de estado**: versión en `EnRevisionExperto` pero sin `experto_id` en revisión | Validación en servicio: al crear `RevisionAcademica` con `tipo_revisor=experto`, `experto_id` es obligatorio |
| **Decisiones simultáneas Comunidad+Experto**: race condition si ambos intentan decidir | Transacción en `registrar_decision`: `SELECT FOR UPDATE` sobre versión + check `revision_academica` existe; primera gana |
| **Seed de Expertos no representativo** | Seed incluye 3 especialidades distintas; el estudiante puede añadir más editando `seed.py` |
| **Cambio breaking en API**: clientes que envíen decision sin `tipo_revisor` | Default `tipo_revisor='comunidad'` mantiene compatibilidad hacia atrás; documentar en README |
| **Experto sin cuenta institucional**: no hay login real | Simulado con selector; fuera de alcance per rúbrica |

## Migration Plan

1. Ejecutar migración `005_experto_revision.sql` (idempotente con `IF NOT EXISTS`)
2. Actualizar `app/db/seed.py` con Expertos de ejemplo
3. Ejecutar `py -m app.db.seed` (recrea BD o migra existente)
4. Verificar que revisiones existentes tienen `tipo_revisor='comunidad'`
5. Ejecutar suite de pruebas completa (`pytest`)
# Proposal

## Why

El cambio de requerimientos del martes 24/11 (Evaluación 2) introduce la figura de **Experto** para la revisión de aportes de materias especializadas. Actualmente la revisión la realiza exclusivamente la Comunidad Estudiantil (Moderadores), pero para materias que requieren conocimiento especializado (p. ej., asignaturas técnicas avanzadas), la comunidad debe poder **convocar a un Experto externo** (profesor o especialista) que evalúe la versión y entregue su decisión fundamentada.

Este cambio extiende HU-03 (Registrar revisión comunitaria) y su caso de uso CU-03, añadiendo el caso de uso CU-13 (Revisar aporte como Experto) y modificando el ciclo de vida de `VersionApunte` (EST-01) y el flujo DSS-02.

## What Changes

- **Nuevo actor**: `Experto en la materia` (actor externo, no usuario del sistema con cuenta institucional)
- **Nuevo caso de uso**: `CU-13 Revisar aporte como Experto` (origen HU-03)
- **Nuevos estados en EST-01**: `EnRevisionExperto` con transiciones desde `PendienteRevision` y hacia `Aprobada`, `Rechazada`, `RequiereCorreccion`
- **Nuevos eventos en EST-01**: `solicitarRevisionExperto`, `evaluacionExperto` (con 3 guardas: aprueba/rechaza/corrige)
- **Modificación en DSS-02**: Variante `Materia especializada - se requiere Experto` con interacción Sistema ↔ Experto
- **Modificación en HU-03 Gherkin**: 4 nuevos escenarios (Solicitud experto, Aprobación experto, Rechazo/corrección experto, Intento no autorizado incluye Experto)
- **Nueva entidad en Modelo de Dominio**: `Experto` (identificador, nombre, correo, especialidad) con asociación `revisa como Experto` a `RevisionAcademica`
- **Entidad `RevisionAcademica`**: ahora puede ser registrada por Moderador (Comunidad) o por Experto

**BREAKING**: El estado `EnRevision` ahora tiene un camino alternativo `EnRevisionExperto`. Código que asuma solo `EnRevision` → `Aprobada/Rechazada/RequiereCorreccion` debe contemplar ambas rutas.

## Capabilities

### New Capabilities
- *(ninguna — la funcionalidad se integra en la capacidad existente)*

### Modified Capabilities
- `gestion-aportes`: Se modifican los requisitos de **decisión de revisión**, **publicación** y **autorización** para cubrir ambos orígenes de decisión (Comunidad y Experto). Se añaden escenarios de transición por Experto en el estado `EnRevisionExperto` y se actualizan los requisitos de "Una decisión por versión y autoría de moderación" y "Aprobación y publicación" para incluir al Experto como posible decisor.

## Impact

- **Base de datos**: Nueva tabla `experto` y columna `experto_id` / `tipo_revisor` en `revision_academica` (o similar) para distinguir quién decidió.
- **API**: Endpoint `POST /moderacion/aportes/{id}/versiones/{v}/revision/decision` debe aceptar `tipo_revisor` (comunidad|experto) y `experto_id` opcional.
- **Servicio de revisiones**: Lógica de transición de estado debe manejar `EnRevisionExperto` y validar autorización de Experto.
- **Templates**: Panel de moderación debe permitir derivar a Experto; vista de Experto para entregar evaluación.
- **Migraciones SQL**: Nueva migración para tabla `experto` y ajustes en `revision_academica`.
- **Pruebas**: Nuevos tests para los 4 escenarios Gherkin de Experto + regresión de comunidad.
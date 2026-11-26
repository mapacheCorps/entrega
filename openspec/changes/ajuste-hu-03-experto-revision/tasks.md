# Tasks

## 1. Base de datos y migración

- [ ] 1.1 Crear migración `app/db/migrations/005_experto_revision.sql` con tabla `experto` y columnas en `revision_academica` (tipo_revisor, experto_id, especialidad_registrada) + índices. Verificar: `sqlite3 data/app.db < migrations/005_experto_revision.sql` ejecuta sin errores y `SELECT * FROM experto` devuelve columnas esperadas.
- [ ] 1.2 Actualizar `app/db/seed.py` para insertar 3 Expertos de ejemplo (especialidades: "Física Cuántica", "Cálculo Avanzado", "Estructuras de Datos") y asegurar que `revision_academica` existentes queden con `tipo_revisor='comunidad'`. Verificar: `py -m app.db.seed` ejecuta y `SELECT * FROM experto` muestra 3 filas.
- [ ] 1.3 Actualizar `app/dominio/entidades.py`: añadir clase `Experto` y campos `tipo_revisor`, `experto_id`, `especialidad_registrada` en `RevisionAcademica`. Verificar: `pytest tests/test_dominio.py -k experto` pasa.

## 2. Servicio de revisiones (lógica de negocio)

- [ ] 2.1 Extender `app/servicios/revisiones.py`: función `registrar_decision` acepta `tipo_revisor` ('comunidad'|'experto') y `experto_id` opcional. Valida que si `tipo_revisor='experto'` entonces `experto_id` requerido. Verificar: test unitario cubre ambos caminos.
- [ ] 2.2 Implementar transición `PendienteRevision` → `EnRevisionExperto` en `solicitar_revision_experto(version_id, especialidad)`. Valida versión en `PendienteRevision` y sin decisión previa. Verificar: test unitaria cubre transición válida e inválida.
- [ ] 2.3 Implementar evaluación de Experto: `evaluar_por_experto(version_id, experto_id, decision, alcance, observaciones)`. Transiciona `EnRevisionExperto` → `Aprobada`/`Rechazada`/`RequiereCorreccion` según decisión. Verificar: 3 tests unitarios (uno por decisión).
- [ ] 2.4 Asegurar transacción atómica en `registrar_decision`: `SELECT FOR UPDATE` sobre versión + check `revision_academica` no existe. Primera decisión gana. Verificar: test de concurrencia simulada (dos decisiones simultáneas → solo una persiste).
- [ ] 2.5 Actualizar `RevisionAcademica` creada para incluir `tipo_revisor`, `experto_id`, `especialidad_registrada` (denormalizada). Verificar: inspección en BD tras test de decisión por Experto.

## 3. API (endpoints)

- [ ] 3.1 Extender `POST /moderacion/aportes/{aporte_id}/versiones/{version_id}/revision/decision` en `app/rutas/moderacion.py` para aceptar `tipo_revisor`, `experto_id` en body. Default `tipo_revisor='comunidad'` para compatibilidad. Verificar: `curl` con JSON completo retorna 201 y `RevisionAcademica` con campos correctos.
- [ ] 3.2 Añadir endpoint `POST /moderacion/aportes/{aporte_id}/versiones/{version_id}/revision/derivar-experto` para transición `PendienteRevision` → `EnRevisionExperto` (Moderador). Verificar: test de integración cubre transición válida y error si versión ya decidida.
- [ ] 3.3 Añadir endpoint `POST /experto/aportes/{aporte_id}/versiones/{version_id}/evaluar` para que Experto entregue evaluación. Verificar: test de integración cubre 3 decisiones (aprobada/rechazada/correccion).
- [ ] 3.4 Actualizar validación de autorización: Moderador solo en endpoints comunidad; Experto solo en endpoint evaluar (selector de rol demo). Verificar: test con rol incorrecto retorna 403.

## 4. Templates y UI

- [ ] 4.1 Actualizar `app/templates/moderacion_aportes.html`: añadir botón "Derivar a Experto" en fila de versión con estado `PendienteRevision`. Botón abre modal para seleccionar especialidad (input texto) y confirmar. Verificar: visual en navegador con rol Moderador.
- [ ] 4.2 Extender selector de rol en `app/templates/base.html` / `app/rutas/demo.py`: añadir opción "Experto (demo)". Al elegir, `session['rol'] = 'experto'` y `session['experto_id']` seleccionable de lista precargada. Verificar: cambio de rol funciona y persiste en sesión.
- [ ] 4.3 Crear `app/templates/experto_evaluacion.html`: lista de versiones en `EnRevisionExperto` asignadas al Experto logueado (demo), con botón "Evaluar" que abre formulario con radio buttons (aprobada/rechazada/correccion), alcance y observaciones. Verificar: visual en navegador con rol Experto.
- [ ] 4.4 Actualizar `app/templates/revision_resultado.html` y ficha de aporte: mostrar `tipo_revisor` y, si experto, `nombre_experto` y `especialidad`. Verificar: visual en ficha de aporte con revisión por experto.

## 5. Pruebas automáticas (una por escenario Gherkin nuevo)

- [ ] 5.1 Test: `test_solicitud_revision_experto.py` — cubre escenario "Solicitud de revisión por Experto para materia especializada". Verificar: `pytest tests/test_gherkin_hu03_experto.py::test_solicitud_experto` pasa.
- [ ] 5.2 Test: `test_aprobacion_experto.py` — cubre "Aprobación de versión revisada por Experto". Verificar: versión pasa a `Publicada`, notificación disparada.
- [ ] 5.3 Test: `test_rechazo_correccion_experto.py` — cubre "Rechazo o solicitud de corrección por Experto" (2 sub-tests). Verificar: versión en `Rechazada`/`RequiereCorreccion`, notificación con feedback.
- [ ] 5.4 Test: `test_intento_no_autorizado_experto.py` — cubre "Intento no autorizado" incluye Experto. Verificar: Estudiante sin rol no puede decidir ni como comunidad ni como experto.
- [ ] 5.5 Test: `test_decisiones_simultaneas_comunidad_experto.py` — cubre "Decisiones simultáneas" extendido. Verificar: primera decisión (comunidad u experto) gana, segunda rechaza.
- [ ] 5.6 Regresión: ejecutar suite completa `pytest` y verificar que tests HU-01, HU-02, HU-03 (comunidad), HU-04, HU-07, HU-08 siguen pasando.

## 6. Documentación y cierre

- [ ] 6.1 Actualizar `README.md` con: cómo probar flujo Experto (rol demo, derivar, evaluar), comandos de migración y seed. Verificar: `cat README.md` incluye sección "Flujo Experto (HU-03/CU-13)".
- [ ] 6.2 Exportar imágenes actualizadas de diagramas: `casos-de-uso.png` (con CU-13), `est-01.png` (con EnRevisionExperto), `dss-02.png` (con variante Experto). Verificar: archivos `.png` en `diagramas/` tienen fecha actual.
- [ ] 6.3 Verificar `openspec validate ajuste-hu-03-experto-revision --strict` pasa sin warnings. Verificar: comando retorna 0.

## Workflow follow-up

- Archivar el cambio después de que el estudiante valide el sistema con `/cin324-validar-sistema`.
- Hacer commit con mensaje: `HU-03: extensión revisión por Experto (cambio ajuste-hu-03-experto-revision)`
- Actualizar `.cin324/proyecto.md`: historia HU-03 → hecha, cambio archivado, fecha.
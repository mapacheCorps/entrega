# Informe de validación — HU-01 · Enviar y clasificar un aporte

**Fecha:** 2026-11-12 · **Cambio de OpenSpec validado:** `hu-01-enviar-clasificar-aporte` · **Estado:** artefactos actualizados; pendiente regenerar y volver a validar.

## Resumen

| Obs. | Lo que observaste | Tipo | Artefacto principal modificado | También revisado |
|------|-------------------|------|----------------------------------|------------------|
| OBS-1 | Al elegir una carrera, el selector de ramo mostraba ramos de otras carreras; al elegir un ramo, el selector de tema mostraba temas de otros ramos. El período académico estaba bien. | **B** (brecha de especificación, con rastro de **C** frente a la ficha) | `07-criterios-aceptacion.md`, HU-01: escenario «Clasificación académica dependiente» | `04-historias-usuario.md`, `03-requisitos.md`, `.cin324/historias/HU-01.md`, `09-casos-de-uso.md`, `10-diagramas-secuencia.md`, `12-trazabilidad.md` |
| OBS-2 | Después de enviar, la confirmación mostraba SHA-256, referencia de almacenamiento, tipo MIME y fecha de creación. Solo debía mostrar información útil para el autor. | **B** (brecha de especificación) | `07-criterios-aceptacion.md`, HU-01: escenario «Confirmación con información útil para el autor» | `04-historias-usuario.md`, `.cin324/historias/HU-01.md`, `10-diagramas-secuencia.md`, `12-trazabilidad.md` |

**Lo que sí funcionó:** los cinco caminos de HU-01 (envío válido, datos faltantes, archivo inválido con corrección, duplicado exacto y fallo de almacenamiento), los estados, el selector de dos perfiles y las 60 pruebas automáticas.

## Detalle por observación

### OBS-1 — Clasificación académica dependiente

- **Lo que dijiste:** al escoger una carrera, el selector de ramo seguía mostrando ramos de otras carreras; lo mismo pasaba con el tema o unidad respecto del ramo. El período académico estaba bien porque un ramo puede dictarse en cualquiera de los dos semestres.
- **Diagnóstico:** **B — brecha de especificación**, con una inconsistencia frente a la ficha: la ficha insinuaba el filtro, pero el Gherkin y el requisito no lo exigían.
- **Resolución aplicada:** se dejó escrito que el selector de ramo ofrece solo los ramos de la carrera seleccionada y el de tema solo los temas del ramo seleccionado; el período académico se mantiene independiente. La validación del servidor sigue rechazando combinaciones incoherentes.
- **Artefactos actualizados:**
  - `.cin324/historias/HU-01.md`: paso 2 del flujo y decisión del 2026-11-12.
  - `03-requisitos.md`: RP-01.
  - `04-historias-usuario.md`: HU-01-CA4.
  - `07-criterios-aceptacion.md`: escenario «Clasificación académica dependiente».
  - `09-casos-de-uso.md`: nota de CU-01.
  - `10-diagramas-secuencia.md`: nota «Opciones de clasificación» en DSS-01.

### OBS-2 — Confirmación con información útil

- **Lo que dijiste:** después de enviar, la pantalla mostraba SHA-256, referencia de almacenamiento y otros datos que son para un desarrollador, no para el autor. Solo debía mostrar información útil.
- **Diagnóstico:** **B — brecha de especificación**. Los artefactos decían qué mostrar, pero no excluían explícitamente los datos técnicos.
- **Resolución aplicada:** la confirmación muestra los identificadores del aporte y de la versión, la clasificación, el estado y la aclaración de que no se publica; no muestra hash SHA-256, referencia de almacenamiento, tipo MIME ni fecha de creación.
- **Artefactos actualizados:**
  - `.cin324/historias/HU-01.md`: paso 9 del flujo y decisión del 2026-11-12.
  - `04-historias-usuario.md`: HU-01-CA5.
  - `07-criterios-aceptacion.md`: escenario «Confirmación con información útil para el autor».
  - `10-diagramas-secuencia.md`: nota «Confirmación al autor» en DSS-01.

## Consistencia final

- `12-trazabilidad.md` se revisó: RP-01 y RP-02 siguen apuntando a HU-01 → CU-01 → DSS-01 → EST-01; la matriz no requiere cambios.
- No se modificó código de la aplicación ni `openspec/`.
- No cambiaron el proceso TO-BE, las relaciones del modelo de dominio ni los estados.

## Siguiente paso

1. Hacer commit de los artefactos actualizados.
2. Ejecutar `/cin324-generar-app` para regenerar el ajuste de HU-01.
3. Volver a ejecutar `/cin324-validar-sistema` para comprobar que OBS-1 y OBS-2 quedaron resueltas.
4. Archivar el cambio `hu-01-enviar-clasificar-aporte` solo después de esa validación.

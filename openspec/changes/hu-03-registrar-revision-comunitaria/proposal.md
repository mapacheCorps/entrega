# HU-03 Registrar revisión comunitaria

> Registro del ciclo original. El flujo vigente de revisión se especifica en [el ajuste de revisión directa](../ajuste-hu-02-revision-directa/proposal.md).

## Por qué

HU-02 deja el aporte validado con un revisor designado. HU-03 permite registrar la evaluación de una versión concreta y publicar únicamente la versión aprobada, según CU-03, RP-04 y RP-06. El cambio cubre P06, P09 y P10 del TO-BE.

## Qué cambia

- El Moderador ve los aportes asignados a su comunidad, consulta la versión y su archivo, e inicia la revisión en nombre del estudiante designado.
- La comunidad registra aprobación, rechazo o solicitud de corrección con alcance y observaciones. La decisión conserva fecha, versión, revisor y comunidad, y cierra la asignación vigente.
- La aprobación publica esa versión en un catálogo básico. El rechazo y la solicitud de corrección conservan el motivo y dejan el material fuera del catálogo.
- El sistema deniega los intentos sin autorización y protege el registro frente a decisiones repetidas o solicitudes para una versión que dejó de ser la actual.

El reenvío de correcciones y la entrega de observaciones al autor corresponden a HU-04. Los avisos de resolución, la búsqueda, la ficha pública detallada y la descarga pública corresponden a HU-05 a HU-08. La aplicación conserva el selector de dos perfiles de demostración.

## Capacidades

### Capacidades nuevas

### Capacidades modificadas

- `gestion-aportes` incorpora la revisión de una versión asignada, las tres decisiones y la publicación tras aprobación.

## Impacto

Se amplían el esquema SQLite, el panel de moderación y la lectura del archivo resguardado por HU-01. El catálogo consulta las versiones publicadas. Se agregan pruebas de decisiones, acceso, integridad y compatibilidad con HU-01 y HU-02.

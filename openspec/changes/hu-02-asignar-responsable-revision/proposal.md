# HU-02 Asignar responsable de revisión

> Registro del ciclo original. El flujo vigente de revisión se especifica en [el ajuste de revisión directa](../ajuste-hu-02-revision-directa/proposal.md).

## Por qué

Los aportes validados en HU-01 quedan pendientes de asignación. HU-02 permite a la comunidad estudiantil organizar su revisión según P05 del TO-BE (cambio C02), el requisito RP-03 y el caso de uso CU-02.

## Qué cambia

- El perfil Moderador abre el panel de la comunidad, consulta los aportes pendientes con una última versión validada y elige cuál asignar.
- El sistema selecciona automáticamente un estudiante de la comunidad que esté disponible, habilitado para el ramo y sea distinto del autor. Prioriza la menor carga activa y desempata por identificador.
- Si encuentra revisor, conserva su identificación en la asignación y cambia el aporte a `Asignado`. Si el aporte ya tiene una asignación vigente, muestra esa asignación.
- Si no encuentra revisor, mantiene el aporte pendiente y visible en el panel e informa la situación sin aprobarlo ni publicarlo.

El alcance cubre P05. La revisión académica, la publicación, el rechazo, las notificaciones, los plazos y los demás flujos de consulta y mantenimiento corresponden a otras historias. Se mantiene el selector de roles de demostración.

## Capabilities

### New Capabilities

### Modified Capabilities

- `gestion-aportes` incorpora la asignación de aportes validados a un revisor y el tratamiento de aportes que siguen pendientes por falta de revisor.

## Impacto

Se amplían el esquema SQLite, los datos de demostración, las rutas y las vistas HTML, y se agregan pruebas para los escenarios de HU-02. La asignación se realiza con los datos locales y no requiere integraciones externas.

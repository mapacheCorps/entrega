# Consulta y entrega de la versión publicada

## ADDED Requirements

### Requirement: Ficha de la misma versión publicada

El sistema DEBE mostrar la ficha de la versión seleccionada con procedencia, clasificación y evidencia de revisión de esa versión.

#### Scenario: Consultar versión desde el catálogo

- **WHEN** un estudiante abre una versión publicada desde el catálogo
- **THEN** la ficha muestra los antecedentes de esa versión y ofrece descargar su archivo

### Requirement: Vista previa o descarga del archivo exacto

El sistema DEBE revalidar que la versión siga publicada y que el archivo esté disponible para cada solicitud. Ofrece vista previa para PDF, PNG y JPG y descarga para los formatos admitidos.

#### Scenario: Archivo publicado disponible

- **WHEN** el estudiante solicita una vista previa admitida o una descarga
- **THEN** recibe el archivo de la misma versión seleccionada

#### Scenario: Versión retirada o archivo ausente

- **WHEN** el estudiante solicita una versión cuya publicación o archivo ya no está disponible
- **THEN** recibe un aviso y puede volver al catálogo

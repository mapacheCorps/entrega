# Casos de uso

## Actores

Los actores humanos son roles desempeñados por integrantes de la comunidad universitaria. La misma persona puede actuar como autor, consultante o integrante de la comunidad en diferentes circunstancias.

| Actor | Tipo | Descripción |
|---|---|---|
| Usuario institucional | Humano | Persona que inicia sesión con una cuenta `@uv.cl` o `@estudiantes.uv.cl`; el dominio determina su tipo de cuenta. |
| Estudiante autor | Humano | Persona con cuenta `@estudiantes.uv.cl` que envía apuntes, conoce la decisión y puede presentar versiones corregidas. |
| Académico autor | Humano | Persona con cuenta `@uv.cl` que envía apuntes y los publica directamente después de la validación. |
| Estudiante consultante | Humano | Busca, consulta, obtiene y reporta errores de los apuntes publicados. |
| Comunidad estudiantil | Colectivo humano | Estudiantes que consultan la cola de revisión, aceptan o rechazan aportes, entregan feedback y moderan el material. |
| Servicio de almacenamiento (propuesto) | Sistema externo | Resguarda los archivos de apuntes. |
| Servicio de correo (propuesto) | Sistema externo | Recibe solicitudes de envío de avisos de resolución. |

## Diagrama de casos de uso

![Casos de uso UML](./diagramas/casos-de-uso.png)

Fuente editable: [`casos-de-uso.puml`](./diagramas/casos-de-uso.puml)

## Casos de uso y su origen

| ID | Objetivo del actor | Actor principal | Historia de origen |
|---|---|---|---|
| CU-01 | Enviar y clasificar aporte | Estudiante autor o Académico autor | [HU-01](./04-historias-usuario.md#hu-01) |
| CU-02 | Consultar cola de revisión | Comunidad estudiantil | [HU-02](./04-historias-usuario.md#hu-02) |
| CU-03 | Evaluar aporte y registrar decisión | Comunidad estudiantil | [HU-03](./04-historias-usuario.md#hu-03) |
| CU-04 | Reenviar aporte corregido | Estudiante autor | [HU-04](./04-historias-usuario.md#hu-04) |
| CU-05 | Conocer resultado y feedback | Estudiante autor | [HU-05](./04-historias-usuario.md#hu-05) |
| CU-06 | Buscar material publicado | Estudiante consultante | [HU-06](./04-historias-usuario.md#hu-06) |
| CU-07 | Consultar ficha y vista previa del apunte | Estudiante consultante | [HU-07](./04-historias-usuario.md#hu-07) |
| CU-08 | Descargar versión publicada del apunte | Estudiante consultante | [HU-08](./04-historias-usuario.md#hu-08) |
| CU-09 | Reportar posible error | Estudiante consultante | [HU-09](./04-historias-usuario.md#hu-09) |
| CU-10 | Gestionar revisiones demoradas | Comunidad estudiantil | [HU-10](./04-historias-usuario.md#hu-10) |
| CU-11 | Corregir o retirar versión | Comunidad estudiantil | [HU-11](./04-historias-usuario.md#hu-11) |
| CU-12 | Iniciar sesión con cuenta institucional | Usuario institucional | [HU-12](./04-historias-usuario.md#hu-12) |

## Reglas principales

1. Todo apunte de una cuenta `@estudiantes.uv.cl` queda pendiente de revisión comunitaria; los aportes de `@uv.cl` se publican después de la validación, sin revisión.
2. La comunidad decide si aprueba o rechaza la versión y registra observaciones.
3. Si la aprueba, se publica la versión aprobada.
4. Si la rechaza, la versión no se publica y el autor recibe la justificación y el feedback para corregirla.
5. Si el autor presenta una nueva versión, esta vuelve a validación y sigue la ruta de su tipo de cuenta.
6. El acceso exige una cuenta institucional `@uv.cl` o `@estudiantes.uv.cl`; otro dominio se rechaza sin crear sesión.

## Notas por caso de uso

- **CU-01 — Clasificación dependiente:** el selector de ramo ofrece solo los ramos de la carrera seleccionada y el de tema solo los temas del ramo seleccionado; el período académico se elige con independencia del ramo. La validación del servidor rechaza combinaciones incoherentes.
- **CU-01 — Ruta según cuenta:** los aportes de `@estudiantes.uv.cl` pasan a la cola de revisión; los de `@uv.cl` se publican después de la validación, sin `RevisionAcademica`.
- **CU-12 — Acceso:** solo se aceptan correos `@uv.cl` y `@estudiantes.uv.cl`; otro dominio se rechaza sin crear sesión.

El diagrama no incorpora relaciones `<<include>>` ni `<<extend>>` sin una dependencia de objetivos que las justifique. El almacenamiento y el correo se mantienen como integraciones propuestas.

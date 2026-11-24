# Evaluacion 2

# Problema
En apuntes de materia especializadas se requieren "expertos" para hacer una revision correcta, ya que no es una materia de conocimiento basico

# Solucion
Para solucionar esto se crea un nuevo boton a la hora de revisar un apunte desde la vista de moderador/academico marcando que un experto debe revisarlo.

# Cambios
En el modelo de dominio crearemos una nueva entidad que es "Experto", por lo que tendremos tres entidades:
- Estudiantes
- Comunidad estudiantil (mods/academicos)
- Expertos (persona que sepa mucho, puede ser un 3ero como un profesor que quiera revisar)

Esta parte solo hace cambios desde la vista de moderador, el estudiante comun no recibe cambios